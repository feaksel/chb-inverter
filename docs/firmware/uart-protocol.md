# UART protocol

The operator dashboard talks to the firmware over USART2 (ST-LINK virtual COM port), **115200 8N1**. Commands are line-based, terminated by `\n` or `\r\n`.

## Line prefixes

| Prefix | Direction | Meaning |
|---|---|---|
| `$T` | MCU → PC | Telemetry frame (20 Hz). |
| `$S` | MCU → PC | Human-readable status line (on demand / on event). |
| `$C` | MCU → PC | PWM configuration line — emitted on boot and on every config change. |
| `$P` | MCU → PC | Protection configuration line — emitted on boot, `CONFIG`, and on every `VNOM` / `OC` change. |
| `$A` | MCU → PC | Async event — `START`, `AUTO_START`, `BOOT_SELF_TEST_DONE`, command echo. |
| `$E` | MCU → PC | Async error or rejection. |
| `$F` | MCU → PC | Fault report. |
| `$R` | MCU → PC | Raw ADC dump (response to `ADCRAW`). |
| `$H` | MCU → PC | Help text (response to `HELP`). |

## Command set

| Command | Allowed states | Effect |
|---|---|---|
| `START` | IDLE | Enable MOE, enter PRECHARGE, then RUN. |
| `STOP` | PRECHARGE, RUN | Disable MOE, return to IDLE. |
| `CLEAR` | FAULT | Clear the latched fault — only after the active condition is gone. |
| `MODE <0..5>` | IDLE, FAULT | Select sensing mode if the required sensors are available. |
| `STATUS` | Any | Print one human-readable status line. |
| `HELP` | Any | Print command summary. |
| `MI <0.0-0.95>` | IDLE | Override modulation index. |
| `RESCAN` | IDLE, FAULT | Re-run the ADC self-test and re-mark sensors available. |
| `MOD STAIR\|PSC\|STAIR_ALT` | IDLE | Pick modulator. |
| `FSW <hz>` | IDLE | Set switching frequency (100..20000 Hz). |
| `BRIDGE BOTH\|B1\|B2` | IDLE | Single-bridge test mode — inactive bridge freewheels (≈ 0 V contribution). |
| `FFUND <hz>` | IDLE | Set fundamental frequency (10..400 Hz). |
| `VNOM <v>` | IDLE, FAULT | Set nominal per-bridge bus voltage (5..60 V); derives UV/OV/IMBAL thresholds. |
| `OC <a>` | IDLE, FAULT | Set overcurrent trip threshold (0.5..20 A). |
| `SPIINV <0..7>` | IDLE, FAULT | Set MCP3201 SPI line-inversion mask (bit 0 = SCK, bit 1 = CS, bit 2 = MISO), then auto-rescan. |
| `ADCRAW` | Any | One-shot raw MCP3201 read; reports `$R,dc1=N,dc2=N,cur=N` (0..4095). |
| `TRIP` | IDLE, PRECHARGE, RUN | Operator-forced fault — latches `FAULT_MANUAL (0x20)`. |
| `CONFIG` | Any | Print active PWM (`$C`) and protection (`$P`) config lines. |

Accepted commands echo as `$A,<cmd>\r\n`. Rejected commands return `$E,<reason>\r\n`.

## Telemetry frame (`$T`)

Emitted at 20 Hz:

```text
$T,<ms>,<state>,<mode>,<fault>,<vdc1>,<vdc2>,<iout>,<level>*<chk>\r\n
```

- `<ms>` — `FSM_Millis()` at frame time.
- `<state>` — one of `BOOT`, `IDLE`, `PRECHARGE`, `RUN`, `FAULT`.
- `<mode>` — current sensing mode (`FULL`, `DC_ONLY`, `CUR_ONLY`, `OPEN`, `DC1`, `DC2`).
- `<fault>` — bitmask: `0x01 = UV`, `0x02 = OV`, `0x04 = OC`, `0x08 = IMBAL`, `0x10 = SENSOR_LOST`, `0x20 = MANUAL`.
- `<vdc1>`, `<vdc2>`, `<iout>` — filtered values. `NAN` if the channel is unavailable.
- `<level>` — current modulator output level (−2..+2 for STAIR; quantized cell index for PSC).
- `<chk>` — 8-bit XOR of bytes between `$` and `*`, printed as two hex characters.

Example:

```text
$T,12345,RUN,FULL,0x00,49.87,50.02,3.41,1*7B
```

## Configuration lines

`$C` — PWM config:

```text
$C,mod=PSC,fsw=5000,bridge=BOTH,ffund=50,mi=0.95,cntoff=1000,lock=OK
```

`cntoff` and `lock` are diagnostics for the PSC carrier phase shift — `lock=OK` means the measured TIM8 ↔ TIM1 offset matches the expected ARR/2; `lock=BAD` means PSC will degrade to 3-level output.

`$P` — protection config:

```text
$P,vnom=50.00,uv=40.00,ov=58.00,oc=15.00,imbal=10.00
```

## Auto-start behavior

If no UART RX byte arrives within 3 s of boot, the firmware issues its own `START` with the loaded defaults (`STAIR / 500 Hz / BOTH / MI 0.95 / 50 Hz fundamental`) and emits `$A,AUTO_START`. Any UART byte during the window cancels auto-start permanently for that boot cycle.

The dashboard's `SerialSource` automatically transmits `STATUS` on connect and on every detected `$A,BOOT_SELF_TEST_DONE`, so a connected dashboard always suppresses auto-start — including across Nucleo resets.
