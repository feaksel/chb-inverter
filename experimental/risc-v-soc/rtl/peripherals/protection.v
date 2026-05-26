/**
 * @file protection.v
 * @brief Hardware Protection and Fault Detection Peripheral
 *
 * Safety-critical peripheral that monitors fault conditions and
 * can immediately disable PWM outputs.
 *
 * Features:
 * - Overcurrent detection (external comparator input)
 * - Overvoltage detection (external comparator input)
 * - E-stop button input
 * - Watchdog timer
 * - Fault latching and clearing
 * - Interrupt generation
 *
 * Register Map (Base: 0x00020200):
 * 0x00: FAULT_STATUS  - Current fault status (read-only, bit-mapped)
 * 0x04: FAULT_ENABLE  - Enable fault detection (write)
 * 0x08: FAULT_CLEAR   - Clear latched faults (write)
 * 0x0C: WATCHDOG_VAL  - Watchdog timeout value (clock cycles)
 * 0x10: WATCHDOG_KICK - Kick watchdog (write any value)
 * 0x14: FAULT_LATCH   - Latched fault status
 *
 * FAULT_STATUS bits:
 * [0]: OCP (overcurrent protection)
 * [1]: OVP (overvoltage protection)
 * [2]: E-STOP
 * [3]: Watchdog timeout
 * [31:4]: Reserved
 */

module protection #(
    parameter ADDR_WIDTH = 8,
    parameter WATCHDOG_DEFAULT = 50_000_000  // 1 second @ 50 MHz
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

    // External fault inputs (active HIGH)
    input  wire                    fault_ocp,    // Overcurrent
    input  wire                    fault_ovp,    // Overvoltage
    input  wire                    estop_n,      // E-stop (active LOW)

    // Outputs
    output wire                    pwm_disable,  // Disable PWM (to PWM peripheral)
    output reg                     irq           // Interrupt request
);

    //==========================================================================
    // Fault Status Bits
    //==========================================================================

    localparam FAULT_OCP       = 0;
    localparam FAULT_OVP       = 1;
    localparam FAULT_ESTOP     = 2;
    localparam FAULT_WATCHDOG  = 3;

    //==========================================================================
    // Registers
    //==========================================================================

    reg [3:0]  fault_enable;        // Enable individual fault detections
    reg [3:0]  fault_status;        // Current fault status
    reg [3:0]  fault_latch;         // Latched faults (sticky)
    reg [31:0] watchdog_timeout;
    reg [31:0] watchdog_counter;
    reg        watchdog_expired;

    // Initialize
    initial begin
        fault_enable = 4'hF;  // All faults enabled by default
        fault_status = 4'h0;
        fault_latch = 4'h0;
        watchdog_timeout = WATCHDOG_DEFAULT;
        watchdog_counter = 0;
        watchdog_expired = 1'b0;
        irq = 1'b0;
    end

    //==========================================================================
    // Fault Detection
    //==========================================================================

    // Sample external fault inputs
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            fault_status <= 4'h0;
        end else begin
            fault_status[FAULT_OCP]    <= fault_ocp && fault_enable[FAULT_OCP];
            fault_status[FAULT_OVP]    <= fault_ovp && fault_enable[FAULT_OVP];
            fault_status[FAULT_ESTOP]  <= !estop_n && fault_enable[FAULT_ESTOP];  // Active LOW
            fault_status[FAULT_WATCHDOG] <= watchdog_expired && fault_enable[FAULT_WATCHDOG];
        end
    end

    // Latch faults (sticky until cleared)
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            fault_latch <= 4'h0;
        end else begin
            // Set latches on fault
            if (fault_status[FAULT_OCP])      fault_latch[FAULT_OCP] <= 1'b1;
            if (fault_status[FAULT_OVP])      fault_latch[FAULT_OVP] <= 1'b1;
            if (fault_status[FAULT_ESTOP])    fault_latch[FAULT_ESTOP] <= 1'b1;
            if (fault_status[FAULT_WATCHDOG]) fault_latch[FAULT_WATCHDOG] <= 1'b1;
        end
    end

    // Disable PWM if any fault is active (latched or current)
    assign pwm_disable = |fault_latch || |fault_status;

    // Generate interrupt on any fault
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            irq <= 1'b0;
        end else begin
            irq <= |fault_status;  // Interrupt if any fault active
        end
    end

    //==========================================================================
    // Watchdog Timer
    //==========================================================================

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            watchdog_counter <= 0;
            watchdog_expired <= 1'b0;
        end else begin
            if (watchdog_counter >= watchdog_timeout) begin
                // Stop counting once expired to prevent overflow wrap-around
                watchdog_expired <= 1'b1;
                watchdog_counter <= watchdog_timeout;  // Hold at timeout value
            end else begin
                watchdog_counter <= watchdog_counter + 1;
            end
        end
    end

    //==========================================================================
    // Wishbone Bus Interface
    //==========================================================================

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            fault_enable <= 4'hF;
            watchdog_timeout <= WATCHDOG_DEFAULT;
            wb_ack <= 1'b0;
            wb_dat_o <= 32'd0;
        end else begin
            wb_ack <= wb_stb && !wb_ack;

            if (wb_stb && wb_we && !wb_ack) begin
                // Write
                case (wb_addr[7:2])
                    6'h01: fault_enable <= wb_dat_i[3:0];
                    6'h02: fault_latch <= fault_latch & ~wb_dat_i[3:0];  // Clear bits
                    6'h03: watchdog_timeout <= wb_dat_i;
                    6'h04: begin
                        // Kick watchdog
                        watchdog_counter <= 0;
                        watchdog_expired <= 1'b0;
                    end
                endcase
            end else if (wb_stb && !wb_we && !wb_ack) begin
                // Read
                case (wb_addr[7:2])
                    6'h00: wb_dat_o <= {28'd0, fault_status};      // FAULT_STATUS
                    6'h01: wb_dat_o <= {28'd0, fault_enable};      // FAULT_ENABLE
                    6'h03: wb_dat_o <= watchdog_timeout;           // WATCHDOG_VAL
                    6'h05: wb_dat_o <= {28'd0, fault_latch};       // FAULT_LATCH
                    default: wb_dat_o <= 32'h0;
                endcase
            end
        end
    end

endmodule
