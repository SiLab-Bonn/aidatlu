set_property BITSTREAM.GENERAL.COMPRESS TRUE [current_design]

proc false_path {patt clk} {
    set p [get_ports -quiet $patt -filter {direction != out}]
    if {[llength $p] != 0} {
        set_input_delay 0 -clock [get_clocks $clk] [get_ports $patt -filter {direction != out}]
        set_false_path -from [get_ports $patt -filter {direction != out}]
    }
    set p [get_ports -quiet $patt -filter {direction != in}]
    if {[llength $p] != 0} {
       	set_output_delay 0 -clock [get_clocks $clk] [get_ports $patt -filter {direction != in}]
	    set_false_path -to [get_ports $patt -filter {direction != in}]
	}
}

# System clock (50MHz)
#create_clock -period 25.000 -name sysclk [get_ports sysclk] 
create_clock -period 20.000 -name clk_enclustra [get_ports clk_enclustra]

set_false_path -through [get_pins infra/clocks/rst_reg/Q]
set_false_path -through [get_nets infra/clocks/nuke_i]

set_property IOSTANDARD LVCMOS33 [get_ports clk_enclustra]
set_property PACKAGE_PIN P17 [get_ports clk_enclustra]

set_property IOSTANDARD LVCMOS33 [get_ports {leds[*]}]
set_property SLEW SLOW [get_ports {leds[*]}]
set_property PACKAGE_PIN M16 [get_ports {leds[0]}]
set_property PACKAGE_PIN M17 [get_ports {leds[1]}]
set_property PACKAGE_PIN L18 [get_ports {leds[2]}]
set_property PACKAGE_PIN M18 [get_ports {leds[3]}]
false_path {leds[*]} clk_enclustra

set_property IOSTANDARD LVCMOS33 [get_ports {rgmii_* phy_rstn}]
set_property PACKAGE_PIN R18 [get_ports {rgmii_txd[0]}]
set_property PACKAGE_PIN T18 [get_ports {rgmii_txd[1]}]
set_property PACKAGE_PIN U17 [get_ports {rgmii_txd[2]}]
set_property PACKAGE_PIN U18 [get_ports {rgmii_txd[3]}]
set_property PACKAGE_PIN T16 [get_ports {rgmii_tx_ctl}]
set_property PACKAGE_PIN N16 [get_ports {rgmii_txc}]
set_property PACKAGE_PIN U16 [get_ports {rgmii_rxd[0]}]
set_property PACKAGE_PIN V17 [get_ports {rgmii_rxd[1]}]
set_property PACKAGE_PIN V15 [get_ports {rgmii_rxd[2]}]
set_property PACKAGE_PIN V16 [get_ports {rgmii_rxd[3]}]
set_property PACKAGE_PIN R16 [get_ports {rgmii_rx_ctl}]
set_property PACKAGE_PIN T14 [get_ports {rgmii_rxc}]
set_property PACKAGE_PIN M13 [get_ports {phy_rstn}]
false_path {phy_rstn} clk_enclustra

# -------------------------------------------------------------------------------------------------


