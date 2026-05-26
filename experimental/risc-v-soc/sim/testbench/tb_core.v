/**
 * @file tb_core.v
 * @brief Testbench for Custom RISC-V Core
 *
 * Tests the complete core with a simple program that executes:
 * - Arithmetic operations (ADDI, ADD, SUB)
 * - Load/Store operations (LW, SW)
 * - Branch operations (BEQ, BNE)
 * - Jump operations (JAL)
 *
 * @author Custom RISC-V Core Team
 * @date 2025-12-08
 */

`timescale 1ns / 1ps

module tb_core;

    //==========================================================================
    // Clock and Reset
    //==========================================================================

    reg clk;
    reg rst_n;

    // 50 MHz clock (20ns period)
    initial begin
        clk = 0;
        forever #10 clk = ~clk;
    end

    //==========================================================================
    // Core Signals
    //==========================================================================

    wire [31:0] iwb_adr_o;
    wire [31:0] iwb_dat_i;
    wire        iwb_cyc_o;
    wire        iwb_stb_o;
    wire        iwb_ack_i;

    wire [31:0] dwb_adr_o;
    wire [31:0] dwb_dat_o;
    wire [31:0] dwb_dat_i;
    wire        dwb_we_o;
    wire [3:0]  dwb_sel_o;
    wire        dwb_cyc_o;
    wire        dwb_stb_o;
    wire        dwb_ack_i;
    wire        dwb_err_i;

    wire [31:0] interrupts;
    assign interrupts = 32'h0;  // No interrupts for now

    //==========================================================================
    // DUT - Device Under Test
    //==========================================================================

    custom_riscv_core #(
        .RESET_VECTOR(32'h00000000)
    ) dut (
        .clk(clk),
        .rst_n(rst_n),

        // Instruction bus
        .iwb_adr_o(iwb_adr_o),
        .iwb_dat_i(iwb_dat_i),
        .iwb_cyc_o(iwb_cyc_o),
        .iwb_stb_o(iwb_stb_o),
        .iwb_ack_i(iwb_ack_i),

        // Data bus
        .dwb_adr_o(dwb_adr_o),
        .dwb_dat_o(dwb_dat_o),
        .dwb_dat_i(dwb_dat_i),
        .dwb_we_o(dwb_we_o),
        .dwb_sel_o(dwb_sel_o),
        .dwb_cyc_o(dwb_cyc_o),
        .dwb_stb_o(dwb_stb_o),
        .dwb_ack_i(dwb_ack_i),
        .dwb_err_i(dwb_err_i),

        // Interrupts
        .interrupts(interrupts)
    );

    //==========================================================================
    // Simple Wishbone Memory Module
    //==========================================================================

    // Instruction memory (1KB = 256 words)
    reg [31:0] imem [0:255];
    reg        imem_ack;

    // Data memory (1KB = 256 words)
    reg [31:0] dmem [0:255];
    reg        dmem_ack;

    // Instruction memory Wishbone slave
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            imem_ack <= 1'b0;
        end else begin
            if (iwb_cyc_o && iwb_stb_o && !imem_ack) begin
                imem_ack <= 1'b1;
            end else begin
                imem_ack <= 1'b0;
            end
        end
    end

    assign iwb_dat_i = (iwb_adr_o[31:2] < 256) ? imem[iwb_adr_o[31:2]] : 32'h00000013; // NOP
    assign iwb_ack_i = imem_ack;

    // Data memory Wishbone slave
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            dmem_ack <= 1'b0;
        end else begin
            if (dwb_cyc_o && dwb_stb_o && !dmem_ack) begin
                dmem_ack <= 1'b1;

                // Write to memory
                if (dwb_we_o && dwb_adr_o[31:2] < 256) begin
                    // Byte-select write
                    if (dwb_sel_o[0]) dmem[dwb_adr_o[31:2]][7:0]   <= dwb_dat_o[7:0];
                    if (dwb_sel_o[1]) dmem[dwb_adr_o[31:2]][15:8]  <= dwb_dat_o[15:8];
                    if (dwb_sel_o[2]) dmem[dwb_adr_o[31:2]][23:16] <= dwb_dat_o[23:16];
                    if (dwb_sel_o[3]) dmem[dwb_adr_o[31:2]][31:24] <= dwb_dat_o[31:24];
                end
            end else begin
                dmem_ack <= 1'b0;
            end
        end
    end

    assign dwb_dat_i = (dwb_adr_o[31:2] < 256) ? dmem[dwb_adr_o[31:2]] : 32'h00000000;
    assign dwb_ack_i = dmem_ack;
    assign dwb_err_i = 1'b0;  // No errors

    //==========================================================================
    // Test Program
    //==========================================================================

    /*
     * Simple test program:
     *
     * 0x00: addi x1, x0, 10      # x1 = 10
     * 0x04: addi x2, x0, 20      # x2 = 20
     * 0x08: add  x3, x1, x2      # x3 = x1 + x2 = 30
     * 0x0C: sub  x4, x3, x1      # x4 = x3 - x1 = 20
     * 0x10: sw   x4, 0(x0)       # Store x4 to address 0
     * 0x14: lw   x5, 0(x0)       # Load from address 0 to x5 (should be 20)
     * 0x18: beq  x0, x0, 8       # Jump forward 8 bytes (to 0x20)
     * 0x1C: addi x6, x0, 99      # Should be skipped
     * 0x20: addi x7, x0, 100     # x7 = 100 (after branch)
     * 0x24: j    end             # Jump to end
     * 0x28: end: (infinite loop or finish)
     */

    initial begin
        // Initialize instruction memory
        imem[0]  = 32'h00A00093;  // addi x1, x0, 10
        imem[1]  = 32'h01400113;  // addi x2, x0, 20
        imem[2]  = 32'h002081B3;  // add  x3, x1, x2
        imem[3]  = 32'h40118233;  // sub  x4, x3, x1
        imem[4]  = 32'h00402023;  // sw   x4, 0(x0)
        imem[5]  = 32'h00002283;  // lw   x5, 0(x0)
        imem[6]  = 32'h00000463;  // beq  x0, x0, 8
        imem[7]  = 32'h06300313;  // addi x6, x0, 99 (skipped)
        imem[8]  = 32'h06400393;  // addi x7, x0, 100
        imem[9]  = 32'h0000006F;  // jal  x0, 0 (infinite loop)

        // Fill rest with NOPs
        for (integer i = 10; i < 256; i = i + 1) begin
            imem[i] = 32'h00000013;  // ADDI x0, x0, 0 (NOP)
        end

        // Initialize data memory to zeros
        for (integer i = 0; i < 256; i = i + 1) begin
            dmem[i] = 32'h00000000;
        end
    end

    //==========================================================================
    // Test Control
    //==========================================================================

    integer cycle_count;
    integer instruction_count;
    reg [31:0] prev_pc;

    initial begin
        // Initialize VCD dump
        $dumpfile("build/core.vcd");
        $dumpvars(0, tb_core);

        // Initialize
        rst_n = 0;
        cycle_count = 0;
        instruction_count = 0;
        prev_pc = 32'hFFFFFFFF;

        // Reset
        #50;
        rst_n = 1;

        $display("");
        $display("========================================");
        $display("RISC-V Core Testbench");
        $display("========================================");
        $display("");
        $display("Starting execution...");
        $display("");

        // Run for a limited time
        #5000;

        // Display results
        $display("");
        $display("========================================");
        $display("Execution Complete");
        $display("========================================");
        $display("Cycles executed: %0d", cycle_count);
        $display("Instructions completed: %0d", instruction_count);
        $display("");

        // Check register values through register file
        $display("Register File Contents:");
        $display("  x1 = 0x%h (expected: 10 = 0x0000000a)", dut.regfile_inst.registers[1]);
        $display("  x2 = 0x%h (expected: 20 = 0x00000014)", dut.regfile_inst.registers[2]);
        $display("  x3 = 0x%h (expected: 30 = 0x0000001e)", dut.regfile_inst.registers[3]);
        $display("  x4 = 0x%h (expected: 20 = 0x00000014)", dut.regfile_inst.registers[4]);
        $display("  x5 = 0x%h (expected: 20 = 0x00000014)", dut.regfile_inst.registers[5]);
        $display("  x6 = 0x%h (expected: 0  = 0x00000000 - skipped)", dut.regfile_inst.registers[6]);
        $display("  x7 = 0x%h (expected: 100 = 0x00000064)", dut.regfile_inst.registers[7]);
        $display("");

        // Check memory
        $display("Data Memory Contents:");
        $display("  dmem[0] = 0x%h (expected: 20 = 0x00000014)", dmem[0]);
        $display("");

        // Verify results
        if (dut.regfile_inst.registers[1] === 32'd10 &&
            dut.regfile_inst.registers[2] === 32'd20 &&
            dut.regfile_inst.registers[3] === 32'd30 &&
            dut.regfile_inst.registers[4] === 32'd20 &&
            dut.regfile_inst.registers[5] === 32'd20 &&
            dut.regfile_inst.registers[6] === 32'd0 &&
            dut.regfile_inst.registers[7] === 32'd100 &&
            dmem[0] === 32'd20) begin
            $display("*** ALL TESTS PASSED! ***");
            $display("");
            $display("Core is executing instructions correctly!");
        end else begin
            $display("*** TESTS FAILED ***");
            $display("");
            $display("Register values do not match expected!");
        end

        $display("========================================");
        $display("");

        $finish;
    end

    // Cycle counter
    always @(posedge clk) begin
        if (rst_n) begin
            cycle_count <= cycle_count + 1;
        end
    end

    // Instruction monitor
    always @(posedge clk) begin
        if (rst_n && dut.state == 3'd0) begin  // STATE_FETCH
            if (dut.pc !== prev_pc) begin
                instruction_count <= instruction_count + 1;
                $display("[Cycle %0d] PC=0x%h, Instr=0x%h",
                         cycle_count, dut.pc, imem[dut.pc[31:2]]);
                prev_pc <= dut.pc;
            end
        end
    end

    // Timeout watchdog
    initial begin
        #50000;
        $display("");
        $display("ERROR: Simulation timeout after 50000ns!");
        $display("Core may be stuck in a loop or stalled.");
        $display("");
        $finish;
    end

endmodule
