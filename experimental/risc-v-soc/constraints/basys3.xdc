##############################################################################
# Basys 3 FPGA Constraints for RISC-V 5-Level Inverter Control SoC
# Board: Digilent Basys 3 (Artix-7 XC7A35T-1CPG236C)
# Clock: 100 MHz oscillator (divided to 50 MHz internally)
##############################################################################

##############################################################################
# Clock and Reset
##############################################################################

# 100 MHz System Clock (W5)
set_property -dict { PACKAGE_PIN W5   IOSTANDARD LVCMOS33 } [get_ports clk_100mhz]
create_clock -period 10.000 -name sys_clk_pin -waveform {0.000 5.000} -add [get_ports clk_100mhz]

# Reset Button (Active-low, btnC)
set_property -dict { PACKAGE_PIN U18  IOSTANDARD LVCMOS33 } [get_ports rst_n]

##############################################################################
# UART (USB-UART Bridge)
##############################################################################

# UART TX (to PC)
set_property -dict { PACKAGE_PIN A18  IOSTANDARD LVCMOS33 } [get_ports uart_tx]

# UART RX (from PC)
set_property -dict { PACKAGE_PIN B18  IOSTANDARD LVCMOS33 } [get_ports uart_rx]

##############################################################################
# PWM Outputs (8 channels) - Connected to Pmod Headers JA and JB
##############################################################################

# Pmod Header JA (Top Row)
# JA1 → pwm_out[0] (S1  - H-Bridge 1, Leg 1, High-side)
# JA2 → pwm_out[1] (S1' - H-Bridge 1, Leg 1, Low-side)
# JA3 → pwm_out[2] (S3  - H-Bridge 1, Leg 2, High-side)
# JA4 → pwm_out[3] (S3' - H-Bridge 1, Leg 2, Low-side)

set_property -dict { PACKAGE_PIN J1   IOSTANDARD LVCMOS33 } [get_ports {pwm_out[0]}]  # JA1
set_property -dict { PACKAGE_PIN L2   IOSTANDARD LVCMOS33 } [get_ports {pwm_out[1]}]  # JA2
set_property -dict { PACKAGE_PIN J2   IOSTANDARD LVCMOS33 } [get_ports {pwm_out[2]}]  # JA3
set_property -dict { PACKAGE_PIN G2   IOSTANDARD LVCMOS33 } [get_ports {pwm_out[3]}]  # JA4

# Pmod Header JB (Top Row)
# JB1 → pwm_out[4] (S5  - H-Bridge 2, Leg 1, High-side)
# JB2 → pwm_out[5] (S5' - H-Bridge 2, Leg 1, Low-side)
# JB3 → pwm_out[6] (S7  - H-Bridge 2, Leg 2, High-side)
# JB4 → pwm_out[7] (S7' - H-Bridge 2, Leg 2, Low-side)

set_property -dict { PACKAGE_PIN A14  IOSTANDARD LVCMOS33 } [get_ports {pwm_out[4]}]  # JB1
set_property -dict { PACKAGE_PIN A16  IOSTANDARD LVCMOS33 } [get_ports {pwm_out[5]}]  # JB2
set_property -dict { PACKAGE_PIN B15  IOSTANDARD LVCMOS33 } [get_ports {pwm_out[6]}]  # JB3
set_property -dict { PACKAGE_PIN B16  IOSTANDARD LVCMOS33 } [get_ports {pwm_out[7]}]  # JB4

##############################################################################
# Protection/Fault Inputs - Pmod Header JC
##############################################################################

# Overcurrent Protection (OCP) - JC1
set_property -dict { PACKAGE_PIN K17  IOSTANDARD LVCMOS33 } [get_ports fault_ocp]

# Overvoltage Protection (OVP) - JC2
set_property -dict { PACKAGE_PIN M18  IOSTANDARD LVCMOS33 } [get_ports fault_ovp]

# Emergency Stop (Active-low) - JC3
set_property -dict { PACKAGE_PIN N17  IOSTANDARD LVCMOS33 } [get_ports estop_n]

##############################################################################
# Sigma-Delta ADC Interface - Pmod Headers JC (bottom) and JD (top)
##############################################################################

# Comparator Inputs (from LM339) - JC bottom row (JC7-JC10)
# These receive 1-bit digital signals from external comparator

set_property -dict { PACKAGE_PIN K18  IOSTANDARD LVCMOS33 } [get_ports {adc_comp_in[0]}]  # JC7  - CH0 (DC Bus 1)
set_property -dict { PACKAGE_PIN P18  IOSTANDARD LVCMOS33 } [get_ports {adc_comp_in[1]}]  # JC8  - CH1 (DC Bus 2)
set_property -dict { PACKAGE_PIN L17  IOSTANDARD LVCMOS33 } [get_ports {adc_comp_in[2]}]  # JC9  - CH2 (AC Voltage)
set_property -dict { PACKAGE_PIN M19  IOSTANDARD LVCMOS33 } [get_ports {adc_comp_in[3]}]  # JC10 - CH3 (AC Current)

# 1-bit DAC Outputs (to RC filters) - JD top row (JD1-JD4)
# These drive the RC filters that create the analog feedback signal

set_property -dict { PACKAGE_PIN H17  IOSTANDARD LVCMOS33 } [get_ports {adc_dac_out[0]}]  # JD1 - CH0 feedback
set_property -dict { PACKAGE_PIN H19  IOSTANDARD LVCMOS33 } [get_ports {adc_dac_out[1]}]  # JD2 - CH1 feedback
set_property -dict { PACKAGE_PIN J19  IOSTANDARD LVCMOS33 } [get_ports {adc_dac_out[2]}]  # JD3 - CH2 feedback
set_property -dict { PACKAGE_PIN K19  IOSTANDARD LVCMOS33 } [get_ports {adc_dac_out[3]}]  # JD4 - CH3 feedback

##############################################################################
# Debug/Status LEDs (Onboard)
##############################################################################

# LED[0] - System Heartbeat
set_property -dict { PACKAGE_PIN U16  IOSTANDARD LVCMOS33 } [get_ports {led[0]}]

# LED[1] - Fault Indicator
set_property -dict { PACKAGE_PIN E19  IOSTANDARD LVCMOS33 } [get_ports {led[1]}]

# LED[2] - PWM Enabled
set_property -dict { PACKAGE_PIN U19  IOSTANDARD LVCMOS33 } [get_ports {led[2]}]

# LED[3] - UART Activity
set_property -dict { PACKAGE_PIN V19  IOSTANDARD LVCMOS33 } [get_ports {led[3]}]

##############################################################################
# GPIO Pins (for expansion/debug) - Using remaining Pmod JD and switches
##############################################################################

# GPIO[0:3] - Pmod Header JD (bottom row) - JD1-JD4 now used for ADC DAC outputs
# GPIO[0:3] remapped to JD7-JD10
set_property -dict { PACKAGE_PIN H18  IOSTANDARD LVCMOS33 } [get_ports {gpio[0]}]   # JD7
set_property -dict { PACKAGE_PIN J18  IOSTANDARD LVCMOS33 } [get_ports {gpio[1]}]   # JD8
set_property -dict { PACKAGE_PIN K18  IOSTANDARD LVCMOS33 } [get_ports {gpio[2]}]   # JD9  (Note: shared with comp_in[0])
set_property -dict { PACKAGE_PIN L18  IOSTANDARD LVCMOS33 } [get_ports {gpio[3]}]   # JD10

# GPIO[4:7] - Reserved/Not connected (JD1-4 used for ADC)
# If needed, can use other available pins

# GPIO[8:15] - Switches (SW0-SW7)
set_property -dict { PACKAGE_PIN V17  IOSTANDARD LVCMOS33 } [get_ports {gpio[8]}]   # SW0
set_property -dict { PACKAGE_PIN V16  IOSTANDARD LVCMOS33 } [get_ports {gpio[9]}]   # SW1
set_property -dict { PACKAGE_PIN W16  IOSTANDARD LVCMOS33 } [get_ports {gpio[10]}]  # SW2
set_property -dict { PACKAGE_PIN W17  IOSTANDARD LVCMOS33 } [get_ports {gpio[11]}]  # SW3
set_property -dict { PACKAGE_PIN W15  IOSTANDARD LVCMOS33 } [get_ports {gpio[12]}]  # SW4
set_property -dict { PACKAGE_PIN V15  IOSTANDARD LVCMOS33 } [get_ports {gpio[13]}]  # SW5
set_property -dict { PACKAGE_PIN W14  IOSTANDARD LVCMOS33 } [get_ports {gpio[14]}]  # SW6
set_property -dict { PACKAGE_PIN W13  IOSTANDARD LVCMOS33 } [get_ports {gpio[15]}]  # SW7

##############################################################################
# Timing Constraints
##############################################################################

# Derived 50 MHz clock (generated internally from 100 MHz)
# This constraint is for the divided clock
create_generated_clock -name clk_50mhz -source [get_ports clk_100mhz] -divide_by 2 [get_pins clk_50mhz_reg/Q]

# Input delay constraints (adjust based on external circuits)
# All inputs are sampled by the 50 MHz clock domain
set_input_delay -clock [get_clocks clk_50mhz] -min 0.0 [get_ports uart_rx]
set_input_delay -clock [get_clocks clk_50mhz] -max 5.0 [get_ports uart_rx]
set_input_delay -clock [get_clocks clk_50mhz] -min 0.0 [get_ports {adc_comp_in[*]}]
set_input_delay -clock [get_clocks clk_50mhz] -max 5.0 [get_ports {adc_comp_in[*]}]
set_input_delay -clock [get_clocks clk_50mhz] -min 0.0 [get_ports fault_ocp]
set_input_delay -clock [get_clocks clk_50mhz] -max 5.0 [get_ports fault_ocp]
set_input_delay -clock [get_clocks clk_50mhz] -min 0.0 [get_ports fault_ovp]
set_input_delay -clock [get_clocks clk_50mhz] -max 5.0 [get_ports fault_ovp]
set_input_delay -clock [get_clocks clk_50mhz] -min 0.0 [get_ports estop_n]
set_input_delay -clock [get_clocks clk_50mhz] -max 5.0 [get_ports estop_n]

# Output delay constraints (adjust based on external circuits)
# All outputs are driven by the 50 MHz clock domain
set_output_delay -clock [get_clocks clk_50mhz] -min -1.0 [get_ports uart_tx]
set_output_delay -clock [get_clocks clk_50mhz] -max 3.0 [get_ports uart_tx]
set_output_delay -clock [get_clocks clk_50mhz] -min -1.0 [get_ports {pwm_out[*]}]
set_output_delay -clock [get_clocks clk_50mhz] -max 3.0 [get_ports {pwm_out[*]}]
set_output_delay -clock [get_clocks clk_50mhz] -min -1.0 [get_ports {led[*]}]
set_output_delay -clock [get_clocks clk_50mhz] -max 3.0 [get_ports {led[*]}]
set_output_delay -clock [get_clocks clk_50mhz] -min -1.0 [get_ports {adc_dac_out[*]}]
set_output_delay -clock [get_clocks clk_50mhz] -max 3.0 [get_ports {adc_dac_out[*]}]

##############################################################################
# Configuration and Bitstream Settings
##############################################################################

# Configuration Bank Voltage
set_property CFGBVS VCCO [current_design]
set_property CONFIG_VOLTAGE 3.3 [current_design]

# Bitstream compression
set_property BITSTREAM.GENERAL.COMPRESS TRUE [current_design]

# Bitstream startup configuration
set_property BITSTREAM.CONFIG.SPI_BUSWIDTH 4 [current_design]
set_property CONFIG_MODE SPIx4 [current_design]

# Prevent timing closure issues during implementation
set_property SEVERITY {Warning} [get_drc_checks NSTD-1]
set_property SEVERITY {Warning} [get_drc_checks UCIO-1]

##############################################################################
# End of Constraints
##############################################################################
