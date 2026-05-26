module protection_macro (
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
	current_sense, 
	voltage_sense, 
	thermal_alert, 
	emergency_stop, 
	channel_disable, 
	system_reset, 
	watchdog_kick, 
	watchdog_timeout, 
	irq, 
	protection_status);
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
   input [3:0] current_sense;
   input [3:0] voltage_sense;
   input thermal_alert;
   output emergency_stop;
   output [3:0] channel_disable;
   output system_reset;
   input watchdog_kick;
   output watchdog_timeout;
   output irq;
   output [31:0] protection_status;
endmodule
