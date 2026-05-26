# Custom RISC-V Core Requirements for 5-Level Inverter

**Document Version:** 1.0
**Date:** 2025-12-03
**Stage:** Planning for Stage 4 Implementation

---

## Table of Contents

1. [Overview](#overview)
2. [Core Architecture Requirements](#core-architecture-requirements)
3. [ISA Selection](#isa-selection)
4. [Custom Instructions](#custom-instructions)
5. [Peripheral Integration](#peripheral-integration)
6. [Memory Architecture](#memory-architecture)
7. [Toolchain Setup](#toolchain-setup)
8. [Performance Requirements](#performance-requirements)
9. [Implementation Options](#implementation-options)
10. [Migration Path from STM32](#migration-path-from-stm32)

---

## Overview

### Purpose

This document outlines the requirements for implementing a **custom RISC-V soft-core processor** for the 5-level cascaded H-bridge inverter control system. The custom core will replace the STM32F401RE microcontroller in Stage 4 of the project.

### Design Goals

1. **Real-time Performance**: Execute 10 kHz control loop with deterministic timing
2. **Power Efficiency**: Optimize for power electronics control algorithms
3. **Extensibility**: Support custom instructions for inverter-specific operations
4. **Educational Value**: Demonstrate complete hardware/software co-design
5. **ASIC Preparation**: Architecture should be suitable for future ASIC implementation

### Key Specifications

| Parameter | Requirement | Notes |
|-----------|-------------|-------|
| Control Loop Frequency | 10 kHz | 100 μs period |
| ISR Latency | < 500 ns | Interrupt to first instruction |
| Control Algorithm Execution | < 50 μs | Leave headroom for safety checks |
| PWM Resolution | ≥ 10 bits | At 10 kHz switching frequency |
| ADC Sampling | 10 kHz | Synchronized with PWM |
| Clock Frequency | ≥ 50 MHz | Typical: 50-100 MHz for FPGA |

---

## Core Architecture Requirements

### 1. Base Processor Core

**Recommended Starting Point:**
- **Custom design** from scratch (most educational)
- **OR modify existing open-source core:**
  - PicoRV32 (simple, well-documented)
  - SERV (bit-serial, area-optimized)
  - VexRiscv (configurable, good performance)
  - Rocket Chip (complex but feature-rich)

**Core Pipeline:**
```
Option A: Simple 3-stage pipeline
┌─────────┐    ┌─────────┐    ┌─────────┐
│  Fetch  │───▶│ Decode/ │───▶│ Write-  │
│         │    │ Execute │    │  back   │
└─────────┘    └─────────┘    └─────────┘

Option B: 5-stage pipeline (better performance)
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│  Fetch  │───▶│ Decode  │───▶│ Execute │───▶│ Memory  │───▶│ Write-  │
│         │    │         │    │         │    │         │    │  back   │
└─────────┘    └─────────┘    └─────────┘    └─────────┘    └─────────┘
```

**Recommended for Inverter Control:** 3-stage pipeline
- Simpler design, easier verification
- Lower latency for interrupts
- Sufficient performance for 10 kHz control

### 2. Critical Features

#### A. Interrupt Controller

```
Priority Levels (highest to lowest):
1. Hardware Fault / Overcurrent (NMI-style)
2. ADC Conversion Complete
3. Timer Overflow (control loop trigger)
4. UART RX/TX
5. GPIO
```

**Requirements:**
- **Fast interrupt response**: < 10 clock cycles from assertion to first instruction
- **Nested interrupts**: Allow higher priority to preempt
- **Vector table**: Direct jump to ISR (no software dispatch)
- **Interrupt masking**: Global and per-interrupt enable

#### B. Timer Units

```
Timer 0: PWM Generation for H-Bridge 1 (S1-S4)
├── 16-bit counter
├── 4 compare registers (CH1, CH1N, CH2, CH2N)
├── Dead-time insertion logic
└── Automatic reload

Timer 1: PWM Generation for H-Bridge 2 (S5-S8)
├── Same structure as Timer 0
└── Phase-synchronized with Timer 0

Timer 2: System Timer
├── 32-bit free-running counter
└── Timestamp generation
```

**Dead-time Insertion Logic:**
```verilog
// Pseudocode for dead-time generation
if (pwm_signal_rising_edge) begin
    output_high_side <= 0;           // Turn off high side
    dead_time_counter <= DEADTIME;    // Start dead-time counter
end

if (dead_time_counter == 0 && pwm_signal == 1) begin
    output_high_side <= 1;           // Turn on high side after dead-time
end

// Similar logic for falling edge and low side
```

#### C. Register File

```
Standard RISC-V:
x0      : Always zero
x1      : Return address
x2 (sp) : Stack pointer
x3 (gp) : Global pointer
x4 (tp) : Thread pointer
x5-x7   : Temporaries
x8-x9   : Saved registers / frame pointer
x10-x17 : Function arguments / return values
x18-x27 : Saved registers
x28-x31 : Temporaries

Optimization: Fast context save/restore for ISR
```

#### D. ALU Features

```
Required Operations:
├── Arithmetic: ADD, SUB, (MUL, DIV if RV32M)
├── Logic: AND, OR, XOR, shifts
├── Comparison: SLT, SLTU
└── Branch: BEQ, BNE, BLT, BGE, BLTU, BGEU

For Control Algorithms:
├── Fixed-point multiply (Q15 or Q31 format)
├── Saturating arithmetic (optional custom instructions)
└── Fast accumulate operations
```

---

## ISA Selection

### Recommended: RV32IMC

```
RV32I   : Base integer instruction set
      M : Hardware multiply/divide
      C : Compressed instructions (16-bit)
```

**Rationale:**

1. **RV32I**: Essential base functionality
2. **M Extension**: Control algorithms require multiply/divide
   - PR controller: Multiple multiplications per sample
   - PI controller: Ki * integral accumulation
   - Fixed-point scaling
3. **C Extension**: Reduces code size by ~30%
   - Important for limited FPGA BRAM
   - Slightly better performance

### Optional Extensions

```
F : Single-precision floating-point
    └── Pros: Easier porting from STM32 (uses floats)
    └── Cons: Significant area increase, slower
    └── Decision: NOT recommended - use fixed-point

D : Double-precision floating-point
    └── Decision: NOT needed for this application

Zicsr : CSR instructions (CSRRW, CSRRS, CSRRC)
    └── Decision: REQUIRED for interrupt handling

Zifencei : Instruction fence
    └── Decision: Optional, useful for debugging
```

### Custom Extension: Zpec (Power Electronics Control)

Proposed custom instructions for inverter control:

```assembly
# Custom instruction format (R-type)
# .insn r opcode, func3, func7, rd, rs1, rs2

# 1. PR Controller Step
#    Executes one iteration of PR controller
#    rd = Kp*error + resonant_term
pr.step  rd, rs1, rs2
    # rs1 = error (Q15)
    # rs2 = pointer to PR state structure
    # rd  = control output (Q15)

# 2. Dead-time Compensation
#    Calculates voltage correction for dead-time effect
dt.comp  rd, rs1, rs2
    # rs1 = current direction (sign bit)
    # rs2 = dead-time in cycles
    # rd  = compensation voltage (Q15)

# 3. PWM Duty Update (Atomic)
#    Updates all 8 PWM channels atomically
pwm.set  rd, rs1, rs2
    # rs1 = pointer to duty cycle array (8x uint16)
    # rs2 = enable mask (8 bits)
    # rd  = status/error code

# 4. Fast Saturation
#    Saturating add/subtract for Q15 fixed-point
qadd     rd, rs1, rs2   # Saturating add
qsub     rd, rs1, rs2   # Saturating subtract

# 5. Fault Check
#    Parallel check of multiple fault conditions
fault.chk rd, rs1
    # rs1 = pointer to fault threshold structure
    # rd  = fault status bitmask
```

**Implementation Impact:**
- Each custom instruction saves 5-20 standard instructions
- Reduces ISR execution time by 30-50%
- Total area increase: ~5-10% of core

---

## Peripheral Integration

### System Architecture

```
                    ┌─────────────────────────────┐
                    │   Custom RISC-V Core        │
                    │  - RV32IMC + Zpec           │
                    │  - 3-stage pipeline         │
                    │  - Interrupt controller     │
                    └──────────┬──────────────────┘
                               │
                ┌──────────────┴──────────────┐
                │   System Bus (Wishbone)     │
                │   32-bit address/data       │
                └──┬────┬────┬────┬────┬─────┘
                   │    │    │    │    │
        ┌──────────┘    │    │    │    └───────────┐
        │               │    │    │                 │
   ┌────▼────┐   ┌─────▼──┐ │ ┌──▼───┐      ┌─────▼─────┐
   │ Instr.  │   │ Data   │ │ │ UART │      │   GPIO    │
   │ Memory  │   │ Memory │ │ └──────┘      │  - LEDs   │
   │ 64 KB   │   │ 64 KB  │ │               │  - Faults │
   └─────────┘   └────────┘ │               └───────────┘
                             │
                    ┌────────┴────────┐
                    │                 │
              ┌─────▼─────┐     ┌────▼─────┐
              │ PWM Timer │     │   ADC    │
              │  Module   │     │Interface │
              │ - TIM0    │     │ - 4 ch   │
              │ - TIM1    │     │ - 10kHz  │
              │ - Dead-   │     │ - DMA    │
              │   time    │     └──────────┘
              └───────────┘
                    │
           ┌────────┴────────┐
           │                 │
    ┌──────▼──────┐   ┌──────▼──────┐
    │ H-Bridge 1  │   │ H-Bridge 2  │
    │ S1, S2, S3, │   │ S5, S6, S7, │
    │ S4          │   │ S8          │
    │ (PWM + PWMn)│   │ (PWM + PWMn)│
    └─────────────┘   └─────────────┘
```

### Bus Standard Options

#### Option A: Wishbone B4 (Recommended)

**Pros:**
- Simple, well-documented
- Many open-source IP cores available
- Easy to implement and verify

**Cons:**
- Slightly lower performance than AXI

**Signals:**
```verilog
// Wishbone master signals
output [31:0] wb_adr_o,   // Address
output [31:0] wb_dat_o,   // Data to peripheral
input  [31:0] wb_dat_i,   // Data from peripheral
output        wb_we_o,    // Write enable
output        wb_stb_o,   // Strobe
output        wb_cyc_o,   // Cycle
input         wb_ack_i    // Acknowledge
```

#### Option B: AXI4-Lite

**Pros:**
- Industry standard
- Better performance for complex systems

**Cons:**
- More complex to implement
- Overkill for this application

**Recommendation:** Use Wishbone for simplicity and educational value.

### Memory Map (Detailed)

```
┌─────────────────────────────────────────────────────┐
│ 0x0000_0000 - 0x0000_FFFF │ Instruction Memory      │
│                            │ (64 KB BRAM)            │
├─────────────────────────────────────────────────────┤
│ 0x0001_0000 - 0x0001_FFFF │ Data Memory             │
│                            │ (64 KB BRAM)            │
├─────────────────────────────────────────────────────┤
│ 0x4000_0000 - 0x4000_00FF │ PWM Timer 0 (H-Bridge 1)│
│   0x00: CNT                │ Counter value           │
│   0x04: ARR                │ Auto-reload register    │
│   0x08: CCR1               │ Capture/Compare 1       │
│   0x0C: CCR2               │ Capture/Compare 2       │
│   0x10: DEADTIME           │ Dead-time config        │
│   0x14: CR                 │ Control register        │
│   0x18: SR                 │ Status register         │
├─────────────────────────────────────────────────────┤
│ 0x4000_0100 - 0x4000_01FF │ PWM Timer 1 (H-Bridge 2)│
│                            │ (Same layout as Timer 0)│
├─────────────────────────────────────────────────────┤
│ 0x4000_0200 - 0x4000_02FF │ System Timer            │
│   0x00: CNT_LOW            │ Counter low 32 bits     │
│   0x04: CNT_HIGH           │ Counter high 32 bits    │
│   0x08: CTRL               │ Control register        │
├─────────────────────────────────────────────────────┤
│ 0x4000_1000 - 0x4000_10FF │ ADC Controller          │
│   0x00: ADC_CH0            │ Current sensor 1        │
│   0x04: ADC_CH1            │ Current sensor 2        │
│   0x08: ADC_CH2            │ Voltage sensor 1        │
│   0x0C: ADC_CH3            │ Voltage sensor 2        │
│   0x10: ADC_CR             │ Control register        │
│   0x14: ADC_SR             │ Status register         │
│   0x18: ADC_IER            │ Interrupt enable        │
├─────────────────────────────────────────────────────┤
│ 0x4000_2000 - 0x4000_20FF │ UART                    │
│   0x00: DATA               │ TX/RX data register     │
│   0x04: STATUS             │ Status flags            │
│   0x08: BAUD_DIV           │ Baud rate divisor       │
│   0x0C: CTRL               │ Control register        │
├─────────────────────────────────────────────────────┤
│ 0x4000_3000 - 0x4000_30FF │ GPIO / Fault Logic      │
│   0x00: GPIO_OUT           │ Output data             │
│   0x04: GPIO_IN            │ Input data              │
│   0x08: GPIO_DIR           │ Direction register      │
│   0x0C: FAULT_STATUS       │ Fault status flags      │
│   0x10: FAULT_MASK         │ Fault enable mask       │
│   0x14: FAULT_THRESHOLD    │ Fault thresholds        │
├─────────────────────────────────────────────────────┤
│ 0x4000_4000 - 0x4000_40FF │ Interrupt Controller    │
│   0x00: IER                │ Interrupt enable        │
│   0x04: IPR                │ Interrupt pending       │
│   0x08: PRIORITY           │ Priority configuration  │
│   0x0C: VECTOR_TABLE       │ Vector table base       │
└─────────────────────────────────────────────────────┘
```

---

## Memory Architecture

### Requirements

**Instruction Memory:**
- Size: 64 KB (should fit control algorithm)
- Type: BRAM (Block RAM on FPGA)
- Access: Single-cycle read
- Interface: Dedicated instruction bus (Harvard architecture)

**Data Memory:**
- Size: 64 KB
- Type: BRAM
- Access: Single-cycle read/write
- Interface: Dedicated data bus

**Why Harvard Architecture?**
- Allows simultaneous instruction fetch and data access
- Better performance for control loops
- Simpler pipeline design

### Memory Organization

```
Instruction Memory (64 KB):
├── 0x0000 - 0x00FF : Vector table (256 bytes)
├── 0x0100 - 0x7FFF : Application code (~32 KB typical)
└── 0x8000 - 0xFFFF : Reserved for future expansion

Data Memory (64 KB):
├── 0x10000 - 0x100FF : Stack (grows down, 256 bytes min)
├── 0x10100 - 0x102FF : Heap (if needed)
├── 0x10300 - 0x103FF : Control algorithm variables
│   ├── PR controller state (64 bytes)
│   ├── PI controller state (32 bytes)
│   ├── Reference signals (64 bytes)
│   └── Measurement buffers (128 bytes)
├── 0x10400 - 0x104FF : PWM duty cycle arrays
├── 0x10500 - 0x105FF : ADC sample buffers
└── 0x10600 - 0x1FFFF : General purpose
```

---

## Toolchain Setup

### 1. RISC-V GNU Toolchain

**Installation:**
```bash
# Clone RISC-V GNU toolchain
git clone https://github.com/riscv/riscv-gnu-toolchain
cd riscv-gnu-toolchain

# Configure for RV32IMC
./configure --prefix=/opt/riscv --with-arch=rv32imc --with-abi=ilp32

# Build (takes ~1 hour)
make

# Add to PATH
export PATH=/opt/riscv/bin:$PATH
```

**Verify Installation:**
```bash
riscv32-unknown-elf-gcc --version
riscv32-unknown-elf-objdump --version
```

### 2. Linker Script

Create `inverter_riscv.ld`:

```ld
OUTPUT_ARCH("riscv")
ENTRY(_start)

MEMORY
{
    IMEM (rx)  : ORIGIN = 0x00000000, LENGTH = 64K
    DMEM (rw)  : ORIGIN = 0x00010000, LENGTH = 64K
}

SECTIONS
{
    .text : {
        *(.text.init)      /* Startup code */
        *(.text)           /* Program code */
        *(.rodata)         /* Read-only data */
    } > IMEM

    .data : {
        __data_start = .;
        *(.data)           /* Initialized data */
        __data_end = .;
    } > DMEM

    .bss : {
        __bss_start = .;
        *(.bss)            /* Uninitialized data */
        *(COMMON)
        __bss_end = .;
    } > DMEM

    .stack : {
        . = ALIGN(16);
        __stack_start = .;
        . = . + 4K;        /* 4KB stack */
        __stack_end = .;
    } > DMEM
}
```

### 3. Startup Code

Create `startup.S`:

```assembly
.section .text.init
.global _start

_start:
    # Initialize stack pointer
    la sp, __stack_end

    # Clear BSS section
    la t0, __bss_start
    la t1, __bss_end
clear_bss:
    beq t0, t1, clear_bss_done
    sw zero, 0(t0)
    addi t0, t0, 4
    j clear_bss
clear_bss_done:

    # Copy .data section from ROM to RAM (if needed)
    # (Skip if Harvard architecture with separate instruction/data memory)

    # Set up trap vector
    la t0, trap_vector
    csrw mtvec, t0

    # Enable interrupts
    li t0, 0x1880      # MIE bit
    csrs mstatus, t0

    # Jump to main
    call main

    # Halt if main returns
hang:
    j hang

# Trap handler
.align 4
trap_vector:
    # Save context
    addi sp, sp, -64
    sw x1, 0(sp)
    sw x5, 4(sp)
    sw x6, 8(sp)
    # ... save other registers ...

    # Call C interrupt handler
    call trap_handler

    # Restore context
    lw x1, 0(sp)
    lw x5, 4(sp)
    # ... restore other registers ...
    addi sp, sp, 64

    mret
```

### 4. Makefile

```makefile
# RISC-V Toolchain
PREFIX = riscv32-unknown-elf-
CC = $(PREFIX)gcc
OBJDUMP = $(PREFIX)objdump
OBJCOPY = $(PREFIX)objcopy

# Flags
ARCH = rv32imc
ABI = ilp32
CFLAGS = -march=$(ARCH) -mabi=$(ABI) -O2 -g -Wall
LDFLAGS = -T inverter_riscv.ld -nostdlib -nostartfiles

# Source files
SRCS = startup.S main.c pwm_control.c current_controller.c
OBJS = $(SRCS:.c=.o)
OBJS := $(OBJS:.S=.o)

# Outputs
ELF = inverter.elf
BIN = inverter.bin
HEX = inverter.hex
LST = inverter.lst

all: $(ELF) $(BIN) $(HEX) $(LST)

$(ELF): $(OBJS)
	$(CC) $(CFLAGS) $(LDFLAGS) -o $@ $^

$(BIN): $(ELF)
	$(OBJCOPY) -O binary $< $@

$(HEX): $(ELF)
	$(OBJCOPY) -O verilog $< $@

$(LST): $(ELF)
	$(OBJDUMP) -d $< > $@

%.o: %.c
	$(CC) $(CFLAGS) -c -o $@ $<

%.o: %.S
	$(CC) $(CFLAGS) -c -o $@ $<

clean:
	rm -f $(OBJS) $(ELF) $(BIN) $(HEX) $(LST)

.PHONY: all clean
```

---

## Performance Requirements

### Timing Analysis

**10 kHz Control Loop Breakdown:**

```
Total period: 100 μs

┌─────────────────────────────────────────────────┐
│ ADC Conversion               │ 10 μs            │
├─────────────────────────────────────────────────┤
│ Interrupt Latency            │ 0.5 μs           │
├─────────────────────────────────────────────────┤
│ ADC Read (4 channels)        │ 2 μs             │
├─────────────────────────────────────────────────┤
│ Current Controller (PR)      │ 15 μs            │
├─────────────────────────────────────────────────┤
│ Voltage Controller (PI)      │ 5 μs             │
├─────────────────────────────────────────────────┤
│ Modulation Calculation       │ 8 μs             │
├─────────────────────────────────────────────────┤
│ PWM Update (8 channels)      │ 3 μs             │
├─────────────────────────────────────────────────┤
│ Safety Checks                │ 5 μs             │
├─────────────────────────────────────────────────┤
│ Overhead / Margin            │ 1.5 μs           │
├─────────────────────────────────────────────────┤
│ TOTAL ISR Time               │ 50 μs            │
└─────────────────────────────────────────────────┘

Remaining time for background tasks: 50 μs
CPU Utilization: 50%
```

### Clock Frequency Calculation

**Assuming 50 μs ISR with ~2500 instructions:**

```
Clock cycles needed = 2500 instructions × 1.5 CPI (cycles per instruction)
                    = 3750 cycles

Frequency = 3750 cycles / 50 μs = 75 MHz

Recommended: 100 MHz (provides margin)
```

### Instruction Count Estimates

**Current Controller (PR) - Per Sample:**

```c
// Pseudocode
float pr_controller(float error, pr_state_t *state) {
    // Proportional term: 2 instructions
    float p_term = state->kp * error;

    // Resonant term (biquad filter): ~30 instructions
    // y[n] = b0*x[n] + b1*x[n-1] + b2*x[n-2] - a1*y[n-1] - a2*y[n-2]
    float resonant = compute_biquad(error, &state->resonant);

    // Output: 1 instruction
    return p_term + resonant;
}

Total: ~35 instructions (with RV32IM multiply/divide)
At 100 MHz: 35 × 10ns = 350 ns
```

**With Custom `pr.step` Instruction:**
- Reduction to ~5 instructions
- At 100 MHz: 50 ns (7× speedup!)

---

## Implementation Options

### Option 1: Minimal Custom Core (Recommended for Learning)

**Features:**
- Simple 3-stage pipeline (Fetch, Decode/Execute, Writeback)
- RV32I base ISA only
- Software multiply/divide
- Basic interrupt controller
- ~1500-2000 lines of Verilog

**Pros:**
- Easiest to understand and verify
- Complete control over every aspect
- Best educational value

**Cons:**
- Lower performance (software multiply)
- May need higher clock frequency

**Estimated Development Time:** 4-6 weeks

### Option 2: RV32IM Custom Core

**Features:**
- 3-stage pipeline
- Hardware multiply/divide
- Interrupt controller with vectoring
- ~2500-3000 lines of Verilog

**Pros:**
- Much better performance for control algorithms
- Still manageable complexity

**Cons:**
- Multiplier takes significant FPGA resources
- More complex to verify

**Estimated Development Time:** 6-8 weeks

### Option 3: Modified PicoRV32

**Features:**
- Start with PicoRV32 core (open-source, well-tested)
- Add custom instructions for inverter control
- Integrate custom peripherals

**Pros:**
- Faster development
- Pre-verified core
- Good documentation

**Cons:**
- Less educational (less from-scratch design)
- May need to understand existing codebase

**Estimated Development Time:** 3-4 weeks

### Option 4: VexRiscv Configuration

**Features:**
- Use VexRiscv generator (Scala/SpinalHDL)
- Configure for RV32IMC
- Add custom peripherals

**Pros:**
- Highly configurable
- Good performance
- Active community

**Cons:**
- Requires learning SpinalHDL
- Less control over micro-architecture

**Estimated Development Time:** 2-3 weeks (if familiar with SpinalHDL)

### Recommendation

**For Maximum Educational Value:**
→ **Option 2: Custom RV32IM Core**

**For Faster Implementation:**
→ **Option 3: Modified PicoRV32**

---

## Migration Path from STM32

### Step 1: Hardware Abstraction Layer (HAL)

**Current STM32 Code:**
```c
// STM32-specific
HAL_TIM_PWM_Start(&htim1, TIM_CHANNEL_1);
```

**Portable HAL:**
```c
// Platform-agnostic
pwm_start(PWM_CHANNEL_1);
```

**Implementation:**
```c
// stm32/hal_pwm.c
void pwm_start(pwm_channel_t channel) {
    HAL_TIM_PWM_Start(&htim1, channel);
}

// riscv/hal_pwm.c
void pwm_start(pwm_channel_t channel) {
    volatile uint32_t *ctrl_reg = (uint32_t*)(PWM_BASE + PWM_CR);
    *ctrl_reg |= (1 << channel);
}
```

### Step 2: Fixed-Point Conversion

**STM32 uses floating-point (with FPU):**
```c
float pr_controller(float error) {
    return kp * error + resonant_term;
}
```

**RISC-V uses fixed-point (Q15 format):**
```c
int16_t pr_controller_q15(int16_t error) {
    // Q15 multiply: (a * b) >> 15
    int32_t p_term = ((int32_t)kp_q15 * error) >> 15;
    return (int16_t)(p_term + resonant_term_q15);
}
```

**Use compile-time selection:**
```c
#ifdef USE_FIXED_POINT
    typedef int16_t control_t;
    #define CONTROL_SCALE 32768
#else
    typedef float control_t;
    #define CONTROL_SCALE 1.0f
#endif
```

### Step 3: Peripheral Mapping

**Create unified peripheral interface:**

```c
// peripheral.h
#ifdef PLATFORM_STM32
    #include "stm32f4xx_hal.h"
    #define PWM_TIM1_BASE TIM1_BASE
#elif PLATFORM_RISCV
    #define PWM_TIM1_BASE 0x40000000
#endif

// Access peripherals consistently
typedef struct {
    volatile uint32_t CNT;
    volatile uint32_t ARR;
    volatile uint32_t CCR1;
    // ...
} pwm_timer_t;

#define PWM_TIMER1 ((pwm_timer_t*)PWM_TIM1_BASE)
```

### Step 4: Testing Strategy

1. **Unit test control algorithms in MATLAB** (golden reference)
2. **Test STM32 implementation** against MATLAB
3. **Port to RISC-V fixed-point**
4. **Test RISC-V in simulation** (Verilator/ModelSim)
5. **Compare RISC-V results with STM32** (should match within quantization error)
6. **Deploy to FPGA** and validate with hardware

---

## Next Steps

### Immediate Actions (Planning Phase)

1. **Choose Implementation Option**
   - Decide: Custom core vs. Modified existing core
   - Consider: Development time, learning goals, performance needs

2. **Set Up Development Environment**
   - Install RISC-V toolchain
   - Install FPGA tools (Vivado/Quartus)
   - Set up simulation environment (Verilator recommended)

3. **Design Review**
   - Review this document with team
   - Finalize ISA selection and custom instructions
   - Create detailed schedule

4. **Create Test Infrastructure**
   - Set up RISC-V instruction set simulator (Spike)
   - Create test vectors from MATLAB reference
   - Prepare verification framework

### Development Phases

**Phase 1: Core Development (3-6 weeks)**
- Implement RISC-V core (or modify existing)
- Verify with ISA compliance tests
- Simulate basic programs

**Phase 2: Peripheral Integration (2-3 weeks)**
- Design PWM timer module
- Design ADC interface
- Integrate with core via bus

**Phase 3: Software Porting (2-3 weeks)**
- Port control algorithms to RISC-V
- Create HAL for RISC-V platform
- Test in simulation

**Phase 4: FPGA Deployment (1-2 weeks)**
- Synthesize for target FPGA
- Timing analysis and optimization
- Hardware bring-up

**Phase 5: Validation (2-3 weeks)**
- Compare with STM32 implementation
- Measure performance and resource usage
- Full inverter testing

**Total Estimated Time:** 10-17 weeks

---

## Resource Estimates

### FPGA Resources (Xilinx Artix-7 Example)

**Custom RV32IM Core:**
```
LUTs (Logic):        ~3,000 - 5,000
Flip-Flops:          ~2,000 - 3,000
Block RAM (36Kb):    4 (for 128KB total memory)
DSP Slices:          3-4 (for hardware multiplier)

Example: Artix-7 XC7A35T has:
- 33,280 LUTs
- 41,600 FFs
- 50 BRAMs (1,800 Kb)
- 90 DSP slices

Core utilization: ~15% LUTs, ~5% FFs, ~8% BRAM, ~4% DSP
Plenty of room for peripherals and expansion!
```

**With Custom Zpec Instructions:**
```
Additional LUTs:     ~500 - 1,000
Additional FFs:      ~300 - 500
Additional DSP:      1-2

Total utilization:   ~18% LUTs, ~6% FFs, ~8% BRAM, ~6% DSP
```

### Power Consumption

**Estimated (Artix-7 @ 100 MHz):**
- Core: ~50-100 mW
- Memory: ~50 mW
- Peripherals: ~30 mW
- Clock network: ~20 mW
- **Total: ~150-200 mW** (much lower than STM32!)

---

## References

### RISC-V Specifications
- RISC-V ISA Manual: https://riscv.org/technical/specifications/
- RISC-V Privileged Architecture: https://riscv.org/specifications/privileged-isa/

### Open-Source Cores
- PicoRV32: https://github.com/YosysHQ/picorv32
- VexRiscv: https://github.com/SpinalHDL/VexRiscv
- SERV: https://github.com/olofk/serv
- Rocket Chip: https://github.com/chipsalliance/rocket-chip

### Tools
- RISC-V GNU Toolchain: https://github.com/riscv/riscv-gnu-toolchain
- Spike ISA Simulator: https://github.com/riscv/riscv-isa-sim
- Verilator (for simulation): https://www.veripool.org/verilator/

### Learning Resources
- "Computer Organization and Design RISC-V Edition" by Patterson & Hennessy
- "Digital Design and Computer Architecture: RISC-V Edition" by Harris & Harris
- RISC-V Online Courses: edX, Coursera

---

## Conclusion

Implementing a custom RISC-V core for the 5-level inverter is both **feasible and educational**. The key requirements are:

✅ **RV32IMC ISA** - Sufficient for control algorithms
✅ **100 MHz clock** - Meets timing requirements
✅ **Custom instructions** (optional) - 30-50% performance boost
✅ **Dedicated peripherals** - PWM, ADC, interrupts
✅ **Harvard architecture** - Simplified memory access

**The project will successfully transition from STM32 to custom RISC-V while maintaining real-time performance for the 10 kHz control loop.**

**Next:** Review this document, choose implementation option, and begin Phase 1 development.

---

**Document Status:** ✅ Ready for Review
**Approval Required:** Yes - before starting implementation
**Last Updated:** 2025-12-03
