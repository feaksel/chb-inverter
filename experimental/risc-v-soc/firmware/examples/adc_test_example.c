/**
 * @file adc_test_example.c
 * @brief Example firmware for testing Sigma-Delta ADC
 *
 * Demonstrates:
 * - ADC initialization
 * - Reading all 4 channels
 * - Converting raw values to engineering units
 * - UART output for monitoring
 *
 * Hardware Setup:
 * - Connect LM339 comparator board to Pmod JC (bottom row)
 * - Connect RC filter network from JD (top row) to comparator inputs
 * - Connect sensor outputs (AMC1301, ACS724) to comparator +/- inputs
 * - Monitor via UART @ 115200 baud
 *
 * @author VexRISCV SoC Project
 * @date 2025-12-03
 */

#include <stdint.h>
#include "sigma_delta_adc.h"

// Assume these are defined elsewhere (uart, timing, etc.)
extern void uart_putc(char c);
extern void uart_puts(const char* s);
extern void uart_put_hex(uint32_t val);
extern void uart_put_float(float val);
extern void delay_ms(uint32_t ms);

//==========================================================================
// UART Helper Functions
//==========================================================================

void print_voltage(const char* label, float voltage) {
    uart_puts(label);
    uart_puts(": ");

    // Convert float to integer and fractional parts
    int32_t int_part = (int32_t)voltage;
    int32_t frac_part = (int32_t)((voltage - int_part) * 1000);
    if (frac_part < 0) frac_part = -frac_part;

    // Print integer part
    if (int_part < 0) {
        uart_putc('-');
        int_part = -int_part;
    }

    // Simple integer to string (works for values up to 999)
    if (int_part >= 100) uart_putc('0' + (int_part / 100) % 10);
    if (int_part >= 10) uart_putc('0' + (int_part / 10) % 10);
    uart_putc('0' + int_part % 10);

    // Print fractional part (3 digits)
    uart_putc('.');
    uart_putc('0' + (frac_part / 100) % 10);
    uart_putc('0' + (frac_part / 10) % 10);
    uart_putc('0' + frac_part % 10);

    uart_puts(" V\n");
}

void print_current(const char* label, float current) {
    uart_puts(label);
    uart_puts(": ");

    int32_t int_part = (int32_t)current;
    int32_t frac_part = (int32_t)((current - int_part) * 1000);
    if (frac_part < 0) frac_part = -frac_part;

    if (int_part < 0) {
        uart_putc('-');
        int_part = -int_part;
    }

    if (int_part >= 10) uart_putc('0' + (int_part / 10) % 10);
    uart_putc('0' + int_part % 10);
    uart_putc('.');
    uart_putc('0' + (frac_part / 100) % 10);
    uart_putc('0' + (frac_part / 10) % 10);
    uart_putc('0' + frac_part % 10);

    uart_puts(" A\n");
}

//==========================================================================
// ADC Test Functions
//==========================================================================

/**
 * @brief Test ADC initialization and basic reading
 */
void test_adc_basic(void) {
    uart_puts("\n=== Sigma-Delta ADC Basic Test ===\n");

    // Initialize ADC
    adc_init();
    uart_puts("ADC initialized\n");

    // Wait for first sample
    delay_ms(1);  // Wait >100 µs for first sample

    // Read raw values
    uart_puts("\nRaw ADC Values:\n");
    for (int i = 0; i < 4; i++) {
        if (adc_wait_for_data((adc_channel_t)i, 10000)) {
            uint16_t raw = adc_read_raw((adc_channel_t)i);
            uart_puts("  CH");
            uart_putc('0' + i);
            uart_puts(": 0x");
            uart_put_hex(raw);
            uart_putc('\n');
        } else {
            uart_puts("  CH");
            uart_putc('0' + i);
            uart_puts(": TIMEOUT\n");
        }
    }

    // Sample counter
    uint32_t samples = adc_get_sample_count();
    uart_puts("\nSample count: ");
    uart_put_hex(samples);
    uart_putc('\n');
}

/**
 * @brief Test ADC with engineering unit conversion
 */
void test_adc_engineering_units(void) {
    uart_puts("\n=== ADC Engineering Units Test ===\n");

    // Read and convert each channel
    if (adc_wait_for_data(ADC_CHANNEL_DC_BUS1, 10000)) {
        float v_dc1 = adc_read_dc_bus_voltage(ADC_CHANNEL_DC_BUS1);
        print_voltage("DC Bus 1", v_dc1);
    }

    if (adc_wait_for_data(ADC_CHANNEL_DC_BUS2, 10000)) {
        float v_dc2 = adc_read_dc_bus_voltage(ADC_CHANNEL_DC_BUS2);
        print_voltage("DC Bus 2", v_dc2);
    }

    if (adc_wait_for_data(ADC_CHANNEL_AC_VOLT, 10000)) {
        float v_ac = adc_read_ac_voltage();
        print_voltage("AC Voltage", v_ac);
    }

    if (adc_wait_for_data(ADC_CHANNEL_AC_CURR, 10000)) {
        float i_ac = adc_read_ac_current();
        print_current("AC Current", i_ac);
    }

    // Calculate power
    float v_ac = adc_read_ac_voltage();
    float i_ac = adc_read_ac_current();
    float power = v_ac * i_ac;

    uart_puts("\nInstantaneous Power: ");
    print_voltage("", power);  // Reuse voltage print for power
    uart_puts(" (V × A = W)\n");
}

/**
 * @brief Continuous monitoring mode
 */
void test_adc_continuous(void) {
    uart_puts("\n=== Continuous ADC Monitoring ===\n");
    uart_puts("Press any key to stop\n\n");

    uint32_t iteration = 0;

    while (1) {  // In real code, check for UART input to exit
        // Wait for new data
        if (adc_wait_for_data(ADC_CHANNEL_DC_BUS1, 10000)) {

            // Read all channels
            float v_dc1 = adc_read_dc_bus_voltage(ADC_CHANNEL_DC_BUS1);
            float v_dc2 = adc_read_dc_bus_voltage(ADC_CHANNEL_DC_BUS2);
            float v_ac = adc_read_ac_voltage();
            float i_ac = adc_read_ac_current();

            // Print iteration number
            uart_puts("[");
            uart_put_hex(iteration++);
            uart_puts("] ");

            // Print values on one line
            uart_puts("DC1: ");
            uart_put_float(v_dc1);
            uart_puts("V  DC2: ");
            uart_put_float(v_dc2);
            uart_puts("V  AC: ");
            uart_put_float(v_ac);
            uart_puts("V  I: ");
            uart_put_float(i_ac);
            uart_puts("A\n");

            // Limit update rate to 100 Hz (readable on terminal)
            delay_ms(10);
        }

        // Exit after 100 iterations for demo
        if (iteration >= 100) break;
    }

    uart_puts("\nContinuous monitoring stopped\n");
}

/**
 * @brief Test ADC data validity flags
 */
void test_adc_validity(void) {
    uart_puts("\n=== ADC Validity Flag Test ===\n");

    // Clear any pending data by reading
    for (int i = 0; i < 4; i++) {
        adc_read_raw((adc_channel_t)i);
    }

    // Check status immediately (should be invalid)
    uart_puts("Initial status (should be 0): 0x");
    uart_put_hex(*ADC_STATUS);
    uart_putc('\n');

    // Wait for new sample
    delay_ms(1);

    // Check status again (should have some valid bits)
    uart_puts("After 1ms (should be non-zero): 0x");
    uart_put_hex(*ADC_STATUS);
    uart_putc('\n');

    // Check individual channels
    uart_puts("\nChannel validity:\n");
    for (int i = 0; i < 4; i++) {
        uart_puts("  CH");
        uart_putc('0' + i);
        uart_puts(": ");
        uart_puts(adc_is_valid((adc_channel_t)i) ? "VALID\n" : "INVALID\n");
    }
}

//==========================================================================
// Main Test Program
//==========================================================================

int main(void) {
    // Initialize UART (assume this is done elsewhere)
    uart_puts("\n\n");
    uart_puts("=====================================\n");
    uart_puts(" Sigma-Delta ADC Test Program\n");
    uart_puts(" VexRISCV SoC - 5-Level Inverter\n");
    uart_puts("=====================================\n");

    // Run tests
    test_adc_basic();
    delay_ms(100);

    test_adc_validity();
    delay_ms(100);

    test_adc_engineering_units();
    delay_ms(100);

    test_adc_continuous();

    uart_puts("\n=== All Tests Complete ===\n");

    // Disable ADC
    adc_disable();
    uart_puts("ADC disabled\n");

    while (1) {
        // Infinite loop
    }

    return 0;
}
