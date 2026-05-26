module memory_macro (
	clk, 
	rst_n, 
	iwb_adr_i, 
	iwb_dat_o, 
	iwb_dat_i, 
	iwb_we_i, 
	iwb_sel_i, 
	iwb_cyc_i, 
	iwb_stb_i, 
	iwb_ack_o, 
	iwb_err_o, 
	dwb_adr_i, 
	dwb_dat_o, 
	dwb_dat_i, 
	dwb_we_i, 
	dwb_sel_i, 
	dwb_cyc_i, 
	dwb_stb_i, 
	dwb_ack_o, 
	dwb_err_o, 
	ext_mem_adr_o, 
	ext_mem_dat_o, 
	ext_mem_dat_i, 
	ext_mem_we_o, 
	ext_mem_sel_o, 
	ext_mem_cyc_o, 
	ext_mem_stb_o, 
	ext_mem_ack_i, 
	ext_mem_err_i, 
	rom_ready, 
	ram_ready, 
	memory_status);
   input clk;
   input rst_n;
   input [31:0] iwb_adr_i;
   output [31:0] iwb_dat_o;
   input [31:0] iwb_dat_i;
   input iwb_we_i;
   input [3:0] iwb_sel_i;
   input iwb_cyc_i;
   input iwb_stb_i;
   output iwb_ack_o;
   output iwb_err_o;
   input [31:0] dwb_adr_i;
   output [31:0] dwb_dat_o;
   input [31:0] dwb_dat_i;
   input dwb_we_i;
   input [3:0] dwb_sel_i;
   input dwb_cyc_i;
   input dwb_stb_i;
   output dwb_ack_o;
   output dwb_err_o;
   output [31:0] ext_mem_adr_o;
   output [31:0] ext_mem_dat_o;
   input [31:0] ext_mem_dat_i;
   output ext_mem_we_o;
   output [3:0] ext_mem_sel_o;
   output ext_mem_cyc_o;
   output ext_mem_stb_o;
   input ext_mem_ack_i;
   input ext_mem_err_i;
   output rom_ready;
   output ram_ready;
   output [31:0] memory_status;

endmodule
