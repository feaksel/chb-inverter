/**
 * @file memory_map.h
 * @brief Memory Map for Custom RISC-V SoC
 *
 * Complete memory map for all peripherals and memory regions.
 * This is IDENTICAL to the VexRiscv SoC memory map for compatibility.
 *
 * @author Custom RISC-V SoC Team
 * @date 2025-12-03
 */

#ifndef MEMORY_MAP_H
#define MEMORY_MAP_H

#include <stdint.h>

//=============================================================================
// Memory Regions
//=============================================================================

#define ROM_BASE        0x00000000  // 32 KB instruction ROM
#define ROM_SIZE        0x00008000  // 32 KB

#define RAM_BASE        0x00010000  // 64 KB data RAM
#define RAM_SIZE        0x00010000  // 64 KB

#define PERIPH_BASE     0x00020000  // Peripheral base address

//=============================================================================
// Peripheral Addresses
//=============================================================================

// PWM Accelerator (Base: 0x00020000)
#define PWM_BASE        (PERIPH_BASE + 0x0000)
#define PWM_SIZE        0x00000100

// Sigma-Delta ADC (Base: 0x00020100)
#define ADC_BASE        (PERIPH_BASE + 0x0100)
#define ADC_SIZE        0x00000100

// Protection/Fault (Base: 0x00020200)
#define PROT_BASE       (PERIPH_BASE + 0x0200)
#define PROT_SIZE       0x00000100

// Timer (Base: 0x00020300)
#define TIMER_BASE      (PERIPH_BASE + 0x0300)
#define TIMER_SIZE      0x00000100

// GPIO (Base: 0x00020400)
#define GPIO_BASE       (PERIPH_BASE + 0x0400)
#define GPIO_SIZE       0x00000100

// UART (Base: 0x00020500)
#define UART_BASE       (PERIPH_BASE + 0x0500)
#define UART_SIZE       0x00000100

//=============================================================================
// PWM Accelerator Registers
//=============================================================================

typedef volatile struct {
    uint32_t CTRL;          // 0x00: Control register
    uint32_t PERIOD;        // 0x04: PWM period
    uint32_t DEADTIME;      // 0x08: Dead-time (nanoseconds)
    uint32_t reserved0;     // 0x0C: Reserved
    uint32_t DUTY_CH0;      // 0x10: Channel 0 duty cycle
    uint32_t DUTY_CH1;      // 0x14: Channel 1 duty cycle
    uint32_t DUTY_CH2;      // 0x18: Channel 2 duty cycle
    uint32_t DUTY_CH3;      // 0x1C: Channel 3 duty cycle
    uint32_t DUTY_CH4;      // 0x20: Channel 4 duty cycle
    uint32_t DUTY_CH5;      // 0x24: Channel 5 duty cycle
    uint32_t DUTY_CH6;      // 0x28: Channel 6 duty cycle
    uint32_t DUTY_CH7;      // 0x2C: Channel 7 duty cycle
    uint32_t STATUS;        // 0x30: Status register
} pwm_regs_t;

#define PWM ((pwm_regs_t*)PWM_BASE)

// PWM Control register bits
#define PWM_CTRL_ENABLE     (1 << 0)    // Enable PWM generation
#define PWM_CTRL_UPDATE     (1 << 1)    // Trigger atomic update
#define PWM_CTRL_SYNC_EN    (1 << 2)    // Enable synchronization

//=============================================================================
// Sigma-Delta ADC Registers
//=============================================================================

typedef volatile struct {
    uint32_t CTRL;          // 0x00: Control register
    uint32_t STATUS;        // 0x04: Status register
    uint32_t DATA_CH0;      // 0x08: Channel 0 data (DC Bus 1)
    uint32_t DATA_CH1;      // 0x0C: Channel 1 data (DC Bus 2)
    uint32_t DATA_CH2;      // 0x10: Channel 2 data (AC Voltage)
    uint32_t DATA_CH3;      // 0x14: Channel 3 data (AC Current)
    uint32_t FIFO_LEVEL;    // 0x18: FIFO fill level
    uint32_t IRQ_EN;        // 0x1C: Interrupt enable
} adc_regs_t;

#define ADC ((adc_regs_t*)ADC_BASE)

// ADC Control register bits
#define ADC_CTRL_ENABLE     (1 << 0)    // Enable ADC
#define ADC_CTRL_FIFO_EN    (1 << 1)    // Enable FIFO
#define ADC_CTRL_CONT       (1 << 2)    // Continuous conversion mode

// ADC Status register bits
#define ADC_STATUS_VALID_CH0  (1 << 0)  // Channel 0 data valid
#define ADC_STATUS_VALID_CH1  (1 << 1)  // Channel 1 data valid
#define ADC_STATUS_VALID_CH2  (1 << 2)  // Channel 2 data valid
#define ADC_STATUS_VALID_CH3  (1 << 3)  // Channel 3 data valid
#define ADC_STATUS_FIFO_FULL  (1 << 8)  // FIFO full
#define ADC_STATUS_FIFO_EMPTY (1 << 9)  // FIFO empty

//=============================================================================
// Protection/Fault Registers
//=============================================================================

typedef volatile struct {
    uint32_t CTRL;          // 0x00: Control register
    uint32_t STATUS;        // 0x04: Status register
    uint32_t FAULT_MASK;    // 0x08: Fault enable mask
    uint32_t FAULT_CLEAR;   // 0x0C: Fault clear (write 1 to clear)
    uint32_t OCP_THRESHOLD; // 0x10: Overcurrent threshold
    uint32_t OVP_THRESHOLD; // 0x14: Overvoltage threshold
    uint32_t WATCHDOG;      // 0x18: Watchdog timer value
    uint32_t IRQ_EN;        // 0x1C: Interrupt enable
} prot_regs_t;

#define PROT ((prot_regs_t*)PROT_BASE)

// Protection Status register bits
#define PROT_STATUS_OCP     (1 << 0)    // Overcurrent fault
#define PROT_STATUS_OVP     (1 << 1)    // Overvoltage fault
#define PROT_STATUS_ESTOP   (1 << 2)    // Emergency stop
#define PROT_STATUS_WD      (1 << 3)    // Watchdog timeout
#define PROT_STATUS_ANY     (0xF)       // Any fault

//=============================================================================
// Timer Registers
//=============================================================================

typedef volatile struct {
    uint32_t CTRL;          // 0x00: Control register
    uint32_t STATUS;        // 0x04: Status register
    uint32_t PRESCALER;     // 0x08: Prescaler value
    uint32_t COUNT;         // 0x0C: Counter value
    uint32_t COMPARE;       // 0x10: Compare value
    uint32_t IRQ_EN;        // 0x14: Interrupt enable
} timer_regs_t;

#define TIMER ((timer_regs_t*)TIMER_BASE)

// Timer Control register bits
#define TIMER_CTRL_ENABLE   (1 << 0)    // Enable timer
#define TIMER_CTRL_IRQ_EN   (1 << 1)    // Enable interrupt
#define TIMER_CTRL_AUTO     (1 << 2)    // Auto-reload mode

//=============================================================================
// GPIO Registers
//=============================================================================

typedef volatile struct {
    uint32_t DATA_OUT;      // 0x00: Output data
    uint32_t DATA_IN;       // 0x04: Input data (read-only)
    uint32_t DIR;           // 0x08: Direction (1=output, 0=input)
    uint32_t IRQ_EN;        // 0x0C: Interrupt enable
    uint32_t IRQ_TYPE;      // 0x10: Interrupt type (edge/level)
    uint32_t IRQ_POL;       // 0x14: Interrupt polarity
} gpio_regs_t;

#define GPIO ((gpio_regs_t*)GPIO_BASE)

//=============================================================================
// UART Registers
//=============================================================================

typedef volatile struct {
    uint32_t DATA;          // 0x00: TX/RX data
    uint32_t STATUS;        // 0x04: Status register
    uint32_t BAUD_DIV;      // 0x08: Baud rate divisor
    uint32_t CTRL;          // 0x0C: Control register
    uint32_t IRQ_EN;        // 0x10: Interrupt enable
} uart_regs_t;

#define UART ((uart_regs_t*)UART_BASE)

// UART Status register bits
#define UART_STATUS_TX_FULL   (1 << 0)  // TX FIFO full
#define UART_STATUS_TX_EMPTY  (1 << 1)  // TX FIFO empty
#define UART_STATUS_RX_FULL   (1 << 2)  // RX FIFO full
#define UART_STATUS_RX_EMPTY  (1 << 3)  // RX FIFO empty
#define UART_STATUS_RX_AVAIL  (1 << 4)  // RX data available

// UART Control register bits
#define UART_CTRL_TX_EN       (1 << 0)  // Enable transmitter
#define UART_CTRL_RX_EN       (1 << 1)  // Enable receiver

#endif // MEMORY_MAP_H
