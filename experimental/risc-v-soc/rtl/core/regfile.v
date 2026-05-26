
module regfile (
    input  wire        clk,
    input  wire        rst_n,

    // Read port 1 (rs1)
    input  wire [4:0]  rs1_addr,   // Register address to read
    output wire [31:0] rs1_data,   // Data read from register

    // Read port 2 (rs2)
    input  wire [4:0]  rs2_addr,   // Register address to read
    output wire [31:0] rs2_data,   // Data read from register

    // Write port (rd)
    input  wire [4:0]  rd_addr,    // Register address to write
    input  wire [31:0] rd_data,    // Data to write
    input  wire        rd_wen      // Write enable (1=write, 0=no write)
);

    //==========================================================================
    // Register Array
    //==========================================================================

    reg [31:0] registers [0:31];  // x0 to x31 (x0 will be ignored in writes)

    //==========================================================================
    // Write Logic (Synchronous)
    //==========================================================================

    /**
     *
     * On rising edge of clk:
     * - If rd_wen is 1 and rd_addr != 0:
     *   * Write rd_data to registers[rd_addr]
     * - If rd_addr == 0:
     *   * Ignore write (x0 is always 0)
     */

    integer i;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // Reset all registers to 0
            for (i = 0; i < 32; i = i + 1) begin
                registers[i] <= 32'h0;
            end
        end else begin
            if (rd_wen && (rd_addr != 5'd0)) begin
                // Write to register (x0 writes are ignored)
                registers[rd_addr] <= rd_data;
            end
        end
    end

    //==========================================================================
    // Read Logic (Combinational)
    //==========================================================================

    /**
     * rs1_data:
     * - 0 if rs1_addr == 0
     * - registers[rs1_addr] otherwise
     */

    assign rs1_data = (rs1_addr == 5'd0) ? 32'h0 : registers[rs1_addr]; 
    assign rs2_data = (rs2_addr == 5'd0) ? 32'h0 : registers[rs2_addr]; 

endmodule
