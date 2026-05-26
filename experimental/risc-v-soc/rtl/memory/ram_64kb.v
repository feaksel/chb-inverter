/**
 * @file ram_64kb.v
 * @brief 64 KB Random Access Memory for runtime data
 *
 * Technology-independent RAM implementation:
 * - FPGA: Synthesizes to Block RAM (multiple BRAM blocks)
 * - ASIC: Use SRAM compiler (single-port or dual-port SRAM)
 *
 * Address space: 0x00008000 - 0x00017FFF (64 KB)
 * Organization: 16K words × 32 bits
 *
 * Features:
 * - Byte-addressable with byte enables
 * - Single-cycle read/write
 * - Synchronous operation
 */

module ram_64kb #(
    parameter ADDR_WIDTH = 16,     // 64KB = 2^16 bytes
    parameter DATA_WIDTH = 32
)(
    input  wire                    clk,
    input  wire [ADDR_WIDTH-1:0]   addr,        // Byte address
    input  wire [DATA_WIDTH-1:0]   data_in,
    input  wire                    we,          // Write enable
    input  wire [3:0]              be,          // Byte enable (4 bits for 32-bit word)
    input  wire                    stb,         // Wishbone strobe
    output reg  [DATA_WIDTH-1:0]   data_out,
    output reg                     ack
);

    // Memory array: 16K words × 32 bits = 64 KB
    localparam MEM_DEPTH = (1 << (ADDR_WIDTH - 2));

    reg [DATA_WIDTH-1:0] ram_memory [0:MEM_DEPTH-1];

    // Word address
    wire [ADDR_WIDTH-3:0] word_addr = addr[ADDR_WIDTH-1:2];

    // Synchronous read/write with byte enables
    always @(posedge clk) begin
        if (stb) begin
            if (we) begin
                // Write with byte enables
                if (be[0]) ram_memory[word_addr][7:0]   <= data_in[7:0];
                if (be[1]) ram_memory[word_addr][15:8]  <= data_in[15:8];
                if (be[2]) ram_memory[word_addr][23:16] <= data_in[23:16];
                if (be[3]) ram_memory[word_addr][31:24] <= data_in[31:24];
            end
            // Read (always performed, write-first behavior)
            data_out <= ram_memory[word_addr];
            ack <= 1'b1;
        end else begin
            ack <= 1'b0;
        end
    end

    // Initialize to zero for simulation
    integer i;
    initial begin
        for (i = 0; i < MEM_DEPTH; i = i + 1) begin
            ram_memory[i] = 32'h0;
        end
        $display("[RAM] Initialized 64KB RAM");
    end

endmodule
