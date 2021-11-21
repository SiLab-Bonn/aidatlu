## Trigger inputs

#set_property IOSTANDARD LVCMOS18 [get_ports {threshold_discr_p_i[*]}]
#set_property PACKAGE_PIN J4 [get_ports {threshold_discr_p_i[4]}]
#set_property PACKAGE_PIN H1 [get_ports {threshold_discr_p_i[5]}]

#set_property IOSTANDARD LVCMOS33 [get_ports {threshold_discr_n_i[*]}]
#set property IOSTANDARD LVDS_25 [get_ports {threshold_discr_p_i[*]}]
#set_property PACKAGE_PIN B1 [get_ports {threshold_discr_p_i[0]}]
#set_property PACKAGE_PIN A1 [get_ports {threshold_discr_n_i[0]}]
#set_property PACKAGE_PIN C4 [get_ports {threshold_discr_p_i[1]}]
#set_property PACKAGE_PIN B4 [get_ports {threshold_discr_n_i[1]}]
#set_property PACKAGE_PIN K2 [get_ports {threshold_discr_p_i[2]}]
#set_property PACKAGE_PIN K1 [get_ports {threshold_discr_n_i[2]}]
#set_property PACKAGE_PIN C6 [get_ports {threshold_discr_p_i[3]}]
#set_property PACKAGE_PIN C5 [get_ports {threshold_discr_n_i[3]}]
#set_property PACKAGE_PIN J4 [get_ports {threshold_discr_p_i[4]}]
#set_property PACKAGE_PIN H4 [get_ports {threshold_discr_n_i[4]}]
#set_property PACKAGE_PIN H1 [get_ports {threshold_discr_p_i[5]}]
#set_property PACKAGE_PIN G1 [get_ports {threshold_discr_n_i[5]}]

## Miscellaneous I/O
set_property IOSTANDARD LVCMOS33 [get_ports clk_gen_rst]
set_property PACKAGE_PIN C1 [get_ports clk_gen_rst]
set_property IOSTANDARD LVCMOS33 [get_ports gpio]
set_property PACKAGE_PIN F6 [get_ports gpio]


## Crystal clock
set_property IOSTANDARD LVDS_25 [get_ports sysclk_40_i_p]
set_property PACKAGE_PIN T5 [get_ports sysclk_40_i_p]
set_property PACKAGE_PIN T4 [get_ports sysclk_40_i_n]

## Output clock (currently not working so set to 0)
set_property IOSTANDARD LVCMOS33 [get_ports sysclk_50_o_p]
set_property PACKAGE_PIN E3 [get_ports sysclk_50_o_p]
set_property IOSTANDARD LVCMOS33 [get_ports sysclk_50_o_n]
set_property PACKAGE_PIN D3 [get_ports sysclk_50_o_n]

## Inputs/Outputs for DUTs
set_property IOSTANDARD LVCMOS33 [get_ports {busy_o[*]}]
set_property PACKAGE_PIN R7 [get_ports {busy_o[0]}]
set_property PACKAGE_PIN U4 [get_ports {busy_o[1]}]
set_property PACKAGE_PIN R8 [get_ports {busy_o[2]}]
set_property PACKAGE_PIN K5 [get_ports {busy_o[3]}]

set_property IOSTANDARD LVCMOS33 [get_ports {triggers_o[*]}]
set_property PACKAGE_PIN R6 [get_ports {triggers_o[0]}]
set_property PACKAGE_PIN P2 [get_ports {triggers_o[1]}]
set_property PACKAGE_PIN R1 [get_ports {triggers_o[2]}]
set_property PACKAGE_PIN U1 [get_ports {triggers_o[3]}]

set_property IOSTANDARD LVCMOS33 [get_ports {cont_o[*]}]
set_property PACKAGE_PIN N5 [get_ports {cont_o[0]}]
set_property PACKAGE_PIN P4 [get_ports {cont_o[1]}]
set_property PACKAGE_PIN M6 [get_ports {cont_o[2]}]
set_property PACKAGE_PIN L6 [get_ports {cont_o[3]}]

set_property IOSTANDARD LVCMOS33 [get_ports {spare_o[*]}]
set_property PACKAGE_PIN L1 [get_ports {spare_o[0]}]
set_property PACKAGE_PIN M4 [get_ports {spare_o[1]}]
set_property PACKAGE_PIN N2 [get_ports {spare_o[2]}]
set_property PACKAGE_PIN M3 [get_ports {spare_o[3]}]

set_property IOSTANDARD LVCMOS33 [get_ports {dut_clk_o[*]}]
set_property PACKAGE_PIN K3 [get_ports {dut_clk_o[0]}]
set_property PACKAGE_PIN F4 [get_ports {dut_clk_o[1]}]
set_property PACKAGE_PIN E2 [get_ports {dut_clk_o[2]}]
set_property PACKAGE_PIN G4 [get_ports {dut_clk_o[3]}]

set_property IOSTANDARD LVCMOS33 [get_ports {cont_i[*]}]
set_property PACKAGE_PIN P5 [get_ports {cont_i[0]}]
set_property PACKAGE_PIN P3 [get_ports {cont_i[1]}]
set_property PACKAGE_PIN N6 [get_ports {cont_i[2]}]
set_property PACKAGE_PIN L5 [get_ports {cont_i[3]}]

set_property IOSTANDARD LVCMOS33 [get_ports {spare_i[*]}]
set_property PACKAGE_PIN M1 [get_ports {spare_i[0]}]
set_property PACKAGE_PIN N4 [get_ports {spare_i[1]}]
set_property PACKAGE_PIN N1 [get_ports {spare_i[2]}]
set_property PACKAGE_PIN M2 [get_ports {spare_i[3]}]

set_property IOSTANDARD LVCMOS33 [get_ports {triggers_i[*]}]
set_property PACKAGE_PIN R5 [get_ports {triggers_i[0]}]
set_property PACKAGE_PIN R2 [get_ports {triggers_i[1]}]
set_property PACKAGE_PIN T1 [get_ports {triggers_i[2]}]
set_property PACKAGE_PIN V1 [get_ports {triggers_i[3]}]

set_property IOSTANDARD LVCMOS33 [get_ports {busy_i[*]}]
set_property PACKAGE_PIN T6 [get_ports {busy_i[0]}]
set_property PACKAGE_PIN U3 [get_ports {busy_i[1]}]
set_property PACKAGE_PIN T8 [get_ports {busy_i[2]}]
set_property PACKAGE_PIN L4 [get_ports {busy_i[3]}]

set_property IOSTANDARD LVCMOS33 [get_ports {dut_clk_i[*]}]
set_property PACKAGE_PIN L3 [get_ports {dut_clk_i[0]}]
set_property PACKAGE_PIN F3 [get_ports {dut_clk_i[1]}]
set_property PACKAGE_PIN D2 [get_ports {dut_clk_i[2]}]
set_property PACKAGE_PIN G3 [get_ports {dut_clk_i[3]}]

# -------------------------------------------------------------------------------------------------






set_property BITSTREAM.CONFIG.SPI_BUSWIDTH 4 [current_design]


create_debug_core u_ila_0 ila
set_property ALL_PROBE_SAME_MU true [get_debug_cores u_ila_0]
set_property ALL_PROBE_SAME_MU_CNT 4 [get_debug_cores u_ila_0]
set_property C_ADV_TRIGGER true [get_debug_cores u_ila_0]
set_property C_DATA_DEPTH 8192 [get_debug_cores u_ila_0]
set_property C_EN_STRG_QUAL true [get_debug_cores u_ila_0]
set_property C_INPUT_PIPE_STAGES 0 [get_debug_cores u_ila_0]
set_property C_TRIGIN_EN false [get_debug_cores u_ila_0]
set_property C_TRIGOUT_EN false [get_debug_cores u_ila_0]
set_property port_width 1 [get_debug_ports u_ila_0/clk]
connect_debug_port u_ila_0/clk [get_nets [list sysclk_40_BUFG]]
set_property PROBE_TYPE DATA_AND_TRIGGER [get_debug_ports u_ila_0/probe0]
set_property port_width 32 [get_debug_ports u_ila_0/probe0]
connect_debug_port u_ila_0/probe0 [get_nets [list {TrigNArray[0][0]} {TrigNArray[0][1]} {TrigNArray[0][2]} {TrigNArray[0][3]} {TrigNArray[0][4]} {TrigNArray[0][5]} {TrigNArray[0][6]} {TrigNArray[0][7]} {TrigNArray[0][8]} {TrigNArray[0][9]} {TrigNArray[0][10]} {TrigNArray[0][11]} {TrigNArray[0][12]} {TrigNArray[0][13]} {TrigNArray[0][14]} {TrigNArray[0][15]} {TrigNArray[0][16]} {TrigNArray[0][17]} {TrigNArray[0][18]} {TrigNArray[0][19]} {TrigNArray[0][20]} {TrigNArray[0][21]} {TrigNArray[0][22]} {TrigNArray[0][23]} {TrigNArray[0][24]} {TrigNArray[0][25]} {TrigNArray[0][26]} {TrigNArray[0][27]} {TrigNArray[0][28]} {TrigNArray[0][29]} {TrigNArray[0][30]} {TrigNArray[0][31]}]]
create_debug_port u_ila_0 probe
set_property PROBE_TYPE DATA_AND_TRIGGER [get_debug_ports u_ila_0/probe1]
set_property port_width 1 [get_debug_ports u_ila_0/probe1]
connect_debug_port u_ila_0/probe1 [get_nets [list {busy_o_OBUF[0]}]]
create_debug_port u_ila_0 probe
set_property PROBE_TYPE DATA_AND_TRIGGER [get_debug_ports u_ila_0/probe2]
set_property port_width 1 [get_debug_ports u_ila_0/probe2]
connect_debug_port u_ila_0/probe2 [get_nets [list {dut_clk_o_OBUF[0]}]]
create_debug_port u_ila_0 probe
set_property PROBE_TYPE DATA_AND_TRIGGER [get_debug_ports u_ila_0/probe3]
set_property port_width 1 [get_debug_ports u_ila_0/probe3]
connect_debug_port u_ila_0/probe3 [get_nets [list TriggerNumberStrobe6_out]]
set_property C_CLK_INPUT_FREQ_HZ 300000000 [get_debug_cores dbg_hub]
set_property C_ENABLE_CLK_DIVIDER false [get_debug_cores dbg_hub]
set_property C_USER_SCAN_CHAIN 1 [get_debug_cores dbg_hub]
connect_debug_port dbg_hub/clk [get_nets sysclk_40_BUFG]
