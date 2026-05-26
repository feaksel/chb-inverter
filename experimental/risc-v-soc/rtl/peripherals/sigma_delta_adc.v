/**
 * @file sigma_delta_adc.v
 * @brief 4-Channel Sigma-Delta ADC Peripheral for RISC-V SoC
 *
 * Integrated FPGA Sigma-Delta ADC with CIC decimation filters.
 * Replaces external SPI ADC interface with on-chip ADC implementation.
 *
 * Features:
 * - 4 independent Sigma-Delta ADC channels
 * - 12-14 bit ENOB (Effective Number of Bits)
 * - 10 kHz output rate per channel
 * - 1 MHz oversampling rate (100× OSR)
 * - 3rd-order CIC decimation filter
 * - Memory-mapped register interface
 * - Continuous automatic sampling
 *
 * Register Map (Base: 0x00020100):
 * 0x00: CTRL        - Control register (enable, reset)
 * 0x04: STATUS      - Status register (data valid flags)
 * 0x08: DATA_CH0    - Channel 0 ADC data (DC Bus 1) [15:0]
 * 0x0C: DATA_CH1    - Channel 1 ADC data (DC Bus 2) [15:0]
 * 0x10: DATA_CH2    - Channel 2 ADC data (AC Voltage) [15:0]
 * 0x14: DATA_CH3    - Channel 3 ADC data (AC Current) [15:0]
 * 0x18: SAMPLE_CNT  - Sample counter (debug)
 *
 * External Interface:
 * - comp_in[3:0]    - Comparator inputs from LM339
 * - dac_out[3:0]    - 1-bit DAC outputs to RC filters
 */

module sigma_delta_adc #(
    parameter ADDR_WIDTH = 8,
    parameter CLK_FREQ = 50_000_000,
    parameter OSR = 100,                // Oversampling ratio
    parameter CIC_ORDER = 3             // CIC filter order
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

    // External comparator interface
    input  wire [3:0]              comp_in,       // From LM339 comparators
    output wire [3:0]              dac_out,       // To RC filters

    // Interrupt
    output reg                     irq            // New data available
);

    //==========================================================================
    // Control Registers
    //==========================================================================

    reg         enable;
    reg  [15:0] adc_data [0:3];         // ADC results for 4 channels
    reg  [3:0]  data_valid;             // Valid flags
    wire [3:0]  adc_data_valid;         // From ADC channels
    wire [15:0] adc_ch0, adc_ch1, adc_ch2, adc_ch3;
    reg  [31:0] sample_counter;

    initial begin
        enable = 1'b0;
        adc_data[0] = 16'd0;
        adc_data[1] = 16'd0;
        adc_data[2] = 16'd0;
        adc_data[3] = 16'd0;
        data_valid = 4'h0;
        sample_counter = 32'd0;
        irq = 1'b0;
    end

    //==========================================================================
    // Sigma-Delta ADC Channels (4× instantiation)
    //==========================================================================

    genvar i;
    generate
        for (i = 0; i < 4; i = i + 1) begin : adc_channels
            sigma_delta_channel #(
                .OSR(OSR),
                .CIC_ORDER(CIC_ORDER)
            ) adc_ch (
                .clk(clk),
                .rst_n(rst_n),
                .enable(enable),
                .comp_in(comp_in[i]),
                .dac_out(dac_out[i]),
                .adc_data(i == 0 ? adc_ch0 :
                          i == 1 ? adc_ch1 :
                          i == 2 ? adc_ch2 : adc_ch3),
                .data_valid(adc_data_valid[i])
            );
        end
    endgenerate

    //==========================================================================
    // Data Capture and Interrupt Generation
    //==========================================================================

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            adc_data[0] <= 16'd0;
            adc_data[1] <= 16'd0;
            adc_data[2] <= 16'd0;
            adc_data[3] <= 16'd0;
            data_valid <= 4'h0;
            sample_counter <= 32'd0;
            irq <= 1'b0;
        end else begin
            // Capture data when valid
            if (adc_data_valid[0]) begin
                adc_data[0] <= adc_ch0;
                data_valid[0] <= 1'b1;
            end
            if (adc_data_valid[1]) begin
                adc_data[1] <= adc_ch1;
                data_valid[1] <= 1'b1;
            end
            if (adc_data_valid[2]) begin
                adc_data[2] <= adc_ch2;
                data_valid[2] <= 1'b1;
            end
            if (adc_data_valid[3]) begin
                adc_data[3] <= adc_ch3;
                data_valid[3] <= 1'b1;
            end

            // Generate interrupt when all channels have new data
            irq <= (adc_data_valid == 4'hF);

            // Sample counter (for debug/verification)
            if (adc_data_valid[0])
                sample_counter <= sample_counter + 1;
        end
    end

    //==========================================================================
    // Wishbone Bus Interface
    //==========================================================================

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            enable <= 1'b0;
            wb_ack <= 1'b0;
            wb_dat_o <= 32'd0;
        end else begin
            wb_ack <= wb_stb && !wb_ack;

            if (wb_stb && wb_we && !wb_ack) begin
                // Write
                case (wb_addr[7:2])
                    6'h00: enable <= wb_dat_i[0];  // CTRL
                endcase
            end else if (wb_stb && !wb_we && !wb_ack) begin
                // Read
                case (wb_addr[7:2])
                    6'h00: wb_dat_o <= {31'd0, enable};                 // CTRL
                    6'h01: wb_dat_o <= {28'd0, data_valid};             // STATUS
                    6'h02: begin
                        wb_dat_o <= {16'd0, adc_data[0]};                // DATA_CH0
                        data_valid[0] <= 1'b0;  // Clear valid flag on read
                    end
                    6'h03: begin
                        wb_dat_o <= {16'd0, adc_data[1]};                // DATA_CH1
                        data_valid[1] <= 1'b0;
                    end
                    6'h04: begin
                        wb_dat_o <= {16'd0, adc_data[2]};                // DATA_CH2
                        data_valid[2] <= 1'b0;
                    end
                    6'h05: begin
                        wb_dat_o <= {16'd0, adc_data[3]};                // DATA_CH3
                        data_valid[3] <= 1'b0;
                    end
                    6'h06: wb_dat_o <= sample_counter;                   // SAMPLE_CNT
                    default: wb_dat_o <= 32'h0;
                endcase
            end
        end
    end

endmodule

//==========================================================================
// Sigma-Delta ADC Channel (Single Channel)
//==========================================================================

module sigma_delta_channel #(
    parameter OSR = 100,
    parameter CIC_ORDER = 3,
    parameter W = 32                    // Internal width
)(
    input  wire        clk,             // 50 MHz system clock
    input  wire        rst_n,
    input  wire        enable,
    input  wire        comp_in,         // Comparator input (1-bit)
    output reg         dac_out,         // 1-bit DAC output
    output wire [15:0] adc_data,        // 16-bit ADC result
    output wire        data_valid       // Data valid strobe
);

    //==========================================================================
    // Clock Divider: 50 MHz → 1 MHz (for 1 MHz sampling)
    //==========================================================================

    localparam CLK_DIV = 50;            // 50 MHz / 50 = 1 MHz

    reg [6:0] clk_div_counter;
    reg       clk_1mhz;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            clk_div_counter <= 7'd0;
            clk_1mhz <= 1'b0;
        end else if (enable) begin
            if (clk_div_counter == CLK_DIV - 1) begin
                clk_div_counter <= 7'd0;
                clk_1mhz <= ~clk_1mhz;  // Toggle at 1 MHz
            end else begin
                clk_div_counter <= clk_div_counter + 1;
            end
        end
    end

    wire clk_1mhz_posedge = (clk_div_counter == 0) && clk_1mhz && enable;

    //==========================================================================
    // Sigma-Delta Modulator (1st order)
    //==========================================================================

    reg signed [31:0] integrator;
    reg               bitstream;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            integrator <= 32'sd0;
            dac_out <= 1'b0;
            bitstream <= 1'b0;
        end else if (clk_1mhz_posedge) begin
            // Error signal = input - feedback
            integrator <= integrator +
                          (comp_in ? 32'sd32768 : -32'sd32768) -
                          (dac_out ? 32'sd32768 : -32'sd32768);

            // 1-bit quantizer
            dac_out <= (integrator >= 0);
            bitstream <= dac_out;
        end
    end

    //==========================================================================
    // CIC Decimation Filter (3rd order)
    //==========================================================================

    // Integrator stages (run at 1 MHz)
    reg [W-1:0] integrator_stage [0:CIC_ORDER-1];
    integer i;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < CIC_ORDER; i = i + 1)
                integrator_stage[i] <= 0;
        end else if (clk_1mhz_posedge) begin
            // First integrator
            integrator_stage[0] <= integrator_stage[0] + (bitstream ? 1 : 0);

            // Cascaded integrators
            for (i = 1; i < CIC_ORDER; i = i + 1)
                integrator_stage[i] <= integrator_stage[i] + integrator_stage[i-1];
        end
    end

    // Decimation counter
    reg [7:0] decim_count;
    reg [W-1:0] snapshot;
    reg snapshot_valid;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            decim_count <= 8'd0;
            snapshot <= 0;
            snapshot_valid <= 1'b0;
        end else if (clk_1mhz_posedge) begin
            decim_count <= decim_count + 1;
            snapshot_valid <= 1'b0;

            if (decim_count == OSR - 1) begin
                decim_count <= 8'd0;
                snapshot <= integrator_stage[CIC_ORDER-1];
                snapshot_valid <= 1'b1;
            end
        end
    end

    // Comb stages (run at 10 kHz)
    reg [W-1:0] comb [0:CIC_ORDER-1];
    reg [W-1:0] comb_delay [0:CIC_ORDER-1];
    reg [15:0]  adc_result;
    reg         result_valid;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < CIC_ORDER; i = i + 1) begin
                comb[i] <= 0;
                comb_delay[i] <= 0;
            end
            adc_result <= 16'd0;
            result_valid <= 1'b0;
        end else if (snapshot_valid) begin
            // First comb
            comb[0] <= snapshot - comb_delay[0];
            comb_delay[0] <= snapshot;

            // Cascaded combs
            for (i = 1; i < CIC_ORDER; i = i + 1) begin
                comb[i] <= comb[i-1] - comb_delay[i];
                comb_delay[i] <= comb[i-1];
            end

            // Output (take top 16 bits, scaled appropriately)
            adc_result <= comb[CIC_ORDER-1][W-1:W-16];
            result_valid <= 1'b1;
        end else begin
            result_valid <= 1'b0;
        end
    end

    assign adc_data = adc_result;
    assign data_valid = result_valid;

endmodule
