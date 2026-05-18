# 5-Level Cascaded H-Bridge Inverter with STM32 Nucleo-F303RE

This project drives a 5-level cascaded H-bridge inverter using an STM32F303RE
(Nucleo-F303RE). TIM1 and TIM8 generate the complementary PWM bridge outputs;
the supervisory FSM adds sensing, protection, UART control, and telemetry.

## Highlights
- 5-level staircase output from two cascaded H-bridges
- Center-aligned complementary PWM with 2 us dead-time
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
PWM defaults remain in [Core/Src/main.c](Core/Src/main.c):
- `SINE_FREQ`: 50 Hz
- `PWM_FREQ_HZ`: 500 Hz
- `SINE_SAMPLES`: 256
- `MODULATION_INDEX`: 0.95, overridable in IDLE with `MI`
- `DEADTIME_US`: 2 us
- `BOOTSTRAP_PRECHARGE_MS`: 6 ms

Protection thresholds are in [Core/Inc/protection.h](Core/Inc/protection.h):
- DC undervoltage: 40.0 V
- DC overvoltage: 58.0 V
- Overcurrent: 15.0 A
- DC imbalance: 10.0 V

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

### Sensing and UART
| Signal | Pin | Notes |
|---|---:|---|
| SCK | PA5 | Bit-banged MCP3201 clock, held at or below 1 MHz |
| CS_DC1 | PC0 | DC bus 1 MCP3201 chip select |
| CS_DC2 | PC1 | DC bus 2 MCP3201 chip select |
| CS_CUR | PC2 | Current MCP3201 chip select |
| MISO_DC1 | PA6 | Independent isolated MISO |
| MISO_DC2 | PC3 | Independent isolated MISO |
| MISO_CUR | PC4 | Independent safe-side MISO |
| USART2_TX | PA2 | ST-LINK VCP TX, 115200 8N1 |
| USART2_RX | PA3 | ST-LINK VCP RX, 115200 8N1 |

The three MCP3201 MISO lines are not shared because the isolated 6N137 outputs
may not tri-state cleanly. The firmware clocks selected ADCs together and reads
their GPIO inputs in parallel.

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
| `MOD STAIR\|PSC` | IDLE | Pick modulator (STAIR = 500 Hz staircase, PSC = phase-shifted carriers) |
| `FSW <hz>` | IDLE | Set switching frequency (100..20000 Hz) |
| `BRIDGE BOTH\|B1\|B2` | IDLE | Single-bridge test mode (inactive bridge freewheels) |
| `FFUND <hz>` | IDLE | Set fundamental frequency (10..400 Hz) |
| `CONFIG` | Any | Print the active PWM config as `$C,mod=...,fsw=...,bridge=...,ffund=...,mi=...` |

Accepted commands echo as `$A,<cmd>\r\n`. Rejected commands return
`$E,<reason>\r\n`. PWM-config changes additionally emit a fresh `$C,...`
line so the dashboard log always reflects the live configuration.

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
