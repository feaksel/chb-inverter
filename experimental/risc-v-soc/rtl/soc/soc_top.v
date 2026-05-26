/**
 * @file soc_top.v
 * @brief Top-level RISC-V SoC for 5-Level Inverter Control (Custom Core)
 *
 * Integrates all components of the RISC-V-based inverter control system:
 * - Custom RV32IM CPU core with Zpec extension
 * - 32 KB ROM (firmware storage)
 * - 64 KB RAM (runtime data)
 * - PWM accelerator peripheral (8 channels with dead-time)
 * - Sigma-Delta ADC peripheral (4-channel integrated)
 * - Protection/fault peripheral (OCP, OVP, E-stop, watchdog)
 * - Timer peripheral
 * - GPIO peripheral (32 pins)
 * - UART peripheral (debug/communication)
 * - Wishbone bus interconnect
 *
 * Target: Digilent Basys 3 (Xilinx Artix-7 XC7A35T)
 * Clock: 50 MHz (from 100 MHz oscillator with divider)
 * ASIC-ready: Technology-independent design
 *
 * This SoC is designed for DROP-IN replacement of VexRiscv.
 * Simply implement custom_riscv_core.v and custom_core_wrapper.v
 * to match the interface, and everything else works!
 *
 * @author Custom RISC-V Core Team
 * @date 2025-12-03
 * @version 1.0 - Adapted from VexRiscv SoC for custom core
 */

module soc_top #(
    parameter CLK_FREQ = 50_000_000,   // 50 MHz system clock
    parameter UART_BAUD = 115200       // UART baud rate
)(
    // Clock and Reset
    input  wire        clk_100mhz,     // Basys 3 100 MHz oscillator
    input  wire        rst_n,          // Active-low reset button

    // UART
    input  wire        uart_rx,
    output wire        uart_tx,

    // PWM Outputs (to H-bridge gate drivers)
    output wire [7:0]  pwm_out,

    // Sigma-Delta ADC Interface (4 channels)
    // Comparator inputs from LM339 (external quad comparator)
    input  wire [3:0]  adc_comp_in,    // Comparator inputs (1-bit per channel)
    // DAC outputs to RC filters (1-bit per channel)
    output wire [3:0]  adc_dac_out,

    // Protection Inputs
    input  wire        fault_ocp,      // Overcurrent protection
    input  wire        fault_ovp,      // Overvoltage protection
    input  wire        estop_n,        // Emergency stop (active low)

    // GPIO (LEDs, switches, debug)
    inout  wire [15:0] gpio,

    // Debug/Status LEDs
    output wire [3:0]  led             // Status indicators
);

    //==========================================================================
    // Clock Generation
    //==========================================================================

    /**
     * Generate 50 MHz system clock from 100 MHz Basys 3 oscillator.
     * For FPGA: Use PLL/MMCM for better jitter performance.
     * For ASIC: Replace with PLL or use external 50 MHz clock.
     */

    reg clk_50mhz;
    reg clk_div;

    always @(posedge clk_100mhz or negedge rst_n) begin
        if (!rst_n) begin
            clk_div <= 1'b0;
            clk_50mhz <= 1'b0;
        end else begin
            clk_div <= ~clk_div;
            if (clk_div)
                clk_50mhz <= ~clk_50mhz;
        end
    end

    wire clk = clk_50mhz;  // System clock

    //==========================================================================
    // Reset Synchronization
    //==========================================================================

    reg [2:0] rst_sync;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            rst_sync <= 3'b000;
        else
            rst_sync <= {rst_sync[1:0], 1'b1};
    end

    wire rst_n_sync = rst_sync[2];

    //==========================================================================
    // CPU (Custom RISC-V Core)
    //==========================================================================

    /**
     * Custom RV32IM core with Zpec extension.
     *
     * The wrapper provides the same Wishbone interface as vexriscv_wrapper,
     * making this a DROP-IN replacement. Internally, your custom core can
     * use cmd/rsp or native Wishbone - the wrapper handles conversion.
     *
     * TO INTEGRATE YOUR CUSTOM CORE:
     * 1. Implement custom_riscv_core.v (RV32IM + Zpec)
     * 2. Implement custom_core_wrapper.v (matches VexRiscv interface)
     * 3. Add both files to the build system
     * 4. Synthesize and test!
     *
     * Everything else (peripherals, memory, bus) is READY TO GO.
     */

    wire [31:0] cpu_ibus_addr;
    wire        cpu_ibus_cyc;
    wire        cpu_ibus_stb;
    wire        cpu_ibus_ack;
    wire [31:0] cpu_ibus_dat;

    wire [31:0] cpu_dbus_addr;
    wire [31:0] cpu_dbus_dat_o;
    wire [31:0] cpu_dbus_dat_i;
    wire        cpu_dbus_we;
    wire [3:0]  cpu_dbus_sel;
    wire        cpu_dbus_cyc;
    wire        cpu_dbus_stb;
    wire        cpu_dbus_ack;
    wire        cpu_dbus_err;

    wire [31:0] cpu_interrupts;

    // CHANGE THIS LINE when you have custom_core_wrapper ready:
    // For now, this references a placeholder module
    custom_core_wrapper cpu (
        .clk(clk),
        .rst_n(rst_n_sync),

        // Instruction bus (Wishbone)
        .ibus_addr(cpu_ibus_addr),
        .ibus_cyc(cpu_ibus_cyc),
        .ibus_stb(cpu_ibus_stb),
        .ibus_ack(cpu_ibus_ack),
        .ibus_dat_i(cpu_ibus_dat),

        // Data bus (Wishbone)
        .dbus_addr(cpu_dbus_addr),
        .dbus_dat_o(cpu_dbus_dat_o),
        .dbus_dat_i(cpu_dbus_dat_i),
        .dbus_we(cpu_dbus_we),
        .dbus_sel(cpu_dbus_sel),
        .dbus_cyc(cpu_dbus_cyc),
        .dbus_stb(cpu_dbus_stb),
        .dbus_ack(cpu_dbus_ack),
        .dbus_err(cpu_dbus_err),

        // Interrupts
        .external_interrupt(cpu_interrupts)
    );

    //==========================================================================
    // Memory: ROM (32 KB)
    //==========================================================================

    // ROM is accessed from BOTH instruction bus (ibus) and data bus (dbus)
    // - ibus: for code fetch
    // - dbus: for constant data reads (via interconnect)
    // Simple priority arbiter: ibus has priority

    wire [14:0] rom_addr_dbus;   // From data bus (via interconnect)
    wire        rom_stb_dbus;    // From data bus
    wire        rom_ack_dbus;    // To data bus

    wire [31:0] rom_dat_o;
    wire        rom_ack;

    // Instruction bus request
    wire rom_req_ibus = cpu_ibus_stb && cpu_ibus_cyc;

    // ROM arbiter: prioritize instruction bus
    wire [14:0] rom_addr_mux = rom_req_ibus ? cpu_ibus_addr[14:0] : rom_addr_dbus;
    wire        rom_stb_mux  = rom_req_ibus ? rom_req_ibus : rom_stb_dbus;

    rom_32kb #(
        .MEM_FILE("firmware/firmware.hex")
    ) rom (
        .clk(clk),
        .addr(rom_addr_mux),
        .stb(rom_stb_mux),
        .data_out(rom_dat_o),
        .ack(rom_ack)
    );

    // Route ack to appropriate bus
    assign cpu_ibus_dat = rom_dat_o;
    assign cpu_ibus_ack = rom_req_ibus ? rom_ack : 1'b0;
    assign rom_ack_dbus = !rom_req_ibus ? rom_ack : 1'b0;

    //==========================================================================
    // Memory: RAM (64 KB)
    //==========================================================================

    wire [15:0] ram_addr;
    wire [31:0] ram_dat_i;
    wire [31:0] ram_dat_o;
    wire        ram_we;
    wire [3:0]  ram_sel;
    wire        ram_stb;
    wire        ram_ack;

    ram_64kb ram (
        .clk(clk),
        .addr(ram_addr),
        .data_in(ram_dat_i),
        .data_out(ram_dat_o),
        .we(ram_we),
        .be(ram_sel),
        .stb(ram_stb),
        .ack(ram_ack)
    );

    //==========================================================================
    // Peripherals: PWM Accelerator
    //==========================================================================

    wire [7:0]  pwm_addr;
    wire [31:0] pwm_dat_i;
    wire [31:0] pwm_dat_o;
    wire        pwm_we;
    wire [3:0]  pwm_sel;
    wire        pwm_stb;
    wire        pwm_ack;
    wire        pwm_disable;

    pwm_accelerator #(
        .CLK_FREQ(CLK_FREQ)
    ) pwm_periph (
        .clk(clk),
        .rst_n(rst_n_sync),
        .wb_addr(pwm_addr),
        .wb_dat_i(pwm_dat_i),
        .wb_dat_o(pwm_dat_o),
        .wb_we(pwm_we),
        .wb_sel(pwm_sel),
        .wb_stb(pwm_stb),
        .wb_ack(pwm_ack),
        .pwm_out(pwm_out),
        .fault(pwm_disable)
    );

    //==========================================================================
    // Peripherals: Sigma-Delta ADC (4-Channel)
    //==========================================================================

    wire [7:0]  adc_addr;
    wire [31:0] adc_dat_i;
    wire [31:0] adc_dat_o;
    wire        adc_we;
    wire [3:0]  adc_sel;
    wire        adc_stb;
    wire        adc_ack;
    wire        adc_irq;

    sigma_delta_adc #(
        .CLK_FREQ(CLK_FREQ),
        .OSR(100),              // 100× oversampling (1 MHz → 10 kHz)
        .CIC_ORDER(3)           // 3rd-order CIC filter
    ) adc_periph (
        .clk(clk),
        .rst_n(rst_n_sync),
        .wb_addr(adc_addr),
        .wb_dat_i(adc_dat_i),
        .wb_dat_o(adc_dat_o),
        .wb_we(adc_we),
        .wb_sel(adc_sel),
        .wb_stb(adc_stb),
        .wb_ack(adc_ack),
        .comp_in(adc_comp_in),     // External comparator inputs
        .dac_out(adc_dac_out),     // 1-bit DAC outputs
        .irq(adc_irq)
    );

    //==========================================================================
    // Peripherals: Protection/Fault
    //==========================================================================

    wire [7:0]  prot_addr;
    wire [31:0] prot_dat_i;
    wire [31:0] prot_dat_o;
    wire        prot_we;
    wire [3:0]  prot_sel;
    wire        prot_stb;
    wire        prot_ack;
    wire        prot_irq;

    protection prot_periph (
        .clk(clk),
        .rst_n(rst_n_sync),
        .wb_addr(prot_addr),
        .wb_dat_i(prot_dat_i),
        .wb_dat_o(prot_dat_o),
        .wb_we(prot_we),
        .wb_sel(prot_sel),
        .wb_stb(prot_stb),
        .wb_ack(prot_ack),
        .fault_ocp(fault_ocp),
        .fault_ovp(fault_ovp),
        .estop_n(estop_n),
        .pwm_disable(pwm_disable),
        .irq(prot_irq)
    );

    //==========================================================================
    // Peripherals: Timer
    //==========================================================================

    wire [7:0]  timer_addr;
    wire [31:0] timer_dat_i;
    wire [31:0] timer_dat_o;
    wire        timer_we;
    wire [3:0]  timer_sel;
    wire        timer_stb;
    wire        timer_ack;
    wire        timer_irq;

    timer #(
        .CLK_FREQ(CLK_FREQ)
    ) timer_periph (
        .clk(clk),
        .rst_n(rst_n_sync),
        .wb_addr(timer_addr),
        .wb_dat_i(timer_dat_i),
        .wb_dat_o(timer_dat_o),
        .wb_we(timer_we),
        .wb_sel(timer_sel),
        .wb_stb(timer_stb),
        .wb_ack(timer_ack),
        .irq(timer_irq)
    );

    //==========================================================================
    // Peripherals: GPIO
    //==========================================================================

    wire [7:0]  gpio_addr;
    wire [31:0] gpio_dat_i_bus;
    wire [31:0] gpio_dat_o_bus;
    wire        gpio_we;
    wire [3:0]  gpio_sel;
    wire        gpio_stb;
    wire        gpio_ack;

    wire [31:0] gpio_in;
    wire [31:0] gpio_out;
    wire [31:0] gpio_oe;

    gpio gpio_periph (
        .clk(clk),
        .rst_n(rst_n_sync),
        .wb_addr(gpio_addr),
        .wb_dat_i(gpio_dat_i_bus),
        .wb_dat_o(gpio_dat_o_bus),
        .wb_we(gpio_we),
        .wb_sel(gpio_sel),
        .wb_stb(gpio_stb),
        .wb_ack(gpio_ack),
        .gpio_in(gpio_in),
        .gpio_out(gpio_out),
        .gpio_oe(gpio_oe)
    );

    // Connect GPIO pins (bidirectional)
    assign gpio = gpio_oe[15:0] ? gpio_out[15:0] : 16'hZZZZ;
    assign gpio_in[15:0] = gpio;
    assign gpio_in[31:16] = 16'd0;  // Unused pins

    //==========================================================================
    // Peripherals: UART
    //==========================================================================

    wire [7:0]  uart_addr;
    wire [31:0] uart_dat_i_bus;
    wire [31:0] uart_dat_o_bus;
    wire        uart_we;
    wire [3:0]  uart_sel;
    wire        uart_stb;
    wire        uart_ack;
    wire        uart_irq;

    uart #(
        .CLK_FREQ(CLK_FREQ),
        .DEFAULT_BAUD(UART_BAUD)
    ) uart_periph (
        .clk(clk),
        .rst_n(rst_n_sync),
        .wb_addr(uart_addr),
        .wb_dat_i(uart_dat_i_bus),
        .wb_dat_o(uart_dat_o_bus),
        .wb_we(uart_we),
        .wb_sel(uart_sel),
        .wb_stb(uart_stb),
        .wb_ack(uart_ack),
        .uart_rx(uart_rx),
        .uart_tx(uart_tx),
        .irq(uart_irq)
    );

    //==========================================================================
    // Wishbone Bus Interconnect
    //==========================================================================

    wishbone_interconnect bus_interconnect (
        .clk(clk),
        .rst_n(rst_n_sync),

        // Master (CPU data bus)
        .m_wb_addr(cpu_dbus_addr),
        .m_wb_dat_i(cpu_dbus_dat_o),
        .m_wb_dat_o(cpu_dbus_dat_i),
        .m_wb_we(cpu_dbus_we),
        .m_wb_sel(cpu_dbus_sel),
        .m_wb_stb(cpu_dbus_stb),
        .m_wb_cyc(cpu_dbus_cyc),
        .m_wb_ack(cpu_dbus_ack),
        .m_wb_err(cpu_dbus_err),

        // Slave: ROM (data bus access only)
        .rom_addr(rom_addr_dbus),
        .rom_stb(rom_stb_dbus),
        .rom_dat_o(rom_dat_o),
        .rom_ack(rom_ack_dbus),

        // Slave: RAM
        .ram_addr(ram_addr),
        .ram_dat_i(ram_dat_i),
        .ram_dat_o(ram_dat_o),
        .ram_we(ram_we),
        .ram_sel(ram_sel),
        .ram_stb(ram_stb),
        .ram_ack(ram_ack),

        // Slave: PWM
        .pwm_addr(pwm_addr),
        .pwm_dat_i(pwm_dat_i),
        .pwm_dat_o(pwm_dat_o),
        .pwm_we(pwm_we),
        .pwm_sel(pwm_sel),
        .pwm_stb(pwm_stb),
        .pwm_ack(pwm_ack),

        // Slave: ADC
        .adc_addr(adc_addr),
        .adc_dat_i(adc_dat_i),
        .adc_dat_o(adc_dat_o),
        .adc_we(adc_we),
        .adc_sel(adc_sel),
        .adc_stb(adc_stb),
        .adc_ack(adc_ack),

        // Slave: Protection
        .prot_addr(prot_addr),
        .prot_dat_i(prot_dat_i),
        .prot_dat_o(prot_dat_o),
        .prot_we(prot_we),
        .prot_sel(prot_sel),
        .prot_stb(prot_stb),
        .prot_ack(prot_ack),

        // Slave: Timer
        .timer_addr(timer_addr),
        .timer_dat_i(timer_dat_i),
        .timer_dat_o(timer_dat_o),
        .timer_we(timer_we),
        .timer_sel(timer_sel),
        .timer_stb(timer_stb),
        .timer_ack(timer_ack),

        // Slave: GPIO
        .gpio_addr(gpio_addr),
        .gpio_dat_i(gpio_dat_i_bus),
        .gpio_dat_o(gpio_dat_o_bus),
        .gpio_we(gpio_we),
        .gpio_sel(gpio_sel),
        .gpio_stb(gpio_stb),
        .gpio_ack(gpio_ack),

        // Slave: UART
        .uart_addr(uart_addr),
        .uart_dat_i(uart_dat_i_bus),
        .uart_dat_o(uart_dat_o_bus),
        .uart_we(uart_we),
        .uart_sel(uart_sel),
        .uart_stb(uart_stb),
        .uart_ack(uart_ack)
    );

    //==========================================================================
    // Interrupt Aggregation
    //==========================================================================

    assign cpu_interrupts = {
        27'd0,
        uart_irq,      // [4]
        timer_irq,     // [3]
        prot_irq,      // [2]
        adc_irq,       // [1]
        1'b0           // [0] - reserved
    };

    //==========================================================================
    // Status LEDs
    //==========================================================================

    assign led[0] = rst_n_sync;         // Power indicator
    assign led[1] = pwm_disable;        // Fault indicator
    assign led[2] = uart_tx;            // UART TX activity
    assign led[3] = |cpu_interrupts;    // Interrupt active

endmodule
