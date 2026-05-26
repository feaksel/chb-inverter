/**
 * @file timer.v
 * @brief General Purpose Timer Peripheral
 *
 * Provides timing and delay functionality with interrupt generation.
 * Useful for periodic tasks, delays, and timeouts.
 *
 * Features:
 * - 32-bit free-running counter
 * - Configurable prescaler
 * - Compare match interrupt
 * - Auto-reload mode
 * - One-shot mode
 *
 * Register Map (Base: 0x00020300):
 * 0x00: CTRL        - Control register (enable, mode, interrupt enable)
 * 0x04: PRESCALER   - Clock prescaler value
 * 0x08: COUNTER     - Current counter value (read-only)
 * 0x0C: COMPARE     - Compare value for match interrupt
 * 0x10: STATUS      - Status register (match flag, etc.)
 *
 * CTRL Register:
 * [0]: ENABLE       - Enable timer
 * [1]: AUTO_RELOAD  - Auto-reload on match (0=one-shot, 1=auto-reload)
 * [2]: INT_ENABLE   - Enable match interrupt
 * [7:3]: Reserved
 *
 * STATUS Register:
 * [0]: MATCH        - Compare match occurred (write 1 to clear)
 * [7:1]: Reserved
 *
 * Timing Calculation:
 * Timer frequency = CLK_FREQ / (PRESCALER + 1)
 * Match time = COMPARE / Timer frequency
 */

module timer #(
    parameter ADDR_WIDTH = 8,
    parameter CLK_FREQ = 50_000_000
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

    // Interrupt
    output reg                     irq
);

    //==========================================================================
    // Control Registers
    //==========================================================================

    reg        enable;
    reg        auto_reload;
    reg        int_enable;
    reg [31:0] prescaler;
    reg [31:0] compare_value;
    reg [31:0] counter;
    reg [31:0] prescaler_counter;
    reg        match_flag;

    // Initialize
    initial begin
        enable = 1'b0;
        auto_reload = 1'b0;
        int_enable = 1'b0;
        prescaler = 32'd0;
        compare_value = 32'hFFFFFFFF;
        counter = 32'd0;
        prescaler_counter = 32'd0;
        match_flag = 1'b0;
        irq = 1'b0;
    end

    //==========================================================================
    // Timer Logic
    //==========================================================================

    wire prescaler_tick = (prescaler_counter >= prescaler);

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            counter <= 32'd0;
            prescaler_counter <= 32'd0;
            match_flag <= 1'b0;
        end else begin
            if (enable) begin
                // Prescaler counter
                if (prescaler_tick) begin
                    prescaler_counter <= 32'd0;

                    // Main counter
                    if (counter >= compare_value) begin
                        match_flag <= 1'b1;

                        if (auto_reload) begin
                            counter <= 32'd0;  // Auto-reload
                        end else begin
                            enable <= 1'b0;    // One-shot mode, stop timer
                        end
                    end else begin
                        counter <= counter + 1;
                    end
                end else begin
                    prescaler_counter <= prescaler_counter + 1;
                end
            end else begin
                counter <= 32'd0;
                prescaler_counter <= 32'd0;
            end
        end
    end

    // Generate interrupt
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            irq <= 1'b0;
        end else begin
            irq <= int_enable && match_flag;
        end
    end

    //==========================================================================
    // Wishbone Bus Interface
    //==========================================================================

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            enable <= 1'b0;
            auto_reload <= 1'b0;
            int_enable <= 1'b0;
            prescaler <= 32'd0;
            compare_value <= 32'hFFFFFFFF;
            wb_ack <= 1'b0;
            wb_dat_o <= 32'd0;
        end else begin
            wb_ack <= wb_stb && !wb_ack;

            if (wb_stb && wb_we && !wb_ack) begin
                // Write
                case (wb_addr[7:2])
                    6'h00: begin  // CTRL
                        enable <= wb_dat_i[0];
                        auto_reload <= wb_dat_i[1];
                        int_enable <= wb_dat_i[2];
                    end
                    6'h01: prescaler <= wb_dat_i;        // PRESCALER
                    6'h03: compare_value <= wb_dat_i;    // COMPARE
                    6'h04: begin  // STATUS (write 1 to clear flags)
                        if (wb_dat_i[0]) match_flag <= 1'b0;
                    end
                endcase
            end else if (wb_stb && !wb_we && !wb_ack) begin
                // Read
                case (wb_addr[7:2])
                    6'h00: wb_dat_o <= {29'd0, int_enable, auto_reload, enable};  // CTRL
                    6'h01: wb_dat_o <= prescaler;        // PRESCALER
                    6'h02: wb_dat_o <= counter;          // COUNTER
                    6'h03: wb_dat_o <= compare_value;    // COMPARE
                    6'h04: wb_dat_o <= {31'd0, match_flag};  // STATUS
                    default: wb_dat_o <= 32'h0;
                endcase
            end
        end
    end

endmodule
