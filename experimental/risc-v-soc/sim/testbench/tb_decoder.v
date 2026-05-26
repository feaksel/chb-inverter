/**
 * @file tb_decoder.v
 * @brief Testbench for RISC-V Instruction Decoder
 *
 * Tests:
 * - Instruction field extraction
 * - Immediate decoding (I, S, B, U, J types)
 * - Control signal generation
 * - All major instruction types
 *
 * @author Custom RISC-V Core Team
 * @date 2025-12-03
 */

`timescale 1ns / 1ps

`include "riscv_defines.vh"

module tb_decoder;

    //==========================================================================
    // Signals
    //==========================================================================

    reg  [31:0] instruction;
    wire [6:0]  opcode;
    wire [2:0]  funct3;
    wire [6:0]  funct7;
    wire [4:0]  rs1_addr;
    wire [4:0]  rs2_addr;
    wire [4:0]  rd_addr;
    wire [31:0] immediate;
    wire [3:0]  alu_op;
    wire        alu_src_imm;
    wire        mem_read;
    wire        mem_write;
    wire        reg_write;
    wire        is_branch;
    wire        is_jump;
    wire        is_system;

    // Test status
    integer errors = 0;
    integer tests = 0;

    //==========================================================================
    // DUT Instantiation
    //==========================================================================

    decoder dut (
        .instruction(instruction),
        .opcode(opcode),
        .funct3(funct3),
        .funct7(funct7),
        .rs1_addr(rs1_addr),
        .rs2_addr(rs2_addr),
        .rd_addr(rd_addr),
        .immediate(immediate),
        .alu_op(alu_op),
        .alu_src_imm(alu_src_imm),
        .mem_read(mem_read),
        .mem_write(mem_write),
        .reg_write(reg_write),
        .is_branch(is_branch),
        .is_jump(is_jump),
        .is_system(is_system)
    );

    //==========================================================================
    // Test Tasks
    //==========================================================================

    task test_fields;
        input [31:0] instr;
        input [6:0]  exp_opcode;
        input [2:0]  exp_funct3;
        input [6:0]  exp_funct7;
        input [4:0]  exp_rs1;
        input [4:0]  exp_rs2;
        input [4:0]  exp_rd;
        input [80*8:1] desc;
        begin
            instruction = instr;
            #10;

            tests = tests + 1;
            if (opcode !== exp_opcode || funct3 !== exp_funct3 ||
                funct7 !== exp_funct7 || rs1_addr !== exp_rs1 ||
                rs2_addr !== exp_rs2 || rd_addr !== exp_rd) begin
                $display("  FAIL: %s", desc);
                $display("        Instruction: 0x%h", instr);
                if (opcode !== exp_opcode)
                    $display("        opcode: got 0x%h, expected 0x%h", opcode, exp_opcode);
                if (funct3 !== exp_funct3)
                    $display("        funct3: got 0x%h, expected 0x%h", funct3, exp_funct3);
                if (funct7 !== exp_funct7)
                    $display("        funct7: got 0x%h, expected 0x%h", funct7, exp_funct7);
                if (rs1_addr !== exp_rs1)
                    $display("        rs1: got %0d, expected %0d", rs1_addr, exp_rs1);
                if (rs2_addr !== exp_rs2)
                    $display("        rs2: got %0d, expected %0d", rs2_addr, exp_rs2);
                if (rd_addr !== exp_rd)
                    $display("        rd: got %0d, expected %0d", rd_addr, exp_rd);
                errors = errors + 1;
            end else begin
                $display("  PASS: %s", desc);
            end
        end
    endtask

    task test_immediate;
        input [31:0] instr;
        input [31:0] exp_imm;
        input [80*8:1] desc;
        begin
            instruction = instr;
            #10;

            tests = tests + 1;
            if (immediate !== exp_imm) begin
                $display("  FAIL: %s", desc);
                $display("        Instruction: 0x%h", instr);
                $display("        Expected immediate: 0x%h (%0d)", exp_imm, $signed(exp_imm));
                $display("        Got immediate:      0x%h (%0d)", immediate, $signed(immediate));
                errors = errors + 1;
            end else begin
                $display("  PASS: %s (imm=0x%h)", desc, immediate);
            end
        end
    endtask

    task test_control;
        input [31:0] instr;
        input [3:0]  exp_alu_op;
        input        exp_alu_src;
        input        exp_mem_rd;
        input        exp_mem_wr;
        input        exp_reg_wr;
        input        exp_branch;
        input        exp_jump;
        input [80*8:1] desc;
        begin
            instruction = instr;
            #10;

            tests = tests + 1;
            if (alu_op !== exp_alu_op || alu_src_imm !== exp_alu_src ||
                mem_read !== exp_mem_rd || mem_write !== exp_mem_wr ||
                reg_write !== exp_reg_wr || is_branch !== exp_branch ||
                is_jump !== exp_jump) begin
                $display("  FAIL: %s", desc);
                $display("        Instruction: 0x%h", instr);
                if (alu_op !== exp_alu_op)
                    $display("        alu_op: got %0d, expected %0d", alu_op, exp_alu_op);
                if (alu_src_imm !== exp_alu_src)
                    $display("        alu_src_imm: got %0d, expected %0d", alu_src_imm, exp_alu_src);
                if (mem_read !== exp_mem_rd)
                    $display("        mem_read: got %0d, expected %0d", mem_read, exp_mem_rd);
                if (mem_write !== exp_mem_wr)
                    $display("        mem_write: got %0d, expected %0d", mem_write, exp_mem_wr);
                if (reg_write !== exp_reg_wr)
                    $display("        reg_write: got %0d, expected %0d", reg_write, exp_reg_wr);
                if (is_branch !== exp_branch)
                    $display("        is_branch: got %0d, expected %0d", is_branch, exp_branch);
                if (is_jump !== exp_jump)
                    $display("        is_jump: got %0d, expected %0d", is_jump, exp_jump);
                errors = errors + 1;
            end else begin
                $display("  PASS: %s", desc);
            end
        end
    endtask

    //==========================================================================
    // Test Stimulus
    //==========================================================================

    initial begin
        // Initialize waveform dump
        $dumpfile("build/decoder.vcd");
        $dumpvars(0, tb_decoder);

        instruction = 32'h00000013;  // NOP (ADDI x0, x0, 0)
        #20;

        $display("========================================");
        $display("Decoder Testbench");
        $display("========================================");
        $display("");

        //======================================================================
        // Test Field Extraction
        //======================================================================
        $display("Testing field extraction:");
        // Note: For I-type instructions like ADDI, funct7 and rs2 fields
        // are part of the immediate and are not meaningful to check.
        // Only testing R-type here where all fields are valid.

        // ADD x7, x3, x4
        // R-type: funct7 = 0, rs2 = 4, rs1 = 3, funct3 = 0, rd = 7, opcode = 0x33
        test_fields(32'h004183B3, 7'h33, 3'h0, 7'h00, 5'd3, 5'd4, 5'd7,
                    "ADD x7, x3, x4");

        //======================================================================
        // Test I-type Immediate Decoding
        //======================================================================
        $display("");
        $display("Testing I-type immediates:");

        // ADDI x5, x10, 100 (positive immediate)
        test_immediate(32'h06450293, 32'd100, "ADDI with imm=100");

        // ADDI x5, x10, -1 (negative immediate, all 1s)
        test_immediate(32'hFFF50293, 32'hFFFFFFFF, "ADDI with imm=-1");

        // ADDI x5, x10, 0 (zero immediate)
        test_immediate(32'h00050293, 32'd0, "ADDI with imm=0");

        // ADDI x5, x10, 2047 (maximum positive 12-bit)
        test_immediate(32'h7FF50293, 32'd2047, "ADDI with imm=2047");

        //======================================================================
        // Test S-type Immediate Decoding
        //======================================================================
        $display("");
        $display("Testing S-type immediates:");

        // SW x5, 100(x10)
        // S-type: imm[11:5]=3, imm[4:0]=4, rs2=5, rs1=10, funct3=2, opcode=0x23
        test_immediate(32'h06552223, 32'd100, "SW with offset=100");

        // SW x5, -4(x10)
        // S-type: imm=-4
        test_immediate(32'hFE552E23, 32'hFFFFFFFC, "SW with offset=-4");

        //======================================================================
        // Test B-type Immediate Decoding
        //======================================================================
        $display("");
        $display("Testing B-type immediates:");

        // BEQ x10, x11, 8
        // B-type: imm=8 (word offset 2, byte offset 8)
        test_immediate(32'h00B50463, 32'd8, "BEQ with offset=8");

        // BEQ x10, x11, -4
        test_immediate(32'hFEB50EE3, 32'hFFFFFFFC, "BEQ with offset=-4");

        //======================================================================
        // Test U-type Immediate Decoding
        //======================================================================
        $display("");
        $display("Testing U-type immediates:");

        // LUI x5, 0x12345 (upper 20 bits)
        test_immediate(32'h123452B7, 32'h12345000, "LUI with imm=0x12345000");

        // AUIPC x5, 0x1000
        test_immediate(32'h01000297, 32'h01000000, "AUIPC with imm=0x01000000");

        //======================================================================
        // Test J-type Immediate Decoding
        //======================================================================
        $display("");
        $display("Testing J-type immediates:");

        // JAL x1, 8 (byte offset)
        test_immediate(32'h008000EF, 32'd8, "JAL with offset=8");

        // JAL x1, -4
        test_immediate(32'hFFDFF0EF, 32'hFFFFFFFC, "JAL with offset=-4");

        //======================================================================
        // Test Control Signals - ADDI
        //======================================================================
        $display("");
        $display("Testing control signals:");

        // ADDI x5, x10, 100
        // Should: use ALU_ADD, use immediate, write register
        test_control(32'h06450293,
                    `ALU_OP_ADD,  // alu_op
                    1'b1,         // alu_src_imm
                    1'b0,         // mem_read
                    1'b0,         // mem_write
                    1'b1,         // reg_write
                    1'b0,         // is_branch
                    1'b0,         // is_jump
                    "ADDI control signals");

        //======================================================================
        // Test Control Signals - ADD (R-type)
        //======================================================================
        // ADD x7, x3, x4
        // Should: use ALU_ADD, use rs2 (not immediate), write register
        test_control(32'h004183B3,
                    `ALU_OP_ADD,  // alu_op
                    1'b0,         // alu_src_imm (use rs2)
                    1'b0,         // mem_read
                    1'b0,         // mem_write
                    1'b1,         // reg_write
                    1'b0,         // is_branch
                    1'b0,         // is_jump
                    "ADD control signals");

        //======================================================================
        // Test Control Signals - LW
        //======================================================================
        // LW x5, 100(x10)
        test_control(32'h06452283,
                    `ALU_OP_ADD,  // alu_op (address calculation)
                    1'b1,         // alu_src_imm
                    1'b1,         // mem_read
                    1'b0,         // mem_write
                    1'b1,         // reg_write
                    1'b0,         // is_branch
                    1'b0,         // is_jump
                    "LW control signals");

        //======================================================================
        // Test Control Signals - SW
        //======================================================================
        // SW x5, 100(x10)
        test_control(32'h06552223,
                    `ALU_OP_ADD,  // alu_op (address calculation)
                    1'b1,         // alu_src_imm
                    1'b0,         // mem_read
                    1'b1,         // mem_write
                    1'b0,         // reg_write (stores don't write registers)
                    1'b0,         // is_branch
                    1'b0,         // is_jump
                    "SW control signals");

        //======================================================================
        // Test Control Signals - BEQ
        //======================================================================
        // BEQ x10, x11, 8
        test_control(32'h00B50463,
                    `ALU_OP_SUB,  // alu_op (comparison by subtraction)
                    1'b0,         // alu_src_imm (compare registers)
                    1'b0,         // mem_read
                    1'b0,         // mem_write
                    1'b0,         // reg_write
                    1'b1,         // is_branch
                    1'b0,         // is_jump
                    "BEQ control signals");

        //======================================================================
        // Test Control Signals - JAL
        //======================================================================
        // JAL x1, 8
        test_control(32'h008000EF,
                    `ALU_OP_ADD,  // alu_op (for PC+4 calculation)
                    1'b1,         // alu_src_imm
                    1'b0,         // mem_read
                    1'b0,         // mem_write
                    1'b1,         // reg_write (save return address)
                    1'b0,         // is_branch
                    1'b1,         // is_jump
                    "JAL control signals");

        //======================================================================
        // Summary
        //======================================================================
        #20;
        $display("");
        $display("========================================");
        $display("Test Summary");
        $display("========================================");
        $display("Total tests: %0d", tests);
        $display("Errors:      %0d", errors);

        if (errors == 0) begin
            $display("");
            $display("*** ALL TESTS PASSED! ***");
            $display("");
            $display("Decoder is working correctly!");
            $display("You can now proceed to implement the core state machine.");
        end else begin
            $display("");
            $display("*** %0d TESTS FAILED ***", errors);
            $display("");
            $display("Fix the decoder implementation:");
            $display("  1. Check immediate format extraction");
            $display("  2. Check sign extension logic");
            $display("  3. Check control signal generation");
            $display("  4. Re-run: make sim-decoder");
        end
        $display("========================================");

        $finish;
    end

    //==========================================================================
    // Timeout watchdog
    //==========================================================================

    initial begin
        #100000;
        $display("ERROR: Testbench timeout!");
        $finish;
    end

endmodule
