#ifndef PROTECTION_H
#define PROTECTION_H

#include "config.h"
#include "sensing.h"
#include <stdint.h>

/* Protection thresholds are runtime-configurable so the inverter can be
 * bench-tested at DC bus voltages other than the 50 V design point. The
 * three voltage thresholds (UV/OV/IMBAL) are derived from a single nominal
 * bus voltage VNOM by fixed ratios; overcurrent OC is independent because
 * it is a load property, not a bus-voltage property.
 *
 * Set at runtime via Protection_SetNominalVoltage / Protection_SetOvercurrent
 * (UART commands VNOM / OC). At VNOM = 50 V the derived thresholds reproduce
 * the original fixed design values:
 *     UV    = 0.80 * 50 = 40.0 V
 *     OV    = 1.16 * 50 = 58.0 V
 *     IMBAL = 0.20 * 50 = 10.0 V
 */
#define PROTECTION_DEFAULT_VNOM_V        50.0f
#define PROTECTION_DEFAULT_OVERCURRENT_A 15.0f

#define PROTECTION_UV_RATIO     0.80f
#define PROTECTION_OV_RATIO     1.16f
#define PROTECTION_IMBAL_RATIO  0.20f

/* Bounds for the runtime setters. VNOM max keeps the derived OV (1.16x)
 * below the 1.5KE62A TVS clamp (84.5 V) and well under the IRFB4110's
 * 100 V rating. OC max is the ACS712-20A sensor's range. */
#define PROTECTION_VNOM_MIN_V        5.0f
#define PROTECTION_VNOM_MAX_V        60.0f
#define PROTECTION_OVERCURRENT_MIN_A 0.5f
#define PROTECTION_OVERCURRENT_MAX_A 20.0f

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

/* Runtime threshold configuration. Setters validate against the bounds
 * above and return 1 on success, 0 if the value was rejected (caller
 * keeps the previous thresholds and should emit an error). */
uint8_t Protection_SetNominalVoltage(float vnom_v);
uint8_t Protection_SetOvercurrent(float amps);

/* Read-back for the $P telemetry line and the dashboard. */
float Protection_GetNominalVoltage(void);
float Protection_GetUndervoltage(void);
float Protection_GetOvervoltage(void);
float Protection_GetImbalance(void);
float Protection_GetOvercurrent(void);

#endif /* PROTECTION_H */
