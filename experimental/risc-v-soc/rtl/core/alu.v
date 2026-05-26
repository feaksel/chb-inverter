`include "riscv_defines.vh"

module alu (
    input  wire [31:0] operand_a,   // First operand (usually rs1)
    input  wire [31:0] operand_b,   // Second operand (rs2 or immediate)
    input  wire [3:0]  alu_op,      // Operation select (from decoder)
    output reg  [31:0] result,      // Result of operation
    output wire        zero         // 1 if result is zero (for branches)
);

    //==========================================================================
    // ALU Operation (Combinational)
    //==========================================================================

always @(*) begin
    case (alu_op)
        `ALU_OP_ADD:  result = operand_a + operand_b;
        `ALU_OP_SUB:  result = operand_a - operand_b;
        `ALU_OP_AND:  result = operand_a & operand_b;
        `ALU_OP_OR:   result = operand_a | operand_b;
        `ALU_OP_XOR:  result = operand_a ^ operand_b;
        `ALU_OP_SLL:  result = operand_a << operand_b[4:0];
        `ALU_OP_SRL:  result = operand_a >> operand_b[4:0];
        `ALU_OP_SRA:  result = $signed(operand_a) >>> operand_b[4:0];
        `ALU_OP_SLT:  result = ($signed(operand_a) < $signed(operand_b)) ? 32'd1 : 32'd0;
        `ALU_OP_SLTU: result = (operand_a < operand_b) ? 32'd1 : 32'd0;

        

        default:      result = 32'hXXXXXXXX;
    endcase
end
 
    //==========================================================================
    // Zero Flag (for branch instructions)
    //==========================================================================

    /**
     * Zero flag is used by branch instructions (BEQ, BNE)
     * It should be 1 if result is all zeros
     */

    assign zero = (result == 32'h0);

    
endmodule
