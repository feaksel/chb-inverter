/**
 * @file sigma_delta_adc.h
 * @brief Sigma-Delta ADC Driver for RISC-V SoC
 *
 * Driver for 4-channel integrated Sigma-Delta ADC peripheral.
 * Provides high-resolution (12-14 bit ENOB) analog-to-digital conversion
 * at 10 kHz sampling rate per channel.
 *
 * Hardware Configuration:
 * - 4 independent ADC channels
 * - 1 MHz oversampling (100× OSR)
 * - 3rd-order CIC decimation filters
 * - External LM339 quad comparator interface
 * - RC filters for 1-bit DAC feedback
 *
 * Channel Mapping:
 * - Channel 0: DC Bus 1 Voltage (0-60V, scaled via AMC1301)
 * - Channel 1: DC Bus 2 Voltage (0-60V, scaled via AMC1301)
 * - Channel 2: AC Output Voltage (±150V peak, scaled via AMC1301)
 * - Channel 3: AC Output Current (±15A peak, ACS724)
 *
 * Register Map (Base: 0x00020100):
 * 0x00: CTRL        - Control register (enable, reset)
 * 0x04: STATUS      - Status register (data valid flags)
 * 0x08: DATA_CH0    - Channel 0 ADC data [15:0]
 * 0x0C: DATA_CH1    - Channel 1 ADC data [15:0]
 * 0x10: DATA_CH2    - Channel 2 ADC data [15:0]
 * 0x14: DATA_CH3    - Channel 3 ADC data [15:0]
 * 0x18: SAMPLE_CNT  - Sample counter (debug)
 *
 * @author Auto-generated for VexRISCV SoC
 * @date 2025-12-03
 * @version 1.0
 */

#ifndef SIGMA_DELTA_ADC_H
#define SIGMA_DELTA_ADC_H

#include <stdint.h>

//==========================================================================
// Base Address
//==========================================================================

#define SIGMA_DELTA_ADC_BASE    0x00020100

//==========================================================================
// Register Offsets
//==========================================================================

#define ADC_CTRL_OFFSET         0x00    // Control register
#define ADC_STATUS_OFFSET       0x04    // Status register
#define ADC_DATA_CH0_OFFSET     0x08    // Channel 0 data
#define ADC_DATA_CH1_OFFSET     0x0C    // Channel 1 data
#define ADC_DATA_CH2_OFFSET     0x10    // Channel 2 data
#define ADC_DATA_CH3_OFFSET     0x14    // Channel 3 data
#define ADC_SAMPLE_CNT_OFFSET   0x18    // Sample counter

//==========================================================================
// Register Addresses
//==========================================================================

#define ADC_CTRL        ((volatile uint32_t*)(SIGMA_DELTA_ADC_BASE + ADC_CTRL_OFFSET))
#define ADC_STATUS      ((volatile uint32_t*)(SIGMA_DELTA_ADC_BASE + ADC_STATUS_OFFSET))
#define ADC_DATA_CH0    ((volatile uint32_t*)(SIGMA_DELTA_ADC_BASE + ADC_DATA_CH0_OFFSET))
#define ADC_DATA_CH1    ((volatile uint32_t*)(SIGMA_DELTA_ADC_BASE + ADC_DATA_CH1_OFFSET))
#define ADC_DATA_CH2    ((volatile uint32_t*)(SIGMA_DELTA_ADC_BASE + ADC_DATA_CH2_OFFSET))
#define ADC_DATA_CH3    ((volatile uint32_t*)(SIGMA_DELTA_ADC_BASE + ADC_DATA_CH3_OFFSET))
#define ADC_SAMPLE_CNT  ((volatile uint32_t*)(SIGMA_DELTA_ADC_BASE + ADC_SAMPLE_CNT_OFFSET))

//==========================================================================
// Control Register Bits
//==========================================================================

#define ADC_CTRL_ENABLE     (1 << 0)    // Enable ADC conversion

//==========================================================================
// Status Register Bits
//==========================================================================

#define ADC_STATUS_CH0_VALID    (1 << 0)    // Channel 0 data valid
#define ADC_STATUS_CH1_VALID    (1 << 1)    // Channel 1 data valid
#define ADC_STATUS_CH2_VALID    (1 << 2)    // Channel 2 data valid
#define ADC_STATUS_CH3_VALID    (1 << 3)    // Channel 3 data valid

//==========================================================================
// Calibration Constants (adjust based on external scaling)
//==========================================================================

// DC Bus Voltage Channels (AMC1301 with voltage divider)
// AMC1301 gain: 8.2×, Divider ratio: 196:1 for 50V input
// ADC range: 0-65535 (16-bit unsigned)
// Voltage = (ADC_value / 65535) × 3.3V / 8.2 × 196
#define DC_BUS_SCALE_FACTOR     (3.3f / 8.2f * 196.0f / 65535.0f)

// AC Voltage Channel (AMC1301 with voltage divider)
// AMC1301 gain: 8.2×, Divider ratio: 565:1 for ±141V peak
// Voltage = ((ADC_value - 32768) / 32768) × 3.3V / 8.2 × 565
#define AC_VOLTAGE_SCALE_FACTOR (3.3f / 8.2f * 565.0f / 32768.0f)
#define AC_VOLTAGE_OFFSET       32768   // Bipolar offset

// AC Current Channel (ACS724 Hall effect sensor)
// Center: 2.5V @ 0A, Sensitivity: 200 mV/A
// Current = ((ADC_value / 65535) × 3.3V - 2.5V) / 0.2V/A
#define AC_CURRENT_SCALE_FACTOR (3.3f / 65535.0f / 0.2f)
#define AC_CURRENT_OFFSET       (2.5f / (3.3f / 65535.0f))

//==========================================================================
// Channel Definitions
//==========================================================================

typedef enum {
    ADC_CHANNEL_DC_BUS1 = 0,    // DC Bus 1 Voltage
    ADC_CHANNEL_DC_BUS2 = 1,    // DC Bus 2 Voltage
    ADC_CHANNEL_AC_VOLT = 2,    // AC Output Voltage
    ADC_CHANNEL_AC_CURR = 3     // AC Output Current
} adc_channel_t;

//==========================================================================
// Function Prototypes
//==========================================================================

/**
 * @brief Initialize the Sigma-Delta ADC
 *
 * Enables the ADC peripheral and starts continuous conversion.
 * All 4 channels sample simultaneously at 10 kHz.
 */
static inline void adc_init(void) {
    *ADC_CTRL = ADC_CTRL_ENABLE;
}

/**
 * @brief Disable the ADC
 */
static inline void adc_disable(void) {
    *ADC_CTRL = 0;
}

/**
 * @brief Check if ADC channel data is valid
 *
 * @param channel ADC channel (0-3)
 * @return 1 if data is valid, 0 otherwise
 */
static inline int adc_is_valid(adc_channel_t channel) {
    return (*ADC_STATUS >> channel) & 1;
}

/**
 * @brief Read raw ADC value from channel
 *
 * @param channel ADC channel (0-3)
 * @return 16-bit unsigned ADC value (0-65535)
 *
 * @note Reading a channel clears its valid flag
 */
static inline uint16_t adc_read_raw(adc_channel_t channel) {
    volatile uint32_t* reg;
    switch (channel) {
        case ADC_CHANNEL_DC_BUS1: reg = ADC_DATA_CH0; break;
        case ADC_CHANNEL_DC_BUS2: reg = ADC_DATA_CH1; break;
        case ADC_CHANNEL_AC_VOLT: reg = ADC_DATA_CH2; break;
        case ADC_CHANNEL_AC_CURR: reg = ADC_DATA_CH3; break;
        default: return 0;
    }
    return (uint16_t)(*reg & 0xFFFF);
}

/**
 * @brief Read DC bus voltage in volts
 *
 * @param channel ADC_CHANNEL_DC_BUS1 or ADC_CHANNEL_DC_BUS2
 * @return Voltage in volts (0-60V typical range)
 */
static inline float adc_read_dc_bus_voltage(adc_channel_t channel) {
    uint16_t raw = adc_read_raw(channel);
    return (float)raw * DC_BUS_SCALE_FACTOR;
}

/**
 * @brief Read AC output voltage in volts
 *
 * @return Voltage in volts (±150V peak typical range)
 */
static inline float adc_read_ac_voltage(void) {
    uint16_t raw = adc_read_raw(ADC_CHANNEL_AC_VOLT);
    int16_t signed_val = (int16_t)(raw - AC_VOLTAGE_OFFSET);
    return (float)signed_val * AC_VOLTAGE_SCALE_FACTOR;
}

/**
 * @brief Read AC output current in amperes
 *
 * @return Current in amperes (±15A peak typical range)
 */
static inline float adc_read_ac_current(void) {
    uint16_t raw = adc_read_raw(ADC_CHANNEL_AC_CURR);
    return ((float)raw * AC_CURRENT_SCALE_FACTOR) -
           (AC_CURRENT_OFFSET * AC_CURRENT_SCALE_FACTOR);
}

/**
 * @brief Get sample counter (for debug)
 *
 * @return Number of complete sample cycles
 */
static inline uint32_t adc_get_sample_count(void) {
    return *ADC_SAMPLE_CNT;
}

/**
 * @brief Wait for new ADC data on channel
 *
 * @param channel ADC channel (0-3)
 * @param timeout Maximum iterations to wait (0 = infinite)
 * @return 1 if data ready, 0 if timeout
 */
static inline int adc_wait_for_data(adc_channel_t channel, uint32_t timeout) {
    uint32_t count = 0;
    while (!adc_is_valid(channel)) {
        if (timeout && (++count >= timeout)) {
            return 0;  // Timeout
        }
    }
    return 1;  // Data ready
}

//==========================================================================
// Example Usage
//==========================================================================

#if 0
// Example: Read all channels continuously

#include "sigma_delta_adc.h"

void main(void) {
    // Initialize ADC
    adc_init();

    while (1) {
        // Wait for new data on any channel
        if (adc_is_valid(ADC_CHANNEL_DC_BUS1)) {
            float v_dc1 = adc_read_dc_bus_voltage(ADC_CHANNEL_DC_BUS1);
            // Use voltage...
        }

        if (adc_is_valid(ADC_CHANNEL_AC_VOLT)) {
            float v_ac = adc_read_ac_voltage();
            float i_ac = adc_read_ac_current();
            // Calculate power, etc...
        }

        // Small delay (ADC samples at 10 kHz = 100 µs period)
        delay_us(100);
    }
}

// Example: Blocking read with timeout

float read_dc_bus1_with_timeout(void) {
    if (adc_wait_for_data(ADC_CHANNEL_DC_BUS1, 10000)) {
        return adc_read_dc_bus_voltage(ADC_CHANNEL_DC_BUS1);
    } else {
        return -1.0f;  // Timeout error
    }
}

#endif

#endif // SIGMA_DELTA_ADC_H
