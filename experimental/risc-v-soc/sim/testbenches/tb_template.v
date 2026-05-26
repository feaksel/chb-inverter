/**
 * @file tb_template.v
 * @brief Template Testbench for RISC-V Modules
 *
 * This is a template testbench that can be copied and modified
 * for testing individual RISC-V modules.
 *
 * Usage:
 * 1. Copy this file to tb_<module_name>.v
 * 2. Modify MODULE_NAME and instantiate your module
 * 3. Add test vectors and assertions
 * 4. Run with: make test MODULE=<module_name>
 *
 * @author Custom RISC-V Core Project
 * @date 2025-12-03
 */

`timescale 1ns/1ps

module tb_template;

    //==========================================================================
    // Parameters
    //==========================================================================

    parameter CLK_PERIOD = 20;  // 50 MHz clock (20 ns period)

    //==========================================================================
    // Signals
    //==========================================================================

    // Clock and reset
    reg clk;
    reg rst_n;

    // Test status
    integer test_count;
    integer pass_count;
    integer fail_count;

    //==========================================================================
    // Clock Generation
    //==========================================================================

    initial begin
        clk = 0;
        forever #(CLK_PERIOD/2) clk = ~clk;
    end

    //==========================================================================
    // Module Under Test (DUT) Instantiation
    //==========================================================================

    // TODO: Instantiate your module here
    // Example:
    // my_module #(
    //     .PARAM1(value1),
    //     .PARAM2(value2)
    // ) dut (
    //     .clk(clk),
    //     .rst_n(rst_n),
    //     // ... other signals
    // );

    //==========================================================================
    // Test Utilities
    //==========================================================================

    // Check result and update counters
    task check_result;
        input [31:0] expected;
        input [31:0] actual;
        input [255:0] test_name;
        begin
            test_count = test_count + 1;
            if (expected === actual) begin
                $display("[PASS] Test %0d: %s", test_count, test_name);
                pass_count = pass_count + 1;
            end else begin
                $display("[FAIL] Test %0d: %s", test_count, test_name);
                $display("       Expected: 0x%08h, Got: 0x%08h", expected, actual);
                fail_count = fail_count + 1;
            end
        end
    endtask

    // Print test summary
    task print_summary;
        begin
            $display("\n========================================");
            $display("Test Summary");
            $display("========================================");
            $display("Total Tests: %0d", test_count);
            $display("Passed:      %0d", pass_count);
            $display("Failed:      %0d", fail_count);
            $display("Success Rate: %0d%%", (pass_count * 100) / test_count);
            $display("========================================\n");

            if (fail_count == 0) begin
                $display("✓ ALL TESTS PASSED");
            end else begin
                $display("✗ SOME TESTS FAILED");
            end
        end
    endtask

    //==========================================================================
    // Test Sequence
    //==========================================================================

    initial begin
        // Initialize counters
        test_count = 0;
        pass_count = 0;
        fail_count = 0;

        // Initialize signals
        rst_n = 0;

        // Dump waveforms for viewing in GTKWave
        $dumpfile("tb_template.vcd");
        $dumpvars(0, tb_template);

        $display("\n========================================");
        $display("Starting testbench: tb_template");
        $display("========================================\n");

        // Reset sequence
        #(CLK_PERIOD * 2);
        rst_n = 1;
        #(CLK_PERIOD);

        //======================================================================
        // Test Cases
        //======================================================================

        // TODO: Add your test cases here

        // Test 1: Example test
        $display("\n--- Test 1: Example Test ---");
        // ... test stimulus ...
        #(CLK_PERIOD);
        // ... check results ...
        // check_result(expected_value, actual_value, "Test description");

        // Test 2: Another example
        $display("\n--- Test 2: Another Test ---");
        // ... test stimulus ...
        #(CLK_PERIOD);
        // ... check results ...

        // Add more test cases as needed

        //======================================================================
        // Test Completion
        //======================================================================

        #(CLK_PERIOD * 10);  // Allow some settling time

        print_summary();

        if (fail_count == 0) begin
            $finish(0);  // Success
        end else begin
            $finish(1);  // Failure
        end
    end

    //==========================================================================
    // Timeout Watchdog
    //==========================================================================

    initial begin
        #(CLK_PERIOD * 100000);  // 100,000 cycles timeout
        $display("\n[ERROR] Testbench timeout!");
        $display("Simulation ran for too long without completing.");
        $finish(2);
    end

    //==========================================================================
    // Signal Monitoring (Optional)
    //==========================================================================

    // Uncomment to monitor signals during simulation
    // initial begin
    //     $monitor("Time=%0t clk=%b rst_n=%b ...", $time, clk, rst_n, ...);
    // end

endmodule
