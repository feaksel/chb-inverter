`include "riscv_defines.vh"

module tb_mdu;
    reg clk, rst_n;
    reg start;
    reg [2:0] funct3;
    reg [31:0] a, b;
    
    wire busy, done;
    wire [63:0] product;
    wire [31:0] quotient, remainder;
    
    // Instantiate MDU
    mdu dut (
        .clk(clk),
        .rst_n(rst_n),
        .start(start),
        .funct3(funct3),
        .a(a),
        .b(b),
        .busy(busy),
        .done(done),
        .product(product),
        .quotient(quotient),
        .remainder(remainder)
    );
    
    // Clock generation
    initial begin
        clk = 0;
        forever #5 clk = ~clk;  // 10ns period (100MHz)
    end
    
    // Main test
    initial begin
        reg [63:0] res_prod;
        reg [31:0] res_quot, res_rem;
        integer timeout, i;
        
        $dumpfile("sim/build/tb_mdu.vcd");
        $dumpvars(0, tb_mdu);
        
        // Initialize
        rst_n = 0;
        start = 0;
        a = 0;
        b = 0;
        funct3 = 0;
        
        @(posedge clk);
        rst_n = 1;
        @(posedge clk);
        @(posedge clk);
        
        $display("\n==========================================");
        $display("MDU Test Suite - All M-Extension Operations");
        $display("==========================================\n");
        
        // ===== TEST 1: MUL =====
        $display("[TEST 1] MUL: a=12, b=10 (expected: 120)");
        funct3 = `FUNCT3_MUL;
        a = 32'd12;
        b = 32'd10;
        start = 1;
        @(posedge clk);
        start = 0;
        timeout = 0;
        while (!done && timeout < 1000) begin
            @(posedge clk);
            timeout = timeout + 1;
        end
        res_prod = product;
        if (res_prod[31:0] == 32'd120)
            $display("✓ PASS: 12 × 10 = 120\n");
        else
            $display("✗ FAIL: Got %d, expected 120\n", res_prod[31:0]);
        
        @(posedge clk);
        
        // ===== TEST 2: MUL large =====
        $display("[TEST 1b] MUL: a=1000, b=1000");
        funct3 = `FUNCT3_MUL;
        a = 32'd1000;
        b = 32'd1000;
        start = 1;
        @(posedge clk);
        start = 0;
        timeout = 0;
        while (!done && timeout < 1000) begin
            @(posedge clk);
            timeout = timeout + 1;
        end
        res_prod = product;
        if (res_prod[31:0] == 32'd1000000)
            $display("✓ PASS: 1000 × 1000 = 1000000\n");
        else
            $display("✗ FAIL: Got %d, expected 1000000\n", res_prod[31:0]);
        
        @(posedge clk);
        
        // ===== TEST 3: MULH =====
        $display("[TEST 2] MULH: a=-1 (0xFFFFFFFF), b=-1 (0xFFFFFFFF)");
        funct3 = `FUNCT3_MULH;
        a = 32'hFFFFFFFF;
        b = 32'hFFFFFFFF;
        start = 1;
        @(posedge clk);
        start = 0;
        timeout = 0;
        while (!done && timeout < 1000) begin
            @(posedge clk);
            timeout = timeout + 1;
        end
        res_prod = product;
        if (res_prod[63:32] == 32'd0)
            $display("✓ PASS: MULH(-1, -1) = 0\n");
        else
            $display("✗ FAIL: Got 0x%08X, expected 0\n", res_prod[63:32]);
        
        @(posedge clk);
        
        // ===== TEST 4: MULHU =====
        $display("[TEST 3] MULHU: a=0xFFFFFFFF, b=0xFFFFFFFF");
        funct3 = `FUNCT3_MULHU;
        a = 32'hFFFFFFFF;
        b = 32'hFFFFFFFF;
        start = 1;
        @(posedge clk);
        start = 0;
        timeout = 0;
        while (!done && timeout < 1000) begin
            @(posedge clk);
            timeout = timeout + 1;
        end
        res_prod = product;
        $display("   Result: 0x%016llX, upper=0x%08X, lower=0x%08X\n", 
                 res_prod, res_prod[63:32], res_prod[31:0]);
        
        @(posedge clk);
        
        // ===== TEST 4: DIV =====
        $display("[TEST 4] DIV: a=100, b=7 (expected quotient: 14)");
        funct3 = `FUNCT3_DIV;
        a = 32'd100;
        b = 32'd7;
        start = 1;
        @(posedge clk);
        start = 0;
        timeout = 0;
        while (!done && timeout < 1000) begin
            @(posedge clk);
            timeout = timeout + 1;
            if (timeout == 50) $display("   [After 50 cycles: busy=%b, done=%b]", dut.busy, dut.done);
        end
        // Capture on THIS cycle (when done is asserted)
        res_quot = quotient;
        $display("   [Timeout=%d, busy=%b, done=%b]", timeout, dut.busy, dut.done);
        if (res_quot == 32'd14)
            $display("✓ PASS: 100 ÷ 7 = 14\n");
        else
            $display("✗ FAIL: Got %d (0x%08X), expected 14\n", res_quot, res_quot);
        
        @(posedge clk);
        
        // ===== TEST 6: DIV by zero =====
        $display("[TEST 5] DIV: a=100, b=0 (expected quotient: -1)");
        funct3 = `FUNCT3_DIV;
        a = 32'd100;
        b = 32'd0;
        start = 1;
        @(posedge clk);
        start = 0;
        timeout = 0;
        while (!done && timeout < 1000) begin
            @(posedge clk);
            timeout = timeout + 1;
        end
        res_quot = quotient;
        if (res_quot == 32'hFFFFFFFF)
            $display("✓ PASS: Division by zero returns -1\n");
        else
            $display("✗ FAIL: Got 0x%08X, expected 0xFFFFFFFF\n", res_quot);
        
        @(posedge clk);
        
        // ===== TEST 7: DIVU =====
        $display("[TEST 6] DIVU: a=0x10000000, b=10");
        funct3 = `FUNCT3_DIVU;
        a = 32'h10000000;
        b = 32'd10;
        start = 1;
        @(posedge clk);
        start = 0;
        timeout = 0;
        while (!done && timeout < 1000) begin
            @(posedge clk);
            timeout = timeout + 1;
        end
        res_quot = quotient;
        $display("   Result: %d (0x%08X)\n", res_quot, res_quot);
        
        @(posedge clk);
        
        // ===== TEST 8: REM =====
        $display("[TEST 7] REM: a=100, b=7 (expected remainder: 2)");
        funct3 = `FUNCT3_REM;
        a = 32'd100;
        b = 32'd7;
        start = 1;
        @(posedge clk);
        start = 0;
        timeout = 0;
        while (!done && timeout < 1000) begin
            @(posedge clk);
            timeout = timeout + 1;
        end
        res_rem = remainder;
        if (res_rem == 32'd2)
            $display("✓ PASS: 100 %% 7 = 2\n");
        else
            $display("✗ FAIL: Got %d, expected 2\n", res_rem);
        
        @(posedge clk);
        
        // ===== TEST 9: REMU =====
        $display("[TEST 8] REMU: a=0xFFFFFFFF, b=10");
        funct3 = `FUNCT3_REMU;
        a = 32'hFFFFFFFF;
        b = 32'd10;
        start = 1;
        @(posedge clk);
        start = 0;
        timeout = 0;
        while (!done && timeout < 1000) begin
            @(posedge clk);
            timeout = timeout + 1;
        end
        res_rem = remainder;
        if (res_rem == 32'd5)
            $display("✓ PASS: 0xFFFFFFFF %% 10 = 5\n");
        else
            $display("✗ FAIL: Got %d, expected 5\n", res_rem);
        
        @(posedge clk);
        
        // ===== EDGE CASES =====
        $display("\n==========================================");
        $display("EDGE CASE TESTS");
        $display("==========================================\n");
        
        // ===== EDGE CASE 1: MUL with zero =====
        $display("[EDGE 1] MUL: a=0, b=1000");
        funct3 = `FUNCT3_MUL;
        a = 32'd0;
        b = 32'd1000;
        start = 1;
        @(posedge clk);
        start = 0;
        timeout = 0;
        while (!done && timeout < 1000) begin
            @(posedge clk);
            timeout = timeout + 1;
        end
        res_prod = product;
        if (res_prod == 64'd0)
            $display("✓ PASS: 0 × 1000 = 0\n");
        else
            $display("✗ FAIL: Got %d, expected 0\n", res_prod);
        
        @(posedge clk);
        
        // ===== EDGE CASE 2: MUL negative × positive =====
        $display("[EDGE 2] MUL: a=-5 (0xFFFFFFFB), b=3");
        funct3 = `FUNCT3_MUL;
        a = 32'hFFFFFFFB;  // -5
        b = 32'd3;
        start = 1;
        @(posedge clk);
        start = 0;
        timeout = 0;
        while (!done && timeout < 1000) begin
            @(posedge clk);
            timeout = timeout + 1;
        end
        res_prod = product;
        $display("   Result: 0x%016llX (lower 32b as signed: %d)\n", res_prod, $signed(res_prod[31:0]));
        if ($signed(res_prod[31:0]) == -32'd15)
            $display("✓ PASS: -5 × 3 = -15\n");
        else
            $display("✗ FAIL: Expected -15\n");
        
        @(posedge clk);
        
        // ===== EDGE CASE 3: MULH with zero =====
        $display("[EDGE 3] MULH: a=0, b=0xFFFFFFFF");
        funct3 = `FUNCT3_MULH;
        a = 32'd0;
        b = 32'hFFFFFFFF;
        start = 1;
        @(posedge clk);
        start = 0;
        timeout = 0;
        while (!done && timeout < 1000) begin
            @(posedge clk);
            timeout = timeout + 1;
        end
        res_prod = product;
        if (res_prod[63:32] == 32'd0)
            $display("✓ PASS: MULH(0, -1) upper = 0\n");
        else
            $display("✗ FAIL: Got 0x%08X, expected 0\n", res_prod[63:32]);
        
        @(posedge clk);
        
        // ===== EDGE CASE 4: MULHSU signed×unsigned =====
        $display("[EDGE 4] MULHSU: a=-1 (0xFFFFFFFF), b=2");
        funct3 = `FUNCT3_MULHSU;
        a = 32'hFFFFFFFF;  // -1
        b = 32'd2;
        start = 1;
        @(posedge clk);
        start = 0;
        timeout = 0;
        while (!done && timeout < 1000) begin
            @(posedge clk);
            timeout = timeout + 1;
        end
        res_prod = product;
        $display("   Result: upper=0x%08X, lower=0x%08X\n", res_prod[63:32], res_prod[31:0]);
        // -1 × 2 = -2 = 0xFFFFFFFFFFFFFFFE, so upper should be 0xFFFFFFFE
        if (res_prod[63:32] == 32'hFFFFFFFE)
            $display("✓ PASS: MULHSU(-1, 2) upper = 0xFFFFFFFE\n");
        else
            $display("✗ FAIL: Got 0x%08X, expected 0xFFFFFFFE\n", res_prod[63:32]);
        
        @(posedge clk);
        
        // ===== EDGE CASE 5: DIV max value =====
        $display("[EDGE 5] DIV: a=2147483647 (0x7FFFFFFF), b=1 (max int / 1)");
        funct3 = `FUNCT3_DIV;
        a = 32'h7FFFFFFF;  // max positive int32
        b = 32'd1;
        start = 1;
        @(posedge clk);
        start = 0;
        timeout = 0;
        while (!done && timeout < 1000) begin
            @(posedge clk);
            timeout = timeout + 1;
        end
        res_quot = quotient;
        if (res_quot == 32'h7FFFFFFF)
            $display("✓ PASS: 2147483647 ÷ 1 = 2147483647\n");
        else
            $display("✗ FAIL: Got 0x%08X, expected 0x7FFFFFFF\n", res_quot);
        
        @(posedge clk);
        
        // ===== EDGE CASE 6: DIV negative / negative =====
        $display("[EDGE 6] DIV: a=-100, b=-7 (both negative)");
        funct3 = `FUNCT3_DIV;
        a = 32'hFFFFFF9C;  // -100
        b = 32'hFFFFFFF9;  // -7
        start = 1;
        @(posedge clk);
        start = 0;
        timeout = 0;
        while (!done && timeout < 1000) begin
            @(posedge clk);
            timeout = timeout + 1;
        end
        res_quot = quotient;
        if (res_quot == 32'd14)
            $display("✓ PASS: -100 ÷ -7 = 14\n");
        else
            $display("✗ FAIL: Got %d, expected 14\n", $signed(res_quot));
        
        @(posedge clk);
        
        // ===== EDGE CASE 7: DIV negative / positive =====
        $display("[EDGE 7] DIV: a=-100, b=7");
        funct3 = `FUNCT3_DIV;
        a = 32'hFFFFFF9C;  // -100
        b = 32'd7;
        start = 1;
        @(posedge clk);
        start = 0;
        timeout = 0;
        while (!done && timeout < 1000) begin
            @(posedge clk);
            timeout = timeout + 1;
        end
        res_quot = quotient;
        if ($signed(res_quot) == -32'd14)
            $display("✓ PASS: -100 ÷ 7 = -14\n");
        else
            $display("✗ FAIL: Got %d, expected -14\n", $signed(res_quot));
        
        @(posedge clk);
        
        // ===== EDGE CASE 8: DIVU with large divisor =====
        $display("[EDGE 8] DIVU: a=0xFFFFFFFF, b=0x80000000");
        funct3 = `FUNCT3_DIVU;
        a = 32'hFFFFFFFF;
        b = 32'h80000000;
        start = 1;
        @(posedge clk);
        start = 0;
        timeout = 0;
        while (!done && timeout < 1000) begin
            @(posedge clk);
            timeout = timeout + 1;
        end
        res_quot = quotient;
        if (res_quot == 32'd1)
            $display("✓ PASS: 0xFFFFFFFF ÷ 0x80000000 = 1\n");
        else
            $display("✗ FAIL: Got %d, expected 1\n", res_quot);
        
        @(posedge clk);
        
        // ===== EDGE CASE 9: REM with dividend = divisor =====
        $display("[EDGE 9] REM: a=7, b=7 (dividend = divisor)");
        funct3 = `FUNCT3_REM;
        a = 32'd7;
        b = 32'd7;
        start = 1;
        @(posedge clk);
        start = 0;
        timeout = 0;
        while (!done && timeout < 1000) begin
            @(posedge clk);
            timeout = timeout + 1;
        end
        res_rem = remainder;
        if (res_rem == 32'd0)
            $display("✓ PASS: 7 %% 7 = 0\n");
        else
            $display("✗ FAIL: Got %d, expected 0\n", res_rem);
        
        @(posedge clk);
        
        // ===== EDGE CASE 10: REM negative =====
        $display("[EDGE 10] REM: a=-100, b=7 (negative dividend)");
        funct3 = `FUNCT3_REM;
        a = 32'hFFFFFF9C;  // -100
        b = 32'd7;
        start = 1;
        @(posedge clk);
        start = 0;
        timeout = 0;
        while (!done && timeout < 1000) begin
            @(posedge clk);
            timeout = timeout + 1;
        end
        res_rem = remainder;
        if ($signed(res_rem) == -32'd2)
            $display("✓ PASS: -100 %% 7 = -2\n");
        else
            $display("✗ FAIL: Got %d, expected -2\n", $signed(res_rem));
        
        @(posedge clk);
        
        // ===== EDGE CASE 11: REMU dividend < divisor =====
        $display("[EDGE 11] REMU: a=5, b=10 (dividend < divisor)");
        funct3 = `FUNCT3_REMU;
        a = 32'd5;
        b = 32'd10;
        start = 1;
        @(posedge clk);
        start = 0;
        timeout = 0;
        while (!done && timeout < 1000) begin
            @(posedge clk);
            timeout = timeout + 1;
        end
        res_rem = remainder;
        if (res_rem == 32'd5)
            $display("✓ PASS: 5 %% 10 = 5\n");
        else
            $display("✗ FAIL: Got %d, expected 5\n", res_rem);
        
        @(posedge clk);
        
        // ===== EDGE CASE 12: DIV by 1 =====
        $display("[EDGE 12] DIV: a=12345, b=1");
        funct3 = `FUNCT3_DIV;
        a = 32'd12345;
        b = 32'd1;
        start = 1;
        @(posedge clk);
        start = 0;
        timeout = 0;
        while (!done && timeout < 1000) begin
            @(posedge clk);
            timeout = timeout + 1;
        end
        res_quot = quotient;
        if (res_quot == 32'd12345)
            $display("✓ PASS: 12345 ÷ 1 = 12345\n");
        else
            $display("✗ FAIL: Got %d, expected 12345\n", res_quot);
        
        @(posedge clk);
        @(posedge clk);
        @(posedge clk);
        
        $display("==========================================");
        $display("MDU Test Suite Complete (All Edge Cases)");
        $display("==========================================\n");
        
        $finish;
    end
    
endmodule
