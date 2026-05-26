
module gpio_core (
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
	gpio, 
	irq, 
	FE_OFN15_rst_n, 
	FE_OFN10_rst_n, 
	FE_OFN3_rst_n, 
	FE_OFN0_rst_n, 
	FE_OFN21_FE_OFN0_rst_n, 
	clk_clone6, 
	clk_clone5, 
	clk_clone4, 
	clk_clone3, 
	clk_clone2, 
	clk_clone1, 
	clk);
   input rst_n;
   input [7:0] wb_adr_i;
   output [31:0] wb_dat_o;
   input [31:0] wb_dat_i;
   input wb_we_i;
   input [3:0] wb_sel_i;
   input wb_cyc_i;
   input wb_stb_i;
   output wb_ack_o;
   output wb_err_o;
   inout [15:0] gpio;
   output irq;
   input FE_OFN15_rst_n;
   input FE_OFN10_rst_n;
   input FE_OFN3_rst_n;
   input FE_OFN0_rst_n;
   input FE_OFN21_FE_OFN0_rst_n;
   input clk_clone6;
   input clk_clone5;
   input clk_clone4;
   input clk_clone3;
   input clk_clone2;
   input clk_clone1;
   input clk;

endmodule
