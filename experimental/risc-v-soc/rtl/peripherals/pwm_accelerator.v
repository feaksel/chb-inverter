/**
 * @file pwm_accelerator.v
 * @brief Hardware PWM Accelerator for 5-Level Inverter
 *
 * Features:
 * - Generates 8× PWM signals (complementary pairs for 4 H-bridge legs)
 * - Level-shifted carrier modulation in hardware
 * - Automatic sine generation from LUT
 * - CPU sets modulation index and frequency via registers
 * - Hardware dead-time insertion (configurable)
 *
 * Register Map (Base: 0x00020000):
 * 0x00: CTRL       - Control register (enable, mode)
 * 0x04: FREQ_DIV   - Carrier frequency divider
 * 0x08: MOD_INDEX  - Modulation index (0-65535 = 0-1.0)
 * 0x0C: SINE_PHASE - Sine phase accumulator
 * 0x10: SINE_FREQ  - Sine frequency control
 * 0x14: DEADTIME   - Dead-time in clock cycles
 * 0x18: STATUS     - Status register (read-only)
 * 0x1C: PWM_OUT    - Current PWM output state (read-only)
 */

module pwm_accelerator #(
    parameter CLK_FREQ = 50_000_000,
    parameter PWM_FREQ = 5_000,
    parameter ADDR_WIDTH = 8
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

    // PWM outputs (to gate drivers)
    output wire [7:0]              pwm_out,     // 8 PWM signals

    // Fault input (disables PWM immediately)
    input  wire                    fault
);

    //==========================================================================
    // Registers
    //==========================================================================

    reg        enable;
    reg        mode;                // 0 = auto sine, 1 = CPU-provided reference
    reg [15:0] freq_div;
    reg [15:0] mod_index;
    reg [31:0] sine_phase;
    reg [15:0] sine_freq;
    reg [15:0] deadtime_cycles;
    reg [15:0] cpu_reference;       // For manual mode

    // Default values
    initial begin
        enable = 1'b0;
        mode = 1'b0;
        freq_div = CLK_FREQ / (PWM_FREQ * 65536);  // For 5 kHz
        mod_index = 16'd0;
        sine_phase = 32'd0;
        sine_freq = 16'd1310;  // 50 Hz @ 50 MHz clock
        deadtime_cycles = 16'd50;  // 1 μs @ 50 MHz
        cpu_reference = 16'd0;
    end

    //==========================================================================
    // Enable gating (disable on fault)
    //==========================================================================

    wire enable_gated = enable && !fault;

    //==========================================================================
    // Carrier Generator (4 carriers for 5-level cascaded H-bridge)
    //==========================================================================

    wire signed [15:0] carrier1, carrier2, carrier3, carrier4;
    wire carrier_sync;

    carrier_generator #(
        .CARRIER_WIDTH(16),
        .COUNTER_WIDTH(16)
    ) carrier_gen (
        .clk(clk),
        .rst_n(rst_n),
        .enable(enable_gated),
        .freq_div(freq_div),
        .carrier1(carrier1),      // -32768 to -16384 (H-bridge 1)
        .carrier2(carrier2),      // -16384 to 0       (H-bridge 2)
        .carrier3(carrier3),      // 0 to +16384       (H-bridge 3)
        .carrier4(carrier4),      // +16384 to +32767  (H-bridge 4)
        .sync_pulse(carrier_sync)
    );

    //==========================================================================
    // Sine Generator
    //==========================================================================

    wire signed [15:0] sine_ref;

    sine_generator #(
        .DATA_WIDTH(16),
        .PHASE_WIDTH(32),
        .LUT_ADDR_WIDTH(8)
    ) sine_gen (
        .clk(clk),
        .rst_n(rst_n),
        .enable(enable),
        .freq_increment({8'd0, sine_freq, 8'd0}),  // FIXED: Use middle 16 bits for finer frequency control
        .modulation_index(mod_index),
        .sine_out(sine_ref),
        .phase()  // Not used
    );

    // Reference selection (auto sine or CPU-provided)
    wire signed [15:0] reference = mode ? $signed(cpu_reference) : sine_ref;

    //==========================================================================
    // PWM Comparators (4 instances for 8 outputs)
    //==========================================================================

    // H-Bridge 1 (S1, S1') - uses carrier1 (-32768 to -16384)
    pwm_comparator #(
        .DATA_WIDTH(16)
    ) pwm_comp1 (
        .clk(clk),
        .rst_n(rst_n),
        .enable(enable_gated),
        .reference(reference),
        .carrier(carrier1),
        .deadtime(deadtime_cycles),
        .pwm_high(pwm_out[0]),
        .pwm_low(pwm_out[1])
    );

    // H-Bridge 2 (S2, S2') - uses carrier2 (-16384 to 0)
    pwm_comparator #(
        .DATA_WIDTH(16)
    ) pwm_comp2 (
        .clk(clk),
        .rst_n(rst_n),
        .enable(enable_gated),
        .reference(reference),
        .carrier(carrier2),
        .deadtime(deadtime_cycles),
        .pwm_high(pwm_out[2]),
        .pwm_low(pwm_out[3])
    );

    // H-Bridge 3 (S3, S3') - uses carrier3 (0 to +16384)
    pwm_comparator #(
        .DATA_WIDTH(16)
    ) pwm_comp3 (
        .clk(clk),
        .rst_n(rst_n),
        .enable(enable_gated),
        .reference(reference),
        .carrier(carrier3),
        .deadtime(deadtime_cycles),
        .pwm_high(pwm_out[4]),
        .pwm_low(pwm_out[5])
    );

    // H-Bridge 4 (S4, S4') - uses carrier4 (+16384 to +32767)
    pwm_comparator #(
        .DATA_WIDTH(16)
    ) pwm_comp4 (
        .clk(clk),
        .rst_n(rst_n),
        .enable(enable_gated),
        .reference(reference),
        .carrier(carrier4),
        .deadtime(deadtime_cycles),
        .pwm_high(pwm_out[6]),
        .pwm_low(pwm_out[7])
    );

    //==========================================================================
    // Wishbone Bus Interface
    //==========================================================================

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            enable <= 1'b0;
            mode <= 1'b0;
            freq_div <= CLK_FREQ / (PWM_FREQ * 65536);
            mod_index <= 16'd0;
            sine_phase <= 32'd0;
            sine_freq <= 16'd1310;
            deadtime_cycles <= 16'd50;
            cpu_reference <= 16'd0;
            wb_ack <= 1'b0;
            wb_dat_o <= 32'd0;
        end else begin
            wb_ack <= wb_stb && !wb_ack;  // Acknowledge after one cycle

            if (wb_stb && wb_we && !wb_ack) begin
                // Write
                case (wb_addr[7:2])
                    6'h00: begin
                        enable <= wb_dat_i[0];
                        mode <= wb_dat_i[1];
                    end
                    6'h01: freq_div <= wb_dat_i[15:0];
                    6'h02: mod_index <= wb_dat_i[15:0];
                    6'h03: sine_phase <= wb_dat_i;
                    6'h04: sine_freq <= wb_dat_i[15:0];
                    6'h05: deadtime_cycles <= wb_dat_i[15:0];
                    6'h08: cpu_reference <= wb_dat_i[15:0];  // 0x20 (for manual mode)
                endcase
            end else if (wb_stb && !wb_we && !wb_ack) begin
                // Read
                case (wb_addr[7:2])
                    6'h00: wb_dat_o <= {30'd0, mode, enable};
                    6'h01: wb_dat_o <= {16'd0, freq_div};
                    6'h02: wb_dat_o <= {16'd0, mod_index};
                    6'h03: wb_dat_o <= sine_phase;
                    6'h04: wb_dat_o <= {16'd0, sine_freq};
                    6'h05: wb_dat_o <= {16'd0, deadtime_cycles};
                    6'h06: wb_dat_o <= {31'd0, carrier_sync};  // STATUS
                    6'h07: wb_dat_o <= {24'd0, pwm_out};       // PWM_OUT
                    6'h08: wb_dat_o <= {16'd0, cpu_reference};
                    default: wb_dat_o <= 32'h0;
                endcase
            end
        end
    end

endmodule
