# Configuration
The AIDA-2020 TLU is configured using a yaml file (tlu_configuration.yaml).
In the following, the possible configuration parameters and settings are briefly explained.

### Internal Trigger Generation (internal_trigger)
The setting internal trigger allows the TLU to generate a trigger internally with a given frequency.
To disable the generation of internal triggers set this frequency to zero.

### DUT Module (dut_module)
The DUT module configures the individual DUT interfaces.
Where each interface can be set to one operating mode.
The possible modes are 'aida', 'aidatrig' and 'eudet'.
With 'aidatrig' the AIDA mode with additional trigger number.
And 'aida' or 'eudet' the AIDA or EUDET operating modes.
It is important to note that only working DUT devices should be enabled.
One not properly working DUT can block the TLU from sending out triggers (especially in EUDET mode).

### Trigger Inputs (trigger_inputs)
Multiple settings of the trigger inputs are configurable.
This includes trigger input thresholds, trigger logic, trigger polarity and trigger signal shaping.

The threshold for each trigger input can be tuned individually between [-1.3; 1.3] V.

Another setting controls the trigger input logic.
Each trigger input can have one of three settings. The input can act as 'active', 'veto' or 'do not care'.
Between each trigger input, there is also the possibility to set 'AND' or 'OR'.
A desired trigger configuration is set with the use of the Python boolean operators.
These operators are used in conjunction with the input channels CH1-CH6 and interpreted as a literal logic expression.
For example "(CH1 & (not CH2)) and (CH3 or CH4 or CH5 or CH6)" produces a valid trigger, when CH1 and not CH2 triggers and when one of CH3, CH4, CH5 or CH6 triggers.
An input channel that is not explicitly set to 'veto' or 'enabled' is automatically set to 'do not care'.

TLU can trigger on a rising or falling edge. Trigger polarity is set using a string or boolean,
'rising' corresponds to false (0) and 'falling' to true (1)

Each trigger input signal can be delayed and stretched by a given number of clock cycles.
This is set with a list containing the number of clock cycles for every different trigger input.
This value is written in a 5-bit register so the maximum stretch or delay in clock cycles is 32.
One should stretch each used trigger input signal at least by 1 to prevent the generation of incomplete triggers.

### Clock LEMO (clock_lemo)
The clock LEMO setting enables or disables the clock LEMO output.
Set this to 'True' or 'False'.

### PMT Power (pmt_control)
Set the PMT control voltage. The possible range is between [0; 1] V.

### Data Handling and Online Monitor
Two settings concern the data handling. The creation of raw and interpreted data files.
At last, the ZMQ connection can be configured.

### Stop Conditions
Two optional stop conditions can be set in tlu_configuration.yaml.
The maximum number of trigger events (max_trigger_number, e.g. max_trigger_number: 1000000)
and a timeout in seconds (timeout, e.g. timeout: 100) can be set.
These configurations are not included by default in the tlu_configuration file, so add them manually if needed.

### Ignore Busy (ignore_busy)
Optional configuration, specific DUT interface ignores busy signals.
Set it for example with
```
dut_1:
    mode: eudet
    ignore_busy: 1
```
