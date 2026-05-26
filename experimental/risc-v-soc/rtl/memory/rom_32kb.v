/**
 * @file rom_32kb.v
 * @brief 32 KB Read-Only Memory for firmware storage
 *
 * Technology-independent ROM implementation:
 * - FPGA: Synthesizes to Block RAM initialized from .hex file
 * - ASIC: Can be replaced with mask ROM or OTP ROM
 *
 * Address space: 0x00000000 - 0x00007FFF (32 KB)
 * Organization: 8K words × 32 bits
 *
 * @note Firmware must be compiled to firmware.hex before synthesis
 */

module rom_32kb #(
    parameter ADDR_WIDTH = 15,     // 32KB = 2^15 bytes
    parameter DATA_WIDTH = 32,
    parameter MEM_FILE = "firmware/firmware.hex"
)(
    input  wire                    clk,
    input  wire [ADDR_WIDTH-1:0]   addr,        // Byte address
    input  wire                    stb,         // Wishbone strobe
    output reg  [DATA_WIDTH-1:0]   data_out,
    output reg                     ack
);

    // Memory array: 8K words × 32 bits = 32 KB
    localparam MEM_DEPTH = (1 << (ADDR_WIDTH - 2));  // Divide by 4 for word addressing

    reg [DATA_WIDTH-1:0] rom_memory [0:MEM_DEPTH-1];

    // Initialize ROM from hex file
    initial begin
        $readmemh(MEM_FILE, rom_memory);

        // Print first few words for verification
        $display("[ROM] Initialized from %s", MEM_FILE);
        $display("[ROM] First 4 words:");
        $display("  0x00000000: 0x%08X", rom_memory[0]);
        $display("  0x00000004: 0x%08X", rom_memory[1]);
        $display("  0x00000008: 0x%08X", rom_memory[2]);
        $display("  0x0000000C: 0x%08X", rom_memory[3]);
    end

    // Word address (ignore bottom 2 bits for 32-bit alignment)
    wire [ADDR_WIDTH-3:0] word_addr = addr[ADDR_WIDTH-1:2];

    // Synchronous read (required for BRAM inference)
    always @(posedge clk) begin
        if (stb) begin
            data_out <= rom_memory[word_addr];
            ack <= 1'b1;
        end else begin
            ack <= 1'b0;
        end
    end

endmodule
