-- ipbus_example
--
-- selection of different IPBus slaves without actual function,
-- just for performance evaluation of the IPbus/uhal system
--
-- Kristian Harder, March 2014
-- based on code by Dave Newbold, February 2011

library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use work.ipbus.all;
use work.ipbus_reg_types.all;
use work.ipbus_decode_ipbus_example.all;

entity ipbus_slaves is
	port(
		ipb_clk: in std_logic;
		ipb_rst: in std_logic;
		ipb_in: in ipb_wbus;
		ipb_out: out ipb_rbus;
		nuke: out std_logic;
		soft_rst: out std_logic;
		--i2c_scl_b: INOUT  std_logic;
        --i2c_sda_b: INOUT  std_logic;
        
        --i2c_sda_i: IN std_logic;
        --i2c_scl_i: IN std_logic;
        --i2c_scl_enb_o: OUT std_logic;
        --i2c_sda_enb_o: OUT std_logic;
                
        i2c_sda_i: IN std_logic_vector(N_I2C_CORES - 1 downto 0);
        i2c_scl_i: IN std_logic_vector(N_I2C_CORES - 1 downto 0);
        i2c_scl_enb_o: OUT std_logic_vector(N_I2C_CORES - 1 downto 0);
        i2c_sda_enb_o: OUT std_logic_vector(N_I2C_CORES - 1 downto 0);
        userled: out std_logic
	);

end ipbus_slaves;

architecture rtl of ipbus_slaves is

	signal ipbw: ipb_wbus_array(N_SLAVES - 1 downto 0);
	signal ipbr: ipb_rbus_array(N_SLAVES - 1 downto 0);
	signal ctrl, stat: ipb_reg_v(0 downto 0);
    --SIGNAL s_i2c_scl_enb         : std_logic;
    --SIGNAL s_i2c_sda_enb         : std_logic;
           
    -->P
    COMPONENT i2c_master
    PORT (
       i2c_scl_i     : IN     std_logic;
       i2c_sda_i     : IN     std_logic;
       ipbus_clk_i   : IN     std_logic;
       ipbus_i       : IN     ipb_wbus;
       ipbus_reset_i : IN     std_logic;
       i2c_scl_enb_o : OUT    std_logic;
       i2c_sda_enb_o : OUT    std_logic;
       ipbus_o       : OUT    ipb_rbus
    );
    END COMPONENT i2c_master;
    FOR ALL : i2c_master USE ENTITY work.i2c_master;--<P
begin

-- ipbus address decode
    --i2c_scl_b <= '0' when (s_i2c_scl_enb = '0') else 'Z';
    --i2c_sda_b <= '0' when (s_i2c_sda_enb = '0') else 'Z';
		
	fabric: entity work.ipbus_fabric_sel
    generic map(
    	NSLV => N_SLAVES,
    	SEL_WIDTH => IPBUS_SEL_WIDTH)
    port map(
      ipb_in => ipb_in,
      ipb_out => ipb_out,
      sel => ipbus_sel_ipbus_example(ipb_in.ipb_addr),
      ipb_to_slaves => ipbw,
      ipb_from_slaves => ipbr
    );

-- Slave 0: id / rst reg

	slave0: entity work.ipbus_ctrlreg_v
		port map(
			clk => ipb_clk,
			reset => ipb_rst,
			ipbus_in => ipbw(N_SLV_CTRL_REG),
			ipbus_out => ipbr(N_SLV_CTRL_REG),
			d => stat,
			q => ctrl
		);
		stat(0) <= X"abcdfedc";
		soft_rst <= ctrl(0)(0);
		nuke <= ctrl(0)(1);

-- Slave 1: register
	slave1: entity work.ipbus_reg_v
		port map(
			clk => ipb_clk,
			reset => ipb_rst,
			ipbus_in => ipbw(N_SLV_REG),
			ipbus_out => ipbr(N_SLV_REG),
			q => open
		);

-- Slave 2: 1kword RAM
--	slave4: entity work.ipbus_ram
--		generic map(ADDR_WIDTH => 10)
--		port map(
--			clk => ipb_clk,
--			reset => ipb_rst,
--			ipbus_in => ipbw(N_SLV_RAM),
--			ipbus_out => ipbr(N_SLV_RAM)
--		);
	
-- Slave 3: peephole RAM
--	slave5: entity work.ipbus_peephole_ram
--		generic map(ADDR_WIDTH => 10)
--		port map(
--			clk => ipb_clk,
--			reset => ipb_rst,
--			ipbus_in => ipbw(N_SLV_PRAM),
--			ipbus_out => ipbr(N_SLV_PRAM)
--		);
--    slave6 : i2c_master
--    PORT MAP (
--         i2c_scl_i     => i2c_scl_b,
--         i2c_sda_i     => i2c_sda_b,
--         ipbus_clk_i   => ipb_clk,
--         ipbus_i       => ipbw(N_SLV_I2C),
--         ipbus_reset_i => ipb_rst,
--         i2c_scl_enb_o => s_i2c_scl_enb,
--         i2c_sda_enb_o => s_i2c_sda_enb,
--         ipbus_o       => ipbr(N_SLV_I2C)
--    );

    -- Instantiate a I2C core for the EEPROM
    slave6 : i2c_master
    PORT MAP (
         i2c_scl_i     => i2c_scl_i(0),
         i2c_sda_i     => i2c_sda_i(0),
         ipbus_clk_i   => ipb_clk,
         ipbus_i       => ipbw(N_SLV_I2C_0),
         ipbus_reset_i => ipb_rst,
         i2c_scl_enb_o => i2c_scl_enb_o(0),
         i2c_sda_enb_o => i2c_sda_enb_o(0),
         ipbus_o       => ipbr(N_SLV_I2C_0)
    );
    slave7 : i2c_master
    PORT MAP (
         i2c_scl_i     => i2c_scl_i(1),
         i2c_sda_i     => i2c_sda_i(1),
         ipbus_clk_i   => ipb_clk,
         ipbus_i       => ipbw(N_SLV_I2C_1),
         ipbus_reset_i => ipb_rst,
         i2c_scl_enb_o => i2c_scl_enb_o(1),
         i2c_sda_enb_o => i2c_sda_enb_o(1),
         ipbus_o       => ipbr(N_SLV_I2C_1)
    );
    slave8 : i2c_master
    PORT MAP (
         i2c_scl_i     => i2c_scl_i(2),
         i2c_sda_i     => i2c_sda_i(2),
         ipbus_clk_i   => ipb_clk,
         ipbus_i       => ipbw(N_SLV_I2C_2),
         ipbus_reset_i => ipb_rst,
         i2c_scl_enb_o => i2c_scl_enb_o(2),
         i2c_sda_enb_o => i2c_sda_enb_o(2),
         ipbus_o       => ipbr(N_SLV_I2C_2)
    );
end rtl;
