/**
 * @file custom_core_wrapper.v
 * @brief Wrapper for Custom RV32IM Core - Simple Passthrough (Approach 2)
 *
 * This wrapper provides the exact same Wishbone interface as vexriscv_wrapper.v,
 * making it a DROP-IN replacement. Since the custom core uses native Wishbone
 * (Approach 2), this wrapper is just a simple passthrough with no conversion.
 *
 * IMPLEMENTATION APPROACH: Native Wishbone (Approach 2)
 * - Core uses Wishbone natively
 * - Wrapper just connects signals directly
 * - No protocol conversion needed
 * - Clean and simple!
 *
 * @author Custom RISC-V Core Team
 * @date 2025-12-03
 * @version 0.2 - Approach 2: Passthrough Wrapper
 */

module custom_core_wrapper (
    input  wire        clk,
    input  wire        rst_n,

    //==========================================================================
    // Wishbone Instruction Bus (master) - TO SoC
    //==========================================================================

    output wire [31:0] ibus_addr,
    output wire        ibus_cyc,
    output wire        ibus_stb,
    input  wire        ibus_ack,
    input  wire [31:0] ibus_dat_i,

    //==========================================================================
    // Wishbone Data Bus (master) - TO SoC
    //==========================================================================

    output wire [31:0] dbus_addr,
    output wire [31:0] dbus_dat_o,
    input  wire [31:0] dbus_dat_i,
    output wire        dbus_we,
    output wire [3:0]  dbus_sel,
    output wire        dbus_cyc,
    output wire        dbus_stb,
    input  wire        dbus_ack,
    input  wire        dbus_err,

    //==========================================================================
    // Interrupts
    //==========================================================================

    input  wire [31:0] external_interrupt
);

    //==========================================================================
    // APPROACH 2: SIMPLE PASSTHROUGH
    //==========================================================================

    /**
     * Since custom_riscv_core uses native Wishbone (Approach 2),
     * this wrapper is extremely simple - just connect signals!
     *
     * No protocol conversion needed.
     * No state machines needed.
     * Just wire connections!
     *
     * This is the beauty of using standard Wishbone natively.
     */

    //==========================================================================
    // Custom Core Instantiation
    //==========================================================================

    custom_riscv_core #(
        .RESET_VECTOR(32'h00000000)  // Start of ROM
    ) cpu (
        .clk(clk),
        .rst_n(rst_n),

        // Instruction Wishbone Bus - Direct connection!
        .iwb_adr_o(ibus_addr),
        .iwb_dat_i(ibus_dat_i),
        .iwb_cyc_o(ibus_cyc),
        .iwb_stb_o(ibus_stb),
        .iwb_ack_i(ibus_ack),

        // Data Wishbone Bus - Direct connection!
        .dwb_adr_o(dbus_addr),
        .dwb_dat_o(dbus_dat_o),
        .dwb_dat_i(dbus_dat_i),
        .dwb_we_o(dbus_we),
        .dwb_sel_o(dbus_sel),
        .dwb_cyc_o(dbus_cyc),
        .dwb_stb_o(dbus_stb),
        .dwb_ack_i(dbus_ack),
        .dwb_err_i(dbus_err),

        // Interrupts
        .interrupts(external_interrupt)
    );

    //==========================================================================
    // That's it! No conversion logic needed for Approach 2.
    //==========================================================================

    /**
     * Compare this to Approach 1 (cmd/rsp):
     * - Approach 1 needs ~100 lines of conversion logic
     * - Approach 2 needs ~5 lines (just wire connections)
     *
     * This is why Approach 2 is cleaner and more reusable!
     */

    // Synthesis-time info
    // synthesis translate_off
    initial begin
        $display("");
        $display("=================================================================");
        $display("INFO: custom_core_wrapper - Approach 2 (Simple Passthrough)");
        $display("=================================================================");
        $display("This wrapper uses DIRECT WISHBONE passthrough.");
        $display("");
        $display("Advantages:");
        $display("  - No protocol conversion needed");
        $display("  - Just ~5 lines of wire connections");
        $display("  - Clean and easy to understand");
        $display("  - Zero latency overhead");
        $display("");
        $display("The core (custom_riscv_core.v) uses native Wishbone,");
        $display("so this wrapper is just a passthrough module.");
        $display("=================================================================");
        $display("");
    end
    // synthesis translate_on

endmodule
