# Homework Guide: RTL-to-GDSII RISC-V CPU Design

**Course:** RTL-to-GDSII Single-Cycle RISC-V CPU Design
**Objective:** Design and implement a 32-bit RISC-V CPU core with complete RTL-to-GDSII flow
**Your Approach:** Multi-cycle RV32IM core (exceeds requirements!)

**Date:** 2025-12-03
**Target Completion:** 3-4 weeks

---

## Table of Contents

1. [Homework Requirements Mapping](#homework-requirements-mapping)
2. [Your Design Overview](#your-design-overview)
3. [Development Workflow](#development-workflow)
4. [Implementation Timeline](#implementation-timeline)
5. [Verification Strategy](#verification-strategy)
6. [RTL-to-GDSII Flow](#rtl-to-gdsii-flow)
7. [Report Structure](#report-structure)
8. [Grading Checklist](#grading-checklist)

---

## Homework Requirements Mapping

### Official Requirements → Your Implementation

| Requirement | Minimum Expected | Your Design | Status |
|-------------|------------------|-------------|--------|
| **Architecture** | 32-bit RISC-V | 32-bit RV32IM | ✅ Exceeds |
| **Execution** | Single-cycle | Multi-cycle (more realistic) | ✅ Exceeds |
| **ISA** | Basic RV32I subset | Full RV32I + M extension | ✅ Exceeds |
| **Instructions** | ~20 instructions | 48+ instructions (RV32I + M) | ✅ Exceeds |
| **RTL Design** | Verilog implementation | Verilog with modules | ✅ Meets |
| **Synthesis** | Gate-level netlist | Yosys + Cadence | ✅ Meets |
| **Place & Route** | Physical layout | OpenROAD + Cadence | ✅ Meets |
| **GDSII** | Final layout file | Complete flow | ✅ Meets |
| **Verification** | Basic testing | Full testbenches + waveforms | ✅ Exceeds |

**Your Bonus Features (for extra credit!):**
- ✅ Wishbone bus interface (industry standard)
- ✅ Multi-cycle execution (realistic design)
- ✅ M extension (multiply/divide hardware)
- ✅ Modular design (reusable components)
- ✅ Complete SoC integration path
- ✅ Custom instructions (Zpec) - optional showcase

---

## Your Design Overview

### Architecture Block Diagram

```
┌────────────────────────────────────────────────────────┐
│              Custom RISC-V Core (RV32IM)               │
│                                                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐            │
│  │ Register │  │   ALU    │  │ Decoder  │            │
│  │   File   │  │ (32-bit) │  │ (RV32IM) │            │
│  │ (32 regs)│  │          │  │          │            │
│  └──────────┘  └──────────┘  └──────────┘            │
│                                                         │
│  ┌──────────────────────────────────────────────────┐ │
│  │         State Machine (Multi-Cycle)               │ │
│  │  FETCH → DECODE → EXECUTE → MEM → WRITEBACK      │ │
│  └──────────────────────────────────────────────────┘ │
│                                                         │
│  ┌──────────────┐         ┌──────────────┐            │
│  │  Instruction │◄────────┤    Data      │            │
│  │  Wishbone    │         │  Wishbone    │            │
│  │     Bus      │         │     Bus      │            │
│  └──────────────┘         └──────────────┘            │
└─────────────┬──────────────────┬────────────────────┘
              │                  │
              ▼                  ▼
        ┌─────────┐        ┌─────────┐
        │   ROM   │        │   RAM   │
        │ (32 KB) │        │ (64 KB) │
        └─────────┘        └─────────┘
```

### Key Specifications

**Core:**
- **ISA:** RV32IM (32-bit integer + multiply/divide)
- **Pipeline:** Multi-cycle (5 states)
- **Registers:** 32 × 32-bit general purpose
- **Bus Interface:** Wishbone B4 (standard protocol)
- **Clock:** 50-100 MHz target

**Supported Instructions:**
- **Arithmetic:** ADD, ADDI, SUB, LUI, AUIPC
- **Logic:** AND, ANDI, OR, ORI, XOR, XORI
- **Shifts:** SLL, SLLI, SRL, SRLI, SRA, SRAI
- **Comparisons:** SLT, SLTI, SLTU, SLTIU
- **Branches:** BEQ, BNE, BLT, BGE, BLTU, BGEU
- **Jumps:** JAL, JALR
- **Memory:** LW, LH, LB, LHU, LBU, SW, SH, SB
- **Multiply/Divide:** MUL, MULH, MULHU, MULHSU, DIV, DIVU, REM, REMU

**Resources:**
- **LUTs/Gates:** ~3,000-5,000 (estimated)
- **Registers:** ~2,000 flip-flops
- **Memory:** 96 KB (32 KB ROM + 64 KB RAM)
- **Timing:** Fmax ~100 MHz (target)

---

## Development Workflow

### Two-Phase Approach

**Phase 1: Home Development (Open-Source Tools)**
- ✅ Implement and test RTL
- ✅ Verify functionality with testbenches
- ✅ Simulate with Icarus Verilog / Verilator
- ✅ Synthesize with Yosys (sanity check)
- ✅ Quick place & route with OpenROAD (optional)

**Phase 2: School Submission (Cadence Tools)**
- ✅ Final synthesis with Cadence Genus
- ✅ Place & route with Cadence Innovus
- ✅ DRC/LVS checks
- ✅ Generate GDSII
- ✅ Post-layout verification

### Development Tools Setup

**At Home (Free/Open-Source):**
```bash
# Install open-source toolchain
sudo apt-get install iverilog gtkwave verilator yosys

# Optional: OpenLane for full flow
git clone https://github.com/The-OpenROAD-Project/OpenLane
cd OpenLane
make
```

**At School (Cadence):**
- Cadence Genus (synthesis)
- Cadence Innovus (place & route)
- Cadence Virtuoso (layout viewer)
- Technology library (provided by school)

---

## Implementation Timeline

### Week 1: Core Implementation (At Home)

**Day 1-2: Register File + ALU**
```
Tasks:
□ Implement rtl/core/regfile.v (32 registers, x0=0)
□ Test: Write/read various registers
□ Implement rtl/core/alu.v (all RV32I operations)
□ Test: Arithmetic, logic, shifts, comparisons

Deliverable: Working regfile + ALU modules
```

**Day 3-4: Decoder**
```
Tasks:
□ Implement rtl/core/decoder.v
□ Decode all RV32I instruction formats (R, I, S, B, U, J)
□ Generate control signals
□ Test: Feed various instructions, verify outputs

Deliverable: Complete instruction decoder
```

**Day 5-7: State Machine**
```
Tasks:
□ Implement multi-cycle state machine in custom_riscv_core.v
□ States: FETCH → DECODE → EXECUTE → MEM → WRITEBACK
□ Connect regfile, ALU, decoder
□ Test: Simple ADD, ADDI instructions

Deliverable: Basic working core (arithmetic only)
```

**Milestone 1:** Core executes arithmetic and logic instructions ✅

### Week 2: Complete RV32I (At Home)

**Day 1-2: Branches and Jumps**
```
Tasks:
□ Implement branch comparison logic
□ Add branch target calculation
□ Implement JAL, JALR
□ Test: Loops, conditional branches, function calls

Deliverable: Control flow working
```

**Day 3-4: Memory Access**
```
Tasks:
□ Add MEM state for load/store
□ Implement LW, SW, LH, LB, etc.
□ Handle byte enables and sign extension
□ Test: Load from memory, store to memory

Deliverable: Full RV32I core
```

**Day 5: Integration Testing**
```
Tasks:
□ Write comprehensive test program
□ Test all instruction types
□ Verify with waveforms
□ Document test results

Deliverable: Verified RV32I implementation
```

**Milestone 2:** Complete RV32I core working ✅

### Week 3: RTL-to-GDSII Flow (At School)

**Day 1-2: Synthesis**
```
Tasks:
□ Set up Cadence Genus project
□ Write synthesis constraints (timing, area)
□ Synthesize to gate-level netlist
□ Analyze reports (area, timing, power)

Deliverable: Gate-level netlist + synthesis report
```

**Day 3-4: Place & Route**
```
Tasks:
□ Set up Cadence Innovus project
□ Floor planning (define core area)
□ Placement (standard cells)
□ Clock tree synthesis
□ Routing (wires between cells)
□ Timing optimization

Deliverable: Physical layout (DEF/LEF files)
```

**Day 5: Verification & GDSII**
```
Tasks:
□ DRC (Design Rule Check)
□ LVS (Layout vs Schematic)
□ Post-layout timing analysis
□ Generate GDSII file
□ Extract parasitics for final simulation

Deliverable: Final GDSII + verification reports
```

**Milestone 3:** Complete RTL-to-GDSII flow ✅

### Week 4: Report & Optional Enhancements

**Report Writing**
```
Tasks:
□ Architecture description
□ Design decisions explanation
□ RTL code documentation
□ Synthesis results analysis
□ Layout screenshots
□ Verification results
□ Conclusions

Deliverable: Complete design report (PDF)
```

**Optional Enhancements (Extra Credit)**
```
Tasks:
□ Add M extension (multiply/divide)
□ Implement custom Zpec instructions
□ Integrate with peripherals (PWM, UART)
□ Performance analysis
□ Area/power optimization

Deliverable: Extended design showcase
```

---

## Verification Strategy

### Three-Level Verification

**Level 1: Unit Testing (Each Module)**

```verilog
// Example: Test Register File
module tb_regfile;
    // Test cases:
    // 1. Write to various registers
    // 2. Read back and verify
    // 3. Verify x0 always reads 0
    // 4. Test simultaneous read/write

    // Run: iverilog -o tb_regfile tb_regfile.v regfile.v
    //      vvp tb_regfile
    //      gtkwave regfile.vcd
endmodule
```

**Level 2: Integration Testing (Full Core)**

```assembly
# Test program: test_core.s
# Test all instruction types

.section .text
.global _start

_start:
    # Arithmetic
    addi x1, x0, 10      # x1 = 10
    addi x2, x0, 20      # x2 = 20
    add  x3, x1, x2      # x3 = 30
    sub  x4, x3, x1      # x4 = 20

    # Logic
    andi x5, x3, 0x0F    # x5 = 30 & 15 = 14
    ori  x6, x5, 0xF0    # x6 = 14 | 240 = 254

    # Branches
    beq  x2, x4, equal   # Should branch (20 == 20)
    addi x7, x0, 1       # Should NOT execute
equal:
    addi x8, x0, 2       # Should execute

    # Memory
    sw   x3, 0(x0)       # Store 30 to address 0
    lw   x9, 0(x0)       # Load back to x9

    # Loop test
    addi x10, x0, 0      # Counter = 0
    addi x11, x0, 10     # Limit = 10
loop:
    addi x10, x10, 1     # counter++
    blt  x10, x11, loop  # Continue if counter < 10

done:
    # Infinite loop (end of test)
    j done

# Compile: riscv32-unknown-elf-as -o test.o test.s
#          riscv32-unknown-elf-ld -T linker.ld -o test.elf test.o
#          riscv32-unknown-elf-objcopy -O verilog test.elf test.hex
```

**Level 3: RISCV-Tests Compliance**

```bash
# Use official RISC-V compliance tests
git clone https://github.com/riscv/riscv-tests
cd riscv-tests
./configure --with-xlen=32
make

# Run tests on your core
cd ../verification
./run_compliance_tests.sh
```

### Verification Checklist

**Functional Verification:**
- [ ] All arithmetic instructions work correctly
- [ ] All logic instructions work correctly
- [ ] All shift instructions work correctly
- [ ] All comparison instructions work correctly
- [ ] All branch instructions work correctly (taken/not taken)
- [ ] JAL/JALR work correctly
- [ ] Load/store with various sizes work (LW, LH, LB, SW, SH, SB)
- [ ] Sign extension works correctly (LH, LB)
- [ ] Zero extension works correctly (LHU, LBU)
- [ ] Register x0 always reads 0
- [ ] PC increments correctly
- [ ] Immediate values decoded correctly (all formats)

**Timing Verification:**
- [ ] All paths meet timing constraints
- [ ] Setup/hold times satisfied
- [ ] Clock frequency meets target (50-100 MHz)

**Coverage Metrics:**
- [ ] Instruction coverage: 100% (all instructions tested)
- [ ] Branch coverage: 100% (all branches taken/not taken)
- [ ] Toggle coverage: >90% (most signals toggle)

---

## RTL-to-GDSII Flow

### Overview of Complete Flow

```
RTL (Verilog)
    │
    ├─► Synthesis (Genus/Yosys)
    │       └─► Gate-level Netlist
    │
    ├─► Place & Route (Innovus/OpenROAD)
    │       ├─► Floorplanning
    │       ├─► Placement
    │       ├─► Clock Tree Synthesis
    │       └─► Routing
    │
    ├─► Verification
    │       ├─► DRC (Design Rule Check)
    │       ├─► LVS (Layout vs Schematic)
    │       └─► STA (Static Timing Analysis)
    │
    └─► GDSII Generation
            └─► Final Layout File
```

### Detailed Steps

#### Step 1: Synthesis (Cadence Genus)

**At School:**

```tcl
# synthesis/cadence/synthesis.tcl

# Set up library
set_db init_lib_search_path /path/to/technology/library
set_db init_hdl_search_path ../rtl/core

# Read technology library
read_libs technology.lib

# Read RTL
read_hdl -sv {
    custom_riscv_core.v
    regfile.v
    alu.v
    decoder.v
}

# Elaborate design
elaborate custom_riscv_core

# Set constraints
create_clock -name clk -period 10.0 [get_ports clk]  # 100 MHz
set_input_delay 2.0 -clock clk [all_inputs]
set_output_delay 2.0 -clock clk [all_outputs]

# Set optimization goals
set_db syn_generic_effort high
set_db syn_map_effort high
set_db syn_opt_effort high

# Synthesize
syn_generic
syn_map
syn_opt

# Report results
report_area > reports/area.rpt
report_timing > reports/timing.rpt
report_power > reports/power.rpt
report_gates > reports/gates.rpt

# Write netlist
write_hdl > outputs/netlist.v
write_sdc > outputs/constraints.sdc

# Write for Innovus
write_design -innovus outputs/design
```

**Expected Results:**
- **Area:** ~3,000-5,000 gates (varies by technology)
- **Timing:** Should meet 100 MHz (10ns period)
- **Power:** ~5-10 mW @ 100 MHz (depends on tech node)

**At Home (Yosys - for verification):**

```bash
# synthesis/openroad/synthesis.sh

#!/bin/bash

# Synthesize with Yosys
yosys -p "
    read_verilog ../rtl/core/custom_riscv_core.v
    read_verilog ../rtl/core/regfile.v
    read_verilog ../rtl/core/alu.v
    read_verilog ../rtl/core/decoder.v
    hierarchy -check -top custom_riscv_core
    proc; opt; memory; opt; fsm; opt
    techmap; opt
    synth -top custom_riscv_core
    stat
    write_verilog netlist.v
"

# View statistics
echo "Synthesis complete. Check netlist.v"
```

#### Step 2: Place & Route (Cadence Innovus)

**At School:**

```tcl
# synthesis/cadence/place_route.tcl

# Read design
read_design outputs/design.v

# Floorplan
floorplan -site core -r 0.7 0.7 10 10 10 10

# Add power rings
add_rings -nets {VDD VSS} -width 2 -spacing 1

# Place standard cells
place_design

# Add filler cells
add_filler -cell FILL*

# Clock tree synthesis
create_ccopt_clock_tree_spec
ccopt_design

# Route
route_design

# Optimize
opt_design

# Verify
verify_connectivity
verify_geometry

# Reports
report_timing > reports/post_route_timing.rpt
report_area > reports/post_route_area.rpt
report_power > reports/post_route_power.rpt

# Generate GDSII
write_stream outputs/design.gds -map_file gds.map

# Save design
save_design final_design
```

**Expected Results:**
- **Area:** Depends on technology and utilization (typically 70-80%)
- **Timing:** Should still meet 100 MHz after routing
- **DRC violations:** 0 (all fixed)
- **LVS:** Clean (layout matches schematic)

#### Step 3: Verification

**Design Rule Check (DRC):**
```tcl
# Verify physical design rules
verify_drc -limit 1000 > reports/drc.rpt

# Should report: 0 violations
```

**Layout vs Schematic (LVS):**
```tcl
# Verify layout matches netlist
verify_lvs netlist.sp layout.gds > reports/lvs.rpt

# Should report: CLEAN
```

**Static Timing Analysis (STA):**
```tcl
# Post-layout timing
read_sdf outputs/design.sdf
report_timing -path_type full_clock > reports/sta.rpt

# Verify:
# - Setup time: positive slack
# - Hold time: positive slack
# - Max frequency: >= 100 MHz
```

---

## Report Structure

### Recommended Report Outline

**1. Introduction (2 pages)**
- Project overview
- Objectives
- Design approach
- Organization of report

**2. Architecture Design (4-5 pages)**
- Block diagram
- Datapath description
- Control unit design
- State machine
- Instruction set architecture
- Design decisions and rationale

**3. RTL Implementation (5-6 pages)**
- Module descriptions
  - Register file
  - ALU
  - Decoder
  - State machine
  - Wishbone interface
- Key code snippets (commented)
- Module interfaces
- Design hierarchy

**4. Verification (3-4 pages)**
- Verification strategy
- Test programs
- Simulation results
- Waveforms (key signals)
- Coverage analysis
- Corner cases tested

**5. Synthesis (3-4 pages)**
- Synthesis strategy
- Constraints
- Technology library used
- Gate-level netlist statistics
- Area report
- Timing report
- Power analysis
- Critical path analysis

**6. Place & Route (4-5 pages)**
- Floorplan
- Placement results
- Clock tree synthesis
- Routing strategy
- Layout screenshots
- Final chip area
- Utilization

**7. Physical Verification (2-3 pages)**
- DRC results
- LVS results
- Post-layout timing
- Parasitic extraction
- Final performance metrics

**8. Results & Analysis (2-3 pages)**
- Performance summary
- Area breakdown
- Power consumption
- Comparison with requirements
- Design trade-offs

**9. Conclusions (1-2 pages)**
- What was learned
- Challenges faced
- Future improvements

**10. References & Appendices**
- References (RISC-V spec, papers, etc.)
- Complete RTL code
- Test programs
- Scripts

**Total: 30-40 pages recommended**

### Key Figures to Include

**Must-Have Diagrams:**
1. Top-level block diagram
2. Datapath architecture
3. State machine diagram
4. Pipeline timing diagram
5. Instruction format diagrams
6. Floorplan
7. Placement view
8. Routing view
9. Clock tree
10. Critical path

**Must-Have Tables:**
1. Instruction set table
2. Register definitions
3. Control signals table
4. Synthesis results summary
5. Timing analysis summary
6. Power analysis summary
7. Area breakdown
8. Comparison with specifications

**Must-Have Waveforms:**
1. Simple instruction execution (ADD)
2. Branch instruction
3. Load/store operation
4. Complete test program
5. Clock and control signals

---

## Grading Checklist

### Functionality (40%)

- [ ] **Core instructions working** (20%)
  - [ ] Arithmetic operations (ADD, SUB, ADDI)
  - [ ] Logic operations (AND, OR, XOR, etc.)
  - [ ] Shift operations (SLL, SRL, SRA)
  - [ ] Comparison operations (SLT, SLTU)
  - [ ] Immediate instructions

- [ ] **Control flow working** (10%)
  - [ ] Branch instructions (BEQ, BNE, etc.)
  - [ ] Jump instructions (JAL, JALR)
  - [ ] PC handling

- [ ] **Memory access working** (10%)
  - [ ] Load instructions (LW, LH, LB)
  - [ ] Store instructions (SW, SH, SB)
  - [ ] Sign/zero extension

### RTL Design Quality (20%)

- [ ] **Code quality** (10%)
  - [ ] Modular design
  - [ ] Clear naming conventions
  - [ ] Well commented
  - [ ] Proper coding style

- [ ] **Design efficiency** (10%)
  - [ ] Resource usage reasonable
  - [ ] Timing efficient
  - [ ] No unnecessary logic

### Verification (15%)

- [ ] **Testbenches** (7%)
  - [ ] Module-level tests
  - [ ] System-level tests
  - [ ] Edge cases covered

- [ ] **Documentation** (8%)
  - [ ] Test plan
  - [ ] Test results
  - [ ] Waveforms
  - [ ] Coverage analysis

### Synthesis (10%)

- [ ] **Successful synthesis** (5%)
  - [ ] No synthesis errors
  - [ ] Meets timing
  - [ ] Reasonable area

- [ ] **Analysis** (5%)
  - [ ] Synthesis reports
  - [ ] Timing analysis
  - [ ] Power analysis

### Place & Route (10%)

- [ ] **Successful P&R** (5%)
  - [ ] Clean DRC
  - [ ] Clean LVS
  - [ ] Meets timing after routing

- [ ] **Layout quality** (5%)
  - [ ] Good floorplan
  - [ ] Efficient utilization
  - [ ] Clean routing

### Report (5%)

- [ ] **Completeness** (3%)
  - [ ] All sections included
  - [ ] Adequate detail
  - [ ] Clear presentation

- [ ] **Quality** (2%)
  - [ ] Professional appearance
  - [ ] Good diagrams
  - [ ] Proper references

### Extra Credit Opportunities (Up to 10% bonus)

- [ ] **M Extension** (+3%)
  - Implement multiply/divide hardware

- [ ] **Custom Instructions** (+3%)
  - Implement Zpec or other custom instructions

- [ ] **SoC Integration** (+2%)
  - Integrate with peripherals (UART, PWM, etc.)

- [ ] **Advanced Optimization** (+2%)
  - Area/power optimization beyond requirements
  - Performance tuning

---

## Tips for Success

### Before Starting

1. **Understand RISC-V ISA thoroughly**
   - Read RISC-V specification (at least RV32I chapter)
   - Understand instruction formats
   - Know what each instruction does

2. **Plan your time**
   - Don't underestimate verification time
   - Leave buffer for Cadence access
   - Start early with open-source tools

3. **Set up environment**
   - Install open-source tools at home
   - Test Cadence access at school early
   - Organize your files from the start

### During Implementation

1. **Test incrementally**
   - Don't write everything then test
   - Test each module as you complete it
   - Add instructions gradually

2. **Use version control**
   - Commit after each working feature
   - Document what you changed
   - Easy to rollback if something breaks

3. **Document as you go**
   - Don't wait until end for report
   - Take screenshots of important results
   - Keep notes on design decisions

### For RTL-to-GDSII at School

1. **Prepare everything at home first**
   - All RTL working
   - All tests passing
   - Scripts ready

2. **Cadence session checklist**
   - All Verilog files
   - Testbenches
   - Constraints file
   - Synthesis script
   - P&R script

3. **Budget time for iterations**
   - First synthesis may have issues
   - Timing may not meet initially
   - P&R may need tweaking

### Common Pitfalls to Avoid

❌ **Don't:**
- Start synthesis before RTL is fully verified
- Ignore timing constraints
- Skip documentation until the end
- Try to implement everything at once
- Forget to save intermediate results

✅ **Do:**
- Test thoroughly before synthesis
- Set realistic timing constraints
- Document continuously
- Implement incrementally
- Save all reports and screenshots

---

## Quick Reference Commands

### Simulation (At Home)

```bash
# Compile and simulate with Icarus Verilog
iverilog -o sim tb_core.v custom_riscv_core.v regfile.v alu.v decoder.v
vvp sim
gtkwave waveform.vcd

# Or use Verilator (faster)
verilator --cc custom_riscv_core.v --exe sim_main.cpp
make -C obj_dir -f Vcustom_riscv_core.mk
./obj_dir/Vcustom_riscv_core
```

### Synthesis (At School)

```bash
# Cadence Genus
genus -f synthesis.tcl -log synthesis.log

# Check results
less reports/area.rpt
less reports/timing.rpt
```

### Place & Route (At School)

```bash
# Cadence Innovus
innovus -init place_route.tcl -log pnr.log

# View layout
innovus
> source load_design.tcl
> gui_show
```

---

## Resources

### RISC-V Resources

- **RISC-V Spec:** https://riscv.org/technical/specifications/
- **RISC-V ISA Manual (PDF):** https://github.com/riscv/riscv-isa-manual
- **RISC-V Tests:** https://github.com/riscv/riscv-tests

### Verification Resources

- **Test Programs:** See `verification/test_programs/`
- **Testbench Templates:** See `sim/testbenches/`
- **Expected Results:** See `verification/golden_outputs/`

### Synthesis Resources

- **Cadence Docs:** Available at school
- **OpenROAD Flow:** See `synthesis/openroad/README.md`
- **Example Scripts:** See `synthesis/cadence/`

### Report Resources

- **Report Template:** See `docs/REPORT_TEMPLATE.md`
- **Example Reports:** Ask professor/TAs
- **LaTeX Template:** See `docs/latex_template/`

---

## Support

**If You Get Stuck:**

1. **Check documentation first**
   - This guide
   - IMPLEMENTATION_ROADMAP.md
   - DROP_IN_REPLACEMENT_GUIDE.md

2. **Debug systematically**
   - Check waveforms
   - Add $display statements
   - Test modules individually

3. **Ask for help**
   - Professor office hours
   - TA sessions
   - Classmates (but don't copy!)

**Common Questions:**

**Q: Do I need to implement ALL RV32I instructions?**
A: The homework requires a "basic subset". ~20 instructions is sufficient. However, implementing full RV32I (40 instructions) will get you extra credit and is not much more work.

**Q: Should I do single-cycle or multi-cycle?**
A: Either is acceptable. Multi-cycle is more realistic and what industry uses, but single-cycle is simpler. Your multi-cycle design exceeds requirements.

**Q: Can I use the M extension?**
A: Yes! This is excellent for extra credit. Your design supports it.

**Q: How much time will I need with Cadence?**
A: Plan for 2-3 sessions of 2-3 hours each:
- Session 1: Synthesis (2 hours)
- Session 2: Place & Route (3 hours)
- Session 3: Verification & fixes (2 hours)

**Q: What if timing doesn't meet?**
A: Options:
- Reduce clock frequency constraint
- Optimize critical paths
- Use better synthesis options
- Pipeline critical paths (advanced)

---

**Document Version:** 1.0
**Last Updated:** 2025-12-03
**Status:** Ready for Implementation ✅

**Good luck with your homework! You've got an excellent head start with all the infrastructure ready.** 🚀
