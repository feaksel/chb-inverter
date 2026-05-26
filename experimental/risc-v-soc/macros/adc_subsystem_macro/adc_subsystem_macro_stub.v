module adc_subsystem_macro (
	clk, 
	rst_n, 
	wb_adr_i, 
	wb_dat_o, 
	wb_dat_i, 
	wb_we_i, 
	wb_sel_i, 
	wb_cyc_i, 
	wb_stb_i, 
	wb_ack_o, 
	wb_err_o, 
	adc_data_in, 
	adc_clk_out, 
	ch0_data, 
	ch1_data, 
	ch2_data, 
	ch3_data, 
	data_valid, 
	irq, 
	adc_status);
   input clk;
   input rst_n;
   input [31:0] wb_adr_i;
   output [31:0] wb_dat_o;
   input [31:0] wb_dat_i;
   input wb_we_i;
   input [3:0] wb_sel_i;
   input wb_cyc_i;
   input wb_stb_i;
   output wb_ack_o;
   output wb_err_o;
   input [3:0] adc_data_in;
   output [3:0] adc_clk_out;
   output [15:0] ch0_data;
   output [15:0] ch1_data;
   output [15:0] ch2_data;
   output [15:0] ch3_data;
   output [3:0] data_valid;
   output irq;
   output [31:0] adc_status;
endmodule
