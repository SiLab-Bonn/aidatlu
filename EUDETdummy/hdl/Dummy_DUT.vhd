----------------------------------------------------------------------------------
--! @file
--
-- Company: University of Bristol 
-- Engineer: David Cussans
-- 
-- Create Date:    16:28:09 07/07/2006 
-- Design Name: 
-- Module Name:    Dummy_DUT - RTL 
-- Project Name: 
-- Target Devices: 
-- Tool versions: 
--! @brief Pretends to be a device under test
--
--
-- Dependencies: 
--
-- Revision: 
-- Revision 0.01 - File Created
-- Additional Comments: 
--
----------------------------------------------------------------------------------
library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;


-- constant definitions.



---- Uncomment the following library declaration if instantiating
---- any Xilinx primitives in this code.
--library UNISIM;
--use UNISIM.VComponents.all;

entity Dummy_DUT is
    Port ( 
           CLK : in  STD_LOGIC;         --! this is the USB clock.
	   RST : in STD_LOGIC;          --! Synchronous clock
           Trigger : in STD_LOGIC;      --! Trigger from TLU
           stretchBusy: in STD_LOGIC; -- flag: if 1, then we want to extend the BUSY signal
           Busy : out STD_LOGIC;        --! Busy to TLU
           DUTClk : out STD_LOGIC;      --! clock from DUT
           TriggerNumber : out STD_LOGIC_VECTOR(31 downto 0);
           TriggerNumberStrobe : out STD_LOGIC;
           FSM_Error : out STD_LOGIC
           );

end entity Dummy_DUT;

architecture RTL of Dummy_DUT is

  component delay is
    generic (
      length : integer := 1);  -- number of clock cycles to delay signal
    port (
      clock  : in  std_logic;             -- rising edge active
      input  : in  std_logic;
      output : out std_logic);
  end component;
    
  -----------------------------------------------------------------------------

  signal Registered_Trigger , Registered_RST : std_logic;     -- trigger and reset signals after being registered to suppress meta-stability.
  
  signal TriggerShiftRegister : STD_LOGIC_VECTOR (31 downto 0);  --! register
                                                                 --to accept
                                                                 --incoming
                                                                 --trigger number

  type state_type is (IDLE , WAIT_FOR_TRIGGER_LOW , CLOCKING , OUTPUT_TRIGGER_NUMBER, BUSYDELAY);
  signal state : state_type := IDLE;
  signal next_state : state_type := IDLE;

  signal TriggerBitCounter : unsigned(4 downto 0) := ( others => '0');  --! stores bit being clocked
                                                         --in from TLU.
  signal InternalDUTClk : std_logic := '0';  -- ! "can't read an output" bodge
  
  constant DUTClockDivider : unsigned(3 downto 0) := to_unsigned(14,4);
  	
  constant TriggerBitCounterLimit : unsigned(4 downto 0) :=  to_unsigned(16,5);

  signal DUTClockCounter : unsigned(4 downto 0) := ( others => '0');
  
  signal s_busySR : unsigned( 14 downto 0) := ( others => '0' );  -- --! Shift register to generate stretch

begin

  trigger_register: delay
    generic map (
      length => 2)
    port map (
      clock  => clk,
      input  => Trigger,
      output => Registered_Trigger);

  reset_register: delay
    generic map (
      length => 2)
    port map (
      clock  => clk,
      input  => RST,
      output => Registered_RST);
  
  
  busy_control: process (clk , state)
  begin  -- process busy_control
    if rising_edge(clk) then
      if state = IDLE then
        busy <= '0';
      else
        busy <= '1';
      end if;
    end if;
  end process busy_control;
  
--  busy_control: process (clk , state)
--    begin  -- process busy_control
--      if rising_edge(clk) then
--        if (stretchBusy ='1') then
--            if ((state = IDLE) and (s_busySR=0)) then
--              busy <= '0';
--              s_busySR <= ( others => '1' );
--            elsif ( (state = IDLE) and (s_busySR /= 0) ) then
--              busy <= '1';
--              s_busySR <= s_busySR -1;
--            else
--              busy <= '1';
--              s_busySR <= s_busySR -1;
--            end if;
--        else
--            if state = IDLE then
--             busy <= '0';
--            else
--              busy <= '1';
--            end if;
--        end if;
--      end if;
--    end process busy_control;

  clock_control: process (clk , state , TriggerBitCounter )
  begin  -- process busy_control
    if rising_edge(clk) then
      if state = CLOCKING then
        if (InternalDUTClk = '0') and (DUTClockCounter = DUTClockDivider)  then
          TriggerBitCounter <= TriggerBitCounter +1;
        else
          TriggerBitCounter <= TriggerBitCounter;
        end if;
      else
        TriggerBitCounter <= ( others => '0');
      end if;
    end if;
  end process clock_control;


  InternalDUTClk_control: process (clk , state , InternalDUTClk)
  begin  -- process busy_control
    if rising_edge(clk) then
      if state = CLOCKING  then
        if DUTClockCounter = DUTClockDivider then
        	InternalDUTClk <= not InternalDUTClk ;
        	DUTClockCounter <= ( others => '0');
        else
            DUTClockCounter <= DUTClockCounter + 1;
        end if;
      else
        InternalDUTClk <= '0';
        DUTClockCounter <= ( others => '0');
      end if;
    end if;
  end process InternalDUTClk_control;

  shift_register_control: process (clk , state , TriggerShiftRegister)
  begin  -- process shift_register_control
    if rising_edge(clk) then
      if  state = IDLE then
        TriggerShiftRegister <= ( others => '0');
      elsif state = CLOCKING then
        if (InternalDUTClk = '1') and (DUTClockCounter=to_unsigned(1,4 ))  then
          -- if (InternalDUTClk = '1') and (DUTClockCounter=to_unsigned(1,DUTClockCounter'length ))  then
          TriggerShiftRegister <= trigger & TriggerShiftRegister( 31 downto 1) ;
          -- TriggerShiftRegister <= trigger & TriggerShiftRegister( TriggerShiftRegister'high downto 1) ;
        else
          TriggerShiftRegister <= TriggerShiftRegister;
        end if;
      end if;
    end if;
  end process shift_register_control;

  strobe_control: process (clk , state )
  begin  -- process stobe_control
    if rising_edge(clk) then
      if state = OUTPUT_TRIGGER_NUMBER then
        TriggerNumber <= TriggerShiftRegister;
        TriggerNumberStrobe <= '1';
      else
        TriggerNumberStrobe  <= '0';
      end if;
    end if;
  end process strobe_control;
  
  busy_delay_control: process(clk, state)
  begin
    if rising_edge(clk) then
        if state= BUSYDELAY then
            s_busySR <= s_busySR -1;
        elsif state= WAIT_FOR_TRIGGER_LOW then
            s_busySR <= ( others => '1' );
        end if;
    end if;
  end process busy_delay_control;
  
--! @brief controls the next state in the state machine
-- type   : combinational
-- inputs : pattern_we, mask_we , beam_state_counter
-- outputs: state , beam_state_counter
  state_logic: process (state, TriggerBitCounter , registered_trigger ,InternalDUTClk, stretchBusy, s_busySR  )
  begin  -- process state_logic
    case state is
	 
      when IDLE =>
        if ( registered_trigger = '1') then
          next_state <= WAIT_FOR_TRIGGER_LOW;
        else
          next_state <= IDLE;
        end if;

      when WAIT_FOR_TRIGGER_LOW =>
        if ( registered_trigger = '0'  ) then
          next_state <= CLOCKING;
        else
          next_state <= WAIT_FOR_TRIGGER_LOW;
        end if;

      when CLOCKING =>
        if (( TriggerBitCounter = TriggerBitCounterLimit ) and ( InternalDUTClk = '0')) then
          next_state <= OUTPUT_TRIGGER_NUMBER;
        else
          next_state <= CLOCKING;
        end if;

      when  OUTPUT_TRIGGER_NUMBER =>
        if (stretchBusy ='1') then
            next_state <= BUSYDELAY;
        else
            next_state <= IDLE;
        end if;   
        
      when BUSYDELAY =>
        if (s_busySR /= 0) then
            next_state <= BUSYDELAY;
        else
            next_state <= IDLE;
        end if;
               
      when others =>
        next_state <= IDLE;
        
    end case;
  end process state_logic;
  
  --! @brief Register that holds the current state of the FSM
  -- type   : combinational
  -- inputs : clk , next_state
  -- outputs: state
  state_register: process (clk )
  begin  -- process state_register
    if rising_edge(clk) then
      if (registered_rst = '1') then
        state <= IDLE;
      else
        state <= next_state;          
      end if;
    end if;
  end process state_register;

  DUTClk <= InternalDUTClk;

  fsm_error <= '0';                     -- hardware to zero.
  
end RTL;

