`include "riscv_defines.vh"

module decoder (
    input  wire [31:0] instruction,  // 32-bit instruction from memory

    // Extracted instruction fields
    output wire [6:0]  opcode,       // Instruction opcode [6:0]
    output wire [2:0]  funct3,       // Function 3 [14:12]
    output wire [6:0]  funct7,       // Function 7 [31:25]
    output wire [4:0]  rs1_addr,     // Source register 1 [19:15]
    output wire [4:0]  rs2_addr,     // Source register 2 [24:20]
    output wire [4:0]  rd_addr,      // Destination register [11:7]
    output reg  [31:0] immediate,    // Decoded immediate value

    // Control signals
    output reg  [3:0]  alu_op,       // ALU operation
    output reg         alu_src_imm,  // ALU source: 0=rs2, 1=immediate
    output reg         mem_read,     // Memory read enable
    output reg         mem_write,    // Memory write enable
    output reg         reg_write,    // Register write enable
    output reg         is_branch,    // Is branch instruction
    output reg         is_jump,      // Is jump instruction (JAL/JALR)
    output reg         is_system     // Is system instruction (ECALL, etc.)
    ,output reg        is_m          // Is M-extension (multiply/divide)
);

    //==========================================================================
    // Instruction Field Extraction
    //==========================================================================

    /**
     * All RISC-V instructions have these fields in the same positions:
     *
     * [31:25] = funct7 (for R-type)
     * [24:20] = rs2 (source register 2)
     * [19:15] = rs1 (source register 1)
     * [14:12] = funct3
     * [11:7]  = rd (destination register)
     * [6:0]   = opcode
     */

    assign opcode   = instruction[6:0];
    assign funct3   = instruction[14:12];
    assign funct7   = instruction[31:25];
    assign rs1_addr = instruction[19:15];
    assign rs2_addr = instruction[24:20];
    assign rd_addr  = instruction[11:7];

    //==========================================================================
    // Immediate Decoding
    //==========================================================================

    /**
     * RISC-V has 6 immediate formats:
     *
     * I-type: [31:20] = imm[11:0]
     *   Used by: ADDI, SLTI, LW, JALR, etc.
     *   Sign-extend bit 31 to fill upper 20 bits
     *
     * S-type: [31:25] = imm[11:5], [11:7] = imm[4:0]
     *   Used by: SW, SH, SB
     *   Sign-extend bit 31
     *
     * B-type: [31] = imm[12], [30:25] = imm[10:5],
     *         [11:8] = imm[4:1], imm[0] = 0
     *   Used by: BEQ, BNE, BLT, BGE, BLTU, BGEU
     *   Sign-extend bit 31, always even (bit 0 = 0)
     *
     * U-type: [31:12] = imm[31:12], [11:0] = 0
     *   Used by: LUI, AUIPC
     *   Upper 20 bits, lower 12 bits are 0
     *
     * J-type: [31] = imm[20], [30:21] = imm[10:1],
     *         [20] = imm[11], [19:12] = imm[19:12], imm[0] = 0
     *   Used by: JAL
     *   Sign-extend bit 31, always even (bit 0 = 0)
     */

    always @(*) begin
        case (opcode)
            `OPCODE_OP_IMM, `OPCODE_LOAD, `OPCODE_JALR: begin
                // I-type immediate
                 immediate = {{20{instruction[31]}}, instruction[31:20]};
            end

            `OPCODE_STORE: begin
                // S-type immediate
                immediate = {{20{instruction[31]}}, instruction[31:25], instruction[11:7]};
            end

            `OPCODE_BRANCH: begin
                // B-type immediate (sign-extended from 13 bits)
                immediate = {{20{instruction[31]}}, instruction[7], instruction[30:25], instruction[11:8], 1'b0};
            end

            `OPCODE_LUI, `OPCODE_AUIPC: begin
                // U-type immediate
                 immediate = {instruction[31:12], 12'h0};
            end

            `OPCODE_JAL: begin
                // J-type immediate (sign-extended from 21 bits)
                immediate = {{12{instruction[31]}}, instruction[19:12], instruction[20], instruction[30:21], 1'b0};
            end

            default: begin
                immediate = 32'h0;
            end
        endcase
    end

    //==========================================================================
    // Control Signal Generation
    //==========================================================================

    /**
     * Based on opcode and funct3/funct7, generate:
     * - alu_op: Which ALU operation to perform
     * - alu_src_imm: Use immediate (1) or rs2 (0) as ALU operand
     * - mem_read: Load instruction (LW, LH, LB, etc.)
     * - mem_write: Store instruction (SW, SH, SB)
     * - reg_write: Write result to rd
     * - is_branch: Branch instruction (BEQ, BNE, etc.)
     * - is_jump: Jump instruction (JAL, JALR)
     * - is_system: System instruction (ECALL, EBREAK, CSR*)
     */

    always @(*) begin
        // Default values
        alu_op = `ALU_OP_ADD;
        alu_src_imm = 1'b0;
        mem_read = 1'b0;
        mem_write = 1'b0;
        reg_write = 1'b0;
        is_branch = 1'b0;
        is_jump = 1'b0;
        is_system = 1'b0;
        is_m = 1'b0;

        case (opcode)
            `OPCODE_OP_IMM: begin
                // I-type arithmetic (ADDI, SLTI, XORI, etc.)
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
                // R-type arithmetic (ADD, SUB, AND, OR, etc.)
                alu_src_imm = 1'b0;  // Use rs2
                reg_write = 1'b1;
                // Check M-extension first (funct7 == `FUNCT7_MUL_DIV)
                if (funct7 == `FUNCT7_MUL_DIV) begin
                    is_m = 1'b1;
                    case (funct3)
                        `FUNCT3_MUL:    alu_op = `ALU_OP_MUL;
                        `FUNCT3_MULH:   alu_op = `ALU_OP_MULH;
                        `FUNCT3_MULHSU: alu_op = `ALU_OP_MULHSU;
                        `FUNCT3_MULHU:  alu_op = `ALU_OP_MULHU;
                        `FUNCT3_DIV:    alu_op = `ALU_OP_DIV;
                        `FUNCT3_DIVU:   alu_op = `ALU_OP_DIVU;
                        `FUNCT3_REM:    alu_op = `ALU_OP_DIV;  // REM uses DIV hardware, core selects remainder
                        `FUNCT3_REMU:   alu_op = `ALU_OP_DIVU; // REMU uses DIVU hardware
                        default:        alu_op = `ALU_OP_ADD;
                    endcase
                end else begin
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
            end

            `OPCODE_LOAD: begin
                // Load instructions (LW, LH, LB, LHU, LBU)
                alu_op = `ALU_OP_ADD;  // Calculate address = rs1 + immediate
                alu_src_imm = 1'b1;
                mem_read = 1'b1;
                reg_write = 1'b1;
            end

            `OPCODE_STORE: begin
                // Store instructions (SW, SH, SB)
                alu_op = `ALU_OP_ADD;  // Calculate address = rs1 + immediate
                alu_src_imm = 1'b1;
                mem_write = 1'b1;
            end

            `OPCODE_BRANCH: begin
                // Branch instructions (BEQ, BNE, BLT, BGE, BLTU, BGEU)
                alu_op = `ALU_OP_SUB;  // For comparison
                is_branch = 1'b1;
            end

            `OPCODE_JAL: begin
                // Jump and Link: rd = PC + 4, PC = PC + immediate
                alu_op = `ALU_OP_ADD;
                alu_src_imm = 1'b1;  // Use immediate for jump offset calculation
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

            `OPCODE_SYSTEM: begin
                // System instructions (ECALL, EBREAK, CSR*)
                // TODO: Implement
            end

            default: begin
                // Invalid opcode - do nothing
            end
        endcase
    end

endmodule
