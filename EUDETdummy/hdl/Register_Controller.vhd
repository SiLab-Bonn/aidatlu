library IEEE;
use IEEE.STD_LOGIC_1164.all;
use IEEE.STD_LOGIC_ARITH.all;
use IEEE.STD_LOGIC_UNSIGNED.all;

-- include address map declarations
use work.TLU_Address_Map.all;

entity Register_Controller is

  port (

    -- Take clock from Zest interface block
    User_CLK : in std_logic;

    -- Register interface to USB
    User_RegAddr    : in  std_logic_vector(15 downto 0);
    User_RegDataIn  : in  std_logic_vector(7 downto 0);
    User_RegDataOut : out std_logic_vector(7 downto 0);
    User_RegWE      : in  std_logic;
    User_RegRE      : in  std_logic;
    
    -- Take clock from trigger logic.
    Logic_CLK : in std_logic;
    
    -- Signals to trigger logic
    DUT_Reset : out std_logic_vector(NUMBER_OF_DUT-1 downto 0);  --separate bits for each DUT

    DUT_Trigger : out std_logic_vector(NUMBER_OF_DUT-1 downto 0);
                  --separate bits for each DUT. Fed via trigger controller,
                  -- so vetoed if DUT does not respond.

    DUT_Debug_Trigger : out std_logic_vector(NUMBER_OF_DUT-1 downto 0);
                  --separate bits for each DUT. Fed straight to output pins
          
    DUT_Busy : in std_logic_vector(NUMBER_OF_DUT-1 downto 0);  -- actual state of DUT
    DUT_Clock_Debug :  in std_logic_vector(NUMBER_OF_DUT-1 downto 0);  -- actual state
                                                                       -- of dut_clk
    DUT_Leds : out std_logic_vector(NUMBER_OF_DUT-1 downto 0);  -- LED on each
                                                                -- RJ45

    -- Mask for beam trigger inputs. 
    Beam_Trigger_AMask   : out std_logic_vector(NUMBER_OF_BEAM_TRIGGERS-1 downto 0) := ( others => '1' ) ;
    Beam_Trigger_OMask   : out std_logic_vector(NUMBER_OF_BEAM_TRIGGERS-1 downto 0) := ( others => '0' ) ;
    Beam_Trigger_VMask   : out std_logic_vector(NUMBER_OF_BEAM_TRIGGERS-1 downto 0);
    Beam_Trigger_Mask_WE : out std_logic;

    --Beam trigger input for debugging.
    beam_trigger_in : in std_logic_vector(NUMBER_OF_BEAM_TRIGGERS-1 downto 0);

    calibration_trigger_interval : out std_logic_vector(7 downto 0);
    
    -- send trigger to, and receive busy from only certain DUT....
    DUT_Mask    : out std_logic_vector(NUMBER_OF_DUT-1 downto 0);
    DUT_Mask_WE : out std_logic;

    -- because of 8-bit interface trigger a read of whole timestamp and then
    -- read each byte separately
    -- this is the current value of the timestamp
    Timestamp : in std_logic_vector(TIMESTAMP_WIDTH-1 downto 0);

    Trigger_Counter : in std_logic_vector(TRIGGER_COUNTER_WIDTH-1 downto 0);
    Particle_Counter : in std_logic_vector(TRIGGER_COUNTER_WIDTH-1 downto 0);  -- fsv
   
    Trigger_Scalers : in TRIGGER_SCALER_ARRAY;

    Buffer_Pointer  : in std_logic_vector(BUFFER_COUNTER_WIDTH-1 downto 0);

    Trigger_Output_FSM_Status : in std_logic_vector(NUMBER_OF_DUT-1 downto 0);
    beam_trigger_fsm_status : in std_logic_vector(2 downto 0);
    DMA_Status : in std_logic;
    Host_Trig_Inhibit     : out std_logic;  -- this is the trigger inhibit controlled by the host
    Trig_Enable_Status    : in  std_logic;  -- this is the overall status of the TLU ( incl. vetos from DUT)
    Clock_Source_Select   : out std_logic;
    Reset_Timestamp       : out std_logic;
    Reset_Buffer_Pointer  : out std_logic;
    Reset_DMA_Controller  : out std_logic;
    Initiate_Readout      : out std_logic;
    Reset_Trigger_Counter : out std_logic;
    Reset_Trigger_Scalers : out std_logic;
    Reset_Trigger_Output_FSM : out std_logic;
    Reset_Beam_Trigger_FSM : out std_logic
    );

end Register_Controller;


architecture rtl of Register_Controller is

  component Select_Scaler
  port (
    trigger_scaler : in  TRIGGER_SCALER;
                                        -- 16-bit register holding scintillator counts
    low_byte_out       : out std_logic_vector(7 downto 0);  -- output to USB i/face
    high_byte_out       : out std_logic_vector(7 downto 0)  -- output to USB i/face
    );
  end component;
  
  signal Output_Data : std_logic_vector(7 downto 0);
  -- output data after Mux, before output reg

  --    signal Internal_Trig_Inhibit : std_logic;  
  --                              -- can't read an output port, so declare a dummy signal

  signal Buffer_Pointer_Register :
    std_logic_vector(BUFFER_POINTER_WIDTH-1 downto 0);
  -- stores the buffer pointer after capture
  signal Timestamp_Register :
    std_logic_vector(TIMESTAMP_WIDTH-1 downto 0);
  -- stores timestamp after capture
  signal Trigger_Counter_Register :
    std_logic_vector(TRIGGER_COUNTER_WIDTH-1 downto 0);
  -- stores the trigger counter after capture

    signal Particle_Counter_Register :
    std_logic_vector(TRIGGER_COUNTER_WIDTH-1 downto 0);
  -- fsv -- stores the Particle counter after capture

  signal Internal_DUT_Mask : std_logic_vector(NUMBER_OF_DUT-1 downto 0);
                                        -- can't read output port, so declare a dummy signal....

  signal Internal_DUT_Leds : std_logic_vector(NUMBER_OF_DUT-1 downto 0);
                                        -- can't read output port, so declare a dummy signal....

  signal Internal_Debug_Trigger : std_logic_vector(NUMBER_OF_DUT-1 downto 0);
                                        -- can't read output port, so declare a dummy signal....

  signal Internal_DUT_Reset : std_logic_vector(NUMBER_OF_DUT-1 downto 0);
                                        -- can't read output port, so declare a dummy signal....

  signal Internal_Calibration_Trigger_Interval : std_logic_vector(CALIBRATION_TRIGGER_COUNTER_WIDTH-1 downto 0) := "00000000";
                                 -- interval between calibration triggers, in units of milli-seconds. Zero turns off triggers
  
  signal Internal_Host_Trig_Inhibit : std_logic :='1';

  signal Internal_Clock_Source_Select : std_logic :='1';

  signal Internal_Beam_Trigger_AMask  : std_logic_vector(NUMBER_OF_BEAM_TRIGGERS-1 downto 0);
  signal Internal_Beam_Trigger_OMask  : std_logic_vector(NUMBER_OF_BEAM_TRIGGERS-1 downto 0);
  signal Internal_Beam_Trigger_VMask  : std_logic_vector(NUMBER_OF_BEAM_TRIGGERS-1 downto 0);

  signal Registered_Trigger_Scalers : TRIGGER_SCALER_ARRAY;  
                                        -- register the scalers...
  signal registered_scaler0 : TRIGGER_SCALER;
  signal registered_scaler1 : TRIGGER_SCALER;
  signal registered_scaler2 : TRIGGER_SCALER;
  signal registered_scaler3 : TRIGGER_SCALER;
  
  signal Trigger_Scaler0_low : std_logic_vector(7 downto 0);
  signal Trigger_Scaler0_high : std_logic_vector(7 downto 0);
  signal Trigger_Scaler1_low : std_logic_vector(7 downto 0);
  signal Trigger_Scaler1_high : std_logic_vector(7 downto 0);
  signal Trigger_Scaler2_low : std_logic_vector(7 downto 0);
  signal Trigger_Scaler2_high : std_logic_vector(7 downto 0);
  signal Trigger_Scaler3_low : std_logic_vector(7 downto 0);
  signal Trigger_Scaler3_high : std_logic_vector(7 downto 0);
  
begin  -- architecture rtl


  -- purpose: selects which of inputs gets multiplexed to readout bus
  -- type   : combinational
  -- inputs : clk,addr,rw
  -- outputs: User_RegDataOut
  -- fsv add Particle_Counter_Register
  read_mux : process (User_RegAddr, User_CLK , DUT_Busy, DUT_Clock_Debug, Internal_Host_Trig_Inhibit,
                      Trig_Enable_Status, Buffer_Pointer_Register, Timestamp_Register,
                      Trigger_Counter_Register, Particle_Counter_Register, Timestamp, Trigger_Counter, Internal_DUT_Mask,
                      Internal_DUT_Leds, Trigger_Output_FSM_Status, DMA_Status) is
  begin  -- process read_mux

    if (
      -- don't clock in data - it doesn't seem to work!
        -- User_CLK'event and User_CLK = '1'
        -- and User_RegRE = '1'
        -- and
        User_RegAddr(15 downto 6) = BASE_ADDRESS(15 downto 6)) then

      case User_RegAddr(5 downto 0) is

        -- read firmware ID
        when FIRMWARE_ID_ADDRESS =>
          Output_Data <= FIRMWARE_ID;

          -- read staus of DUT_BUSY lines.
        when DUT_BUSY_ADDRESS =>
          Output_Data(NUMBER_OF_DUT-1 downto 0) <= DUT_Busy;
          Output_Data(7 downto NUMBER_OF_DUT)   <= (others => '0');

        -- read DUT_CLOCK ( aka DUT_TRIGGER_DATA ) lines
        when DUT_CLOCK_DEBUG_ADDRESS =>
          Output_Data(NUMBER_OF_DUT-1 downto 0) <= DUT_Clock_Debug;
          Output_Data(7 downto NUMBER_OF_DUT)   <= (others => '0');


          -- read state of trigger inhibit line
        when TRIG_INHIBIT_ADDRESS =>
          Output_Data(0) <= Internal_Host_Trig_Inhibit;
          Output_Data(1) <= Trig_Enable_Status;
          Output_Data(7 downto 2)   <= (others => '0');

        when CLOCK_SOURCE_SELECT_ADDRESS =>
          Output_Data(0) <= Internal_Clock_Source_Select;
          Output_Data(7 downto 1)   <= (others => '0');

        -- interval between internal triggersa
        when INTERNAL_TRIGGER_INTERVAL =>
          Output_Data(7 downto 0) <= Internal_Calibration_Trigger_Interval;
          
          -- read buffer pointer
          -- for now assume a 16-bit buffer pointer
        when REGISTERED_BUFFER_POINTER_ADDRESS_0 =>
          Output_Data <= Buffer_Pointer_Register(7 downto 0);
        when REGISTERED_BUFFER_POINTER_ADDRESS_1 =>
          Output_Data <= Buffer_Pointer_Register(15 downto 8);

          -- read buffer pointer
          -- for now assume a 16-bit buffer pointer
        when BUFFER_POINTER_ADDRESS_0 =>
          Output_Data <= Buffer_Pointer(7 downto 0);
        when BUFFER_POINTER_ADDRESS_1 =>
          Output_Data(BUFFER_COUNTER_WIDTH-9 downto 0) <= Buffer_Pointer(BUFFER_COUNTER_WIDTH-1 downto 8);
			 Output_Data(7 downto BUFFER_COUNTER_WIDTH-8) <= (others => '0');
          
          -- read timestamp
          -- assume a 64-bit timestamp
        when REGISTERED_TIMESTAMP_ADDRESS_0 =>
          Output_Data <= Timestamp_Register(7 downto 0);
        when REGISTERED_TIMESTAMP_ADDRESS_1 =>
          Output_Data <= Timestamp_Register(15 downto 8);
        when REGISTERED_TIMESTAMP_ADDRESS_2 =>
          Output_Data <= Timestamp_Register(23 downto 16);
        when REGISTERED_TIMESTAMP_ADDRESS_3 =>
          Output_Data <= Timestamp_Register(31 downto 24);
        when REGISTERED_TIMESTAMP_ADDRESS_4 =>
          Output_Data <= Timestamp_Register(39 downto 32);
        when REGISTERED_TIMESTAMP_ADDRESS_5 =>
          Output_Data <= Timestamp_Register(47 downto 40);
        when REGISTERED_TIMESTAMP_ADDRESS_6 =>
          Output_Data <= Timestamp_Register(55 downto 48);
        when REGISTERED_TIMESTAMP_ADDRESS_7 =>
          Output_Data <= Timestamp_Register(63 downto 56);

          -- read registered trigger counter.
          -- assume a 32-bit trigger counter
        when REGISTERED_TRIGGER_COUNTER_ADDRESS_0 =>
          Output_Data <= Trigger_Counter_Register(7 downto 0);
        when REGISTERED_TRIGGER_COUNTER_ADDRESS_1 =>
          Output_Data <= Trigger_Counter_Register(15 downto 8);
        when REGISTERED_TRIGGER_COUNTER_ADDRESS_2 =>
          Output_Data <= Trigger_Counter_Register(23 downto 16);
        when REGISTERED_TRIGGER_COUNTER_ADDRESS_3 =>
          Output_Data <= Trigger_Counter_Register(31 downto 24);

          -- read registered Particle counter.  -- fsv  --
          -- assume a 32-bit trigger counter
        when REGISTERED_PARTICLE_COUNTER_ADDRESS_0 =>
          Output_Data <= Particle_Counter_Register(7 downto 0);
        when REGISTERED_PARTICLE_COUNTER_ADDRESS_1 =>
          Output_Data <= Particle_Counter_Register(15 downto 8);
        when REGISTERED_PARTICLE_COUNTER_ADDRESS_2 =>
          Output_Data <= Particle_Counter_Register(23 downto 16);
        when REGISTERED_PARTICLE_COUNTER_ADDRESS_3 =>
          Output_Data <= Particle_Counter_Register(31 downto 24);

          -- read unregistered timestamp
          -- assume a 64-bit timestamp
        when TIMESTAMP_ADDRESS_0 =>
          Output_Data <= Timestamp(7 downto 0);
        when TIMESTAMP_ADDRESS_1 =>
          Output_Data <= Timestamp(15 downto 8);
        when TIMESTAMP_ADDRESS_2 =>
          Output_Data <= Timestamp(23 downto 16);
        when TIMESTAMP_ADDRESS_3 =>
          Output_Data <= Timestamp(31 downto 24);
        when TIMESTAMP_ADDRESS_4 =>
          Output_Data <= Timestamp(39 downto 32);
        when TIMESTAMP_ADDRESS_5 =>
          Output_Data <= Timestamp(47 downto 40);
        when TIMESTAMP_ADDRESS_6 =>
          Output_Data <= Timestamp(55 downto 48);
        when TIMESTAMP_ADDRESS_7 =>
          Output_Data <= Timestamp(63 downto 56);

          -- read unregisteredtrigger counter.
          -- assume a 32-bit trigger counter
        when TRIGGER_COUNTER_ADDRESS_0 =>
          Output_Data <= Trigger_Counter(7 downto 0);
        when TRIGGER_COUNTER_ADDRESS_1 =>
          Output_Data <= Trigger_Counter(15 downto 8);
        when TRIGGER_COUNTER_ADDRESS_2 =>
          Output_Data <= Trigger_Counter(23 downto 16);
        when TRIGGER_COUNTER_ADDRESS_3 =>
          Output_Data <= Trigger_Counter(31 downto 24);

          -- read status of DUT mask
        when DUT_MASK_ADDRESS                              =>
          Output_Data(NUMBER_OF_DUT-1 downto 0) <= Internal_DUT_Mask;
          Output_Data(7 downto NUMBER_OF_DUT)   <= (others => '0');

          -- read status of LEDs
        when DUT_LED_ADDRESS                               =>
          Output_Data(NUMBER_OF_DUT-1 downto 0) <= Internal_DUT_Leds;
          Output_Data(7 downto NUMBER_OF_DUT)   <= (others => '0');

        -- read status of debugging trigger (connected to dut trigger
        -- outputs without trigger/busy handshake.
        when DUT_DEBUG_TRIGGER_ADDRESS                     =>
          Output_Data(NUMBER_OF_DUT-1 downto 0) <= Internal_Debug_Trigger;
          Output_Data(7 downto NUMBER_OF_DUT)   <= (others => '0');

        -- read status of beam trigger inputs
        -- (useful for debugging)
        when BEAM_TRIGGER_IN_ADDRESS          =>
          Output_Data(NUMBER_OF_BEAM_TRIGGERS-1 downto 0) <= beam_trigger_in;
          Output_Data(7 downto NUMBER_OF_BEAM_TRIGGERS)   <= (others => '0');


        -- read status of beam_trigger_omask, amask , vmask
        when BEAM_TRIGGER_OMASK_ADDRESS        =>
          Output_Data(NUMBER_OF_BEAM_TRIGGERS-1 downto 0) <= Internal_Beam_Trigger_OMask;
          Output_Data(7 downto NUMBER_OF_BEAM_TRIGGERS)   <= (others => '0');

        when BEAM_TRIGGER_AMASK_ADDRESS        =>
          Output_Data(NUMBER_OF_BEAM_TRIGGERS-1 downto 0) <= Internal_Beam_Trigger_AMask;
          Output_Data(7 downto NUMBER_OF_BEAM_TRIGGERS)   <= (others => '0');

        when BEAM_TRIGGER_VMASK_ADDRESS        =>
          Output_Data(NUMBER_OF_BEAM_TRIGGERS-1 downto 0) <= Internal_Beam_Trigger_VMask;
          Output_Data(7 downto NUMBER_OF_BEAM_TRIGGERS)   <= (others => '0');

        -- read status of reset lines
        when DUT_RESET_ADDRESS                     =>
          Output_Data(NUMBER_OF_DUT-1 downto 0) <= Internal_DUT_Reset;
          Output_Data(7 downto NUMBER_OF_DUT)   <= (others => '0');          

        when TRIGGER_FSM_STATUS_ADDRESS =>
          Output_Data(NUMBER_OF_DUT-1 downto 0) <= Trigger_Output_FSM_Status;
          Output_Data(7 downto NUMBER_OF_DUT)   <= (others => '0');

        when BEAM_TRIGGER_FSM_STATUS_ADDRESS =>
          Output_Data(2 downto 0) <= beam_trigger_fsm_status;
          Output_Data(7 downto 3)   <= (others => '0');
          
        when DMA_STATUS_ADDRESS =>
          Output_Data(0) <= DMA_Status;
          Output_Data(7 downto 1)   <= (others => '0');
          
--          trigger_scaler_read_mux:
--            for BEAM_TRIGGER_IDX in 0 to NUMBER_OF_BEAM_TRIGGERS-1 generate
--              high_low:
--                for HIGH_LOW_BYTE in 0 to 1 generate
--                  when (TRIGGER_IN0_COUNTER_0 + BEAM_TRIGGER_IDX*2 + HIGH_LOW_BYTE) =>                    
--                    register_scaler: Select_Scaler
--                      port map (
--                        trigger_scaler => Trigger_Scalers(BEAM_TRIGGER_IDX1),
--                        byte_select => HIGH_LOW_BYTE1,
--                        byte_out => Output_Data
--                        );
--                end generate;  -- HIGH_LOW
--            end generate;  -- BEAM_TRIGGER_IDX
--                    Output_Data <= Registered_Trigger_Scaler_Byte(BEAM_TRIGGER_IDX*2 + HIGH_LOW_BYTE);

        when TRIGGER_IN0_COUNTER_0 =>
          Output_Data <= Trigger_Scaler0_low;

        when TRIGGER_IN0_COUNTER_1 =>
          Output_Data <= Trigger_Scaler0_high;

        when TRIGGER_IN1_COUNTER_0 =>
          Output_Data <= Trigger_Scaler1_low;

        when TRIGGER_IN1_COUNTER_1 =>
          Output_Data <= Trigger_Scaler1_high;

        when TRIGGER_IN2_COUNTER_0 =>
          Output_Data <= Trigger_Scaler2_low;

        when TRIGGER_IN2_COUNTER_1 =>
          Output_Data <= Trigger_Scaler2_high;

        when TRIGGER_IN3_COUNTER_0 =>
          Output_Data <= Trigger_Scaler3_low;

        when TRIGGER_IN3_COUNTER_1 =>
          Output_Data <= Trigger_Scaler3_high;          

          
        when others =>
          -- if the address is out of range return zero
          --Output_Data(7 downto 0)   <= (others => '0');
			 null;
			 
      end case;

      --else
      --  -- if the address is out of range return zero
      --  Output_Data(7 downto 0)   <= (others => '0');
    end if;

  end process read_mux;

--  trigger_scaler_register_mux:
--  for BEAM_TRIGGER_IDX1 in 0 to NUMBER_OF_BEAM_TRIGGERS-1 generate
--    high_low1:
--    for HIGH_LOW_BYTE1 in 0 to 1 generate
--      register_scaler: Select_Scaler
--        port map (
--          trigger_scaler => Trigger_Scalers(BEAM_TRIGGER_IDX1),
--          byte_select => HIGH_LOW_BYTE1,
--          byte_out => Registered_Scaler_Byte(BEAM_TRIGGER_IDX1*2 + HIGH_LOW_BYTE1)
--          );
--    end generate;  -- HIGH_LOW
--  end generate;  -- BEAM_TRIGGER_IDX

--              Registered_Scaler <= Registered_Trigger_Scalers(BEAM_TRIGGER_IDX);
--  Registered_Trigger_Scaler(8*(HIGH_LOW_BYTE+1)-1 downto 7*HIGH_LOW_BYTE);
  

  -- purpose: Writing to STATE_CAPTURE_ADDRESS registers
  --          Timestamp, Trigger_Counter, Buffer_Pointer
  -- type   : combinational
  -- inputs : User_CLK
  -- outputs: Timestamp_Register, Trigger_Counter_Register,
  --          Buffer_Pointer_Register

  write_mux : process (User_CLK, Timestamp,
                           Trigger_Counter, Buffer_Pointer) is
  begin  -- process capture_state
	 -- clock the data to be written on the *falling* edge of user clock.
    if (User_CLK'event and User_CLK = '0') then
      if ( User_RegWE = '1' and User_RegAddr(15 downto 6) = BASE_ADDRESS(15 downto 6)) then

        -- Capture timestamp, trigger_counter and buffer_pointer
        -- into registers.
        if (User_RegAddr(5 downto 0) = STATE_CAPTURE_ADDRESS) then
          Timestamp_Register <= Timestamp;
          Trigger_Counter_Register <= Trigger_Counter;
          Particle_Counter_Register <= Particle_Counter;   --  fsv
          Buffer_Pointer_Register(BUFFER_COUNTER_WIDTH-1 downto 0)                    <= Buffer_Pointer;
          Buffer_Pointer_Register(BUFFER_POINTER_WIDTH-1 downto BUFFER_COUNTER_WIDTH) <= (others => '0');

          Registered_Trigger_Scalers <= Trigger_Scalers;
          
        end if;

        -- output DUT reset signals.
        if (User_RegAddr(5 downto 0) = DUT_RESET_ADDRESS ) then
          Internal_DUT_Reset <= User_RegDataIn(NUMBER_OF_DUT-1 downto 0);
        end if;

        -- output DUT trigger signals for one clock cycle...
        if (User_RegAddr(5 downto 0) = DUT_TRIGGER_ADDRESS
            ) then
          DUT_Trigger <= User_RegDataIn(NUMBER_OF_DUT-1 downto 0);
        end if;

        -- output trigger inhibit signal
        if (User_RegAddr(5 downto 0) = TRIG_INHIBIT_ADDRESS ) then
          Internal_Host_Trig_Inhibit <= User_RegDataIn(0);
        end if;

        -- set the frequency of the internal (calibration) triggers
        if (User_RegAddr(5 downto 0) = INTERNAL_TRIGGER_INTERVAL ) then
          Internal_Calibration_Trigger_Interval <= User_RegDataIn;
        end if;
        
        -- output DUT_mask
        if ( User_RegAddr(5 downto 0) = DUT_MASK_ADDRESS ) then
          Internal_DUT_Mask <= User_RegDataIn(NUMBER_OF_DUT-1 downto 0);
          DUT_Mask_WE       <= '1';
        end if;

        -- write to LEDs
        if ( User_RegAddr(5 downto 0) = DUT_LED_ADDRESS ) then
          Internal_DUT_Leds <= User_RegDataIn(NUMBER_OF_DUT-1 downto 0);
        end if;


        -- Select which clock source drives the trigger logic
        -- 0 = external clock
        -- 1 = USB ( 48MHz ) clock
        if (User_RegAddr(5 downto 0) = CLOCK_SOURCE_SELECT_ADDRESS ) then
          Internal_Clock_Source_Select <= User_RegDataIn(0);
        end if;

        -- Write to the trigger output.
        if ( User_RegAddr(5 downto 0) = DUT_DEBUG_TRIGGER_ADDRESS ) then
          Internal_Debug_Trigger <= User_RegDataIn(NUMBER_OF_DUT-1 downto 0);
        end if;

        -- output pointer/counter reset signals for one clock cycle.
        if (User_RegAddr(5 downto 0) = RESET_REGISTER_ADDRESS
            ) then
          Reset_Timestamp       <=
            User_RegDataIn(TIMESTAMP_RESET_BIT);
          Reset_Trigger_Counter <=
            User_RegDataIn(TRIGGER_COUNTER_RESET_BIT);
          Reset_Buffer_Pointer  <=
            User_RegDataIn(BUFFER_POINTER_RESET_BIT);
          Reset_DMA_Controller  <=
            User_RegDataIn(DMA_CONTROLLER_RESET_BIT);
          Reset_Trigger_Output_FSM <= User_RegDataIn(TRIGGER_FSM_RESET_BIT);
          --Reset_Beam_Trigger_FSM <= User_RegDataIn(BEAM_TRIGGER_FSM_RESET_BIT);
	  Reset_Trigger_Scalers <= User_RegDataIn(TRIGGER_SCALERS_RESET_BIT);
       end if;



        -- Initiate readout block readout of trigger info
        if (User_RegAddr(5 downto 0) = INITIATE_READOUT_ADDRESS
            ) then
          Initiate_Readout <= '1';
        end if;

                                        -- set beam trigger output masks.
        if (User_RegAddr(5 downto 0) = BEAM_TRIGGER_AMASK_ADDRESS or
            User_RegAddr(5 downto 0) = BEAM_TRIGGER_OMASK_ADDRESS or
            User_RegAddr(5 downto 0) = BEAM_TRIGGER_VMASK_ADDRESS
            ) then
          Beam_Trigger_Mask_WE <= '1';
          if (User_RegAddr(5 downto 0) = BEAM_TRIGGER_AMASK_ADDRESS) then
            Internal_Beam_Trigger_AMask <= User_RegDataIn(NUMBER_OF_BEAM_TRIGGERS-1 downto 0);
          elsif (User_RegAddr(5 downto 0) = BEAM_TRIGGER_OMASK_ADDRESS) then
            Internal_Beam_Trigger_OMask <= User_RegDataIn(NUMBER_OF_BEAM_TRIGGERS-1 downto 0);
          else
            Internal_Beam_Trigger_VMask <= User_RegDataIn(NUMBER_OF_BEAM_TRIGGERS-1 downto 0);
          end if;
        end if;


      else
        initiate_readout <= '0';
        DUT_Mask_WE      <= '0';
        Beam_Trigger_Mask_WE <= '0';
        Reset_Timestamp       <= '0';
        Reset_Trigger_Counter <= '0';
        Reset_Buffer_Pointer  <= '0';
        Reset_DMA_Controller  <= '0';
        Reset_Trigger_Output_FSM <= '0';
        Reset_Beam_Trigger_FSM <= '0';
        
      end if;

    end if;  -- end of clk'falling
  end process write_mux;


  registered_scaler0 <= Registered_Trigger_Scalers(0);
  Trigger_Scaler0_low <= registered_scaler0(7 downto 0);
  Trigger_Scaler0_high <= registered_scaler0(15 downto 8);

  registered_scaler1 <= Registered_Trigger_Scalers(1);
  Trigger_Scaler1_low <= registered_scaler1(7 downto 0);
  Trigger_Scaler1_high <= registered_scaler1(15 downto 8);

  registered_scaler2 <= Registered_Trigger_Scalers(2);
  Trigger_Scaler2_low <= registered_scaler2(7 downto 0);
  Trigger_Scaler2_high <= registered_scaler2(15 downto 8);

  registered_scaler3 <= Registered_Trigger_Scalers(3);
  Trigger_Scaler3_low <= registered_scaler3(7 downto 0);
  Trigger_Scaler3_high <= registered_scaler3(15 downto 8);
  

  -- purpose: output register for data output to USB
  -- type   : combinational
  -- inputs : clk, User_RegDataOut
  -- outputs: User_RegDataOut
--         output_register: process (User_CLK, Output_Data) is
--           begin                      -- process output_register
--             if (User_CLK'event and User_CLK='1') then
--               User_RegDataOut <= Output_Data;
--             end if;
--           end process output_register;

  User_RegDataOut <= Output_Data;

  DUT_Mask <= Internal_DUT_Mask;

  DUT_Leds <= Internal_DUT_Leds;

  DUT_Debug_Trigger <= Internal_Debug_Trigger;

  DUT_Reset <= Internal_DUT_Reset;

  Clock_Source_Select <= Internal_Clock_Source_Select;

  Host_Trig_Inhibit <= Internal_Host_Trig_Inhibit;

  calibration_trigger_interval <= Internal_Calibration_Trigger_Interval;

  Beam_Trigger_OMask <= Internal_Beam_Trigger_OMask;
  Beam_Trigger_AMask <= Internal_Beam_Trigger_AMask;
  Beam_Trigger_VMask <= Internal_Beam_Trigger_VMask;

  
end architecture rtl;



