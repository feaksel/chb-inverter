module pwm_accelerator_macro (
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
	pwm_out, 
	pwm_out_n, 
	irq, 
	pwm_sync_out, 
	pwm_sync_in, 
	pwm_status);
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
   output [7:0] pwm_out;
   output [7:0] pwm_out_n;
   output irq;
   output pwm_sync_out;
   input pwm_sync_in;
   output [31:0] pwm_status;
endmodule
