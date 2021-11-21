--=============================================================================
--! @file fmcTLU_pkg.vhd
--=============================================================================
---
--! @brief VHDL Package Header fmc_mTLU_lib.fmcTLU
--
--! @author  phdgc
--! @date  16:44:31 11/08/12         
--
-- using Mentor Graphics HDL Designer(TM) 2010.3 (Build 21)
--
LIBRARY ieee;
USE ieee.std_logic_1164.all;
PACKAGE fmcTLU IS
  
  constant c_NUM_TIME_BITS : natural := 5;
  constant c_NUM_TRIG_INPUTS : natural := 4;
  constant c_EVENT_DATA_WIDTH : natural := 32;
  constant c_DATA_WIDTH : natural := 32;
  
  subtype t_triggerTime is std_logic_vector(c_NUM_TIME_BITS-1 downto 0);
  --type    t_triggerTimeArray is array(natural range <>) of t_triggerTime;
  type    t_triggerTimeArray is array(natural range <>) of std_logic_vector(c_NUM_TIME_BITS-1 downto 0) ;

  type t_registerArray is array(natural range <>) of std_logic_vector(c_DATA_WIDTH-1 downto 0) ;
  
END fmcTLU;
