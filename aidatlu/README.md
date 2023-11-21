# Configuration
The AIDA-2020 TLU is configured using a yaml file (tlu_configuration.yaml).
In the following, the possible configuration parameters and settings are briefly explained.

### internal_trigger
The setting internal trigger allows the TLU to generate a trigger internally with a given frequency.
To disable the generation of internal triggers set this frequency to zero.

### dut_module
The DUT module configures the individual DUT interfaces.
Where each interface can be set to one operating mode.
The possible modes are 'aida', 'aidatrig' and 'eudet'.
With 'aidatrig' the AIDA mode with additional trigger number.
It is important to note that only working DUT devices should be enabled.
One not properly working DUT can block the TLU from sending out triggers.

### trigger_inputs
Trigger inputs take care of the complete control of the trigger inputs.
Where the threshold for each trigger input can be tuned in Volt between [-1.3; 1.3] V.

Another setting controls the trigger input logic. 
Each trigger input can have one of three settings. The input can act as 'active', 'veto' or 'do not care'.
Between each trigger input, there is also the possibility to set 'AND' or 'OR'.
A desired trigger configuration is set with the use of the [Python bitwise operators](https://wiki.python.org/moin/BitwiseOperators).
These operators are used in conjunction with the input channels CH1-CH6 and interpreted as a literal logic expression.
An input channel that is not explicitly set to 'veto' or 'enabled' is automatically set to 'do not care'.

Trigger polarity controls if the TLU should trigger on a rising (0) or falling (1) edge of an incoming trigger signal.

Each trigger input signal can be delayed and stretched by a given number of clock cycles.
This is set with a list containing the number of clock cycles for every different trigger input.
This value is written in a 5-bit register so the maximum stretch or delay in clock cycles is 32.
One should stretch each used trigger input signal at least by 1 to prevent the generation of incomplete triggers.

### clock_lemo
The clock LEMO setting enables or disables the clock LEMO output.
Set to 'True' or 'False'.

### pmt_control
Sets the PMT control voltage between [0; 1] V.

### Others
Two settings concern the data handling. The creation of raw and interpreted data files.
At last, the zmq connection is set.