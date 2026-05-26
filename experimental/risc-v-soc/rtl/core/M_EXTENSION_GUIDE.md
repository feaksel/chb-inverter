# M Extension Implementation Guide — Unified MDU Approach

**Goal:** Implement multiply and divide instructions using a unified Multi-cycle Divide/Multiply Unit (MDU)
**Time:** 2-3 hours for full integration and testing
**Difficulty:** Medium (multi-cycle state machine + signed arithmetic handling)
**Benefit:** Native M-extension support (MUL, MULH, MULHSU, MULHU, DIV, DIVU, REM, REMU) with ~32-34 cycle latency per operation

---

## What is the M Extension?

The **M Extension** adds integer multiplication and division to RV32I:

| Instruction | Operation                 | Encoding           | Description                               |
| ----------- | ------------------------- | ------------------ | ----------------------------------------- |
| **MUL**     | rd = (rs1 × rs2)[31:0]    | R-type, funct3=000 | Multiply, lower 32 bits                   |
| **MULH**    | rd = (rs1 × rs2)[63:32]   | R-type, funct3=001 | Multiply signed×signed, upper 32 bits     |
| **MULHSU**  | rd = (rs1 × rs2)[63:32]   | R-type, funct3=010 | Multiply signed×unsigned, upper 32 bits   |
| **MULHU**   | rd = (rs1 × rs2)[63:32]   | R-type, funct3=011 | Multiply unsigned×unsigned, upper 32 bits |
| **DIV**     | rd = rs1 ÷ rs2 (signed)   | R-type, funct3=100 | Divide signed (quotient)                  |
| **DIVU**    | rd = rs1 ÷ rs2 (unsigned) | R-type, funct3=101 | Divide unsigned (quotient)                |
| **REM**     | rd = rs1 % rs2 (signed)   | R-type, funct3=110 | Remainder signed                          |
| **REMU**    | rd = rs1 % rs2 (unsigned) | R-type, funct3=111 | Remainder unsigned                        |

**All M-extension instructions:**

- Use R-type format: `[31:25] funct7=0000001, [24:20] rs2, [19:15] rs1, [14:12] funct3, [11:7] rd, [6:0] opcode=0110011`
- Operate at ~32-34 cycles per instruction (iterative shift-add multiply, restoring divide)
- Follow RISC-V semantics including division-by-zero handling

---

## Architecture Overview: Unified MDU

The M extension is implemented via a **unified Multiply/Divide Unit (MDU)** module that handles both multiply and divide operations. This approach:

- Keeps the main ALU simple and combinational (only handles RV32I operations)
- Implements both operations in a single module with shared state infrastructure
- Uses a simple one-cycle start pulse / done pulse handshake
- Stalls the core pipeline during the ~32 cycle operation

### Design Trade-offs

| Aspect             | Unified MDU               |
| ------------------ | ------------------------- |
| Area               | Smaller (1 state machine) |
| Latency            | 32-34 cycles (MUL or DIV) |
| Control Complexity | Simple (1 start signal)   |
| Reusability        | Good (single module)      |

**We chose Unified MDU for simplicity and smaller area while maintaining good performance.**

---

## Step 1: Add M Extension Definitions to `riscv_defines.vh`

The file `/home/furka/5level-inverter/02-embedded/riscv/rtl/core/riscv_defines.vh` already contains:

```verilog
// Funct7 Codes for ALU Operations
`define FUNCT7_ADD        7'b0000000  // ADD, SRL
`define FUNCT7_SUB        7'b0100000  // SUB, SRA
`define FUNCT7_MUL_DIV    7'b0000001  // M extension (multiply/divide)

// Funct3 Codes for M Extension (Multiply/Divide)
`define FUNCT3_MUL        3'b000  // Multiply (lower 32 bits)
`define FUNCT3_MULH       3'b001  // Multiply (upper 32 bits, signed × signed)
`define FUNCT3_MULHSU     3'b010  // Multiply (upper 32 bits, signed × unsigned)
`define FUNCT3_MULHU      3'b011  // Multiply (upper 32 bits, unsigned × unsigned)
`define FUNCT3_DIV        3'b100  // Divide (signed)
`define FUNCT3_DIVU       3'b101  // Divide (unsigned)
`define FUNCT3_REM        3'b110  // Remainder (signed)
`define FUNCT3_REMU       3'b111  // Remainder (unsigned)

// ALU Operations (for pipeline routing)
`define ALU_OP_MUL        4'd10  // Multiply (lower 32 bits)
`define ALU_OP_MULH       4'd11  // Multiply signed (upper 32 bits)
`define ALU_OP_MULHSU     4'd12  // Multiply signed×unsigned (upper 32 bits)
`define ALU_OP_MULHU      4'd13  // Multiply unsigned (upper 32 bits)
`define ALU_OP_DIV        4'd14  // Divide signed
`define ALU_OP_DIVU       4'd15  // Divide unsigned
```

**No changes needed to `riscv_defines.vh`** — it already includes all M extension definitions.

---

## Step 2: Implement the Unified MDU Module

### File: `rtl/core/mdu.v`

The MDU is a single Verilog module that combines multiply and divide logic. Key aspects:

#### Module Interface

```verilog
module mdu (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        start,          // Start operation (one-cycle pulse)
    input  wire [2:0]  funct3,         // Operation select (determines MUL vs DIV and variants)
    input  wire [31:0] a,              // Operand A (rs1)
    input  wire [31:0] b,              // Operand B (rs2)
    output reg         busy,           // Unit is busy (stall pipeline)
    output reg         done,           // Operation complete (one-cycle pulse)
    output reg [63:0]  product,        // Multiply result: full 64-bit product
    output reg [31:0]  quotient,       // Divide result: quotient
    output reg [31:0]  remainder       // Divide result: remainder
);
```

#### Behavior

1. **IDLE State:** Waits for `start` signal
   - When `start=1` for one cycle, latches `funct3`, `a`, `b` and enters either MUL or DIV state based on `funct3`
2. **MUL State:** Iterative shift-and-add multiply
   - Latches operands at input or takes absolute value if signed
   - Performs 32 iterations of shift-add algorithm
   - On the last iteration, outputs full 64-bit `product`
   - Returns to IDLE and asserts `done` pulse
3. **DIV State:** Iterative long division (restoring algorithm)
   - Converts operands to unsigned absolute values if needed
   - Performs 32 iterations of division
   - Handles division-by-zero (quotient = -1 per RISC-V, remainder = dividend)
   - On completion, outputs `quotient` and `remainder`
   - Returns to IDLE and asserts `done` pulse

#### Signedness Handling

- **MUL variants:**

  - `MULH` (`funct3=001`): Both operands treated as signed; absolute values multiplied, result sign computed as XOR of input signs
  - `MULHSU` (`funct3=010`): rs1 signed, rs2 unsigned; absolute values multiplied, sign based on rs1 sign
  - `MULHU` (`funct3=011`): Both operands treated as unsigned
  - `MUL` (`funct3=000`): Both unsigned (ignores signedness, produces same result as unsigned multiply)

- **DIV variants:**
  - `DIV` (`funct3=100`): Signed division; quotient sign = sign_a XOR sign_b, remainder sign = sign_a
  - `DIVU` (`funct3=101`): Unsigned division; no sign handling needed
  - `REM` (`funct3=110`): Signed remainder; remainder sign = dividend sign
  - `REMU` (`funct3=111`): Unsigned remainder

**The MDU internally detects signedness from `funct3` and applies appropriate conversions.**

---

## Step 3: Update the Instruction Decoder

### File: `rtl/core/decoder.v`

The decoder must recognize M-extension instructions and route them appropriately.

#### Changes Required

1. **Add M-extension detection output:**

   ```verilog
   output reg is_m   // Is M-extension (multiply/divide)
   ```

2. **In the `OPCODE_OP` case, check `funct7`:**

   ```verilog
   `OPCODE_OP: begin
       alu_src_imm = 1'b0;
       reg_write = 1'b1;

       // Check for M-extension (funct7 == 7'b0000001)
       if (funct7 == `FUNCT7_MUL_DIV) begin
           is_m = 1'b1;
           case (funct3)
               `FUNCT3_MUL:    alu_op = `ALU_OP_MUL;
               `FUNCT3_MULH:   alu_op = `ALU_OP_MULH;
               `FUNCT3_MULHSU: alu_op = `ALU_OP_MULHSU;
               `FUNCT3_MULHU:  alu_op = `ALU_OP_MULHU;
               `FUNCT3_DIV:    alu_op = `ALU_OP_DIV;
               `FUNCT3_DIVU:   alu_op = `ALU_OP_DIVU;
               `FUNCT3_REM:    alu_op = `ALU_OP_DIV;  // REM uses DIV hardware
               `FUNCT3_REMU:   alu_op = `ALU_OP_DIVU; // REMU uses DIVU hardware
               default:        alu_op = `ALU_OP_ADD;
           endcase
       end else begin
           is_m = 1'b0;
           // Original RV32I R-type handling (ADD, SUB, AND, OR, etc.)
           case (funct3)
               `FUNCT3_ADD_SUB: alu_op = funct7[5] ? `ALU_OP_SUB : `ALU_OP_ADD;
               // ... rest of RV32I opcodes
           endcase
       end
   end
   ```

**Effect:** When an M-extension instruction is decoded, `is_m=1` and the appropriate `alu_op` is selected (even though it won't be used by the main ALU; instead the core will check `is_m` and route to the MDU).

---

## Step 4: Update the Core Control Path

### File: `rtl/core/custom_riscv_core.v`

The core's execute pipeline must detect M instructions, start the MDU, stall, and capture results.

#### 4.1 Add MDU Control Signals

```verilog
// M-extension (MDU) signals
wire        is_m;                // From decoder
reg         mdu_start;           // Start pulse to MDU
wire        mdu_busy;            // MDU is busy
wire        mdu_done;            // MDU operation complete
wire [63:0] mdu_product;         // MDU multiply result (64-bit)
wire [31:0] mdu_quotient;        // MDU divide result (quotient)
wire [31:0] mdu_remainder;       // MDU divide result (remainder)
reg [31:0]  mdu_result_reg;      // Temporary latch for selected MDU result
```

#### 4.2 Add STATE_MULDIV to State Machine

```verilog
// State machine states
localparam STATE_FETCH     = 3'd0;
localparam STATE_DECODE    = 3'd1;
localparam STATE_EXECUTE   = 3'd2;
localparam STATE_MEM       = 3'd3;
localparam STATE_WRITEBACK = 3'd4;
localparam STATE_MULDIV    = 3'd5;   // NEW: Multi-cycle multiply/divide
```

#### 4.3 Connect Decoder Output

```verilog
decoder decoder_inst (
    .instruction(instruction),
    // ... other ports ...
    .is_m(is_m)  // NEW: M-extension flag
);
```

#### 4.4 Implement EXECUTE → MULDIV Transition

In the `STATE_EXECUTE` block:

```verilog
STATE_EXECUTE: begin
    if (is_m) begin
        // M-extension instruction: start MDU and stall
        mdu_start <= 1'b1;
        state <= STATE_MULDIV;
    end else begin
        // Regular ALU operation
        alu_result_reg <= alu_result;

        if (mem_read || mem_write) begin
            state <= STATE_MEM;
        end else begin
            state <= STATE_WRITEBACK;
        end
    end
end
```

#### 4.5 Implement MULDIV State

Add this new state to the core state machine:

```verilog
STATE_MULDIV: begin
    // Clear the one-cycle start pulse
    mdu_start <= 1'b0;

    // Wait for MDU to complete
    if (mdu_done) begin
        // Select result based on funct3
        case (funct3)
            `FUNCT3_MUL:    mdu_result_reg <= mdu_product[31:0];      // Lower 32 bits
            `FUNCT3_MULH:   mdu_result_reg <= mdu_product[63:32];     // Upper 32 bits (signed*signed)
            `FUNCT3_MULHSU: mdu_result_reg <= mdu_product[63:32];     // Upper 32 bits (signed*unsigned)
            `FUNCT3_MULHU:  mdu_result_reg <= mdu_product[63:32];     // Upper 32 bits (unsigned*unsigned)
            `FUNCT3_DIV:    mdu_result_reg <= mdu_quotient;           // Quotient (signed)
            `FUNCT3_DIVU:   mdu_result_reg <= mdu_quotient;           // Quotient (unsigned)
            `FUNCT3_REM:    mdu_result_reg <= mdu_remainder;          // Remainder (signed)
            `FUNCT3_REMU:   mdu_result_reg <= mdu_remainder;          // Remainder (unsigned)
            default:        mdu_result_reg <= mdu_product[31:0];
        endcase

        alu_result_reg <= mdu_result_reg;
        state <= STATE_WRITEBACK;
    end else begin
        // Still waiting; remain in MULDIV
        state <= STATE_MULDIV;
    end
end
```

#### 4.6 Instantiate MDU Module

Add this module instantiation in the core (typically near other peripheral instantiations):

```verilog
mdu mdu_inst (
    .clk(clk),
    .rst_n(rst_n),
    .start(mdu_start),
    .funct3(funct3),
    .a(rs1_data),
    .b(rs2_data),
    .busy(mdu_busy),
    .done(mdu_done),
    .product(mdu_product),
    .quotient(mdu_quotient),
    .remainder(mdu_remainder)
);
```

#### 4.7 Initialize MDU Control Signals on Reset

In the reset block:

```verilog
if (!rst_n) begin
    // ... existing reset code ...
    mdu_start <= 1'b0;
    mdu_result_reg <= 32'd0;
end
```

---

## Step 5: Verification and Testing

### 5.1 Unit-Level Testbench (MDU standalone)

Create a testbench file: `sim/testbench/tb_mdu.v`

This testbench:

- Instantiates the MDU module
- Applies test vectors for all 8 M-extension operations
- Checks results against expected values

### 5.2 Integration Testing

The full core testbench should exercise:

- All multiply variants with various operand combinations (positive, negative, mixed)
- All divide variants including division-by-zero
- Back-to-back M instructions to verify pipelining/stalling behavior
- Mixed M and non-M instructions to verify pipeline integration

---

## Step 6: Integration Checklist

Before committing M-extension support, verify:

- [ ] `riscv_defines.vh` contains all `FUNCT3_*` and `ALU_OP_*` defines (already present)
- [ ] `decoder.v` detects M-extension and sets `is_m` flag
- [ ] `decoder.v` maps `funct3` to correct `alu_op` codes
- [ ] `custom_riscv_core.v` includes `STATE_MULDIV` state
- [ ] `custom_riscv_core.v` implements EXECUTE→MULDIV→WRITEBACK flow
- [ ] `mdu.v` is instantiated in the core with correct port connections
- [ ] MDU control signals are initialized on reset
- [ ] Testbench exercises all 8 M operations with edge cases
- [ ] Simulation passes without errors
- [ ] (Optional) Synthesize with target FPGA tool and verify timing

---

## Edge Cases and Special Behaviors

### Multiply Edge Cases

| Operation | Input           | Expected Output | Behavior                                         |
| --------- | --------------- | --------------- | ------------------------------------------------ |
| MUL       | 2^31-1 × 2^31-1 | Lower 32 bits   | Wraps naturally                                  |
| MULH      | -1 × -1         | 0               | (-1)×(-1) = 1; upper=0                           |
| MULHSU    | -1 × -1         | 0xFFFFFFFF      | Treated as signed×unsigned; result=-1 upper part |
| DIV       | -2^31 / -1      | -2^31           | Overflow case; result unchanged per spec         |

### Division Edge Cases

| Operation | Input      | Expected Output | Behavior                              |
| --------- | ---------- | --------------- | ------------------------------------- |
| DIV       | x / 0      | -1 (0xFFFFFFFF) | Division by zero; quotient=-1         |
| REM       | x / 0      | x               | Division by zero; remainder=dividend  |
| DIV       | -2^31 / -1 | -2^31           | Overflow; result is operand unchanged |

---

## Performance Considerations

- **Multiply latency:** 32 cycles (shift-add algorithm, 32 iterations)
- **Divide latency:** ~32 cycles (restoring algorithm, 32 iterations)
- **Pipeline stall:** Core remains in `STATE_MULDIV` for entire operation duration
- **Throughput:** Approximately 1 M-instruction per 34 cycles (32 iterations + state transitions)

---

## Debug Tips

1. **Monitor MDU signals in simulation:**

   - `mdu_start`: Should pulse for one cycle when an M instruction enters EXECUTE
   - `mdu_busy`: Should go high immediately after `mdu_start`, low when `mdu_done` pulses
   - `mdu_done`: Should pulse for one cycle when operation completes

2. **Verify state machine transitions:**

   - Trace the core state: EXECUTE → MULDIV → WRITEBACK
   - Check that `alu_result_reg` receives the correct 32-bit result from `mdu_result_reg`

3. **Validate funct3 routing:**
   - Use `$display` or waveforms to confirm correct `funct3` value reaches MDU
   - Verify result selection matches `funct3` (e.g., `MULH` selects `product[63:32]`, not `product[31:0]`)

---

## Summary

**What you implemented:**

- 8 new instructions (MUL, MULH, MULHSU, MULHU, DIV, DIVU, REM, REMU)
- 64-bit multiply logic (32×32→64)
- 32-bit divide logic via iterative algorithm
- Unified MDU module with multiply/divide state machine
- Decoder changes to recognize funct7 = 0000001
- Core pipeline integration with STATE_MULDIV stall state

**Benefits:**

- 10-100× speedup for math-heavy code
- Can compile with `-march=rv32im` (native multiply/divide)
- Simpler core control than separate units

**Time spent:**

- Implementation: ~2-3 hours
- Testing and debugging: ~1-2 hours

---

**Congratulations!** Your RISC-V core now has hardware multiply/divide via the unified MDU! 🚀
