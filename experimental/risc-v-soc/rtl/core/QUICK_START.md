# Quick Start: Implement Your RISC-V Core

**Goal:** Get from templates to working CPU in 2-3 weeks
**For:** Homework submission (RTL-to-GDSII flow)

---

## Week 1: Core Modules (7-10 hours)

### Day 1-2: Register File (2-3 hours)

**File:** `regfile.v`

**What to implement:**
```verilog
// 1. WRITE LOGIC (in always block around line 51):
always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        for (i = 1; i < 32; i = i + 1) begin
            registers[i] <= 32'h0;
        end
    end else if (rd_wen && (rd_addr != 5'd0)) begin
        registers[rd_addr] <= rd_data;  // ADD THIS LINE
    end
end

// 2. READ LOGIC (around line 75):
assign rs1_data = (rs1_addr == 5'd0) ? 32'h0 : registers[rs1_addr];  // ADD THIS
assign rs2_data = (rs2_addr == 5'd0) ? 32'h0 : registers[rs2_addr];  // ADD THIS
```

**Test it:**
```bash
cd /home/user/5level-inverter/02-embedded/riscv/verification
iverilog -o test_regfile tb_regfile.v ../rtl/core/regfile.v
vvp test_regfile
# Should see: All tests passed!
```

**Done when:** Can write/read registers, x0 always returns 0

---

### Day 3-4: ALU (3-4 hours)

**File:** `alu.v`

**What to implement:**
```verilog
// Fill in the case statement (around line 50):
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
        `ALU_OP_SLT:  result = ($signed(operand_a) < $signed(operand_b)) ? 32'd1 : 32'd0;
        `ALU_OP_SLTU: result = (operand_a < operand_b) ? 32'd1 : 32'd0;
        default:      result = 32'hXXXXXXXX;
    endcase
end
```

**Test it:**
```bash
iverilog -o test_alu tb_alu.v ../rtl/core/alu.v ../rtl/core/riscv_defines.vh
vvp test_alu
# Verify each operation works
```

**Done when:** All 10 operations produce correct results

---

### Day 5-7: Decoder (4-5 hours)

**File:** `decoder.v`

**What to implement:**

**1. Immediate Decoding (around line 80):**
```verilog
always @(*) begin
    case (opcode)
        `OPCODE_OP_IMM, `OPCODE_LOAD, `OPCODE_JALR: begin
            // I-type: sign-extend bits [31:20]
            immediate = {{20{instruction[31]}}, instruction[31:20]};
        end

        `OPCODE_STORE: begin
            // S-type: sign-extend [31:25] + [11:7]
            immediate = {{20{instruction[31]}}, instruction[31:25], instruction[11:7]};
        end

        `OPCODE_BRANCH: begin
            // B-type: sign-extend, bit 0 always 0
            immediate = {{19{instruction[31]}}, instruction[31], instruction[7],
                         instruction[30:25], instruction[11:8], 1'b0};
        end

        `OPCODE_LUI, `OPCODE_AUIPC: begin
            // U-type: upper 20 bits, lower 12 are 0
            immediate = {instruction[31:12], 12'h0};
        end

        `OPCODE_JAL: begin
            // J-type: sign-extend, bit 0 always 0
            immediate = {{11{instruction[31]}}, instruction[31], instruction[19:12],
                         instruction[20], instruction[30:21], 1'b0};
        end

        default: immediate = 32'h0;
    endcase
end
```

**2. Control Signals (around line 150):**
```verilog
always @(*) begin
    // Defaults
    alu_op = `ALU_OP_ADD;
    alu_src_imm = 1'b0;
    mem_read = 1'b0;
    mem_write = 1'b0;
    reg_write = 1'b0;
    is_branch = 1'b0;
    is_jump = 1'b0;
    is_system = 1'b0;

    case (opcode)
        `OPCODE_OP_IMM: begin
            // ADDI, SLTI, XORI, ORI, ANDI, SLLI, SRLI, SRAI
            alu_src_imm = 1'b1;
            reg_write = 1'b1;
            case (funct3)
                `FUNCT3_ADD_SUB: alu_op = `ALU_OP_ADD;   // ADDI
                `FUNCT3_SLT:     alu_op = `ALU_OP_SLT;   // SLTI
                `FUNCT3_SLTU:    alu_op = `ALU_OP_SLTU;  // SLTIU
                `FUNCT3_XOR:     alu_op = `ALU_OP_XOR;   // XORI
                `FUNCT3_OR:      alu_op = `ALU_OP_OR;    // ORI
                `FUNCT3_AND:     alu_op = `ALU_OP_AND;   // ANDI
                `FUNCT3_SLL:     alu_op = `ALU_OP_SLL;   // SLLI
                `FUNCT3_SRL_SRA: alu_op = instruction[30] ? `ALU_OP_SRA : `ALU_OP_SRL; // SRLI/SRAI
            endcase
        end

        `OPCODE_OP: begin
            // ADD, SUB, SLL, SLT, SLTU, XOR, SRL, SRA, OR, AND
            alu_src_imm = 1'b0;  // Use rs2
            reg_write = 1'b1;
            case (funct3)
                `FUNCT3_ADD_SUB: alu_op = funct7[5] ? `ALU_OP_SUB : `ALU_OP_ADD;  // ADD/SUB
                `FUNCT3_SLL:     alu_op = `ALU_OP_SLL;
                `FUNCT3_SLT:     alu_op = `ALU_OP_SLT;
                `FUNCT3_SLTU:    alu_op = `ALU_OP_SLTU;
                `FUNCT3_XOR:     alu_op = `ALU_OP_XOR;
                `FUNCT3_SRL_SRA: alu_op = funct7[5] ? `ALU_OP_SRA : `ALU_OP_SRL;
                `FUNCT3_OR:      alu_op = `ALU_OP_OR;
                `FUNCT3_AND:     alu_op = `ALU_OP_AND;
            endcase
        end

        `OPCODE_LUI: begin
            // Load Upper Immediate: rd = immediate (already in upper 20 bits)
            alu_op = `ALU_OP_ADD;  // Can use ADD with rs1=0
            alu_src_imm = 1'b1;
            reg_write = 1'b1;
        end

        `OPCODE_AUIPC: begin
            // Add Upper Immediate to PC: rd = PC + immediate
            alu_op = `ALU_OP_ADD;
            alu_src_imm = 1'b1;
            reg_write = 1'b1;
        end

        `OPCODE_BRANCH: begin
            // BEQ, BNE, BLT, BGE, BLTU, BGEU
            alu_op = `ALU_OP_SUB;  // For comparison
            is_branch = 1'b1;
        end

        `OPCODE_JAL: begin
            // Jump and Link: rd = PC + 4, PC = PC + immediate
            alu_op = `ALU_OP_ADD;
            is_jump = 1'b1;
            reg_write = 1'b1;
        end

        `OPCODE_JALR: begin
            // Jump and Link Register: rd = PC + 4, PC = (rs1 + immediate) & ~1
            alu_op = `ALU_OP_ADD;
            alu_src_imm = 1'b1;
            is_jump = 1'b1;
            reg_write = 1'b1;
        end

        `OPCODE_LOAD: begin
            // LW, LH, LB, LHU, LBU
            alu_op = `ALU_OP_ADD;  // Calculate address = rs1 + immediate
            alu_src_imm = 1'b1;
            mem_read = 1'b1;
            reg_write = 1'b1;
        end

        `OPCODE_STORE: begin
            // SW, SH, SB
            alu_op = `ALU_OP_ADD;  // Calculate address = rs1 + immediate
            alu_src_imm = 1'b1;
            mem_write = 1'b1;
        end
    endcase
end
```

**Test it:**
```bash
iverilog -o test_decoder tb_decoder.v ../rtl/core/decoder.v ../rtl/core/riscv_defines.vh
vvp test_decoder
# Verify instruction decoding for each type
```

**Done when:** All instruction formats decode correctly

---

## Week 2: State Machine & Integration (10-15 hours)

### Day 1-3: Basic State Machine (5-7 hours)

**File:** `custom_riscv_core.v`

**What to implement:**

**1. Signals & Instantiations (around line 220):**
```verilog
// Uncomment module instantiations around line 267:

// Register File
regfile regfile_inst (
    .clk(clk),
    .rst_n(rst_n),
    .rs1_addr(rs1_addr),
    .rs2_addr(rs2_addr),
    .rd_addr(rd_addr),
    .rd_data(rd_data),
    .rd_wen(rd_wen),
    .rs1_data(rs1_data),
    .rs2_data(rs2_data)
);

// ALU
alu alu_inst (
    .operand_a(alu_operand_a),
    .operand_b(alu_operand_b),
    .alu_op(alu_op),
    .result(alu_result),
    .zero(alu_zero)
);

// Decoder
decoder decoder_inst (
    .instruction(instruction),
    .opcode(opcode),
    .funct3(funct3),
    .funct7(funct7),
    .rs1_addr(rs1_addr),
    .rs2_addr(rs2_addr),
    .rd_addr(rd_addr),
    .immediate(immediate),
    .alu_op(alu_op),
    .alu_src_imm(alu_src_imm),
    .mem_read(is_load),
    .mem_write(is_store),
    .reg_write(reg_write_internal),
    .is_branch(is_branch),
    .is_jump(is_jump),
    .is_system(is_system)
);
```

**2. State Machine (replace placeholder around line 219):**
```verilog
// Remove placeholder tie-offs and implement:
reg [31:0] alu_result_reg;
reg        reg_write_enable;

// Wishbone control
reg iwb_cyc_reg, iwb_stb_reg;
reg dwb_cyc_reg, dwb_stb_reg;
reg [31:0] dwb_adr_reg, dwb_dat_reg;
reg dwb_we_reg;
reg [3:0] dwb_sel_reg;

assign iwb_cyc_o = iwb_cyc_reg;
assign iwb_stb_o = iwb_stb_reg;
assign iwb_adr_o = pc;

assign dwb_cyc_o = dwb_cyc_reg;
assign dwb_stb_o = dwb_stb_reg;
assign dwb_adr_o = dwb_adr_reg;
assign dwb_dat_o = dwb_dat_reg;
assign dwb_we_o = dwb_we_reg;
assign dwb_sel_o = dwb_sel_reg;

assign alu_operand_a = (opcode == `OPCODE_AUIPC) ? pc : rs1_data;
assign alu_operand_b = alu_src_imm ? immediate : rs2_data;
assign rd_data = is_load ? dwb_dat_i : alu_result_reg;
assign rd_wen = reg_write_enable && (state == STATE_WRITEBACK);

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        pc <= RESET_VECTOR;
        state <= STATE_FETCH;
        iwb_cyc_reg <= 1'b0;
        iwb_stb_reg <= 1'b0;
        dwb_cyc_reg <= 1'b0;
        dwb_stb_reg <= 1'b0;
        reg_write_enable <= 1'b0;
    end else begin
        case (state)
            STATE_FETCH: begin
                // Request instruction from memory
                iwb_cyc_reg <= 1'b1;
                iwb_stb_reg <= 1'b1;

                if (iwb_ack_i) begin
                    instruction <= iwb_dat_i;
                    iwb_cyc_reg <= 1'b0;
                    iwb_stb_reg <= 1'b0;
                    state <= STATE_DECODE;
                end
            end

            STATE_DECODE: begin
                // Decoder runs combinationally
                // Register file reads happen here
                state <= STATE_EXECUTE;
            end

            STATE_EXECUTE: begin
                // ALU operates
                alu_result_reg <= alu_result;

                if (is_load || is_store) begin
                    state <= STATE_MEM;
                end else begin
                    state <= STATE_WRITEBACK;
                end
            end

            STATE_MEM: begin
                if (is_load || is_store) begin
                    dwb_cyc_reg <= 1'b1;
                    dwb_stb_reg <= 1'b1;
                    dwb_adr_reg <= alu_result_reg;  // Address from ALU
                    dwb_we_reg <= is_store;

                    if (is_store) begin
                        dwb_dat_reg <= rs2_data;  // Data to store
                        // Set byte enables based on funct3
                        case (funct3)
                            3'b000: dwb_sel_reg <= 4'b0001 << alu_result_reg[1:0];  // SB
                            3'b001: dwb_sel_reg <= 4'b0011 << {alu_result_reg[1], 1'b0};  // SH
                            3'b010: dwb_sel_reg <= 4'b1111;  // SW
                            default: dwb_sel_reg <= 4'b1111;
                        endcase
                    end else begin
                        dwb_sel_reg <= 4'b1111;  // Full word for loads
                    end

                    if (dwb_ack_i) begin
                        dwb_cyc_reg <= 1'b0;
                        dwb_stb_reg <= 1'b0;
                        state <= STATE_WRITEBACK;
                    end
                end else begin
                    state <= STATE_WRITEBACK;
                end
            end

            STATE_WRITEBACK: begin
                // Write to register file if needed
                reg_write_enable <= reg_write_internal && !is_branch;

                // Update PC
                if (is_jump) begin
                    if (opcode == `OPCODE_JAL) begin
                        pc <= pc + immediate;
                    end else begin  // JALR
                        pc <= (rs1_data + immediate) & ~32'h1;
                    end
                end else if (is_branch) begin
                    // Check branch condition based on funct3
                    case (funct3)
                        `FUNCT3_BEQ:  if (alu_zero) pc <= pc + immediate; else pc <= pc + 4;
                        `FUNCT3_BNE:  if (!alu_zero) pc <= pc + immediate; else pc <= pc + 4;
                        `FUNCT3_BLT:  if (alu_result[31]) pc <= pc + immediate; else pc <= pc + 4;
                        `FUNCT3_BGE:  if (!alu_result[31]) pc <= pc + immediate; else pc <= pc + 4;
                        `FUNCT3_BLTU: if (alu_result[31]) pc <= pc + immediate; else pc <= pc + 4;
                        `FUNCT3_BGEU: if (!alu_result[31]) pc <= pc + immediate; else pc <= pc + 4;
                        default: pc <= pc + 4;
                    endcase
                end else begin
                    pc <= pc + 4;
                end

                state <= STATE_FETCH;
                reg_write_enable <= 1'b0;
            end
        endcase
    end
end
```

**Test it:**
```bash
cd ../sim
# Create simple test program (see below)
iverilog -o test_core tb_core.v ../rtl/core/*.v
vvp test_core
gtkwave core.vcd
```

**Done when:** Can execute simple arithmetic instructions (ADD, ADDI)

---

### Day 4-5: Memory & Branches (3-5 hours)

Already included in state machine above! Test with:

**Test program:**
```assembly
# test.s
.section .text
.global _start

_start:
    addi x1, x0, 10     # x1 = 10
    addi x2, x0, 20     # x2 = 20
    add x3, x1, x2      # x3 = 30
    beq x1, x1, skip    # Should branch
    addi x4, x0, 99     # Should NOT execute
skip:
    addi x5, x0, 42     # Should execute
    sw x3, 0(x0)        # Store 30 to address 0
    lw x6, 0(x0)        # Load back to x6
loop:
    j loop              # Infinite loop
```

**Done when:** Branches, jumps, loads, and stores all work

---

## Week 3: Synthesis & Homework Submission (8-10 hours at school)

### At School - Cadence Session 1 (2-3 hours)

**Synthesis with Genus:**

```bash
cd /home/user/5level-inverter/02-embedded/riscv/synthesis/cadence

# 1. Copy your RTL files
cp ../../rtl/core/{custom_riscv_core.v,regfile.v,alu.v,decoder.v} .

# 2. Run Genus
genus -f synthesis.tcl

# 3. Check reports
less reports/area.rpt
less reports/timing.rpt
less reports/power.rpt

# Expected: ~3000-5000 gates, meets timing @ 100 MHz
```

**If timing doesn't meet:** Reduce clock frequency in constraints

---

### At School - Cadence Session 2 (3-4 hours)

**Place & Route with Innovus:**

```bash
# 1. Run Innovus
innovus -init place_route.tcl

# 2. View layout
innovus
> source load_design.tcl
> gui_show

# 3. Take screenshots for report!

# 4. Check reports
less reports/post_route_timing.rpt
less reports/drc.rpt
less reports/lvs.rpt

# Expected: Clean DRC/LVS, still meets timing
```

---

### At School - Session 3 (2-3 hours)

**Final verification & GDSII:**

```bash
# 1. Generate GDSII
innovus
> write_stream design.gds

# 2. View in Virtuoso/Calibre
# (Ask TA for instructions)

# 3. Extract results for report
# - Area (mm²)
# - Power (mW @ 100 MHz)
# - Max frequency
# - Gate count
# - Layout screenshots
```

---

## Testing Quick Reference

### Unit Tests (Individual Modules)

```bash
cd verification/unit_tests

# Test regfile
iverilog -o test_regfile test_regfile.v ../../rtl/core/regfile.v
vvp test_regfile

# Test ALU
iverilog -o test_alu test_alu.v ../../rtl/core/alu.v ../../rtl/core/riscv_defines.vh
vvp test_alu

# Test decoder
iverilog -o test_decoder test_decoder.v ../../rtl/core/decoder.v ../../rtl/core/riscv_defines.vh
vvp test_decoder
```

### Integration Test (Full Core)

```bash
cd verification/integration

# Simple test
iverilog -o test_simple test_simple.v ../../rtl/core/*.v
vvp test_simple
gtkwave simple.vcd

# Full test
iverilog -o test_full test_full.v ../../rtl/core/*.v
vvp test_full
# Should see: All tests passed!
```

---

## Common Issues & Solutions

### Issue 1: Register x0 not returning 0
**Solution:** Check read logic uses ternary operator:
```verilog
assign rs1_data = (rs1_addr == 5'd0) ? 32'h0 : registers[rs1_addr];
```

### Issue 2: ALU shifts not working
**Solution:** Use only lower 5 bits:
```verilog
result = operand_a << operand_b[4:0];  // NOT operand_b
```

### Issue 3: Branches not working
**Solution:** Check branch condition logic and PC update

### Issue 4: Loads/stores failing
**Solution:**
- Check byte enable generation
- Verify address calculation (ALU result)
- Check sign extension for loads

### Issue 5: Synthesis fails
**Solution:**
- Check for undriven signals
- Check for combinational loops
- Verify all always blocks have reset

### Issue 6: Timing doesn't meet
**Solution:**
- Reduce clock frequency (90 MHz or 80 MHz)
- Check critical path in timing report
- Simplify complex combinational logic

---

## Checklist Before Cadence Session

**Files to bring:**
- [ ] All .v files (custom_riscv_core.v, regfile.v, alu.v, decoder.v)
- [ ] riscv_defines.vh
- [ ] Synthesis script (synthesis.tcl)
- [ ] Place & route script (place_route.tcl)
- [ ] Constraints file (.sdc)
- [ ] Test results (screenshots, logs)
- [ ] USB drive or laptop for file transfer

**Verified at home:**
- [ ] All unit tests pass
- [ ] Integration tests pass
- [ ] Waveforms look correct
- [ ] No syntax errors
- [ ] Yosys synthesis works (optional sanity check)

---

## Report Writing Tips

**Include these figures:**
1. Block diagram (from HOMEWORK_GUIDE.md)
2. State machine diagram
3. Sample waveforms (ADD, branch, load/store)
4. Floorplan screenshot
5. Layout screenshot (zoomed out)
6. Layout screenshot (zoomed in, showing cells)
7. Critical path diagram

**Include these tables:**
1. Instruction set (opcode, format, function)
2. Synthesis results (area, timing, power)
3. Post-route results (area, timing, power)
4. Comparison with requirements

**Include these code snippets:**
1. Register file (key parts)
2. ALU (operations)
3. Decoder (one instruction type)
4. State machine (key states)

---

## Success Criteria

**Minimum (passing grade):**
- [ ] Core executes ~20 basic instructions
- [ ] Synthesis works
- [ ] Place & route completes
- [ ] GDSII generated
- [ ] Report submitted

**Exceeds expectations (high grade):**
- [ ] Full RV32I (40+ instructions)
- [ ] Multi-cycle design
- [ ] Clean timing
- [ ] Good utilization
- [ ] Comprehensive report
- [ ] M extension (extra credit)

---

**You've got this!** Follow this guide step-by-step and you'll have a working CPU in 2-3 weeks. 🚀

**Questions?** Check:
1. This guide
2. HOMEWORK_GUIDE.md (detailed info)
3. IMPLEMENTATION_ROADMAP.md (more examples)
4. Module comments (inline hints)
