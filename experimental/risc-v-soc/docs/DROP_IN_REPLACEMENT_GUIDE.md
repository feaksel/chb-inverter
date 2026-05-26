# Drop-In Replacement Guide: Custom RV32IM Core for VexRiscv SoC

**Document Version:** 1.0
**Date:** 2025-12-03
**Purpose:** Guide for replacing VexRiscv core while preserving all SoC infrastructure

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [VexRiscv Interface Analysis](#vexriscv-interface-analysis)
3. [Drop-In Replacement Strategy](#drop-in-replacement-strategy)
4. [Custom Core Wrapper Design](#custom-core-wrapper-design)
5. [Zpec Custom Extension Design](#zpec-custom-extension-design)
6. [Integration Checklist](#integration-checklist)
7. [Simplified Implementation Roadmap](#simplified-implementation-roadmap)
8. [Testing and Verification](#testing-and-verification)

---

## Executive Summary

### The Big Picture

You have a **working VexRiscv SoC** (`riscv-soc-vexrv/`) with:
- ✅ All peripherals working (PWM, sigma-delta ADC, UART, GPIO, protection)
- ✅ Complete firmware drivers
- ✅ Tested in simulation and hardware
- ✅ Build system and toolchain configured

**Goal:** Replace ONLY the VexRiscv core with your custom RV32IM core, keeping everything else.

### Why This Approach?

```
┌─────────────────────────────────────────────────────────┐
│                     VexRiscv SoC                        │
│  ┌────────────────┐                                     │
│  │  VexRiscv Core │  ← REPLACE THIS                    │
│  │  (black box)   │                                     │
│  └────────┬───────┘                                     │
│           │ cmd/rsp protocol                            │
│  ┌────────▼───────┐                                     │
│  │    Wrapper     │  ← KEEP THIS (or adapt slightly)   │
│  │ cmd/rsp → WB   │                                     │
│  └────────┬───────┘                                     │
│           │ Wishbone                                    │
│  ┌────────▼────────────────────────────────────────┐   │
│  │           Wishbone Interconnect                  │   │
│  └────┬─────┬─────┬──────┬──────┬──────┬──────────┘   │
│       │     │     │      │      │      │               │
│    ┌──▼─┐ ┌─▼──┐ ┌▼───┐ ┌▼───┐ ┌▼───┐ ┌▼────┐        │
│    │ROM │ │RAM │ │PWM │ │ADC │ │TIM │ │UART │ ← KEEP │
│    └────┘ └────┘ └────┘ └────┘ └────┘ └─────┘        │
└─────────────────────────────────────────────────────────┘
```

**Key Benefits:**
- 🎯 Reuse **all working peripherals** (PWM, ADC, UART, etc.)
- 🎯 Reuse **all firmware drivers** (no peripheral code changes)
- 🎯 Reuse **memory map** (addresses stay the same)
- 🎯 Reuse **build system** and toolchain
- 🎯 **Only focus on core implementation** + custom instructions

---

## VexRiscv Interface Analysis

### VexRiscv Core Interface

From `vexriscv_wrapper.v` analysis, VexRiscv core has this interface:

```verilog
module VexRiscv (
    input  wire        clk,
    input  wire        reset,  // Active HIGH reset

    // ============ Instruction Bus (iBus) - cmd/rsp protocol ============
    // Command phase: CPU requests instruction
    output wire        iBus_cmd_valid,        // CPU has valid fetch request
    input  wire        iBus_cmd_ready,        // Bus ready to accept command
    output wire [31:0] iBus_cmd_payload_pc,   // Program counter (address)

    // Response phase: Memory provides instruction
    input  wire        iBus_rsp_valid,        // Response is valid
    input  wire        iBus_rsp_payload_error,// Bus error (usually 0)
    input  wire [31:0] iBus_rsp_payload_inst, // Instruction data

    // ============ Data Bus (dBus) - cmd/rsp protocol ============
    // Command phase: CPU requests data read/write
    output wire        dBus_cmd_valid,        // CPU has valid load/store
    input  wire        dBus_cmd_ready,        // Bus ready to accept command
    output wire        dBus_cmd_payload_wr,   // 1=write, 0=read
    output wire [3:0]  dBus_cmd_payload_mask, // Byte enable (4 bits for 32-bit)
    output wire [31:0] dBus_cmd_payload_address, // Memory address
    output wire [31:0] dBus_cmd_payload_data,    // Write data
    output wire [1:0]  dBus_cmd_payload_size,    // Access size (0=byte, 1=half, 2=word)

    // Response phase: Memory provides read data
    input  wire        dBus_rsp_ready,        // Response available
    input  wire        dBus_rsp_error,        // Bus error
    input  wire [31:0] dBus_rsp_data,         // Read data

    // ============ Interrupts ============
    input  wire        timerInterrupt,        // Timer interrupt
    input  wire        externalInterrupt,     // External interrupt
    input  wire        softwareInterrupt      // Software interrupt
);
```

### cmd/rsp Protocol Explained

**Instruction Bus (iBus) - Simplified:**
```
Clock cycle:    1      2      3      4      5
              ┌───┐  ┌───┐  ┌───┐  ┌───┐  ┌───┐
CPU cmd_valid ──┘   └──────────────────────────  (CPU requests instruction)
CPU pc        ──<0x1000>──────────────────────  (PC = 0x1000)
Bus cmd_ready ─────────┘   └───────────────────  (Bus accepts)
Bus rsp_valid ─────────────────┘   └───────────  (Instruction ready)
Bus inst      ─────────────────<0x12345678>────  (Instruction data)

Timeline:
1. CPU: "I want instruction at PC=0x1000" (cmd_valid=1)
2. Bus: "OK, I see your request" (cmd_ready=1)
3. Bus: "Here's your instruction" (rsp_valid=1, inst=0x12345678)
4. CPU: Fetches next instruction
```

**Data Bus (dBus) - Read Example:**
```
Clock cycle:    1      2      3      4
              ┌───┐  ┌───┐  ┌───┐  ┌───┐
CPU cmd_valid ──┘   └─────────────────────
CPU address   ──<0x10000>────────────────  (Read from RAM)
CPU wr        ──────────────────────────── (wr=0, read)
Bus cmd_ready ─────────┘   └──────────────
Bus rsp_ready ─────────────────┘   └──────
Bus data      ─────────────────<0xABCD>───  (Data from memory)
```

**Data Bus (dBus) - Write Example:**
```
Clock cycle:    1      2      3      4
              ┌───┐  ┌───┐  ┌───┐  ┌───┐
CPU cmd_valid ──┘   └─────────────────────
CPU address   ──<0x20100>────────────────  (Write to PWM)
CPU data      ──<0x5678>─────────────────  (Write data)
CPU wr        ────────┘   └───────────────  (wr=1, write)
CPU mask      ──<1111>───────────────────  (All bytes)
Bus cmd_ready ─────────┘   └──────────────
Bus rsp_ready ─────────────────┘   └──────  (Write complete)
```

### Key Observations

1. **Handshaking:** Both command and response use valid/ready handshaking
2. **Separate buses:** Instruction and data are completely independent (Harvard architecture)
3. **Simple protocol:** Much simpler than AXI or full Wishbone
4. **Single-cycle capable:** Can complete in 2-3 clock cycles for fast memory
5. **Error handling:** Both buses have error signals (rarely used)

---

## Drop-In Replacement Strategy

### Three Approaches

#### **Approach 1: Match VexRiscv Interface Exactly (Recommended)**

Create your custom core with the **exact same cmd/rsp interface**:

```verilog
module custom_riscv_core (
    input  wire        clk,
    input  wire        reset,

    // Use IDENTICAL interface as VexRiscv
    output wire        iBus_cmd_valid,
    input  wire        iBus_cmd_ready,
    output wire [31:0] iBus_cmd_payload_pc,
    input  wire        iBus_rsp_valid,
    input  wire [31:0] iBus_rsp_payload_inst,
    // ... (same for dBus)

    // Interrupts
    input  wire        timerInterrupt,
    input  wire        externalInterrupt,
    input  wire        softwareInterrupt
);
    // Your custom RV32IM implementation here
    // + Zpec custom instructions
endmodule
```

**Then in `vexriscv_wrapper.v`, change line 108:**
```verilog
// OLD:
VexRiscv cpu (

// NEW:
custom_riscv_core cpu (
```

**That's it!** Everything else stays the same.

**Pros:**
- ✅ Zero changes to SoC infrastructure
- ✅ All peripherals work immediately
- ✅ Easiest integration
- ✅ Can test incrementally (start with RV32I, add features)

**Cons:**
- ⚠️ Must implement cmd/rsp handshaking in your core
- ⚠️ Slightly more complex core design

---

#### **Approach 2: Native Wishbone Core + Modified Wrapper**

Design your core with **native Wishbone interface**:

```verilog
module custom_riscv_core (
    input  wire        clk,
    input  wire        rst_n,

    // Wishbone instruction bus
    output wire [31:0] iwb_adr_o,
    input  wire [31:0] iwb_dat_i,
    output wire        iwb_cyc_o,
    output wire        iwb_stb_o,
    input  wire        iwb_ack_i,

    // Wishbone data bus
    output wire [31:0] dwb_adr_o,
    output wire [31:0] dwb_dat_o,
    input  wire [31:0] dwb_dat_i,
    output wire        dwb_we_o,
    output wire [3:0]  dwb_sel_o,
    output wire        dwb_cyc_o,
    output wire        dwb_stb_o,
    input  wire        dwb_ack_i,

    // Interrupts
    input  wire [31:0] interrupts
);
    // Your core with native Wishbone
endmodule
```

**Then create `custom_core_wrapper.v`** (replaces `vexriscv_wrapper.v`):
```verilog
module custom_core_wrapper (
    input  wire        clk,
    input  wire        rst_n,

    // Wishbone buses (same as vexriscv_wrapper output)
    output wire [31:0] ibus_addr,
    output wire        ibus_cyc,
    output wire        ibus_stb,
    input  wire        ibus_ack,
    input  wire [31:0] ibus_dat_i,

    output wire [31:0] dbus_addr,
    output wire [31:0] dbus_dat_o,
    input  wire [31:0] dbus_dat_i,
    output wire        dbus_we,
    output wire [3:0]  dbus_sel,
    output wire        dbus_cyc,
    output wire        dbus_stb,
    input  wire        dbus_ack,
    input  wire        dbus_err,

    input  wire [31:0] external_interrupt
);

    // Direct connection - no conversion needed!
    custom_riscv_core cpu (
        .clk(clk),
        .rst_n(rst_n),

        // Instruction bus - direct passthrough
        .iwb_adr_o(ibus_addr),
        .iwb_dat_i(ibus_dat_i),
        .iwb_cyc_o(ibus_cyc),
        .iwb_stb_o(ibus_stb),
        .iwb_ack_i(ibus_ack),

        // Data bus - direct passthrough
        .dwb_adr_o(dbus_addr),
        .dwb_dat_o(dbus_dat_o),
        .dwb_dat_i(dbus_dat_i),
        .dwb_we_o(dbus_we),
        .dwb_sel_o(dbus_sel),
        .dwb_cyc_o(dbus_cyc),
        .dwb_stb_o(dbus_stb),
        .dwb_ack_i(dbus_ack),

        .interrupts(external_interrupt)
    );

endmodule
```

**Then in `soc_top.v`, replace:**
```verilog
// OLD:
vexriscv_wrapper cpu_wrapper (

// NEW:
custom_core_wrapper cpu_wrapper (
```

**Pros:**
- ✅ Simpler core design (standard Wishbone)
- ✅ More reusable (Wishbone is universal)
- ✅ Easier to understand

**Cons:**
- ⚠️ Need to modify one more file (soc_top.v)
- ⚠️ New wrapper file to maintain

---

#### **Approach 3: Hybrid - Internal Wishbone, cmd/rsp Interface**

Design core with **internal Wishbone**, but add **cmd/rsp adapter inside the core module**:

```verilog
module custom_riscv_core (
    // External interface: cmd/rsp (matches VexRiscv)
    output wire        iBus_cmd_valid,
    // ... etc

    // Internal interface: Wishbone
    wire [31:0] internal_iwb_adr;
    wire [31:0] internal_iwb_dat;
    wire        internal_iwb_cyc;
    // ... etc

    // Internal cmd/rsp to Wishbone adapter
    cmd_rsp_to_wb ibus_adapter (
        .cmd_valid(iBus_cmd_valid),
        .cmd_ready(iBus_cmd_ready),
        // ...
        .wb_adr(internal_iwb_adr),
        .wb_dat(internal_iwb_dat),
        // ...
    );

    // Core pipeline uses Wishbone internally
    riscv_pipeline core (
        .iwb_adr_o(internal_iwb_adr),
        // ...
    );
endmodule
```

**Pros:**
- ✅ Best of both worlds
- ✅ Drop-in compatible with VexRiscv
- ✅ Internally uses standard Wishbone

**Cons:**
- ⚠️ More complex core module
- ⚠️ Extra adapter logic (small overhead)

---

### Recommendation

**Use Approach 1 or 2:**

- **Approach 1** if you want zero SoC changes (just swap the core module)
- **Approach 2** if you prefer standard Wishbone (cleaner core design)

For learning purposes, **Approach 1** is recommended because:
- You learn cmd/rsp protocol (simple and elegant)
- Zero changes to existing working SoC
- Can incrementally test

---

## Custom Core Wrapper Design

### Complete Wrapper Template (Approach 1)

Here's a complete wrapper you can use as a starting point:

```verilog
/**
 * @file custom_core_wrapper.v
 * @brief Wrapper for Custom RV32IM Core with cmd/rsp Interface
 *
 * This module wraps the custom RISC-V core to match VexRiscv interface.
 * It's designed to be a DROP-IN replacement for vexriscv_wrapper.v
 *
 * @author Custom RISC-V Core Team
 * @date 2025-12-03
 */

module custom_core_wrapper (
    input  wire        clk,
    input  wire        rst_n,

    // Wishbone Instruction Bus (to memory controller)
    output wire [31:0] ibus_addr,
    output wire        ibus_cyc,
    output wire        ibus_stb,
    input  wire        ibus_ack,
    input  wire [31:0] ibus_dat_i,

    // Wishbone Data Bus (to memory controller)
    output wire [31:0] dbus_addr,
    output wire [31:0] dbus_dat_o,
    input  wire [31:0] dbus_dat_i,
    output wire        dbus_we,
    output wire [3:0]  dbus_sel,
    output wire        dbus_cyc,
    output wire        dbus_stb,
    input  wire        dbus_ack,
    input  wire        dbus_err,

    // Interrupts
    input  wire [31:0] external_interrupt
);

    //==========================================================================
    // Reset Polarity Conversion
    //==========================================================================

    // Custom core uses active-low reset (standard), wrapper provides active-high
    wire reset = !rst_n;

    //==========================================================================
    // Custom Core Native Signals (cmd/rsp protocol)
    //==========================================================================

    // Instruction Bus
    wire        core_ibus_cmd_valid;
    wire        core_ibus_cmd_ready;
    wire [31:0] core_ibus_cmd_payload_pc;
    wire        core_ibus_rsp_valid;
    wire        core_ibus_rsp_payload_error;
    wire [31:0] core_ibus_rsp_payload_inst;

    // Data Bus
    wire        core_dbus_cmd_valid;
    wire        core_dbus_cmd_ready;
    wire        core_dbus_cmd_payload_wr;
    wire [3:0]  core_dbus_cmd_payload_mask;
    wire [31:0] core_dbus_cmd_payload_address;
    wire [31:0] core_dbus_cmd_payload_data;
    wire [1:0]  core_dbus_cmd_payload_size;
    wire        core_dbus_rsp_ready;
    wire        core_dbus_rsp_error;
    wire [31:0] core_dbus_rsp_data;

    //==========================================================================
    // Custom RISC-V Core Instantiation
    //==========================================================================

    custom_riscv_core #(
        .RESET_VECTOR(32'h00000000)  // Start of instruction memory
    ) cpu (
        .clk(clk),
        .reset(reset),

        // Instruction bus (cmd/rsp interface)
        .iBus_cmd_valid(core_ibus_cmd_valid),
        .iBus_cmd_ready(core_ibus_cmd_ready),
        .iBus_cmd_payload_pc(core_ibus_cmd_payload_pc),
        .iBus_rsp_valid(core_ibus_rsp_valid),
        .iBus_rsp_payload_error(core_ibus_rsp_payload_error),
        .iBus_rsp_payload_inst(core_ibus_rsp_payload_inst),

        // Data bus (cmd/rsp interface)
        .dBus_cmd_valid(core_dbus_cmd_valid),
        .dBus_cmd_ready(core_dbus_cmd_ready),
        .dBus_cmd_payload_wr(core_dbus_cmd_payload_wr),
        .dBus_cmd_payload_mask(core_dbus_cmd_payload_mask),
        .dBus_cmd_payload_address(core_dbus_cmd_payload_address),
        .dBus_cmd_payload_data(core_dbus_cmd_payload_data),
        .dBus_cmd_payload_size(core_dbus_cmd_payload_size),
        .dBus_rsp_ready(core_dbus_rsp_ready),
        .dBus_rsp_error(core_dbus_rsp_error),
        .dBus_rsp_data(core_dbus_rsp_data),

        // Interrupts
        .timerInterrupt(1'b0),                    // Use external timer
        .externalInterrupt(|external_interrupt),  // Any bit set
        .softwareInterrupt(1'b0)                  // Not used
    );

    //==========================================================================
    // Instruction Bus: cmd/rsp to Wishbone Adapter
    //==========================================================================

    reg ibus_active;  // Transaction in progress

    always @(posedge clk or posedge reset) begin
        if (reset) begin
            ibus_active <= 1'b0;
        end else begin
            if (core_ibus_cmd_valid && !ibus_active) begin
                // Start new transaction
                ibus_active <= 1'b1;
            end else if (ibus_ack) begin
                // Transaction complete
                ibus_active <= 1'b0;
            end
        end
    end

    // Wishbone outputs
    assign ibus_addr = core_ibus_cmd_payload_pc;
    assign ibus_cyc  = ibus_active;
    assign ibus_stb  = ibus_active;

    // Core inputs
    assign core_ibus_cmd_ready       = !ibus_active;
    assign core_ibus_rsp_valid       = ibus_ack;
    assign core_ibus_rsp_payload_inst = ibus_dat_i;
    assign core_ibus_rsp_payload_error = 1'b0;

    //==========================================================================
    // Data Bus: cmd/rsp to Wishbone Adapter
    //==========================================================================

    reg dbus_active;  // Transaction in progress

    always @(posedge clk or posedge reset) begin
        if (reset) begin
            dbus_active <= 1'b0;
        end else begin
            if (core_dbus_cmd_valid && !dbus_active) begin
                // Start new transaction
                dbus_active <= 1'b1;
            end else if (dbus_ack || dbus_err) begin
                // Transaction complete
                dbus_active <= 1'b0;
            end
        end
    end

    // Wishbone outputs
    assign dbus_addr  = core_dbus_cmd_payload_address;
    assign dbus_dat_o = core_dbus_cmd_payload_data;
    assign dbus_we    = core_dbus_cmd_payload_wr;
    assign dbus_sel   = core_dbus_cmd_payload_mask;
    assign dbus_cyc   = dbus_active;
    assign dbus_stb   = dbus_active;

    // Core inputs
    assign core_dbus_cmd_ready = !dbus_active;
    assign core_dbus_rsp_ready = dbus_ack || dbus_err;
    assign core_dbus_rsp_data  = dbus_dat_i;
    assign core_dbus_rsp_error = dbus_err;

endmodule
```

**Usage:**
1. Save this as `custom_core_wrapper.v` in `rtl/cpu/`
2. Create your `custom_riscv_core.v` with matching interface
3. In `soc_top.v`, replace `vexriscv_wrapper` with `custom_core_wrapper`

---

## Zpec Custom Extension Design

### Overview

The **Zpec** (Power electronics control) extension adds custom instructions optimized for inverter control algorithms.

### Instruction Encoding

RISC-V custom instructions use **custom-0** to **custom-3** opcodes:
```
┌────────┬────────┬────────┬────────┬────────┐
│ custom-0 : 0x0B (0001011) - Reserved for Zpec
│ custom-1 : 0x2B (0101011) - Available
│ custom-2 : 0x5B (1011011) - Available
│ custom-3 : 0x7B (1111011) - Available
└────────┴────────┴────────┴────────┴────────┘
```

**Use custom-0 (0x0B) for Zpec instructions.**

### Zpec Instruction Set

#### 1. **PR Controller Step** (`pr.step`)

**Purpose:** Execute one iteration of Proportional-Resonant controller

**Assembly Syntax:**
```assembly
pr.step rd, rs1, rs2
```

**Encoding (R-type):**
```
31      25 24   20 19   15 14   12 11    7 6      0
┌──────────┬───────┬───────┬───────┬───────┬────────┐
│ 0000000  │  rs2  │  rs1  │  000  │   rd  │ 0001011│
│ funct7   │ src2  │ src1  │funct3 │ dest  │ opcode │
└──────────┴───────┴───────┴───────┴───────┴────────┘
```

**Operation:**
```verilog
// rs1: error value (Q15 fixed-point)
// rs2: address of PR state structure in memory
// rd:  control output (Q15)

typedef struct {
    int16_t kp;           // Proportional gain (Q15)
    int16_t kr;           // Resonant gain (Q15)
    int16_t x_prev;       // Previous input x[n-1]
    int16_t x_prev2;      // Previous input x[n-2]
    int16_t y_prev;       // Previous output y[n-1]
    int16_t y_prev2;      // Previous output y[n-2]
    int16_t b0, b1, b2;   // Resonant numerator coefficients
    int16_t a1, a2;       // Resonant denominator coefficients
} pr_state_t;

// Pseudocode for pr.step:
int16_t error = (int16_t)rs1;
pr_state_t *state = (pr_state_t*)rs2;

// Proportional term: p = kp * error
int32_t p_term = ((int32_t)state->kp * error) >> 15;

// Resonant term (biquad IIR filter):
// y[n] = b0*x[n] + b1*x[n-1] + b2*x[n-2] - a1*y[n-1] - a2*y[n-2]
int32_t r_term = ((int32_t)state->b0 * error) >> 15;
r_term += ((int32_t)state->b1 * state->x_prev) >> 15;
r_term += ((int32_t)state->b2 * state->x_prev2) >> 15;
r_term -= ((int32_t)state->a1 * state->y_prev) >> 15;
r_term -= ((int32_t)state->a2 * state->y_prev2) >> 15;

// Update state
state->x_prev2 = state->x_prev;
state->x_prev = error;
state->y_prev2 = state->y_prev;
state->y_prev = (int16_t)r_term;

// Output: proportional + resonant
rd = (int16_t)(p_term + r_term);
```

**Performance:**
- Standard RV32IM: ~35 instructions, ~350 ns @ 100 MHz
- With `pr.step`: ~1 instruction, ~50 ns @ 100 MHz
- **Speedup: 7×**

**Hardware Implementation:**
```verilog
// In decode stage:
wire is_pr_step = (opcode == 7'b0001011) && (funct3 == 3'b000) && (funct7 == 7'b0000000);

// In execute stage:
if (is_pr_step) begin
    // Read state from memory (rs2 is pointer)
    pr_state <= memory[rs2>>2 +: sizeof(pr_state_t)/4];

    // Compute PR algorithm (use DSP slices for multiply)
    pr_output <= pr_compute(rs1, pr_state);

    // Write back result
    rd_data <= pr_output;

    // Update state in memory
    memory[rs2>>2 +: sizeof(pr_state_t)/4] <= pr_state_updated;
end
```

---

#### 2. **Saturating Add/Subtract** (`qadd`, `qsub`)

**Purpose:** Fixed-point arithmetic with saturation (prevent overflow)

**Assembly Syntax:**
```assembly
qadd rd, rs1, rs2   # Saturating add: rd = saturate(rs1 + rs2)
qsub rd, rs1, rs2   # Saturating subtract: rd = saturate(rs1 - rs2)
```

**Encoding:**
```
qadd: funct7=0000001, funct3=000, opcode=0001011
qsub: funct7=0000001, funct3=001, opcode=0001011
```

**Operation (Q15 format):**
```c
int16_t qadd_q15(int16_t a, int16_t b) {
    int32_t result = (int32_t)a + (int32_t)b;

    // Saturate to Q15 range: -32768 to 32767
    if (result > 32767)
        return 32767;
    else if (result < -32768)
        return -32768;
    else
        return (int16_t)result;
}
```

**Hardware:**
```verilog
wire [31:0] add_result = rs1_data + rs2_data;
wire overflow = (rs1_data[31] == rs2_data[31]) && (add_result[31] != rs1_data[31]);

assign qadd_result = overflow ? (rs1_data[31] ? 32'h8000 : 32'h7FFF)  // Saturate
                               : add_result;                           // Normal
```

---

#### 3. **Dead-Time Compensation** (`dt.comp`)

**Purpose:** Calculate voltage correction for dead-time effects

**Assembly Syntax:**
```assembly
dt.comp rd, rs1, rs2
```

**Encoding:**
```
funct7=0000010, funct3=000, opcode=0001011
```

**Operation:**
```c
// rs1: current direction (bit 0: 1=positive, 0=negative)
// rs2: dead-time in nanoseconds
// rd:  compensation voltage (Q15)

// Dead-time causes voltage error:
// V_error = (dead_time / T_pwm) * V_dc * sign(current)

int16_t dt_comp(uint32_t current_sign, uint32_t dead_time_ns) {
    // Constants (configured by CSR or hardcoded)
    const uint32_t T_PWM_NS = 100000;  // 100 us = 10 kHz
    const int16_t V_DC_Q15 = 16384;    // V_dc in Q15 (e.g., 50V = 0.5 in Q15)

    // Compute: (dead_time / T_pwm) * V_dc
    int32_t error = ((int32_t)dead_time_ns * V_DC_Q15) / T_PWM_NS;

    // Apply sign
    if (current_sign & 1)
        return (int16_t)error;
    else
        return (int16_t)(-error);
}
```

**Hardware:**
```verilog
// Dedicated divider (or use LUT for common dead-times)
wire [15:0] dt_ratio = (dead_time_ns * 32768) / T_PWM_NS;
wire [15:0] compensation = (dt_ratio * V_DC_Q15) >> 15;
assign dt_comp_result = current_sign[0] ? compensation : -compensation;
```

---

#### 4. **Atomic PWM Update** (`pwm.set`)

**Purpose:** Update all 8 PWM channels atomically (no glitches)

**Assembly Syntax:**
```assembly
pwm.set rd, rs1, rs2
```

**Encoding:**
```
funct7=0000011, funct3=000, opcode=0001011
```

**Operation:**
```c
// rs1: pointer to 8×uint16_t duty cycle array
// rs2: enable mask (bit 0-7 for channels 0-7)
// rd:  status (0=success, non-zero=error)

typedef struct {
    uint16_t ch0_duty;  // 0-1000 (0-100.0%)
    uint16_t ch1_duty;
    uint16_t ch2_duty;
    uint16_t ch3_duty;
    uint16_t ch4_duty;
    uint16_t ch5_duty;
    uint16_t ch6_duty;
    uint16_t ch7_duty;
} pwm_array_t;

void pwm_set(pwm_array_t *duties, uint8_t enable_mask) {
    // Write to hardware PWM shadow registers
    PWM_TIM0->CCR1_SHADOW = duties->ch0_duty;
    PWM_TIM0->CCR2_SHADOW = duties->ch1_duty;
    // ... etc for all 8 channels

    // Atomic update: trigger simultaneous transfer
    PWM_CTRL->UPDATE_TRIGGER = 1;  // All channels update on next PWM cycle
}
```

**Hardware:**
```verilog
// In PWM peripheral:
reg [15:0] ccr_shadow [0:7];   // Shadow registers
reg [15:0] ccr_active [0:7];   // Active registers (used by comparator)
reg update_pending;

// When pwm.set executes:
always @(posedge clk) begin
    if (pwm_set_instruction) begin
        // Load shadow registers
        for (i = 0; i < 8; i = i + 1) begin
            if (enable_mask[i])
                ccr_shadow[i] <= duty_array[i];
        end
        update_pending <= 1;
    end

    // On PWM period boundary (counter overflow)
    if (pwm_counter == 0 && update_pending) begin
        // Atomic transfer: shadow → active
        ccr_active <= ccr_shadow;
        update_pending <= 0;
    end
end
```

---

#### 5. **Parallel Fault Check** (`fault.chk`)

**Purpose:** Check multiple fault conditions in parallel

**Assembly Syntax:**
```assembly
fault.chk rd, rs1
```

**Encoding:**
```
funct7=0000100, funct3=000, opcode=0001011
```

**Operation:**
```c
// rs1: pointer to fault threshold structure
// rd:  fault status bitmask (bit 0-31 for different faults)

typedef struct {
    int16_t dc_bus1_max;        // Max DC bus 1 voltage
    int16_t dc_bus2_max;
    int16_t ac_current_max;     // Max AC current magnitude
    int16_t temperature_max;    // Max temperature
    // ... more thresholds
} fault_thresholds_t;

uint32_t fault_chk(fault_thresholds_t *thresholds) {
    uint32_t faults = 0;

    // Read sensors (parallel in hardware)
    int16_t dc_bus1 = ADC->DATA_CH0;
    int16_t dc_bus2 = ADC->DATA_CH1;
    int16_t ac_curr = ADC->DATA_CH2;

    // Parallel comparisons
    if (dc_bus1 > thresholds->dc_bus1_max)     faults |= (1 << 0);
    if (dc_bus2 > thresholds->dc_bus2_max)     faults |= (1 << 1);
    if (abs(ac_curr) > thresholds->ac_current_max) faults |= (1 << 2);
    // ... etc

    return faults;
}
```

**Hardware:**
```verilog
// Parallel comparator tree
wire [31:0] fault_bits;

assign fault_bits[0] = (adc_ch0 > threshold_0);
assign fault_bits[1] = (adc_ch1 > threshold_1);
assign fault_bits[2] = (abs(adc_ch2) > threshold_2);
// ... etc

// Single-cycle result
assign fault_chk_result = fault_bits;

// Optional: Trigger immediate interrupt if any fault
assign fault_interrupt = |fault_bits;
```

---

### Zpec CSR Registers

**Custom CSRs for Zpec configuration:**

```
CSR Address: 0x7C0 - 0x7CF (custom read/write)

0x7C0: ZPEC_CTRL      - Zpec control register
       [0]: ZPEC_ENABLE (1=enable custom instructions)
       [1]: PR_ACCEL_EN (1=enable PR accelerator)
       [2]: DT_COMP_EN  (1=enable dead-time compensation)

0x7C1: PWM_FREQ       - PWM frequency (Hz)
0x7C2: DEAD_TIME      - Dead-time (ns)
0x7C3: V_DC_BUS       - DC bus voltage (Q15)
0x7C4: FAULT_STATUS   - Current fault status (read-only)
0x7C5: FAULT_ENABLE   - Fault enable mask
```

**Usage:**
```assembly
# Enable Zpec
li t0, 0x7
csrw 0x7C0, t0        # Enable all Zpec features

# Configure dead-time
li t1, 1000           # 1000 ns
csrw 0x7C2, t1

# Read fault status
csrr t2, 0x7C4
bnez t2, fault_handler
```

---

### Complete Zpec Instruction Summary

| Mnemonic | Encoding | Cycles | Equivalent Standard Instr. | Speedup |
|----------|----------|--------|----------------------------|---------|
| `pr.step` | 0x0000000/0x000/0x0B | 5-10 | ~35 | 7× |
| `qadd` | 0x0000001/0x000/0x0B | 1 | 5 | 5× |
| `qsub` | 0x0000001/0x001/0x0B | 1 | 5 | 5× |
| `dt.comp` | 0x0000010/0x000/0x0B | 2-3 | 15 | 7× |
| `pwm.set` | 0x0000011/0x000/0x0B | 3-5 | 20 | 6× |
| `fault.chk` | 0x0000100/0x000/0x0B | 1 | 10 | 10× |

**Overall ISR Speedup:** 40-60% reduction in control loop execution time

---

## Integration Checklist

### Phase 1: Core Module Creation

- [ ] Create `custom_riscv_core.v` in `02-embedded/riscv/rtl/core/`
- [ ] Implement RV32I base ISA (40 instructions)
- [ ] Implement M extension (8 multiply/divide instructions)
- [ ] Add cmd/rsp interface (matching VexRiscv)
- [ ] Test core with simple assembly programs
- [ ] Verify against `riscv-tests` compliance suite

### Phase 2: Zpec Extension

- [ ] Add Zpec instruction decoder (6 instructions)
- [ ] Implement `qadd`/`qsub` (simplest, test first)
- [ ] Implement `pr.step` (most complex)
- [ ] Implement `dt.comp`
- [ ] Implement `pwm.set`
- [ ] Implement `fault.chk`
- [ ] Add Zpec CSR registers
- [ ] Test each instruction individually

### Phase 3: Wrapper Integration

- [ ] Copy `vexriscv_wrapper.v` to `custom_core_wrapper.v`
- [ ] Update instantiation to use `custom_riscv_core`
- [ ] Verify cmd/rsp to Wishbone conversion works
- [ ] Test with ROM/RAM access

### Phase 4: SoC Integration

- [ ] Update `soc_top.v` to use `custom_core_wrapper`
- [ ] Re-synthesize for FPGA
- [ ] Check resource utilization (should be < 30% LUTs)
- [ ] Run timing analysis (should meet 100 MHz)

### Phase 5: Firmware Testing

- [ ] Compile existing firmware with RISC-V toolchain
- [ ] Test UART (print "Hello World")
- [ ] Test GPIO (blink LED)
- [ ] Test timer interrupts
- [ ] Test ADC reading
- [ ] Test PWM output

### Phase 6: Control Algorithm

- [ ] Port PR controller from STM32
- [ ] Use `pr.step` instruction
- [ ] Port PI controller
- [ ] Port modulation calculation
- [ ] Use `pwm.set` for atomic updates
- [ ] Test full control loop @ 10 kHz

### Phase 7: Validation

- [ ] Compare with STM32 implementation
- [ ] Measure ISR execution time
- [ ] Measure control loop latency
- [ ] Run 24-hour stability test
- [ ] Validate THD < 5%

---

## Simplified Implementation Roadmap

### Timeline Overview

**Total: 8-10 weeks for full custom core + Zpec**

```
Week 1-2:  Core basics (fetch, decode, ALU)
Week 3-4:  Memory interface, branches, loads/stores
Week 5:    M extension (multiply/divide)
Week 6:    Interrupts and CSRs
Week 7:    Zpec instructions
Week 8:    Integration and testing
Week 9-10: Control algorithm porting and validation
```

---

### Week 1-2: Core Basics

**Goal:** Implement fetch, decode, register file, and basic ALU

**Tasks:**

1. **Register File** (Day 1)
   ```verilog
   module regfile (
       input  wire        clk,
       input  wire [4:0]  rs1_addr, rs2_addr, rd_addr,
       output wire [31:0] rs1_data, rs2_data,
       input  wire        wr_en,
       input  wire [31:0] rd_data
   );
       reg [31:0] regs [1:31];  // x0 is always 0

       always @(posedge clk) begin
           if (wr_en && rd_addr != 0)
               regs[rd_addr] <= rd_data;
       end

       assign rs1_data = (rs1_addr == 0) ? 32'h0 : regs[rs1_addr];
       assign rs2_data = (rs2_addr == 0) ? 32'h0 : regs[rs2_addr];
   endmodule
   ```

2. **Instruction Fetch** (Day 2-3)
   ```verilog
   module fetch_stage (
       input  wire        clk,
       input  wire        reset,
       input  wire        stall,
       input  wire        branch_taken,
       input  wire [31:0] branch_target,

       // Instruction bus (cmd/rsp)
       output reg         ibus_cmd_valid,
       input  wire        ibus_cmd_ready,
       output reg  [31:0] ibus_cmd_payload_pc,
       input  wire        ibus_rsp_valid,
       input  wire [31:0] ibus_rsp_payload_inst,

       // To decode stage
       output reg  [31:0] pc_out,
       output reg  [31:0] instruction_out
   );
       reg [31:0] pc;

       always @(posedge clk or posedge reset) begin
           if (reset) begin
               pc <= 32'h00000000;  // Reset vector
               ibus_cmd_valid <= 0;
           end else if (!stall) begin
               if (branch_taken) begin
                   pc <= branch_target;
               end else if (ibus_cmd_ready) begin
                   ibus_cmd_valid <= 1;
                   ibus_cmd_payload_pc <= pc;
               end

               if (ibus_rsp_valid) begin
                   instruction_out <= ibus_rsp_payload_inst;
                   pc_out <= pc;
                   pc <= pc + 4;  // Next instruction
               end
           end
       end
   endmodule
   ```

3. **Decode Stage** (Day 4-5)
   ```verilog
   `include "riscv_defines.vh"

   module decode_stage (
       input  wire [31:0] instruction,
       input  wire [31:0] pc,

       // Register file interface
       output wire [4:0]  rs1_addr,
       output wire [4:0]  rs2_addr,
       output wire [4:0]  rd_addr,

       // Control signals
       output reg  [3:0]  alu_op,
       output reg         alu_src_imm,  // 1=use immediate, 0=use rs2
       output reg         mem_read,
       output reg         mem_write,
       output reg         reg_write,
       output reg         branch,
       output reg         jump,

       // Immediate value
       output reg  [31:0] immediate
   );
       // Extract instruction fields
       wire [6:0] opcode = instruction[6:0];
       wire [2:0] funct3 = instruction[14:12];
       wire [6:0] funct7 = instruction[31:25];

       assign rs1_addr = instruction[19:15];
       assign rs2_addr = instruction[24:20];
       assign rd_addr  = instruction[11:7];

       // Decode logic
       always @(*) begin
           // Defaults
           alu_op = `ALU_OP_ADD;
           alu_src_imm = 0;
           mem_read = 0;
           mem_write = 0;
           reg_write = 0;
           branch = 0;
           jump = 0;
           immediate = 32'h0;

           case (opcode)
               `OPCODE_OP_IMM: begin  // ADDI, SLTI, XORI, etc.
                   alu_src_imm = 1;
                   reg_write = 1;
                   immediate = {{20{instruction[31]}}, instruction[31:20]};  // I-type imm

                   case (funct3)
                       `FUNCT3_ADD_SUB: alu_op = `ALU_OP_ADD;
                       `FUNCT3_SLT:     alu_op = `ALU_OP_SLT;
                       `FUNCT3_SLTU:    alu_op = `ALU_OP_SLTU;
                       `FUNCT3_XOR:     alu_op = `ALU_OP_XOR;
                       `FUNCT3_OR:      alu_op = `ALU_OP_OR;
                       `FUNCT3_AND:     alu_op = `ALU_OP_AND;
                       // ... more cases
                   endcase
               end

               `OPCODE_OP: begin  // ADD, SUB, MUL, etc.
                   reg_write = 1;
                   // Decode based on funct3 and funct7
                   // ...
               end

               `OPCODE_LOAD: begin
                   alu_src_imm = 1;
                   mem_read = 1;
                   reg_write = 1;
                   immediate = {{20{instruction[31]}}, instruction[31:20]};
               end

               // ... more opcodes
           endcase
       end
   endmodule
   ```

4. **ALU** (Day 6-7)
   ```verilog
   module alu (
       input  wire [31:0] operand_a,
       input  wire [31:0] operand_b,
       input  wire [3:0]  alu_op,
       output reg  [31:0] result,
       output wire        zero
   );
       always @(*) begin
           case (alu_op)
               `ALU_OP_ADD:  result = operand_a + operand_b;
               `ALU_OP_SUB:  result = operand_a - operand_b;
               `ALU_OP_AND:  result = operand_a & operand_b;
               `ALU_OP_OR:   result = operand_a | operand_b;
               `ALU_OP_XOR:  result = operand_a ^ operand_b;
               `ALU_OP_SLL:  result = operand_a << operand_b[4:0];
               `ALU_OP_SRL:  result = operand_a >> operand_b[4:0];
               `ALU_OP_SRA:  result = $signed(operand_a) >>> operand_b[4:0];
               `ALU_OP_SLT:  result = ($signed(operand_a) < $signed(operand_b)) ? 1 : 0;
               `ALU_OP_SLTU: result = (operand_a < operand_b) ? 1 : 0;
               default: result = 32'hx;
           endcase
       end

       assign zero = (result == 32'h0);
   endmodule
   ```

**Milestone:** Can execute ADD, ADDI, XOR, OR, AND instructions

---

### Week 3-4: Memory and Branches

**Goal:** Implement loads, stores, branches, and jumps

**Tasks:**

1. **Load/Store Unit** (Day 8-10)
   ```verilog
   module load_store_unit (
       input  wire        clk,
       input  wire        reset,
       input  wire        mem_read,
       input  wire        mem_write,
       input  wire [2:0]  funct3,
       input  wire [31:0] address,
       input  wire [31:0] write_data,

       // Data bus (cmd/rsp)
       output reg         dbus_cmd_valid,
       input  wire        dbus_cmd_ready,
       output reg         dbus_cmd_payload_wr,
       output reg  [3:0]  dbus_cmd_payload_mask,
       output reg  [31:0] dbus_cmd_payload_address,
       output reg  [31:0] dbus_cmd_payload_data,
       input  wire        dbus_rsp_ready,
       input  wire [31:0] dbus_rsp_data,

       output reg  [31:0] read_data
   );
       always @(posedge clk or posedge reset) begin
           if (reset) begin
               dbus_cmd_valid <= 0;
           end else begin
               if (mem_read || mem_write) begin
                   dbus_cmd_valid <= 1;
                   dbus_cmd_payload_wr <= mem_write;
                   dbus_cmd_payload_address <= address;
                   dbus_cmd_payload_data <= write_data;

                   // Byte mask based on funct3
                   case (funct3[1:0])
                       2'b00: dbus_cmd_payload_mask <= 4'b0001 << address[1:0];  // Byte
                       2'b01: dbus_cmd_payload_mask <= 4'b0011 << {address[1], 1'b0};  // Half
                       2'b10: dbus_cmd_payload_mask <= 4'b1111;  // Word
                       default: dbus_cmd_payload_mask <= 4'b0000;
                   endcase
               end

               if (dbus_rsp_ready) begin
                   // Handle sign extension for LB, LH
                   case (funct3)
                       3'b000: read_data <= {{24{dbus_rsp_data[7]}}, dbus_rsp_data[7:0]};   // LB
                       3'b001: read_data <= {{16{dbus_rsp_data[15]}}, dbus_rsp_data[15:0]}; // LH
                       3'b010: read_data <= dbus_rsp_data;                                   // LW
                       3'b100: read_data <= {24'h0, dbus_rsp_data[7:0]};                    // LBU
                       3'b101: read_data <= {16'h0, dbus_rsp_data[15:0]};                   // LHU
                       default: read_data <= 32'hx;
                   endcase
               end
           end
       end
   endmodule
   ```

2. **Branch Unit** (Day 11-12)
   ```verilog
   module branch_unit (
       input  wire [31:0] rs1_data,
       input  wire [31:0] rs2_data,
       input  wire [2:0]  funct3,
       input  wire        branch,
       input  wire        jump,
       input  wire [31:0] pc,
       input  wire [31:0] immediate,

       output reg         branch_taken,
       output reg  [31:0] branch_target
   );
       wire condition_met;

       // Branch condition evaluation
       always @(*) begin
           case (funct3)
               `FUNCT3_BEQ:  condition_met = (rs1_data == rs2_data);
               `FUNCT3_BNE:  condition_met = (rs1_data != rs2_data);
               `FUNCT3_BLT:  condition_met = ($signed(rs1_data) < $signed(rs2_data));
               `FUNCT3_BGE:  condition_met = ($signed(rs1_data) >= $signed(rs2_data));
               `FUNCT3_BLTU: condition_met = (rs1_data < rs2_data);
               `FUNCT3_BGEU: condition_met = (rs1_data >= rs2_data);
               default: condition_met = 0;
           endcase
       end

       always @(*) begin
           if (jump) begin
               branch_taken = 1;
               branch_target = pc + immediate;  // JAL
           end else if (branch && condition_met) begin
               branch_taken = 1;
               branch_target = pc + immediate;  // Bxx
           end else begin
               branch_taken = 0;
               branch_target = pc + 4;
           end
       end
   endmodule
   ```

**Milestone:** Can execute LW, SW, BEQ, BNE, JAL

---

### Week 5: M Extension

**Goal:** Add hardware multiply and divide

**Tasks:**

1. **Multiplier** (Day 13-14)
   ```verilog
   module multiplier (
       input  wire        clk,
       input  wire        reset,
       input  wire        start,
       input  wire [31:0] multiplicand,
       input  wire [31:0] multiplier,
       input  wire [2:0]  funct3,  // MUL, MULH, MULHSU, MULHU

       output reg         done,
       output reg  [31:0] result
   );
       // Use DSP slices for efficient multiplication
       wire signed [63:0] mul_ss = $signed(multiplicand) * $signed(multiplier);
       wire [63:0] mul_uu = multiplicand * multiplier;
       wire signed [63:0] mul_su = $signed(multiplicand) * {1'b0, multiplier};

       reg [1:0] state;
       localparam IDLE = 0, BUSY = 1, DONE = 2;

       always @(posedge clk or posedge reset) begin
           if (reset) begin
               state <= IDLE;
               done <= 0;
           end else begin
               case (state)
                   IDLE: begin
                       if (start) begin
                           state <= BUSY;
                           done <= 0;
                       end
                   end

                   BUSY: begin
                       // Multiply takes 3 cycles on most FPGAs
                       state <= DONE;
                   end

                   DONE: begin
                       done <= 1;
                       case (funct3)
                           3'b000: result <= mul_ss[31:0];   // MUL (lower)
                           3'b001: result <= mul_ss[63:32];  // MULH (upper, signed×signed)
                           3'b010: result <= mul_su[63:32];  // MULHSU (upper, signed×unsigned)
                           3'b011: result <= mul_uu[63:32];  // MULHU (upper, unsigned×unsigned)
                           default: result <= 32'hx;
                       endcase
                       state <= IDLE;
                   end
               endcase
           end
       end
   endmodule
   ```

2. **Divider** (Day 15-16)
   ```verilog
   // Simple non-restoring divider (32 cycles)
   module divider (
       input  wire        clk,
       input  wire        reset,
       input  wire        start,
       input  wire [31:0] dividend,
       input  wire [31:0] divisor,
       input  wire [2:0]  funct3,  // DIV, DIVU, REM, REMU

       output reg         done,
       output reg  [31:0] result
   );
       // Implement non-restoring division algorithm
       // Takes ~32 clock cycles

       // ... (implementation omitted for brevity)
       // See Patterson & Hennessy for algorithm details
   endmodule
   ```

**Milestone:** Can execute MUL, MULH, DIV, REM

---

### Week 6: Interrupts and CSRs

**Goal:** Implement interrupt controller and CSR access

**Tasks:**

1. **CSR File** (Day 17-18)
   ```verilog
   module csr_file (
       input  wire        clk,
       input  wire        reset,
       input  wire [11:0] csr_addr,
       input  wire [31:0] csr_wdata,
       input  wire [1:0]  csr_op,  // 00=none, 01=write, 10=set, 11=clear
       output reg  [31:0] csr_rdata,

       // Interrupt interface
       input  wire        external_interrupt,
       input  wire        timer_interrupt,
       output wire        interrupt_pending,
       output wire [31:0] interrupt_vector,

       // Trap handling
       input  wire        trap_entry,
       input  wire [31:0] trap_pc,
       input  wire [31:0] trap_cause,
       input  wire        mret
   );
       // CSR registers
       reg [31:0] mstatus;   // Machine status
       reg [31:0] mie;       // Machine interrupt enable
       reg [31:0] mtvec;     // Trap vector base
       reg [31:0] mepc;      // Exception PC
       reg [31:0] mcause;    // Cause register
       reg [31:0] mip;       // Interrupt pending

       // Zpec CSRs
       reg [31:0] zpec_ctrl;
       reg [31:0] pwm_freq;
       reg [31:0] dead_time;

       // CSR read
       always @(*) begin
           case (csr_addr)
               12'h300: csr_rdata = mstatus;
               12'h304: csr_rdata = mie;
               12'h305: csr_rdata = mtvec;
               12'h341: csr_rdata = mepc;
               12'h342: csr_rdata = mcause;
               12'h344: csr_rdata = mip;
               12'h7C0: csr_rdata = zpec_ctrl;
               12'h7C1: csr_rdata = pwm_freq;
               12'h7C2: csr_rdata = dead_time;
               default: csr_rdata = 32'h0;
           endcase
       end

       // CSR write
       always @(posedge clk or posedge reset) begin
           if (reset) begin
               mstatus <= 32'h0;
               mie <= 32'h0;
               mtvec <= 32'h0;
               mepc <= 32'h0;
               mcause <= 32'h0;
               zpec_ctrl <= 32'h0;
           end else begin
               // Update mip based on interrupts
               mip <= {30'h0, timer_interrupt, external_interrupt};

               // Trap entry
               if (trap_entry) begin
                   mepc <= trap_pc;
                   mcause <= trap_cause;
                   mstatus[7] <= mstatus[3];  // MPIE <= MIE
                   mstatus[3] <= 0;           // MIE <= 0 (disable interrupts)
               end

               // Return from trap
               if (mret) begin
                   mstatus[3] <= mstatus[7];  // MIE <= MPIE
                   mstatus[7] <= 1;           // MPIE <= 1
               end

               // CSR instructions
               case (csr_op)
                   2'b01: begin  // CSRRW
                       case (csr_addr)
                           12'h300: mstatus <= csr_wdata;
                           12'h304: mie <= csr_wdata;
                           12'h305: mtvec <= csr_wdata;
                           12'h7C0: zpec_ctrl <= csr_wdata;
                           // ... etc
                       endcase
                   end

                   2'b10: begin  // CSRRS (set bits)
                       case (csr_addr)
                           12'h300: mstatus <= mstatus | csr_wdata;
                           // ... etc
                       endcase
                   end

                   2'b11: begin  // CSRRC (clear bits)
                       case (csr_addr)
                           12'h300: mstatus <= mstatus & ~csr_wdata;
                           // ... etc
                       endcase
                   end
               endcase
           end
       end

       // Interrupt controller
       wire mie_bit = mstatus[3];
       wire interrupt_enabled = mie_bit && (|(mie & mip));
       assign interrupt_pending = interrupt_enabled;
       assign interrupt_vector = mtvec;

   endmodule
   ```

**Milestone:** Can handle interrupts and execute CSR instructions

---

### Week 7: Zpec Instructions

**Goal:** Implement all 6 Zpec custom instructions

**Tasks:**

1. **Decode Zpec** (Day 19)
   ```verilog
   // In decode stage, add:
   wire is_zpec = (opcode == 7'b0001011);  // custom-0

   wire is_pr_step   = is_zpec && (funct7 == 7'b0000000) && (funct3 == 3'b000);
   wire is_qadd      = is_zpec && (funct7 == 7'b0000001) && (funct3 == 3'b000);
   wire is_qsub      = is_zpec && (funct7 == 7'b0000001) && (funct3 == 3'b001);
   wire is_dt_comp   = is_zpec && (funct7 == 7'b0000010) && (funct3 == 3'b000);
   wire is_pwm_set   = is_zpec && (funct7 == 7'b0000011) && (funct3 == 3'b000);
   wire is_fault_chk = is_zpec && (funct7 == 7'b0000100) && (funct3 == 3'b000);
   ```

2. **Implement qadd/qsub** (Day 20)
   ```verilog
   module zpec_qadd_qsub (
       input  wire [31:0] a,
       input  wire [31:0] b,
       input  wire        is_sub,
       output wire [31:0] result
   );
       wire [32:0] sum = is_sub ? ({a[31], a} - {b[31], b})
                                 : ({a[31], a} + {b[31], b});

       wire overflow = sum[32] != sum[31];

       assign result = overflow ? (sum[32] ? 32'h8000 : 32'h7FFF) : sum[31:0];
   endmodule
   ```

3. **Implement pr.step** (Day 21-23)
   ```verilog
   module zpec_pr_step (
       input  wire        clk,
       input  wire        reset,
       input  wire        start,
       input  wire [15:0] error,      // Q15
       input  wire [31:0] state_addr, // Pointer to PR state in memory

       // Memory interface (to read/write state)
       output reg         mem_read,
       output reg         mem_write,
       output reg  [31:0] mem_addr,
       output reg  [31:0] mem_wdata,
       input  wire [31:0] mem_rdata,
       input  wire        mem_ready,

       output reg         done,
       output reg  [15:0] output_val  // Q15
   );
       // State machine: READ_STATE → COMPUTE → WRITE_STATE → DONE
       // ... (implementation omitted for brevity)

       // Use DSP slices for Q15 multiply:
       wire signed [31:0] q15_mult;
       assign q15_mult = ($signed(a) * $signed(b)) >>> 15;
   endmodule
   ```

4. **Implement dt.comp** (Day 24)
5. **Implement pwm.set** (Day 25)
6. **Implement fault.chk** (Day 26)

**Milestone:** All Zpec instructions working

---

### Week 8: Integration

**Goal:** Integrate core into SoC, synthesize, test

**Tasks:**

1. Replace VexRiscv in wrapper (Day 27)
2. Build for Basys3 FPGA (Day 28)
3. Fix timing issues if any (Day 29)
4. Test with simple firmware (Day 30)

---

### Week 9-10: Control Algorithm

**Goal:** Port 5-level inverter control algorithm

**Tasks:**

1. Port PR controller to use `pr.step` (Day 31-32)
2. Port modulation calculation (Day 33)
3. Test control loop @ 10 kHz (Day 34-35)
4. 24-hour stability test (Day 36-40)

---

## Testing and Verification

### Unit Tests

For each module, create testbench in `02-embedded/riscv/sim/testbenches/`:

```bash
cd 02-embedded/riscv/tools
make new-module NAME=regfile
make test MODULE=regfile
make waves MODULE=regfile
```

### ISA Compliance Tests

Use official RISC-V compliance tests:

```bash
git clone https://github.com/riscv/riscv-tests
cd riscv-tests
./configure --with-xlen=32
make

# Run tests in simulation
cd ../riscv/tools
make test PROGRAM=../../riscv-tests/isa/rv32ui-p-add
```

### Integration Tests

Test peripherals one by one:

```c
// Test UART
void test_uart() {
    uart_init(115200);
    uart_print("Hello from custom core!\n");
}

// Test PWM
void test_pwm() {
    pwm_init();
    pwm_set_duty(0, 500);  // 50% duty cycle
}

// Test ADC
void test_adc() {
    adc_init();
    uint16_t val = adc_read(ADC_CHANNEL_DC_BUS1);
    uart_printf("ADC: %d\n", val);
}
```

### Performance Benchmarks

Measure control loop timing:

```c
void control_loop_isr() {
    uint32_t start = read_cycle_counter();

    // Read ADC
    int16_t error = adc_read_q15(ADC_CHANNEL_AC_CURR);

    // PR controller (with Zpec)
    asm volatile("pr.step %0, %1, %2" : "=r"(output) : "r"(error), "r"(&pr_state));

    // Update PWM
    uint16_t duties[8] = { /* ... */ };
    asm volatile("pwm.set %0, %1, %2" : "=r"(status) : "r"(duties), "r"(0xFF));

    uint32_t end = read_cycle_counter();

    // Should be < 5000 cycles @ 100 MHz = 50 μs
    assert((end - start) < 5000);
}
```

---

## Summary

### What You Keep from VexRiscv SoC

✅ **All peripherals** (PWM, ADC, UART, GPIO, timer, protection)
✅ **Wishbone interconnect**
✅ **Memory map** (peripherals at 0x00020000+)
✅ **Firmware drivers** (sigma_delta_adc.h, pwm_accelerator.h, etc.)
✅ **Build system** (Vivado project, constraints, scripts)
✅ **Toolchain configuration** (RISC-V GCC, linker scripts)

### What You Replace

🔄 **VexRiscv core** → **Custom RV32IM core**
🔄 **cmd/rsp wrapper** (or reuse with custom core)

### What You Add

➕ **Zpec custom instructions** (pr.step, qadd, qsub, dt.comp, pwm.set, fault.chk)
➕ **Zpec CSRs** (configuration registers)
➕ **Performance gains** (40-60% faster control loop)

### Development Effort

- **Core implementation:** 6-8 weeks
- **Zpec extension:** 1-2 weeks
- **Integration & testing:** 1-2 weeks
- **Total:** 8-12 weeks

---

## Next Steps

1. **Review this guide** thoroughly
2. **Choose approach** (cmd/rsp interface or Wishbone native)
3. **Start with Week 1** (register file + ALU)
4. **Test incrementally** (don't wait until everything is done)
5. **Use existing tools** (Makefile, testbenches from IMPLEMENTATION_ROADMAP.md)

---

**Document Status:** ✅ Ready for Implementation
**Last Updated:** 2025-12-03
**Version:** 1.0
