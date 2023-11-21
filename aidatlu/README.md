# Configuration
Settings and configurations of the AIDA 2020 TLU are set through a yaml file (tlu_configuration.yaml).

### internal_trigger
The first setting internal trigger allows the TLU to generate trigger internally with a given frequency.
To disable the generation of internal trigger one sets this frequency to zero.

### dut_module
In the second setting called DUT module, the different DUT interfaces and operating modes are configured.
The possible modes are 'aida', 'aidatrig' and 'eudet'.
These correspond to the according operating modes with 'aidatrig' the AIDA mode with trigger number.
It is important to note that only working DUT devices should be enabled.
One not properly working DUT can block the TLU from sending out triggers.

### trigger_inputs
Trigger inputs take care of the complete control of the trigger inputs.
Where for one the trigger input thresholds can be tuned in Volt between [-1.3; 1.3] V.

The next setting controls the trigger logic. 
Each trigger input can have one of three settings. The input can act as 'active', 'veto' or 'do not care'.
Between each trigger input there is also the possibility to set 'AND' or 'OR'.
A desired trigger configuration is set with the use of the [python bitwise operators](https://wiki.python.org/moin/BitwiseOperators).
These operators are used in conjunction with the input channels CH1-CH6 and interpreted as a literaral expression.
An input channel that is not explicitly set to 'veto' or 'enabled' is automatically set to 'do not care'.

The last two settings control if the TLU should trigger on a rising or falling edge of an incoming trigger signal.
With the other dictionary one controls the trigger signal shapes.

Each trigger input signal can be delayed and stretched by an amount of clock cycles.
This is set with a list containing the number of clock cycles for every different trigger input.
This value is written in a 5-bit register so the maximum stretch or delay in clock cycles is 32.

### clock_lemo
The clock LEMO setting enables or disables the clock LEMO output.
Set to 'True' or 'False'.

### pmt_control
Sets the PMT control voltage between [0; 1] V.

### Others
Two settings concern the data handling. The creation of raw and interpreted data files.

At last the zmq connection is set.