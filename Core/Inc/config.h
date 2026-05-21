#ifndef CONFIG_H
#define CONFIG_H

#include "stm32f3xx.h"
#include <stdint.h>

#define CONFIG_SYSCLK_HZ 64000000u
#define CONFIG_APB1_CLK_HZ 32000000u
#define CONFIG_APB1_TIMER_CLK_HZ 64000000u

#define CONFIG_UART_BAUD 115200u
#define CONFIG_SENSE_HZ 1000u
#define CONFIG_TELEMETRY_PERIOD_MS 50u

#define CONFIG_IIR_ALPHA 0.1f
#define CONFIG_ADC_COUNTS 4096.0f
#define CONFIG_VDC_DIVIDER_GAIN (105.1f / 5.1f)
#define CONFIG_VDC_ADC_REF 5.0f
#define CONFIG_CUR_ADC_REF 3.3f
#define CONFIG_ACS_DIVIDER_GAIN 0.6f
#define CONFIG_ACS_ZERO_VOLTS 2.5f
#define CONFIG_ACS_SENSITIVITY_V_PER_A 0.1f

/* MCP3201 pins. SCK is bit-banged on PA5. Each MCP3201 still has its own
 * chip-select (CS_DC1/DC2/CUR) so the firmware can address them individually.
 *
 * MISO topology on this board: TWO physical MISO return lines, not three.
 *   - MISO_DC1 (PA6): the lower-bridge island, DC1 ADC only.
 *   - MISO_DC2 / MISO_CUR (PC3): the upper-bridge island carries BOTH the
 *     DC2 ADC and the current ADC on a single wire-shared isolated return.
 * Because DC2 and CUR share PC3, SPI_MCP3201_Read must read strictly one
 * channel at a time (one CS asserted) — see spi_mcp3201.c. PC4 is unused. */
#define MCP3201_SCK_PORT GPIOA
#define MCP3201_SCK_PIN 5u
#define MCP3201_MISO_DC1_PORT GPIOA
#define MCP3201_MISO_DC1_PIN 6u
#define MCP3201_CS_DC1_PORT GPIOC
#define MCP3201_CS_DC1_PIN 0u
#define MCP3201_CS_DC2_PORT GPIOC
#define MCP3201_CS_DC2_PIN 1u
#define MCP3201_CS_CUR_PORT GPIOC
#define MCP3201_CS_CUR_PIN 2u
#define MCP3201_MISO_DC2_PORT GPIOC
#define MCP3201_MISO_DC2_PIN 3u
#define MCP3201_MISO_CUR_PORT GPIOC
#define MCP3201_MISO_CUR_PIN 3u   /* shared with DC2 on this board */

/* Hardware fault output. Driven LOW when a fault is latched, HIGH otherwise
 * (active-low, per build guide v3.1 header pin 16 "FAULT_OUT"). Wire the
 * PCB's FAULT_OUT trace to this STM32 pin. */
#define FAULT_OUT_PORT GPIOB
#define FAULT_OUT_PIN 5u

#define UART_VCP_PORT GPIOA
#define UART_VCP_TX_PIN 2u
#define UART_VCP_RX_PIN 3u

/* 32 NOPs plus GPIO overhead keeps the bit-banged SCK below 1 MHz. The
 * isolated 6N137 path has propagation delay in both directions, so this margin
 * is intentional instead of running near the MCP3201's absolute limit. */
#define MCP3201_HALF_PERIOD_DELAY_CYCLES 32u

typedef enum {
    MODE_FULL = 0,
    MODE_DC_ONLY = 1,
    MODE_CURRENT_ONLY = 2,
    MODE_OPEN_LOOP = 3,
    MODE_DC1_ONLY = 4,
    MODE_DC2_ONLY = 5,
    MODE_COUNT
} sensing_mode_t;

#define SENSOR_MASK_DC1 0x01u
#define SENSOR_MASK_DC2 0x02u
#define SENSOR_MASK_CUR 0x04u
#define SENSOR_MASK_ALL (SENSOR_MASK_DC1 | SENSOR_MASK_DC2 | SENSOR_MASK_CUR)

#endif /* CONFIG_H */
