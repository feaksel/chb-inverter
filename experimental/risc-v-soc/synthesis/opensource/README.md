# Open-Source Synthesis & Verification Workflow

This directory contains scripts for synthesizing and verifying your RISC-V core using **open-source tools** at home, before using Cadence tools at school.

## Purpose

**Why use open-source tools?**
1. **Verify at home** before Cadence sessions at school
2. **Catch bugs early** in your development cycle
3. **Iterate quickly** without needing school lab access
4. **Learn industry tools** (Yosys, Verilator, Icarus Verilog)

**Workflow:**
```
┌─────────────────────────────────────────────────────────────┐
│                     AT HOME (Daily)                          │
├─────────────────────────────────────────────────────────────┤
│  1. Write RTL code                                          │
│  2. Run unit tests (make test)                              │
│  3. Fix bugs found by testbenches                           │
│  4. Run lint (make lint)                                    │
│  5. Run synthesis (make synth)                              │
│  6. Repeat until clean                                      │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                  AT SCHOOL (Once Ready)                     │
├─────────────────────────────────────────────────────────────┤
│  1. Run Cadence Genus synthesis                             │
│  2. Run Cadence Innovus place & route                       │
│  3. Generate GDSII                                          │
│  4. Export reports for homework                             │
└─────────────────────────────────────────────────────────────┘
```

## Tools Required

### 1. Icarus Verilog (Simulation)

**Purpose:** Run testbenches and verify functionality

**Install:**
```bash
# Ubuntu/Debian
sudo apt-get install iverilog

# macOS
brew install icarus-verilog

# Check installation
iverilog -v
```

### 2. GTKWave (Waveform Viewer)

**Purpose:** View simulation waveforms for debugging

**Install:**
```bash
# Ubuntu/Debian
sudo apt-get install gtkwave

# macOS
brew install gtkwave

# Check installation
gtkwave --version
```

### 3. Yosys (Synthesis)

**Purpose:** Synthesize RTL to gate-level netlist

**Install:**
```bash
# Ubuntu/Debian
sudo apt-get install yosys

# macOS
brew install yosys

# Check installation
yosys -V
```

### 4. Verilator (Lint Checking)

**Purpose:** Catch common Verilog errors before synthesis

**Install:**
```bash
# Ubuntu/Debian
sudo apt-get install verilator

# macOS
brew install verilator

# Check installation
verilator --version
```

## Quick Start

```bash
# Navigate to this directory
cd 02-embedded/riscv/synthesis/opensource

# Run all tests (recommended first step)
make test

# If tests pass, run lint checking
make lint

# If lint passes, run synthesis
make synth

# View waveforms (optional)
make wave-regfile
make wave-alu
make wave-decoder
```

## Available Commands

### Testing Commands

| Command | Description | Output |
|---------|-------------|--------|
| `make test` | Run all unit tests | Terminal output + build/*.vcd |
| `make sim-regfile` | Test register file only | build/sim_regfile |
| `make sim-alu` | Test ALU only | build/sim_alu |
| `make sim-decoder` | Test decoder only | build/sim_decoder |
| `make sim-core` | Test full core (after implementation) | build/sim_core |

### Waveform Viewing

| Command | Description |
|---------|-------------|
| `make wave-regfile` | View register file waveforms |
| `make wave-alu` | View ALU waveforms |
| `make wave-decoder` | View decoder waveforms |
| `make wave-core` | View full core waveforms |

### Synthesis Commands

| Command | Description | Output |
|---------|-------------|--------|
| `make synth` | Synthesize with Yosys | build/netlist_yosys.v |
| `make lint` | Run Verilator lint | Terminal warnings/errors |

### Utility Commands

| Command | Description |
|---------|-------------|
| `make clean` | Remove all build files |
| `make help` | Show all available commands |

## Detailed Workflow

### Step 1: Run Tests

**Before writing any code:**
```bash
make test
```

**Expected output (before implementation):**
```
=========================================
Running Register File Testbench
=========================================

Test 1: Write and read x5
  FAIL: Expected 0xDEADBEEF, got 0x00000000

*** 14 TESTS FAILED ***
```

This is normal! The templates have TODO markers. Now implement the code.

### Step 2: Implement Module

Edit `../../rtl/core/regfile.v` and add the implementation:

```verilog
// Write logic
always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        for (i = 1; i < 32; i = i + 1) begin
            registers[i] <= 32'h0;
        end
    end else if (rd_wen && (rd_addr != 5'd0)) begin
        registers[rd_addr] <= rd_data;  // ← ADD THIS
    end
end

// Read logic
assign rs1_data = (rs1_addr == 5'd0) ? 32'h0 : registers[rs1_addr];  // ← ADD THIS
assign rs2_data = (rs2_addr == 5'd0) ? 32'h0 : registers[rs2_addr];  // ← ADD THIS
```

### Step 3: Re-run Tests

```bash
make sim-regfile
```

**Expected output (after correct implementation):**
```
*** ALL TESTS PASSED! ***

Register file is working correctly!
You can now proceed to implement the ALU.
```

### Step 4: Lint Checking

After all unit tests pass:

```bash
make lint
```

**Clean output (no errors):**
```
=========================================
Running Verilator Lint
=========================================

Lint complete!
```

**If errors:**
```
%Warning-UNUSED: regfile.v:55: Signal is not used: 'unused_signal'
```

Fix all warnings before proceeding.

### Step 5: Synthesis

```bash
make synth
```

**Expected output:**
```
=========================================
Synthesizing with Yosys
=========================================

[... synthesis messages ...]

Number of cells:                   1234
  $_AND_          123
  $_OR_           456
  $_XOR_          78
  $_DFF_P_        32
  ...

=========================================
Synthesis Complete!
=========================================

Output files:
  build/netlist_yosys.v  - Gate-level netlist
  build/design.json      - Design JSON
  reports/synthesis.txt  - Statistics

To view netlist: less build/netlist_yosys.v
=========================================
```

**Check reports/synthesis.txt** for gate count and other statistics.

### Step 6: Review Synthesis Output

```bash
less reports/synthesis.txt
```

**Look for:**
- **Gate count:** How many gates were used?
- **Register count:** Should match your design (32 registers + state registers)
- **Warnings:** Any optimization warnings?

**Compare with Cadence:** When you run Cadence Genus at school, gate counts should be similar.

## Output Files

After running commands, you'll have:

```
build/
├── sim_regfile              # Regfile simulation executable
├── sim_alu                  # ALU simulation executable
├── sim_decoder              # Decoder simulation executable
├── regfile.vcd              # Regfile waveform
├── alu.vcd                  # ALU waveform
├── decoder.vcd              # Decoder waveform
├── netlist_yosys.v          # Yosys synthesized netlist
└── design.json              # Design JSON

reports/
└── synthesis.txt            # Synthesis statistics
```

## Interpreting Results

### Test Results

**All tests passed:**
✅ Module is functionally correct
→ Proceed to next module or synthesis

**Some tests failed:**
❌ Debug using waveforms and print statements
→ Fix issues and re-run

### Lint Results

**No warnings:**
✅ Code is clean
→ Ready for synthesis

**Warnings present:**
⚠️ Review each warning
→ Fix critical warnings before synthesis

### Synthesis Results

**Synthesis successful:**
✅ Design can be synthesized
→ Ready for Cadence at school

**Synthesis errors:**
❌ Fix RTL issues
→ Re-run tests and synthesis

## Common Issues

### Issue 1: Tests Hang

**Symptom:** Test runs forever without output

**Cause:** Combinational loop or missing clock

**Fix:**
- Check for combinational loops in always @(*) blocks
- Ensure testbench generates clock
- Check for infinite loops in testbench

**Kill hung test:** Press Ctrl+C

### Issue 2: Synthesis Errors

**Symptom:**
```
ERROR: Cannot find module 'regfile'
```

**Cause:** File path incorrect or module name mismatch

**Fix:**
- Check file exists: `ls ../../rtl/core/regfile.v`
- Check module name matches filename
- Check synth.ys has correct paths

### Issue 3: Verilator Warnings

**Symptom:**
```
%Warning-UNUSED: Signal is not used
```

**Cause:** Declared signals not connected

**Fix:**
- Remove unused signals
- Or connect them if they should be used
- Use `/* verilator lint_off UNUSED */` if intentional

### Issue 4: Waveform Won't Open

**Symptom:** GTKWave says "cannot open file"

**Cause:** Simulation didn't run or VCD not generated

**Fix:**
- Run simulation first: `make sim-regfile`
- Check build/ directory for .vcd files
- Ensure $dumpfile() in testbench

## Tips for Success

1. **Test incrementally**
   - Don't implement everything at once
   - Test each module as you complete it
   - Fix bugs immediately when found

2. **Use waveforms**
   - Waveforms show exactly what happened
   - Much faster than adding print statements
   - Learn to read timing diagrams

3. **Read error messages**
   - Error messages tell you exactly what's wrong
   - Don't skip over them
   - Google error messages if unclear

4. **Compare with reference**
   - Check RISC-V ISA manual
   - Compare with implementation hints
   - Ask for help if stuck

5. **Keep code clean**
   - Fix lint warnings
   - Add comments for complex logic
   - Use consistent formatting

## Comparison: Open-Source vs Cadence

| Feature | Open-Source | Cadence |
|---------|-------------|---------|
| **Cost** | Free | School license |
| **Availability** | Use anywhere | School only |
| **Synthesis** | Technology-independent | Technology-specific |
| **Speed** | Fast | Slower (more optimization) |
| **Quality** | Good for verification | Production quality |
| **Reports** | Basic | Comprehensive |
| **Use case** | Development & debug | Final submission |

**Strategy:**
- Use **open-source** for daily development and debugging
- Use **Cadence** for final synthesis and GDSII generation

## Checklist Before School

Before going to school for Cadence session:

- [ ] All unit tests pass (`make test`)
- [ ] Lint checking clean (`make lint`)
- [ ] Yosys synthesis successful (`make synth`)
- [ ] Reviewed synthesis report (reports/synthesis.txt)
- [ ] Code is committed to git
- [ ] Bring synthesis/cadence/*.tcl scripts
- [ ] Know what to expect (gate count, timing)

If all checked, you're ready for Cadence! 🎉

## Next Steps

1. **Complete all modules:** regfile → alu → decoder → core
2. **All tests pass:** No failures
3. **Synthesis clean:** No errors
4. **Ready for school:** Checklist complete

Then proceed to Cadence flow at school:
```bash
cd ../cadence
# Follow HOMEWORK_GUIDE.md for Cadence workflow
```

## Support

**Documentation:**
- See `../../docs/HOMEWORK_GUIDE.md` for complete workflow
- See `../../rtl/core/QUICK_START.md` for implementation steps
- See `../../sim/README.md` for detailed test information

**Tool Documentation:**
- Icarus Verilog: http://iverilog.icarus.com/
- Yosys: http://www.clifford.at/yosys/
- Verilator: https://www.veripool.org/verilator/

**RISC-V Resources:**
- RISC-V ISA Manual: https://riscv.org/technical/specifications/
- RISC-V Assembly Programmer's Manual: https://github.com/riscv/riscv-asm-manual

---

**Good luck with your implementation!** 🚀

Remember: Open-source tools are your friends for daily development. Use them often!
