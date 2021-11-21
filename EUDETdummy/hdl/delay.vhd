LIBRARY ieee;
USE ieee.std_logic_1164.ALL;
use IEEE.std_logic_arith.all;
USE ieee.std_logic_unsigned.all;

entity delay is
  
  generic (
    length : integer := 1);  -- number of clock cycles to delay signal
  port (
    clock  : in  std_logic;             -- rising edge active
    input  : in  std_logic;
    output : out std_logic);

end delay;

architecture rtl of delay is

  component dtype
    port (
      Q : out std_logic;
      C   : in std_logic;
      CLR : in std_logic;
      D   : in std_logic;
      CE  : in std_logic;
      PRE : in std_logic
      );
  end component;

  signal internal_signal : std_logic_vector( length downto 0);  -- signals along the pipe-line
  
begin  -- rtl

  internal_signal(0) <= input;
  
  pipeline: for N in 1 to length generate

    pipelinestage: dtype
      port map (
        q => internal_signal(N),
        c => clock ,
        clr => '0' ,
        d => internal_signal(N-1),
        ce => '1' ,
        pre => '0'
        );
    
  end generate pipeline;

  output <= internal_signal(length);
  
end rtl;
