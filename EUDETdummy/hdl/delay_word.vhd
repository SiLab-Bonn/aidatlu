LIBRARY ieee;
USE ieee.std_logic_1164.ALL;
use IEEE.std_logic_arith.all;
USE ieee.std_logic_unsigned.all;

entity delay_word is
  
  generic (
    length : integer := 1 ; -- number of clock cycles to delay signal
    width : integer := 1 );             -- width of bus
  port (
    clock  : in  std_logic;             -- rising edge active
    input  : in  std_logic_vector(width-1 downto 0);
    output : out std_logic_vector(width-1 downto 0)
    );

end delay_word;

architecture rtl of delay_word is


  subtype DataWord is std_logic_vector( width-1 downto 0 );
  type WordArray is array (length downto 0) of DataWord;
  signal InternalSignal : WordArray;  -- signals along the pipe-line
  
begin  -- rtl

  InternalSignal(0) <= input;
  
  pipeline: for N in 1 to length generate

    pipelinestage: process (clock , InternalSignal(N-1))
    begin  -- process pipelinestage
      if rising_edge(clock) then
        InternalSignal(N) <= InternalSignal(N-1);
      end if;      
    end process pipelinestage;
    
  end generate pipeline;

  output <= InternalSignal(length);
  
end rtl;
