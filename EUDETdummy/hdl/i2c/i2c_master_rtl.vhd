--=============================================================================
--! @file i2c_master_rtl.vhd
--=============================================================================
--
-------------------------------------------------------------------------------
-- --
-- University of Bristol, High Energy Physics Group.
-- --
------------------------------------------------------------------------------- --
-- VHDL Architecture work.i2c_master.rtl
--
--! @brief Wraps the Wishbone I2C master in a wrapper where the IPBus signals\n
--! are bundled together in a record\n
--
--! @author David Cussans , David.Cussans@bristol.ac.uk
--
--! @date 17:22:12 11/30/12
--
--! @version v0.1
--
--! @details
--!
--!
--! <b>Dependencies:</b>\n
--!
--! <b>References:</b>\n
--!
--! <b>Modified by:</b>\n
--! Author: 
-------------------------------------------------------------------------------
--! \n\n<b>Last changes:</b>\n
-------------------------------------------------------------------------------
--! @todo <next thing to do> \n
--! <another thing to do> \n
--
--------------------------------------------------------------------------------
-- 
-- Created using using Mentor Graphics HDL Designer(TM) 2010.3 (Build 21)
--
LIBRARY ieee;
USE ieee.std_logic_1164.all;
USE ieee.numeric_std.all;

USE work.ipbus.all;

ENTITY i2c_master IS
   PORT( 
      i2c_scl_i     : IN     std_logic;
      i2c_sda_i     : IN     std_logic;
      ipbus_clk_i   : IN     std_logic;
      ipbus_i       : IN     ipb_wbus;    -- Signals from IPBus core to slave
      ipbus_reset_i : IN     std_logic;
      i2c_scl_enb_o : OUT    std_logic;
      i2c_sda_enb_o : OUT    std_logic;
      ipbus_o       : OUT    ipb_rbus     -- signals from slave to IPBus core
   );

-- Declarations

END ENTITY i2c_master ;

--
ARCHITECTURE rtl OF i2c_master IS
  
  --signal s_i2c_scl, s_i2c_scl_o, s_i2c_scl_enb, s_i2c_sda, s_i2c_sda_enb : std_logic ;
  
BEGIN
  
  --i2c_scl_b <= s_i2c_scl when (s_i2c_scl_enb = '0') else 'Z';
  --i2c_sda_b <= s_i2c_sda when (s_i2c_sda_enb = '0') else 'Z';

  i2c_interface: entity work.i2c_master_top port map(
                wb_clk_i => ipbus_clk_i,
                wb_rst_i => ipbus_reset_i,
                arst_i => '1',
                wb_adr_i => ipbus_i.ipb_addr(2 downto 0),
                wb_dat_i => ipbus_i.ipb_wdata(7 downto 0),
                wb_dat_o => ipbus_o.ipb_rdata(7 downto 0),
                wb_we_i => ipbus_i.ipb_write,
                wb_stb_i => ipbus_i.ipb_strobe,
                wb_cyc_i => '1',
                wb_ack_o => ipbus_o.ipb_ack,
                wb_inta_o => open,
                scl_pad_i => i2c_scl_i,
                scl_pad_o => open,
                scl_padoen_o => i2c_scl_enb_o,
                sda_pad_i => i2c_sda_i,
                sda_pad_o => open,
                sda_padoen_o => i2c_sda_enb_o
        );
        
  
  ipbus_o.ipb_rdata(31 downto 8) <= ( others => '0');
  ipbus_o.ipb_err <= '0'; -- never return an error.
  
END ARCHITECTURE rtl;

