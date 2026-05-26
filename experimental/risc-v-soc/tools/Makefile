# Makefile for RISC-V RV32IM Custom Core
# Supports Verilator and Icarus Verilog simulation

#==========================================================================
# Configuration
#==========================================================================

# Project directories
ROOT_DIR := ..
RTL_DIR := $(ROOT_DIR)/rtl/core
SIM_DIR := $(ROOT_DIR)/sim
TB_DIR := $(SIM_DIR)/testbenches
BUILD_DIR := $(SIM_DIR)/build
WAVE_DIR := $(SIM_DIR)/waves

# Toolchain
RISCV_PREFIX ?= riscv32-unknown-elf-
CC := $(RISCV_PREFIX)gcc
AS := $(RISCV_PREFIX)as
LD := $(RISCV_PREFIX)ld
OBJCOPY := $(RISCV_PREFIX)objcopy
OBJDUMP := $(RISCV_PREFIX)objdump

# Simulation tools
SIMULATOR ?= iverilog  # Options: iverilog, verilator
IVERILOG := iverilog
VVP := vvp
GTKWAVE := gtkwave
VERILATOR := verilator

# Compiler flags
CFLAGS := -march=rv32im -mabi=ilp32 -O2 -Wall -Wextra
LDFLAGS := -nostdlib -nostartfiles
ASFLAGS := -march=rv32im -mabi=ilp32

#==========================================================================
# Source Files
#==========================================================================

# RTL source files (add as you implement modules)
RTL_SOURCES := \
	$(RTL_DIR)/riscv_defines.vh

# Testbench sources
TB_SOURCES := \
	$(TB_DIR)/tb_template.v

#==========================================================================
# Targets
#==========================================================================

.PHONY: all clean help test sim waves dirs

all: dirs
	@echo "RISC-V Core Build System"
	@echo "========================"
	@echo "Use 'make help' to see available commands"

help:
	@echo "Available targets:"
	@echo "  make test MODULE=<name>  - Run testbench for specified module"
	@echo "  make sim MODULE=<name>   - Run simulation (same as test)"
	@echo "  make waves MODULE=<name> - Open waveform viewer"
	@echo "  make clean               - Clean build artifacts"
	@echo "  make dirs                - Create directory structure"
	@echo ""
	@echo "Examples:"
	@echo "  make test MODULE=regfile"
	@echo "  make waves MODULE=regfile"
	@echo "  make clean"
	@echo ""
	@echo "Simulator selection (default: iverilog):"
	@echo "  make test MODULE=regfile SIMULATOR=iverilog"
	@echo "  make test MODULE=regfile SIMULATOR=verilator"

dirs:
	@mkdir -p $(BUILD_DIR)
	@mkdir -p $(WAVE_DIR)

#==========================================================================
# Simulation Targets (Icarus Verilog)
#==========================================================================

ifeq ($(SIMULATOR),iverilog)

test: dirs
	@echo "========================================"
	@echo "Running testbench: tb_$(MODULE)"
	@echo "Simulator: Icarus Verilog"
	@echo "========================================"
	@if [ ! -f $(TB_DIR)/tb_$(MODULE).v ]; then \
		echo "Error: Testbench $(TB_DIR)/tb_$(MODULE).v not found!"; \
		exit 1; \
	fi
	$(IVERILOG) -g2012 -o $(BUILD_DIR)/tb_$(MODULE).vvp \
		-I $(RTL_DIR) \
		-s tb_$(MODULE) \
		$(TB_DIR)/tb_$(MODULE).v \
		$(RTL_DIR)/$(MODULE).v \
		$(RTL_SOURCES)
	$(VVP) $(BUILD_DIR)/tb_$(MODULE).vvp
	@mv tb_$(MODULE).vcd $(WAVE_DIR)/ 2>/dev/null || true
	@echo "========================================"
	@echo "Simulation complete"
	@echo "Waveform: $(WAVE_DIR)/tb_$(MODULE).vcd"
	@echo "========================================"

waves:
	@if [ ! -f $(WAVE_DIR)/tb_$(MODULE).vcd ]; then \
		echo "Error: Waveform file $(WAVE_DIR)/tb_$(MODULE).vcd not found!"; \
		echo "Run 'make test MODULE=$(MODULE)' first."; \
		exit 1; \
	fi
	$(GTKWAVE) $(WAVE_DIR)/tb_$(MODULE).vcd &

endif

#==========================================================================
# Simulation Targets (Verilator)
#==========================================================================

ifeq ($(SIMULATOR),verilator)

test: dirs
	@echo "========================================"
	@echo "Running testbench: tb_$(MODULE)"
	@echo "Simulator: Verilator"
	@echo "========================================"
	@if [ ! -f $(TB_DIR)/tb_$(MODULE).v ]; then \
		echo "Error: Testbench $(TB_DIR)/tb_$(MODULE).v not found!"; \
		exit 1; \
	fi
	$(VERILATOR) --cc --exe --build \
		-I$(RTL_DIR) \
		--top-module tb_$(MODULE) \
		--Mdir $(BUILD_DIR)/verilator_$(MODULE) \
		--trace \
		$(TB_DIR)/tb_$(MODULE).v \
		$(RTL_DIR)/$(MODULE).v \
		$(RTL_SOURCES)
	$(BUILD_DIR)/verilator_$(MODULE)/Vtb_$(MODULE)
	@echo "========================================"
	@echo "Simulation complete"
	@echo "========================================"

waves:
	@echo "Verilator: Use VCD viewer to open trace file"
	@echo "Trace file: $(BUILD_DIR)/verilator_$(MODULE)/trace.vcd"

endif

#==========================================================================
# Assembly and C Program Compilation
#==========================================================================

# Compile assembly program
%.elf: %.s
	$(AS) $(ASFLAGS) -o $(BUILD_DIR)/$@.o $<
	$(LD) $(LDFLAGS) -o $(BUILD_DIR)/$@ $(BUILD_DIR)/$@.o
	$(OBJDUMP) -d $(BUILD_DIR)/$@ > $(BUILD_DIR)/$(@:.elf=.dis)
	$(OBJCOPY) -O binary $(BUILD_DIR)/$@ $(BUILD_DIR)/$(@:.elf=.bin)
	@echo "Built: $(BUILD_DIR)/$@"

# Compile C program
%.c.elf: %.c
	$(CC) $(CFLAGS) -c -o $(BUILD_DIR)/$@.o $<
	$(LD) $(LDFLAGS) -o $(BUILD_DIR)/$@ $(BUILD_DIR)/$@.o
	$(OBJDUMP) -d $(BUILD_DIR)/$@ > $(BUILD_DIR)/$(@:.elf=.dis)
	$(OBJCOPY) -O binary $(BUILD_DIR)/$@ $(BUILD_DIR)/$(@:.elf=.bin)
	@echo "Built: $(BUILD_DIR)/$@"

# Convert binary to hex (for loading into instruction memory)
%.hex: %.bin
	od -An -tx4 -w4 -v $(BUILD_DIR)/$< | awk '{print $$1}' > $(BUILD_DIR)/$@
	@echo "Generated: $(BUILD_DIR)/$@"

#==========================================================================
# Quick Tests for Common Modules
#==========================================================================

test-regfile:
	@$(MAKE) test MODULE=regfile

test-alu:
	@$(MAKE) test MODULE=alu

test-decode:
	@$(MAKE) test MODULE=decode

test-core:
	@$(MAKE) test MODULE=riscv_core_simple

test-all: test-regfile test-alu test-decode test-core
	@echo "All tests completed!"

#==========================================================================
# Cleanup
#==========================================================================

clean:
	rm -rf $(BUILD_DIR)
	rm -rf $(WAVE_DIR)
	rm -f *.vcd *.vvp *.log
	@echo "Cleaned build artifacts"

distclean: clean
	rm -f $(ROOT_DIR)/rtl/core/*.vcd
	rm -f $(TB_DIR)/*.vcd
	@echo "Deep clean complete"

#==========================================================================
# Linting (optional, requires verilator)
#==========================================================================

lint:
	@echo "Running Verilator linter..."
	$(VERILATOR) --lint-only \
		-I$(RTL_DIR) \
		$(RTL_DIR)/*.v \
		2>&1 | tee lint.log
	@echo "Lint complete. Check lint.log for results."

#==========================================================================
# Synthesis Check (optional, requires Yosys)
#==========================================================================

synth-check:
	@echo "Running synthesis check with Yosys..."
	yosys -p "read_verilog -sv $(RTL_DIR)/*.v; synth -top riscv_core_top; stat" \
		2>&1 | tee synth.log
	@echo "Synthesis check complete. Check synth.log for results."

#==========================================================================
# Information Targets
#==========================================================================

info:
	@echo "Project Information"
	@echo "==================="
	@echo "Root directory:    $(ROOT_DIR)"
	@echo "RTL directory:     $(RTL_DIR)"
	@echo "Testbench dir:     $(TB_DIR)"
	@echo "Build directory:   $(BUILD_DIR)"
	@echo "Waveform dir:      $(WAVE_DIR)"
	@echo ""
	@echo "Simulator:         $(SIMULATOR)"
	@echo "RISC-V toolchain:  $(RISCV_PREFIX)"
	@echo ""
	@echo "RTL source files:"
	@for file in $(RTL_SOURCES); do echo "  $$file"; done
	@echo ""

env-check:
	@echo "Checking environment..."
	@which $(IVERILOG) > /dev/null && echo "✓ Icarus Verilog found" || echo "✗ Icarus Verilog not found"
	@which $(VVP) > /dev/null && echo "✓ VVP found" || echo "✗ VVP not found"
	@which $(GTKWAVE) > /dev/null && echo "✓ GTKWave found" || echo "✗ GTKWave not found"
	@which $(VERILATOR) > /dev/null && echo "✓ Verilator found" || echo "✗ Verilator not found"
	@which $(CC) > /dev/null && echo "✓ RISC-V GCC found" || echo "✗ RISC-V GCC not found"
	@which $(AS) > /dev/null && echo "✓ RISC-V assembler found" || echo "✗ RISC-V assembler not found"

#==========================================================================
# Development Helpers
#==========================================================================

# Create new module template
new-module:
	@if [ -z "$(NAME)" ]; then \
		echo "Error: Please specify NAME=<module_name>"; \
		exit 1; \
	fi
	@echo "Creating module: $(NAME).v"
	@echo "/**" > $(RTL_DIR)/$(NAME).v
	@echo " * @file $(NAME).v" >> $(RTL_DIR)/$(NAME).v
	@echo " * @brief <Brief description>" >> $(RTL_DIR)/$(NAME).v
	@echo " */" >> $(RTL_DIR)/$(NAME).v
	@echo "" >> $(RTL_DIR)/$(NAME).v
	@echo "module $(NAME) (" >> $(RTL_DIR)/$(NAME).v
	@echo "    input  wire       clk," >> $(RTL_DIR)/$(NAME).v
	@echo "    input  wire       rst_n" >> $(RTL_DIR)/$(NAME).v
	@echo "    // TODO: Add ports" >> $(RTL_DIR)/$(NAME).v
	@echo ");" >> $(RTL_DIR)/$(NAME).v
	@echo "" >> $(RTL_DIR)/$(NAME).v
	@echo "    // TODO: Implement module" >> $(RTL_DIR)/$(NAME).v
	@echo "" >> $(RTL_DIR)/$(NAME).v
	@echo "endmodule" >> $(RTL_DIR)/$(NAME).v
	@echo "Created: $(RTL_DIR)/$(NAME).v"
	@echo ""
	@echo "Creating testbench: tb_$(NAME).v"
	@cp $(TB_DIR)/tb_template.v $(TB_DIR)/tb_$(NAME).v
	@sed -i 's/tb_template/tb_$(NAME)/g' $(TB_DIR)/tb_$(NAME).v
	@echo "Created: $(TB_DIR)/tb_$(NAME).v"
	@echo ""
	@echo "Next steps:"
	@echo "  1. Edit $(RTL_DIR)/$(NAME).v - implement your module"
	@echo "  2. Edit $(TB_DIR)/tb_$(NAME).v - write test cases"
	@echo "  3. Run: make test MODULE=$(NAME)"

# Quick start guide
quickstart:
	@echo "Quick Start Guide for RISC-V Core Development"
	@echo "=============================================="
	@echo ""
	@echo "1. Check environment:"
	@echo "   make env-check"
	@echo ""
	@echo "2. Create a new module:"
	@echo "   make new-module NAME=regfile"
	@echo ""
	@echo "3. Implement the module:"
	@echo "   Edit rtl/core/regfile.v"
	@echo ""
	@echo "4. Write tests:"
	@echo "   Edit sim/testbenches/tb_regfile.v"
	@echo ""
	@echo "5. Run simulation:"
	@echo "   make test MODULE=regfile"
	@echo ""
	@echo "6. View waveforms:"
	@echo "   make waves MODULE=regfile"
	@echo ""
	@echo "For more help:"
	@echo "   make help"
	@echo "   See docs/IMPLEMENTATION_ROADMAP.md"
	@echo ""

.PHONY: lint synth-check info env-check new-module quickstart
