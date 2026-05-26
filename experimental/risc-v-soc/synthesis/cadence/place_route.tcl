#===============================================================================
# Cadence Innovus Place & Route Script
# For: Custom RISC-V Core (RV32IM)
# Target: School technology library
#===============================================================================

# Note: Update paths for your school's setup
set TECH_LIB_PATH "/path/to/school/technology/library"
set DESIGN_PATH "outputs"

#===============================================================================
# Initialize
#===============================================================================

puts "Initializing Innovus..."

# Set paths
set init_lef_file "$TECH_LIB_PATH/tech.lef"
set init_verilog "$DESIGN_PATH/netlist.v"
set init_design_netlist "$DESIGN_PATH/netlist.v"
set init_top_cell custom_core_wrapper

# Power/ground nets
set init_pwr_net VDD
set init_gnd_net VSS

# Technology file
set init_mmmc_file mmmc.tcl

# Read design
init_design

#===============================================================================
# Floorplan
#===============================================================================

puts "Creating floorplan..."

# Create floorplan
# Utilization: 0.7 = 70% (leave 30% for routing)
# Aspect ratio: 1.0 = square chip
# Core to IO spacing: 10 microns
floorPlan -site core -r 0.7 1.0 10 10 10 10

# Or specify absolute size (if you know it)
# floorPlan -site core -s 200 200 10 10 10 10  # 200x200 microns

# View floorplan
# gui_show

#===============================================================================
# Power Planning
#===============================================================================

puts "Adding power rings and stripes..."

# Add power rings around core
addRing -nets {VDD VSS} \
        -width 2 \
        -spacing 1 \
        -layer {top metal5 bottom metal5 left metal6 right metal6}

# Add power stripes
addStripe -nets {VDD VSS} \
          -layer metal4 \
          -direction vertical \
          -width 1 \
          -spacing 1 \
          -number_of_sets 4

addStripe -nets {VDD VSS} \
          -layer metal3 \
          -direction horizontal \
          -width 1 \
          -spacing 1 \
          -number_of_sets 4

# Special route (connect power/ground)
sroute -connect { blockPin padPin padRing corePin floatingStripe } \
       -layerChangeRange { metal1 metal6 } \
       -blockPinTarget { nearestTarget } \
       -padPinPortConnect { allPort oneGeom } \
       -padPinTarget { nearestTarget } \
       -corePinTarget { firstAfterRowEnd } \
       -floatingStripeTarget { blockring padring ring stripe ringpin blockpin followpin } \
       -allowJogging 1 \
       -crossoverViaLayerRange { metal1 metal6 } \
       -nets { VDD VSS } \
       -allowLayerChange 1 \
       -blockPin useLef \
       -targetViaLayerRange { metal1 metal6 }

#===============================================================================
# Placement
#===============================================================================

puts "Placing standard cells..."

# Set placement mode
setPlaceMode -fp false

# Place design
placeDesign

# Add filler cells (to fill gaps between cells)
# Update cell names based on your library
addFiller -cell {FILL1 FILL2 FILL4 FILL8} -prefix FILLER

# Optimize placement
refinePlace

# Check placement
checkPlace

#===============================================================================
# Pre-CTS Optimization
#===============================================================================

puts "Pre-CTS optimization..."

# Set optimization mode
setOptMode -fixCap true -fixTran true -fixFanoutLoad true

# Optimize
optDesign -preCTS

#===============================================================================
# Clock Tree Synthesis
#===============================================================================

puts "Synthesizing clock tree..."

# Create clock tree spec
create_ccopt_clock_tree_spec -file ccopt.spec

# Set CTS mode
set_ccopt_mode -integration true

# Run CTS
ccopt_design

#===============================================================================
# Post-CTS Optimization
#===============================================================================

puts "Post-CTS optimization..."

optDesign -postCTS

# Hold time fixing
optDesign -postCTS -hold

#===============================================================================
# Routing
#===============================================================================

puts "Routing design..."

# Set routing mode
setNanoRouteMode -quiet -drouteFixAntenna true
setNanoRouteMode -quiet -routeWithTimingDriven true
setNanoRouteMode -quiet -routeWithSiDriven true

# Global routing
globalNetConnect VDD -type pgpin -pin VDD -inst * -override
globalNetConnect VSS -type pgpin -pin VSS -inst * -override

# Route design
routeDesign

#===============================================================================
# Post-Route Optimization
#===============================================================================

puts "Post-route optimization..."

# Optimize timing
optDesign -postRoute

# Fix hold violations
optDesign -postRoute -hold

# Final optimization
optDesign -postRoute -incr

#===============================================================================
# Filler Cells (if not done earlier)
#===============================================================================

# Add/update filler if needed
# deleteFiller -prefix FILLER
# addFiller -cell {FILL1 FILL2 FILL4 FILL8} -prefix FILLER

#===============================================================================
# Verification
#===============================================================================

puts "Verifying design..."

# Create reports directory
exec mkdir -p reports

# Verify connectivity
verify_connectivity -report reports/connectivity.rpt

# Verify geometry
verify_geometry -report reports/geometry.rpt

# Check DRC
verify_drc -report reports/drc.rpt -limit 1000

#===============================================================================
# Reports
#===============================================================================

puts "Generating reports..."

# Timing reports
report_timing -nworst 10 > reports/post_route_timing.rpt
report_timing -nworst 10 -path_type full > reports/post_route_timing_full.rpt

# Setup timing
report_timing -late > reports/setup_timing.rpt

# Hold timing
report_timing -early > reports/hold_timing.rpt

# Area report
report_area > reports/post_route_area.rpt

# Power report
report_power > reports/post_route_power.rpt

# Summary
summaryReport -outfile reports/summary.rpt

# Clock tree report
report_ccopt_clock_trees -file reports/clock_tree.rpt

#===============================================================================
# Extract Parasitics
#===============================================================================

puts "Extracting parasitics..."

# Extract RC
extractRC

# Write SDF for post-layout simulation
write_sdf outputs/post_route.sdf

#===============================================================================
# Save Design
#===============================================================================

puts "Saving design..."

# Save design database
saveDesign final_design.enc

#===============================================================================
# Generate Outputs
#===============================================================================

puts "Generating output files..."

# GDSII stream file
# Update map file path based on your library
streamOut outputs/design.gds \
          -mapFile $TECH_LIB_PATH/gds.map \
          -stripes 1 \
          -units 1000 \
          -mode ALL

# Netlist (with physical info)
saveNetlist outputs/post_route_netlist.v

# DEF file
defOut -floorplan -netlist -routing outputs/design.def

# LEF file (for hierarchical design)
# lefOut outputs/design.lef

#===============================================================================
# Screenshots for Report
#===============================================================================

puts "Taking screenshots..."

# Show full chip
fit
# Take screenshot: File -> Save Image -> PNG

# Show zoomed view
zoomBox 50 50 150 150
# Take screenshot

# Show detail view
zoomBox 75 75 125 125
# Take screenshot

#===============================================================================
# Summary
#===============================================================================

puts "\n========================================="
puts "Place & Route Complete!"
puts "========================================="
puts ""
puts "Check reports:"
puts "  reports/drc.rpt              - DRC violations (should be 0)"
puts "  reports/connectivity.rpt     - Connectivity check"
puts "  reports/post_route_timing.rpt - Final timing"
puts "  reports/post_route_area.rpt  - Final area"
puts "  reports/post_route_power.rpt - Final power"
puts ""
puts "Output files:"
puts "  outputs/design.gds           - GDSII layout"
puts "  outputs/post_route_netlist.v - Final netlist"
puts "  outputs/design.def           - DEF file"
puts "  outputs/post_route.sdf       - Timing delays"
puts ""
puts "To view layout:"
puts "  1. In Innovus GUI: File -> Load Design"
puts "  2. In Virtuoso: Open outputs/design.gds"
puts ""
puts "For report, include:"
puts "  1. Floorplan screenshot"
puts "  2. Full chip layout"
puts "  3. Zoomed cell view"
puts "  4. Clock tree visualization"
puts "  5. Timing/area/power numbers"
puts ""
puts "If DRC violations exist:"
puts "  1. Check reports/drc.rpt for details"
puts "  2. May need to adjust floorplan or routing"
puts "  3. Consult with TA/professor"
puts ""
puts "========================================="

# Open GUI for viewing (if not already open)
# gui_show
