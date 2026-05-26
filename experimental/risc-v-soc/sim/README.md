# Simulation and Verification

This directory contains testbenches and simulation scripts for verifying the custom RISC-V core implementation.

## Directory Structure

```
sim/
├── testbench/           # Unit testbenches
│   ├── tb_regfile.v     # Register file tests
│   ├── tb_alu.v         # ALU tests
│   ├── tb_decoder.v     # Decoder tests
│   └── tb_core.v        # Full core tests (create after implementing state machine)
└── README.md            # This file
```

## Quick Start

### Prerequisites

**Required tools:**
- **Icarus Verilog** (iverilog) - For simulation
- **GTKWave** (optional) - For viewing waveforms

**Install on Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install iverilog gtkwave
```

**Install on macOS:**
```bash
brew install icarus-verilog gtkwave
```

### Running Tests

All tests can be run from the `synthesis/opensource` directory using the Makefile:

```bash
cd ../synthesis/opensource

# Run all unit tests
make test

# Run individual tests
make sim-regfile
make sim-alu
make sim-decoder
```

### Expected Output

**All tests passing:**
```
=========================================
Register File Testbench
=========================================

Test 1: Write and read x5
  PASS: Read correct value 0xDEADBEEF

Test 2: x0 hardwired to 0 (read)
  PASS: x0 reads as 0

...

=========================================
Test Summary
=========================================
Total tests: 14
Errors:      0

*** ALL TESTS PASSED! ***

Register file is working correctly!
You can now proceed to implement the ALU.
=========================================
```

**Tests failing:**
```
Test 1: Write and read x5
  FAIL: Expected 0xDEADBEEF, got 0x00000000

...

*** 5 TESTS FAILED ***

Fix the register file implementation:
  1. Check write logic (rd_wen && rd_addr != 0)
  2. Check read logic (x0 handling)
  3. Re-run: make sim-regfile
```

## Testbench Details

### tb_regfile.v - Register File Tests

**Tests:**
1. Write and read single register
2. x0 always reads as 0
3. Writes to x0 are ignored
4. Write and read multiple registers
5. Simultaneous dual-port read (rs1 and rs2)
6. Simultaneous write and read (forwarding)

**Total:** 14 test cases

**What it validates:**
- Register write logic works correctly
- x0 is hardwired to 0 (both read and write)
- Dual-port read capability
- Reset functionality

### tb_alu.v - ALU Tests

**Tests:**
- **ADD:** 4 test cases (including overflow)
- **SUB:** 4 test cases (including underflow)
- **AND:** 3 test cases
- **OR:** 3 test cases
- **XOR:** 3 test cases
- **SLL:** 4 test cases (including edge cases)
- **SRL:** 4 test cases (logical shift)
- **SRA:** 4 test cases (arithmetic shift with sign extension)
- **SLT:** 5 test cases (signed comparison)
- **SLTU:** 4 test cases (unsigned comparison)
- **Zero flag:** 2 test cases

**Total:** 40+ test cases

**What it validates:**
- All 10 ALU operations produce correct results
- Signed vs unsigned operations
- Shift operations use only lower 5 bits
- Zero flag is set correctly

### tb_decoder.v - Decoder Tests

**Tests:**
1. **Field extraction:** 2 test cases (I-type and R-type)
2. **I-type immediates:** 4 test cases (positive, negative, zero, max)
3. **S-type immediates:** 2 test cases (positive and negative offsets)
4. **B-type immediates:** 2 test cases (forward and backward branches)
5. **U-type immediates:** 2 test cases (LUI and AUIPC)
6. **J-type immediates:** 2 test cases (forward and backward jumps)
7. **Control signals:** 6 test cases (ADDI, ADD, LW, SW, BEQ, JAL)

**Total:** 20+ test cases

**What it validates:**
- Instruction fields extracted correctly
- All 6 immediate formats decoded correctly
- Sign extension works properly
- Control signals generated correctly for each instruction type

## Viewing Waveforms

To view waveforms in GTKWave:

```bash
# After running tests, waveforms are saved to build/*.vcd
cd ../synthesis/opensource

# View specific waveform
make wave-regfile
make wave-alu
make wave-decoder
```

**GTKWave tips:**
1. Click on signals in the left pane to add them to the waveform view
2. Use Zoom Fit (Ctrl+Alt+F) to see all data
3. Use the search function to find specific signals
4. Save your view configuration for later use

## Debugging Failed Tests

### Common Issues

**1. Register File Tests Failing**

**Symptom:** Reads return 0 when they shouldn't
- **Check:** Did you implement the read logic?
- **Fix:** Add the conditional read logic:
  ```verilog
  assign rs1_data = (rs1_addr == 5'd0) ? 32'h0 : registers[rs1_addr];
  ```

**Symptom:** Writes don't persist
- **Check:** Did you implement the write logic?
- **Fix:** Add write logic in the always block:
  ```verilog
  if (rd_wen && (rd_addr != 5'd0)) begin
      registers[rd_addr] <= rd_data;
  end
  ```

**2. ALU Tests Failing**

**Symptom:** Some operations work, others don't
- **Check:** Did you implement all case statements?
- **Fix:** Make sure every ALU_OP_* has an implementation

**Symptom:** Shift operations incorrect
- **Check:** Are you using only lower 5 bits of operand_b?
- **Fix:** Use `operand_b[4:0]` for shift amount

**Symptom:** SLT/SLTU incorrect
- **Check:** Are you using $signed() for SLT but not SLTU?
- **Fix:**
  ```verilog
  SLT:  result = ($signed(operand_a) < $signed(operand_b)) ? 32'd1 : 32'd0;
  SLTU: result = (operand_a < operand_b) ? 32'd1 : 32'd0;
  ```

**3. Decoder Tests Failing**

**Symptom:** Immediate values wrong
- **Check:** Are you using the correct bit fields?
- **Check:** Is sign extension working?
- **Fix:** Use replication for sign extension:
  ```verilog
  immediate = {{20{instruction[31]}}, instruction[31:20]};  // I-type
  ```

**Symptom:** Control signals wrong
- **Check:** Did you implement all opcode cases?
- **Check:** Are you setting all control signals in each case?
- **Fix:** Make sure to set all control signals (not just some)

## Test Development Workflow

**Recommended order:**

1. **Implement regfile.v**
   - Add write logic
   - Add read logic
   - Run: `make sim-regfile`
   - Debug until all tests pass

2. **Implement alu.v**
   - Add all 10 operations
   - Run: `make sim-alu`
   - Debug until all tests pass

3. **Implement decoder.v**
   - Add immediate decoding (start with I-type)
   - Add control signals (start with ADDI)
   - Run: `make sim-decoder`
   - Add more instruction types
   - Debug until all tests pass

4. **Implement state machine**
   - Implement FETCH, DECODE, EXECUTE, MEM, WRITEBACK states
   - Create tb_core.v to test full instruction execution
   - Run instruction sequences
   - Debug until programs run correctly

## Integration Testing

After all unit tests pass, create integration tests:

**Example test program (assembly):**
```asm
    addi x1, x0, 10      # x1 = 10
    addi x2, x0, 20      # x2 = 20
    add  x3, x1, x2      # x3 = x1 + x2 = 30
    sub  x4, x3, x1      # x4 = x3 - x1 = 20
```

**Convert to machine code:**
```hex
00A00093  # addi x1, x0, 10
01400113  # addi x2, x0, 20
002081B3  # add  x3, x1, x2
40118233  # sub  x4, x3, x1
```

**Load into memory and simulate:**
- Update ROM with test program
- Run simulation
- Check register values match expected

## Performance Metrics

The testbenches also help measure:

1. **Code Coverage:**
   - Which lines of code were tested
   - Which cases were exercised

2. **Timing:**
   - Combinational delay
   - Critical path identification

3. **Correctness:**
   - Functional verification
   - Edge case handling

## Next Steps

After all unit tests pass:

1. ✅ **Unit tests pass** → Implement core state machine
2. ✅ **State machine works** → Run integration tests
3. ✅ **Integration tests pass** → Synthesize with Yosys
4. ✅ **Yosys synthesis clean** → Take to school for Cadence
5. ✅ **Cadence synthesis** → Place & Route
6. ✅ **P&R complete** → Generate GDSII
7. ✅ **GDSII ready** → Write homework report

## Additional Resources

**Icarus Verilog Documentation:**
- http://iverilog.icarus.com/

**GTKWave Documentation:**
- http://gtkwave.sourceforge.net/

**RISC-V ISA Manual:**
- https://riscv.org/technical/specifications/

**Debugging Tips:**
- Use `$display()` to print values during simulation
- Use `$monitor()` to track signal changes
- View waveforms to see signal transitions
- Compare with RISC-V ISA manual for instruction encoding

## Support

If tests are failing and you're stuck:

1. Check the implementation hints in the RTL files
2. View waveforms to see what's happening
3. Add debug print statements
4. Compare with RISC-V ISA specification
5. Check the QUICK_START.md guide for implementation examples

---

**Happy testing!** 🧪

Remember: Every test that passes gets you closer to a working RISC-V core!
