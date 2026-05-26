// rv32im_integrated_macro_stub.v
// This defines the interface for Genus to treat the CPU as a Black Box.

module rv32im_integrated_macro (
    clk, 
    rst_n, 
    iwb_adr_o, 
    iwb_dat_i, 
    iwb_cyc_o, 
    iwb_stb_o, 
    iwb_ack_i, 
    dwb_adr_o, 
    dwb_dat_o, 
    dwb_dat_i, 
    dwb_we_o, 
    dwb_sel_o, 
    dwb_cyc_o, 
    dwb_stb_o, 
    dwb_ack_i, 
    dwb_err_i, 
    interrupts
);
   input clk;
   input rst_n;
   output [31:0] iwb_adr_o;
   input [31:0] iwb_dat_i;
   output iwb_cyc_o;
   output iwb_stb_o;
   input iwb_ack_i;
   output [31:0] dwb_adr_o;
   output [31:0] dwb_dat_o;
   input [31:0] dwb_dat_i;
   output dwb_we_o;
   output [3:0] dwb_sel_o;
   output dwb_cyc_o;
   output dwb_stb_o;
   input dwb_ack_i;
   input dwb_err_i;
   input [31:0] interrupts;
endmodule
