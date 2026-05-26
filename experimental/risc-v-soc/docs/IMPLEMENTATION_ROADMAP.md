# RV32IM Custom Core Implementation Roadmap

**Document Version:** 1.0
**Date:** 2025-12-03
**Target:** Hand-written RISC-V RV32IM Core from Scratch
**Complexity:** ~2500-3000 lines of Verilog

---

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Development Phases](#development-phases)
4. [Detailed Roadmap](#detailed-roadmap)
5. [Milestone Testing](#milestone-testing)
6. [Code Organization](#code-organization)
7. [Common Pitfalls](#common-pitfalls)
8. [Resources](#resources)

---

## Overview

### What You'll Build

A complete **RV32IM RISC-V processor** with:
- ✅ 3-stage pipeline (Fetch → Decode/Execute → Writeback)
- ✅ 32× 32-bit general-purpose registers
- ✅ Full RV32I base instruction set (40 instructions)
- ✅ Hardware multiply/divide (RV32M extension, 8 instructions)
- ✅ Interrupt controller with vectoring (5 priority levels)
- ✅ Wishbone bus interface for peripherals
- ✅ Harvard architecture (separate instruction/data memory)

### Timeline

**Total Estimate: 10-12 weeks** (10-15 hours/week)

```
Week 1-2:   Environment setup, basic infrastructure
Week 3-4:   Register file, ALU, simple instructions
Week 5-6:   Branch/jump logic, pipeline hazards
Week 7-8:   Memory interface, load/store instructions
Week 9-10:  Multiply/divide unit (RV32M)
Week 11:    Interrupt controller
Week 12:    Integration testing, debugging
```

### Complexity Breakdown

| Module | Lines of Verilog | Complexity | Time |
|--------|-----------------|------------|------|
| Register File | ~100 | Low | 4 hours |
| ALU | ~250 | Low | 8 hours |
| Instruction Decoder | ~400 | Medium | 12 hours |
| Pipeline Control | ~300 | High | 16 hours |
| Multiply/Divide | ~500 | High | 20 hours |
| Memory Interface | ~200 | Medium | 10 hours |
| Interrupt Controller | ~350 | High | 18 hours |
| Top-level Integration | ~400 | Medium | 12 hours |
| **Total** | **~2500** | | **~100 hours** |

---

## Prerequisites

### Required Tools

1. **Verilog Simulator**
   ```bash
   # Verilator (recommended - fast, open-source)
   sudo apt-get install verilator

   # Or Icarus Verilog (simple, free)
   sudo apt-get install iverilog gtkwave
   ```

2. **RISC-V Toolchain**
   ```bash
   # Install prebuilt toolchain
   sudo apt-get install gcc-riscv64-unknown-elf

   # Or build from source
   git clone https://github.com/riscv/riscv-gnu-toolchain
   cd riscv-gnu-toolchain
   ./configure --prefix=/opt/riscv --with-arch=rv32im --with-abi=ilp32
   make
   export PATH=/opt/riscv/bin:$PATH
   ```

3. **Waveform Viewer**
   ```bash
   sudo apt-get install gtkwave
   ```

4. **Text Editor / IDE**
   - VSCode with Verilog extensions
   - Vim with verilog plugins
   - Emacs with verilog-mode

### Knowledge Prerequisites

**Must Have:**
- ✅ Digital logic design (combinational and sequential)
- ✅ Verilog syntax and simulation
- ✅ Basic computer architecture (registers, ALU, memory)

**Should Have:**
- ✅ RISC-V assembly language basics
- ✅ Pipeline concepts (hazards, forwarding, stalls)
- ✅ Finite state machines (FSMs)

**Nice to Have:**
- Timing analysis
- Formal verification
- FPGA synthesis

### Recommended Reading

**Before Starting:**
1. **"Computer Organization and Design: RISC-V Edition"** by Patterson & Hennessy
   - Chapter 4 (The Processor) - Must read!
   - Chapter 5 (Pipeline hazards)

2. **RISC-V ISA Specification** (Volume 1: User-Level ISA)
   - Download: https://riscv.org/technical/specifications/
   - Focus on RV32I and RV32M chapters

3. **Online Tutorial**
   - "Building a RISC-V CPU Core" by Steve Hoover
   - https://github.com/stevehoover/RISC-V_MYTH_Workshop

---

## Development Phases

### Phase 1: Foundation (Weeks 1-2)
- Set up development environment
- Create project structure
- Implement basic building blocks
- Write first testbenches

### Phase 2: Single-Cycle Core (Weeks 3-4)
- Register file
- ALU
- Simple instruction execution (no memory, no branches)
- **Milestone:** Execute `ADD`, `SUB`, `AND`, `OR` instructions

### Phase 3: Control Flow (Weeks 5-6)
- Branch and jump instructions
- Program counter logic
- **Milestone:** Execute factorial program

### Phase 4: Memory System (Weeks 7-8)
- Load/store instructions
- Wishbone bus interface
- Memory arbiter
- **Milestone:** Execute program with data memory access

### Phase 5: M Extension (Weeks 9-10)
- Multiplier unit
- Divider unit
- **Milestone:** Execute multiply/divide operations

### Phase 6: Interrupts (Week 11)
- Interrupt controller
- CSR (Control and Status Registers)
- Vectored interrupts
- **Milestone:** Handle timer interrupt

### Phase 7: Integration & Testing (Week 12)
- Full system testing
- RISC-V compliance tests
- Performance optimization
- **Milestone:** Pass RV32IM compliance suite

---

## Detailed Roadmap

### Week 1-2: Environment Setup and Infrastructure

#### Day 1-2: Project Setup

**Tasks:**
1. Create directory structure
2. Set up Makefile build system
3. Install and verify tools

**Deliverables:**
```bash
riscv/
├── rtl/
│   └── core/
│       └── (empty, ready for modules)
├── sim/
│   └── testbenches/
├── tools/
│   └── Makefile
└── docs/
    └── IMPLEMENTATION_ROADMAP.md (this file)
```

**Test:**
```bash
cd riscv/sim
make hello_world_tb  # Should compile and run a simple testbench
```

#### Day 3-5: Define Instruction Encoding

**Tasks:**
1. Create `riscv_defines.vh` header file
2. Define opcodes, function codes
3. Document instruction formats

**Deliverables:**
- `rtl/core/riscv_defines.vh` (see reusable code section)

**Example:**
```verilog
// R-type instruction format
// [31:25] funct7, [24:20] rs2, [19:15] rs1, [14:12] funct3, [11:7] rd, [6:0] opcode

`define OPCODE_OP       7'b0110011  // R-type ALU operations
`define OPCODE_OP_IMM   7'b0010011  // I-type immediate operations
`define OPCODE_LOAD     7'b0000011  // Load instructions
`define OPCODE_STORE    7'b0100011  // Store instructions
`define OPCODE_BRANCH   7'b1100011  // Branch instructions
// ... etc
```

#### Day 6-7: Basic Testbench Infrastructure

**Tasks:**
1. Create generic testbench template
2. Implement instruction memory model
3. Add waveform dumping

**Deliverables:**
- `sim/testbenches/tb_template.v`
- `sim/testbenches/instruction_mem.v`

**Test:**
Run a NOP loop and verify with GTKWave.

---

### Week 3-4: Single-Cycle Core

#### Step 1: Register File (4 hours)

**Module:** `regfile.v`

**Specifications:**
- 32 registers (x0-x31)
- x0 hardwired to zero
- 2 read ports (rs1, rs2)
- 1 write port (rd)
- Synchronous write, asynchronous read

**Implementation:**
```verilog
module regfile (
    input  wire        clk,
    input  wire        rst_n,

    // Read ports
    input  wire [4:0]  rs1_addr,
    output wire [31:0] rs1_data,
    input  wire [4:0]  rs2_addr,
    output wire [31:0] rs2_data,

    // Write port
    input  wire        wr_en,
    input  wire [4:0]  rd_addr,
    input  wire [31:0] rd_data
);
    // 32 registers, 32-bit each
    reg [31:0] registers [1:31];  // x0 is not stored (always 0)

    integer i;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 1; i < 32; i = i + 1) begin
                registers[i] <= 32'h0;
            end
        end else if (wr_en && rd_addr != 5'd0) begin
            registers[rd_addr] <= rd_data;
        end
    end

    // Asynchronous read
    assign rs1_data = (rs1_addr == 5'd0) ? 32'h0 : registers[rs1_addr];
    assign rs2_data = (rs2_addr == 5'd0) ? 32'h0 : registers[rs2_addr];
endmodule
```

**Testbench:**
```verilog
// Test: Write to x1, read from x1
initial begin
    #10 wr_en = 1; rd_addr = 5'd1; rd_data = 32'hDEADBEEF;
    #10 wr_en = 0;
    #1  assert(rs1_data == 32'hDEADBEEF) else $error("Register write failed!");

    // Test: x0 always zero
    #10 wr_en = 1; rd_addr = 5'd0; rd_data = 32'hBAD;
    #10 wr_en = 0; rs1_addr = 5'd0;
    #1  assert(rs1_data == 32'h0) else $error("x0 not hardwired to zero!");

    $display("✓ Register file tests passed");
    $finish;
end
```

**Checkpoint:** Register file passes all tests

---

#### Step 2: ALU (8 hours)

**Module:** `alu.v`

**Operations:**
```
ADD, SUB, AND, OR, XOR
SLL (shift left logical)
SRL (shift right logical)
SRA (shift right arithmetic)
SLT (set less than, signed)
SLTU (set less than, unsigned)
```

**Implementation:**
```verilog
module alu (
    input  wire [31:0] operand_a,
    input  wire [31:0] operand_b,
    input  wire [3:0]  alu_op,
    output reg  [31:0] result,
    output wire        zero,
    output wire        negative,
    output wire        overflow
);
    // ALU operations
    localparam ALU_ADD  = 4'b0000;
    localparam ALU_SUB  = 4'b0001;
    localparam ALU_AND  = 4'b0010;
    localparam ALU_OR   = 4'b0011;
    localparam ALU_XOR  = 4'b0100;
    localparam ALU_SLL  = 4'b0101;
    localparam ALU_SRL  = 4'b0110;
    localparam ALU_SRA  = 4'b0111;
    localparam ALU_SLT  = 4'b1000;
    localparam ALU_SLTU = 4'b1001;

    always @(*) begin
        case (alu_op)
            ALU_ADD:  result = operand_a + operand_b;
            ALU_SUB:  result = operand_a - operand_b;
            ALU_AND:  result = operand_a & operand_b;
            ALU_OR:   result = operand_a | operand_b;
            ALU_XOR:  result = operand_a ^ operand_b;
            ALU_SLL:  result = operand_a << operand_b[4:0];
            ALU_SRL:  result = operand_a >> operand_b[4:0];
            ALU_SRA:  result = $signed(operand_a) >>> operand_b[4:0];
            ALU_SLT:  result = ($signed(operand_a) < $signed(operand_b)) ? 32'd1 : 32'd0;
            ALU_SLTU: result = (operand_a < operand_b) ? 32'd1 : 32'd0;
            default:  result = 32'h0;
        endcase
    end

    assign zero = (result == 32'h0);
    assign negative = result[31];
    assign overflow = /* overflow detection logic */;
endmodule
```

**Testbench:**
```verilog
// Test each operation
initial begin
    // Test ADD
    operand_a = 32'd10; operand_b = 32'd20; alu_op = ALU_ADD;
    #1 assert(result == 32'd30) else $error("ADD failed!");

    // Test SUB
    operand_a = 32'd50; operand_b = 32'd30; alu_op = ALU_SUB;
    #1 assert(result == 32'd20) else $error("SUB failed!");

    // Test SLT (signed less than)
    operand_a = -32'd5; operand_b = 32'd10; alu_op = ALU_SLT;
    #1 assert(result == 32'd1) else $error("SLT failed!");

    $display("✓ ALU tests passed");
    $finish;
end
```

**Checkpoint:** ALU passes all tests

---

#### Step 3: Instruction Decoder (12 hours)

**Module:** `decode.v`

**Purpose:** Decode 32-bit instruction into control signals

**Outputs:**
- Register addresses (rs1, rs2, rd)
- Immediate value
- ALU operation
- Memory read/write enable
- Register write enable
- Branch/jump signals

**Implementation Strategy:**

```verilog
module decode (
    input  wire [31:0] instruction,

    // Register file control
    output reg  [4:0]  rs1_addr,
    output reg  [4:0]  rs2_addr,
    output reg  [4:0]  rd_addr,
    output reg         reg_write,

    // ALU control
    output reg  [3:0]  alu_op,
    output reg         alu_src,  // 0=rs2, 1=immediate

    // Memory control
    output reg         mem_read,
    output reg         mem_write,
    output reg  [2:0]  mem_width,  // byte, half-word, word

    // Branch/Jump control
    output reg         branch,
    output reg         jump,
    output reg         jalr,

    // Immediate value
    output reg  [31:0] immediate
);
    // Extract instruction fields
    wire [6:0] opcode = instruction[6:0];
    wire [2:0] funct3 = instruction[14:12];
    wire [6:0] funct7 = instruction[31:25];

    always @(*) begin
        // Default values
        rs1_addr = instruction[19:15];
        rs2_addr = instruction[24:20];
        rd_addr  = instruction[11:7];
        reg_write = 1'b0;
        alu_src = 1'b0;
        mem_read = 1'b0;
        mem_write = 1'b0;
        branch = 1'b0;
        jump = 1'b0;
        jalr = 1'b0;

        case (opcode)
            `OPCODE_OP: begin  // R-type (register-register)
                reg_write = 1'b1;
                alu_src = 1'b0;
                case (funct3)
                    3'b000: alu_op = (funct7[5]) ? ALU_SUB : ALU_ADD;
                    3'b001: alu_op = ALU_SLL;
                    3'b010: alu_op = ALU_SLT;
                    3'b011: alu_op = ALU_SLTU;
                    3'b100: alu_op = ALU_XOR;
                    3'b101: alu_op = (funct7[5]) ? ALU_SRA : ALU_SRL;
                    3'b110: alu_op = ALU_OR;
                    3'b111: alu_op = ALU_AND;
                endcase
            end

            `OPCODE_OP_IMM: begin  // I-type (register-immediate)
                reg_write = 1'b1;
                alu_src = 1'b1;
                immediate = {{20{instruction[31]}}, instruction[31:20]};  // Sign-extend
                case (funct3)
                    3'b000: alu_op = ALU_ADD;  // ADDI
                    3'b010: alu_op = ALU_SLT;  // SLTI
                    3'b011: alu_op = ALU_SLTU; // SLTIU
                    3'b100: alu_op = ALU_XOR;  // XORI
                    3'b110: alu_op = ALU_OR;   // ORI
                    3'b111: alu_op = ALU_AND;  // ANDI
                    3'b001: begin
                        alu_op = ALU_SLL;  // SLLI
                        immediate = {27'b0, instruction[24:20]};  // Shift amount
                    end
                    3'b101: begin
                        alu_op = (funct7[5]) ? ALU_SRA : ALU_SRL;  // SRAI/SRLI
                        immediate = {27'b0, instruction[24:20]};
                    end
                endcase
            end

            `OPCODE_LOAD: begin  // Load instructions
                reg_write = 1'b1;
                alu_src = 1'b1;
                alu_op = ALU_ADD;  // Address = rs1 + offset
                mem_read = 1'b1;
                immediate = {{20{instruction[31]}}, instruction[31:20]};
                mem_width = funct3;  // LB/LH/LW/LBU/LHU
            end

            `OPCODE_STORE: begin  // Store instructions
                alu_src = 1'b1;
                alu_op = ALU_ADD;  // Address = rs1 + offset
                mem_write = 1'b1;
                immediate = {{20{instruction[31]}}, instruction[31:25], instruction[11:7]};
                mem_width = funct3;  // SB/SH/SW
            end

            `OPCODE_BRANCH: begin  // Branch instructions
                alu_src = 1'b0;
                branch = 1'b1;
                immediate = {{19{instruction[31]}}, instruction[31], instruction[7],
                             instruction[30:25], instruction[11:8], 1'b0};
                // Branch condition checked in execute stage
            end

            // ... (continue for JAL, JALR, LUI, AUIPC, etc.)

            default: begin
                // Invalid instruction - set all to zero
            end
        endcase
    end
endmodule
```

**Testbench:**
```verilog
// Test: Decode ADD instruction (0x003100B3 = add x1, x2, x3)
initial begin
    instruction = 32'h003100B3;
    #1
    assert(opcode == `OPCODE_OP) else $error("Wrong opcode!");
    assert(rd_addr == 5'd1) else $error("Wrong rd!");
    assert(rs1_addr == 5'd2) else $error("Wrong rs1!");
    assert(rs2_addr == 5'd3) else $error("Wrong rs2!");
    assert(reg_write == 1'b1) else $error("reg_write should be 1!");
    assert(alu_op == ALU_ADD) else $error("Wrong ALU op!");

    $display("✓ Decoder tests passed");
end
```

**Checkpoint:** Decoder correctly decodes all RV32I instruction types

---

#### Step 4: Simple Datapath (8 hours)

**Module:** `riscv_core_simple.v`

**Purpose:** Connect register file, ALU, and decoder

**Architecture:**
```
┌─────────────────┐
│   Instruction   │
│     Memory      │
└────────┬────────┘
         │
         ▼
    ┌─────────┐
    │ Decoder │
    └────┬────┘
         │
    ┌────┴───────────────┐
    │                    │
    ▼                    ▼
┌───────┐          ┌─────────┐
│  Reg  │───rs1───▶│   ALU   │
│ File  │          │         │
│       │───rs2───▶│  (MUX)  │
└───────┘          └────┬────┘
    ▲                   │
    │                   │
    └───────result──────┘
```

**Implementation:**
```verilog
module riscv_core_simple (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [31:0] instruction,
    output reg  [31:0] result
);
    // Decode signals
    wire [4:0]  rs1_addr, rs2_addr, rd_addr;
    wire [31:0] rs1_data, rs2_data;
    wire [31:0] immediate;
    wire [3:0]  alu_op;
    wire        alu_src;
    wire        reg_write;

    // ALU signals
    wire [31:0] alu_operand_b;
    wire [31:0] alu_result;

    // Instantiate modules
    decode decoder (
        .instruction(instruction),
        .rs1_addr(rs1_addr),
        .rs2_addr(rs2_addr),
        .rd_addr(rd_addr),
        .reg_write(reg_write),
        .alu_op(alu_op),
        .alu_src(alu_src),
        .immediate(immediate)
        // ... other signals
    );

    regfile registers (
        .clk(clk),
        .rst_n(rst_n),
        .rs1_addr(rs1_addr),
        .rs1_data(rs1_data),
        .rs2_addr(rs2_addr),
        .rs2_data(rs2_data),
        .wr_en(reg_write),
        .rd_addr(rd_addr),
        .rd_data(alu_result)
    );

    // ALU operand B mux: rs2 or immediate
    assign alu_operand_b = alu_src ? immediate : rs2_data;

    alu arithmetic_unit (
        .operand_a(rs1_data),
        .operand_b(alu_operand_b),
        .alu_op(alu_op),
        .result(alu_result),
        .zero(),
        .negative(),
        .overflow()
    );

    always @(posedge clk) begin
        result <= alu_result;
    end
endmodule
```

**Testbench:**
```verilog
// Test: Execute ADD x1, x0, x0  (x1 = 0 + 0)
//       Then ADDI x1, x1, 10    (x1 = 0 + 10)
//       Then ADD x2, x1, x1     (x2 = 10 + 10 = 20)

initial begin
    rst_n = 0;
    #10 rst_n = 1;

    // Instruction 1: ADDI x1, x0, 10
    instruction = 32'h00A00093;  // addi x1, x0, 10
    #10 assert(result == 32'd10) else $error("ADDI failed!");

    // Instruction 2: ADD x2, x1, x1
    instruction = 32'h001081B3;  // add x2, x1, x1
    #10 assert(result == 32'd20) else $error("ADD failed!");

    $display("✓ Simple datapath tests passed");
    $finish;
end
```

**Milestone:** Execute simple arithmetic instructions ✅

---

### Week 5-6: Control Flow and Branches

#### Step 5: Program Counter (PC) Logic (6 hours)

**Module:** `pc_unit.v`

**Features:**
- Increment PC by 4 (next instruction)
- Branch target calculation
- Jump target calculation

**Implementation:**
```verilog
module pc_unit (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        stall,

    // Control signals
    input  wire        branch_taken,
    input  wire        jump,
    input  wire        jalr,

    // Branch/jump targets
    input  wire [31:0] branch_target,
    input  wire [31:0] jump_target,
    input  wire [31:0] jalr_target,

    // Output
    output reg  [31:0] pc,
    output wire [31:0] pc_next
);
    // Next PC calculation
    reg [31:0] pc_plus_4;

    always @(*) begin
        pc_plus_4 = pc + 32'd4;

        if (jalr)
            pc_next = jalr_target & ~32'd1;  // Clear LSB for JALR
        else if (jump)
            pc_next = jump_target;
        else if (branch_taken)
            pc_next = branch_target;
        else
            pc_next = pc_plus_4;
    end

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            pc <= 32'h0;
        else if (!stall)
            pc <= pc_next;
    end
endmodule
```

**Checkpoint:** PC correctly updates for sequential, branch, and jump instructions

---

#### Step 6: Branch Logic (8 hours)

**Module:** `branch_unit.v`

**Branch Conditions:**
```
BEQ  : Branch if Equal (rs1 == rs2)
BNE  : Branch if Not Equal (rs1 != rs2)
BLT  : Branch if Less Than (signed)
BGE  : Branch if Greater or Equal (signed)
BLTU : Branch if Less Than (unsigned)
BGEU : Branch if Greater or Equal (unsigned)
```

**Implementation:**
```verilog
module branch_unit (
    input  wire [31:0] rs1_data,
    input  wire [31:0] rs2_data,
    input  wire [2:0]  funct3,
    input  wire        branch_en,
    output reg         branch_taken
);
    always @(*) begin
        branch_taken = 1'b0;
        if (branch_en) begin
            case (funct3)
                3'b000: branch_taken = (rs1_data == rs2_data);                        // BEQ
                3'b001: branch_taken = (rs1_data != rs2_data);                        // BNE
                3'b100: branch_taken = ($signed(rs1_data) < $signed(rs2_data));      // BLT
                3'b101: branch_taken = ($signed(rs1_data) >= $signed(rs2_data));     // BGE
                3'b110: branch_taken = (rs1_data < rs2_data);                         // BLTU
                3'b111: branch_taken = (rs1_data >= rs2_data);                        // BGEU
                default: branch_taken = 1'b0;
            endcase
        end
    end
endmodule
```

**Test Program:**
```c
// Factorial program in C
int factorial(int n) {
    int result = 1;
    for (int i = 2; i <= n; i++) {
        result = result * i;
    }
    return result;
}

// Compile to RISC-V assembly:
// riscv32-unknown-elf-gcc -march=rv32i -O2 -S factorial.c
```

**Milestone:** Execute factorial program with loops ✅

---

### Week 7-8: Memory System

#### Step 7: Wishbone Master Interface (10 hours)

**Module:** `wishbone_master.v`

**Wishbone B4 Signals:**
```
Master Outputs:
  - wb_addr   : Address
  - wb_dat_o  : Write data
  - wb_we     : Write enable
  - wb_sel    : Byte select
  - wb_stb    : Strobe
  - wb_cyc    : Cycle

Master Inputs:
  - wb_dat_i  : Read data
  - wb_ack    : Acknowledge
```

**FSM States:**
```
IDLE → REQUEST → WAIT_ACK → DONE
```

**Implementation:**
```verilog
module wishbone_master (
    input  wire        clk,
    input  wire        rst_n,

    // CPU interface
    input  wire        mem_req,       // Memory request
    input  wire        mem_we,        // Write enable
    input  wire [31:0] mem_addr,
    input  wire [31:0] mem_wdata,
    input  wire [3:0]  mem_be,        // Byte enable
    output reg  [31:0] mem_rdata,
    output reg         mem_ready,

    // Wishbone bus
    output reg  [31:0] wb_addr,
    output reg  [31:0] wb_dat_o,
    output reg         wb_we,
    output reg  [3:0]  wb_sel,
    output reg         wb_stb,
    output reg         wb_cyc,
    input  wire [31:0] wb_dat_i,
    input  wire        wb_ack
);
    localparam IDLE     = 2'b00;
    localparam REQUEST  = 2'b01;
    localparam WAIT_ACK = 2'b10;

    reg [1:0] state;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= IDLE;
            wb_cyc <= 1'b0;
            wb_stb <= 1'b0;
            mem_ready <= 1'b0;
        end else begin
            case (state)
                IDLE: begin
                    mem_ready <= 1'b0;
                    if (mem_req) begin
                        wb_addr <= mem_addr;
                        wb_dat_o <= mem_wdata;
                        wb_we <= mem_we;
                        wb_sel <= mem_be;
                        wb_cyc <= 1'b1;
                        wb_stb <= 1'b1;
                        state <= WAIT_ACK;
                    end
                end

                WAIT_ACK: begin
                    if (wb_ack) begin
                        mem_rdata <= wb_dat_i;
                        mem_ready <= 1'b1;
                        wb_cyc <= 1'b0;
                        wb_stb <= 1'b0;
                        state <= IDLE;
                    end
                end
            endcase
        end
    end
endmodule
```

**Checkpoint:** Wishbone interface passes handshake tests

---

#### Step 8: Load/Store Instructions (8 hours)

**Additions to Datapath:**
- Memory address calculation (rs1 + offset)
- Byte/half-word/word access
- Sign extension for LB, LH
- Zero extension for LBU, LHU

**Load/Store Logic:**
```verilog
// In execute stage
wire [31:0] mem_addr = rs1_data + immediate;

// Byte enable generation
reg [3:0] byte_enable;
always @(*) begin
    case (mem_width)
        3'b000: byte_enable = (4'b0001 << mem_addr[1:0]);  // LB/SB
        3'b001: byte_enable = (4'b0011 << mem_addr[1:0]);  // LH/SH
        3'b010: byte_enable = 4'b1111;                      // LW/SW
        default: byte_enable = 4'b0000;
    endcase
end

// Load data alignment and sign extension
reg [31:0] load_data_aligned;
always @(*) begin
    case (mem_width)
        3'b000: begin  // LB (signed byte)
            case (mem_addr[1:0])
                2'b00: load_data_aligned = {{24{mem_rdata[7]}}, mem_rdata[7:0]};
                2'b01: load_data_aligned = {{24{mem_rdata[15]}}, mem_rdata[15:8]};
                2'b10: load_data_aligned = {{24{mem_rdata[23]}}, mem_rdata[23:16]};
                2'b11: load_data_aligned = {{24{mem_rdata[31]}}, mem_rdata[31:24]};
            endcase
        end
        3'b001: begin  // LH (signed half-word)
            case (mem_addr[1])
                1'b0: load_data_aligned = {{16{mem_rdata[15]}}, mem_rdata[15:0]};
                1'b1: load_data_aligned = {{16{mem_rdata[31]}}, mem_rdata[31:16]};
            endcase
        end
        3'b010: load_data_aligned = mem_rdata;  // LW (word)
        3'b100: begin  // LBU (unsigned byte)
            case (mem_addr[1:0])
                2'b00: load_data_aligned = {24'h0, mem_rdata[7:0]};
                2'b01: load_data_aligned = {24'h0, mem_rdata[15:8]};
                2'b10: load_data_aligned = {24'h0, mem_rdata[23:16]};
                2'b11: load_data_aligned = {24'h0, mem_rdata[31:24]};
            endcase
        end
        3'b101: begin  // LHU (unsigned half-word)
            case (mem_addr[1])
                1'b0: load_data_aligned = {16'h0, mem_rdata[15:0]};
                1'b1: load_data_aligned = {16'h0, mem_rdata[31:16]};
            endcase
        end
        default: load_data_aligned = 32'h0;
    endcase
end
```

**Test Program:**
```c
// Array sum program
int sum_array(int* array, int length) {
    int sum = 0;
    for (int i = 0; i < length; i++) {
        sum += array[i];
    }
    return sum;
}
```

**Milestone:** Execute programs with memory access ✅

---

### Week 9-10: Multiply/Divide (M Extension)

#### Step 9: Multiplier (12 hours)

**Module:** `multiplier.v`

**Algorithm Options:**
1. **Combinational (fast, large area)**
2. **Sequential (slow, small area)** ← Recommended
3. **Booth's algorithm (balanced)**

**Sequential Implementation (32 cycles):**
```verilog
module multiplier (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        start,
    input  wire        is_signed,
    input  wire [31:0] multiplicand,
    input  wire [31:0] multiplier,
    output reg  [63:0] product,
    output reg         done
);
    reg [4:0]  count;
    reg [63:0] partial_product;
    reg [32:0] multiplicand_ext;
    reg [32:0] multiplier_ext;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            count <= 5'd0;
            done <= 1'b0;
            product <= 64'h0;
        end else if (start && !done) begin
            if (count == 5'd0) begin
                // Initialize
                multiplicand_ext <= is_signed ? {multiplicand[31], multiplicand} : {1'b0, multiplicand};
                multiplier_ext <= is_signed ? {multiplier[31], multiplier} : {1'b0, multiplier};
                partial_product <= 64'h0;
                count <= 5'd1;
                done <= 1'b0;
            end else if (count <= 5'd32) begin
                // Add-shift algorithm
                if (multiplier_ext[0]) begin
                    partial_product <= partial_product + ({31'h0, multiplicand_ext} << (count - 1));
                end
                multiplier_ext <= multiplier_ext >> 1;
                count <= count + 1;
            end else begin
                product <= partial_product;
                done <= 1'b1;
                count <= 5'd0;
            end
        end else if (!start) begin
            done <= 1'b0;
        end
    end
endmodule
```

**M Extension Instructions:**
```
MUL    : Multiply (lower 32 bits)
MULH   : Multiply (upper 32 bits, signed × signed)
MULHSU : Multiply (upper 32 bits, signed × unsigned)
MULHU  : Multiply (upper 32 bits, unsigned × unsigned)
```

**Checkpoint:** Multiplier passes test vectors

---

#### Step 10: Divider (8 hours)

**Module:** `divider.v`

**Algorithm:** Non-restoring division (33 cycles)

**Implementation:**
```verilog
module divider (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        start,
    input  wire        is_signed,
    input  wire [31:0] dividend,
    input  wire [31:0] divisor,
    output reg  [31:0] quotient,
    output reg  [31:0] remainder,
    output reg         done,
    output reg         div_by_zero
);
    reg [4:0]  count;
    reg [31:0] divisor_reg;
    reg [31:0] quotient_reg;
    reg [63:0] remainder_reg;
    reg        dividend_sign, divisor_sign;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            count <= 5'd0;
            done <= 1'b0;
            div_by_zero <= 1'b0;
        end else if (start && !done) begin
            if (count == 5'd0) begin
                // Check for division by zero
                if (divisor == 32'h0) begin
                    quotient <= 32'hFFFFFFFF;
                    remainder <= dividend;
                    div_by_zero <= 1'b1;
                    done <= 1'b1;
                end else begin
                    // Initialize
                    dividend_sign <= is_signed && dividend[31];
                    divisor_sign <= is_signed && divisor[31];
                    divisor_reg <= (is_signed && divisor[31]) ? -divisor : divisor;
                    remainder_reg <= {32'h0, (is_signed && dividend[31]) ? -dividend : dividend};
                    quotient_reg <= 32'h0;
                    count <= 5'd1;
                    div_by_zero <= 1'b0;
                end
            end else if (count <= 5'd32) begin
                // Non-restoring division algorithm
                remainder_reg <= remainder_reg << 1;
                if (remainder_reg[63:32] >= divisor_reg) begin
                    remainder_reg[63:32] <= remainder_reg[63:32] - divisor_reg;
                    quotient_reg <= {quotient_reg[30:0], 1'b1};
                end else begin
                    quotient_reg <= {quotient_reg[30:0], 1'b0};
                end
                count <= count + 1;
            end else begin
                // Sign correction
                quotient <= (dividend_sign ^ divisor_sign) ? -quotient_reg : quotient_reg;
                remainder <= dividend_sign ? -remainder_reg[31:0] : remainder_reg[31:0];
                done <= 1'b1;
                count <= 5'd0;
            end
        end else if (!start) begin
            done <= 1'b0;
        end
    end
endmodule
```

**M Extension Instructions:**
```
DIV  : Divide (signed)
DIVU : Divide (unsigned)
REM  : Remainder (signed)
REMU : Remainder (unsigned)
```

**Test Cases:**
```verilog
// Test division: 100 / 7 = 14 remainder 2
dividend = 32'd100; divisor = 32'd7;
#340 assert(quotient == 32'd14) else $error("DIV failed!");
     assert(remainder == 32'd2) else $error("REM failed!");

// Test division by zero
dividend = 32'd100; divisor = 32'd0;
#340 assert(div_by_zero == 1'b1) else $error("Divide by zero not detected!");
```

**Milestone:** Execute multiply/divide instructions ✅

---

### Week 11: Interrupt Controller

#### Step 11: CSR (Control and Status Registers) (10 hours)

**Module:** `csr_unit.v`

**Required CSRs:**
```
mstatus   : Machine status register
mie       : Machine interrupt enable
mip       : Machine interrupt pending
mtvec     : Machine trap vector base address
mepc      : Machine exception PC
mcause    : Machine trap cause
mscratch  : Machine scratch register
```

**Implementation:**
```verilog
module csr_unit (
    input  wire        clk,
    input  wire        rst_n,

    // CSR read/write interface
    input  wire [11:0] csr_addr,
    input  wire [31:0] csr_wdata,
    input  wire        csr_we,
    output reg  [31:0] csr_rdata,

    // Interrupt interface
    input  wire [4:0]  irq_pending,
    output wire        irq_enable,
    output wire [31:0] trap_vector,

    // Trap handling
    input  wire        trap_enter,
    input  wire        trap_return,
    input  wire [31:0] trap_pc,
    input  wire [31:0] trap_cause,
    output reg  [31:0] trap_epc
);
    // CSR registers
    reg [31:0] mstatus;   // Machine status
    reg [31:0] mie;       // Interrupt enable
    reg [31:0] mip;       // Interrupt pending
    reg [31:0] mtvec;     // Trap vector
    reg [31:0] mepc;      // Exception PC
    reg [31:0] mcause;    // Trap cause
    reg [31:0] mscratch;  // Scratch register

    // mstatus bit positions
    localparam MIE_BIT = 3;   // Machine interrupt enable
    localparam MPIE_BIT = 7;  // Previous interrupt enable

    assign irq_enable = mstatus[MIE_BIT];
    assign trap_vector = mtvec;
    assign trap_epc = mepc;

    // Update interrupt pending register
    always @(posedge clk) begin
        mip[4:0] <= irq_pending;
    end

    // CSR read
    always @(*) begin
        case (csr_addr)
            12'h300: csr_rdata = mstatus;
            12'h304: csr_rdata = mie;
            12'h344: csr_rdata = mip;
            12'h305: csr_rdata = mtvec;
            12'h341: csr_rdata = mepc;
            12'h342: csr_rdata = mcause;
            12'h340: csr_rdata = mscratch;
            default: csr_rdata = 32'h0;
        endcase
    end

    // CSR write
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            mstatus <= 32'h0;
            mie <= 32'h0;
            mtvec <= 32'h0;
            mepc <= 32'h0;
            mcause <= 32'h0;
            mscratch <= 32'h0;
        end else begin
            if (trap_enter) begin
                // Save current state and disable interrupts
                mepc <= trap_pc;
                mcause <= trap_cause;
                mstatus[MPIE_BIT] <= mstatus[MIE_BIT];  // Save current IE
                mstatus[MIE_BIT] <= 1'b0;               // Disable interrupts
            end else if (trap_return) begin
                // Restore previous state
                mstatus[MIE_BIT] <= mstatus[MPIE_BIT];
                mstatus[MPIE_BIT] <= 1'b1;
            end else if (csr_we) begin
                case (csr_addr)
                    12'h300: mstatus <= csr_wdata;
                    12'h304: mie <= csr_wdata;
                    12'h305: mtvec <= csr_wdata;
                    12'h341: mepc <= csr_wdata;
                    12'h342: mcause <= csr_wdata;
                    12'h340: mscratch <= csr_wdata;
                endcase
            end
        end
    end
endmodule
```

**Checkpoint:** CSR operations (csrrw, csrrs, csrrc) work correctly

---

#### Step 12: Interrupt Controller (8 hours)

**Module:** `interrupt_controller.v`

**Features:**
- 5 priority levels
- Vectored interrupts
- Interrupt masking
- Interrupt pending flags

**Implementation:**
```verilog
module interrupt_controller (
    input  wire       clk,
    input  wire       rst_n,

    // Interrupt requests
    input  wire [4:0] irq_lines,      // 5 interrupt lines
    input  wire [4:0] irq_enable,     // Per-interrupt enable
    input  wire       global_enable,  // Global interrupt enable

    // Interrupt acknowledge
    input  wire       irq_ack,

    // Outputs to core
    output reg        irq_pending,
    output reg  [2:0] irq_id,         // Which interrupt (0-4)
    output reg  [31:0] irq_vector     // Interrupt vector address
);
    // Priority encoder (higher number = higher priority)
    always @(*) begin
        irq_pending = 1'b0;
        irq_id = 3'd0;
        irq_vector = 32'h0;

        if (global_enable) begin
            // Check interrupts from highest to lowest priority
            if (irq_lines[4] && irq_enable[4]) begin
                irq_pending = 1'b1;
                irq_id = 3'd4;
                irq_vector = 32'h00000040;  // Vector for IRQ 4
            end else if (irq_lines[3] && irq_enable[3]) begin
                irq_pending = 1'b1;
                irq_id = 3'd3;
                irq_vector = 32'h00000030;  // Vector for IRQ 3
            end else if (irq_lines[2] && irq_enable[2]) begin
                irq_pending = 1'b1;
                irq_id = 3'd2;
                irq_vector = 32'h00000020;  // Vector for IRQ 2
            end else if (irq_lines[1] && irq_enable[1]) begin
                irq_pending = 1'b1;
                irq_id = 3'd1;
                irq_vector = 32'h00000010;  // Vector for IRQ 1
            end else if (irq_lines[0] && irq_enable[0]) begin
                irq_pending = 1'b1;
                irq_id = 3'd0;
                irq_vector = 32'h00000000;  // Vector for IRQ 0
            end
        end
    end

    // Interrupt pending register (sticky)
    reg [4:0] irq_pending_reg;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            irq_pending_reg <= 5'b0;
        end else begin
            // Set pending bit when interrupt arrives
            irq_pending_reg <= irq_pending_reg | irq_lines;

            // Clear pending bit when acknowledged
            if (irq_ack) begin
                irq_pending_reg[irq_id] <= 1'b0;
            end
        end
    end
endmodule
```

**Test Program:**
```c
// Timer interrupt handler
void timer_isr(void) __attribute__((interrupt));
void timer_isr(void) {
    // Read ADC values
    adc_read();

    // Execute control algorithm
    pr_controller_step();

    // Update PWM
    pwm_update();

    // Clear interrupt flag
    clear_timer_interrupt();
}

int main(void) {
    // Enable timer interrupt
    enable_timer_interrupt();
    enable_global_interrupts();

    while (1) {
        // Background tasks
    }
}
```

**Milestone:** Handle timer interrupts correctly ✅

---

### Week 12: Integration and Testing

#### Step 13: Full System Integration (12 hours)

**Top-Level Module:** `riscv_core_top.v`

**Integrate All Components:**
1. Fetch stage
2. Decode/Execute stage
3. Writeback stage
4. Multiplier/Divider
5. CSR unit
6. Interrupt controller
7. Wishbone bus interface

**3-Stage Pipeline:**
```
┌─────────────────────────────────────────────────────────────┐
│                    STAGE 1: FETCH                           │
│  ┌──────┐       ┌──────────────┐       ┌──────────────┐    │
│  │  PC  │──────▶│ Instruction  │──────▶│ Instruction  │    │
│  └──────┘       │    Memory    │       │   Register   │    │
│                 └──────────────┘       └──────────────┘    │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              STAGE 2: DECODE / EXECUTE                      │
│  ┌──────────┐   ┌──────────┐   ┌─────┐   ┌──────────────┐ │
│  │ Decoder  │──▶│ Register │──▶│ ALU │──▶│ Result       │ │
│  └──────────┘   │  File    │   └─────┘   │ Register     │ │
│                 └──────────┘              └──────────────┘ │
│                      │                                      │
│                      └──────▶ Branch Unit                   │
│                                                             │
│                     Multiplier / Divider (multi-cycle)      │
│                     Memory Access (Wishbone)                │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   STAGE 3: WRITEBACK                        │
│  ┌──────────────┐        ┌──────────────┐                  │
│  │  Result MUX  │───────▶│   Register   │                  │
│  │ (ALU/MEM/PC) │        │     File     │                  │
│  └──────────────┘        └──────────────┘                  │
└─────────────────────────────────────────────────────────────┘
```

**Pipeline Hazards to Handle:**
1. **Data hazards:** Forwarding or stalling
2. **Control hazards:** Branch prediction or flush
3. **Structural hazards:** Multi-cycle operations

**Simplified Hazard Handling:**
```verilog
// Data hazard detection
wire data_hazard = (rs1_addr == prev_rd_addr && prev_reg_write) ||
                   (rs2_addr == prev_rd_addr && prev_reg_write);

// Stall pipeline if hazard detected
wire pipeline_stall = data_hazard ||
                     multiplier_busy ||
                     divider_busy ||
                     mem_busy;

// Flush pipeline on branch/jump
wire pipeline_flush = branch_taken || jump || trap_enter;
```

**Checkpoint:** Full system simulates and executes test programs

---

#### Step 14: RISC-V Compliance Testing (8 hours)

**Test Suite:** https://github.com/riscv/riscv-arch-test

**Test Categories:**
```
1. RV32I Base Tests
   - Arithmetic (ADD, SUB, etc.)
   - Logic (AND, OR, XOR)
   - Shifts (SLL, SRL, SRA)
   - Branches (BEQ, BNE, BLT, etc.)
   - Jumps (JAL, JALR)
   - Load/Store (LB, LH, LW, SB, SH, SW)
   - Immediate (ADDI, ANDI, etc.)

2. RV32M Extension Tests
   - Multiply (MUL, MULH, MULHU, MULHSU)
   - Divide (DIV, DIVU, REM, REMU)

3. Interrupt Tests
   - Timer interrupt
   - External interrupt
   - Nested interrupts
```

**Running Tests:**
```bash
cd verification/riscv_tests
make test-rv32i
make test-rv32m

# Expected output:
# RV32I tests: 40/40 PASSED
# RV32M tests: 8/8 PASSED
```

**Milestone:** Pass all RV32IM compliance tests ✅

---

#### Step 15: Performance Benchmarking (4 hours)

**Benchmark Programs:**
```c
// 1. Dhrystone benchmark
// 2. CoreMark benchmark
// 3. Control algorithm execution time
```

**Metrics to Measure:**
```
- Instructions per cycle (IPC)
- Clock cycles per control loop iteration
- Interrupt latency
- Memory access latency
```

**Expected Performance:**
```
Clock: 50-100 MHz
IPC: 0.5-0.8 (due to stalls and multi-cycle ops)
Control loop: ~50 μs @ 50 MHz
Interrupt latency: < 500 ns
```

**Final Milestone:** Core meets all performance requirements ✅

---

## Milestone Testing

### Testing Strategy

**Level 1: Unit Tests** (Each module)
- Test individual functionality
- Use directed test vectors
- Verify edge cases

**Level 2: Integration Tests** (Subsystems)
- Test multiple modules together
- Use small assembly programs
- Verify interfaces

**Level 3: System Tests** (Full core)
- Run complete programs
- Use RISC-V compliance tests
- Verify timing and performance

**Level 4: Application Tests** (Control algorithms)
- Port control code from STM32
- Run inverter control simulation
- Verify against MATLAB reference

### Test Programs Roadmap

```
Week 3-4:  add_test.s, sub_test.s, logic_test.s
Week 5-6:  branch_test.s, loop_test.s, factorial.s
Week 7-8:  load_store_test.s, array_sum.s, string_copy.s
Week 9-10: multiply_test.s, divide_test.s, fixed_point.s
Week 11:   interrupt_test.s, timer_isr.s
Week 12:   full_control_algorithm.c
```

---

## Code Organization

### Directory Structure

```
riscv/
├── rtl/
│   └── core/
│       ├── riscv_core_top.v          # Top-level
│       ├── riscv_defines.vh          # Constants
│       ├── fetch.v                   # Fetch stage
│       ├── decode.v                  # Decoder
│       ├── execute.v                 # Execute stage
│       ├── writeback.v               # Writeback stage
│       ├── regfile.v                 # Register file
│       ├── alu.v                     # ALU
│       ├── branch_unit.v             # Branch logic
│       ├── pc_unit.v                 # Program counter
│       ├── multiplier.v              # Multiplier
│       ├── divider.v                 # Divider
│       ├── csr_unit.v                # CSR registers
│       ├── interrupt_controller.v    # Interrupts
│       └── wishbone_master.v         # Bus interface
├── sim/
│   ├── testbenches/
│   │   ├── tb_regfile.v
│   │   ├── tb_alu.v
│   │   ├── tb_decode.v
│   │   ├── tb_core_simple.v
│   │   └── tb_riscv_core_top.v
│   └── programs/
│       ├── add_test.s
│       ├── factorial.s
│       └── control_algorithm.c
├── verification/
│   └── riscv_tests/
│       └── (compliance test suite)
└── tools/
    ├── Makefile
    └── assemble.sh
```

### File Naming Conventions

- **Modules:** `module_name.v`
- **Testbenches:** `tb_module_name.v`
- **Headers:** `header_name.vh`
- **Assembly:** `program_name.s`
- **C programs:** `program_name.c`

---

## Common Pitfalls

### 1. Sign Extension Errors

**Problem:** Forgetting to sign-extend immediates

**Solution:**
```verilog
// WRONG: Zero-extend signed immediate
immediate = {20'b0, instruction[31:20]};

// CORRECT: Sign-extend
immediate = {{20{instruction[31]}}, instruction[31:20]};
```

### 2. Branch Target Calculation

**Problem:** Incorrect PC-relative addressing

**Solution:**
```verilog
// Branch offset is PC-relative, not absolute
branch_target = pc + immediate;  // NOT just immediate
```

### 3. Register x0 Not Hardwired

**Problem:** Allowing writes to x0

**Solution:**
```verilog
// In register file write logic
if (wr_en && rd_addr != 5'd0) begin  // Check rd_addr != 0
    registers[rd_addr] <= rd_data;
end
```

### 4. Pipeline Hazards Not Handled

**Problem:** RAW (read-after-write) hazards

**Solution:**
```verilog
// Stall pipeline or forward results
wire data_hazard = (rs1_addr == prev_rd_addr) && prev_reg_write;
wire stall = data_hazard;
```

### 5. Byte Enable for Memory Access

**Problem:** Writing full word when should write byte

**Solution:**
```verilog
// Generate correct byte enable based on address and access width
case (mem_width)
    3'b000: byte_enable = (4'b0001 << mem_addr[1:0]);  // Byte
    3'b001: byte_enable = (4'b0011 << mem_addr[1]);    // Half-word
    3'b010: byte_enable = 4'b1111;                      // Word
endcase
```

### 6. Multiply/Divide Timing

**Problem:** Not stalling pipeline during multi-cycle ops

**Solution:**
```verilog
wire pipeline_stall = multiplier_busy || divider_busy;
```

### 7. Interrupt Priority

**Problem:** Low-priority interrupt blocking high-priority

**Solution:**
```verilog
// Check interrupts from highest to lowest priority
if (irq[4]) ...
else if (irq[3]) ...
else if (irq[2]) ...
```

---

## Resources

### Official Documentation

1. **RISC-V ISA Manual**
   - https://riscv.org/technical/specifications/
   - Chapters: RV32I, RV32M, Privileged Architecture

2. **RISC-V Assembly Programmer's Manual**
   - https://github.com/riscv/riscv-asm-manual

### Open-Source Reference Implementations

1. **PicoRV32** (Simple, educational)
   - https://github.com/YosysHQ/picorv32
   - Good starting point for understanding

2. **SERV** (Bit-serial, minimal)
   - https://github.com/olofk/serv
   - Shows how small a RISC-V core can be

3. **VexRiscv** (Configurable, high-performance)
   - https://github.com/SpinalHDL/VexRiscv
   - Written in SpinalHDL, but good architecture

### Tutorials and Courses

1. **Building a RISC-V CPU Core**
   - https://github.com/stevehoover/RISC-V_MYTH_Workshop
   - 5-day workshop with TL-Verilog

2. **Nand2Tetris (for background)**
   - https://www.nand2tetris.org/
   - Build computer from logic gates up

### Tools

1. **Verilator** (Fast simulator)
   - https://www.veripool.org/verilator/

2. **GTKWave** (Waveform viewer)
   - http://gtkwave.sourceforge.net/

3. **RISC-V GNU Toolchain**
   - https://github.com/riscv/riscv-gnu-toolchain

### Books

1. **"Computer Organization and Design: RISC-V Edition"**
   - Patterson & Hennessy
   - Chapter 4 (The Processor) is essential

2. **"The RISC-V Reader"**
   - Patterson & Waterman
   - Quick overview of RISC-V ISA

3. **"Digital Design and Computer Architecture: RISC-V Edition"**
   - Harris & Harris
   - Practical examples in Verilog

---

## Summary

This roadmap takes you from zero to a working RV32IM processor in 12 weeks:

✅ **Week 1-2:** Environment setup, defines, basic infrastructure
✅ **Week 3-4:** Register file, ALU, simple datapath
✅ **Week 5-6:** Branches, jumps, control flow
✅ **Week 7-8:** Memory system, load/store
✅ **Week 9-10:** Multiply/divide (M extension)
✅ **Week 11:** Interrupt controller, CSRs
✅ **Week 12:** Integration, testing, compliance

**End Result:**
- ~2500-3000 lines of Verilog
- Full RV32IM ISA support
- 3-stage pipeline
- Hardware multiply/divide
- Vectored interrupt controller
- RISC-V compliance test passing
- Ready for control algorithm implementation

**Next Steps After Completion:**
1. Integrate with peripherals (PWM, ADC, UART)
2. Port control algorithms from STM32
3. Test with inverter simulation
4. Deploy to FPGA
5. (Optional) Add custom Zpec instructions

---

**Document Status:** ✅ Complete
**Last Updated:** 2025-12-03
**Version:** 1.0

**Good luck with your RISC-V core implementation! 🚀**
