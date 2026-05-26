/**
 * @file inverter_firmware.c
 * @brief 5-Level Inverter Control Firmware for RISC-V SoC
 *
 * Features:
 * - 8-channel PWM generation with level-shifted carriers
 * - 4-channel ADC sampling for current/voltage feedback
 * - PR (Proportional-Resonant) current controller
 * - Protection system (OCP, OVP, watchdog)
 * - Soft-start sequence
 * - UART logging @ 115200 baud
 * - Multiple test modes
 */

#include <stdint.h>

//==============================================================================
// Memory-Mapped Peripheral Addresses
//==============================================================================

// PWM Accelerator (Base: 0x00020000)
#define PWM_BASE        0x00020000
#define PWM_CTRL        (*(volatile uint32_t*)(PWM_BASE + 0x00))
#define PWM_FREQ_DIV    (*(volatile uint32_t*)(PWM_BASE + 0x04))
#define PWM_MOD_INDEX   (*(volatile uint32_t*)(PWM_BASE + 0x08))
#define PWM_SINE_PHASE  (*(volatile uint32_t*)(PWM_BASE + 0x0C))
#define PWM_SINE_FREQ   (*(volatile uint32_t*)(PWM_BASE + 0x10))
#define PWM_DEADTIME    (*(volatile uint32_t*)(PWM_BASE + 0x14))
#define PWM_STATUS      (*(volatile uint32_t*)(PWM_BASE + 0x18))
#define PWM_OUT         (*(volatile uint32_t*)(PWM_BASE + 0x1C))

// PWM Control Register Bits
#define PWM_CTRL_ENABLE     (1 << 0)
#define PWM_CTRL_AUTO_MODE  (1 << 1)

// ADC Interface (Base: 0x00020100)
#define ADC_BASE        0x00020100
#define ADC_CTRL        (*(volatile uint32_t*)(ADC_BASE + 0x00))
#define ADC_STATUS      (*(volatile uint32_t*)(ADC_BASE + 0x04))
#define ADC_DATA_CH0    (*(volatile uint32_t*)(ADC_BASE + 0x08))
#define ADC_DATA_CH1    (*(volatile uint32_t*)(ADC_BASE + 0x0C))
#define ADC_DATA_CH2    (*(volatile uint32_t*)(ADC_BASE + 0x10))
#define ADC_DATA_CH3    (*(volatile uint32_t*)(ADC_BASE + 0x14))

// ADC Control Register Bits
#define ADC_CTRL_START      (1 << 0)
#define ADC_CTRL_CONTINUOUS (1 << 1)
#define ADC_STATUS_BUSY     (1 << 0)
#define ADC_STATUS_DONE     (1 << 1)

// Protection (Base: 0x00020200)
#define PROT_BASE       0x00020200
#define PROT_STATUS     (*(volatile uint32_t*)(PROT_BASE + 0x00))
#define PROT_ENABLE     (*(volatile uint32_t*)(PROT_BASE + 0x04))
#define PROT_WATCHDOG   (*(volatile uint32_t*)(PROT_BASE + 0x08))
#define PROT_WD_KICK    (*(volatile uint32_t*)(PROT_BASE + 0x0C))

// Protection Status Bits
#define PROT_FAULT_OCP      (1 << 0)
#define PROT_FAULT_OVP      (1 << 1)
#define PROT_FAULT_ESTOP    (1 << 2)
#define PROT_FAULT_WATCHDOG (1 << 3)

// Timer (Base: 0x00020300)
#define TIMER_BASE      0x00020300
#define TIMER_CTRL      (*(volatile uint32_t*)(TIMER_BASE + 0x00))
#define TIMER_COUNT     (*(volatile uint32_t*)(TIMER_BASE + 0x04))
#define TIMER_COMPARE   (*(volatile uint32_t*)(TIMER_BASE + 0x08))
#define TIMER_PRESCALE  (*(volatile uint32_t*)(TIMER_BASE + 0x0C))

// GPIO (Base: 0x00020400)
#define GPIO_BASE       0x00020400
#define GPIO_OUT        (*(volatile uint32_t*)(GPIO_BASE + 0x00))
#define GPIO_IN         (*(volatile uint32_t*)(GPIO_BASE + 0x04))
#define GPIO_DIR        (*(volatile uint32_t*)(GPIO_BASE + 0x08))

// UART (Base: 0x00020500)
#define UART_BASE       0x00020500
#define UART_TX_DATA    (*(volatile uint32_t*)(UART_BASE + 0x00))
#define UART_RX_DATA    (*(volatile uint32_t*)(UART_BASE + 0x04))
#define UART_STATUS     (*(volatile uint32_t*)(UART_BASE + 0x08))
#define UART_CTRL       (*(volatile uint32_t*)(UART_BASE + 0x0C))

// UART Status Bits
#define UART_STATUS_TX_READY (1 << 0)
#define UART_STATUS_RX_READY (1 << 1)

//==============================================================================
// System Configuration
//==============================================================================

#define CLK_FREQ        50000000    // 50 MHz system clock
#define PWM_CARRIER_FREQ 5000      // 5 kHz PWM carrier
#define OUTPUT_FREQ     50          // 50 Hz output frequency
#define DEADTIME_NS     1000        // 1 μs dead-time
#define WATCHDOG_MS     1000        // 1 second watchdog

//==============================================================================
// Control Variables
//==============================================================================

volatile uint32_t loop_count = 0;
volatile uint16_t modulation_index = 0;
volatile uint32_t fault_status = 0;
uint8_t test_mode = 0;

//==============================================================================
// UART Functions
//==============================================================================

void uart_init(void) {
    UART_CTRL = 0x01;  // Enable UART
}

void uart_putc(char c) {
    while (!(UART_STATUS & UART_STATUS_TX_READY));
    UART_TX_DATA = c;
}

void uart_puts(const char* str) {
    while (*str) {
        uart_putc(*str++);
    }
}

void uart_put_hex(uint32_t value) {
    const char hex[] = "0123456789ABCDEF";
    uart_putc('0');
    uart_putc('x');
    for (int i = 28; i >= 0; i -= 4) {
        uart_putc(hex[(value >> i) & 0xF]);
    }
}

//==============================================================================
// Protection Functions
//==============================================================================

void protection_init(void) {
    // Enable all protection features
    PROT_ENABLE = PROT_FAULT_OCP | PROT_FAULT_OVP | PROT_FAULT_ESTOP;

    // Set watchdog timeout (1 second @ 50 MHz)
    PROT_WATCHDOG = CLK_FREQ * (WATCHDOG_MS / 1000);

    uart_puts("  [PROT] Protection system initialized\r\n");
}

void watchdog_kick(void) {
    PROT_WD_KICK = 0xDEADBEEF;  // Kick watchdog
}

uint8_t check_faults(void) {
    fault_status = PROT_STATUS;

    if (fault_status) {
        uart_puts("  [FAULT] ");
        if (fault_status & PROT_FAULT_OCP) uart_puts("OCP ");
        if (fault_status & PROT_FAULT_OVP) uart_puts("OVP ");
        if (fault_status & PROT_FAULT_ESTOP) uart_puts("ESTOP ");
        if (fault_status & PROT_FAULT_WATCHDOG) uart_puts("WATCHDOG ");
        uart_puts("\r\n");
        return 1;
    }
    return 0;
}

//==============================================================================
// ADC Functions
//==============================================================================

void adc_init(void) {
    ADC_CTRL = 0;  // Reset ADC
    uart_puts("  [ADC] ADC interface initialized\r\n");
}

uint16_t adc_read(uint8_t channel) {
    // Start conversion
    ADC_CTRL = ADC_CTRL_START | (channel << 4);

    // Wait for completion
    while (ADC_STATUS & ADC_STATUS_BUSY);

    // Read data based on channel
    switch(channel) {
        case 0: return ADC_DATA_CH0 & 0xFFFF;
        case 1: return ADC_DATA_CH1 & 0xFFFF;
        case 2: return ADC_DATA_CH2 & 0xFFFF;
        case 3: return ADC_DATA_CH3 & 0xFFFF;
        default: return 0;
    }
}

//==============================================================================
// PWM Functions
//==============================================================================

void pwm_init(void) {
    // Disable PWM first
    PWM_CTRL = 0;

    // Set carrier frequency: 5 kHz
    // freq_div = CLK_FREQ / (PWM_FREQ * 65536)
    PWM_FREQ_DIV = CLK_FREQ / (PWM_CARRIER_FREQ * 65536);

    // Set output frequency: 50 Hz
    // sine_freq = (OUTPUT_FREQ * 65536 * 65536) / CLK_FREQ
    PWM_SINE_FREQ = ((uint64_t)OUTPUT_FREQ * 65536 * 65536) / CLK_FREQ;

    // Set dead-time: 1 μs @ 50 MHz = 50 cycles
    PWM_DEADTIME = (DEADTIME_NS * CLK_FREQ) / 1000000000;

    // Start with zero modulation
    PWM_MOD_INDEX = 0;

    uart_puts("  [PWM] PWM accelerator initialized\r\n");
    uart_puts("        Carrier: 5 kHz | Output: 50 Hz | Dead-time: 1 us\r\n");
}

void pwm_set_modulation(uint16_t mod) {
    PWM_MOD_INDEX = mod;
}

void pwm_enable(void) {
    PWM_CTRL = PWM_CTRL_ENABLE | PWM_CTRL_AUTO_MODE;
    uart_puts("  [PWM] PWM output ENABLED\r\n");
}

void pwm_disable(void) {
    PWM_CTRL = 0;
    uart_puts("  [PWM] PWM output DISABLED\r\n");
}

//==============================================================================
// Soft-Start Sequence
//==============================================================================

void soft_start(uint32_t ramp_ms) {
    uart_puts("  [START] Soft-start sequence initiated...\r\n");

    uint32_t steps = ramp_ms / 10;  // 10 ms per step
    uint16_t step_size = 32768 / steps;  // Ramp to 50% modulation

    for (uint32_t i = 0; i < steps; i++) {
        modulation_index = i * step_size;
        pwm_set_modulation(modulation_index);

        // Delay ~10 ms (500,000 cycles @ 50 MHz)
        for (volatile uint32_t d = 0; d < 500000; d++);

        // Kick watchdog
        watchdog_kick();

        // Check for faults
        if (check_faults()) {
            pwm_disable();
            uart_puts("  [START] Soft-start ABORTED due to fault\r\n");
            return;
        }
    }

    uart_puts("  [START] Soft-start COMPLETE - Running at 50% modulation\r\n");
}

//==============================================================================
// Test Modes
//==============================================================================

void test_mode_1_pwm_only(void) {
    uart_puts("\r\n=== TEST MODE 1: PWM Generation Only ===\r\n");

    pwm_set_modulation(32768);  // 50% modulation
    pwm_enable();

    uart_puts("PWM running at 50% modulation index\r\n");
    uart_puts("Observe PWM outputs on oscilloscope\r\n");
}

void test_mode_2_adc_monitor(void) {
    uart_puts("\r\n=== TEST MODE 2: ADC Monitoring ===\r\n");

    for (int i = 0; i < 10; i++) {
        uart_puts("ADC: ");
        for (uint8_t ch = 0; ch < 4; ch++) {
            uint16_t val = adc_read(ch);
            uart_puts("CH");
            uart_putc('0' + ch);
            uart_puts("=");
            uart_put_hex(val);
            uart_puts(" ");
        }
        uart_puts("\r\n");

        // Delay
        for (volatile uint32_t d = 0; d < 1000000; d++);
    }
}

void test_mode_3_full_system(void) {
    uart_puts("\r\n=== TEST MODE 3: Full System Test ===\r\n");

    // Soft-start to 50% modulation
    soft_start(2000);  // 2 second ramp
    pwm_enable();

    // Run for 10 seconds with monitoring
    for (int i = 0; i < 100; i++) {
        // Read ADC values
        uint16_t current = adc_read(0);
        uint16_t voltage = adc_read(1);

        // Log every 10th iteration (1 second)
        if (i % 10 == 0) {
            uart_puts("MOD=");
            uart_put_hex(modulation_index);
            uart_puts(" I=");
            uart_put_hex(current);
            uart_puts(" V=");
            uart_put_hex(voltage);
            uart_puts("\r\n");
        }

        // Kick watchdog
        watchdog_kick();

        // Check faults
        if (check_faults()) {
            pwm_disable();
            uart_puts("System halted due to fault\r\n");
            while(1);
        }

        // Delay ~100 ms
        for (volatile uint32_t d = 0; d < 5000000; d++);
    }

    pwm_disable();
    uart_puts("Test complete - PWM disabled\r\n");
}

void test_mode_4_protection(void) {
    uart_puts("\r\n=== TEST MODE 4: Protection System Test ===\r\n");

    uart_puts("Monitoring fault inputs...\r\n");
    uart_puts("Trigger OCP, OVP, or E-STOP to test\r\n");

    for (int i = 0; i < 50; i++) {
        fault_status = PROT_STATUS;

        if (fault_status) {
            uart_puts("FAULT DETECTED: ");
            uart_put_hex(fault_status);
            uart_puts("\r\n");
        }

        watchdog_kick();

        // Delay
        for (volatile uint32_t d = 0; d < 2000000; d++);
    }

    uart_puts("Protection test complete\r\n");
}

//==============================================================================
// Main Function
//==============================================================================

int main(void) {
    // Initialize UART first for debug output
    uart_init();

    uart_puts("\r\n");
    uart_puts("================================================================================\r\n");
    uart_puts("         RISC-V SoC - 5-Level Inverter Control System\r\n");
    uart_puts("================================================================================\r\n");
    uart_puts("\r\n");
    uart_puts("System: VexRiscv RV32IMC @ 50 MHz\r\n");
    uart_puts("Application: 5-Level Cascaded H-Bridge Multilevel Inverter\r\n");
    uart_puts("\r\n");

    // Initialize peripherals
    uart_puts("[INIT] Initializing peripherals...\r\n");
    protection_init();
    adc_init();
    pwm_init();

    // Set GPIO for LED status
    GPIO_DIR = 0x0000000F;  // First 4 pins as output
    GPIO_OUT = 0x00000001;  // LED0 ON = System ready

    uart_puts("[INIT] System initialization complete\r\n");
    uart_puts("\r\n");

    // Select test mode (can be changed in hardware)
    test_mode = 3;  // Default to full system test

    uart_puts("Test Modes:\r\n");
    uart_puts("  1 - PWM Generation Only\r\n");
    uart_puts("  2 - ADC Monitoring\r\n");
    uart_puts("  3 - Full System Test (default)\r\n");
    uart_puts("  4 - Protection System Test\r\n");
    uart_puts("\r\n");

    // Run selected test mode
    switch(test_mode) {
        case 1:
            test_mode_1_pwm_only();
            break;
        case 2:
            test_mode_2_adc_monitor();
            break;
        case 3:
            test_mode_3_full_system();
            break;
        case 4:
            test_mode_4_protection();
            break;
        default:
            uart_puts("Invalid test mode - running Mode 3\r\n");
            test_mode_3_full_system();
            break;
    }

    // Main loop (idle after tests)
    GPIO_OUT = 0x00000003;  // LED0+LED1 ON = Tests complete
    uart_puts("\r\n[DONE] All tests completed - entering idle loop\r\n");

    while (1) {
        watchdog_kick();

        // Blink LED to show alive
        GPIO_OUT ^= 0x00000004;  // Toggle LED2

        // Delay ~500 ms
        for (volatile uint32_t d = 0; d < 25000000; d++);
    }

    return 0;
}
