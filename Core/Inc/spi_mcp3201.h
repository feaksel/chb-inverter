#ifndef SPI_MCP3201_H
#define SPI_MCP3201_H

#include "config.h"
#include <stdint.h>

typedef struct {
    uint16_t dc1;
    uint16_t dc2;
    uint16_t current;
} mcp3201_samples_t;

void SPI_MCP3201_Init(void);
void SPI_MCP3201_Read(uint8_t mask, mcp3201_samples_t *samples);

#endif /* SPI_MCP3201_H */
