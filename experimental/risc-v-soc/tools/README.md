# RISC-V Core Build System

**⚠️ IMPORTANT: This directory contains legacy build scripts.**

**For current development, use the new workflow in:**
- **`../synthesis/opensource/`** - For testing and synthesis at home
- See `../README.md` for complete instructions

---

## New Workflow (Recommended)

**For homework and current development:**

```bash
# Navigate to the new build directory
cd ../synthesis/opensource

# Run all tests
make test

# Run individual tests
make sim-regfile
make sim-alu
make sim-decoder

# Lint checking
make lint

# Synthesis
make synth

# View waveforms
make wave-regfile
make wave-alu
make wave-decoder

# See help
make help
```

**Complete documentation:**
- **Quick Start:** `../rtl/core/QUICK_START.md`
- **Testing Guide:** `../sim/README.md`
- **Open-Source Workflow:** `../synthesis/opensource/README.md`
- **Main README:** `../README.md`

---

## What's Different?

### Old Workflow (This Directory)
- Generic Makefile for module creation
- Separate testbench directory structure
- Less focused on homework requirements

### New Workflow (synthesis/opensource/)
- **Homework-specific** build system
- **Comprehensive testbenches** with 40+ test cases
- **Dual workflow** support (home + school)
- **Integrated synthesis** (Yosys + Cadence)
- **Better documentation** with step-by-step guides

---

## Migration Guide

If you were using this directory, here's how to switch:

### Old Command → New Command

| Old Command | New Command |
|-------------|-------------|
| `make test MODULE=regfile` | `cd ../synthesis/opensource && make sim-regfile` |
| `make test MODULE=alu` | `cd ../synthesis/opensource && make sim-alu` |
| `make waves MODULE=regfile` | `cd ../synthesis/opensource && make wave-regfile` |
| `make lint` | `cd ../synthesis/opensource && make lint` |
| `make test-all` | `cd ../synthesis/opensource && make test` |

### File Locations

| Old Location | New Location |
|--------------|--------------|
| `../sim/testbenches/tb_regfile.v` | `../sim/testbench/tb_regfile.v` ✅ (exists) |
| `../sim/testbenches/tb_alu.v` | `../sim/testbench/tb_alu.v` ✅ (exists) |
| Build artifacts in `../sim/build/` | Build artifacts in `../synthesis/opensource/build/` |
| Waveforms in `../sim/waves/` | Waveforms in `../synthesis/opensource/build/` |

---

## Why Switch?

The new workflow in `synthesis/opensource/` provides:

1. ✅ **Complete testbenches** - 40+ test cases ready to use
2. ✅ **Homework integration** - Aligned with RTL-to-GDSII assignment
3. ✅ **Better documentation** - Step-by-step guides
4. ✅ **Dual workflow** - Open-source at home, Cadence at school
5. ✅ **Synthesis support** - Yosys and Cadence scripts ready
6. ✅ **Detailed error messages** - Tests tell you exactly what's wrong
7. ✅ **Quick start guide** - Get running in 5 minutes

---

## Legacy Commands (Still Available)

If you want to use this directory's Makefile (not recommended for homework):

### Environment Check

```bash
make env-check
```

Verifies that all required tools are installed.

### Create a New Module

```bash
make new-module NAME=regfile
```

Creates:
- `../rtl/core/regfile.v` (module template)
- `../sim/testbenches/tb_regfile.v` (testbench template)

**Note:** The new workflow already has better templates in place!

### Run Tests

```bash
make test MODULE=regfile
```

**Better:** Use `cd ../synthesis/opensource && make sim-regfile` instead.

### View Waveforms

```bash
make waves MODULE=regfile
```

**Better:** Use `cd ../synthesis/opensource && make wave-regfile` instead.

### Multiple Module Tests

```bash
make test-regfile                # Test register file
make test-alu                    # Test ALU
make test-decode                 # Test decoder
make test-core                   # Test full core
make test-all                    # Run all tests
```

**Better:** Use `cd ../synthesis/opensource && make test` instead.

### Cleanup

```bash
make clean                       # Remove build artifacts
make distclean                   # Deep clean
```

---

## Required Tools (Same for Both Workflows)

### Simulation

- **Icarus Verilog** (`iverilog`, `vvp`)
  ```bash
  sudo apt-get install iverilog
  ```

- **GTKWave** (waveform viewer)
  ```bash
  sudo apt-get install gtkwave
  ```

- **Verilator** (lint checking)
  ```bash
  sudo apt-get install verilator
  ```

### Synthesis

- **Yosys** (open-source synthesis)
  ```bash
  sudo apt-get install yosys
  ```

### RISC-V Toolchain (Optional - for firmware)

- **GCC for RISC-V**
  ```bash
  # Ubuntu/Debian
  sudo apt-get install gcc-riscv64-unknown-elf

  # Or build from source
  git clone https://github.com/riscv/riscv-gnu-toolchain
  cd riscv-gnu-toolchain
  ./configure --prefix=/opt/riscv --with-arch=rv32im --with-abi=ilp32
  make
  ```

---

## Recommended Next Steps

1. **Read the main README:**
   ```bash
   less ../README.md
   ```

2. **Follow the homework guide:**
   ```bash
   less ../docs/HOMEWORK_GUIDE.md
   ```

3. **Use the new workflow:**
   ```bash
   cd ../synthesis/opensource
   make help
   ```

4. **Start implementing:**
   ```bash
   # Follow step-by-step guide
   less ../rtl/core/QUICK_START.md
   ```

---

## Additional Resources

### Primary Documentation (Use These!)

- **Main README:** `../README.md` ⭐⭐⭐
- **Homework Guide:** `../docs/HOMEWORK_GUIDE.md` ⭐⭐⭐
- **Quick Start:** `../rtl/core/QUICK_START.md` ⭐⭐⭐
- **Testing Guide:** `../sim/README.md` ⭐⭐
- **Open-Source Workflow:** `../synthesis/opensource/README.md` ⭐⭐

### Legacy Documentation (Outdated)

- ~~`../docs/IMPLEMENTATION_ROADMAP.md`~~ (superseded by HOMEWORK_GUIDE.md)
- ~~`../docs/CUSTOM_CORE_REQUIREMENTS.md`~~ (if exists, outdated)

### Project Guidelines

- **Claude.md:** `../../../CLAUDE.md` (project-wide guidelines)

---

## Support

**For homework and current development:**
1. Check `../README.md`
2. Read `../docs/HOMEWORK_GUIDE.md`
3. Use `../synthesis/opensource/` workflow
4. Follow `../rtl/core/QUICK_START.md`

**For questions:**
1. Check documentation (usually has the answer)
2. Read error messages (tests are very detailed)
3. View waveforms (shows exactly what happened)
4. Check RISC-V ISA manual
5. Ask TA/professor

---

**Status:** Legacy (use `../synthesis/opensource/` instead)
**Last Updated:** 2025-12-05
**Superseded By:** `../synthesis/opensource/README.md`
