/**
 * @file gpio.v
 * @brief General Purpose Input/Output Peripheral
 *
 * Provides 32 bidirectional GPIO pins with individual direction control.
 * Useful for LEDs, buttons, debug signals, and general interfacing.
 *
 * Features:
 * - 32 GPIO pins
 * - Individual direction control (input/output)
 * - Input synchronization (2-stage)
 * - Output enable control
 *
 * Register Map (Base: 0x00020400):
 * 0x00: DATA_OUT    - Output data register
 * 0x04: DATA_IN     - Input data register (read-only)
 * 0x08: DIR         - Direction control (0=input, 1=output)
 * 0x0C: OUTPUT_EN   - Output enable (0=disabled, 1=enabled)
 *
 * Usage Example:
 * - Set pin 0 as output: DIR[0] = 1, OUTPUT_EN[0] = 1
 * - Write to pin 0: DATA_OUT[0] = 1
 * - Read pin 1: value = DATA_IN[1]
 */

module gpio #(
    parameter ADDR_WIDTH = 8,
    parameter NUM_GPIOS = 32
)(
    // Wishbone bus interface
    input  wire                    clk,
    input  wire                    rst_n,
    input  wire [ADDR_WIDTH-1:0]   wb_addr,
    input  wire [31:0]             wb_dat_i,
    output reg  [31:0]             wb_dat_o,
    input  wire                    wb_we,
    input  wire [3:0]              wb_sel,
    input  wire                    wb_stb,
    output reg                     wb_ack,

    // GPIO pins (bidirectional)
    input  wire [NUM_GPIOS-1:0]    gpio_in,
    output wire [NUM_GPIOS-1:0]    gpio_out,
    output wire [NUM_GPIOS-1:0]    gpio_oe     // Output enable
);

    //==========================================================================
    // Control Registers
    //==========================================================================

    reg [NUM_GPIOS-1:0] data_out;       // Output data
    reg [NUM_GPIOS-1:0] direction;      // Direction (0=in, 1=out)
    reg [NUM_GPIOS-1:0] output_enable;  // Output enable

    // Input synchronization (prevent metastability)
    reg [NUM_GPIOS-1:0] gpio_in_sync1;
    reg [NUM_GPIOS-1:0] gpio_in_sync2;

    // Initialize
    initial begin
        data_out = {NUM_GPIOS{1'b0}};
        direction = {NUM_GPIOS{1'b0}};     // All inputs by default
        output_enable = {NUM_GPIOS{1'b0}};
        gpio_in_sync1 = {NUM_GPIOS{1'b0}};
        gpio_in_sync2 = {NUM_GPIOS{1'b0}};
    end

    //==========================================================================
    // Input Synchronization
    //==========================================================================

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            gpio_in_sync1 <= {NUM_GPIOS{1'b0}};
            gpio_in_sync2 <= {NUM_GPIOS{1'b0}};
        end else begin
            gpio_in_sync1 <= gpio_in;
            gpio_in_sync2 <= gpio_in_sync1;
        end
    end

    //==========================================================================
    // Output Assignment
    //==========================================================================

    assign gpio_out = data_out;
    assign gpio_oe = direction & output_enable;

    //==========================================================================
    // Wishbone Bus Interface
    //==========================================================================

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            data_out <= {NUM_GPIOS{1'b0}};
            direction <= {NUM_GPIOS{1'b0}};
            output_enable <= {NUM_GPIOS{1'b0}};
            wb_ack <= 1'b0;
            wb_dat_o <= 32'd0;
        end else begin
            wb_ack <= wb_stb && !wb_ack;

            if (wb_stb && wb_we && !wb_ack) begin
                // Write
                case (wb_addr[7:2])
                    6'h00: data_out <= wb_dat_i[NUM_GPIOS-1:0];       // DATA_OUT
                    6'h02: direction <= wb_dat_i[NUM_GPIOS-1:0];      // DIR
                    6'h03: output_enable <= wb_dat_i[NUM_GPIOS-1:0];  // OUTPUT_EN
                endcase
            end else if (wb_stb && !wb_we && !wb_ack) begin
                // Read
                case (wb_addr[7:2])
                    6'h00: wb_dat_o <= {{(32-NUM_GPIOS){1'b0}}, data_out};        // DATA_OUT
                    6'h01: wb_dat_o <= {{(32-NUM_GPIOS){1'b0}}, gpio_in_sync2};   // DATA_IN
                    6'h02: wb_dat_o <= {{(32-NUM_GPIOS){1'b0}}, direction};       // DIR
                    6'h03: wb_dat_o <= {{(32-NUM_GPIOS){1'b0}}, output_enable};   // OUTPUT_EN
                    default: wb_dat_o <= 32'h0;
                endcase
            end
        end
    end

endmodule
