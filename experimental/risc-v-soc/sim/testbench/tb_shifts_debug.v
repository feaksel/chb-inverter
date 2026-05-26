/**
 * @file tb_shifts_debug.v
 * @brief Focused testbench to debug R-type shift operations
 *
 * Tests only SLL and SRL with detailed logging
 */

`timescale 1ns / 1ps

module tb_shifts_debug;

    reg clk;
    reg rst_n;

    initial begin
        clk = 0;
        forever #10 clk = ~clk;
    end

    wire [31:0] iwb_adr_o, iwb_dat_i, dwb_adr_o, dwb_dat_o, dwb_dat_i;
    wire iwb_cyc_o, iwb_stb_o, iwb_ack_i;
    wire dwb_we_o, dwb_cyc_o, dwb_stb_o, dwb_ack_i, dwb_err_i;
    wire [3:0] dwb_sel_o;
    wire [31:0] interrupts;
    assign interrupts = 32'h0;

    custom_riscv_core #(
        .RESET_VECTOR(32'h00000000)
    ) dut (
        .clk(clk),
        .rst_n(rst_n),
        .iwb_adr_o(iwb_adr_o),
        .iwb_dat_i(iwb_dat_i),
        .iwb_cyc_o(iwb_cyc_o),
        .iwb_stb_o(iwb_stb_o),
        .iwb_ack_i(iwb_ack_i),
        .dwb_adr_o(dwb_adr_o),
        .dwb_dat_o(dwb_dat_o),
        .dwb_dat_i(dwb_dat_i),
        .dwb_we_o(dwb_we_o),
        .dwb_sel_o(dwb_sel_o),
        .dwb_cyc_o(dwb_cyc_o),
        .dwb_stb_o(dwb_stb_o),
        .dwb_ack_i(dwb_ack_i),
        .dwb_err_i(dwb_err_i),
        .interrupts(interrupts)
    );

    reg [31:0] imem [0:255];
    reg        imem_ack;
    reg [31:0] dmem [0:255];
    reg        dmem_ack;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            imem_ack <= 1'b0;
        end else begin
            imem_ack <= (iwb_cyc_o && iwb_stb_o && !imem_ack) ? 1'b1 : 1'b0;
        end
    end

    assign iwb_dat_i = (iwb_adr_o[31:2] < 256) ? imem[iwb_adr_o[31:2]] : 32'h00000013;
    assign iwb_ack_i = imem_ack;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            dmem_ack <= 1'b0;
        end else begin
            if (dwb_cyc_o && dwb_stb_o && !dmem_ack) begin
                dmem_ack <= 1'b1;
                if (dwb_we_o && dwb_adr_o[31:2] < 256) begin
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
    assign dwb_err_i = 1'b0;

    integer init_i;

    initial begin
        // Simple shift test program
        imem[0]  = 32'h00800093;  // addi x1, x0, 8       -> x1 = 8 (shift amount)
        imem[1]  = 32'h00400113;  // addi x2, x0, 4       -> x2 = 4 (value to shift)

        // R-type SLL (correct encoding: opcode = 0110011)
        imem[2]  = 32'h001091B3;  // sll x3, x1, x1       -> x3 = 8 << 8 = 2048 = 0x800
        imem[3]  = 32'h00111233;  // sll x4, x2, x1       -> x4 = 4 << 8 = 1024 = 0x400

        // R-type SRL and SRA
        imem[4]  = 32'h0010D2B3;  // srl x5, x1, x1       -> x5 = 8 >> 8 = 0
        imem[5]  = 32'h40109333;  // sra x6, x1, x1       -> x6 = 8 >>> 8 = 0 (arithmetic)

        // Infinite loop
        imem[6]  = 32'h0000006F;  // jal x0, 0

        for (init_i = 7; init_i < 256; init_i = init_i + 1) begin
            imem[init_i] = 32'h00000013;
        end

        for (init_i = 0; init_i < 256; init_i = init_i + 1) begin
            dmem[init_i] = 32'h00000000;
        end
    end

    // Detailed state monitoring
    always @(posedge clk) begin
        if (rst_n && dut.state == 3'd1) begin  // DECODE state
            $display("[DECODE] instr=0x%h, rs1_addr=%0d, rs2_addr=%0d, rd_addr=%0d, alu_src_imm=%b, imm=0x%h",
                     dut.instruction, dut.rs1_addr, dut.rs2_addr, dut.rd_addr,
                     dut.alu_src_imm, dut.immediate);
            $display("         rs1_data=0x%h, rs2_data=0x%h",
                     dut.rs1_data, dut.rs2_data);
        end
        if (rst_n && dut.state == 3'd2) begin  // EXECUTE state
            $display("[EXECUTE] PC=0x%h, ALU_op=%d, op_a=0x%h, op_b=0x%h, result=0x%h",
                     dut.pc, dut.alu_op, dut.alu_operand_a, dut.alu_operand_b, dut.alu_result);
        end
        if (rst_n && dut.state == 3'd4 && dut.rd_wen) begin  // WRITEBACK with reg write
            $display("[WRITEBACK] Writing x%0d = 0x%h",
                     dut.rd_addr, dut.rd_data);
        end
    end

    initial begin
        $dumpfile("build/shifts_debug.vcd");
        $dumpvars(0, tb_shifts_debug);

        rst_n = 0;
        #50;
        rst_n = 1;

        $display("");
        $display("========================================");
        $display("R-Type Shift Debug Testbench");
        $display("========================================");
        $display("");

        #2000;

        $display("");
        $display("========================================");
        $display("Final Register Values");
        $display("========================================");
        $display("x1 = 0x%h (expected: 0x00000008)", dut.regfile_inst.registers[1]);
        $display("x2 = 0x%h (expected: 0x00000004)", dut.regfile_inst.registers[2]);
        $display("x3 = 0x%h (expected: 0x00000800 = 2048)", dut.regfile_inst.registers[3]);
        $display("x4 = 0x%h (expected: 0x00000400 = 1024)", dut.regfile_inst.registers[4]);
        $display("x5 = 0x%h (expected: 0x00000000)", dut.regfile_inst.registers[5]);
        $display("x6 = 0x%h (expected: 0x00000000)", dut.regfile_inst.registers[6]);
        $display("");

        if (dut.regfile_inst.registers[3] == 32'h00000800 &&
            dut.regfile_inst.registers[4] == 32'h00000400 &&
            dut.regfile_inst.registers[5] == 32'h00000000) begin
            $display("*** R-TYPE SHIFTS WORK CORRECTLY ***");
        end else begin
            $display("*** SHIFTS HAVE ISSUES ***");
            $display("Check the waveform and execution log above");
        end
        $display("========================================");

        $finish;
    end

    initial begin
        #10000;
        $display("ERROR: Timeout!");
        $finish;
    end

endmodule
