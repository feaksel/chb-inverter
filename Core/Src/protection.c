#include "protection.h"

static uint8_t g_latched_faults = FAULT_NONE;

/* Runtime protection thresholds. Initialised to the values derived from the
 * 50 V default nominal bus voltage, so power-on behavior matches the original
 * fixed design (UV 40 / OV 58 / IMBAL 10 / OC 15). Updated by the runtime
 * setters below. Plain statics — only ever touched from main-loop context
 * (FSM_Run → handle_sensing → Protection_Check, and the UART handlers),
 * never from an ISR, so no volatile / atomicity concern. */
static float g_vnom_v  = PROTECTION_DEFAULT_VNOM_V;
static float g_uv_v    = PROTECTION_DEFAULT_VNOM_V * PROTECTION_UV_RATIO;
static float g_ov_v    = PROTECTION_DEFAULT_VNOM_V * PROTECTION_OV_RATIO;
static float g_imbal_v = PROTECTION_DEFAULT_VNOM_V * PROTECTION_IMBAL_RATIO;
static float g_oc_a    = PROTECTION_DEFAULT_OVERCURRENT_A;

/* Per-bit debounce counters. A fault must be seen for PROTECTION_TRIP_COUNT
 * consecutive Protection_Check calls (== consecutive 1 kHz sensor scans) before
 * it is reported. Any clean read resets the corresponding counter. */
static uint8_t g_uv_count = 0u;
static uint8_t g_ov_count = 0u;
static uint8_t g_oc_count = 0u;
static uint8_t g_imbal_count = 0u;

static float abs_f(float value)
{
    return (value < 0.0f) ? -value : value;
}

static uint8_t check_dc_channel(const sensor_channel_t *channel)
{
    uint8_t faults = FAULT_NONE;
    float volts = Sensing_RawToVdc(channel->last_raw);

    if (volts < g_uv_v) {
        faults |= FAULT_UV;
    }
    if (volts > g_ov_v) {
        faults |= FAULT_OV;
    }
    return faults;
}

static uint8_t check_current_channel(const sensor_channel_t *channel)
{
    float amps = Sensing_RawToCurrent(channel->last_raw);

    return (abs_f(amps) > g_oc_a) ? FAULT_OC : FAULT_NONE;
}

static uint8_t instant_faults(const sensing_data_t *data, sensing_mode_t mode)
{
    uint8_t faults = FAULT_NONE;

    switch (mode) {
    case MODE_FULL:
        faults |= check_dc_channel(&data->dc1);
        faults |= check_dc_channel(&data->dc2);
        faults |= check_current_channel(&data->current);
        if (abs_f(Sensing_RawToVdc(data->dc1.last_raw) -
                  Sensing_RawToVdc(data->dc2.last_raw)) > g_imbal_v) {
            faults |= FAULT_IMBAL;
        }
        break;
    case MODE_DC_ONLY:
        faults |= check_dc_channel(&data->dc1);
        faults |= check_dc_channel(&data->dc2);
        if (abs_f(Sensing_RawToVdc(data->dc1.last_raw) -
                  Sensing_RawToVdc(data->dc2.last_raw)) > g_imbal_v) {
            faults |= FAULT_IMBAL;
        }
        break;
    case MODE_CURRENT_ONLY:
        faults |= check_current_channel(&data->current);
        break;
    case MODE_DC1_ONLY:
        faults |= check_dc_channel(&data->dc1);
        if (data->current.available != 0u) {
            faults |= check_current_channel(&data->current);
        }
        break;
    case MODE_DC2_ONLY:
        faults |= check_dc_channel(&data->dc2);
        if (data->current.available != 0u) {
            faults |= check_current_channel(&data->current);
        }
        break;
    case MODE_OPEN_LOOP:
    default:
        break;
    }

    return faults;
}

static uint8_t debounce_bit(uint8_t *counter, uint8_t hit)
{
    if (hit == 0u) {
        *counter = 0u;
        return 0u;
    }
    if (*counter < 255u) {
        (*counter)++;
    }
    return (*counter >= PROTECTION_TRIP_COUNT) ? 1u : 0u;
}

uint8_t Protection_Check(const sensing_data_t *data, sensing_mode_t mode)
{
    uint8_t instant;
    uint8_t tripped = FAULT_NONE;

    if (data == (const sensing_data_t *)0) {
        return FAULT_SENSOR_LOST;
    }

    instant = instant_faults(data, mode);

    if (debounce_bit(&g_uv_count, (instant & FAULT_UV) ? 1u : 0u) != 0u) {
        tripped |= FAULT_UV;
    }
    if (debounce_bit(&g_ov_count, (instant & FAULT_OV) ? 1u : 0u) != 0u) {
        tripped |= FAULT_OV;
    }
    if (debounce_bit(&g_oc_count, (instant & FAULT_OC) ? 1u : 0u) != 0u) {
        tripped |= FAULT_OC;
    }
    if (debounce_bit(&g_imbal_count, (instant & FAULT_IMBAL) ? 1u : 0u) != 0u) {
        tripped |= FAULT_IMBAL;
    }

    return tripped;
}

void Protection_Latch(uint8_t faults)
{
    /* Fault bits are latched until CLEAR proves the active condition has gone
     * away. This prevents PWM from re-enabling after a transient trip without
     * an operator acknowledgement. */
    g_latched_faults |= faults;
}

void Protection_ClearLatched(void)
{
    g_latched_faults = FAULT_NONE;
    g_uv_count = 0u;
    g_ov_count = 0u;
    g_oc_count = 0u;
    g_imbal_count = 0u;
}

uint8_t Protection_GetLatched(void)
{
    return g_latched_faults;
}

uint8_t Protection_SetNominalVoltage(float vnom_v)
{
    if ((vnom_v < PROTECTION_VNOM_MIN_V) || (vnom_v > PROTECTION_VNOM_MAX_V)) {
        return 0u;
    }
    g_vnom_v  = vnom_v;
    g_uv_v    = vnom_v * PROTECTION_UV_RATIO;
    g_ov_v    = vnom_v * PROTECTION_OV_RATIO;
    g_imbal_v = vnom_v * PROTECTION_IMBAL_RATIO;
    return 1u;
}

uint8_t Protection_SetOvercurrent(float amps)
{
    if ((amps < PROTECTION_OVERCURRENT_MIN_A) || (amps > PROTECTION_OVERCURRENT_MAX_A)) {
        return 0u;
    }
    g_oc_a = amps;
    return 1u;
}

float Protection_GetNominalVoltage(void) { return g_vnom_v; }
float Protection_GetUndervoltage(void)   { return g_uv_v; }
float Protection_GetOvervoltage(void)    { return g_ov_v; }
float Protection_GetImbalance(void)      { return g_imbal_v; }
float Protection_GetOvercurrent(void)    { return g_oc_a; }
