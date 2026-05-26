# RISC-V Test Programs

This directory contains C programs compiled for testing the custom RISC-V core.

## Workflow: C to Testbench

### 1. Write C Program

Write your program with these constraints:
- Use `void _start(void) __attribute__((naked, noreturn));` as entry point
- No standard library (`-nostdlib` compilation)
- RV32I instructions only (no multiply, divide, floating-point)
- Results in `a0` (x10) register for easy verification

### 2. Compile with RISC-V GCC

```bash
# Simple inline assembly (recommended for small programs)
/opt/riscv/bin/riscv32-unknown-elf-gcc \
    -march=rv32i \
    -mabi=ilp32 \
    -nostdlib \
    -nostartfiles \
    -o program.elf \
    program.c \
    -Wl,--section-start=.text=0x0

# Complex programs with functions
/opt/riscv/bin/riscv32-unknown-elf-gcc \
    -march=rv32i \
    -mabi=ilp32 \
    -nostdlib \
    -T linker.ld \
    -O0 \
    -fno-inline \
    -o program.elf \
    program.c
```

### 3. Verify Disassembly

```bash
/opt/riscv/bin/riscv32-unknown-elf-objdump -d program.elf
```

Check that:
- `_start` is at address 0x00000000
- Only RV32I instructions are used
- No unexpected library calls

### 4. Extract Binary and Convert to Verilog

```bash
# Extract raw binary
/opt/riscv/bin/riscv32-unknown-elf-objcopy -O binary program.elf program.bin

# Convert to Verilog hex format
python3 bin2verilog.py program.bin -o program_imem.vh
```

### 5. Create Testbench

```verilog
// Include the converted hex file in your testbench
initial begin
    `include "../../programs/program_imem.vh"

    // Fill rest with NOPs
    for (init_i = NUM_WORDS; init_i < 256; init_i = init_i + 1) begin
        imem[init_i] = 32'h00000013;
    end
end
```

### 6. Run Simulation

```bash
cd ../sim/testbench
iverilog -I../../rtl/core -o test_program tb_program.v ../../rtl/core/*.v
vvp test_program
```

## Available Programs

### factorial_simple.c - Phase 3 Milestone

- **Purpose**: Tests control flow (branches, jumps, loops)
- **Algorithm**: Calculate factorial(5) = 120 using repeated addition
- **Result**: a0 (x10) = 120
- **Instructions Used**: ADDI, ADD, BEQ, BGE, J, MV (pseudo-instruction)
- **Testbench**: `tb_c_factorial.v`

### memory_test.c - Phase 4 Milestone (TODO)

- **Purpose**: Tests load/store operations and Wishbone bus
- **Algorithm**: Array initialization, sorting, sum calculation
- **Result**: Sum in a0 (x10)
- **Instructions Used**: LW, SW, LB, SB, LH, SH, and all control flow

## Tips for Writing Test Programs

1. **Start Simple**: Begin with inline assembly for full control
2. **Use Volatile**: Prevents compiler optimizations that might use unsupported instructions
3. **Check Disassembly**: Always verify the generated machine code
4. **RV32I Only**: No multiply (M), compressed (C), or floating-point (F) extensions
5. **Test Incrementally**: Test individual features before combining them

## Common Issues

### Compiler Uses Multiply (__mulsi3)

**Problem**: Even with repeated addition, compiler optimizes to multiply
**Solution**: Use inline assembly or `-O0` with volatile variables

### _start Not at Address 0

**Problem**: Functions appear in wrong order
**Solution**: Use inline assembly or explicit section placement

### Undefined References

**Problem**: Linker looking for standard library functions
**Solution**: Use `-nostdlib -nostartfiles` flags

## References

- RISC-V Specification: https://riscv.org/technical/specifications/
- RISC-V Assembly Programmer's Manual: https://github.com/riscv/riscv-asm-manual
- GCC RISC-V Options: https://gcc.gnu.org/onlinedocs/gcc/RISC-V-Options.html
