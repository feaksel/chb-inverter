/**
 * @file adc_interface.v
 * @brief SPI Master ADC Interface Peripheral
 *
 * Provides SPI master interface for reading external ADC chips.
 * Supports 4-channel operation with configurable SPI clock.
 *
 * Features:
 * - SPI master mode (CPOL=0, CPHA=0)
 * - Configurable clock divider
 * - 4 independent channels
 * - Automatic conversion triggering
 * - 16-bit ADC data readout
 *
 * Register Map (Base: 0x00020100):
 * 0x00: CTRL        - Control register (enable, start conversion)
 * 0x04: CLK_DIV     - SPI clock divider (SPI_CLK = CLK / (2 * CLK_DIV))
 * 0x08: CH_SELECT   - Channel selection (0-3)
 * 0x0C: DATA_CH0    - Channel 0 ADC data (read-only)
 * 0x10: DATA_CH1    - Channel 1 ADC data (read-only)
 * 0x14: DATA_CH2    - Channel 2 ADC data (read-only)
 * 0x18: DATA_CH3    - Channel 3 ADC data (read-only)
 * 0x1C: STATUS      - Status register (busy, valid flags)
 *
 * CTRL Register:
 * [0]: ENABLE       - Enable SPI module
 * [1]: START        - Start conversion (self-clearing)
 * [2]: AUTO_MODE    - Automatic sequential conversion
 * [7:4]: Reserved
 *
 * STATUS Register:
 * [0]: BUSY         - SPI transaction in progress
 * [3:1]: Reserved
 * [7:4]: VALID[3:0] - Data valid flags for each channel
 */

module adc_interface #(
    parameter ADDR_WIDTH = 8,
    parameter CLK_FREQ = 50_000_000,
    parameter DEFAULT_CLK_DIV = 50  // 500 kHz SPI clock
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

    // SPI interface (to external ADC)
    output reg                     spi_sck,      // SPI clock
    output reg                     spi_mosi,     // Master out, slave in
    input  wire                    spi_miso,     // Master in, slave out
    output reg                     spi_cs_n,     // Chip select (active low)

    // Interrupt
    output reg                     irq           // Interrupt when conversion complete
);

    //==========================================================================
    // Control Registers
    //==========================================================================

    reg        enable;
    reg        start;
    reg        auto_mode;
    reg [7:0]  clk_div;
    reg [1:0]  channel_select;
    reg [15:0] adc_data [0:3];      // ADC data for 4 channels
    reg [3:0]  data_valid;          // Valid flags for each channel

    // Initialize
    initial begin
        enable = 1'b0;
        start = 1'b0;
        auto_mode = 1'b0;
        clk_div = DEFAULT_CLK_DIV;
        channel_select = 2'd0;
        adc_data[0] = 16'd0;
        adc_data[1] = 16'd0;
        adc_data[2] = 16'd0;
        adc_data[3] = 16'd0;
        data_valid = 4'h0;
        spi_sck = 1'b0;
        spi_mosi = 1'b0;
        spi_cs_n = 1'b1;
        irq = 1'b0;
    end

    //==========================================================================
    // SPI State Machine
    //==========================================================================

    localparam STATE_IDLE       = 3'd0;
    localparam STATE_CS_ASSERT  = 3'd1;
    localparam STATE_SEND_CMD   = 3'd2;
    localparam STATE_READ_DATA  = 3'd3;
    localparam STATE_CS_DEASSERT = 3'd4;

    reg [2:0]  spi_state;
    reg [7:0]  clk_counter;
    reg [4:0]  bit_counter;
    reg [15:0] rx_shift_reg;
    reg [7:0]  tx_shift_reg;
    reg        spi_busy;

    // SPI clock generation
    wire spi_clk_edge = (clk_counter == clk_div - 1);

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            spi_state <= STATE_IDLE;
            spi_cs_n <= 1'b1;
            spi_sck <= 1'b0;
            spi_mosi <= 1'b0;
            clk_counter <= 8'd0;
            bit_counter <= 5'd0;
            rx_shift_reg <= 16'd0;
            tx_shift_reg <= 8'd0;
            spi_busy <= 1'b0;
            irq <= 1'b0;
        end else begin
            // Default: clear interrupt
            irq <= 1'b0;

            case (spi_state)
                STATE_IDLE: begin
                    spi_cs_n <= 1'b1;
                    spi_sck <= 1'b0;
                    spi_busy <= 1'b0;
                    clk_counter <= 8'd0;

                    if (enable && start) begin
                        spi_state <= STATE_CS_ASSERT;
                        spi_busy <= 1'b1;
                        // Prepare command byte: 0b1xxx0000 where xxx is channel
                        tx_shift_reg <= {1'b1, channel_select, 5'b00000};
                    end
                end

                STATE_CS_ASSERT: begin
                    spi_cs_n <= 1'b0;
                    clk_counter <= clk_counter + 1;
                    if (spi_clk_edge) begin
                        spi_state <= STATE_SEND_CMD;
                        bit_counter <= 5'd0;
                        clk_counter <= 8'd0;
                    end
                end

                STATE_SEND_CMD: begin
                    clk_counter <= clk_counter + 1;

                    if (spi_clk_edge) begin
                        if (bit_counter < 8) begin
                            // Toggle clock
                            spi_sck <= ~spi_sck;

                            if (!spi_sck) begin
                                // Rising edge of SPI clock - output data
                                spi_mosi <= tx_shift_reg[7];
                                tx_shift_reg <= {tx_shift_reg[6:0], 1'b0};
                            end else begin
                                // Falling edge - increment bit counter
                                bit_counter <= bit_counter + 1;
                            end
                        end else begin
                            spi_state <= STATE_READ_DATA;
                            bit_counter <= 5'd0;
                            spi_sck <= 1'b0;
                        end
                        clk_counter <= 8'd0;
                    end
                end

                STATE_READ_DATA: begin
                    clk_counter <= clk_counter + 1;

                    if (spi_clk_edge) begin
                        if (bit_counter < 16) begin
                            // Toggle clock
                            spi_sck <= ~spi_sck;

                            if (!spi_sck) begin
                                // Rising edge - sample data
                                rx_shift_reg <= {rx_shift_reg[14:0], spi_miso};
                            end else begin
                                // Falling edge
                                bit_counter <= bit_counter + 1;
                            end
                        end else begin
                            spi_state <= STATE_CS_DEASSERT;
                            spi_sck <= 1'b0;
                        end
                        clk_counter <= 8'd0;
                    end
                end

                STATE_CS_DEASSERT: begin
                    spi_cs_n <= 1'b1;
                    clk_counter <= clk_counter + 1;

                    if (spi_clk_edge) begin
                        // Store received data
                        adc_data[channel_select] <= rx_shift_reg;
                        data_valid[channel_select] <= 1'b1;
                        irq <= 1'b1;  // Generate interrupt

                        // If auto mode, move to next channel
                        if (auto_mode) begin
                            channel_select <= channel_select + 1;
                            spi_state <= STATE_CS_ASSERT;
                        end else begin
                            spi_state <= STATE_IDLE;
                        end
                        clk_counter <= 8'd0;
                    end
                end

                default: spi_state <= STATE_IDLE;
            endcase
        end
    end

    //==========================================================================
    // Wishbone Bus Interface
    //==========================================================================

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            enable <= 1'b0;
            start <= 1'b0;
            auto_mode <= 1'b0;
            clk_div <= DEFAULT_CLK_DIV;
            channel_select <= 2'd0;
            wb_ack <= 1'b0;
            wb_dat_o <= 32'd0;
        end else begin
            wb_ack <= wb_stb && !wb_ack;
            start <= 1'b0;  // Start is self-clearing

            if (wb_stb && wb_we && !wb_ack) begin
                // Write
                case (wb_addr[7:2])
                    6'h00: begin  // CTRL
                        enable <= wb_dat_i[0];
                        start <= wb_dat_i[1];
                        auto_mode <= wb_dat_i[2];
                    end
                    6'h01: clk_div <= wb_dat_i[7:0];              // CLK_DIV
                    6'h02: channel_select <= wb_dat_i[1:0];       // CH_SELECT
                endcase
            end else if (wb_stb && !wb_we && !wb_ack) begin
                // Read
                case (wb_addr[7:2])
                    6'h00: wb_dat_o <= {29'd0, auto_mode, start, enable};  // CTRL
                    6'h01: wb_dat_o <= {24'd0, clk_div};                    // CLK_DIV
                    6'h02: wb_dat_o <= {30'd0, channel_select};             // CH_SELECT
                    6'h03: wb_dat_o <= {16'd0, adc_data[0]};                // DATA_CH0
                    6'h04: wb_dat_o <= {16'd0, adc_data[1]};                // DATA_CH1
                    6'h05: wb_dat_o <= {16'd0, adc_data[2]};                // DATA_CH2
                    6'h06: wb_dat_o <= {16'd0, adc_data[3]};                // DATA_CH3
                    6'h07: wb_dat_o <= {24'd0, data_valid, 3'd0, spi_busy}; // STATUS
                    default: wb_dat_o <= 32'h0;
                endcase
            end
        end
    end

endmodule
