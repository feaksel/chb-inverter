# 5-Level Cascaded H-Bridge Inverter with STM32 Nucleo-F303RE

This project drives a 5-level cascaded H-bridge inverter using an STM32F303RE
(Nucleo-F303RE). TIM1 and TIM8 generate the complementary PWM bridge outputs;
the supervisory FSM adds sensing, protection, UART control, and telemetry.

## Highlights
- 5-level staircase output from two cascaded H-bridges
- Center-aligned complementary PWM with 3 us dead-time
- Bootstrap precharge before RUN
- MCP3201-based isolated DC bus sensing and safe-side current sensing
- Graceful sensing-mode fallback when sensors are missing or faulty
- Latched protection faults with safe PWM shutdown through `BDTR.MOE = 0`
- USART2 telemetry and line-based control over the ST-LINK virtual COM port

## Control Flow
1. System init sets clock, SysTick, LUT, GPIO, timers, sensor GPIO, UART, TIM6,
   NVIC, and the FSM.
2. TIM1 update interrupt calls `Pwm_TIM1_UpdateHandler` (in
   [Core/Src/pwm_modulator.c](Core/Src/pwm_modulator.c)) which dispatches
   to the active modulator (STAIR or PSC) and owns all PWM duty content.
3. TIM6 runs at 1 kHz and only sets `g_sense_pending`; sensor reads happen in
   the main loop.
4. The main loop runs `FSM_Run()`, which handles commands, sensing, protection,
   state transitions, and 20 Hz telemetry.

## Key Parameters
PWM defaults are in [Core/Inc/pwm_config.h](Core/Inc/pwm_config.h); most
are runtime-configurable over UART (see PWM commands below):
- Modulator: `STAIR` (default), `PSC`, or `STAIR_ALT` — set with `MOD`
- Switching frequency: 500 Hz default — set with `FSW` (100–20000 Hz)
- Fundamental frequency: 50 Hz default — set with `FFUND`
- Modulation index: 0.95 default — set with `MI` (0.0–0.95)
- Bridge select: `BOTH` default — set with `BRIDGE` (BOTH/B1/B2)

Compile-time PWM constants in [Core/Src/pwm_modulator.c](Core/Src/pwm_modulator.c):
- Sine LUT size: 256 samples
- Dead-time: 3 us (`PWM_DEAD_TIME_DTG`, sized for the IRFB4110 power stage)
- Bootstrap precharge: 6 ms

Protection threshold defaults are in [Core/Inc/protection.h](Core/Inc/protection.h)
and correspond to the default 50 V nominal bus. They are runtime-adjustable
with `VNOM` / `OC` (see UART commands below):
- DC undervoltage: 40.0 V (`0.80 × VNOM`)
- DC overvoltage: 58.0 V (`1.16 × VNOM`)
- DC imbalance: 10.0 V (`0.20 × VNOM`)
- Overcurrent: 15.0 A (independent of VNOM)

## Pinout

### PWM Outputs
| Signal | Timer channel | Pin |
|---|---|---:|
| PWM_1H | TIM1_CH1 | PA8 |
| PWM_1L | TIM1_CH1N | PA7 |
| PWM_2H | TIM1_CH2 | PA9 |
| PWM_2L | TIM1_CH2N | PA12 |
| PWM_3H | TIM8_CH1 | PB6 |
| PWM_3L | TIM8_CH1N | PB3 |
| PWM_4H | TIM8_CH2 | PB8 |
| PWM_4L | TIM8_CH2N | PB0 |

### Sensing, UART, and fault output
| Signal | Pin | Notes |
|---|---:|---|
| SCK | PA5 | Bit-banged MCP3201 clock, held at or below 1 MHz |
| CS_DC1 | PC0 | DC bus 1 MCP3201 chip select |
| CS_DC2 | PC1 | DC bus 2 MCP3201 chip select |
| CS_CUR | PC2 | Current MCP3201 chip select |
| MISO_DC1 | PA6 | Lower-bridge island MISO (DC1 ADC only) |
| MISO_DC2 / MISO_CUR | PC3 | Upper-bridge island MISO — DC2 ADC and current ADC share this wire |
| USART2_TX | PA2 | ST-LINK VCP TX, 115200 8N1 |
| USART2_RX | PA3 | ST-LINK VCP RX, 115200 8N1 |
| FAULT_OUT | PB5 | Active-low hardware fault flag (LOW = fault latched) |

This board uses **two** MCP3201 MISO return lines, not three. The lower-bridge
island returns DC1 on PA6. The upper-bridge island carries both the DC2 ADC
and the current ADC on a single wire-shared isolated return on PC3 — each ADC
keeps its own chip select, and the firmware reads strictly one channel at a
time (one CS asserted) so the two never drive the shared wire together.
PC4 is unused.

`FAULT_OUT` (PB5) is an active-low GPIO the firmware pulls LOW whenever a
fault is latched and releases HIGH on return to IDLE — for an indicator LED
or an external interlock. It corresponds to build guide v3.1 header pin 16.

### SPI line inversion (`SPIINV`)
Each MCP3201 SPI line crosses the isolation barrier through a 6N137
optocoupler, which **inverts** (LED on → output low). If your board has an
odd number of inverting stages in a line, the firmware must drive/read that
line inverted to cancel it. `SPIINV <mask>` sets this at runtime — bit 0 =
SCK, bit 1 = CS, bit 2 = MISO:

- `SPIINV 0` — direct drive, no inversion (power-on default)
- `SPIINV 7` — all three lines inverted (standard one-6N137-per-line wiring)
- other values invert individual lines for unusual mixed wiring

`SPIINV` also auto-runs the sensor self-test (like `RESCAN`) so you see
immediately whether the sensors come alive. The active mask is reported in
the `STATUS` line as `spiinv=0xN`. Once you know the right value, set
`SPI_DEFAULT_INVERT_MASK` in [Core/Inc/spi_mcp3201.h](Core/Inc/spi_mcp3201.h)
to make it the power-on default.

## Sensing Modes
| ID | Mode | Sensors used | Active protection |
|---:|---|---|---|
| 0 | `FULL` | DC1, DC2, current | UV, OV, OC, imbalance |
| 1 | `DC_ONLY` | DC1, DC2 | UV, OV, imbalance |
| 2 | `CUR_ONLY` | Current | OC |
| 3 | `OPEN` | None | None |
| 4 | `DC1` | DC1, optional current | DC1 UV/OV, plus OC if current is available |
| 5 | `DC2` | DC2, optional current | DC2 UV/OV, plus OC if current is available |

At boot, each ADC is read four times. Sensors stuck at `0x000` or `0xFFF` are
marked unavailable, and the FSM auto-demotes to the most capable supported mode.
`OPEN` mode is allowed for demos but disables all protection and emits a UART
warning when selected or started.

## UART Commands
Commands are line-based and terminated by `\n` or `\r\n`.

| Command | Allowed states | Effect |
|---|---|---|
| `START` | IDLE | Enable MOE and enter PRECHARGE, then RUN |
| `STOP` | PRECHARGE, RUN | Disable MOE and return to IDLE |
| `CLEAR` | FAULT | Clear latched fault only after the active condition is gone |
| `MODE <0..5>` | IDLE, FAULT | Select sensing mode if required sensors are available |
| `STATUS` | Any | Print one human-readable status line |
| `HELP` | Any | Print command summary |
| `MI <0.0-0.95>` | IDLE | Override modulation index |
| `RESCAN` | IDLE, FAULT | Re-run the ADC self-test and re-mark sensors available |
| `MOD STAIR\|PSC\|STAIR_ALT` | IDLE | Pick modulator (STAIR = 500 Hz staircase, PSC = phase-shifted carriers, STAIR_ALT = bridge-balanced staircase) |
| `FSW <hz>` | IDLE | Set switching frequency (100..20000 Hz) |
| `BRIDGE BOTH\|B1\|B2` | IDLE | Single-bridge test mode (inactive bridge freewheels) |
| `FFUND <hz>` | IDLE | Set fundamental frequency (10..400 Hz) |
| `VNOM <v>` | IDLE, FAULT | Set nominal per-bridge bus voltage (5..60 V); derives UV/OV/IMBAL thresholds |
| `OC <a>` | IDLE, FAULT | Set overcurrent trip threshold (0.5..20 A) |
| `SPIINV <0..7>` | IDLE, FAULT | Set MCP3201 SPI line-inversion mask, then auto-rescan sensors |
| `ADCRAW` | Any | One-shot raw MCP3201 read; reports `$R,dc1=N,dc2=N,cur=N` (0..4095) |
| `TRIP` | IDLE, PRECHARGE, RUN | Operator-forced fault — latches `FAULT_MANUAL`, enters FAULT, drives FAULT_OUT low |
| `CONFIG` | Any | Print active PWM (`$C`) and protection (`$P`) config lines |

Accepted commands echo as `$A,<cmd>\r\n`. Rejected commands return
`$E,<reason>\r\n`. PWM-config changes additionally emit a fresh `$C,...`
line and protection-config changes emit a `$P,...` line, so the dashboard
log always reflects the live configuration.

### Configurable protection thresholds
The DC-bus protection thresholds are not fixed — they scale with a single
nominal bus voltage so the inverter can be bench-tested below the 50 V
design point (e.g. a 12 V supply) without the undervoltage trip firing
immediately. `VNOM <v>` sets the nominal voltage; the firmware derives:

- undervoltage = `0.80 × VNOM`
- overvoltage = `1.16 × VNOM`
- imbalance = `0.20 × VNOM`

At `VNOM 50` the derived thresholds are 40 / 58 / 10 V — the original
fixed design values. At `VNOM 12` they become 9.6 / 13.9 / 2.4 V.
Overcurrent (`OC`) is independent of VNOM because it is a load property.
The active protection config is reported on the `$P` line:
`$P,vnom=12.00,uv=9.60,ov=13.92,oc=15.00,imbal=2.40`.

**Auto-start.** If no UART byte is received within 3 s after boot, the
firmware issues its own `START` using the defaults from
[Core/Inc/pwm_config.h](Core/Inc/pwm_config.h) (`STAIR / 500 Hz / BOTH /
MI 0.95 / 50 Hz`) and emits `$A,AUTO_START`. Sending any UART byte during
those 3 s cancels auto-start permanently and the system waits for an
explicit `START`. This lets the inverter run standalone for demos while
preserving the explicit-arm behavior whenever an operator is at the keyboard.

## Telemetry
Telemetry is emitted at 20 Hz:

```text
$T,<ms>,<state>,<mode>,<fault>,<vdc1>,<vdc2>,<iout>,<level>*<chk>\r\n
```

`<chk>` is the 8-bit XOR of bytes between `$` and `*`, printed as two hex
characters. Fault bits are `0x01=UV`, `0x02=OV`, `0x04=OC`, `0x08=IMBAL`, and
`0x10=SENSOR_LOST`. Unused or unavailable channels print `NAN`.

Example:

```text
$T,12345,RUN,FULL,0x00,49.87,50.02,3.41,1*7B
```

## Build and Flash

### CubeIDE (normal workflow)
1. Open the project in STM32CubeIDE 1.17+.
2. Build the project (`Project → Build All` or hammer icon).
3. Connect the Nucleo-F303RE over USB.
4. Run or debug to flash the target.

The CubeIDE project source paths cover the whole `Core/` and `Drivers/`
trees, so new files under `Core/Src` and `Core/Inc` are picked up
automatically by the auto-discovery build.

### Command-line build (CI / verification)
Uses the same compiler CubeIDE ships, no project import needed:

```
GCC=/c/ST/STM32CubeIDE_<version>/STM32CubeIDE/plugins/com.st.stm32cube.ide.mcu.externaltools.gnu-tools-for-stm32.<ver>/tools/bin/arm-none-eabi-gcc.exe
CFLAGS="-mcpu=cortex-m4 -mfpu=fpv4-sp-d16 -mfloat-abi=hard -mthumb \
        -DDEBUG -DUSE_HAL_DRIVER -DSTM32F303xE \
        -ICore/Inc -IDrivers/STM32F3xx_HAL_Driver/Inc/Legacy \
        -IDrivers/STM32F3xx_HAL_Driver/Inc \
        -IDrivers/CMSIS/Device/ST/STM32F3xx/Include -IDrivers/CMSIS/Include \
        -O0 -g3 -Wall -Wextra -ffunction-sections -fdata-sections"
LDFLAGS="-mcpu=cortex-m4 -mfpu=fpv4-sp-d16 -mfloat-abi=hard -mthumb \
         -TSTM32F303RETX_FLASH.ld -Wl,--gc-sections -static \
         --specs=nano.specs --specs=nosys.specs -u_printf_float \
         -Wl,--start-group -lc -lm -Wl,--end-group"

mkdir -p build
for f in Core/Src/*.c Drivers/STM32F3xx_HAL_Driver/Src/*.c; do
  "$GCC" $CFLAGS -c "$f" -o "build/$(basename "$f" .c).o"
done
"$GCC" $CFLAGS -c Core/Startup/startup_stm32f303retx.s -o build/startup.o
"$GCC" $LDFLAGS build/*.o -o build/5levelchb.elf
# Optional: generate flashable formats
"${GCC%gcc.exe}objcopy.exe" -O binary build/5levelchb.elf build/5levelchb.bin
"${GCC%gcc.exe}objcopy.exe" -O ihex   build/5levelchb.elf build/5levelchb.hex
"${GCC%gcc.exe}size.exe"               build/5levelchb.elf
```

Expected output for the current branch: ~36 KB Flash, ~4 KB RAM, zero
warnings under `-Wall -Wextra -Wshadow -Wundef`.

### Flashing without CubeIDE
- **Drag and drop:** plug in the Nucleo, a USB drive named `NODE_F303RE`
  appears, copy `build/5levelchb.bin` onto it. ST-LINK does the rest.
- **STM32CubeProgrammer CLI:**
  `STM32_Programmer_CLI.exe -c port=SWD -w build/5levelchb.hex -rst`

## Dashboard tests
The dashboard parser and simulator have unit tests that do **not** require
PySide6, pyserial, or pyqtgraph and run in under a second:

```
cd dashboard
py -3 -m unittest discover tests -v
```

Current branch ships 19 tests covering the NMEA parser, fault encoding,
all FSM states/modes, the scenario simulator, and the new PWM-config
setters (modulator / FSW / bridge / fundamental frequency).

## Hardware bringup
Two docs cover bench testing:

- **[FIRST_BENCH_SESSION.md](FIRST_BENCH_SESSION.md)** — focused linear
  walkthrough for your first time on the bench with the new branch.
  Folds git pull, dashboard setup, flashing, and all three modulator
  tests (STAIR / STAIR_ALT / PSC) into one continuous procedure with
  explicit pass/fail checkpoints and TLP250-protection checks at every
  step. Start here.
- **[HARDWARE_BRINGUP.md](HARDWARE_BRINGUP.md)** — comprehensive
  phase-by-phase reference. Build-guide-style coverage of every test
  phase, what to expect, what the firmware emits on UART, scope
  captures, troubleshooting trees. Consult when something doesn't
  match the first-session doc.

Read at least the first one before applying any DC bus voltage.

## Notes and Safety
- This project drives power stages. Use proper gate drivers, isolation, and
  protection before applying high voltage.
- Verify dead-time, bootstrap timing, and sensor scaling on your hardware.
- `OPEN` mode is intentionally unprotected and should be used only for limited
  low-risk demos.
