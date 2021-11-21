-- Address decode logic for ipbus fabric
-- 
-- 
-- 
-- Paolo Baesso, February 2017

library IEEE;
use IEEE.STD_LOGIC_1164.all;
use ieee.numeric_std.all;

package ipbus_decode_tlu is

  constant IPBUS_SEL_WIDTH: positive := 5; -- Should be enough for now?
  subtype ipbus_sel_t is std_logic_vector(IPBUS_SEL_WIDTH - 1 downto 0);
  function ipbus_sel_ipbus_example(addr : in std_logic_vector(31 downto 0)) return ipbus_sel_t;

-- START automatically  generated VHDL the Fri Oct  7 12:10:31 2016 
  constant N_SLV_CTRL_REG: integer := 0; --for tests
  constant N_SLV_REG: integer := 1; -- for tests
  constant N_SLV_I2C_0: integer := 2; --I2C core for the TLU
  constant N_SLV_DUT: integer :=3;
  constant N_SLV_SHUT: integer :=4;
  constant N_SLV_EVBUF: integer :=5;
  constant N_SLV_EVFMT: integer :=6;
  constant N_SLV_TRGIN: integer :=7;
  constant N_SLV_TRGLGC: integer :=8;
  constant N_SLV_LGCCLK: integer :=9;
    
  constant N_SLAVES: integer := 10; --Total number of IPBus slaves
-- END automatically generated VHDL
  --constant N_I2C_CORES: integer := 3; --How many I2C cores
    
end ipbus_decode_tlu;

package body ipbus_decode_tlu is

  function ipbus_sel_ipbus_example(addr : in std_logic_vector(31 downto 0)) return ipbus_sel_t is
    variable sel: ipbus_sel_t;
  begin

-- START automatically  generated VHDL the Fri Oct  7 12:10:31 2016 
    if    std_match(addr, "----------------0000----------0-") then
        sel := ipbus_sel_t(to_unsigned(N_SLV_CTRL_REG, IPBUS_SEL_WIDTH)); -- ctrl_reg / base 0x00000000 / mask 0x00003002
    elsif std_match(addr, "----------------0000----------1-") then
        sel := ipbus_sel_t(to_unsigned(N_SLV_REG, IPBUS_SEL_WIDTH)); -- reg / base 0x00000002 / mask 0x00003002
    elsif std_match(addr, "----------------0001------------") then
        sel := ipbus_sel_t(to_unsigned(N_SLV_DUT, IPBUS_SEL_WIDTH)); -- ram / base 0x00001000 / mask 0x00003000
    elsif std_match(addr, "----------------0010----------0-") then
        sel := ipbus_sel_t(to_unsigned(N_SLV_SHUT, IPBUS_SEL_WIDTH)); -- shutter / base 0x00002000 / mask 0x00003002
    elsif std_match(addr, "----------------0011------------") then
        sel := ipbus_sel_t(to_unsigned(N_SLV_I2C_0, IPBUS_SEL_WIDTH)); -- i2c / base 0x00003000 / mask 0x00003002
    elsif std_match(addr, "----------------0100------------") then
        sel := ipbus_sel_t(to_unsigned(N_SLV_EVBUF, IPBUS_SEL_WIDTH)); -- event buffer / base 0x00004000 / mask 0x00003002
    elsif std_match(addr, "----------------0101------------") then
        sel := ipbus_sel_t(to_unsigned(N_SLV_EVFMT, IPBUS_SEL_WIDTH)); -- event formatter / base 0x00005000 / mask 0x00003002
    elsif std_match(addr, "----------------0110------------") then
        sel := ipbus_sel_t(to_unsigned(N_SLV_TRGIN, IPBUS_SEL_WIDTH)); -- trigger inputs / base 0x00006000 / mask 0x00003002
    elsif std_match(addr, "----------------0111------------") then
        sel := ipbus_sel_t(to_unsigned(N_SLV_TRGLGC, IPBUS_SEL_WIDTH)); -- trigger logic / base 0x00007000 / mask 0x00003002
    elsif std_match(addr, "----------------1000------------") then
        sel := ipbus_sel_t(to_unsigned(N_SLV_LGCCLK, IPBUS_SEL_WIDTH)); -- logic clocks / base 0x00008000 / mask 0x00003002
-- END automatically generated VHDL
 
    else
        sel := ipbus_sel_t(to_unsigned(N_SLAVES, IPBUS_SEL_WIDTH));
    end if;

    return sel;

  end function ipbus_sel_ipbus_example;

end ipbus_decode_tlu;

