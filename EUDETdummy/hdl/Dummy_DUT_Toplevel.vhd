-------------------------------------------------------------------------------
--! @file
--! @brief Top level of firmware for dummy JRA1-TLU
-------------------------------------------------------------------------------
-- File name: Dummy_DUT_Toplevel.vhd
-- Version: 0.1
-- Date: 20/Oct/2009
-- David Cussans
--
-- Changes
--
-------------------------------------------------------------------------------

library IEEE;
use IEEE.STD_LOGIC_1164.all;

use IEEE.NUMERIC_STD.all;

--! Use library for instantiating Xilinx primitive components.
--library UNISIM;
--use UNISIM.vcomponents.all;

--! include definition of TLU address map
use work.TLU_Address_Map_v02.all;

--! Top level with all the hardware ports.
entity Dummy_DUT_Toplevel is
  port (
    USB_StreamCLK      : in    std_logic;  --! 48MHz clock from FX2
    USB_StreamFIFOADDR : out   std_logic_vector(1 downto 0);
    USB_StreamPKTEND_n : out   std_logic;
    USB_StreamFlags_n  : in    std_logic_vector(2 downto 0);
    USB_StreamSLOE_n   : out   std_logic;
    USB_StreamSLRD_n   : out   std_logic;
    USB_StreamSLWR_n   : out   std_logic;
    USB_StreamData     : inout std_logic_vector(15 downto 0);
    USB_StreamFX2Rdy   : in    std_logic;

    USB_RegCLK  : in    std_logic; --! 48MHz clock from FX2
    USB_RegAddr : in    std_logic_vector(15 downto 0);
    USB_RegData : inout std_logic_vector(7 downto 0);
    USB_RegOE_n : in    std_logic;
    USB_RegRD_n : in    std_logic;
    USB_RegWR_n : in    std_logic;
    USB_RegCS_n : in    std_logic;

    USB_Interrupt : out std_logic;

    User_Signals : inout std_logic_vector(7 downto 0);

    S_CLK      : out   std_logic;
    S_A        : out   std_logic_vector(22 downto 0);
    S_DA       : inout std_logic_vector(8 downto 0);
    S_DB       : inout std_logic_vector(8 downto 0);
    S_ADV_LD_N : out   std_logic;
    S_BWA_N    : out   std_logic;
    S_BWB_N    : out   std_logic;
    S_OE_N     : out   std_logic;
    S_WE_N     : out   std_logic;

    IO_CLK_N : inout std_logic;         --! Posive side of differential user clock
    IO_CLK_P : inout std_logic;         --! Posive side of differential user clock
    IO       : inout std_logic_vector(46 downto 0)  --! The 47 I/O pins
    );
end Dummy_DUT_Toplevel;

architecture arch of Dummy_DUT_Toplevel is
	
  --! Declare interfaces component
  component ZestSC1_Interfaces
    port (
      --! FPGA pin connections
      USB_StreamCLK      : in    std_logic;
      USB_StreamFIFOADDR : out   std_logic_vector(1 downto 0);
      USB_StreamPKTEND_n : out   std_logic;
      USB_StreamFlags_n  : in    std_logic_vector(2 downto 0);
      USB_StreamSLOE_n   : out   std_logic;
      USB_StreamSLRD_n   : out   std_logic;
      USB_StreamSLWR_n   : out   std_logic;
      USB_StreamData     : inout std_logic_vector(15 downto 0);
      USB_StreamFX2Rdy   : in    std_logic;

      USB_RegCLK  : in    std_logic;
      USB_RegAddr : in    std_logic_vector(15 downto 0);
      USB_RegData : inout std_logic_vector(7 downto 0);
      USB_RegOE_n : in    std_logic;
      USB_RegRD_n : in    std_logic;
      USB_RegWR_n : in    std_logic;
      USB_RegCS_n : in    std_logic;

      USB_Interrupt : out std_logic;

      S_CLK      : out   std_logic;
      S_A        : out   std_logic_vector(22 downto 0);
      S_ADV_LD_N : out   std_logic;
      S_BWA_N    : out   std_logic;
      S_BWB_N    : out   std_logic;
      S_DA       : inout std_logic_vector(8 downto 0);
      S_DB       : inout std_logic_vector(8 downto 0);
      S_OE_N     : out   std_logic;
      S_WE_N     : out   std_logic;

      --! User connections
      --! Streaming interface
      User_CLK : out std_logic;
      User_RST : out std_logic;

      User_StreamBusGrantLength : in std_logic_vector(11 downto 0);

      User_StreamDataIn     : out std_logic_vector(15 downto 0);
      User_StreamDataInWE   : out std_logic;
      User_StreamDataInBusy : in  std_logic;

      User_StreamDataOut     : in  std_logic_vector(15 downto 0);
      User_StreamDataOutWE   : in  std_logic;
      User_StreamDataOutBusy : out std_logic;

      --! Register interface
      User_RegAddr    : out std_logic_vector(15 downto 0);
      User_RegDataIn  : out std_logic_vector(7 downto 0);
      User_RegDataOut : in  std_logic_vector(7 downto 0);
      User_RegWE      : out std_logic;
      User_RegRE      : out std_logic;

      --! Signals and interrupts
      User_Interrupt : in std_logic;

      --! SRAM interface
      User_SRAM_A        : in  std_logic_vector(22 downto 0);
      User_SRAM_W        : in  std_logic;
      User_SRAM_R        : in  std_logic;
      User_SRAM_DR_VALID : out std_logic;
      User_SRAM_DW       : in  std_logic_vector(17 downto 0);
      User_SRAM_DR       : out std_logic_vector(17 downto 0)
      );
  end component;

  component Register_Controller is

                                  port (

                                    --! Take clock from Zest interface block
                                    User_CLK : in std_logic;

                                    --! Register interface to USB
                                    User_RegAddr    : in  std_logic_vector(15 downto 0);
                                    User_RegDataIn  : in  std_logic_vector(7 downto 0);
                                    User_RegDataOut : out std_logic_vector(7 downto 0);
                                    User_RegWE      : in  std_logic;
                                    User_RegRE      : in  std_logic;

				    Logic_CLK : in std_logic;
				    
                                    --! Signals to trigger logic
                                    DUT_Reset : out std_logic_vector(NUMBER_OF_DUT-1 downto 0);  --separate bits for each DUT

                                    DUT_Trigger : out std_logic_vector(NUMBER_OF_DUT-1 downto 0);
                                    DUT_Debug_Trigger : out std_logic_vector(NUMBER_OF_DUT-1 downto 0);
                                    DUT_Busy : in std_logic_vector(NUMBER_OF_DUT-1 downto 0);  -- actual state of DUT
                                    DUT_Clock_Debug :  in std_logic_vector(NUMBER_OF_DUT-1 downto 0);  -- actual state of
                                                                                                       -- DUT_CLOCK

    				    I2C_Select : out std_logic_vector(WIDTH_OF_I2C_SELECT_PORT-1 downto 0); -- output to mux/demux that selects I2C ports

    				    I2C_SCL_OUT : out std_logic; -- drives SCL
    				    I2C_SCL_IN : in std_logic; -- state of SCL

    				    I2C_SDA_OUT : out std_logic; -- drives SDA
    				    I2C_SDA_IN : in std_logic; -- state of SDA

                                    -- Mask for beam trigger inputs. 
                                    Beam_Trigger_AMask   : out std_logic_vector(NUMBER_OF_BEAM_TRIGGERS-1 downto 0);
                                    Beam_Trigger_OMask   : out std_logic_vector(NUMBER_OF_BEAM_TRIGGERS-1 downto 0);
                                    Beam_Trigger_VMask   : out std_logic_vector(NUMBER_OF_BEAM_TRIGGERS-1 downto 0);
                                    
                                    Trigger_pattern      : out  std_logic_vector (15 downto 0);
                                    Aux_pattern          : out  std_logic_vector (15 downto 0);
    
                                    Beam_Trigger_Mask_WE : out std_logic;
                                    Beam_Trigger_Pattern_WE : out std_logic;
    
                                    --Beam trigger input for debugging.
                                    beam_trigger_in : in std_logic_vector(NUMBER_OF_BEAM_TRIGGERS-1 downto 0);
                                    calibration_trigger_interval : out std_logic_vector(7 downto 0);
                                    -- send trigger to, and receive busy from only certain DUT....
                                    DUT_Mask    : out std_logic_vector(NUMBER_OF_DUT-1 downto 0);
                                    enable_DUT_veto : out std_logic_vector(NUMBER_OF_DUT-1 downto 0); --
                                    --! controls if a DUT can halt triggers by
                                    --! raising DUT_CLK line.
                                    DUT_Mask_WE : out std_logic;

                                    -- because of 8-bit interface trigger a read of whole timestamp and then
                                    -- read each byte separately
                                    Timestamp : in std_logic_vector(TIMESTAMP_WIDTH-1 downto 0);

                                    Trigger_Counter : in std_logic_vector(TRIGGER_COUNTER_WIDTH-1 downto 0);
                                    Particle_Counter : in std_logic_vector(TRIGGER_COUNTER_WIDTH-1 downto 0);  -- fsv
                                    Auxiliary_Counter : in std_logic_vector(TRIGGER_COUNTER_WIDTH-1 downto 0);
                                    Trigger_Scalers : in TRIGGER_SCALER_ARRAY;
                                    Buffer_Pointer  : in std_logic_vector(BUFFER_COUNTER_WIDTH-1 downto 0);

                                    Trigger_Output_FSM_Status : in std_logic_vector(NUMBER_OF_DUT-1 downto 0);
                                    Trigger_FSM_State_Value : in std_logic_vector(( (NUMBER_OF_DUT*4)-1) downto 0);
                                    beam_trigger_fsm_status : in std_logic_vector(2 downto 0);
                                    DMA_Status : in std_logic;
                                    Host_Trig_Inhibit     : out std_logic;
                                    Trig_Enable_Status    : in  std_logic;  -- this is the overall status of the TLU ( incl. vetos from DUT)
                                    Clock_Source_Select   : out std_logic;
                                    Clock_DCM_Locked      : in std_logic;
                                    Reset_Timestamp       : out std_logic;
                                    Reset_Buffer_Pointer  : out std_logic;
                                    Reset_DMA_Controller  : out std_logic;
                                    Reset_ClockGen        : out std_logic;
                                    Initiate_Readout      : out std_logic;
                                    Reset_Trigger_Counter : out std_logic;
				    Reset_Trigger_Scalers : out std_logic;
                                    Reset_Trigger_Output_FSM : out std_logic;
                                    Reset_Beam_Trigger_FSM : out std_logic;
                                    Stop_if_Timestamp_Buffer_Full : out std_logic;
                                    strobe_width        : out std_logic_vector(STROBE_COUNTER_WIDTH-1 downto 0);
                                    strobe_period        : out std_logic_vector(STROBE_COUNTER_WIDTH-1 downto 0);
                                    write_strobe_data   : out std_logic;
                                    enable_strobe       : out std_logic;
                                    strobe_running      : in std_logic;
				    Write_Trigger_Bits_Mode : out std_logic;
                                    Trigger_Handshake_Mode : out std_logic_vector(NUMBER_OF_DUT-1 downto 0)
                                    );
  end component;

  -----------------------------------------------------------------------------
  
  component Dummy_DUT 
    Port ( 
           CLK : in  STD_LOGIC;         --! this is the USB clock.
	   RST : in STD_LOGIC;          --! Synchronous clock
           Trigger : in STD_LOGIC;      --! Trigger from TLU
           Busy : out STD_LOGIC;        --! Busy to TLU
           DUTClk : out STD_LOGIC;      --! clock from DUT
           TriggerNumber : out STD_LOGIC_VECTOR(15 downto 0);
           TriggerNumberStrobe : out STD_LOGIC;
           FSM_Error : out STD_LOGIC
           );
  end component;
      
  -----------------------------------------------------------------------------

  component Trigger_Number_Error_Checker is
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
end component;

  -----------------------------------------------------------------------------

  -- declaration of chipscope core ....
  
  component dummy_dut_chipscope_ila
  PORT (
    CONTROL : INOUT STD_LOGIC_VECTOR(35 DOWNTO 0);
    CLK : IN STD_LOGIC;
    TRIG0 : IN STD_LOGIC_VECTOR(15 DOWNTO 0);
    TRIG1 : IN STD_LOGIC_VECTOR(15 DOWNTO 0);
    TRIG2 : IN STD_LOGIC_VECTOR(3 DOWNTO 0));
  end component;

  component dummy_dut_chipscope_icon
  PORT (
    CONTROL0 : INOUT STD_LOGIC_VECTOR(35 DOWNTO 0));
  end component;

  -- Chipscope signals
  signal CONTROL : STD_LOGIC_VECTOR(35 DOWNTO 0);
  signal TRIG0 : STD_LOGIC_VECTOR(15 DOWNTO 0);
  signal TRIG1 : STD_LOGIC_VECTOR(15 DOWNTO 0);
  signal TRIG2 : STD_LOGIC_VECTOR(3 DOWNTO 0);
  

  -----------------------------------------------------------------------------

  
  -- Declare signals
  signal CLK  : std_logic;
  signal RST  : std_logic;

  -- Register interface
  signal Addr    : std_logic_vector(15 downto 0);
  signal DataIn  : std_logic_vector(7 downto 0);
  signal DataOut : std_logic_vector(7 downto 0);
  signal WE      : std_logic;
  signal RE      : std_logic;

  -- signals associated with streaming interface.
  signal Host_Data    : std_logic_vector(15 downto 0);
  signal Host_Data_WE : std_logic;
  signal Host_Busy    : std_logic;
  
  -- Interrupt signal
  -- not used in this design
  signal Interrupt : std_logic;


  -- Signals associated with DUT
  signal DUT_Reset        : std_logic_vector(NUMBER_OF_DUT-1 downto 0);  --separate bits for each DUT
  signal DUT_Busy : std_logic_vector(NUMBER_OF_DUT-1 downto 0);  -- actual state of DUT
  signal DUT_Clock :  std_logic_vector(NUMBER_OF_DUT-1 downto 0);  -- actual state of DUT_CLK
  signal DUT_Trigger :  std_logic_vector(NUMBER_OF_DUT-1 downto 0);  --

  subtype TriggerNumberType is std_logic_vector(15 downto 0);
  type TriggerNumberArray is array (NUMBER_OF_DUT-1 downto 0) of TriggerNumberType;
  signal TriggerNumber : TriggerNumberArray;  -- trigger number clocked out from TLU

  signal TriggerCounter : TriggerNumberArray;  -- trigger number inside
                                                 -- error checker
  
  signal TriggerNumberStrobe : std_logic_vector(NUMBER_OF_DUT-1 downto 0);  -- strobes high

  signal ErrorFlag : std_logic_vector(NUMBER_OF_DUT-1 downto 0);  -- strobes high

  -- I2C signals
  signal I2C_Select : std_logic_vector(WIDTH_OF_I2C_SELECT_PORT-1 downto 0); 
  signal I2C_SDA_OUT :std_logic; 
  signal I2C_SCL_OUT :std_logic; 
  signal I2C_SDA_IN  :std_logic; 
  signal I2C_SCL_IN  :std_logic; 
  
  signal trigger_scalers : TRIGGER_SCALER_ARRAY;  -- array of 16 bit registers
  
-- a bodge, since I can't figure out how to make it work with aggregates.
  -- declare a constant for the unused IO => .
  constant unused_io : std_logic_vector(7 downto 0) := "ZZZZZZZZ" ;

  for all : zestsc1_interfaces use entity work.zestsc1_interfaces(arch);

-----------------------------------------------------------------------
-- end of declarations start of instantiation
-----------------------------------------------------------------------

begin



  -- let unused IO float for now 
  (  IO(7) , IO(10) , IO(19) , IO(24) ,
     IO(33) , IO(39) , IO(40) , IO(45) ) <= unused_io;
  
    -- Instantiate interfaces component
  Interfaces : ZestSC1_Interfaces
    port map (
      USB_StreamCLK      => USB_StreamCLK,
      USB_StreamFIFOADDR => USB_StreamFIFOADDR,
      USB_StreamPKTEND_n => USB_StreamPKTEND_n,
      USB_StreamFlags_n  => USB_StreamFlags_n,
      USB_StreamSLOE_n   => USB_StreamSLOE_n,
      USB_StreamSLRD_n   => USB_StreamSLRD_n,
      USB_StreamSLWR_n   => USB_StreamSLWR_n,
      USB_StreamData     => USB_StreamData,
      USB_StreamFX2Rdy   => USB_StreamFX2Rdy,

      USB_RegCLK  => USB_RegCLK,
      USB_RegAddr => USB_RegAddr,
      USB_RegData => USB_RegData,
      USB_RegOE_n => USB_RegOE_n,
      USB_RegRD_n => USB_RegRD_n,
      USB_RegWR_n => USB_RegWR_n,
      USB_RegCS_n => USB_RegCS_n,

      USB_Interrupt => USB_Interrupt,

      S_CLK      => S_CLK,
      S_A        => S_A,
      S_ADV_LD_N => S_ADV_LD_N,
      S_BWA_N    => S_BWA_N,
      S_BWB_N    => S_BWB_N,
      S_DA       => S_DA,
      S_DB       => S_DB,
      S_OE_N     => S_OE_N,
      S_WE_N     => S_WE_N,

      -- User connections
      -- Streaming interface
      User_CLK => CLK,
      -- bodge for simulation
      -- User_CLK => open,
      User_RST => RST,

      User_StreamBusGrantLength => "100000000000",  --! In clock cycles.
--      User_StreamBusGrantLength => X"100",  -- In clock cycles. Clutching at
--                                           --straws, make this the same as
--                                           --Example2.vhd ( i.e. 256 cycles not
--                                           --2048 )
--
      User_StreamDataIn     => open,
      User_StreamDataInWE   => open,
      User_StreamDataInBusy => '1',

      User_StreamDataOut     => Host_Data,
      User_StreamDataOutWE   => Host_Data_WE,
      User_StreamDataOutBusy => Host_Busy,

      -- Register interface
      User_RegAddr    => Addr,
      User_RegDataIn  => DataIn,
      User_RegDataOut => DataOut,
      User_RegWE      => WE,
      User_RegRE      => RE,

      -- Interrupts
      User_Interrupt => Interrupt,

      -- SRAM interface
      User_SRAM_A        => "00000000000000000000000",
      User_SRAM_W        => '0',
      User_SRAM_R        => '0',
      User_SRAM_DR_VALID => open,
      User_SRAM_DW       => "000000000000000000",
      User_SRAM_DR       => open
      );


    reg_ctrl : Register_Controller
    port map (

      -- Take clock from Zest interface block
      User_CLK => clk,

      -- Register interface
      User_RegAddr    => Addr,
      User_RegDataIn  => DataIn,
      User_RegDataOut => DataOut,
      User_RegWE      => WE,
      User_RegRE      => RE,

      Logic_CLK => clk,
      
      -- Signals to trigger logic
--      DUT_Reset => ,           --separate bits for each DUT

--      DUT_Trigger => Host_DUT_Trigger,

--      DUT_Debug_Trigger => Host_DUT_Debug_Trigger , 
      DUT_Busy => DUT_Busy,             -- actual state of DUT
      DUT_Clock_Debug => DUT_Clock,

      I2C_Select  => I2C_Select ,
      I2C_SCL_OUT => I2C_SCL_OUT ,
      I2C_SCL_IN  => I2C_SCL_IN ,
      I2C_SDA_OUT => I2C_SDA_OUT,
      I2C_SDA_IN  => I2C_SDA_IN ,
  
      -- Mask for beam trigger inputs. 
--      Beam_Trigger_AMask   => open,
--      Beam_Trigger_OMask   => open,
--      Beam_Trigger_VMask   => open,
--      Beam_Trigger_Mask_WE => open,
      
      				    
--      Trigger_pattern	=> open,
--      Aux_pattern	=> open,
--      Beam_Trigger_Pattern_WE	=> beam_trigger_pattern_we,


      --Beam trigger input for debugging.
      beam_trigger_in => ( others => '0'),

--      calibration_trigger_interval => Calibration_Trigger_Interval,
      
      -- send trigger to, and receive busy from only certain DUT....
--      DUT_Mask    => DUT_Mask,
--      DUT_Mask_WE => DUT_MAsk_WE,

      -- because of 8-bit interface trigger a read of whole timestamp and then
      -- read each byte separately
      Timestamp => ( others => '0'),

      Trigger_Counter => ( others => '0'),
      Particle_Counter => ( others => '0'),   --  fsv
      Auxiliary_Counter => ( others => '0'),                        
      Trigger_Scalers => trigger_scalers,
      
      Buffer_Pointer  => ( others => '0'),

      Trigger_Output_FSM_Status => ( others => '0'),
      Trigger_FSM_State_Value => ( others => '0'),
      beam_trigger_fsm_status => ( others => '0'),
      DMA_Status => '0',
--      Host_Trig_Inhibit  => host_veto,
      Trig_Enable_Status => '0',
      
--      Clock_Source_Select => Clock_Source_Select,    
      Clock_DCM_Locked => '0' , 
---      Reset_Timestamp    => Reset_Timestamp,
--      Reset_Buffer_Pointer => Reset_Buffer_Pointer,
--      Reset_DMA_Controller => Reset_DMA_Controller,
--      Reset_ClockGen => Reset_ClockGen ,
--      Initiate_Readout => Initiate_Readout,
--     Reset_Trigger_Counter => Reset_Trigger_Counter,
--      Reset_Trigger_Scalers => Reset_Trigger_Scalers,
--      Reset_Trigger_Output_FSM => trigger_fsm_reset,
--      Reset_Beam_Trigger_FSM => beam_trigger_fsm_reset,
--      Stop_if_Timestamp_Buffer_Full => stop_if_buffer_full,
--      strobe_width   =>   strobe_width ,
--      strobe_period  =>   strobe_period , 
--      write_strobe_data   =>   write_strobe_data , 
--      enable_strobe => enable_strobe , 
      strobe_running => '0' 
--      Write_Trigger_Bits_Mode => write_trigger_bits_mode,
--      Trigger_Handshake_Mode => dut_trigger_handshake_mode
      );

-- bodge for simulation:
--  clk <= usb_streamclk ;
  
----------------------------------------------
-- Use a generate statement to generate the required number of
-- trigger outputs.
  Trigger_Outputs :
  for DUT in 0 to NUMBER_OF_DUT-1 generate
  begin
  
    -- connect up the input pins to the internal signals.
    -- odd numbered inputs are inverted to reduce ground bounce in LVDS-->TTL converters
    -- the odd-numbered outputs are inverted to reduce ground bounce.

    -- Cross the TRIGGER-->BUSY and DUT_CLK-->Reset lines to allow connection
    -- to TLU

    -- Trigger and Reset are inputs to the Dummy DUT, but wired to BUSY and
    -- CLOCK lines.
    inverted_inputs: if ( (DUT=1) or (DUT=3) or (DUT=5) ) generate
      DUT_Trigger(DUT) <= not IO(DUT_BUSY_BIT(DUT));
      DUT_Reset(DUT)   <= not IO(DUT_CLOCK_BIT(DUT));
    end generate inverted_inputs;
    
    noninverted_inputs: if ( (DUT=0) or (DUT=2) or (DUT=4) ) generate
      DUT_Trigger(DUT) <= IO(DUT_BUSY_BIT(DUT));
      DUT_Reset(DUT)   <= IO(DUT_CLOCK_BIT(DUT));
    end generate noninverted_inputs;

    ---------------------------------------------------------------------------
    -- Busy and DUT_Clock are *outputs* from the Dummy DUT, but wired to
    -- TRIGGER and RESET outputs.
    inverted_outputs: if ( (DUT=1) or (DUT=3) or (DUT=5) ) generate
      IO(TRIGGER_OUTPUT_BIT(DUT)) <= not DUT_Busy(DUT);
      IO(DUT_RESET_BIT(DUT)) <= not DUT_Clock(DUT);
    end generate inverted_outputs;

    noninverted_outputs: if ( (DUT=0) or (DUT=2) or (DUT=4) ) generate
      IO(TRIGGER_OUTPUT_BIT(DUT)) <= DUT_Busy(DUT);
      IO(DUT_RESET_BIT(DUT)) <= DUT_Clock(DUT);
    end generate noninverted_outputs;

    -- generate an instance of the Dummy DUT behind each connector
    DUT_Instance: Dummy_DUT 
      Port map ( 
           CLK => CLK,
           RST => DUT_Reset(DUT),
           Trigger => DUT_Trigger(DUT),
           Busy => DUT_Busy(DUT),
           DUTClk => DUT_Clock(DUT),
           TriggerNumber => TriggerNumber(DUT),
           TriggerNumberStrobe => TriggerNumberStrobe(DUT), 
           FSM_Error => open
           );

    -- generate an instance of an error checker for each DUT
    error_checker_instance :  Trigger_Number_Error_Checker 
      Port map (
        CLK => CLK,
        RST => DUT_Reset(DUT),
        TriggerNumber => TriggerNumber(DUT),
        TriggerNumberStrobe => TriggerNumberStrobe(DUT),
        TriggerCounter => TriggerCounter(DUT), 
        ErrorFlag => ErrorFlag(DUT)
        );
      
  end generate;

  -- chipscope instrumentation
  icon0 : dummy_dut_chipscope_icon
  port map (
    CONTROL0 => CONTROL );

  ila0 : dummy_dut_chipscope_ila
  port map (
    CONTROL => CONTROL,
    CLK => CLK,
    TRIG0 => TRIG0,
    TRIG1 => TRIG1,
    TRIG2 => TRIG2);

   -- copy signals to the Chipscope core ports...
  TRIG0 <= TriggerNumber(0);
  TRIG1 <= TriggerCounter(0);
  TRIG2(0) <= ErrorFlag(0);
  TRIG2(1) <= TriggerNumberStrobe(0);
  TRIG2(2) <= DUT_Reset(0);
  TRIG2(3) <= DUT_Trigger(0);
  
---------------------------------------------------------------

-- connect up I2C bus-select lines.
 i2c_bus_select: for BUS_ID in 0 to WIDTH_OF_I2C_SELECT_PORT-1 generate
  begin
    IO(I2C_BUS_SELECT_IO_BITS(BUS_ID)) <= I2C_Select(BUS_ID);
  end generate;

  -- conenct up I2C data lines
  IO(I2C_SCL_OUT_IO_BIT) <= I2C_SCL_OUT;
  IO(I2C_SDA_OUT_IO_BIT) <= I2C_SDA_OUT;
  I2C_SCL_IN <= IO(I2C_SCL_IN_IO_BIT);
  I2C_SDA_IN <= IO(I2C_SDA_IN_IO_BIT);
    
	-- connect up BEAM_TRIGGER and CLK to GPIO for debugging...
  IO(GPIO_BIT(0)) <= DUT_Trigger(0);
  IO(GPIO_BIT(1)) <= DUT_Reset(0);
  IO(GPIO_BIT(2)) <= DUT_Busy(0);
  IO(GPIO_BIT(3)) <= ErrorFlag(0); -- DUT_Clock(0);
  
end arch;
