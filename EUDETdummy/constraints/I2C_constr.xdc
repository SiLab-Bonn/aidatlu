set_property IOSTANDARD LVCMOS33 [get_ports i2c_reset]
set_property PACKAGE_PIN C2 [get_ports i2c_reset]

set_property IOSTANDARD LVCMOS33 [get_ports i2c_scl_b]
set_property PACKAGE_PIN N17 [get_ports i2c_scl_b]

set_property IOSTANDARD LVCMOS33 [get_ports i2c_sda_b]
set_property PACKAGE_PIN P18 [get_ports i2c_sda_b]



create_clock -period 25.000 -name sysclk_40_i_p -waveform {0.000 12.500} [get_ports sysclk_40_i_p]
#set_property ASYNC_REG true [get_cells I1/sync_registers/s_ring_d4_reg]
#set_property ASYNC_REG true [get_cells I1/sync_registers/s_ring_d3_reg]
#set_property ASYNC_REG true [get_cells I1/sync_ipbus/s_ring_d0_reg]
#set_property ASYNC_REG true [get_cells I1/sync_ipbus/s_ring_d1_reg]

#set_clock_groups -asynchronous -group [get_clocks pll_base_inst_n_2] -group [get_clocks mmcm_n_8]
#set_property ASYNC_REG true [get_cells I1/sync_ipbus/s_ring_d3_reg]
#set_property ASYNC_REG true [get_cells I1/sync_ipbus/s_ring_d4_reg]
#set_property ASYNC_REG true [get_cells I6/s_logic_reset_d1_reg]
#set_property ASYNC_REG true [get_cells I6/s_logic_reset_d2_reg]
#set_property ASYNC_REG true [get_cells I1/sync_registers/s_ring_d1_reg]
#set_property ASYNC_REG true [get_cells I1/sync_registers/s_ring_d0_reg]
#set_clock_groups -asynchronous -group [get_clocks mmcm_n_8] -group [get_clocks pll_base_inst_n_2]


#Define clock groups and make them asynchronous with each other
set_clock_groups -asynchronous -group {clk_enclustra I_1 mmcm_n_10 mmcm_n_6 mmcm_n_8 clk_ipb_i} -group {sysclk_40_i_p I pll_base_inst_n_2 s_clk160}

# -------------------------------------------------------------------------------------------------



#DEBUG PROBES





