#===============================================================================
# Open-Source Synthesis & Simulation Makefile
# For: Custom RISC-V Core (RV32IM)
# Tools: Icarus Verilog, Yosys, Verilator
#===============================================================================

# Directories
RTL_DIR = ../../rtl
CORE_DIR = $(RTL_DIR)/core
SIM_DIR = ../../sim
TB_DIR = $(SIM_DIR)/testbench
BUILD_DIR = build
REPORTS_DIR = reports

# RTL source files
RTL_SOURCES = \
	$(CORE_DIR)/regfile.v \
	$(CORE_DIR)/alu.v \
	$(CORE_DIR)/decoder.v \
	$(CORE_DIR)/custom_riscv_core.v \
	$(CORE_DIR)/custom_core_wrapper.v

# Testbench files
TB_REGFILE = $(TB_DIR)/tb_regfile.v
TB_ALU = $(TB_DIR)/tb_alu.v
TB_DECODER = $(TB_DIR)/tb_decoder.v
TB_CORE = $(TB_DIR)/tb_core.v

# Defines file
DEFINES = $(CORE_DIR)/riscv_defines.vh

# Simulation executables
SIM_REGFILE = $(BUILD_DIR)/sim_regfile
SIM_ALU = $(BUILD_DIR)/sim_alu
SIM_DECODER = $(BUILD_DIR)/sim_decoder
SIM_CORE = $(BUILD_DIR)/sim_core

# Tools
IVERILOG = iverilog
VVP = vvp
YOSYS = yosys
VERILATOR = verilator

# Flags
IVERILOG_FLAGS = -g2012 -Wall
YOSYS_FLAGS =
VERILATOR_FLAGS = --lint-only --timing -Wall

#===============================================================================
# Default target
#===============================================================================

.PHONY: all
all: test

#===============================================================================
# Directory creation
#===============================================================================

$(BUILD_DIR):
	mkdir -p $(BUILD_DIR)

$(REPORTS_DIR):
	mkdir -p $(REPORTS_DIR)

#===============================================================================
# Simulation targets
#===============================================================================

# Register file simulation
.PHONY: sim-regfile
sim-regfile: $(BUILD_DIR) $(SIM_REGFILE)
	@echo "========================================="
	@echo "Running Register File Testbench"
	@echo "========================================="
	$(VVP) $(SIM_REGFILE)

$(SIM_REGFILE): $(CORE_DIR)/regfile.v $(TB_REGFILE)
	$(IVERILOG) $(IVERILOG_FLAGS) -o $@ -I$(CORE_DIR) $^

# ALU simulation
.PHONY: sim-alu
sim-alu: $(BUILD_DIR) $(SIM_ALU)
	@echo "========================================="
	@echo "Running ALU Testbench"
	@echo "========================================="
	$(VVP) $(SIM_ALU)

$(SIM_ALU): $(CORE_DIR)/alu.v $(TB_ALU) $(DEFINES)
	$(IVERILOG) $(IVERILOG_FLAGS) -o $@ -I$(CORE_DIR) $(CORE_DIR)/alu.v $(TB_ALU)

# Decoder simulation
.PHONY: sim-decoder
sim-decoder: $(BUILD_DIR) $(SIM_DECODER)
	@echo "========================================="
	@echo "Running Decoder Testbench"
	@echo "========================================="
	$(VVP) $(SIM_DECODER)

$(SIM_DECODER): $(CORE_DIR)/decoder.v $(TB_DECODER) $(DEFINES)
	$(IVERILOG) $(IVERILOG_FLAGS) -o $@ -I$(CORE_DIR) $(CORE_DIR)/decoder.v $(TB_DECODER)

# Full core simulation
.PHONY: sim-core
sim-core: $(BUILD_DIR) $(SIM_CORE)
	@echo "========================================="
	@echo "Running Core Testbench"
	@echo "========================================="
	$(VVP) $(SIM_CORE)

$(SIM_CORE): $(RTL_SOURCES) $(TB_CORE) $(DEFINES)
	$(IVERILOG) $(IVERILOG_FLAGS) -o $@ -I$(CORE_DIR) $(RTL_SOURCES) $(TB_CORE)

# Run all simulations
.PHONY: test
test: sim-regfile sim-alu sim-decoder
	@echo ""
	@echo "========================================="
	@echo "All Unit Tests Complete!"
	@echo "========================================="
	@echo ""
	@echo "Next steps:"
	@echo "  1. If all tests pass, implement core state machine"
	@echo "  2. Run 'make sim-core' to test full core"
	@echo "  3. Run 'make synth' to synthesize with Yosys"
	@echo "  4. Run 'make lint' to check for issues"
	@echo ""

#===============================================================================
# Synthesis targets (Yosys)
#===============================================================================

.PHONY: synth
synth: $(BUILD_DIR) $(REPORTS_DIR)
	@echo "========================================="
	@echo "Synthesizing with Yosys"
	@echo "========================================="
	$(YOSYS) synth.ys
	@echo ""
	@echo "Synthesis complete! Check reports/synthesis.txt"
	@echo ""

#===============================================================================
# Lint checking (Verilator)
#===============================================================================

.PHONY: lint
lint:
	@echo "========================================="
	@echo "Running Verilator Lint"
	@echo "========================================="
	$(VERILATOR) $(VERILATOR_FLAGS) -I$(CORE_DIR) $(RTL_SOURCES)
	@echo ""
	@echo "Lint complete!"
	@echo ""

#===============================================================================
# Waveform viewing
#===============================================================================

.PHONY: wave-regfile
wave-regfile: sim-regfile
	gtkwave $(BUILD_DIR)/regfile.vcd &

.PHONY: wave-alu
wave-alu: sim-alu
	gtkwave $(BUILD_DIR)/alu.vcd &

.PHONY: wave-decoder
wave-decoder: sim-decoder
	gtkwave $(BUILD_DIR)/decoder.vcd &

.PHONY: wave-core
wave-core: sim-core
	gtkwave $(BUILD_DIR)/core.vcd &

#===============================================================================
# Clean
#===============================================================================

.PHONY: clean
clean:
	rm -rf $(BUILD_DIR)
	rm -rf $(REPORTS_DIR)
	@echo "Build directory cleaned"

#===============================================================================
# Help
#===============================================================================

.PHONY: help
help:
	@echo "Available targets:"
	@echo ""
	@echo "  Simulation:"
	@echo "    make sim-regfile  - Run register file testbench"
	@echo "    make sim-alu      - Run ALU testbench"
	@echo "    make sim-decoder  - Run decoder testbench"
	@echo "    make sim-core     - Run full core testbench"
	@echo "    make test         - Run all unit tests"
	@echo ""
	@echo "  Synthesis:"
	@echo "    make synth        - Synthesize with Yosys"
	@echo "    make lint         - Run Verilator lint checking"
	@echo ""
	@echo "  Waveforms:"
	@echo "    make wave-regfile - View register file waveforms"
	@echo "    make wave-alu     - View ALU waveforms"
	@echo "    make wave-decoder - View decoder waveforms"
	@echo "    make wave-core    - View core waveforms"
	@echo ""
	@echo "  Utilities:"
	@echo "    make clean        - Clean build files"
	@echo "    make help         - Show this help"
	@echo ""
	@echo "Quick start:"
	@echo "  1. make test         # Run all unit tests"
	@echo "  2. make lint         # Check for issues"
	@echo "  3. make synth        # Synthesize design"
	@echo ""
