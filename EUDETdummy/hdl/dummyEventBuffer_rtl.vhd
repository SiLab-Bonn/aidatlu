--=============================================================================
--! @file eventBuffer_rtl.vhd
--=============================================================================
--
-------------------------------------------------------------------------------
-- --
-- University of Bristol, High Energy Physics Group.
-- --
------------------------------------------------------------------------------- --
-- VHDL Architecture fmc_mTLU_lib.eventBuffer.rtl
--
-- 
-- Created using using Mentor Graphics HDL Designer(TM) 2010.3 (Build 21)
--
LIBRARY ieee;
USE ieee.std_logic_1164.all;
USE ieee.numeric_std.all;

USE work.ipbus.all;

--! @brief Stores input words (64bits) for readout over IPBus. 
--! Uses a FIFO ( 64bits at input, 32 bits at output )
--
--
--! @author David Cussans , David.Cussans@bristol.ac.uk
--
--! @date 15:24:50 11/13/12
--
--! @version v0.1
--
--! @details
--! \n\nIPBus Address map:
--! \li 0x0000 - FIFO data
--! \li 0x0001 - FIFO fill level
--! \li 0x0010 - FIFO status/control: (Writing Bit-0 resets pointers, Reading bit-1 returns "prog_full" flag)
--!
--! <b>Modified by: Alvaro Dosil , alvaro.dosil@usc.es </b>\n
--------------------------------------------------------------------------------

ENTITY eventBuffer IS
    GENERIC( 
        g_EVENT_DATA_WIDTH    : positive := 32;
        g_IPBUS_WIDTH         : positive := 32;
        g_READ_COUNTER_WIDTH  : positive := 13
    );
    PORT( 
        clk_4x_logic_i    : IN     std_logic;
        data_strobe_i     : IN     std_logic;                                         -- Indicates data to transfer
        event_data_i      : IN     std_logic_vector (g_EVENT_DATA_WIDTH-1 DOWNTO 0);
        ipbus_clk_i       : IN     std_logic;
        ipbus_i           : IN     ipb_wbus;
        ipbus_reset_i     : IN     std_logic;
        strobe_4x_logic_i : IN     std_logic;
        --trigger_count_i   : IN     std_logic_vector (g_IPBUS_WIDTH-1 DOWNTO 0); --! Not used yet.
        rst_fifo_o			: OUT 	std_logic;														--! rst signal to first level fifos
        buffer_full_o     : OUT    std_logic;                                         --! Goes high when event buffer almost full
        ipbus_o           : OUT    ipb_rbus;
        logic_reset_i     : IN     std_logic                                          -- reset buffers when high. Synch withclk_4x_logic
    );

-- Declarations

END ENTITY eventBuffer ;

--
ARCHITECTURE rtl OF eventBuffer IS
    signal s_rd_data_count    : std_logic_vector(g_READ_COUNTER_WIDTH-1 downto 0) := (others =>'0');
    signal s_fifo_fill_level : std_logic_vector(g_IPBUS_WIDTH-1 downto 0) := (others =>'0');  -- read-counter - 2*write_count
    signal s_write_strobe    : std_logic := '0';
    signal s_rst_fifo, s_rst_fifo_ipb : std_logic := '0';                             -- ! Take high to reset FIFO pointers.
    signal s_fifo_prog_full : std_logic := '0';                       -- ! Controlled by programmable-full flag of FIFO core
    signal s_fifo_rd_en : std_logic := '0';                           -- ! Take high to clock data out of FIFO
    signal s_fifo_dout : std_logic_vector(g_IPBUS_WIDTH-1 downto 0);  -- ! Output from FIFO ( fall-through mode)
    signal s_fifo_valid : std_logic := '1';                           -- ! High when data in FIFO
    signal s_fifo_full, s_fifo_almost_full, s_fifo_empty, s_fifo_almost_empty : std_logic := '0'; -- ! full and empty FIFO flags
    signal s_fifo_status_ipb , s_fifo_fill_level_d1 : std_logic_vector(ipbus_o.ipb_rdata'range) := (others => '0');  -- data registered onto IPBus clock
    signal s_ack : std_logic := '0';      -- -- IPBus ACK signal
    COMPONENT dummy_event_fifo
    PORT (
        rst : IN STD_LOGIC;
        wr_clk : IN STD_LOGIC;
        rd_clk : IN STD_LOGIC;
        din : IN STD_LOGIC_VECTOR(g_EVENT_DATA_WIDTH-1 DOWNTO 0);
        wr_en : IN STD_LOGIC;
        rd_en : IN STD_LOGIC;
        dout : OUT STD_LOGIC_VECTOR(g_EVENT_DATA_WIDTH-1 DOWNTO 0);
        full : OUT STD_LOGIC;
        almost_full : OUT STD_LOGIC;
        empty : OUT STD_LOGIC;
        almost_empty : OUT STD_LOGIC;
        rd_data_count : OUT STD_LOGIC_VECTOR(12 DOWNTO 0);
        prog_full : OUT STD_LOGIC
    );
    END COMPONENT;
  
BEGIN

  -----------------------------------------------------------------------------
  -- IPBus IO
  -----------------------------------------------------------------------------

  --! Generate IPBus ACK 
    ipbus_ack: process(ipbus_clk_i)
    begin
    if rising_edge(ipbus_clk_i) then
        s_ack <= ipbus_i.ipb_strobe and not s_ack;
    end if;
    end process ipbus_ack;
    ipbus_o.ipb_ack <= s_ack;
    
    --! Generate FIFO read enable
    --! take high for one cycle ( when ipb_strobe goes high but before ACK goes
    --high to follow it
    s_fifo_rd_en  <= '1' when
        ipbus_i.ipb_strobe = '1' and ipbus_i.ipb_write = '0' and ipbus_i.ipb_addr(1 downto 0) = "00" and s_ack = '0'
        else '0';
    ipbus_o.ipb_err <= '0';

    --! Multiplex output data.
    with ipbus_i.ipb_addr(1 downto 0) select ipbus_o.ipb_rdata <=
        s_fifo_dout          when "00",
        s_fifo_fill_level    when "01",
        s_fifo_status_ipb	 when "10",
        (others => '1')      when others;

    ipbus_write: process (ipbus_clk_i)
    begin  -- process ipbus_write
    if rising_edge(ipbus_clk_i) then
        s_rst_fifo_ipb <= '0';
        if ipbus_i.ipb_strobe = '1' and ipbus_i.ipb_addr(1 downto 0) = "10" and ipbus_i.ipb_write = '1' then
            s_rst_fifo_ipb <= '1';
        end if;
        -- Register data onto IPBus clock domain to ease timing closure.
        s_fifo_status_ipb <=  X"000000" & "000" & s_fifo_prog_full & s_fifo_full & s_fifo_almost_full & s_fifo_almost_empty & s_fifo_empty;
        s_fifo_fill_level <= X"0000" & "000" & s_rd_data_count; 
    end if;
    end process ipbus_write;
  
    rst_fifo_o <= s_rst_fifo_ipb;
    s_rst_fifo <= s_rst_fifo_ipb or logic_reset_i;
  
  -----------------------------------------------------------------------------
  -- FIFO and fill-level calculation
  -----------------------------------------------------------------------------
  
  -- Instantiate a buffer to store the data. 64-bit on input, 32-bit on output.
  --event_fifo : entity work.tlu_event_fifo
    event_fifo : dummy_event_fifo
    PORT MAP (
        rst => s_rst_fifo,
        wr_clk => clk_4x_logic_i,
        rd_clk => ipbus_clk_i,
        --din => event_data_i,
        din => event_data_i,
        wr_en => data_strobe_i,
        rd_en => s_fifo_rd_en,
        dout => s_fifo_dout,
        full => s_fifo_full,
        almost_full => s_fifo_almost_full,
        empty => s_fifo_empty,
        almost_empty => s_fifo_almost_empty,
        rd_data_count => s_rd_data_count,
        prog_full => s_fifo_prog_full
    );
    buffer_full_o <= s_fifo_prog_full;
  
END ARCHITECTURE rtl;

