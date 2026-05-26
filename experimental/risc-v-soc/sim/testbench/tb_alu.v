/**
 * @file tb_alu.v
 * @brief Testbench for RISC-V ALU
 *
 * Tests all ALU operations:
 * - Arithmetic: ADD, SUB
 * - Logic: AND, OR, XOR
 * - Shifts: SLL, SRL, SRA
 * - Comparisons: SLT, SLTU
 *
 * @author Custom RISC-V Core Team
 * @date 2025-12-03
 */

`timescale 1ns / 1ps

`include "riscv_defines.vh"

module tb_alu;

    //==========================================================================
    // Signals
    //==========================================================================

    reg  [31:0] operand_a;
    reg  [31:0] operand_b;
    reg  [3:0]  alu_op;
    wire [31:0] result;
    wire        zero;

    // Test status
    integer errors = 0;
    integer tests = 0;

    //==========================================================================
    // DUT Instantiation
    //==========================================================================

    alu dut (
        .operand_a(operand_a),
        .operand_b(operand_b),
        .alu_op(alu_op),
        .result(result),
        .zero(zero)
    );

    //==========================================================================
    // Test Task
    //==========================================================================

    task test_alu;
        input [31:0] a;
        input [31:0] b;
        input [3:0]  op;
        input [31:0] expected;
        input [80*8:1] op_name;  // Operation name string
        begin
            operand_a = a;
            operand_b = b;
            alu_op = op;
            #10;  // Wait for combinational logic

            tests = tests + 1;
            if (result !== expected) begin
                $display("  FAIL: %s", op_name);
                $display("        a=0x%h, b=0x%h", a, b);
                $display("        Expected: 0x%h, Got: 0x%h", expected, result);
                errors = errors + 1;
            end else begin
                $display("  PASS: %s (0x%h)", op_name, result);
            end
        end
    endtask

    //==========================================================================
    // Test Stimulus
    //==========================================================================

    initial begin
        // Initialize waveform dump
        $dumpfile("build/alu.vcd");
        $dumpvars(0, tb_alu);

        // Initialize signals
        operand_a = 0;
        operand_b = 0;
        alu_op = 0;

        #20;

        $display("========================================");
        $display("ALU Testbench");
        $display("========================================");
        $display("");

        //======================================================================
        // Test ADD
        //======================================================================
        $display("Testing ADD operations:");
        test_alu(32'd10, 32'd20, `ALU_OP_ADD, 32'd30, "ADD: 10 + 20 = 30");
        test_alu(32'd0, 32'd0, `ALU_OP_ADD, 32'd0, "ADD: 0 + 0 = 0");
        test_alu(32'hFFFFFFFF, 32'd1, `ALU_OP_ADD, 32'd0, "ADD: -1 + 1 = 0 (overflow)");
        test_alu(32'd100, 32'd50, `ALU_OP_ADD, 32'd150, "ADD: 100 + 50 = 150");

        //======================================================================
        // Test SUB
        //======================================================================
        $display("");
        $display("Testing SUB operations:");
        test_alu(32'd30, 32'd10, `ALU_OP_SUB, 32'd20, "SUB: 30 - 10 = 20");
        test_alu(32'd10, 32'd10, `ALU_OP_SUB, 32'd0, "SUB: 10 - 10 = 0");
        test_alu(32'd0, 32'd1, `ALU_OP_SUB, 32'hFFFFFFFF, "SUB: 0 - 1 = -1");
        test_alu(32'd100, 32'd150, `ALU_OP_SUB, 32'hFFFFFFCE, "SUB: 100 - 150 = -50");

        //======================================================================
        // Test AND
        //======================================================================
        $display("");
        $display("Testing AND operations:");
        test_alu(32'hFF, 32'h0F, `ALU_OP_AND, 32'h0F, "AND: 0xFF & 0x0F = 0x0F");
        test_alu(32'hAAAAAAAA, 32'h55555555, `ALU_OP_AND, 32'h00000000, "AND: 0xAAAAAAAA & 0x55555555 = 0");
        test_alu(32'hFFFFFFFF, 32'hFFFFFFFF, `ALU_OP_AND, 32'hFFFFFFFF, "AND: 0xFFFFFFFF & 0xFFFFFFFF = 0xFFFFFFFF");

        //======================================================================
        // Test OR
        //======================================================================
        $display("");
        $display("Testing OR operations:");
        test_alu(32'hF0, 32'h0F, `ALU_OP_OR, 32'hFF, "OR: 0xF0 | 0x0F = 0xFF");
        test_alu(32'hAAAAAAAA, 32'h55555555, `ALU_OP_OR, 32'hFFFFFFFF, "OR: 0xAAAAAAAA | 0x55555555 = 0xFFFFFFFF");
        test_alu(32'h00000000, 32'h00000000, `ALU_OP_OR, 32'h00000000, "OR: 0 | 0 = 0");

        //======================================================================
        // Test XOR
        //======================================================================
        $display("");
        $display("Testing XOR operations:");
        test_alu(32'hFF, 32'h0F, `ALU_OP_XOR, 32'hF0, "XOR: 0xFF ^ 0x0F = 0xF0");
        test_alu(32'hAAAAAAAA, 32'hAAAAAAAA, `ALU_OP_XOR, 32'h00000000, "XOR: 0xAAAAAAAA ^ 0xAAAAAAAA = 0");
        test_alu(32'hAAAAAAAA, 32'h55555555, `ALU_OP_XOR, 32'hFFFFFFFF, "XOR: 0xAAAAAAAA ^ 0x55555555 = 0xFFFFFFFF");

        //======================================================================
        // Test SLL (Shift Left Logical)
        //======================================================================
        $display("");
        $display("Testing SLL operations:");
        test_alu(32'd1, 32'd5, `ALU_OP_SLL, 32'd32, "SLL: 1 << 5 = 32");
        test_alu(32'd1, 32'd0, `ALU_OP_SLL, 32'd1, "SLL: 1 << 0 = 1");
        test_alu(32'd1, 32'd31, `ALU_OP_SLL, 32'h80000000, "SLL: 1 << 31 = 0x80000000");
        test_alu(32'hF, 32'd4, `ALU_OP_SLL, 32'hF0, "SLL: 0xF << 4 = 0xF0");

        //======================================================================
        // Test SRL (Shift Right Logical)
        //======================================================================
        $display("");
        $display("Testing SRL operations:");
        test_alu(32'd32, 32'd2, `ALU_OP_SRL, 32'd8, "SRL: 32 >> 2 = 8");
        test_alu(32'h80000000, 32'd1, `ALU_OP_SRL, 32'h40000000, "SRL: 0x80000000 >> 1 = 0x40000000");
        test_alu(32'hFFFFFFFF, 32'd4, `ALU_OP_SRL, 32'h0FFFFFFF, "SRL: 0xFFFFFFFF >> 4 = 0x0FFFFFFF");
        test_alu(32'd100, 32'd0, `ALU_OP_SRL, 32'd100, "SRL: 100 >> 0 = 100");

        //======================================================================
        // Test SRA (Shift Right Arithmetic - sign extension)
        //======================================================================
        $display("");
        $display("Testing SRA operations:");
        test_alu(32'd32, 32'd2, `ALU_OP_SRA, 32'd8, "SRA: 32 >>> 2 = 8");
        test_alu(32'hFFFFFFE0, 32'd2, `ALU_OP_SRA, 32'hFFFFFFF8, "SRA: -32 >>> 2 = -8 (sign extended)");
        test_alu(32'h80000000, 32'd1, `ALU_OP_SRA, 32'hC0000000, "SRA: 0x80000000 >>> 1 = 0xC0000000");
        test_alu(32'h7FFFFFFF, 32'd4, `ALU_OP_SRA, 32'h07FFFFFF, "SRA: 0x7FFFFFFF >>> 4 = 0x07FFFFFF");

        //======================================================================
        // Test SLT (Set Less Than - signed)
        //======================================================================
        $display("");
        $display("Testing SLT operations:");
        test_alu(32'hFFFFFFFB, 32'd10, `ALU_OP_SLT, 32'd1, "SLT: -5 < 10 = 1 (signed)");
        test_alu(32'd10, 32'hFFFFFFFB, `ALU_OP_SLT, 32'd0, "SLT: 10 < -5 = 0 (signed)");
        test_alu(32'd5, 32'd10, `ALU_OP_SLT, 32'd1, "SLT: 5 < 10 = 1");
        test_alu(32'd10, 32'd5, `ALU_OP_SLT, 32'd0, "SLT: 10 < 5 = 0");
        test_alu(32'd10, 32'd10, `ALU_OP_SLT, 32'd0, "SLT: 10 < 10 = 0");

        //======================================================================
        // Test SLTU (Set Less Than Unsigned)
        //======================================================================
        $display("");
        $display("Testing SLTU operations:");
        test_alu(32'hFFFFFFFF, 32'd10, `ALU_OP_SLTU, 32'd0, "SLTU: 0xFFFFFFFF < 10 = 0 (unsigned)");
        test_alu(32'd10, 32'hFFFFFFFF, `ALU_OP_SLTU, 32'd1, "SLTU: 10 < 0xFFFFFFFF = 1 (unsigned)");
        test_alu(32'd5, 32'd10, `ALU_OP_SLTU, 32'd1, "SLTU: 5 < 10 = 1");
        test_alu(32'd10, 32'd5, `ALU_OP_SLTU, 32'd0, "SLTU: 10 < 5 = 0");

        //======================================================================
        // Test Zero Flag
        //======================================================================
        $display("");
        $display("Testing zero flag:");
        operand_a = 10;
        operand_b = 10;
        alu_op = `ALU_OP_SUB;
        #10;
        tests = tests + 1;
        if (zero !== 1'b1) begin
            $display("  FAIL: Zero flag should be 1 when result is 0");
            errors = errors + 1;
        end else begin
            $display("  PASS: Zero flag = 1 when result = 0");
        end

        operand_a = 10;
        operand_b = 5;
        alu_op = `ALU_OP_SUB;
        #10;
        tests = tests + 1;
        if (zero !== 1'b0) begin
            $display("  FAIL: Zero flag should be 0 when result is non-zero");
            errors = errors + 1;
        end else begin
            $display("  PASS: Zero flag = 0 when result != 0");
        end

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
            $display("ALU is working correctly!");
            $display("You can now proceed to implement the decoder.");
        end else begin
            $display("");
            $display("*** %0d TESTS FAILED ***", errors);
            $display("");
            $display("Fix the ALU implementation:");
            $display("  1. Check each operation case");
            $display("  2. Pay attention to signed vs unsigned");
            $display("  3. Remember to use only lower 5 bits for shift amount");
            $display("  4. Re-run: make sim-alu");
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
