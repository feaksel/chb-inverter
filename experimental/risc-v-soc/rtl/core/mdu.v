`include "riscv_defines.vh"

module mdu (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        start,
    input  wire [2:0]  funct3,     // operation select (MUL/DIV/REM variants)
    input  wire [31:0] a,
    input  wire [31:0] b,
    output reg         busy,
    output reg         done,
    output reg [63:0]  product,
    output reg [31:0]  quotient,
    output reg [31:0]  remainder
);

    // Internal state
    localparam IDLE = 2'd0;
    localparam MUL  = 2'd1;
    localparam DIV  = 2'd2;

    reg [1:0] state;

    // Multiplier internals
    reg [63:0] multiplicand;
    reg [31:0] multiplier;
    reg [63:0] acc;
    reg [5:0]  mul_count;
    reg        mul_sign;

    // Divider internals
    reg [63:0] dividend_shift;
    reg [31:0] divisor_abs;
    reg [31:0] quotient_reg;
    reg [31:0] remainder_reg;
    reg [5:0]  div_count;
    reg        dividend_neg, divisor_neg;
    reg [31:0] dividend_abs;

    // Latches for start
    reg [2:0]  op_latched;
    reg [31:0] a_latched, b_latched;

    wire is_mul = (op_latched == `FUNCT3_MUL) || (op_latched == `FUNCT3_MULH) ||
                  (op_latched == `FUNCT3_MULHSU) || (op_latched == `FUNCT3_MULHU);
    wire is_div = (op_latched == `FUNCT3_DIV) || (op_latched == `FUNCT3_DIVU) ||
                  (op_latched == `FUNCT3_REM) || (op_latched == `FUNCT3_REMU);

    // Helper: signedness for multiplier operands (based on funct3 semantics)
    wire mul_signed_a = (op_latched == `FUNCT3_MULH) || (op_latched == `FUNCT3_MULHSU);
    wire mul_signed_b = (op_latched == `FUNCT3_MULH);

    // Helper: divider op_sel mapping (internal)
    wire [1:0] div_op_sel = (op_latched == `FUNCT3_DIV)  ? 2'b00 :
                           (op_latched == `FUNCT3_DIVU) ? 2'b01 :
                           (op_latched == `FUNCT3_REM)  ? 2'b10 : 2'b11;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= IDLE;
            busy <= 1'b0;
            done <= 1'b0;
            product <= 64'd0;
            quotient <= 32'd0;
            remainder <= 32'd0;
            multiplicand <= 64'd0;
            multiplier <= 32'd0;
            acc <= 64'd0;
            mul_count <= 6'd0;
            dividend_shift <= 64'd0;
            divisor_abs <= 32'd0;
            quotient_reg <= 32'd0;
            remainder_reg <= 32'd0;
            div_count <= 6'd0;
            op_latched <= 3'd0;
            a_latched <= 32'd0;
            b_latched <= 32'd0;
            dividend_neg <= 1'b0;
            divisor_neg <= 1'b0;
        end else begin
            case (state)
                IDLE: begin
                    done <= 1'b0;
                    if (start) begin
                        // Latch inputs
                        op_latched <= funct3;
                        a_latched <= a;
                        b_latched <= b;

                        // Decide path
                        if ( (funct3 == `FUNCT3_MUL) || (funct3 == `FUNCT3_MULH) ||
                             (funct3 == `FUNCT3_MULHSU) || (funct3 == `FUNCT3_MULHU) ) begin
                            // Prepare multiplier (unsigned abs conversion if needed)
                            mul_sign <= ((funct3 == `FUNCT3_MULH) || (funct3 == `FUNCT3_MULHSU)) && a[31];
                            // Proper signed handling below
                            multiplicand <= {32'd0, ((funct3 == `FUNCT3_MULH) && a[31]) ? (~a + 1'b1) : a};
                            multiplier <= ((funct3 == `FUNCT3_MULH) && b[31]) ? (~b + 1'b1) : b;
                            acc <= 64'd0;
                            mul_count <= 6'd0;
                            busy <= 1'b1;
                            state <= MUL;
                        end else begin
                            // Divider prepare
                            dividend_neg <= ((funct3 == `FUNCT3_DIV) || (funct3 == `FUNCT3_REM)) && a[31];
                            divisor_neg <= ((funct3 == `FUNCT3_DIV) || (funct3 == `FUNCT3_REM)) && b[31];
                            dividend_abs <= (((funct3 == `FUNCT3_DIV) || (funct3 == `FUNCT3_REM)) && a[31]) ? (~a + 1'b1) : a;
                            divisor_abs <= (((funct3 == `FUNCT3_DIV) || (funct3 == `FUNCT3_REM)) && b[31]) ? (~b + 1'b1) : b;
                            // Put dividend in upper 32 bits so we can shift it out MSB-first
                            dividend_shift <= {(((funct3 == `FUNCT3_DIV) || (funct3 == `FUNCT3_REM)) && a[31]) ? (~a + 1'b1) : a, 32'd0};
                            quotient_reg <= 32'd0;
                            remainder_reg <= 32'd0;
                            div_count <= 6'd0;
                            busy <= 1'b1;
                            state <= DIV;
                        end
                    end
                end

                MUL: begin
                    if (mul_count < 32) begin
                        if (multiplier[0]) begin
                            acc <= acc + multiplicand;
                        end
                        multiplicand <= multiplicand << 1;
                        multiplier <= multiplier >> 1;
                        mul_count <= mul_count + 1;
                    end else begin
                        // Apply sign correction based on operation type
                        // MULH: both operands are signed
                        //   If exactly one operand is negative (a_neg XOR b_neg), negate result
                        // MULHSU: a is signed, b is unsigned
                        //   If a is negative, negate result  
                        // MULHU: both unsigned, no sign correction
                        // MUL: lower 32 bits, no sign correction needed (inherent in 2's complement)
                        if (op_latched == `FUNCT3_MULH) begin
                            // MULH: negate if exactly one operand is negative (signs differ)
                            if ((a_latched[31] ^ b_latched[31]) == 1'b1) begin
                                product <= ~acc + 64'd1;
                            end else begin
                                product <= acc;
                            end
                        end else if (op_latched == `FUNCT3_MULHSU && a_latched[31]) begin
                            // MULHSU: negate if a is negative
                            product <= ~acc + 64'd1;
                        end else begin
                            // MULHU or MUL: no sign correction
                            product <= acc;
                        end
                        busy <= 1'b0;
                        done <= 1'b1;
                        state <= IDLE;
                    end
                end

                DIV: begin
                    if (divisor_abs == 32'd0) begin
                        // division by zero behaviour
                        quotient <= 32'hFFFFFFFF;
                        remainder <= dividend_shift[63:32];
                        busy <= 1'b0;
                        done <= 1'b1;
                        state <= IDLE;
                    end else if (div_count < 32) begin
                        // Standard long division: 
                        // Shift remainder left, bring in next dividend bit from MSB
                        // Check if remainder >= divisor, if so subtract and set quotient bit to 1
                        
                        if ({remainder_reg[30:0], dividend_shift[63]} >= divisor_abs) begin
                            // Remainder is large enough: subtract divisor and set quotient bit to 1
                            remainder_reg <= {remainder_reg[30:0], dividend_shift[63]} - divisor_abs;
                            quotient_reg <= {quotient_reg[30:0], 1'b1};
                        end else begin
                            // Remainder is small: keep as is and set quotient bit to 0
                            remainder_reg <= {remainder_reg[30:0], dividend_shift[63]};
                            quotient_reg <= {quotient_reg[30:0], 1'b0};
                        end
                        dividend_shift <= {dividend_shift[62:0], 1'b0};
                        div_count <= div_count + 1;
                    end else begin
                        // Done with iterations - apply sign correction and output
                        if (op_latched == `FUNCT3_DIV) begin
                            // signed: quotient sign = sign_a ^ sign_b, remainder sign = sign_a
                            quotient <= (dividend_neg ^ divisor_neg) ? (~quotient_reg + 32'd1) : quotient_reg;
                            remainder <= dividend_neg ? (~remainder_reg + 32'd1) : remainder_reg[31:0];
                        end else if (op_latched == `FUNCT3_DIVU) begin
                            // unsigned
                            quotient <= quotient_reg;
                            remainder <= remainder_reg[31:0];
                        end else if (op_latched == `FUNCT3_REM) begin
                            // signed remainder: remainder sign = sign of dividend
                            remainder <= dividend_neg ? (~remainder_reg + 32'd1) : remainder_reg[31:0];
                            quotient <= (dividend_neg ^ divisor_neg) ? (~quotient_reg + 32'd1) : quotient_reg;
                        end else begin
                            // REMU: unsigned remainder
                            remainder <= remainder_reg[31:0];
                            quotient <= quotient_reg;
                        end
                        busy <= 1'b0;
                        done <= 1'b1;
                        state <= IDLE;
                    end
                end

                default: state <= IDLE;
            endcase

            // clear done after one cycle (so it's a pulse)
            if (done) begin
                done <= 1'b0;
            end
        end
    end

endmodule
