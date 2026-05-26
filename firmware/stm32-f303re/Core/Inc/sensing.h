#ifndef SENSING_H
#define SENSING_H

#include "config.h"
#include <stdint.h>

typedef enum {
    SENSOR_DC1 = 0,
    SENSOR_DC2 = 1,
    SENSOR_CUR = 2
} sensor_id_t;

typedef struct {
    uint16_t last_raw;
    float last_value;
    float filtered_value;
    uint8_t consecutive_rail_reads;
    uint8_t available;
    uint8_t initialized;
} sensor_channel_t;

typedef struct {
    sensor_channel_t dc1;
    sensor_channel_t dc2;
    sensor_channel_t current;
    uint32_t last_scan_ms;
} sensing_data_t;

extern volatile uint8_t g_sense_pending;

void Sensing_Init(void);
void Sensing_TIM6_IRQHandler(void);
void Sensing_SelfTest(void);
uint8_t Sensing_Service(sensing_mode_t mode, uint32_t now_ms);
const sensing_data_t *Sensing_GetData(void);
uint8_t Sensing_GetAvailableMask(void);
uint8_t Sensing_ModeRequiredMask(sensing_mode_t mode);
uint8_t Sensing_ModeSampleMask(sensing_mode_t mode);
uint8_t Sensing_ModeSensorsAvailable(sensing_mode_t mode);
uint8_t Sensing_ModeUsesDc1ForTelemetry(sensing_mode_t mode);
uint8_t Sensing_ModeUsesDc2ForTelemetry(sensing_mode_t mode);
uint8_t Sensing_ModeUsesCurrentForTelemetry(sensing_mode_t mode);
float Sensing_RawToVdc(uint16_t raw);
float Sensing_RawToCurrent(uint16_t raw);

#endif /* SENSING_H */
