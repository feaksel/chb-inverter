/**
 * @file riscv_defines.vh
 * @brief RISC-V RV32IM Instruction Set Definitions
 *
 * This file contains all opcode, funct3, funct7, and CSR address
 * definitions for the RV32IM instruction set.
 *
 * @author Custom RISC-V Core Project
 * @date 2025-12-03
 * @version 1.0
 */

`ifndef RISCV_DEFINES_VH
`define RISCV_DEFINES_VH

//==========================================================================
// Instruction Formats
//==========================================================================

// R-type: [31:25] funct7, [24:20] rs2, [19:15] rs1, [14:12] funct3, [11:7] rd, [6:0] opcode
// I-type: [31:20] imm[11:0], [19:15] rs1, [14:12] funct3, [11:7] rd, [6:0] opcode
// S-type: [31:25] imm[11:5], [24:20] rs2, [19:15] rs1, [14:12] funct3, [11:7] imm[4:0], [6:0] opcode
// B-type: [31] imm[12], [30:25] imm[10:5], [24:20] rs2, [19:15] rs1, [14:12] funct3, [11:8] imm[4:1], [7] imm[11], [6:0] opcode
// U-type: [31:12] imm[31:12], [11:7] rd, [6:0] opcode
// J-type: [31] imm[20], [30:21] imm[10:1], [20] imm[11], [19:12] imm[19:12], [11:7] rd, [6:0] opcode

//==========================================================================
// Opcodes (bits [6:0])
//==========================================================================

`define OPCODE_LOAD       7'b0000011  // Load instructions (LB, LH, LW, LBU, LHU)
`define OPCODE_LOAD_FP    7'b0000111  // Floating-point load (not implemented)
`define OPCODE_MISC_MEM   7'b0001111  // Memory ordering (FENCE)
`define OPCODE_OP_IMM     7'b0010011  // Integer register-immediate (ADDI, SLTI, etc.)
`define OPCODE_AUIPC      7'b0010111  // Add upper immediate to PC
`define OPCODE_OP_IMM_32  7'b0011011  // RV64I only (not implemented)

`define OPCODE_STORE      7'b0100011  // Store instructions (SB, SH, SW)
`define OPCODE_STORE_FP   7'b0100111  // Floating-point store (not implemented)
`define OPCODE_AMO        7'b0101111  // Atomic memory operations (not implemented)
`define OPCODE_OP         7'b0110011  // Integer register-register (ADD, SUB, MUL, etc.)
`define OPCODE_LUI        7'b0110111  // Load upper immediate
`define OPCODE_OP_32      7'b0111011  // RV64I only (not implemented)

`define OPCODE_MADD       7'b1000011  // Fused multiply-add (not implemented)
`define OPCODE_MSUB       7'b1000111  // Fused multiply-subtract (not implemented)
`define OPCODE_NMSUB      7'b1001011  // Fused negate multiply-subtract (not implemented)
`define OPCODE_NMADD      7'b1001111  // Fused negate multiply-add (not implemented)
`define OPCODE_OP_FP      7'b1010011  // Floating-point operations (not implemented)

`define OPCODE_BRANCH     7'b1100011  // Branch instructions (BEQ, BNE, BLT, etc.)
`define OPCODE_JALR       7'b1100111  // Jump and link register
`define OPCODE_JAL        7'b1101111  // Jump and link
`define OPCODE_SYSTEM     7'b1110011  // System instructions (ECALL, EBREAK, CSR)

//==========================================================================
// Funct3 Codes for ALU Operations (OP and OP_IMM)
//==========================================================================

`define FUNCT3_ADD_SUB    3'b000  // ADD/SUB (funct7 distinguishes)
`define FUNCT3_SLL        3'b001  // Shift left logical
`define FUNCT3_SLT        3'b010  // Set less than (signed)
`define FUNCT3_SLTU       3'b011  // Set less than (unsigned)
`define FUNCT3_XOR        3'b100  // Bitwise XOR
`define FUNCT3_SRL_SRA    3'b101  // Shift right logical/arithmetic (funct7 distinguishes)
`define FUNCT3_OR         3'b110  // Bitwise OR
`define FUNCT3_AND        3'b111  // Bitwise AND

//==========================================================================
// Funct7 Codes for ALU Operations
//==========================================================================

`define FUNCT7_ADD        7'b0000000  // ADD, SRL
`define FUNCT7_SUB        7'b0100000  // SUB, SRA
`define FUNCT7_MUL_DIV    7'b0000001  // M extension (multiply/divide)

//==========================================================================
// Funct3 Codes for Load Instructions
//==========================================================================

`define FUNCT3_LB         3'b000  // Load byte (signed)
`define FUNCT3_LH         3'b001  // Load halfword (signed)
`define FUNCT3_LW         3'b010  // Load word
`define FUNCT3_LBU        3'b100  // Load byte (unsigned)
`define FUNCT3_LHU        3'b101  // Load halfword (unsigned)

//==========================================================================
// Funct3 Codes for Store Instructions
//==========================================================================

`define FUNCT3_SB         3'b000  // Store byte
`define FUNCT3_SH         3'b001  // Store halfword
`define FUNCT3_SW         3'b010  // Store word

//==========================================================================
// Funct3 Codes for Branch Instructions
//==========================================================================

`define FUNCT3_BEQ        3'b000  // Branch if equal
`define FUNCT3_BNE        3'b001  // Branch if not equal
`define FUNCT3_BLT        3'b100  // Branch if less than (signed)
`define FUNCT3_BGE        3'b101  // Branch if greater or equal (signed)
`define FUNCT3_BLTU       3'b110  // Branch if less than (unsigned)
`define FUNCT3_BGEU       3'b111  // Branch if greater or equal (unsigned)

//==========================================================================
// Funct3 Codes for M Extension (Multiply/Divide)
//==========================================================================

`define FUNCT3_MUL        3'b000  // Multiply (lower 32 bits)
`define FUNCT3_MULH       3'b001  // Multiply (upper 32 bits, signed × signed)
`define FUNCT3_MULHSU     3'b010  // Multiply (upper 32 bits, signed × unsigned)
`define FUNCT3_MULHU      3'b011  // Multiply (upper 32 bits, unsigned × unsigned)
`define FUNCT3_DIV        3'b100  // Divide (signed)
`define FUNCT3_DIVU       3'b101  // Divide (unsigned)
`define FUNCT3_REM        3'b110  // Remainder (signed)
`define FUNCT3_REMU       3'b111  // Remainder (unsigned)

//==========================================================================
// Funct3 Codes for System Instructions
//==========================================================================

`define FUNCT3_PRIV       3'b000  // Privileged (ECALL, EBREAK, MRET, WFI)
`define FUNCT3_CSRRW      3'b001  // CSR read/write
`define FUNCT3_CSRRS      3'b010  // CSR read and set bits
`define FUNCT3_CSRRC      3'b011  // CSR read and clear bits
`define FUNCT3_CSRRWI     3'b101  // CSR read/write immediate
`define FUNCT3_CSRRSI     3'b110  // CSR read and set bits immediate
`define FUNCT3_CSRRCI     3'b111  // CSR read and clear bits immediate

//==========================================================================
// System Instruction Funct12 Codes
//==========================================================================

`define FUNCT12_ECALL     12'b000000000000  // Environment call
`define FUNCT12_EBREAK    12'b000000000001  // Environment break
`define FUNCT12_MRET      12'b001100000010  // Machine return (from trap)
`define FUNCT12_WFI       12'b000100000101  // Wait for interrupt

//==========================================================================
// CSR Addresses
//==========================================================================

// Machine Information Registers
`define CSR_MVENDORID     12'hF11  // Vendor ID
`define CSR_MARCHID       12'hF12  // Architecture ID
`define CSR_MIMPID        12'hF13  // Implementation ID
`define CSR_MHARTID       12'hF14  // Hardware thread ID

// Machine Trap Setup
`define CSR_MSTATUS       12'h300  // Machine status register
`define CSR_MISA          12'h301  // ISA and extensions
`define CSR_MEDELEG       12'h302  // Machine exception delegation
`define CSR_MIDELEG       12'h303  // Machine interrupt delegation
`define CSR_MIE           12'h304  // Machine interrupt enable
`define CSR_MTVEC         12'h305  // Machine trap-handler base address
`define CSR_MCOUNTEREN    12'h306  // Machine counter enable

// Machine Trap Handling
`define CSR_MSCRATCH      12'h340  // Machine scratch register
`define CSR_MEPC          12'h341  // Machine exception program counter
`define CSR_MCAUSE        12'h342  // Machine trap cause
`define CSR_MTVAL         12'h343  // Machine bad address or instruction
`define CSR_MIP           12'h344  // Machine interrupt pending

// Machine Counter/Timers
`define CSR_MCYCLE        12'hB00  // Machine cycle counter (lower 32 bits)
`define CSR_MINSTRET      12'hB02  // Machine instructions retired counter (lower 32 bits)
`define CSR_MCYCLEH       12'hB80  // Machine cycle counter (upper 32 bits)
`define CSR_MINSTRETH     12'hB82  // Machine instructions retired counter (upper 32 bits)

// User-mode accessible counters
`define CSR_CYCLE         12'hC00  // Cycle counter (lower 32 bits)
`define CSR_TIME          12'hC01  // Timer (lower 32 bits)
`define CSR_INSTRET       12'hC02  // Instructions retired (lower 32 bits)
`define CSR_CYCLEH        12'hC80  // Cycle counter (upper 32 bits)
`define CSR_TIMEH         12'hC81  // Timer (upper 32 bits)
`define CSR_INSTRETH      12'hC82  // Instructions retired (upper 32 bits)

//==========================================================================
// mstatus Register Bit Positions
//==========================================================================

`define MSTATUS_MIE       3   // Machine interrupt enable
`define MSTATUS_MPIE      7   // Previous machine interrupt enable
`define MSTATUS_MPP_LO    11  // Previous privilege mode (low bit)
`define MSTATUS_MPP_HI    12  // Previous privilege mode (high bit)

//==========================================================================
// mcause Register Values
//==========================================================================

// Interrupt bit (bit 31 of mcause)
`define MCAUSE_INTERRUPT_BIT  31

// Interrupt causes (with bit 31 set)
`define MCAUSE_SOFTWARE_INT   32'h80000003  // Machine software interrupt
`define MCAUSE_TIMER_INT      32'h80000007  // Machine timer interrupt
`define MCAUSE_EXTERNAL_INT   32'h8000000B  // Machine external interrupt

// Exception causes (bit 31 clear)
`define MCAUSE_INSTR_MISALIGN     32'h00000000  // Instruction address misaligned
`define MCAUSE_INSTR_ACCESS_FAULT 32'h00000001  // Instruction access fault
`define MCAUSE_ILLEGAL_INSTR      32'h00000002  // Illegal instruction
`define MCAUSE_BREAKPOINT         32'h00000003  // Breakpoint
`define MCAUSE_LOAD_MISALIGN      32'h00000004  // Load address misaligned
`define MCAUSE_LOAD_ACCESS_FAULT  32'h00000005  // Load access fault
`define MCAUSE_STORE_MISALIGN     32'h00000006  // Store address misaligned
`define MCAUSE_STORE_ACCESS_FAULT 32'h00000007  // Store access fault
`define MCAUSE_ECALL_M_MODE       32'h0000000B  // Environment call from M-mode

//==========================================================================
// ALU Operations (Internal Control Signals)
//==========================================================================

// These are internal ALU operation codes (not part of ISA)
`define ALU_OP_ADD        4'b0000
`define ALU_OP_SUB        4'b0001
`define ALU_OP_AND        4'b0010
`define ALU_OP_OR         4'b0011
`define ALU_OP_XOR        4'b0100
`define ALU_OP_SLL        4'b0101
`define ALU_OP_SRL        4'b0110
`define ALU_OP_SRA        4'b0111
`define ALU_OP_SLT        4'b1000
`define ALU_OP_SLTU       4'b1001
`define ALU_OP_PASS_A     4'b1010  // Pass operand A (for LUI, AUIPC)
`define ALU_OP_PASS_B     4'b1011  // Pass operand B
// (M Extension):
`define ALU_OP_MUL    4'd10  // Multiply (lower 32 bits)
`define ALU_OP_MULH   4'd11  // Multiply signed (upper 32 bits)
`define ALU_OP_MULHSU 4'd12  // Multiply signed×unsigned (upper 32 bits)
`define ALU_OP_MULHU  4'd13  // Multiply unsigned (upper 32 bits)
`define ALU_OP_DIV    4'd14  // Divide signed
`define ALU_OP_DIVU   4'd15  // Divide unsigned
//==========================================================================
// Memory Access Widths
//==========================================================================

`define MEM_WIDTH_BYTE    2'b00
`define MEM_WIDTH_HALF    2'b01
`define MEM_WIDTH_WORD    2'b10

//==========================================================================
// Pipeline Control Signals
//==========================================================================

`define BRANCH_NOT_TAKEN  1'b0
`define BRANCH_TAKEN      1'b1

//==========================================================================
// Register File Special Registers
//==========================================================================

`define REG_ZERO          5'd0   // x0: Always zero
`define REG_RA            5'd1   // x1: Return address
`define REG_SP            5'd2   // x2: Stack pointer
`define REG_GP            5'd3   // x3: Global pointer
`define REG_TP            5'd4   // x4: Thread pointer

//==========================================================================
// Privilege Levels
//==========================================================================

`define PRIV_USER         2'b00
`define PRIV_SUPERVISOR   2'b01
`define PRIV_RESERVED     2'b10
`define PRIV_MACHINE      2'b11

//==========================================================================
// Constants
//==========================================================================

`define XLEN              32     // Register width
`define RESET_VECTOR      32'h00000000  // Reset PC value
`define TRAP_VECTOR       32'h00000004  // Default trap vector (can be changed via mtvec)

//==========================================================================
// Utility Macros
//==========================================================================

// Extract instruction fields
`define GET_OPCODE(instr)   instr[6:0]
`define GET_RD(instr)       instr[11:7]
`define GET_FUNCT3(instr)   instr[14:12]
`define GET_RS1(instr)      instr[19:15]
`define GET_RS2(instr)      instr[24:20]
`define GET_FUNCT7(instr)   instr[31:25]
`define GET_FUNCT12(instr)  instr[31:20]

// Immediate extraction
`define GET_I_IMM(instr)    {{20{instr[31]}}, instr[31:20]}
`define GET_S_IMM(instr)    {{20{instr[31]}}, instr[31:25], instr[11:7]}
`define GET_B_IMM(instr)    {{19{instr[31]}}, instr[31], instr[7], instr[30:25], instr[11:8], 1'b0}
`define GET_U_IMM(instr)    {instr[31:12], 12'b0}
`define GET_J_IMM(instr)    {{11{instr[31]}}, instr[31], instr[19:12], instr[20], instr[30:21], 1'b0}

//==========================================================================
// Debug and Simulation
//==========================================================================

`ifdef SIMULATION
    `define ASSERT(condition, message) \
        if (!(condition)) begin \
            $display("ASSERTION FAILED: %s", message); \
            $display("  File: %s, Line: %d", `__FILE__, `__LINE__); \
            $finish; \
        end
`else
    `define ASSERT(condition, message)
`endif

`endif // RISCV_DEFINES_VH
