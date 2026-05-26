#include "sensing.h"
#include "spi_mcp3201.h"

volatile uint8_t g_sense_pending = 0u;

static sensing_data_t g_sensing;

static sensor_channel_t *channel_from_mask(uint8_t single_mask)
{
    if (single_mask == SENSOR_MASK_DC1) {
        return &g_sensing.dc1;
    }
    if (single_mask == SENSOR_MASK_DC2) {
        return &g_sensing.dc2;
    }
    return &g_sensing.current;
}

float Sensing_RawToVdc(uint16_t raw)
{
    return (float)raw * CONFIG_VDC_DIVIDER_GAIN * (CONFIG_VDC_ADC_REF / CONFIG_ADC_COUNTS);
}

float Sensing_RawToCurrent(uint16_t raw)
{
    float volts = (float)raw * (CONFIG_CUR_ADC_REF / CONFIG_ADC_COUNTS);
    return ((volts / CONFIG_ACS_DIVIDER_GAIN) - CONFIG_ACS_ZERO_VOLTS) /
           CONFIG_ACS_SENSITIVITY_V_PER_A;
}

static float raw_to_value(uint8_t single_mask, uint16_t raw)
{
    if ((single_mask == SENSOR_MASK_DC1) || (single_mask == SENSOR_MASK_DC2)) {
        return Sensing_RawToVdc(raw);
    }
    return Sensing_RawToCurrent(raw);
}

static void update_channel(uint8_t single_mask, uint16_t raw, uint8_t *lost_mask)
{
    sensor_channel_t *ch = channel_from_mask(single_mask);
    float value = raw_to_value(single_mask, raw);
    uint8_t rail = ((raw == 0u) || (raw == 0x0FFFu)) ? 1u : 0u;

    ch->last_raw = raw;
    ch->last_value = value;

    if (ch->initialized == 0u) {
        ch->filtered_value = value;
        ch->initialized = 1u;
    } else {
        ch->filtered_value += CONFIG_IIR_ALPHA * (value - ch->filtered_value);
    }

    if (rail != 0u) {
        if (ch->consecutive_rail_reads < 255u) {
            ch->consecutive_rail_reads++;
        }
    } else {
        ch->consecutive_rail_reads = 0u;
    }

    if ((ch->available != 0u) && (ch->consecutive_rail_reads >= 5u)) {
        ch->available = 0u;
        *lost_mask |= single_mask;
    }
}

void Sensing_Init(void)
{
    g_sense_pending = 0u;
    g_sensing.dc1 = (sensor_channel_t){0};
    g_sensing.dc2 = (sensor_channel_t){0};
    g_sensing.current = (sensor_channel_t){0};
    g_sensing.last_scan_ms = 0u;

    RCC->APB1ENR |= RCC_APB1ENR_TIM6EN;
    TIM6->CR1 = 0u;
    TIM6->DIER = 0u;
    TIM6->PSC = 64u - 1u;
    TIM6->ARR = (CONFIG_APB1_TIMER_CLK_HZ / 64u / CONFIG_SENSE_HZ) - 1u;
    TIM6->EGR = TIM_EGR_UG;
    TIM6->SR = 0u;
    TIM6->DIER = TIM_DIER_UIE;

    NVIC_SetPriority(TIM6_DAC_IRQn, 2u);
    NVIC_EnableIRQ(TIM6_DAC_IRQn);
    TIM6->CR1 = TIM_CR1_CEN;
}

void Sensing_TIM6_IRQHandler(void)
{
    if ((TIM6->SR & TIM_SR_UIF) != 0u) {
        TIM6->SR &= ~TIM_SR_UIF;
        g_sense_pending = 1u;
    }
}

static void self_test_channel(uint8_t single_mask,
                              const uint16_t values[4],
                              sensor_channel_t *channel)
{
    uint8_t all_low = 1u;
    uint8_t all_high = 1u;
    uint32_t sum = 0u;

    for (uint32_t i = 0; i < 4u; i++) {
        if (values[i] != 0u) {
            all_low = 0u;
        }
        if (values[i] != 0x0FFFu) {
            all_high = 0u;
        }
        sum += values[i];
    }

    if ((all_low != 0u) || (all_high != 0u)) {
        channel->available = 0u;
        channel->initialized = 0u;
        channel->consecutive_rail_reads = 5u;
    } else {
        uint16_t avg = (uint16_t)(sum / 4u);
        channel->available = 1u;
        channel->initialized = 1u;
        channel->last_raw = avg;
        channel->last_value = raw_to_value(single_mask, avg);
        channel->filtered_value = channel->last_value;
        channel->consecutive_rail_reads = 0u;
    }
}

void Sensing_SelfTest(void)
{
    uint16_t dc1_values[4] = {0u, 0u, 0u, 0u};
    uint16_t dc2_values[4] = {0u, 0u, 0u, 0u};
    uint16_t cur_values[4] = {0u, 0u, 0u, 0u};

    for (uint32_t i = 0; i < 4u; i++) {
        mcp3201_samples_t samples;
        SPI_MCP3201_Read(SENSOR_MASK_ALL, &samples);
        dc1_values[i] = samples.dc1;
        dc2_values[i] = samples.dc2;
        cur_values[i] = samples.current;
    }

    self_test_channel(SENSOR_MASK_DC1, dc1_values, &g_sensing.dc1);
    self_test_channel(SENSOR_MASK_DC2, dc2_values, &g_sensing.dc2);
    self_test_channel(SENSOR_MASK_CUR, cur_values, &g_sensing.current);
}

uint8_t Sensing_Service(sensing_mode_t mode, uint32_t now_ms)
{
    uint8_t scan_mask;
    uint8_t lost_mask = 0u;
    mcp3201_samples_t samples;

    if (g_sense_pending == 0u) {
        return 0u;
    }

    g_sense_pending = 0u;
    scan_mask = Sensing_ModeSampleMask(mode);
    if (scan_mask == 0u) {
        g_sensing.last_scan_ms = now_ms;
        return 0u;
    }

    SPI_MCP3201_Read(scan_mask, &samples);
    if ((scan_mask & SENSOR_MASK_DC1) != 0u) {
        update_channel(SENSOR_MASK_DC1, samples.dc1, &lost_mask);
    }
    if ((scan_mask & SENSOR_MASK_DC2) != 0u) {
        update_channel(SENSOR_MASK_DC2, samples.dc2, &lost_mask);
    }
    if ((scan_mask & SENSOR_MASK_CUR) != 0u) {
        update_channel(SENSOR_MASK_CUR, samples.current, &lost_mask);
    }

    g_sensing.last_scan_ms = now_ms;
    return lost_mask;
}

const sensing_data_t *Sensing_GetData(void)
{
    return &g_sensing;
}

uint8_t Sensing_GetAvailableMask(void)
{
    uint8_t mask = 0u;

    if (g_sensing.dc1.available != 0u) {
        mask |= SENSOR_MASK_DC1;
    }
    if (g_sensing.dc2.available != 0u) {
        mask |= SENSOR_MASK_DC2;
    }
    if (g_sensing.current.available != 0u) {
        mask |= SENSOR_MASK_CUR;
    }

    return mask;
}

uint8_t Sensing_ModeRequiredMask(sensing_mode_t mode)
{
    switch (mode) {
    case MODE_FULL:
        return SENSOR_MASK_ALL;
    case MODE_DC_ONLY:
        return SENSOR_MASK_DC1 | SENSOR_MASK_DC2;
    case MODE_CURRENT_ONLY:
        return SENSOR_MASK_CUR;
    case MODE_DC1_ONLY:
        return SENSOR_MASK_DC1;
    case MODE_DC2_ONLY:
        return SENSOR_MASK_DC2;
    case MODE_OPEN_LOOP:
    default:
        return 0u;
    }
}

uint8_t Sensing_ModeSampleMask(sensing_mode_t mode)
{
    uint8_t available = Sensing_GetAvailableMask();

    switch (mode) {
    case MODE_FULL:
        return SENSOR_MASK_ALL & available;
    case MODE_DC_ONLY:
        return (SENSOR_MASK_DC1 | SENSOR_MASK_DC2) & available;
    case MODE_CURRENT_ONLY:
        return SENSOR_MASK_CUR & available;
    case MODE_DC1_ONLY:
        return (SENSOR_MASK_DC1 | SENSOR_MASK_CUR) & available;
    case MODE_DC2_ONLY:
        return (SENSOR_MASK_DC2 | SENSOR_MASK_CUR) & available;
    case MODE_OPEN_LOOP:
    default:
        return 0u;
    }
}

uint8_t Sensing_ModeSensorsAvailable(sensing_mode_t mode)
{
    uint8_t required = Sensing_ModeRequiredMask(mode);
    return ((Sensing_GetAvailableMask() & required) == required) ? 1u : 0u;
}

uint8_t Sensing_ModeUsesDc1ForTelemetry(sensing_mode_t mode)
{
    return ((mode == MODE_FULL) || (mode == MODE_DC_ONLY) || (mode == MODE_DC1_ONLY)) ? 1u : 0u;
}

uint8_t Sensing_ModeUsesDc2ForTelemetry(sensing_mode_t mode)
{
    return ((mode == MODE_FULL) || (mode == MODE_DC_ONLY) || (mode == MODE_DC2_ONLY)) ? 1u : 0u;
}

uint8_t Sensing_ModeUsesCurrentForTelemetry(sensing_mode_t mode)
{
    const sensing_data_t *data = Sensing_GetData();

    if ((mode == MODE_FULL) || (mode == MODE_CURRENT_ONLY)) {
        return 1u;
    }
    if (((mode == MODE_DC1_ONLY) || (mode == MODE_DC2_ONLY)) && (data->current.available != 0u)) {
        return 1u;
    }
    return 0u;
}
