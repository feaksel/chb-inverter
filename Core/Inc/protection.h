#ifndef PROTECTION_H
#define PROTECTION_H

#include "config.h"
#include "sensing.h"
#include <stdint.h>

#define PROTECTION_UNDERVOLTAGE_V 40.0f
#define PROTECTION_OVERVOLTAGE_V 58.0f
#define PROTECTION_OVERCURRENT_A 15.0f
#define PROTECTION_IMBALANCE_V 10.0f

/* N consecutive sensor scans must agree before a fault trips. At 1 kHz sense
 * rate this gives a 3 ms debounce, ignoring single-sample noise without losing
 * fast-trip behavior on real faults. */
#define PROTECTION_TRIP_COUNT 3u

#define FAULT_NONE 0x00u
#define FAULT_UV 0x01u
#define FAULT_OV 0x02u
#define FAULT_OC 0x04u
#define FAULT_IMBAL 0x08u
#define FAULT_SENSOR_LOST 0x10u

uint8_t Protection_Check(const sensing_data_t *data, sensing_mode_t mode);
void Protection_Latch(uint8_t faults);
void Protection_ClearLatched(void);
uint8_t Protection_GetLatched(void);

#endif /* PROTECTION_H */
