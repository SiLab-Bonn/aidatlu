-- Top-level design for TLU v1E
--
-- This version is for Enclustra AX3 module, using the RGMII PHY on the PM3 baseboard
--
-- You must edit this file to set the IP and MAC addresses
--
-- Dave Newbold, 4/10/16--

library IEEE;
library UNISIM;
use IEEE.STD_LOGIC_1164.ALL;
use ieee.numeric_std.all;
use work.fmcTLU.all;
use work.ipbus_decode_tlu.all;
use work.ipbus.all;
use work.ipbus_reg_types.all;
use UNISIM.vcomponents.all;

--Library UNISIM;
--use UNISIM.vcomponents.all;

use work.ipbus.ALL;

entity top_EUDET_dummy is
    generic(
    constant FW_VERSION : unsigned(31 downto 0):= X"ffff0006"; -- Firmware revision. Remember to change this as needed.
    g_NUM_DUTS  : positive := 4; -- <- was 3
    g_NUM_TRIG_INPUTS   :positive := 6;-- <- was 4
    g_NUM_EDGE_INPUTS   :positive := 6;--  <-- was 4
    g_NUM_EXT_SLAVES    :positive :=8;--  <-- ??
    g_EVENT_DATA_WIDTH  :positive := 32;--  <-- ??
    g_IPBUS_WIDTH   :positive := 32;--  <-- was 32 
    g_SPILL_COUNTER_WIDTH   :positive := 12;--  <-- ??
    g_BUILD_SIMULATED_MAC   :integer := 0
    );
    port(
    --Clock
        --sysclk: in std_logic; --50 MHz clock input from FPGA
        clk_enclustra: in std_logic; --Enclustra onboard oscillator 40 MHz. Used for the IPBus block
        sysclk_50_o_p : out std_logic; --50 MHz clock output to FMC pins
        sysclk_50_o_n : out std_logic; --50 MHz clock output to FMC pins
        sysclk_40_i_p: in std_logic;
        sysclk_40_i_n: in std_logic;
    --Misc
        leds: out std_logic_vector(3 downto 0); -- status LEDs
        dip_sw: in std_logic_vector(3 downto 0); -- switches
        gpio: out std_logic; -- gpio pin on J1 (eventually make it inout)
    --RGMII interface signals
        rgmii_txd: out std_logic_vector(3 downto 0);
        rgmii_tx_ctl: out std_logic;
        rgmii_txc: out std_logic;
        rgmii_rxd: in std_logic_vector(3 downto 0);
        rgmii_rx_ctl: in std_logic;
        rgmii_rxc: in std_logic;
        phy_rstn: out std_logic; 
    --I2C bus
        i2c_scl_b: inout std_logic;
        i2c_sda_b: inout std_logic;
        i2c_reset: out std_logic; --Reset line for the expander serial lines
    --Clock generator controls
        clk_gen_rst: out std_logic; --Reset line for the Si5345 clock generator (active low)
        --clk_gen_lol: in std_logic; --LOL signal. Do not use for now as it is connected to CONT_FROM_FPGA<0>
    --TLU signals for DUTs
        busy_i: in std_logic_vector(g_NUM_DUTS-1 downto 0);-- Busy lines from DUTs (active high) (busy to FPGA)
        busy_o: out std_logic_vector(g_NUM_DUTS-1 downto 0);-- Busy lines to DUTs (active high) (busy from FPGA)
        cont_i: in std_logic_vector(g_NUM_DUTS-1 downto 0); --Control lines from DUTs
        cont_o: out std_logic_vector(g_NUM_DUTS-1 downto 0); --Control lines to DUTs
        spare_i: in std_logic_vector(g_NUM_DUTS-1 downto 0); --Spare lines from DUTs
        spare_o: out std_logic_vector(g_NUM_DUTS-1 downto 0); --Spare lines to DUTs
        triggers_i: in std_logic_vector(g_NUM_DUTS-1 downto 0); --Trigger lines from DUTs
        triggers_o: out std_logic_vector(g_NUM_DUTS-1 downto 0); --Trigger lines to DUTs
        dut_clk_i: in std_logic_vector(g_NUM_DUTS-1 downto 0); --Clock from DUTs
        dut_clk_o: out std_logic_vector(g_NUM_DUTS-1 downto 0) --Clock to DUTs
  
        
        --reset_or_clk_n_o: out std_logic_vector(g_NUM_DUTS-1 downto 0); --T0 synchronization signal
        --reset_or_clk_p_o: out std_logic_vector(g_NUM_DUTS-1 downto 0);
        --shutter_to_dut_n_o: out std_logic_vector(g_NUM_DUTS-1 downto 0); --Shutter output
        --shutter_to_dut_p_o: out std_logic_vector(g_NUM_DUTS-1 downto 0);         

    );

end top_EUDET_dummy;

architecture rtl of top_EUDET_dummy is

	signal clk_ipb, rst_ipb, nuke, soft_rst, phy_rst_e, clk_200, sysclk_40, clk_encl_buf, userled: std_logic;
	signal mac_addr: std_logic_vector(47 downto 0);
	signal ip_addr: std_logic_vector(31 downto 0);
	signal ipb_out: ipb_wbus;
	signal ipb_in: ipb_rbus;
	signal inf_leds: std_logic_vector(1 downto 0);
	signal s_i2c_scl_enb         : std_logic;
    signal s_i2c_sda_enb         : std_logic;
    signal encl_clock50: std_logic; -- This is a 50 MHz clock generated from the Enclustra onboard oscillator (rather than the clock input)
    
	--signal s_i2c_sda_i : std_logic;
	--signal s_i2c_scl_i : std_logic;
	------------------------------------------
	-- Internal signal declarations
    SIGNAL T0_o                  : std_logic;
    SIGNAL buffer_full_o         : std_logic;                                             --! Goes high when event buffer almost full
    SIGNAL clk_8x_logic         : std_logic;                                             -- 320MHz clock
    SIGNAL clk_4x_logic          : std_logic;                                             --! normally 160MHz
    SIGNAL clk_logic_xtal        : std_logic;                                             -- ! 40MHz clock from onboard xtal
    SIGNAL data_strobe           : std_logic;                                             -- goes high when data ready to load into event buffer
    SIGNAL dout                  : std_logic;
    SIGNAL dout1                 : std_logic;
    SIGNAL event_data            : std_logic_vector(g_EVENT_DATA_WIDTH-1 DOWNTO 0);
    signal ipbww: ipb_wbus_array(N_SLAVES - 1 downto 0);
    signal ipbrr: ipb_rbus_array(N_SLAVES - 1 downto 0);
    SIGNAL logic_clocks_reset    : std_logic;                                             -- Goes high to reset counters etc. Sync with clk_4x_logic
    SIGNAL logic_reset           : std_logic;
    SIGNAL overall_trigger       : std_logic;                                             --! goes high to load trigger data
    SIGNAL overall_veto          : std_logic;                                             --! Halts triggers when high
    SIGNAL postVetoTrigger_times : t_triggerTimeArray(g_NUM_TRIG_INPUTS-1 DOWNTO 0);      -- ! trigger arrival time ( w.r.t. logic_strobe)
    SIGNAL postVetotrigger       : std_logic_vector(g_NUM_TRIG_INPUTS-1 DOWNTO 0);        -- ! High when trigger from input connector active and enabled
    --trigger_count_i   : IN     std_logic_vector (g_IPBUS_WIDTH-1 DOWNTO 0); --! Not used yet.
    SIGNAL rst_fifo_o            : std_logic;                                             --! rst signal to first level fifos
    SIGNAL s_edge_fall_times     : t_triggerTimeArray(g_NUM_EDGE_INPUTS-1 DOWNTO 0);      -- Array of edge times ( w.r.t. logic_strobe)
    SIGNAL s_edge_falling        : std_logic_vector(g_NUM_EDGE_INPUTS-1 DOWNTO 0);        -- ! High when falling edge
    SIGNAL s_edge_rise_times     : t_triggerTimeArray(g_NUM_EDGE_INPUTS-1 DOWNTO 0);      -- Array of edge times ( w.r.t. logic_strobe)
    SIGNAL s_edge_rising         : std_logic_vector(g_NUM_EDGE_INPUTS-1 DOWNTO 0);        -- ! High when rising edge
    --SIGNAL s_i2c_scl_enb         : std_logic;
    --SIGNAL s_i2c_sda_enb         : std_logic;
    SIGNAL s_shutter             : std_logic;                                             --! shutter signal from TimePix, retimed onto local clock
    SIGNAL s_triggerLogic_reset  : std_logic;
    SIGNAL shutter_cnt_i         : std_logic_vector(g_SPILL_COUNTER_WIDTH-1 DOWNTO 0);
    SIGNAL shutter_i             : std_logic;
    SIGNAL spill_cnt_i           : std_logic_vector(g_SPILL_COUNTER_WIDTH-1 DOWNTO 0);
    SIGNAL spill_i               : std_logic;
    SIGNAL strobe_8x_logic      : std_logic;                                             --! Pulses one cycle every 4 of 16x clock.
    SIGNAL strobe_4x_logic       : std_logic;                                             -- one pulse every 4 cycles of clk_4x
    SIGNAL trigger_count         : std_logic_vector(g_IPBUS_WIDTH-1 DOWNTO 0);
    type   myTrigArray is array (g_NUM_DUTS-1 downto 0) of std_logic_vector(g_IPBUS_WIDTH-1 DOWNTO 0);
    signal TrigNArray : myTrigArray;
    SIGNAL TriggerNumber         : std_logic_vector(g_EVENT_DATA_WIDTH-1 DOWNTO 0);
    SIGNAL TriggerNumberStrobe   :  std_logic_vector(g_NUM_DUTS-1 downto 0);
    SIGNAL stretchFlags          : std_logic_vector(g_NUM_DUTS-1 downto 0) := "0011"; -- ! define which dummyDUT have their busy line stretched

    SIGNAL trigger_times         : t_triggerTimeArray(g_NUM_TRIG_INPUTS-1 DOWNTO 0);      -- ! trigger arrival time ( w.r.t. logic_strobe)
    SIGNAL triggers              : std_logic_vector(g_NUM_TRIG_INPUTS-1 DOWNTO 0);
    SIGNAL veto_o                : std_logic;                                             --! goes high when one or more DUT are busy
	signal ctrl, stat: ipb_reg_v(0 downto 0);
	--My signals
	--SIGNAL busy_toggle_o         : std_logic_vector(g_NUM_DUTS-1 downto 0);
	
----------------------------------------------
----------------------------------------------
    component DUTInterfaces
    generic(
	   g_NUM_DUTS : positive := 4;-- <- was 3
	   g_IPBUS_WIDTH : positive := 32
	   );
    port (
        clk_4x_logic_i          : IN     std_logic ;
        strobe_4x_logic_i       : IN     std_logic ;                                  --! goes high every 4th clock cycle
        trigger_counter_i       : IN     std_logic_vector (g_EVENT_DATA_WIDTH-1 DOWNTO 0); --! Number of trigger events since last reset
        trigger_i               : IN     std_logic ;                                  --! goes high when trigger logic issues a trigger
        reset_or_clk_to_dut_i   : IN     std_logic ;                                  --! Synchronization signal. Passed TO DUT pins
        shutter_to_dut_i        : IN     std_logic ;                                  --! Goes high TO indicate data-taking active. DUTs report busy unless ignoreShutterVeto IPBus flag is set high
        -- IPBus signals.
        ipbus_clk_i             : IN     std_logic ;
        ipbus_i                 : IN     ipb_wbus ;                                   --! Signals from IPBus core TO slave
        ipbus_reset_i           : IN     std_logic ;
        ipbus_o                 : OUT    ipb_rbus ;                                   --! signals from slave TO IPBus core
        -- Signals to/from DUT
        busy_from_dut       : IN     std_logic_vector (g_NUM_DUTS-1 DOWNTO 0);    --! BUSY input from DUTs
        busy_to_dut       : OUT     std_logic_vector (g_NUM_DUTS-1 DOWNTO 0);     --! BUSY input to DUTs (single ended)
        clk_from_dut  : IN std_logic_vector(g_NUM_DUTS-1 DOWNTO 0); --new signal for TLU, replace differential I/O
        clk_to_dut : OUT std_logic_vector(g_NUM_DUTS-1 DOWNTO 0); --new signal for TLU, replace differential I/O
        reset_to_dut: OUT    std_logic_vector (g_NUM_DUTS-1 DOWNTO 0);     --! Replaces reset_or_clk_to_dut
        trigger_to_dut : OUT    std_logic_vector (g_NUM_DUTS-1 DOWNTO 0);     --! Trigger output
        shutter_to_dut      : OUT    std_logic_vector (g_NUM_DUTS-1 DOWNTO 0);     --! Shutter output
        veto_o                  : OUT    std_logic   
    );
    end component DUTInterfaces;
----------------------------------------------
----------------------------------------------
    component Dummy_DUT 
    Port ( 
        CLK : in  STD_LOGIC;         --! this is the USB clock.
        RST : in STD_LOGIC;          --! Synchronous clock
        Trigger : in STD_LOGIC;      --! Trigger from TLU
        stretchBusy: in STD_LOGIC;   --! flag: if 1 extend the BUSY signal
        Busy : out STD_LOGIC;        --! Busy to TLU
        DUTClk : out STD_LOGIC;      --! clock from DUT
        TriggerNumber : out STD_LOGIC_VECTOR(31 downto 0);
        TriggerNumberStrobe : out STD_LOGIC;
        FSM_Error : out STD_LOGIC
        );
end component;
----------------------------------------------
----------------------------------------------

   COMPONENT eventBuffer
   GENERIC (
        g_EVENT_DATA_WIDTH   : positive := 32;
        g_IPBUS_WIDTH        : positive := 32;
        g_READ_COUNTER_WIDTH : positive := 16
   );
   PORT (
        clk_4x_logic_i    : IN     std_logic ;
        data_strobe_i     : IN     std_logic ;                                     -- Indicates data TO transfer
        event_data_i      : IN     std_logic_vector (g_EVENT_DATA_WIDTH-1 DOWNTO 0);
        ipbus_clk_i       : IN     std_logic ;
        ipbus_i           : IN     ipb_wbus ;
        ipbus_reset_i     : IN     std_logic ;
        strobe_4x_logic_i : IN     std_logic ;
        --trigger_count_i   : IN     std_logic_vector (g_IPBUS_WIDTH-1 DOWNTO 0); --! Not used yet.
        rst_fifo_o        : OUT    std_logic ;                                     --! rst signal TO first level fifos
        buffer_full_o     : OUT    std_logic ;                                     --! Goes high when event buffer almost full
        ipbus_o           : OUT    ipb_rbus ;
        logic_reset_i     : IN     std_logic                                       -- reset buffers when high. Synch withclk_4x_logic
   );
   END COMPONENT eventBuffer;
----------------------------------------------
----------------------------------------------
--    COMPONENT eventFormatter
--    GENERIC (
--        g_EVENT_DATA_WIDTH   : positive := 64;
--        g_IPBUS_WIDTH        : positive := 32;
--        g_COUNTER_TRIG_WIDTH : positive := 32;
--        g_COUNTER_WIDTH      : positive := 12;
--        g_EVTTYPE_WIDTH      : positive := 4;      --! Width of the event type word
--        --g_NUM_INPUT_TYPES     : positive := 4;               -- Number of different input types (trigger, shutter, edge...)
--        g_NUM_EDGE_INPUTS    : positive := 4;      --! Number of edge inputs
--        g_NUM_TRIG_INPUTS    : positive := 6       --! Number of trigger inputs (POSSIBLY WRONG!)
--    );
--    PORT (
--        clk_4x_logic_i         : IN     std_logic ;                                         --! Rising edge active
--        ipbus_clk_i            : IN     std_logic ;
--        logic_strobe_i         : IN     std_logic ;                                         --! Pulses high once every 4 cycles of clk_4x_logic
--        logic_reset_i          : IN     std_logic ;                                         --! goes high TO reset counters. Synchronous with clk_4x_logic
--        rst_fifo_i             : IN     std_logic ;                                         --! Goes high TO reset FIFOs
--        buffer_full_i          : IN     std_logic ;                                         --! Goes high when output fifo full
--        trigger_i              : IN     std_logic ;                                         --! goes high TO load trigger data. One cycle of clk_4x_logic
--        trigger_times_i        : IN     t_triggerTimeArray (g_NUM_TRIG_INPUTS-1 DOWNTO 0);  --! Array of trigger times ( w.r.t. logic_strobe)
--        trigger_inputs_fired_i : IN     std_logic_vector (g_NUM_TRIG_INPUTS-1 DOWNTO 0);    --! high for each input that "fired"
--        trigger_cnt_i          : IN     std_logic_vector (g_COUNTER_TRIG_WIDTH-1 DOWNTO 0); --! Trigger count
--        shutter_i              : IN     std_logic ;
--        shutter_cnt_i          : IN     std_logic_vector (g_COUNTER_WIDTH-1 DOWNTO 0);
--        spill_i                : IN     std_logic ;
--        spill_cnt_i            : IN     std_logic_vector (g_COUNTER_WIDTH-1 DOWNTO 0);
--        edge_rise_i            : IN     std_logic_vector (g_NUM_EDGE_INPUTS-1 DOWNTO 0);    --! High when rising edge
--        edge_fall_i            : IN     std_logic_vector (g_NUM_EDGE_INPUTS-1 DOWNTO 0);    --! High when falling edge
--        edge_rise_time_i       : IN     t_triggerTimeArray (g_NUM_EDGE_INPUTS-1 DOWNTO 0);  --! Array of edge times ( w.r.t. logic_strobe)
--        edge_fall_time_i       : IN     t_triggerTimeArray (g_NUM_EDGE_INPUTS-1 DOWNTO 0);  --! Array of edge times ( w.r.t. logic_strobe)
--        ipbus_i                : IN     ipb_wbus ;
--        ipbus_o                : OUT    ipb_rbus ;
--        data_strobe_o          : OUT    std_logic ;                                         --! goes high when data ready TO load into event buffer
--        event_data_o           : OUT    std_logic_vector (g_EVENT_DATA_WIDTH-1 DOWNTO 0);
--        reset_timestamp_i      : IN     std_logic ;                                         --! Taking high causes timestamp TO be reset. Combined with internal timestmap reset and written to reset_timestamp_o
--        reset_timestamp_o      : OUT    std_logic                                           --! Goes high for one clock cycle of clk_4x_logic when timestamp reset
--    );
--    END COMPONENT eventFormatter;   
----------------------------------------------
----------------------------------------------
    COMPONENT logic_clocks
    GENERIC (
        g_USE_EXTERNAL_CLK : integer := 1
    );
    PORT (
        ipbus_clk_i           : IN     std_logic ;
        ipbus_i               : IN     ipb_wbus ;
        ipbus_reset_i         : IN     std_logic ;
        Reset_i               : IN     std_logic ;
        clk_logic_xtal_i      : IN     std_logic ; -- ! 40MHz clock from onboard xtal
        clk_8x_logic_o       : OUT    std_logic ; -- 640MHz clock
        clk_4x_logic_o        : OUT    std_logic ; -- 160MHz clock
        ipbus_o               : OUT    ipb_rbus ;
        strobe_8x_logic_o    : OUT    std_logic ; -- strobes once every 4 cycles of clk_16x
        strobe_4x_logic_o     : OUT    std_logic ; -- one pulse every 4 cycles of clk_4x
        --extclk_p_b            : INOUT  std_logic ; -- either external clock in, or a clock being driven out
        --extclk_n_b            : INOUT  std_logic ;
        DUT_clk_o             : OUT    std_logic ;
        logic_clocks_locked_o : OUT    std_logic ;
        logic_reset_o         : OUT    std_logic   -- Goes high TO reset counters etc. Sync with clk_4x_logic
    );
    END COMPONENT logic_clocks;
----------------------------------------------


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
    
--    component clk_wiz_0
--    port
--     (-- Clock in ports
--      clk_in1           : in     std_logic;
--      -- Clock out ports
--      clk_out1          : out    std_logic;
--      -- Status and control signals
--      reset             : in     std_logic;
--      locked            : out    std_logic
--     );
--    end component;
    

    -- Optional embedded configurations
    -- pragma synthesis_off
    FOR ALL : DUTInterfaces USE ENTITY work.DUTInterfaces;
    --FOR ALL : IPBusInterface USE ENTITY work.IPBusInterface;
    FOR ALL : T0_Shutter_Iface USE ENTITY work.T0_Shutter_Iface;
    FOR ALL : eventBuffer USE ENTITY work.eventBuffer;
    FOR ALL : eventFormatter USE ENTITY work.eventFormatter;
    FOR ALL : i2c_master USE ENTITY work.i2c_master;--<P
    FOR ALL : logic_clocks USE ENTITY work.logic_clocks;
    FOR ALL : triggerInputs_newTLU USE ENTITY work.triggerInputs_newTLU;
    FOR ALL : triggerLogic USE ENTITY work.triggerLogic;
    -- pragma synthesis_on 
      	
begin
    
--led_iic_test <= iic_test;

--Implicit instantiation of output tristate buffers.
    i2c_scl_b <= '0' when (s_i2c_scl_enb = '0') else 'Z';
    i2c_sda_b <= '0' when (s_i2c_sda_enb = '0') else 'Z';

    
    
    -- Infrastructure
    -- ModuleWare code(v1.12) for instance 'I9' of 'gnd'
    logic_clocks_reset <= '0';
    -- ModuleWare code(v1.12) for instance 'I11' of 'gnd'
    spill_i <= '0';
    -- ModuleWare code(v1.12) for instance 'I12' of 'gnd'
    spill_cnt_i <= (OTHERS => '0');
    -- ModuleWare code(v1.12) for instance 'I13' of 'gnd'
    shutter_i <= '0';
    -- ModuleWare code(v1.12) for instance 'I14' of 'gnd'
    shutter_cnt_i <= (OTHERS => '0');
    -- ModuleWare code(v1.12) for instance 'I17' of 'gnd'
    dout1 <= '0';
    -- ModuleWare code(v1.12) for instance 'I18' of 'gnd'
    dout <= '0';
    -- ModuleWare code(v1.12) for instance 'I19' of 'merge'
    --gpio_hdr <= dout1 & dout & s_shutter & T0_o;
    -- ModuleWare code(v1.12) for instance 'I8' of 'sor'
    overall_veto <= buffer_full_o OR veto_o;
    -- ModuleWare code(v1.12) for instance 'I16' of 'sor'
    s_triggerLogic_reset <= logic_reset OR T0_o;

    i2c_reset <= '1';
    clk_gen_rst <= '1';
    gpio <= strobe_8x_logic;
    sysclk_50_o_p <= '0';
    sysclk_50_o_n <= '0';
    --busy_o <= std_logic_vector(to_unsigned(0,    busy_o'length));
    --busy_o <= '000000';
    --sysclk_40_o_p <= sysclk;

------------------------------------------
	infra: entity work.enclustra_ax3_pm3_infra
		port map(
			sysclk => clk_encl_buf,
			clk_ipb_o => clk_ipb,
			rst_ipb_o => rst_ipb,
			rst_125_o => phy_rst_e,
			clk_200_o => clk_200,
			nuke => nuke,
			soft_rst => soft_rst,
			leds => inf_leds,
			rgmii_txd => rgmii_txd,
			rgmii_tx_ctl => rgmii_tx_ctl,
			rgmii_txc => rgmii_txc,
			rgmii_rxd => rgmii_rxd,
			rgmii_rx_ctl => rgmii_rx_ctl,
			rgmii_rxc => rgmii_rxc,
			mac_addr => mac_addr,
			ip_addr => ip_addr,
			ipb_in => ipb_in,
			ipb_out => ipb_out
		);
		
	--leds <= not ('0' & userled & inf_leds); -- Check this.
	phy_rstn <= not phy_rst_e;
		
--	mac_addr <= X"020ddba1151" & dip_sw; -- Careful here, arbitrary addresses do not always work
--	ip_addr <= X"c0a8c81" & dip_sw; -- 192.168.200.16+n
	mac_addr <= X"020ddba1151d"; -- Careful here, arbitrary addresses do not always work
	ip_addr <= X"c0a8c81d"; -- 192.168.200.29

------------------------------------------
    I1 : entity work.ipbus_ctrlreg_v
    port map(
        clk => clk_ipb,
        reset => rst_ipb,
        ipbus_in => ipbww(N_SLV_CTRL_REG),
        ipbus_out => ipbrr(N_SLV_CTRL_REG),
        d => stat,
        q => ctrl
    );
    stat(0) <= std_logic_vector(FW_VERSION);-- <-Let's use this as firmware revision number
    soft_rst <= ctrl(0)(0);
    nuke <= ctrl(0)(1);
    
------------------------------------------
	I2 : entity work.ipbus_fabric_sel
    generic map(
    	NSLV => N_SLAVES,
    	SEL_WIDTH => IPBUS_SEL_WIDTH)
    port map(
      ipb_in => ipb_out,
      ipb_out => ipb_in,
      sel => ipbus_sel_ipbus_example(ipb_out.ipb_addr),
      ipb_to_slaves => ipbww,
      ipb_from_slaves => ipbrr
    );

------------------------------------------
    I3 : i2c_master
    PORT MAP (
        i2c_scl_i     => i2c_scl_b,
        i2c_sda_i     => i2c_sda_b,
        ipbus_clk_i   => clk_ipb,
        ipbus_i       => ipbww(N_SLV_I2C_0),
        ipbus_reset_i => rst_ipb,
        i2c_scl_enb_o => s_i2c_scl_enb,
        i2c_sda_enb_o => s_i2c_sda_enb,
        ipbus_o       => ipbrr(N_SLV_I2C_0)
    );
    
----------------------------------------------
    I4 : logic_clocks
    GENERIC MAP (
        g_USE_EXTERNAL_CLK => 0
    )
    PORT MAP (
        ipbus_clk_i           => clk_ipb,
        ipbus_i               => ipbww(N_SLV_LGCCLK),
        ipbus_reset_i         => rst_ipb,
        Reset_i               => logic_clocks_reset,
        clk_logic_xtal_i      => sysclk_40, -- Not sure this is correct
        clk_8x_logic_o       => clk_8x_logic,
        clk_4x_logic_o        => clk_4x_logic,
        ipbus_o               => ipbrr(N_SLV_LGCCLK),
        strobe_8x_logic_o    => strobe_8x_logic,
        strobe_4x_logic_o     => strobe_4x_logic,
        DUT_clk_o             => open,
        logic_clocks_locked_o => leds(3),
        logic_reset_o         => logic_reset
    );    



------------------------------------------      
--    I6 : eventFormatter
--    GENERIC MAP (
--        g_EVENT_DATA_WIDTH   => g_EVENT_DATA_WIDTH,
--        g_IPBUS_WIDTH        => g_IPBUS_WIDTH,
--        g_COUNTER_TRIG_WIDTH => g_IPBUS_WIDTH,
--        g_COUNTER_WIDTH      => 12,
--        g_EVTTYPE_WIDTH      => 4,                         --! Width of the event type word
--        --g_NUM_INPUT_TYPES     : positive := 4;               -- Number of different input types (trigger, shutter, edge...)
--        g_NUM_EDGE_INPUTS    => g_NUM_EDGE_INPUTS,         --! Number of edge inputs
--        g_NUM_TRIG_INPUTS    => g_NUM_TRIG_INPUTS          --! Number of trigger inputs
--    )
--    PORT MAP (
--        clk_4x_logic_i         => clk_4x_logic,
--        ipbus_clk_i            => clk_ipb,
--        logic_strobe_i         => strobe_4x_logic,
--        logic_reset_i          => logic_reset,
--        rst_fifo_i             => rst_fifo_o,
--        buffer_full_i          => buffer_full_o,
--        trigger_i              => overall_trigger,
--        trigger_times_i        => postVetoTrigger_times,
--        trigger_inputs_fired_i => postVetotrigger,
--        trigger_cnt_i          => trigger_count,
--        shutter_i              => shutter_i,
--        shutter_cnt_i          => shutter_cnt_i,
--        spill_i                => spill_i,
--        spill_cnt_i            => spill_cnt_i,
--        edge_rise_i            => s_edge_rising,
--        edge_fall_i            => s_edge_falling,
--        edge_rise_time_i       => s_edge_rise_times,
--        edge_fall_time_i       => s_edge_fall_times,
--        ipbus_i                => ipbww(N_SLV_EVFMT),
--        ipbus_o                => ipbrr(N_SLV_EVFMT),
--        data_strobe_o          => data_strobe,
--        event_data_o           => event_data,
--        reset_timestamp_i      => T0_o,
--        reset_timestamp_o      => OPEN
--    );

------------------------------------------
    I7 : eventBuffer
    GENERIC MAP (
        g_EVENT_DATA_WIDTH   => 32,
        g_IPBUS_WIDTH        => g_IPBUS_WIDTH,
        g_READ_COUNTER_WIDTH => 13
        
    )
    PORT MAP (
        clk_4x_logic_i    => clk_4x_logic,
        --clk_4x_logic_i    => sysclk_40,
        data_strobe_i     => TriggerNumberStrobe(0),
        event_data_i      => TrigNArray(0),
        ipbus_clk_i       => clk_ipb,
        ipbus_i           => ipbww(N_SLV_EVBUF),
        ipbus_reset_i     => rst_ipb,
        strobe_4x_logic_i => strobe_4x_logic,
        rst_fifo_o        => rst_fifo_o,
        buffer_full_o     => buffer_full_o,
        ipbus_o           => ipbrr(N_SLV_EVBUF),
        logic_reset_i     => logic_reset
    );
    

------------------------------------------
--    I9 : DUTInterfaces
--    GENERIC MAP (
--        g_NUM_DUTS    => g_NUM_DUTS,
--        g_IPBUS_WIDTH => g_IPBUS_WIDTH
--    )
--    PORT MAP (
--         clk_4x_logic_i          => clk_4x_logic,
--         strobe_4x_logic_i       => strobe_4x_logic,
--         trigger_counter_i       => trigger_count,
--         trigger_i               => overall_trigger,
--         reset_or_clk_to_dut_i   => T0_o,
--         shutter_to_dut_i        => s_shutter,
--         ipbus_clk_i             => clk_ipb,
--         ipbus_i                 => ipbww(N_SLV_DUT),
--         ipbus_reset_i           => rst_ipb,
--         ipbus_o                 => ipbrr(N_SLV_DUT),
--         busy_from_dut       => busy_i,
--         busy_to_dut        => open,
--         clk_from_dut => dut_clk_i,
--         clk_to_dut => dut_clk_o,
--         --reset_or_clk_to_dut_n_o => reset_or_clk_n_o,
--         --reset_or_clk_to_dut_p_o => reset_or_clk_p_o,
--         reset_to_dut => spare_o,
--         trigger_to_dut => triggers_o,
--         --shutter_to_dut_n_o      => shutter_to_dut_n_o,
--         --shutter_to_dut_p_o      => shutter_to_dut_p_o,
--         shutter_to_dut  => cont_o,
--         veto_o                  => veto_o
--    );
    
  
         
-------------TEST AREA------------    
--    test0: entity work.test_inToOut
--    port map(
--        clk_in => clk_200,
--        busy_in=> busy_i,
--        control_in=> cont_i,
--        trig_in=> triggers_i,
--        clkDut_in=> dut_clk_i,
--        spare_in=> spare_i,
--        busy_out=> busy_o,
--        control_out=> cont_o,
--        trig_out=> triggers_o,
--        clkDut_out=> dut_clk_o,
--        spare_out=> spare_o
--    );

--    dutout0: entity work.DUTs_outputs
--    port map(
--        clk_in => encl_clock50, 
--        d_clk_o => dut_clk_o,
--        d_trg_o => triggers_o,
--        d_busy_o => busy_o,
--        d_cont_o => cont_o,
--        d_spare_o => spare_o
--    );
   
--    clk50_o_fromEnclustra : clk_wiz_0
--       port map ( 
--       -- Clock in ports
--       clk_in1 => clk_encl_buf, --sysclk_40,
--      -- Clock out ports  
--       clk_out1 => encl_clock50,
--      -- Status and control signals                
--       reset => '0',
--       locked =>  open          
--     );

    
----------------------------------------------
    OutBlocks:
    for iDUT in 0 to g_NUM_DUTS-1 generate
    begin


--     generate an instance of the Dummy DUT behind connector 0
    DUT_Instance: Dummy_DUT 
      Port map ( 
           --CLK => clk_4x_logic,--160 Mhz clock
           CLK => sysclk_40,
           RST => cont_i(iDUT),-- coming from HDMI pin
           Trigger => triggers_i(iDUT), --coming from HDMI pin
           stretchBusy => stretchFlags(iDUT), 
           Busy => busy_o(iDUT), --going out on HDMI pin
           DUTClk => dut_clk_o(iDUT), --going out on HDMI pin
           TriggerNumber => TrigNArray(iDUT),
           TriggerNumberStrobe => TriggerNumberStrobe(iDUT),
           FSM_Error => open
           );



    end generate;


    

------------------------------------------      


------------------------------------------
    IBUFGDS_inst: IBUFGDS
    generic map (
        IBUF_LOW_PWR=> false
    )
    port map (
        O => sysclk_40,
        I => sysclk_40_i_p,
        IB => sysclk_40_i_n
    );
    
------------------------------------------
    IBUFG_inst: IBUFG
    port map (
        O => clk_encl_buf,
        I => clk_enclustra--sysclk
    );    



      


end rtl;
