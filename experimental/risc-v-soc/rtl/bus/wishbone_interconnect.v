/**
 * @file wishbone_interconnect.v
 * @brief Wishbone Bus Interconnect for RISC-V SoC
 *
 * Implements address decoding and multiplexing for connecting the
 * RISC-V CPU to memory and peripherals via Wishbone bus.
 *
 * Memory Map:
 * 0x0000_0000 - 0x0000_7FFF : ROM (32 KB)
 * 0x0000_8000 - 0x0001_7FFF : RAM (64 KB)
 * 0x0002_0000 - 0x0002_00FF : PWM Peripheral
 * 0x0002_0100 - 0x0002_01FF : ADC Interface
 * 0x0002_0200 - 0x0002_02FF : Protection/Fault
 * 0x0002_0300 - 0x0002_03FF : Timer
 * 0x0002_0400 - 0x0002_04FF : GPIO
 * 0x0002_0500 - 0x0002_05FF : UART
 *
 * Features:
 * - Simple priority-based arbitration (single master)
 * - Address-based peripheral selection
 * - Error response for unmapped addresses
 */

module wishbone_interconnect #(
    parameter ADDR_WIDTH = 32,
    parameter DATA_WIDTH = 32
)(
    input  wire                    clk,
    input  wire                    rst_n,

    // Master interface (CPU)
    input  wire [ADDR_WIDTH-1:0]   m_wb_addr,
    input  wire [DATA_WIDTH-1:0]   m_wb_dat_i,
    output reg  [DATA_WIDTH-1:0]   m_wb_dat_o,
    input  wire                    m_wb_we,
    input  wire [3:0]              m_wb_sel,
    input  wire                    m_wb_stb,
    input  wire                    m_wb_cyc,
    output reg                     m_wb_ack,
    output reg                     m_wb_err,

    // Slave interface: ROM
    output wire [14:0]             rom_addr,
    output wire                    rom_stb,
    input  wire [DATA_WIDTH-1:0]   rom_dat_o,
    input  wire                    rom_ack,

    // Slave interface: RAM
    output wire [15:0]             ram_addr,
    output wire [DATA_WIDTH-1:0]   ram_dat_i,
    output wire                    ram_we,
    output wire [3:0]              ram_sel,
    output wire                    ram_stb,
    input  wire [DATA_WIDTH-1:0]   ram_dat_o,
    input  wire                    ram_ack,

    // Slave interface: PWM Peripheral
    output wire [7:0]              pwm_addr,
    output wire [DATA_WIDTH-1:0]   pwm_dat_i,
    output wire                    pwm_we,
    output wire [3:0]              pwm_sel,
    output wire                    pwm_stb,
    input  wire [DATA_WIDTH-1:0]   pwm_dat_o,
    input  wire                    pwm_ack,

    // Slave interface: ADC Interface
    output wire [7:0]              adc_addr,
    output wire [DATA_WIDTH-1:0]   adc_dat_i,
    output wire                    adc_we,
    output wire [3:0]              adc_sel,
    output wire                    adc_stb,
    input  wire [DATA_WIDTH-1:0]   adc_dat_o,
    input  wire                    adc_ack,

    // Slave interface: Protection/Fault
    output wire [7:0]              prot_addr,
    output wire [DATA_WIDTH-1:0]   prot_dat_i,
    output wire                    prot_we,
    output wire [3:0]              prot_sel,
    output wire                    prot_stb,
    input  wire [DATA_WIDTH-1:0]   prot_dat_o,
    input  wire                    prot_ack,

    // Slave interface: Timer
    output wire [7:0]              timer_addr,
    output wire [DATA_WIDTH-1:0]   timer_dat_i,
    output wire                    timer_we,
    output wire [3:0]              timer_sel,
    output wire                    timer_stb,
    input  wire [DATA_WIDTH-1:0]   timer_dat_o,
    input  wire                    timer_ack,

    // Slave interface: GPIO
    output wire [7:0]              gpio_addr,
    output wire [DATA_WIDTH-1:0]   gpio_dat_i,
    output wire                    gpio_we,
    output wire [3:0]              gpio_sel,
    output wire                    gpio_stb,
    input  wire [DATA_WIDTH-1:0]   gpio_dat_o,
    input  wire                    gpio_ack,

    // Slave interface: UART
    output wire [7:0]              uart_addr,
    output wire [DATA_WIDTH-1:0]   uart_dat_i,
    output wire                    uart_we,
    output wire [3:0]              uart_sel,
    output wire                    uart_stb,
    input  wire [DATA_WIDTH-1:0]   uart_dat_o,
    input  wire                    uart_ack
);

    //==========================================================================
    // Address Decoding
    //==========================================================================

    // Memory regions
    localparam ADDR_ROM_BASE  = 32'h0000_0000;
    localparam ADDR_ROM_END   = 32'h0000_7FFF;
    localparam ADDR_RAM_BASE  = 32'h0000_8000;
    localparam ADDR_RAM_END   = 32'h0001_7FFF;

    // Peripheral regions
    localparam ADDR_PWM_BASE  = 32'h0002_0000;
    localparam ADDR_PWM_END   = 32'h0002_00FF;
    localparam ADDR_ADC_BASE  = 32'h0002_0100;
    localparam ADDR_ADC_END   = 32'h0002_01FF;
    localparam ADDR_PROT_BASE = 32'h0002_0200;
    localparam ADDR_PROT_END  = 32'h0002_02FF;
    localparam ADDR_TIMER_BASE = 32'h0002_0300;
    localparam ADDR_TIMER_END  = 32'h0002_03FF;
    localparam ADDR_GPIO_BASE = 32'h0002_0400;
    localparam ADDR_GPIO_END  = 32'h0002_04FF;
    localparam ADDR_UART_BASE = 32'h0002_0500;
    localparam ADDR_UART_END  = 32'h0002_05FF;

    // Chip select signals
    wire sel_rom   = (m_wb_addr >= ADDR_ROM_BASE)   && (m_wb_addr <= ADDR_ROM_END);
    wire sel_ram   = (m_wb_addr >= ADDR_RAM_BASE)   && (m_wb_addr <= ADDR_RAM_END);
    wire sel_pwm   = (m_wb_addr >= ADDR_PWM_BASE)   && (m_wb_addr <= ADDR_PWM_END);
    wire sel_adc   = (m_wb_addr >= ADDR_ADC_BASE)   && (m_wb_addr <= ADDR_ADC_END);
    wire sel_prot  = (m_wb_addr >= ADDR_PROT_BASE)  && (m_wb_addr <= ADDR_PROT_END);
    wire sel_timer = (m_wb_addr >= ADDR_TIMER_BASE) && (m_wb_addr <= ADDR_TIMER_END);
    wire sel_gpio  = (m_wb_addr >= ADDR_GPIO_BASE)  && (m_wb_addr <= ADDR_GPIO_END);
    wire sel_uart  = (m_wb_addr >= ADDR_UART_BASE)  && (m_wb_addr <= ADDR_UART_END);

    // Error detection (unmapped address)
    wire sel_error = !(sel_rom | sel_ram | sel_pwm | sel_adc | sel_prot | sel_timer | sel_gpio | sel_uart);

    //==========================================================================
    // ROM Interface
    //==========================================================================

    assign rom_addr = m_wb_addr[14:0];
    assign rom_stb  = m_wb_stb && m_wb_cyc && sel_rom;

    //==========================================================================
    // RAM Interface
    //==========================================================================

    assign ram_addr   = m_wb_addr[15:0];
    assign ram_dat_i  = m_wb_dat_i;
    assign ram_we     = m_wb_we;
    assign ram_sel    = m_wb_sel;
    assign ram_stb    = m_wb_stb && m_wb_cyc && sel_ram;

    //==========================================================================
    // PWM Peripheral Interface
    //==========================================================================

    assign pwm_addr   = m_wb_addr[7:0];
    assign pwm_dat_i  = m_wb_dat_i;
    assign pwm_we     = m_wb_we;
    assign pwm_sel    = m_wb_sel;
    assign pwm_stb    = m_wb_stb && m_wb_cyc && sel_pwm;

    //==========================================================================
    // ADC Interface
    //==========================================================================

    assign adc_addr   = m_wb_addr[7:0];
    assign adc_dat_i  = m_wb_dat_i;
    assign adc_we     = m_wb_we;
    assign adc_sel    = m_wb_sel;
    assign adc_stb    = m_wb_stb && m_wb_cyc && sel_adc;

    //==========================================================================
    // Protection Peripheral Interface
    //==========================================================================

    assign prot_addr  = m_wb_addr[7:0];
    assign prot_dat_i = m_wb_dat_i;
    assign prot_we    = m_wb_we;
    assign prot_sel   = m_wb_sel;
    assign prot_stb   = m_wb_stb && m_wb_cyc && sel_prot;

    //==========================================================================
    // Timer Interface
    //==========================================================================

    assign timer_addr  = m_wb_addr[7:0];
    assign timer_dat_i = m_wb_dat_i;
    assign timer_we    = m_wb_we;
    assign timer_sel   = m_wb_sel;
    assign timer_stb   = m_wb_stb && m_wb_cyc && sel_timer;

    //==========================================================================
    // GPIO Interface
    //==========================================================================

    assign gpio_addr  = m_wb_addr[7:0];
    assign gpio_dat_i = m_wb_dat_i;
    assign gpio_we    = m_wb_we;
    assign gpio_sel   = m_wb_sel;
    assign gpio_stb   = m_wb_stb && m_wb_cyc && sel_gpio;

    //==========================================================================
    // UART Interface
    //==========================================================================

    assign uart_addr  = m_wb_addr[7:0];
    assign uart_dat_i = m_wb_dat_i;
    assign uart_we    = m_wb_we;
    assign uart_sel   = m_wb_sel;
    assign uart_stb   = m_wb_stb && m_wb_cyc && sel_uart;

    //==========================================================================
    // Response Multiplexing
    //==========================================================================

    always @(*) begin
        // Default values
        m_wb_dat_o = 32'h0;
        m_wb_ack   = 1'b0;
        m_wb_err   = 1'b0;

        // Multiplex based on selected peripheral
        if (sel_rom) begin
            m_wb_dat_o = rom_dat_o;
            m_wb_ack   = rom_ack;
        end else if (sel_ram) begin
            m_wb_dat_o = ram_dat_o;
            m_wb_ack   = ram_ack;
        end else if (sel_pwm) begin
            m_wb_dat_o = pwm_dat_o;
            m_wb_ack   = pwm_ack;
        end else if (sel_adc) begin
            m_wb_dat_o = adc_dat_o;
            m_wb_ack   = adc_ack;
        end else if (sel_prot) begin
            m_wb_dat_o = prot_dat_o;
            m_wb_ack   = prot_ack;
        end else if (sel_timer) begin
            m_wb_dat_o = timer_dat_o;
            m_wb_ack   = timer_ack;
        end else if (sel_gpio) begin
            m_wb_dat_o = gpio_dat_o;
            m_wb_ack   = gpio_ack;
        end else if (sel_uart) begin
            m_wb_dat_o = uart_dat_o;
            m_wb_ack   = uart_ack;
        end else if (sel_error && m_wb_stb && m_wb_cyc) begin
            m_wb_err   = 1'b1;  // Bus error for unmapped address
        end
    end

endmodule
