/**
 * @file custom_riscv_core.v
 * @brief Custom RV32IM RISC-V Core with Zpec Extension (Native Wishbone)
 *
 * This is the main processor core implementing:
 * - RV32I base integer instruction set (40 instructions)
 * - M extension: multiply/divide (8 instructions)
 * - Zpec extension: power electronics custom instructions (6 instructions)
 *
 * Architecture: 3-stage pipeline (Fetch, Decode/Execute, Writeback)
 * ISA: RV32IM + Zpec
 * Bus: Native Wishbone B4 (Approach 2 - Cleaner Design)
 *
 * IMPLEMENTATION APPROACH: Native Wishbone (Approach 2)
 * - Core uses standard Wishbone B4 protocol directly
 * - No cmd/rsp conversion needed
 * - Cleaner, more reusable design
 * - Wrapper is just a simple passthrough
 *
 * @author Custom RISC-V Core Team
 * @date 2025-12-03
 * @version 0.2 - Approach 2: Native Wishbone Template
 */

module custom_riscv_core #(
    parameter RESET_VECTOR = 32'h00000000  // Reset PC address
)(
    input  wire        clk,
    input  wire        rst_n,  // Active LOW reset (Wishbone standard)

    //==========================================================================
    // Instruction Wishbone Bus (Master)
    //==========================================================================

    output wire [31:0] iwb_adr_o,   // Instruction address
    input  wire [31:0] iwb_dat_i,   // Instruction data from memory
    output wire        iwb_cyc_o,   // Cycle active
    output wire        iwb_stb_o,   // Strobe
    input  wire        iwb_ack_i,   // Acknowledge

    //==========================================================================
    // Data Wishbone Bus (Master)
    //==========================================================================

    output wire [31:0] dwb_adr_o,   // Data address
    output wire [31:0] dwb_dat_o,   // Data to write
    input  wire [31:0] dwb_dat_i,   // Data read from memory/peripheral
    output wire        dwb_we_o,    // Write enable (1=write, 0=read)
    output wire [3:0]  dwb_sel_o,   // Byte select
    output wire        dwb_cyc_o,   // Cycle active
    output wire        dwb_stb_o,   // Strobe
    input  wire        dwb_ack_i,   // Acknowledge
    input  wire        dwb_err_i,   // Bus error

    //==========================================================================
    // Interrupts
    //==========================================================================

    input  wire [31:0] interrupts   // Interrupt inputs [31:0]
);

    //==========================================================================
    // IMPLEMENTATION GUIDE - Approach 2: Native Wishbone
    //==========================================================================

    /**
     * WISHBONE PROTOCOL BASICS:
     *
     * Read Cycle:
     *   1. Master asserts CYC, STB, ADR (and clears WE)
     *   2. Slave sees STB=1, prepares data
     *   3. Slave asserts ACK with valid data on DAT_I
     *   4. Master reads data, clears CYC/STB
     *
     * Write Cycle:
     *   1. Master asserts CYC, STB, ADR, DAT_O, WE, SEL
     *   2. Slave sees STB=1 and WE=1, writes data
     *   3. Slave asserts ACK
     *   4. Master clears CYC/STB
     *
     * IMPLEMENTATION STRATEGY:
     *
     * Stage 1: Fetch
     *   - Generate iwb_adr_o = PC
     *   - Assert iwb_cyc_o, iwb_stb_o
     *   - Wait for iwb_ack_i
     *   - Latch instruction from iwb_dat_i
     *   - Increment PC
     *
     * Stage 2: Decode/Execute
     *   - Decode instruction
     *   - Read register file
     *   - Execute ALU operation
     *   - For LOAD/STORE:
     *     * Assert dwb_cyc_o, dwb_stb_o
     *     * Set dwb_adr_o, dwb_we_o, dwb_sel_o
     *     * Wait for dwb_ack_i
     *   - For branches: update PC
     *
     * Stage 3: Writeback
     *   - Write result to register file
     *   - For LOAD: write dwb_dat_i to register
     *
     * START SIMPLE:
     *   1. Implement single-cycle (no pipeline) first
     *   2. Just fetch → decode → execute → writeback sequentially
     *   3. Add pipelining later for performance
     */

    //==========================================================================
    // Internal Signals
    //==========================================================================

    // Program Counter
    reg [31:0] pc;

    // Instruction register
    reg [31:0] instruction;

    // Register file signals
    wire [4:0]  rs1_addr, rs2_addr, rd_addr;
    wire [31:0] rs1_data, rs2_data, rd_data;
    wire        rd_wen;

    // Decode signals
    wire [6:0]  opcode;
    wire [2:0]  funct3;
    wire [6:0]  funct7;
    wire [31:0] immediate;

    // ALU signals
    wire [31:0] alu_operand_a, alu_operand_b;
    wire [3:0]  alu_op;
    wire [31:0] alu_result;
    wire        alu_zero;
    // M-extension signal from decoder
    wire        is_m;

    // Control signals from decoder
    wire        alu_src_imm;      // ALU source: 0=rs2, 1=immediate
    wire        mem_read;         // Memory read enable (loads)
    wire        mem_write;        // Memory write enable (stores)
    wire        reg_write;        // Register write enable
    wire        is_branch;        // Is branch instruction
    wire        is_jump;          // Is jump instruction
    wire        is_system;        // Is system instruction
    wire        branch_taken;
    wire [31:0] branch_target;

    // State machine (for multi-cycle operations)
    reg [2:0] state;
    localparam STATE_FETCH     = 3'd0;
    localparam STATE_DECODE    = 3'd1;
    localparam STATE_EXECUTE   = 3'd2;
    localparam STATE_MEM       = 3'd3;
    localparam STATE_WRITEBACK = 3'd4;
    localparam STATE_MULDIV    = 3'd5;

    reg [31:0] alu_result_reg;
    // M-extension control and results
    reg         mdu_start;
    wire        mdu_busy;
    wire        mdu_done;
    wire [63:0] mdu_product;
    wire [31:0] mdu_quotient;
    wire [31:0] mdu_remainder;

    // temporary register to capture result from MDU
    reg [31:0]  mdu_result_reg;

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
    assign rd_data = mem_read ? dwb_dat_i : alu_result_reg;
    assign rd_wen = reg_write && (state == STATE_WRITEBACK) && !is_branch;


    // Initialize PC on reset
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            pc <= RESET_VECTOR;
            state <= STATE_FETCH;
            iwb_cyc_reg <= 1'b0;
            iwb_stb_reg <= 1'b0;
            dwb_cyc_reg <= 1'b0;
            dwb_stb_reg <= 1'b0;
            mdu_start <= 1'b0;
            mdu_result_reg <= 32'd0;
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
                    if (is_m) begin
                        // Start multiply/divide unit based on funct3
                        // Start pulse lasts one cycle
                        // Start unified MDU
                        mdu_start <= 1'b1;
                        state <= STATE_MULDIV;
                    end else begin
                        alu_result_reg <= alu_result;

                        if (mem_read || mem_write) begin
                            state <= STATE_MEM;
                        end else begin
                            state <= STATE_WRITEBACK;
                        end
                    end
                end

                STATE_MULDIV: begin
                    // Clear one-cycle start pulse
                    mdu_start <= 1'b0;

                    // Wait for MDU completion
                    if (mdu_done) begin
                        // If multiply variants -> select product high/low; else select quotient/remainder
                        case (funct3)
                            `FUNCT3_MUL:    mdu_result_reg <= mdu_product[31:0];
                            `FUNCT3_MULH:   mdu_result_reg <= mdu_product[63:32];
                            `FUNCT3_MULHSU: mdu_result_reg <= mdu_product[63:32];
                            `FUNCT3_MULHU:  mdu_result_reg <= mdu_product[63:32];
                            `FUNCT3_DIV:    mdu_result_reg <= mdu_quotient;
                            `FUNCT3_DIVU:   mdu_result_reg <= mdu_quotient;
                            `FUNCT3_REM:    mdu_result_reg <= mdu_remainder;
                            `FUNCT3_REMU:   mdu_result_reg <= mdu_remainder;
                            default:        mdu_result_reg <= mdu_product[31:0];
                        endcase
                        alu_result_reg <= mdu_result_reg;
                        state <= STATE_WRITEBACK;
                    end else begin
                        // remain in MULDIV until unit signals done
                        state <= STATE_MULDIV;
                    end
                end

                STATE_MEM: begin
                    if (mem_read || mem_write) begin
                        dwb_cyc_reg <= 1'b1;
                        dwb_stb_reg <= 1'b1;
                        dwb_adr_reg <= alu_result_reg;  // Address from ALU
                        dwb_we_reg <= mem_write;

                        if (mem_write) begin
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
                    // Register write happens via rd_wen signal (combinational)

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
                end
            endcase

        end
    end

    //==========================================================================
    // MODULE INSTANTIATIONS
    //==========================================================================
    
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

    // Instruction Decoder
    decoder decoder_inst (
        .instruction(instruction),
        .opcode(opcode),
        .funct3(funct3),
        .funct7(funct7),
        .rs1_addr(rs1_addr),
        .rs2_addr(rs2_addr),
        .rd_addr(rd_addr),
        .immediate(immediate),
        // Control signals
        .alu_op(alu_op),
        .alu_src_imm(alu_src_imm),
        .mem_read(mem_read),
        .mem_write(mem_write),
        .reg_write(reg_write),
        .is_branch(is_branch),
        .is_jump(is_jump),
        .is_system(is_system),
        .is_m(is_m)
    );

    /*

    // CSR File (for interrupts and system instructions)
    csr_file csr_inst (
        .clk(clk),
        .rst_n(rst_n),
        .csr_addr(instruction[31:20]),
        .csr_wdata(rs1_data),
        .csr_rdata(csr_rdata),
        .csr_we(csr_we),
        .interrupts(interrupts),
        .interrupt_taken(interrupt_taken),
        .trap_vector(trap_vector)
    );
    
    */

    // Unified MDU instance (handles MUL/MULH/MULHSU/MULHU and DIV/DIVU/REM/REMU)
    mdu mdu_inst (
        .clk(clk),
        .rst_n(rst_n),
        .start(mdu_start),
        .funct3(funct3),
        .a(rs1_data),
        .b(rs2_data),
        .busy(mdu_busy),
        .done(mdu_done),
        .product(mdu_product),
        .quotient(mdu_quotient),
        .remainder(mdu_remainder)
    );
endmodule
