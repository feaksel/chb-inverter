# MDU Stalling and Pipeline Behavior

**Understanding Multi-Cycle Operations in Your RISC-V Core**

---

## The Problem: Multi-Cycle Operations in a Pipelined Core

### Why MDU Takes Multiple Cycles

Looking at your `mdu.v`, the multiply-divide unit is **sequential** (not combinational):

```verilog
// From mdu.v
localparam IDLE = 2'd0;
localparam MUL  = 2'd1;
localparam DIV  = 2'd2;

// Multiply takes 32 iterations (shift-and-add)
if (mul_count < 32) begin
    // ... multiply logic
    mul_count <= mul_count + 1;
end

// Divide takes 32 iterations (long division)
if (div_count < 32) begin
    // ... divide logic
    div_count <= div_count + 1;
end
```

**Result:**
- Multiply: **~33 cycles** (1 setup + 32 iterations)
- Divide: **~33 cycles** (1 setup + 32 iterations)

Compare to ALU operations: **1 cycle**

---

## Pipeline Without Stalling (INCORRECT)

### What Would Happen Without Stall Logic

```
Clock Cycle:   1      2      3      4      5      6      7      ...    35     36
              ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Instruction 1: │ IF  │ ID  │ EX (MUL starts)                          │ WB  │
(MUL x1,x2,x3) │     │     │  └──────────────────────────────────────►│     │
                                     (should take 33 cycles)

Instruction 2: │     │ IF  │ ID  │ EX  │ WB  │  ❌ WRONG!
(ADD x4,x1,x5) │     │     │     │     │     │
                            └──► Uses x1 before MUL finishes!
                                 x1 still has OLD value!

Instruction 3: │     │     │ IF  │ ID  │ EX  │ WB  │  ❌ WRONG!
(SUB x6,x1,x7) │     │     │     │     │     │
                            └──► Also uses x1 too early!
```

**Problem:** Instructions 2 and 3 try to use `x1` before the MUL completes!

This is called a **Read-After-Write (RAW) hazard** or **data hazard**.

---

## Pipeline With Stalling (CORRECT)

### How Stalling Works

When the MDU is busy, the core **freezes** the pipeline:

```
Clock Cycle:   1      2      3      4      5      6    ...    35     36     37
              ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Instruction 1: │ IF  │ ID  │ EX (MUL starts) ───────────────────────►│ WB  │
(MUL x1,x2,x3) │     │     │  busy=1 ─────────────────────────────►│ done │
               │     │     │                                         │      │

Instruction 2: │     │ IF  │ ID  │ STALL... (waiting for MUL)────────►│ ID  │ EX  │ WB
(ADD x4,x1,x5) │     │     │     │                                   │     │     │
               │     │     │     │◄─ Pipeline frozen ────────────────┘     │     │
                                                                    └─► Now x1 ready!

Instruction 3: │     │     │ IF  │ STALL... (waiting) ─────────────────────►│ IF  │ ID
(SUB x6,x1,x7) │     │     │     │                                         │     │
                            └──► Fetch also stalled
```

**Key Points:**
1. **MDU busy signal** prevents pipeline from advancing
2. **Instructions queue up** behind the MDU operation
3. **PC doesn't increment** during stall
4. **Result is correct** - no data hazards!

---

## How Stalling is Implemented

### 1. MDU Busy Signal

From your `mdu.v`:

```verilog
output reg busy,
output reg done,

always @(posedge clk or negedge rst_n) begin
    case (state)
        IDLE: begin
            done <= 1'b0;
            if (start) begin
                busy <= 1'b1;  // ← Signal starts here
                state <= MUL or DIV;
            end
        end

        MUL: begin
            if (mul_count < 32) begin
                // Still computing...
                // busy stays 1
            end else begin
                busy <= 1'b0;   // ← Signal clears here
                done <= 1'b1;   // ← Result ready
                state <= IDLE;
            end
        end
    endcase
end
```

**Signals:**
- `busy = 1` → MDU is computing, pipeline must stall
- `busy = 0, done = 1` → Result ready, pipeline can continue
- `done` is a 1-cycle pulse to latch the result

### 2. Core Stall Logic

In your `custom_riscv_core.v`, you need:

```verilog
// Stall signal generation
wire mdu_stall = mdu_busy;  // Stall if MDU is busy

// In state machine:
STATE_EXECUTE: begin
    if (is_m) begin
        // M extension instruction (MUL/DIV)
        mdu_start <= 1'b1;
        state <= STATE_MDU_WAIT;
    end else begin
        // Regular instruction
        // ... normal execution
    end
end

STATE_MDU_WAIT: begin
    mdu_start <= 1'b0;

    if (mdu_done) begin
        // Result ready, capture it
        rd_data <= (funct3 == DIV || funct3 == REM) ?
                   mdu_quotient : mdu_product[31:0];
        state <= STATE_WB;
    end
    // else: stay in this state (stall)
end

// PC update logic:
always @(posedge clk) begin
    if (!mdu_stall && !other_stalls) begin
        pc <= pc_next;  // Only update PC when not stalled
    end
    // else: PC stays the same (stall)
end
```

### 3. Pipeline Control During Stall

```verilog
// Prevent fetch when stalled
assign iwb_stb_o = (state == STATE_FETCH) && !mdu_stall;

// Prevent decode advancement
always @(posedge clk) begin
    if (!mdu_stall) begin
        instruction_reg <= iwb_dat_i;  // Latch new instruction
    end
    // else: keep old instruction
end

// Prevent writeback when not ready
assign reg_write_enable = reg_write && !mdu_stall && state == STATE_WB;
```

---

## Detailed Pipeline Timing Example

### Example: Three Instructions with MUL

```assembly
MUL  x1, x2, x3    # Takes 33 cycles
ADD  x4, x1, x5    # Depends on x1 (data hazard!)
SUB  x6, x4, x7    # Depends on x4
```

### Cycle-by-Cycle Breakdown

```
Cycle  PC    State         Instruction      Action
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  1   0x100  FETCH         -                Fetch MUL instruction
  2   0x100  DECODE        MUL x1,x2,x3     Decode MUL
  3   0x100  EXECUTE       MUL x1,x2,x3     Start MDU (mdu_start=1, busy=1)
  4   0x100  MDU_WAIT      MUL x1,x2,x3     MDU computing... busy=1, stall=1
  5   0x100  MDU_WAIT      MUL x1,x2,x3     MDU computing... (iter 1)
  6   0x100  MDU_WAIT      MUL x1,x2,x3     MDU computing... (iter 2)
  ...
 35   0x100  MDU_WAIT      MUL x1,x2,x3     MDU computing... (iter 32)
 36   0x100  MDU_WAIT      MUL x1,x2,x3     MDU done! (done=1, busy=0)
 37   0x104  WB            MUL x1,x2,x3     Write result to x1, PC+=4
 38   0x104  FETCH         -                Fetch ADD instruction (finally!)
 39   0x104  DECODE        ADD x4,x1,x5     Decode ADD, x1 now has correct value ✓
 40   0x108  EXECUTE       ADD x4,x1,x5     Execute ADD
 41   0x108  WB            ADD x4,x1,x5     Write result to x4, PC+=4
 42   0x10C  FETCH         -                Fetch SUB instruction
 43   0x10C  DECODE        SUB x6,x4,x7     Decode SUB
 44   0x110  EXECUTE       SUB x6,x4,x7     Execute SUB
 45   0x110  WB            SUB x6,x4,x7     Write result to x6, PC+=4
```

**Key Observations:**
1. **PC stays at 0x100** from cycles 1-37 (stalled)
2. **ADD instruction waits** until MUL completes
3. **Total cycles for MUL:** 36 cycles (fetch + decode + execute + wait + wb)
4. **No data hazard** because pipeline is stalled

---

## Effects of Stalling on Performance

### Performance Impact

**Without M extension (only ALU operations):**
```
CPI (Cycles Per Instruction) ≈ 1-2
(with simple pipeline)
```

**With M extension (including MUL/DIV):**
```
CPI ≈ 1-2 for most instructions
CPI ≈ 36 for MUL/DIV

Average CPI depends on how often you use MUL/DIV
```

### Example: Control Loop Performance

**Without Hardware Multiply:**
```c
// Software multiply (shift-and-add in C)
int32_t result = a * b;  // ~50-100 instructions, ~60-120 cycles
```

**With Hardware Multiply (MDU):**
```assembly
MUL x1, x2, x3  # 1 instruction, ~36 cycles
```

**With Zpec Multiply-Accumulate:**
```assembly
ZPEC.MAC x1, x2, x3, x4  # 1 instruction, ~3 cycles (pipelined)
```

### Stall Impact on Different Code

**Example 1: Compute-Heavy Code**
```assembly
# Many MUL/DIV operations
MUL  x1, x2, x3    # 36 cycles
MUL  x4, x5, x6    # 36 cycles
MUL  x7, x8, x9    # 36 cycles
DIV  x10, x11, x12 # 36 cycles
# Total: 144 cycles for 4 instructions
# CPI = 36
```

**Example 2: Mixed Code**
```assembly
# Mix of operations
ADD  x1, x2, x3    # 2 cycles
MUL  x4, x1, x5    # 36 cycles
ADD  x6, x4, x7    # 2 cycles
SUB  x8, x6, x9    # 2 cycles
# Total: 42 cycles for 4 instructions
# CPI = 10.5
```

**Example 3: ALU-Only Code**
```assembly
# No multiply/divide
ADD  x1, x2, x3    # 2 cycles
SUB  x4, x5, x6    # 2 cycles
AND  x7, x8, x9    # 2 cycles
OR   x10, x11, x12 # 2 cycles
# Total: 8 cycles for 4 instructions
# CPI = 2
```

---

## Common Issues and Solutions

### Issue 1: MDU Never Completes

**Symptom:** Core hangs in MDU_WAIT state forever

**Possible Causes:**
```verilog
// ❌ WRONG: done pulse too short
always @(posedge clk) begin
    if (count == 32) begin
        done <= 1'b1;  // Set done
    end
    done <= 1'b0;      // Immediately clear! ❌
end

// ✓ CORRECT: done stays high until start clears
always @(posedge clk) begin
    if (count == 32) begin
        done <= 1'b1;
        state <= IDLE;
    end else if (!start) begin
        done <= 1'b0;  // Clear only when not starting
    end
end
```

**Debug:**
```verilog
// Add to simulation
always @(posedge clk) begin
    if (mdu_busy) begin
        $display("MDU busy: count=%d, state=%d", mul_count, state);
    end
    if (mdu_done) begin
        $display("MDU done! Result ready");
    end
end
```

### Issue 2: Results Corrupted

**Symptom:** Multiply/divide gives wrong results

**Possible Causes:**

1. **Result captured at wrong time:**
```verilog
// ❌ WRONG: Capture before done
if (mdu_busy) begin
    rd_data <= mdu_product;  // Still computing! ❌
end

// ✓ CORRECT: Capture when done
if (mdu_done) begin
    rd_data <= mdu_product;  // Result ready ✓
end
```

2. **Wrong output selected:**
```verilog
// Check funct3 to select correct output
case (funct3)
    `FUNCT3_MUL:    rd_data <= product[31:0];   // Lower 32 bits
    `FUNCT3_MULH:   rd_data <= product[63:32];  // Upper 32 bits
    `FUNCT3_DIV:    rd_data <= quotient;
    `FUNCT3_REM:    rd_data <= remainder;
endcase
```

### Issue 3: Pipeline Deadlock

**Symptom:** Core stalls on non-MDU instruction after MDU

**Possible Causes:**
```verilog
// ❌ WRONG: Stall signal not cleared
assign stall = mdu_busy;  // But mdu_busy might stick high!

// ✓ CORRECT: Stall only when actually waiting
assign stall = (state == STATE_MDU_WAIT) && mdu_busy;
```

### Issue 4: Data Hazard Not Caught

**Symptom:** Subsequent instruction uses old register value

**Solution:** Ensure stall logic prevents fetch:
```verilog
// Prevent PC increment during stall
always @(posedge clk) begin
    if (rst_n && !stall) begin
        pc <= pc_next;
    end
    // else PC stays same (stall)
end

// Prevent instruction fetch during stall
assign iwb_stb_o = fetch_enable && !stall;
```

---

## Optimization: Result Forwarding (Advanced)

Instead of always stalling, you can **forward** the result if it's ready:

```verilog
// In decode stage:
wire raw_hazard_rs1 = (rs1_addr == prev_rd_addr) && prev_rd_wen;
wire raw_hazard_rs2 = (rs2_addr == prev_rd_addr) && prev_rd_wen;

// Forwarding mux
always @(*) begin
    if (mdu_done && raw_hazard_rs1) begin
        rs1_data_forwarded = mdu_result;  // Forward from MDU
    end else begin
        rs1_data_forwarded = rs1_data;    // Normal read
    end
end
```

This allows:
```
Cycle  Instruction          Action
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 36    MUL x1, x2, x3       MDU done
 37    ADD x4, x1, x5       Forward x1 from MDU (no stall!) ✓
```

**Benefit:** Save 1-2 cycles after each MDU operation

---

## Verification Checklist

### Test Your Stall Logic

**Test 1: Basic MUL/DIV**
```assembly
MUL x1, x2, x3
NOP
NOP
```
- [ ] Verify MDU takes 33 cycles
- [ ] Verify busy signal asserted
- [ ] Verify result correct

**Test 2: Back-to-Back MUL**
```assembly
MUL x1, x2, x3
MUL x4, x5, x6
```
- [ ] Verify both complete
- [ ] Verify no overlap
- [ ] Total cycles = 2 × 33 = 66

**Test 3: Data Hazard**
```assembly
MUL x1, x2, x3
ADD x4, x1, x5    # Uses x1 - must wait!
```
- [ ] Verify ADD waits for MUL
- [ ] Verify ADD uses correct x1 value
- [ ] No data hazard

**Test 4: No Hazard**
```assembly
MUL x1, x2, x3
ADD x4, x5, x6    # Doesn't use x1
```
- [ ] Still stalls (simple implementation)
- [ ] Or doesn't stall (with forwarding)
- [ ] ADD executes correctly

**Test 5: Mixed Code**
```assembly
ADD x1, x2, x3    # 2 cycles
MUL x4, x5, x6    # 33 cycles
SUB x7, x1, x8    # 2 cycles (can execute immediately)
```
- [ ] Verify timing correct
- [ ] Verify SUB can use x1 (no hazard)

---

## Summary

### Key Takeaways

1. **MDU is Multi-Cycle:** 33 cycles for multiply/divide
2. **Stalling is Necessary:** Prevents data hazards
3. **Pipeline Freezes:** PC, fetch, decode all wait
4. **Busy Signal Controls Stall:** busy=1 → stall
5. **Done Signal Releases:** done=1 → continue

### State Transition

```
IDLE ──start──► MDU_WAIT ──done──► WB ──► (next instruction)
                   │
                   └──busy──► (stay, stall pipeline)
```

### Performance Trade-off

| Approach | Cycles/Instruction | Complexity | Accuracy |
|----------|-------------------|------------|----------|
| Software multiply | ~60-120 | Low | Perfect |
| Hardware multiply (your MDU) | ~33 | Medium | Perfect |
| Hardware multiply (pipelined) | ~4-8 | High | Perfect |
| Hardware multiply (combinational) | 1 | Very High | Perfect |
| Zpec MAC | 3 | Medium | Perfect |

Your MDU is a good **balance** between performance and complexity!

### Next Steps

1. **Verify your stall logic** with waveforms
2. **Test data hazard scenarios** thoroughly
3. **Measure actual cycle counts** in simulation
4. **Consider forwarding** if you need better performance
5. **Profile your control code** to see MUL/DIV usage

---

**Document Version:** 1.0
**Last Updated:** 2025-12-08

**Your MDU stalling is working correctly if:**
- ✅ Pipeline freezes during multiply/divide
- ✅ PC doesn't advance until MDU completes
- ✅ Subsequent instructions wait for results
- ✅ No data hazards occur
- ✅ Results are always correct
