# CSR and Compliance Implementation Guide

**Document Version:** 1.0
**Date:** 2025-12-08
**Stage:** CSR, Interrupts, Exceptions, and Compliance Testing
**Prerequisite:** Completed RV32I + M Extension

---

## Table of Contents

1. [Overview](#overview)
2. [CSR (Control and Status Registers)](#csr-control-and-status-registers)
3. [Privileged Architecture](#privileged-architecture)
4. [Exception Handling](#exception-handling)
5. [Interrupt Handling](#interrupt-handling)
6. [System Instructions](#system-instructions)
7. [Integration with Core](#integration-with-core)
8. [Testing Strategy](#testing-strategy)
9. [RISC-V Compliance Tests](#risc-v-compliance-tests)
10. [Debugging Guide](#debugging-guide)

---

## Overview

### What You'll Implement

This guide covers the final pieces to complete a fully functional RV32IM core:

**Phase 1: CSR Unit (8-10 hours)**
- Control and Status Register file
- CSR read/write/set/clear operations
- Machine-mode CSRs (mstatus, mie, mip, mtvec, mepc, mcause, etc.)

**Phase 2: Exception Handling (6-8 hours)**
- Exception detection (illegal instruction, misaligned access, etc.)
- Trap entry (save PC, update CSRs, jump to handler)
- Trap return (restore state, return from handler)

**Phase 3: Interrupt Handling (8-10 hours)**
- Interrupt controller
- External interrupts
- Timer interrupts
- Software interrupts
- Interrupt priority and masking

**Phase 4: System Instructions (4-6 hours)**
- ECALL (environment call)
- EBREAK (breakpoint)
- MRET (return from machine-mode trap)
- WFI (wait for interrupt)
- CSR instructions (CSRRW, CSRRS, CSRRC, and immediate variants)

**Phase 5: Integration & Testing (10-15 hours)**
- Integrate all components with core
- Write comprehensive testbenches
- Run RISC-V compliance tests
- Debug and fix issues

**Total Estimated Time: 40-50 hours (5-7 weeks @ 8 hours/week)**

### Why CSRs and Interrupts Matter

For your inverter control application, interrupts are **critical**:

```
Timer Interrupt (10 kHz)
        │
        ├─► Read ADC values (current/voltage)
        ├─► Execute control algorithm (PR controller)
        ├─► Update PWM duty cycles
        └─► Clear interrupt flag
```

Without interrupts:
- ❌ Polling is inefficient
- ❌ Timing jitter
- ❌ Missed control deadlines

With interrupts:
- ✅ Deterministic timing
- ✅ Low latency response
- ✅ Efficient CPU usage

---

## CSR (Control and Status Registers)

### What are CSRs?

CSRs are special registers that control processor behavior and store system state. They're separate from the 32 general-purpose registers (x0-x31).

**Key CSRs for RV32IM:**

| CSR Address | Name | Description |
|-------------|------|-------------|
| 0x300 | mstatus | Machine status register (interrupt enable, etc.) |
| 0x304 | mie | Machine interrupt enable (which interrupts are enabled) |
| 0x305 | mtvec | Machine trap vector (where to jump on trap) |
| 0x340 | mscratch | Machine scratch register (for trap handlers) |
| 0x341 | mepc | Machine exception PC (return address) |
| 0x342 | mcause | Machine trap cause (which exception/interrupt) |
| 0x343 | mtval | Machine trap value (bad address or instruction) |
| 0x344 | mip | Machine interrupt pending (which interrupts are pending) |

**Performance Counters (Optional but useful):**

| CSR Address | Name | Description |
|-------------|------|-------------|
| 0xB00 | mcycle | Machine cycle counter (lower 32 bits) |
| 0xB02 | minstret | Machine instructions retired counter |
| 0xB80 | mcycleh | Machine cycle counter (upper 32 bits) |
| 0xB82 | minstreth | Machine instructions retired (upper 32 bits) |

### CSR Module Implementation

#### Step 1: Create CSR Register File

**File:** `rtl/core/csr_unit.v`

```verilog
/**
 * @file csr_unit.v
 * @brief Control and Status Register Unit for RV32IM
 *
 * Implements machine-mode CSRs for trap handling, interrupts,
 * and performance counters.
 *
 * @author Custom RISC-V Core Team
 * @date 2025-12-08
 * @version 1.0
 */

`include "riscv_defines.vh"

module csr_unit (
    input  wire        clk,
    input  wire        rst_n,

    //==========================================================================
    // CSR Read/Write Interface (from core)
    //==========================================================================

    input  wire [11:0] csr_addr,      // CSR address
    input  wire [31:0] csr_wdata,     // Data to write
    input  wire [2:0]  csr_op,        // Operation: 000=none, 001=RW, 010=RS, 011=RC
    output reg  [31:0] csr_rdata,     // Data read
    output wire        csr_valid,     // CSR address is valid (exists)

    //==========================================================================
    // Trap Interface (from core)
    //==========================================================================

    input  wire        trap_entry,    // Entering trap handler
    input  wire        trap_return,   // Returning from trap (MRET)
    input  wire [31:0] trap_pc,       // PC at time of trap
    input  wire [31:0] trap_cause,    // Exception/interrupt cause
    input  wire [31:0] trap_val,      // Bad address or instruction

    output reg  [31:0] trap_vector,   // Address of trap handler
    output reg  [31:0] epc_out,       // Return address (mepc)

    //==========================================================================
    // Interrupt Interface
    //==========================================================================

    input  wire [31:0] interrupts_i,  // Interrupt lines from peripherals
    output wire        interrupt_pending, // Any interrupt pending
    output wire        interrupt_enabled, // Global interrupt enable
    output reg  [31:0] interrupt_cause,   // Which interrupt to service

    //==========================================================================
    // Performance Counters
    //==========================================================================

    input  wire        instr_retired  // Increment minstret when instruction retires
);

    //==========================================================================
    // CSR Registers
    //==========================================================================

    // Machine Trap Setup
    reg [31:0] mstatus;    // Machine status register
    reg [31:0] mie;        // Machine interrupt enable
    reg [31:0] mtvec;      // Machine trap vector base address

    // Machine Trap Handling
    reg [31:0] mscratch;   // Machine scratch register
    reg [31:0] mepc;       // Machine exception program counter
    reg [31:0] mcause;     // Machine trap cause
    reg [31:0] mtval;      // Machine trap value
    reg [31:0] mip;        // Machine interrupt pending (read-only, reflects interrupts_i)

    // Machine Counters
    reg [63:0] mcycle;     // Cycle counter (64-bit)
    reg [63:0] minstret;   // Instructions retired counter (64-bit)

    // Read-only info registers (hardcoded)
    localparam [31:0] MVENDORID = 32'h00000000;  // Non-commercial implementation
    localparam [31:0] MARCHID   = 32'h00000000;  // Architecture ID (0 = not assigned)
    localparam [31:0] MIMPID    = 32'h00000001;  // Implementation version 1
    localparam [31:0] MHARTID   = 32'h00000000;  // Hardware thread ID 0
    localparam [31:0] MISA      = 32'h40000100;  // RV32I + M extension
                                                  // Bit 30: MXL=01 (32-bit)
                                                  // Bit 8:  I extension
                                                  // Bit 12: M extension

    //==========================================================================
    // mstatus Bit Fields
    //==========================================================================

    // Bit positions (as defined in riscv_defines.vh)
    // `MSTATUS_MIE   = 3   (Machine Interrupt Enable)
    // `MSTATUS_MPIE  = 7   (Previous MIE value)
    // `MSTATUS_MPP_LO/HI = 11,12 (Previous privilege mode - always 11 for M-mode)

    wire mie_bit  = mstatus[`MSTATUS_MIE];
    wire mpie_bit = mstatus[`MSTATUS_MPIE];

    //==========================================================================
    // Interrupt Logic
    //==========================================================================

    // Update mip based on external interrupt lines
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            mip <= 32'h0;
        end else begin
            mip <= interrupts_i;
        end
    end

    // Determine if any interrupt is pending and enabled
    wire [31:0] pending_and_enabled = mip & mie;
    assign interrupt_pending = (|pending_and_enabled) && mie_bit;
    assign interrupt_enabled = mie_bit;

    // Priority encoder for interrupts (higher bit = higher priority)
    // Standard RISC-V interrupt priority: external > software > timer
    integer i;
    always @(*) begin
        interrupt_cause = 32'h0;
        for (i = 31; i >= 0; i = i - 1) begin
            if (pending_and_enabled[i]) begin
                interrupt_cause = 32'h80000000 | i;  // Set bit 31 for interrupt
            end
        end
    end

    //==========================================================================
    // Trap Vector Calculation
    //==========================================================================

    // mtvec[1:0] = mode: 00=Direct, 01=Vectored
    // mtvec[31:2] = base address (aligned to 4 bytes)

    wire [1:0]  mtvec_mode = mtvec[1:0];
    wire [31:0] mtvec_base = {mtvec[31:2], 2'b00};

    always @(*) begin
        if (mtvec_mode == 2'b00) begin
            // Direct mode: all traps jump to base address
            trap_vector = mtvec_base;
        end else begin
            // Vectored mode: interrupts jump to base + 4*cause
            if (trap_cause[31]) begin
                // Interrupt: vectored
                trap_vector = mtvec_base + ({trap_cause[30:0], 2'b00});
            end else begin
                // Exception: direct to base
                trap_vector = mtvec_base;
            end
        end
    end

    assign epc_out = mepc;

    //==========================================================================
    // CSR Read Logic
    //==========================================================================

    reg valid;

    always @(*) begin
        csr_rdata = 32'h0;
        valid = 1'b1;

        case (csr_addr)
            // Machine Information Registers
            `CSR_MVENDORID:  csr_rdata = MVENDORID;
            `CSR_MARCHID:    csr_rdata = MARCHID;
            `CSR_MIMPID:     csr_rdata = MIMPID;
            `CSR_MHARTID:    csr_rdata = MHARTID;

            // Machine Trap Setup
            `CSR_MSTATUS:    csr_rdata = mstatus;
            `CSR_MISA:       csr_rdata = MISA;
            `CSR_MIE:        csr_rdata = mie;
            `CSR_MTVEC:      csr_rdata = mtvec;

            // Machine Trap Handling
            `CSR_MSCRATCH:   csr_rdata = mscratch;
            `CSR_MEPC:       csr_rdata = mepc;
            `CSR_MCAUSE:     csr_rdata = mcause;
            `CSR_MTVAL:      csr_rdata = mtval;
            `CSR_MIP:        csr_rdata = mip;

            // Machine Counters
            `CSR_MCYCLE:     csr_rdata = mcycle[31:0];
            `CSR_MCYCLEH:    csr_rdata = mcycle[63:32];
            `CSR_MINSTRET:   csr_rdata = minstret[31:0];
            `CSR_MINSTRETH:  csr_rdata = minstret[63:32];

            // User-accessible counters (shadow mcycle/minstret)
            `CSR_CYCLE:      csr_rdata = mcycle[31:0];
            `CSR_CYCLEH:     csr_rdata = mcycle[63:32];
            `CSR_INSTRET:    csr_rdata = minstret[31:0];
            `CSR_INSTRETH:   csr_rdata = minstret[63:32];

            // Invalid CSR
            default: begin
                csr_rdata = 32'h0;
                valid = 1'b0;
            end
        endcase
    end

    assign csr_valid = valid;

    //==========================================================================
    // CSR Write Logic
    //==========================================================================

    // CSR operations:
    // 000: No operation
    // 001: CSRRW  - Read/Write (write wdata, read old value)
    // 010: CSRRS  - Read and Set bits (set bits from wdata)
    // 011: CSRRC  - Read and Clear bits (clear bits from wdata)
    // 101: CSRRWI - Read/Write Immediate
    // 110: CSRRSI - Read and Set Immediate
    // 111: CSRRCI - Read and Clear Immediate

    wire csr_write = (csr_op != 3'b000);

    reg [31:0] csr_wdata_final;

    always @(*) begin
        case (csr_op[1:0])
            2'b01: csr_wdata_final = csr_wdata;                    // CSRRW/CSRRWI
            2'b10: csr_wdata_final = csr_rdata | csr_wdata;        // CSRRS/CSRRSI
            2'b11: csr_wdata_final = csr_rdata & ~csr_wdata;       // CSRRC/CSRRCI
            default: csr_wdata_final = 32'h0;
        endcase
    end

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // Reset values
            mstatus   <= 32'h0;          // MIE=0 (interrupts disabled)
            mie       <= 32'h0;          // All interrupts disabled
            mtvec     <= 32'h00000000;   // Trap vector at address 0 (should be set by software)
            mscratch  <= 32'h0;
            mepc      <= 32'h0;
            mcause    <= 32'h0;
            mtval     <= 32'h0;
            mcycle    <= 64'h0;
            minstret  <= 64'h0;

        end else begin
            // Update performance counters
            mcycle <= mcycle + 64'd1;
            if (instr_retired) begin
                minstret <= minstret + 64'd1;
            end

            //======================================================================
            // Trap Entry
            //======================================================================

            if (trap_entry) begin
                // Save current state
                mepc   <= trap_pc;        // Save PC
                mcause <= trap_cause;     // Save cause
                mtval  <= trap_val;       // Save trap value (bad address/instruction)

                // Update mstatus
                mstatus[`MSTATUS_MPIE] <= mstatus[`MSTATUS_MIE];  // Save current MIE
                mstatus[`MSTATUS_MIE]  <= 1'b0;                    // Disable interrupts
                mstatus[`MSTATUS_MPP_HI:`MSTATUS_MPP_LO] <= 2'b11; // Previous privilege = M-mode

            //======================================================================
            // Trap Return (MRET)
            //======================================================================

            end else if (trap_return) begin
                // Restore previous state
                mstatus[`MSTATUS_MIE]  <= mstatus[`MSTATUS_MPIE];  // Restore MIE
                mstatus[`MSTATUS_MPIE] <= 1'b1;                     // Set MPIE to 1
                mstatus[`MSTATUS_MPP_HI:`MSTATUS_MPP_LO] <= 2'b11; // Stay in M-mode

            //======================================================================
            // Normal CSR Write
            //======================================================================

            end else if (csr_write && valid) begin
                case (csr_addr)
                    `CSR_MSTATUS:   mstatus   <= csr_wdata_final & 32'h00001888; // Only writable bits
                    `CSR_MIE:       mie       <= csr_wdata_final;
                    `CSR_MTVEC:     mtvec     <= csr_wdata_final;
                    `CSR_MSCRATCH:  mscratch  <= csr_wdata_final;
                    `CSR_MEPC:      mepc      <= csr_wdata_final & 32'hFFFFFFFE; // Clear LSB
                    `CSR_MCAUSE:    mcause    <= csr_wdata_final;
                    `CSR_MTVAL:     mtval     <= csr_wdata_final;

                    // Counters (writable)
                    `CSR_MCYCLE:    mcycle[31:0]   <= csr_wdata_final;
                    `CSR_MCYCLEH:   mcycle[63:32]  <= csr_wdata_final;
                    `CSR_MINSTRET:  minstret[31:0] <= csr_wdata_final;
                    `CSR_MINSTRETH: minstret[63:32]<= csr_wdata_final;

                    // Read-only registers - ignore writes
                    default: ;
                endcase
            end
        end
    end

endmodule
```

#### Step 2: Testing the CSR Unit

**File:** `sim/testbenches/tb_csr_unit.v`

```verilog
`timescale 1ns / 1ps
`include "riscv_defines.vh"

module tb_csr_unit;

    reg        clk;
    reg        rst_n;
    reg [11:0] csr_addr;
    reg [31:0] csr_wdata;
    reg [2:0]  csr_op;
    wire [31:0] csr_rdata;
    wire        csr_valid;

    reg        trap_entry;
    reg        trap_return;
    reg [31:0] trap_pc;
    reg [31:0] trap_cause;
    reg [31:0] trap_val;
    wire [31:0] trap_vector;
    wire [31:0] epc_out;

    reg [31:0] interrupts_i;
    wire       interrupt_pending;
    wire       interrupt_enabled;
    wire [31:0] interrupt_cause;

    reg        instr_retired;

    // Instantiate CSR unit
    csr_unit dut (
        .clk(clk),
        .rst_n(rst_n),
        .csr_addr(csr_addr),
        .csr_wdata(csr_wdata),
        .csr_op(csr_op),
        .csr_rdata(csr_rdata),
        .csr_valid(csr_valid),
        .trap_entry(trap_entry),
        .trap_return(trap_return),
        .trap_pc(trap_pc),
        .trap_cause(trap_cause),
        .trap_val(trap_val),
        .trap_vector(trap_vector),
        .epc_out(epc_out),
        .interrupts_i(interrupts_i),
        .interrupt_pending(interrupt_pending),
        .interrupt_enabled(interrupt_enabled),
        .interrupt_cause(interrupt_cause),
        .instr_retired(instr_retired)
    );

    // Clock generation
    initial clk = 0;
    always #5 clk = ~clk;

    // Test sequence
    initial begin
        $dumpfile("csr_unit.vcd");
        $dumpvars(0, tb_csr_unit);

        // Initialize
        rst_n = 0;
        csr_addr = 12'h0;
        csr_wdata = 32'h0;
        csr_op = 3'b000;
        trap_entry = 0;
        trap_return = 0;
        trap_pc = 32'h0;
        trap_cause = 32'h0;
        trap_val = 32'h0;
        interrupts_i = 32'h0;
        instr_retired = 0;

        #20 rst_n = 1;
        #10;

        $display("=== Test 1: Read-Only Registers ===");
        // Read MISA
        csr_addr = `CSR_MISA;
        #10;
        $display("MISA = 0x%h (expected 0x40000100)", csr_rdata);
        assert(csr_rdata == 32'h40000100) else $error("MISA incorrect!");

        // Read MVENDORID
        csr_addr = `CSR_MVENDORID;
        #10;
        $display("MVENDORID = 0x%h", csr_rdata);

        $display("\n=== Test 2: Write and Read mstatus ===");
        // Write to mstatus using CSRRW
        csr_addr = `CSR_MSTATUS;
        csr_wdata = 32'h00000008;  // Set MIE bit
        csr_op = 3'b001;  // CSRRW
        #10;
        csr_op = 3'b000;  // Stop writing
        #10;
        $display("mstatus after write = 0x%h (expected 0x00000008)", csr_rdata);
        assert(csr_rdata == 32'h00000008) else $error("mstatus write failed!");

        $display("\n=== Test 3: Set bits with CSRRS ===");
        // Set additional bits using CSRRS
        csr_addr = `CSR_MSTATUS;
        csr_wdata = 32'h00000080;  // Set MPIE bit
        csr_op = 3'b010;  // CSRRS
        #10;
        csr_op = 3'b000;
        #10;
        $display("mstatus after CSRRS = 0x%h (expected 0x00000088)", csr_rdata);
        assert(csr_rdata == 32'h00000088) else $error("CSRRS failed!");

        $display("\n=== Test 4: Clear bits with CSRRC ===");
        // Clear bits using CSRRC
        csr_addr = `CSR_MSTATUS;
        csr_wdata = 32'h00000008;  // Clear MIE bit
        csr_op = 3'b011;  // CSRRC
        #10;
        csr_op = 3'b000;
        #10;
        $display("mstatus after CSRRC = 0x%h (expected 0x00000080)", csr_rdata);
        assert(csr_rdata == 32'h00000080) else $error("CSRRC failed!");

        $display("\n=== Test 5: Trap Entry ===");
        // Setup trap vector
        csr_addr = `CSR_MTVEC;
        csr_wdata = 32'h00001000;  // Trap vector at 0x1000
        csr_op = 3'b001;
        #10;
        csr_op = 3'b000;
        #10;

        // Enable interrupts
        csr_addr = `CSR_MSTATUS;
        csr_wdata = 32'h00000008;  // Set MIE
        csr_op = 3'b001;
        #10;
        csr_op = 3'b000;
        #10;

        // Trigger trap
        trap_entry = 1;
        trap_pc = 32'h00000100;
        trap_cause = 32'h8000000B;  // External interrupt
        trap_val = 32'h0;
        #10;
        trap_entry = 0;
        #10;

        // Check mepc
        csr_addr = `CSR_MEPC;
        #10;
        $display("mepc = 0x%h (expected 0x00000100)", csr_rdata);
        assert(csr_rdata == 32'h00000100) else $error("mepc not saved!");

        // Check mcause
        csr_addr = `CSR_MCAUSE;
        #10;
        $display("mcause = 0x%h (expected 0x8000000B)", csr_rdata);
        assert(csr_rdata == 32'h8000000B) else $error("mcause not saved!");

        // Check that interrupts are disabled
        csr_addr = `CSR_MSTATUS;
        #10;
        $display("mstatus = 0x%h (MIE should be 0, MPIE should be 1)", csr_rdata);
        assert(csr_rdata[3] == 1'b0) else $error("MIE not cleared!");
        assert(csr_rdata[7] == 1'b1) else $error("MPIE not set!");

        $display("\n=== Test 6: Trap Return (MRET) ===");
        trap_return = 1;
        #10;
        trap_return = 0;
        #10;

        // Check that interrupts are re-enabled
        csr_addr = `CSR_MSTATUS;
        #10;
        $display("mstatus after MRET = 0x%h (MIE should be 1)", csr_rdata);
        assert(csr_rdata[3] == 1'b1) else $error("MIE not restored!");

        $display("\n=== Test 7: Interrupt Pending ===");
        // Enable timer interrupt in mie
        csr_addr = `CSR_MIE;
        csr_wdata = 32'h00000080;  // Bit 7 = timer interrupt
        csr_op = 3'b001;
        #10;
        csr_op = 3'b000;
        #10;

        // Assert timer interrupt
        interrupts_i = 32'h00000080;
        #20;
        $display("interrupt_pending = %b (expected 1)", interrupt_pending);
        $display("interrupt_cause = 0x%h (expected 0x80000007)", interrupt_cause);
        assert(interrupt_pending == 1'b1) else $error("Interrupt not pending!");
        assert(interrupt_cause == 32'h80000007) else $error("Wrong interrupt cause!");

        $display("\n=== Test 8: Performance Counters ===");
        // Retire some instructions
        repeat (10) begin
            instr_retired = 1;
            #10;
            instr_retired = 0;
            #10;
        end

        // Read minstret
        csr_addr = `CSR_MINSTRET;
        #10;
        $display("minstret = %d (expected 10)", csr_rdata);
        assert(csr_rdata == 32'd10) else $error("minstret incorrect!");

        // Read mcycle
        csr_addr = `CSR_MCYCLE;
        #10;
        $display("mcycle = %d", csr_rdata);

        $display("\n=== All Tests Passed! ===");
        #100 $finish;
    end

endmodule
```

**Run the test:**

```bash
cd sim
iverilog -o tb_csr tb_csr_unit.v ../rtl/core/csr_unit.v
vvp tb_csr
gtkwave csr_unit.vcd
```

**Expected Output:**

```
=== Test 1: Read-Only Registers ===
MISA = 0x40000100 (expected 0x40000100)
MVENDORID = 0x00000000

=== Test 2: Write and Read mstatus ===
mstatus after write = 0x00000008 (expected 0x00000008)

=== Test 3: Set bits with CSRRS ===
mstatus after CSRRS = 0x00000088 (expected 0x00000088)

=== Test 4: Clear bits with CSRRC ===
mstatus after CSRRC = 0x00000080 (expected 0x00000080)

=== Test 5: Trap Entry ===
mepc = 0x00000100 (expected 0x00000100)
mcause = 0x8000000B (expected 0x8000000B)
mstatus = 0x00000088 (MIE should be 0, MPIE should be 1)

=== Test 6: Trap Return (MRET) ===
mstatus after MRET = 0x00000088 (MIE should be 1)

=== Test 7: Interrupt Pending ===
interrupt_pending = 1 (expected 1)
interrupt_cause = 0x80000007 (expected 0x80000007)

=== Test 8: Performance Counters ===
minstret = 10 (expected 10)
mcycle = 305

=== All Tests Passed! ===
```

---

## Privileged Architecture

### Machine Mode Only

For an embedded inverter controller, we only need **Machine mode** (the highest privilege level). This simplifies the design:

- No User mode (no need for privilege level checking)
- No Supervisor mode (no need for virtual memory)
- All code runs at machine level with full access

### Key Concepts

**1. Privilege Levels (we only use M-mode):**
- Machine mode (M): Privilege level 11 (binary)
- Can access all CSRs and memory
- Can execute any instruction

**2. Trap Handling:**
- **Trap** = Exception or Interrupt
- **Exception** = Synchronous event (illegal instruction, misaligned access)
- **Interrupt** = Asynchronous event (timer, external)

**3. Trap Flow:**

```
Normal Execution
      │
      ├─► Exception/Interrupt occurs
      │
      ├─► Save PC → mepc
      │   Save cause → mcause
      │   Save trap value → mtval
      │
      ├─► Disable interrupts (MIE ← 0)
      │   Save old MIE → MPIE
      │
      ├─► Jump to trap vector (mtvec)
      │
      ▼
Trap Handler
      │
      ├─► Save registers (if needed)
      ├─► Handle trap
      ├─► Restore registers
      │
      ├─► Execute MRET
      │
      ├─► Restore MIE ← MPIE
      │   PC ← mepc
      │
      ▼
Resume Normal Execution
```

---

## Exception Handling

### Types of Exceptions

**For RV32IM, you need to detect:**

| Exception Code | Name | When it occurs |
|----------------|------|----------------|
| 0 | Instruction address misaligned | PC not 4-byte aligned |
| 1 | Instruction access fault | Instruction fetch error |
| 2 | Illegal instruction | Unknown opcode |
| 3 | Breakpoint | EBREAK instruction |
| 4 | Load address misaligned | Load from unaligned address |
| 5 | Load access fault | Load from invalid address |
| 6 | Store address misaligned | Store to unaligned address |
| 7 | Store access fault | Store to invalid address |
| 11 | Environment call from M-mode | ECALL instruction |

### Exception Detection Module

**File:** `rtl/core/exception_unit.v`

```verilog
`include "riscv_defines.vh"

module exception_unit (
    input  wire [31:0] pc,              // Current PC
    input  wire [31:0] instruction,     // Current instruction
    input  wire [31:0] mem_addr,        // Memory address (for load/store)
    input  wire        mem_read,        // Is load instruction
    input  wire        mem_write,       // Is store instruction
    input  wire        bus_error,       // Bus error from Wishbone
    input  wire        illegal_instr,   // From decoder
    input  wire        ecall,           // ECALL instruction
    input  wire        ebreak,          // EBREAK instruction

    output reg         exception_taken, // Exception occurred
    output reg  [31:0] exception_cause, // Exception code
    output reg  [31:0] exception_val    // Bad address or instruction
);

    always @(*) begin
        exception_taken = 1'b0;
        exception_cause = 32'h0;
        exception_val = 32'h0;

        // Priority encoder (check highest priority first)

        // 1. Instruction address misaligned (PC not 4-byte aligned)
        if (pc[1:0] != 2'b00) begin
            exception_taken = 1'b1;
            exception_cause = `MCAUSE_INSTR_MISALIGN;
            exception_val = pc;

        // 2. Instruction access fault (from bus error on fetch)
        // (Handled in fetch stage - not checked here)

        // 3. Illegal instruction
        end else if (illegal_instr) begin
            exception_taken = 1'b1;
            exception_cause = `MCAUSE_ILLEGAL_INSTR;
            exception_val = instruction;

        // 4. Breakpoint (EBREAK)
        end else if (ebreak) begin
            exception_taken = 1'b1;
            exception_cause = `MCAUSE_BREAKPOINT;
            exception_val = pc;

        // 5. Load address misaligned
        end else if (mem_read) begin
            // Check alignment based on access width
            // (This should be determined by funct3 of the load instruction)
            // For simplicity, we'll check word alignment here
            if (mem_addr[1:0] != 2'b00) begin
                exception_taken = 1'b1;
                exception_cause = `MCAUSE_LOAD_MISALIGN;
                exception_val = mem_addr;
            end else if (bus_error) begin
                // Load access fault
                exception_taken = 1'b1;
                exception_cause = `MCAUSE_LOAD_ACCESS_FAULT;
                exception_val = mem_addr;
            end

        // 6. Store address misaligned / access fault
        end else if (mem_write) begin
            if (mem_addr[1:0] != 2'b00) begin
                exception_taken = 1'b1;
                exception_cause = `MCAUSE_STORE_MISALIGN;
                exception_val = mem_addr;
            end else if (bus_error) begin
                exception_taken = 1'b1;
                exception_cause = `MCAUSE_STORE_ACCESS_FAULT;
                exception_val = mem_addr;
            end

        // 7. Environment call (ECALL)
        end else if (ecall) begin
            exception_taken = 1'b1;
            exception_cause = `MCAUSE_ECALL_M_MODE;
            exception_val = 32'h0;
        end
    end

endmodule
```

---

## Interrupt Handling

### Interrupt Sources

For your inverter controller, you need:

**1. Timer Interrupt (Priority: High)**
- 10 kHz control loop
- Most critical for real-time control

**2. External Interrupts (Priority: Medium-High)**
- ADC conversion complete
- Overcurrent protection
- Fault detection

**3. Software Interrupt (Priority: Low)**
- Rarely used in embedded systems
- Can be used for inter-core communication (not needed here)

### Interrupt Controller Module

**File:** `rtl/core/interrupt_controller.v`

```verilog
`include "riscv_defines.vh"

module interrupt_controller (
    input  wire        clk,
    input  wire        rst_n,

    //==========================================================================
    // External Interrupt Inputs
    //==========================================================================

    input  wire        timer_int,       // Timer interrupt (highest priority)
    input  wire        external_int,    // External interrupt
    input  wire        software_int,    // Software interrupt (lowest priority)
    input  wire [15:0] peripheral_ints, // Additional peripheral interrupts

    //==========================================================================
    // From CSR Unit
    //==========================================================================

    input  wire        global_int_en,   // mstatus.MIE
    input  wire [31:0] mie,             // Which interrupts are enabled

    //==========================================================================
    // To CSR Unit
    //==========================================================================

    output reg  [31:0] interrupt_lines, // Interrupt request lines

    //==========================================================================
    // To Core
    //==========================================================================

    output reg         interrupt_req,   // Interrupt request to core
    output reg  [31:0] interrupt_cause  // Which interrupt (for mcause)
);

    // Standard RISC-V interrupt bit positions:
    // Bit 3:  Machine software interrupt
    // Bit 7:  Machine timer interrupt
    // Bit 11: Machine external interrupt
    // Bits 16-31: Custom/platform-specific

    always @(*) begin
        // Combine all interrupt sources into interrupt_lines
        interrupt_lines = 32'h0;
        interrupt_lines[3]  = software_int;
        interrupt_lines[7]  = timer_int;
        interrupt_lines[11] = external_int;
        interrupt_lines[31:16] = peripheral_ints;
    end

    // Determine which interrupts are both pending and enabled
    wire [31:0] pending_and_enabled = interrupt_lines & mie;

    // Priority encoder: select highest priority interrupt
    always @(*) begin
        interrupt_req = 1'b0;
        interrupt_cause = 32'h0;

        if (global_int_en && (|pending_and_enabled)) begin
            interrupt_req = 1'b1;

            // Priority order (high to low):
            // 1. Machine external interrupt (bit 11)
            // 2. Machine software interrupt (bit 3)
            // 3. Machine timer interrupt (bit 7)
            // 4. Platform-specific (bits 16-31)

            if (pending_and_enabled[11]) begin
                interrupt_cause = `MCAUSE_EXTERNAL_INT;  // 0x8000000B
            end else if (pending_and_enabled[3]) begin
                interrupt_cause = `MCAUSE_SOFTWARE_INT;  // 0x80000003
            end else if (pending_and_enabled[7]) begin
                interrupt_cause = `MCAUSE_TIMER_INT;     // 0x80000007
            end else begin
                // Find first set bit in platform-specific range
                integer i;
                for (i = 31; i >= 16; i = i - 1) begin
                    if (pending_and_enabled[i]) begin
                        interrupt_cause = 32'h80000000 | i;
                    end
                end
            end
        end
    end

endmodule
```

### Interrupt Testing

**File:** `sim/testbenches/tb_interrupt_controller.v`

```verilog
`timescale 1ns / 1ps
`include "riscv_defines.vh"

module tb_interrupt_controller;

    reg        clk;
    reg        rst_n;
    reg        timer_int;
    reg        external_int;
    reg        software_int;
    reg [15:0] peripheral_ints;
    reg        global_int_en;
    reg [31:0] mie;
    wire [31:0] interrupt_lines;
    wire       interrupt_req;
    wire [31:0] interrupt_cause;

    interrupt_controller dut (
        .clk(clk),
        .rst_n(rst_n),
        .timer_int(timer_int),
        .external_int(external_int),
        .software_int(software_int),
        .peripheral_ints(peripheral_ints),
        .global_int_en(global_int_en),
        .mie(mie),
        .interrupt_lines(interrupt_lines),
        .interrupt_req(interrupt_req),
        .interrupt_cause(interrupt_cause)
    );

    initial clk = 0;
    always #5 clk = ~clk;

    initial begin
        $dumpfile("interrupt_controller.vcd");
        $dumpvars(0, tb_interrupt_controller);

        // Initialize
        rst_n = 0;
        timer_int = 0;
        external_int = 0;
        software_int = 0;
        peripheral_ints = 16'h0;
        global_int_en = 0;
        mie = 32'h0;

        #20 rst_n = 1;
        #10;

        $display("=== Test 1: Interrupts Disabled ===");
        timer_int = 1;
        mie = 32'h00000080;  // Enable timer interrupt
        #20;
        $display("interrupt_req = %b (expected 0, global disabled)", interrupt_req);
        assert(interrupt_req == 1'b0) else $error("Interrupt should be disabled!");

        $display("\n=== Test 2: Timer Interrupt ===");
        global_int_en = 1;
        #20;
        $display("interrupt_req = %b (expected 1)", interrupt_req);
        $display("interrupt_cause = 0x%h (expected 0x80000007)", interrupt_cause);
        assert(interrupt_req == 1'b1) else $error("Interrupt not requested!");
        assert(interrupt_cause == `MCAUSE_TIMER_INT) else $error("Wrong cause!");

        $display("\n=== Test 3: Interrupt Priority ===");
        // Assert both timer and external
        external_int = 1;
        mie = 32'h00000880;  // Enable both
        #20;
        $display("interrupt_cause = 0x%h (expected 0x8000000B - external)", interrupt_cause);
        assert(interrupt_cause == `MCAUSE_EXTERNAL_INT) else $error("Priority wrong!");

        $display("\n=== Test 4: Clear Interrupt ===");
        external_int = 0;
        timer_int = 0;
        #20;
        $display("interrupt_req = %b (expected 0)", interrupt_req);
        assert(interrupt_req == 1'b0) else $error("Interrupt not cleared!");

        $display("\n=== All Tests Passed! ===");
        #100 $finish;
    end

endmodule
```

---

## System Instructions

### CSR Instructions

**CSRRW** - CSR Read/Write
```
rd = CSR[csr]
CSR[csr] = rs1
```

**CSRRS** - CSR Read and Set Bits
```
rd = CSR[csr]
CSR[csr] = CSR[csr] | rs1
```

**CSRRC** - CSR Read and Clear Bits
```
rd = CSR[csr]
CSR[csr] = CSR[csr] & ~rs1
```

**Immediate variants:** CSRRWI, CSRRSI, CSRRCI
- Use zero-extended 5-bit immediate instead of rs1

### Privileged Instructions

**ECALL** - Environment Call
```assembly
ecall  # Raise exception (cause = 11 for M-mode)
```
- Used for system calls (though not typical in bare-metal embedded)

**EBREAK** - Breakpoint
```assembly
ebreak  # Raise breakpoint exception (cause = 3)
```
- Used by debuggers

**MRET** - Machine Return
```assembly
mret  # Return from trap handler
```
- PC ← mepc
- mstatus.MIE ← mstatus.MPIE
- mstatus.MPIE ← 1

**WFI** - Wait for Interrupt
```assembly
wfi  # Idle until interrupt
```
- Stalls pipeline until interrupt occurs
- Can be implemented as NOP for simplicity

### Implementation in Decoder

Add to your `decoder.v`:

```verilog
// In decoder.v, add to the OPCODE_SYSTEM case:

`OPCODE_SYSTEM: begin
    case (funct3)
        `FUNCT3_PRIV: begin  // 3'b000
            // Check funct12
            case (instr[31:20])
                `FUNCT12_ECALL: begin
                    // ECALL instruction
                    is_ecall = 1'b1;
                end
                `FUNCT12_EBREAK: begin
                    // EBREAK instruction
                    is_ebreak = 1'b1;
                end
                `FUNCT12_MRET: begin
                    // MRET instruction
                    is_mret = 1'b1;
                end
                `FUNCT12_WFI: begin
                    // WFI instruction
                    is_wfi = 1'b1;
                end
                default: begin
                    illegal_instr = 1'b1;
                end
            endcase
        end

        `FUNCT3_CSRRW, `FUNCT3_CSRRS, `FUNCT3_CSRRC,
        `FUNCT3_CSRRWI, `FUNCT3_CSRRSI, `FUNCT3_CSRRCI: begin
            // CSR instructions
            is_csr = 1'b1;
            csr_op = funct3;
            csr_addr = instr[31:20];

            // For immediate variants, use zimm (zero-extended immediate)
            if (funct3[2]) begin  // Immediate variant
                csr_wdata = {27'b0, instr[19:15]};  // zimm = rs1 field
            end else begin
                // Use rs1 register value
                rs1_addr = instr[19:15];
            end

            rd_addr = instr[11:7];
            reg_write = (rd_addr != 5'b0);  // Write rd if not x0
        end

        default: begin
            illegal_instr = 1'b1;
        end
    endcase
end
```

---

## Integration with Core

### Modify Core State Machine

Your core needs additional states to handle traps:

```verilog
// State machine states
localparam STATE_RESET   = 3'd0;
localparam STATE_FETCH   = 3'd1;
localparam STATE_DECODE  = 3'd2;
localparam STATE_EXECUTE = 3'd3;
localparam STATE_MEM     = 3'd4;
localparam STATE_WB      = 3'd5;
localparam STATE_TRAP    = 3'd6;  // New: handle trap entry
```

### Trap Handling Logic

```verilog
// In your core, add trap handling:

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        state <= STATE_RESET;
        pc <= RESET_VECTOR;
        // ... other resets
    end else begin
        case (state)
            STATE_RESET: begin
                state <= STATE_FETCH;
            end

            STATE_FETCH: begin
                // Check for interrupts BEFORE fetching
                if (interrupt_req && !stall) begin
                    trap_entry <= 1'b1;
                    trap_pc <= pc;
                    trap_cause <= interrupt_cause;
                    trap_val <= 32'h0;
                    state <= STATE_TRAP;
                end else begin
                    // Normal fetch
                    // ...
                end
            end

            STATE_DECODE: begin
                // ...
            end

            STATE_EXECUTE: begin
                // Check for exceptions
                if (exception_taken) begin
                    trap_entry <= 1'b1;
                    trap_pc <= pc;
                    trap_cause <= exception_cause;
                    trap_val <= exception_val;
                    state <= STATE_TRAP;
                end else if (is_mret) begin
                    // MRET: return from trap
                    trap_return <= 1'b1;
                    pc <= epc_out;
                    state <= STATE_FETCH;
                end else if (is_wfi) begin
                    // WFI: wait for interrupt
                    if (interrupt_pending) begin
                        state <= STATE_FETCH;  // Continue if interrupt pending
                    end
                    // else stay in EXECUTE (stall until interrupt)
                end else begin
                    // Normal execution
                    // ...
                end
            end

            STATE_TRAP: begin
                // Jump to trap handler
                pc <= trap_vector;
                trap_entry <= 1'b0;
                state <= STATE_FETCH;
            end

            // ... other states
        endcase
    end
end
```

### Complete Integration Checklist

- [ ] Instantiate `csr_unit` in core
- [ ] Instantiate `exception_unit` in core
- [ ] Instantiate `interrupt_controller` in core
- [ ] Connect CSR read/write to decoder
- [ ] Add trap entry/return logic to state machine
- [ ] Connect exception detection signals
- [ ] Connect interrupt signals
- [ ] Handle MRET, ECALL, EBREAK in execute stage
- [ ] Update decoder for CSR instructions
- [ ] Add trap state to FSM

---

## Testing Strategy

### Level 1: Unit Tests (Done Above)

✅ CSR unit tested
✅ Interrupt controller tested
✅ Exception unit tested

### Level 2: Integration Tests

**Test Program 1: Simple CSR Access**

```assembly
# test_csr_basic.s
.section .text
.global _start

_start:
    # Write to mscratch
    li x1, 0xDEADBEEF
    csrw mscratch, x1

    # Read back from mscratch
    csrr x2, mscratch

    # Check x2 == 0xDEADBEEF
    li x3, 0xDEADBEEF
    bne x2, x3, fail

    # Set bits in mstatus (enable MIE)
    li x4, 0x00000008
    csrs mstatus, x4

    # Read mstatus
    csrr x5, mstatus

    # Check bit 3 is set
    andi x6, x5, 0x08
    beqz x6, fail

pass:
    li x10, 1  # Success code
    j end

fail:
    li x10, 0  # Failure code

end:
    # Infinite loop
    j end
```

**Test Program 2: Exception Handling**

```assembly
# test_exception.s
.section .text
.global _start

_start:
    # Setup trap vector
    la x1, trap_handler
    csrw mtvec, x1

    # Execute illegal instruction
    .word 0x00000000  # All zeros = illegal

    # Should never reach here
    j fail

trap_handler:
    # Read mcause
    csrr x2, mcause

    # Check mcause == 2 (illegal instruction)
    li x3, 2
    bne x2, x3, fail

    # Read mepc
    csrr x4, mepc

    # Set mepc to skip bad instruction
    addi x4, x4, 4
    csrw mepc, x4

    # Return from trap
    mret

    # After MRET, we continue here
pass:
    li x10, 1
    j end

fail:
    li x10, 0

end:
    j end
```

**Test Program 3: Interrupt Handling**

```assembly
# test_interrupt.s
.section .text
.global _start

_start:
    # Setup trap vector
    la x1, trap_handler
    csrw mtvec, x1

    # Enable machine interrupts in mie (bit 7 = timer)
    li x2, 0x00000080
    csrw mie, x2

    # Enable global interrupts in mstatus (bit 3 = MIE)
    li x3, 0x00000008
    csrw mstatus, x3

    # Wait for interrupt
    li x10, 0  # Counter
wait_loop:
    addi x10, x10, 1
    j wait_loop

trap_handler:
    # Read mcause
    csrr x2, mcause

    # Check if it's an interrupt (bit 31 set)
    srli x3, x2, 31
    beqz x3, fail

    # Check if it's timer interrupt (code 7)
    andi x4, x2, 0x1F
    li x5, 7
    bne x4, x5, fail

    # Clear interrupt (platform-specific)
    # (This would normally write to timer peripheral)

    # Return from trap
    mret

    # After MRET, continue in wait_loop
    # We should see x10 has incremented

fail:
    li x10, 0xFFFFFFFF
    j end

end:
    j end
```

### Level 3: Full System Test

**Complete Test Sequence:**

1. Reset and initialize
2. Write to various CSRs
3. Read back and verify
4. Trigger exceptions (illegal instruction, misaligned access)
5. Verify trap handler called
6. Verify state saved correctly
7. Return from trap
8. Enable interrupts
9. Trigger interrupt
10. Verify interrupt handler called
11. Clear interrupt and return

---

## RISC-V Compliance Tests

### What are Compliance Tests?

Official RISC-V test suite that verifies your core implements the ISA correctly.

- **Location:** https://github.com/riscv/riscv-arch-test
- **Tests:** Pre-written assembly programs with expected outputs
- **Coverage:** All instructions, corner cases, combinations

### Setting Up Compliance Tests

**Step 1: Clone the Test Repository**

```bash
cd /home/furka/5level-inverter/02-embedded/riscv
mkdir -p verification
cd verification
git clone https://github.com/riscv/riscv-arch-test.git
cd riscv-arch-test
```

**Step 2: Build Your Test Harness**

You need to create a "target" that interfaces your core with the tests.

**File:** `verification/riscv_tests/target_custom_core/model_test.h`

```c
#ifndef _COMPLIANCE_MODEL_H
#define _COMPLIANCE_MODEL_H

// Begin test signature (results written here)
#define RVTEST_IO_WRITE_STR(_SP, _STR)

#define RVTEST_IO_INIT
#define RVTEST_IO_ASSERT_GPR_EQ(_SP, _R, _I)
#define RVTEST_IO_ASSERT_SFPR_EQ(_F, _R, _I)
#define RVTEST_IO_ASSERT_DFPR_EQ(_D, _R, _I)

// Define signature area in memory
#define TEST_SIG_START 0x80001000
#define TEST_SIG_END   0x80002000

#endif // _COMPLIANCE_MODEL_H
```

**Step 3: Adapt Tests for Your Core**

You need to:
1. Convert test programs to hex format your simulator understands
2. Run simulation
3. Extract signature (results)
4. Compare with expected outputs

**Script:** `verification/run_compliance.sh`

```bash
#!/bin/bash

# RISC-V Compliance Test Runner for Custom Core

TESTS_DIR="riscv-arch-test/riscv-test-suite/rv32i_m"
WORK_DIR="work"
SIM_DIR="../sim"

mkdir -p $WORK_DIR

echo "=== Running RV32IM Compliance Tests ==="

# List of tests to run
TESTS=(
    "I-ADD-01"
    "I-ADDI-01"
    "I-AND-01"
    "I-ANDI-01"
    "I-AUIPC-01"
    "I-BEQ-01"
    "I-BGE-01"
    # ... add all tests
)

PASSED=0
FAILED=0

for TEST in "${TESTS[@]}"; do
    echo "Running test: $TEST"

    # Compile test
    riscv32-unknown-elf-gcc -march=rv32im -mabi=ilp32 \
        -nostdlib -T linker.ld \
        -o $WORK_DIR/$TEST.elf \
        $TESTS_DIR/$TEST.S

    # Convert to hex
    riscv32-unknown-elf-objcopy -O verilog \
        $WORK_DIR/$TEST.elf \
        $WORK_DIR/$TEST.hex

    # Run simulation
    cd $SIM_DIR
    iverilog -o sim tb_core.v ../rtl/core/*.v
    vvp sim +test=$WORK_DIR/$TEST.hex > $WORK_DIR/$TEST.log
    cd -

    # Extract signature
    grep "SIGNATURE" $WORK_DIR/$TEST.log > $WORK_DIR/$TEST.sig

    # Compare with reference
    if diff $WORK_DIR/$TEST.sig \
            $TESTS_DIR/references/$TEST.reference_output > /dev/null; then
        echo "  ✓ PASSED"
        ((PASSED++))
    else
        echo "  ✗ FAILED"
        ((FAILED++))
    fi
done

echo ""
echo "=== Results ==="
echo "Passed: $PASSED"
echo "Failed: $FAILED"
echo "Total:  $((PASSED + FAILED))"

if [ $FAILED -eq 0 ]; then
    echo "🎉 All tests passed!"
    exit 0
else
    echo "❌ Some tests failed"
    exit 1
fi
```

### Running Compliance Tests

```bash
cd verification
chmod +x run_compliance.sh
./run_compliance.sh
```

**Expected Output:**

```
=== Running RV32IM Compliance Tests ===
Running test: I-ADD-01
  ✓ PASSED
Running test: I-ADDI-01
  ✓ PASSED
Running test: I-AND-01
  ✓ PASSED
...
Running test: M-MUL-01
  ✓ PASSED
Running test: M-DIV-01
  ✓ PASSED

=== Results ===
Passed: 48
Failed: 0
Total:  48
🎉 All tests passed!
```

### Debugging Failed Tests

If tests fail:

1. **Look at the waveform:**
   ```bash
   gtkwave work/I-ADD-01.vcd
   ```

2. **Check the signature:**
   ```bash
   cat work/I-ADD-01.sig
   cat riscv-arch-test/.../references/I-ADD-01.reference_output
   diff work/I-ADD-01.sig references/I-ADD-01.reference_output
   ```

3. **Common issues:**
   - Incorrect ALU operation
   - Wrong immediate encoding
   - Branch target calculation error
   - Load/store alignment issues
   - CSR read/write errors

---

## Debugging Guide

### Common Issues and Solutions

**Issue 1: Interrupts Not Firing**

```
Symptoms: interrupt_req stays 0 even when interrupt asserted
Checks:
  1. mstatus.MIE = 1? (global enable)
  2. mie[bit] = 1? (specific interrupt enabled)
  3. Interrupt actually asserted?
  4. Priority encoder working?
```

**Issue 2: Trap Handler Not Called**

```
Symptoms: Exception occurs but PC doesn't jump to trap_vector
Checks:
  1. trap_entry signal asserted?
  2. mtvec contains valid address?
  3. State machine enters TRAP state?
  4. PC updated correctly?
```

**Issue 3: MRET Doesn't Return Correctly**

```
Symptoms: After MRET, core crashes or jumps to wrong address
Checks:
  1. mepc contains correct return address?
  2. mepc aligned to 4 bytes?
  3. mstatus.MPIE restored to MIE?
  4. PC loaded from mepc?
```

**Issue 4: CSR Instructions Don't Work**

```
Symptoms: CSR values don't change or read wrong
Checks:
  1. Decoder sets is_csr correctly?
  2. CSR address correct?
  3. csr_op correct? (001=RW, 010=RS, 011=RC)
  4. CSR write enable correct?
  5. Check timing (setup/hold)
```

### Debug Features to Add

**1. Debug CSR (Custom)**

```verilog
`define CSR_DEBUG  12'h7FF  // Custom debug CSR

// In csr_unit.v:
reg [31:0] debug_reg;

// Read:
`CSR_DEBUG: csr_rdata = debug_reg;

// Write:
`CSR_DEBUG: debug_reg <= csr_wdata_final;
```

Use this to communicate with testbench.

**2. Assertion Checks**

```verilog
// In your core:
always @(posedge clk) begin
    // Check: PC should always be 4-byte aligned
    assert(pc[1:0] == 2'b00) else begin
        $error("PC misaligned: 0x%h", pc);
        $finish;
    end

    // Check: After MRET, should jump to mepc
    if (trap_return) begin
        assert(pc == epc_out) else begin
            $error("MRET: PC != mepc (PC=0x%h, mepc=0x%h)", pc, epc_out);
        end
    end
end
```

**3. Waveform Markers**

```verilog
// Add markers in simulation for easier debugging
always @(posedge clk) begin
    if (trap_entry) $display(">>> TRAP ENTRY at PC=0x%h, cause=0x%h", pc, trap_cause);
    if (trap_return) $display("<<< TRAP RETURN to PC=0x%h", epc_out);
    if (interrupt_req) $display("!!! INTERRUPT REQUEST: cause=0x%h", interrupt_cause);
end
```

---

## Summary and Next Steps

### What You've Accomplished

By completing this guide, you've implemented:

✅ **CSR Unit**
- Machine-mode CSRs
- Performance counters
- Trap handling CSRs

✅ **Exception Handling**
- All required RV32I exceptions
- Proper state saving/restoration

✅ **Interrupt Handling**
- Timer, external, software interrupts
- Priority encoding
- Interrupt masking

✅ **System Instructions**
- CSR read/write/set/clear
- ECALL, EBREAK, MRET, WFI

✅ **Compliance Testing**
- RISC-V official test suite
- Full ISA verification

### Your Core is Now Complete! 🎉

You have a fully functional **RV32IM core** with:
- 48 instructions (40 RV32I + 8 M extension)
- Exception and interrupt support
- CSR system
- Compliance tested

### Next Steps for Inverter Project

**1. Integrate with SOC**
```
Custom RISC-V Core (done!)
        │
        ├─► Timer Peripheral (generates 10 kHz interrupt)
        ├─► ADC Interface (reads current/voltage)
        ├─► PWM Accelerator (updates duty cycles)
        └─► Protection Unit (overcurrent detection)
```

**2. Port Control Algorithms**
- Convert MATLAB/Simulink models to C
- Compile with RISC-V GCC
- Test on simulation

**3. Deploy to FPGA**
- Synthesize for Artix-7
- Upload to FPGA
- Test with real hardware

**4. Performance Optimization**
- Profile interrupt latency
- Optimize critical paths
- Add custom Zpec instructions if needed

### Milestone Checklist

**Before Moving to Next Stage:**

- [ ] All unit tests passing
- [ ] Integration tests passing
- [ ] Exception handling working (ECALL, EBREAK, illegal instruction)
- [ ] Interrupt handling working (timer, external)
- [ ] MRET correctly returns from traps
- [ ] CSR instructions work (CSRRW, CSRRS, CSRRC)
- [ ] Performance counters incrementing
- [ ] RISC-V compliance tests passing (target: 100%)
- [ ] Waveforms look correct
- [ ] No timing violations
- [ ] Code is documented

**Congratulations on completing your RV32IM core!** 🚀

---

**Document Version:** 1.0
**Last Updated:** 2025-12-08
**Status:** Complete
**Next:** SOC Integration (see `docs/SOC_INTEGRATION_GUIDE.md`)
