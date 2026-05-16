#ifndef PWM_CONFIG_H
#define PWM_CONFIG_H

#include <stdint.h>

/* Modulator selection. The default (STAIR) is byte-for-byte the bench-validated
 * 500 Hz quantize-to-5-levels implementation. PSC is the new unipolar
 * phase-shifted-carriers modulator at the configured switching frequency. */
typedef enum {
    MODULATOR_STAIR = 0,
    MODULATOR_PSC = 1,
    MODULATOR_COUNT
} modulator_type_t;

/* Bridge selection for single-bridge test mode. The inactive bridge has all
 * four MOSFETs forced to the "both LS on, both HS off" freewheel state so its
 * contribution to the cascaded output is ~0 V. The active bridge produces its
 * normal 3-level output (-Vdc / 0 / +Vdc). */
typedef enum {
    BRIDGE_BOTH = 0,
    BRIDGE_B1_ONLY = 1,
    BRIDGE_B2_ONLY = 2,
    BRIDGE_COUNT
} bridge_select_t;

typedef struct {
    modulator_type_t modulator;
    uint32_t switching_freq_hz;
    bridge_select_t bridge_select;
    float modulation_index;
    float fundamental_freq_hz;
} pwm_config_t;

/* Safe defaults. With no UART input, the firmware boots to these and
 * (optionally) auto-starts after a delay — see FSM auto-start logic. */
#define PWM_DEFAULT_MODULATOR       MODULATOR_STAIR
#define PWM_DEFAULT_SWITCHING_HZ    500u
#define PWM_DEFAULT_BRIDGE_SELECT   BRIDGE_BOTH
#define PWM_DEFAULT_MI              0.95f
#define PWM_DEFAULT_FUNDAMENTAL_HZ  50.0f

/* Bounds for runtime config. Rejected by UART parser if outside. */
#define PWM_FSW_MIN_HZ              100u
#define PWM_FSW_MAX_HZ              20000u
#define PWM_FUNDAMENTAL_MIN_HZ      10.0f
#define PWM_FUNDAMENTAL_MAX_HZ      400.0f

/* Auto-start: if no UART byte is received within this many ms after boot,
 * the FSM issues its own START so the inverter runs standalone with defaults.
 * Any received UART byte cancels auto-start permanently. */
#define PWM_AUTOSTART_DELAY_MS      3000u

#endif /* PWM_CONFIG_H */
