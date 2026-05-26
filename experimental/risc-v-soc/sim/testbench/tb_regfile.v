/**
 * @file tb_regfile.v
 * @brief Testbench for RISC-V Register File
 *
 * Tests:
 * - Write and read operations
 * - x0 hardwired to 0
 * - Simultaneous read/write
 * - All registers
 *
 * @author Custom RISC-V Core Team
 * @date 2025-12-03
 */

`timescale 1ns / 1ps

module tb_regfile;

    //==========================================================================
    // Signals
    //==========================================================================

    reg         clk;
    reg         rst_n;
    reg  [4:0]  rs1_addr;
    wire [31:0] rs1_data;
    reg  [4:0]  rs2_addr;
    wire [31:0] rs2_data;
    reg  [4:0]  rd_addr;
    reg  [31:0] rd_data;
    reg         rd_wen;

    // Test status
    integer errors = 0;
    integer tests = 0;

    //==========================================================================
    // DUT Instantiation
    //==========================================================================

    regfile dut (
        .clk(clk),
        .rst_n(rst_n),
        .rs1_addr(rs1_addr),
        .rs1_data(rs1_data),
        .rs2_addr(rs2_addr),
        .rs2_data(rs2_data),
        .rd_addr(rd_addr),
        .rd_data(rd_data),
        .rd_wen(rd_wen)
    );

    //==========================================================================
    // Clock Generation
    //==========================================================================

    initial begin
        clk = 0;
        forever #5 clk = ~clk;  // 100 MHz clock (10ns period)
    end

    //==========================================================================
    // Test Stimulus
    //==========================================================================

    initial begin
        // Initialize waveform dump
        $dumpfile("build/regfile.vcd");
        $dumpvars(0, tb_regfile);

        // Initialize signals
        rst_n = 0;
        rs1_addr = 0;
        rs2_addr = 0;
        rd_addr = 0;
        rd_data = 0;
        rd_wen = 0;

        // Reset
        #20;
        rst_n = 1;
        #10;

        $display("========================================");
        $display("Register File Testbench");
        $display("========================================");
        $display("");

        //======================================================================
        // Test 1: Write and read single register
        //======================================================================
        $display("Test 1: Write and read x5");
        @(negedge clk);  // Wait for negedge to set up signals
        rd_addr = 5;
        rd_data = 32'hDEADBEEF;
        rd_wen = 1;
        @(posedge clk);  // Write happens here
        @(negedge clk);
        rd_wen = 0;
        @(posedge clk);

        rs1_addr = 5;
        #1;  // Wait for combinational read

        tests = tests + 1;
        if (rs1_data !== 32'hDEADBEEF) begin
            $display("  FAIL: Expected 0xDEADBEEF, got 0x%h", rs1_data);
            errors = errors + 1;
        end else begin
            $display("  PASS: Read correct value 0x%h", rs1_data);
        end

        //======================================================================
        // Test 2: x0 always reads as 0
        //======================================================================
        $display("");
        $display("Test 2: x0 hardwired to 0 (read)");
        rs1_addr = 0;
        #1;

        tests = tests + 1;
        if (rs1_data !== 32'h0) begin
            $display("  FAIL: x0 should be 0, got 0x%h", rs1_data);
            errors = errors + 1;
        end else begin
            $display("  PASS: x0 reads as 0");
        end

        //======================================================================
        // Test 3: Writes to x0 are ignored
        //======================================================================
        $display("");
        $display("Test 3: x0 hardwired to 0 (write ignored)");
        @(negedge clk);  // Set up signals at negedge
        rd_addr = 0;
        rd_data = 32'hBADBADBA;
        rd_wen = 1;
        @(posedge clk);  // Write attempt (should be ignored)
        @(negedge clk);
        rd_wen = 0;
        @(posedge clk);

        rs1_addr = 0;
        #1;

        tests = tests + 1;
        if (rs1_data !== 32'h0) begin
            $display("  FAIL: x0 should remain 0, got 0x%h", rs1_data);
            errors = errors + 1;
        end else begin
            $display("  PASS: Write to x0 ignored");
        end

        //======================================================================
        // Test 4: Write and read multiple registers
        //======================================================================
        $display("");
        $display("Test 4: Write and read multiple registers");

        // Write x1 = 0x11111111
        @(negedge clk);  // Set up signals at negedge
        rd_addr = 1;
        rd_data = 32'h11111111;
        rd_wen = 1;
        @(posedge clk);  // Write happens here

        // Write x2 = 0x22222222
        @(negedge clk);  // Wait for negedge before changing signals!
        rd_addr = 2;
        rd_data = 32'h22222222;
        @(posedge clk);

        // Write x31 = 0xFFFFFFFF
        @(negedge clk);  // Wait for negedge before changing signals!
        rd_addr = 31;
        rd_data = 32'hFFFFFFFF;
        @(posedge clk);

        @(negedge clk);  // Wait for negedge before disabling write!
        rd_wen = 0;
        @(posedge clk);

        // Read x1
        rs1_addr = 1;
        #1;
        tests = tests + 1;
        if (rs1_data !== 32'h11111111) begin
            $display("  FAIL: x1 expected 0x11111111, got 0x%h", rs1_data);
            errors = errors + 1;
        end else begin
            $display("  PASS: x1 = 0x%h", rs1_data);
        end

        // Read x2
        rs1_addr = 2;
        #1;
        tests = tests + 1;
        if (rs1_data !== 32'h22222222) begin
            $display("  FAIL: x2 expected 0x22222222, got 0x%h", rs1_data);
            errors = errors + 1;
        end else begin
            $display("  PASS: x2 = 0x%h", rs1_data);
        end

        // Read x31
        rs1_addr = 31;
        #1;
        tests = tests + 1;
        if (rs1_data !== 32'hFFFFFFFF) begin
            $display("  FAIL: x31 expected 0xFFFFFFFF, got 0x%h", rs1_data);
            errors = errors + 1;
        end else begin
            $display("  PASS: x31 = 0x%h", rs1_data);
        end

        //======================================================================
        // Test 5: Simultaneous dual-port read
        //======================================================================
        $display("");
        $display("Test 5: Dual-port read (rs1 and rs2)");
        rs1_addr = 1;
        rs2_addr = 2;
        #1;

        tests = tests + 1;
        if (rs1_data !== 32'h11111111 || rs2_data !== 32'h22222222) begin
            $display("  FAIL: rs1=0x%h (expected 0x11111111), rs2=0x%h (expected 0x22222222)",
                     rs1_data, rs2_data);
            errors = errors + 1;
        end else begin
            $display("  PASS: rs1=0x%h, rs2=0x%h", rs1_data, rs2_data);
        end

        //======================================================================
        // Test 6: Write and read same register (forwarding test)
        //======================================================================
        $display("");
        $display("Test 6: Simultaneous write and read");
        @(negedge clk);  // Set up signals at negedge
        rd_addr = 10;
        rd_data = 32'h12345678;
        rd_wen = 1;
        rs1_addr = 10;
        @(posedge clk);  // Write happens here
        #1;  // Wait for read

        tests = tests + 1;
        if (rs1_data !== 32'h12345678) begin
            $display("  FAIL: Expected 0x12345678, got 0x%h", rs1_data);
            errors = errors + 1;
        end else begin
            $display("  PASS: Write and read x10 = 0x%h", rs1_data);
        end

        rd_wen = 0;

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
            $display("Register file is working correctly!");
            $display("You can now proceed to implement the ALU.");
        end else begin
            $display("");
            $display("*** %0d TESTS FAILED ***", errors);
            $display("");
            $display("Fix the register file implementation:");
            $display("  1. Check write logic (rd_wen && rd_addr != 0)");
            $display("  2. Check read logic (x0 handling)");
            $display("  3. Re-run: make sim-regfile");
        end
        $display("========================================");

        $finish;
    end

    //==========================================================================
    // Timeout watchdog
    //==========================================================================

    initial begin
        #10000;
        $display("ERROR: Testbench timeout!");
        $finish;
    end

endmodule
