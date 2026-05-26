#ifndef SPI_MCP3201_H
#define SPI_MCP3201_H

#include "config.h"
#include <stdint.h>

typedef struct {
    uint16_t dc1;
    uint16_t dc2;
    uint16_t current;
} mcp3201_samples_t;

/* SPI line-inversion mask. Each MCP3201 SPI line crosses the galvanic
 * isolation barrier through a 6N137 optocoupler, and the 6N137 inverts
 * (LED on -> output low). If a line passes through an odd number of
 * inverting stages, set its bit so the firmware drives/reads that line
 * inverted, cancelling the hardware inversion. Standard build-guide wiring
 * (one 6N137 per line) needs SPI_INVERT_ALL.
 *
 * Runtime-settable via SPI_MCP3201_SetInvert (UART command SPIINV). */
#define SPI_INVERT_SCK   0x01u
#define SPI_INVERT_CS    0x02u
#define SPI_INVERT_MISO  0x04u
#define SPI_INVERT_NONE  0x00u
#define SPI_INVERT_ALL   (SPI_INVERT_SCK | SPI_INVERT_CS | SPI_INVERT_MISO)

/* Value applied at boot. 0 keeps the original direct-drive behavior. Change
 * to SPI_INVERT_ALL once the bench confirms the optocouplers invert, to make
 * it the power-on default. */
#define SPI_DEFAULT_INVERT_MASK SPI_INVERT_NONE

void SPI_MCP3201_Init(void);
void SPI_MCP3201_Read(uint8_t mask, mcp3201_samples_t *samples);

/* Set/get the line-inversion mask (bitwise OR of SPI_INVERT_*). SetInvert
 * also re-applies the SCK/CS idle levels with the new polarity. */
void SPI_MCP3201_SetInvert(uint8_t mask);
uint8_t SPI_MCP3201_GetInvert(void);

#endif /* SPI_MCP3201_H */
