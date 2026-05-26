/**
 * @file uart.v
 * @brief Simple UART Peripheral for Debug and Communication
 *
 * Provides basic UART functionality with configurable baud rate.
 * Standard 8N1 format (8 data bits, no parity, 1 stop bit).
 *
 * Features:
 * - Configurable baud rate via clock divider
 * - 8N1 format (8 data, no parity, 1 stop)
 * - TX and RX with status flags
 * - Interrupt on RX data ready
 * - Simple buffering (1-byte TX/RX)
 *
 * Register Map (Base: 0x00020500):
 * 0x00: DATA        - TX/RX data register
 * 0x04: STATUS      - Status register (TX_EMPTY, RX_READY, etc.)
 * 0x08: CTRL        - Control register (enable, interrupt enable)
 * 0x0C: BAUD_DIV    - Baud rate divider (CLK / BAUD_DIV = baud rate)
 *
 * STATUS Register:
 * [0]: RX_READY     - Receive data available
 * [1]: TX_EMPTY     - Transmit buffer empty
 * [2]: RX_OVERRUN   - Receive overrun error
 * [3]: FRAME_ERROR  - Frame error detected
 * [7:4]: Reserved
 *
 * CTRL Register:
 * [0]: RX_ENABLE    - Enable receiver
 * [1]: TX_ENABLE    - Enable transmitter
 * [2]: RX_INT_EN    - Enable RX interrupt
 * [7:3]: Reserved
 *
 * Baud Rate Calculation:
 * BAUD_DIV = CLK_FREQ / BAUD_RATE
 * Example: 50 MHz / 115200 = 434
 */

module uart #(
    parameter ADDR_WIDTH = 8,
    parameter CLK_FREQ = 50_000_000,
    parameter DEFAULT_BAUD = 115200
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

    // UART interface
    input  wire                    uart_rx,
    output reg                     uart_tx,

    // Interrupt
    output reg                     irq
);

    //==========================================================================
    // Control Registers
    //==========================================================================

    localparam DEFAULT_BAUD_DIV = CLK_FREQ / DEFAULT_BAUD;

    reg        rx_enable;
    reg        tx_enable;
    reg        rx_int_en;
    reg [15:0] baud_div;
    reg [7:0]  tx_data;
    reg [7:0]  rx_data;
    reg        rx_ready;
    reg        tx_empty;
    reg        rx_overrun;
    reg        frame_error;

    // Initialize
    initial begin
        rx_enable = 1'b1;
        tx_enable = 1'b1;
        rx_int_en = 1'b0;
        baud_div = DEFAULT_BAUD_DIV;
        tx_data = 8'd0;
        rx_data = 8'd0;
        rx_ready = 1'b0;
        tx_empty = 1'b1;
        rx_overrun = 1'b0;
        frame_error = 1'b0;
        uart_tx = 1'b1;
        irq = 1'b0;
    end

    //==========================================================================
    // TX State Machine
    //==========================================================================

    localparam TX_IDLE  = 2'd0;
    localparam TX_START = 2'd1;
    localparam TX_DATA  = 2'd2;
    localparam TX_STOP  = 2'd3;

    reg [1:0]  tx_state;
    reg [15:0] tx_baud_counter;
    reg [2:0]  tx_bit_counter;
    reg [7:0]  tx_shift_reg;
    reg        tx_start;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            tx_state <= TX_IDLE;
            uart_tx <= 1'b1;
            tx_baud_counter <= 16'd0;
            tx_bit_counter <= 3'd0;
            tx_shift_reg <= 8'd0;
            tx_empty <= 1'b1;
        end else begin
            case (tx_state)
                TX_IDLE: begin
                    uart_tx <= 1'b1;
                    // tx_empty is set in TX_STOP when transmission completes
                    // Removed race condition: was setting tx_empty=1 every cycle here
                    tx_baud_counter <= 16'd0;

                    if (tx_enable && tx_start) begin
                        tx_state <= TX_START;
                        tx_shift_reg <= tx_data;
                        tx_empty <= 1'b0;
                    end
                end

                TX_START: begin
                    uart_tx <= 1'b0;  // Start bit
                    tx_baud_counter <= tx_baud_counter + 1;

                    if (tx_baud_counter >= baud_div - 1) begin
                        tx_state <= TX_DATA;
                        tx_baud_counter <= 16'd0;
                        tx_bit_counter <= 3'd0;
                    end
                end

                TX_DATA: begin
                    uart_tx <= tx_shift_reg[0];
                    tx_baud_counter <= tx_baud_counter + 1;

                    if (tx_baud_counter >= baud_div - 1) begin
                        tx_shift_reg <= {1'b0, tx_shift_reg[7:1]};
                        tx_bit_counter <= tx_bit_counter + 1;
                        tx_baud_counter <= 16'd0;

                        if (tx_bit_counter == 7) begin
                            tx_state <= TX_STOP;
                        end
                    end
                end

                TX_STOP: begin
                    uart_tx <= 1'b1;  // Stop bit
                    tx_baud_counter <= tx_baud_counter + 1;

                    if (tx_baud_counter >= baud_div - 1) begin
                        tx_state <= TX_IDLE;
                        tx_baud_counter <= 16'd0;
                        tx_empty <= 1'b1;  // Set tx_empty when transmission completes
                    end
                end
            endcase
        end
    end

    //==========================================================================
    // RX State Machine
    //==========================================================================

    localparam RX_IDLE  = 2'd0;
    localparam RX_START = 2'd1;
    localparam RX_DATA  = 2'd2;
    localparam RX_STOP  = 2'd3;

    reg [1:0]  rx_state;
    reg [15:0] rx_baud_counter;
    reg [2:0]  rx_bit_counter;
    reg [7:0]  rx_shift_reg;
    reg        uart_rx_sync1;
    reg        uart_rx_sync2;

    // Synchronize RX input (prevent metastability)
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            uart_rx_sync1 <= 1'b1;
            uart_rx_sync2 <= 1'b1;
        end else begin
            uart_rx_sync1 <= uart_rx;
            uart_rx_sync2 <= uart_rx_sync1;
        end
    end

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            rx_state <= RX_IDLE;
            rx_baud_counter <= 16'd0;
            rx_bit_counter <= 3'd0;
            rx_shift_reg <= 8'd0;
            rx_ready <= 1'b0;
            rx_overrun <= 1'b0;
            frame_error <= 1'b0;
        end else begin
            case (rx_state)
                RX_IDLE: begin
                    rx_baud_counter <= 16'd0;

                    if (rx_enable && !uart_rx_sync2) begin
                        // Falling edge detected (start bit)
                        rx_state <= RX_START;
                    end
                end

                RX_START: begin
                    rx_baud_counter <= rx_baud_counter + 1;

                    // Sample at middle of bit period
                    if (rx_baud_counter >= (baud_div >> 1)) begin
                        if (!uart_rx_sync2) begin
                            // Valid start bit
                            rx_state <= RX_DATA;
                            rx_baud_counter <= 16'd0;
                            rx_bit_counter <= 3'd0;
                        end else begin
                            // False start bit
                            rx_state <= RX_IDLE;
                        end
                    end
                end

                RX_DATA: begin
                    rx_baud_counter <= rx_baud_counter + 1;

                    if (rx_baud_counter >= baud_div - 1) begin
                        rx_shift_reg <= {uart_rx_sync2, rx_shift_reg[7:1]};
                        rx_bit_counter <= rx_bit_counter + 1;
                        rx_baud_counter <= 16'd0;

                        if (rx_bit_counter == 7) begin
                            rx_state <= RX_STOP;
                        end
                    end
                end

                RX_STOP: begin
                    rx_baud_counter <= rx_baud_counter + 1;

                    if (rx_baud_counter >= baud_div - 1) begin
                        if (uart_rx_sync2) begin
                            // Valid stop bit
                            if (rx_ready) begin
                                rx_overrun <= 1'b1;  // Previous data not read
                            end else begin
                                rx_data <= rx_shift_reg;
                                rx_ready <= 1'b1;
                            end
                        end else begin
                            frame_error <= 1'b1;  // Invalid stop bit
                        end
                        rx_state <= RX_IDLE;
                        rx_baud_counter <= 16'd0;
                    end
                end
            endcase
        end
    end

    // Generate interrupt
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            irq <= 1'b0;
        end else begin
            irq <= rx_int_en && rx_ready;
        end
    end

    //==========================================================================
    // Wishbone Bus Interface
    //==========================================================================

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            rx_enable <= 1'b1;
            tx_enable <= 1'b1;
            rx_int_en <= 1'b0;
            baud_div <= DEFAULT_BAUD_DIV;
            tx_start <= 1'b0;
            wb_ack <= 1'b0;
            wb_dat_o <= 32'd0;
        end else begin
            wb_ack <= wb_stb && !wb_ack;
            tx_start <= 1'b0;  // Self-clearing

            if (wb_stb && wb_we && !wb_ack) begin
                // Write
                case (wb_addr[7:2])
                    6'h00: begin  // DATA
                        tx_data <= wb_dat_i[7:0];
                        tx_start <= 1'b1;
                    end
                    6'h02: begin  // CTRL
                        rx_enable <= wb_dat_i[0];
                        tx_enable <= wb_dat_i[1];
                        rx_int_en <= wb_dat_i[2];
                    end
                    6'h03: baud_div <= wb_dat_i[15:0];  // BAUD_DIV
                endcase
            end else if (wb_stb && !wb_we && !wb_ack) begin
                // Read
                case (wb_addr[7:2])
                    6'h00: begin  // DATA
                        wb_dat_o <= {24'd0, rx_data};
                        rx_ready <= 1'b0;     // Clear RX_READY on read
                        rx_overrun <= 1'b0;   // Clear errors
                        frame_error <= 1'b0;
                    end
                    6'h01: wb_dat_o <= {28'd0, frame_error, rx_overrun, tx_empty, rx_ready};  // STATUS
                    6'h02: wb_dat_o <= {29'd0, rx_int_en, tx_enable, rx_enable};  // CTRL
                    6'h03: wb_dat_o <= {16'd0, baud_div};  // BAUD_DIV
                    default: wb_dat_o <= 32'h0;
                endcase
            end
        end
    end

endmodule
