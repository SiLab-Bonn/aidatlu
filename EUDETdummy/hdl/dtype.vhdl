----- CELL dtype                       -----
library IEEE;
use IEEE.STD_LOGIC_1164.all;
-- use IEEE.VITAL_Timing.all;

entity dtype is

  port(
    Q : out std_logic;
    C   : in std_logic;
    CLR : in std_logic;
    D   : in std_logic;
	 CE  : in std_logic;
    PRE : in std_logic
    );

end dtype;

architecture dtype_V of dtype is
begin

  VITALBehavior         : process(C, CLR, PRE)
  begin

    if (CLR = '1') then
      Q <= '0';
    elsif (PRE = '1') then
      Q <= '1';
    elsif (rising_edge(C) and CE='1') then
      Q <= D ;
    end if;
  end process;
end dtype_V;

