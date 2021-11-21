----------------------------------------------------------------------------------
--! @file
--
-- Company: University of Bristol 
-- Engineer: David Cussans
-- 
-- Create Date:    11/11/09
-- Design Name: 
-- Module Name:    Trigger_Number_Error_Checker - RTL 
-- Project Name: 
-- Target Devices: 
-- Tool versions: 
--! @brief Checks the trigger numbers being returned by the dummy dut.
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

entity Trigger_Number_Error_Checker is
    Port ( 
           CLK : in  STD_LOGIC;         --! this is the USB clock.
	   RST : in STD_LOGIC;          --! Synchronous with clock
           TriggerNumber : in STD_LOGIC_VECTOR(15 downto 0);  --! should
                                                              --incremeent from
                                                              --0
           TriggerNumberStrobe : in STD_LOGIC;  --! Active high
           TriggerCounter : out  STD_LOGIC_VECTOR(15 downto 0);  --!internal counter
           ErrorFlag : out STD_LOGIC    --! goes high if internal number
                                        --doesn't match
           );

end entity Trigger_Number_Error_Checker;

architecture RTL of Trigger_Number_Error_Checker is


  
  signal InternalTriggerCounter : std_logic_vector(TriggerNumber'high downto 0);  -- internal
                                                                          -- store
                                                                          -- to compare with output from TLU

  signal InternalErrorFlag : std_logic := '0';  -- VHDL can't read an out-port bodge

  signal Registered_TriggerNumberStrobe0 ,Registered_TriggerNumberStrobe1 ,Registered_TriggerNumberStrobe2  : std_logic := '0';  
                                        -- bodge 'cos I don't understand RTL...
  signal Registered_TriggerNumber : std_logic_vector(15 downto 0);
  
begin

  delay_triggerstrobe: process (clk , TriggerNumberStrobe ,Registered_TriggerNumberStrobe0 ,Registered_TriggerNumberStrobe1 , Registered_TriggerNumberStrobe2 )
  begin  -- process delay_triggerstrobe
    if rising_edge(clk) then
      Registered_TriggerNumberStrobe0 <= TriggerNumberStrobe;
      Registered_TriggerNumberStrobe1 <= Registered_TriggerNumberStrobe0;
      Registered_TriggerNumberStrobe2 <= Registered_TriggerNumberStrobe1;
    end if;
  end process delay_triggerstrobe;

  register_trigger_number: process (clk , TriggerNumber  )
  begin  -- process register_trigger_number
    if rising_edge(clk) then
      Registered_TriggerNumber <= TriggerNumber;
    end if;
  end process register_trigger_number;

  
  check_error: process (clk ,Registered_TriggerNumberStrobe0 , Registered_TriggerNumber , InternalTriggerCounter)
  begin  -- process busy_control
    if (rising_edge(clk) and (Registered_TriggerNumberStrobe0 = '1'))  then
      if ( unsigned(Registered_TriggerNumber) /= (unsigned(InternalTriggerCounter)+2) )then  --
        -- temporary fix to check that checker is working.
--              if ( unsigned(Registered_TriggerNumber) /= (unsigned(InternalTriggerCounter)+1) )then
        InternalErrorFlag <= '1';
      else
        InternalErrorFlag <= '0';
      end if;
    end if;
  end process check_error;

  output_error: process (clk ,  Registered_TriggerNumberStrobe1 , InternalErrorFlag)
  begin  -- process output_error
    if (rising_edge(clk)and (Registered_TriggerNumberStrobe1 = '1')) then
      ErrorFlag <=  InternalErrorFlag;
    end if;   
  end process output_error;

  
  register_trigger_number: process (clk ,  Registered_TriggerNumberStrobe2 , TriggerNumber )
  begin  -- process output_error
    if (rising_edge(clk)and (Registered_TriggerNumberStrobe2 = '1')) then
      InternalTriggerCounter <= TriggerNumber;
    end if;   
  end process output_error;

  TriggerCounter <= InternalTriggerCounter;
  
end RTL;

