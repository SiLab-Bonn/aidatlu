# Constellation Satellite

Satellite for the [constellation](https://constellation.pages.desy.de/) control and data acquisition framework.

## Installation

After installing IPbus and the required Python bindings. Install the constellation requirement from the top file.

```bash
pip install .[constellation]
```

## Usage

Start the satellite with:
```bash
SatelliteAidaTLU
```

## Tests
The AIDA-TLU satellite can be tested using the
TLU mock. By default, the TLU hardware will be used, but to substitute the TLU with the mock just set the environmental variable.

```bash
TLU_MOCK=True SatelliteAidaTLU
```

## Configuration

| Configuration | Description | Type |
|-----------|-------------|------|
| `internal_trigger_rate` | Generates internal trigger with a given frequency given in Hz | Integer |
| `dut_interfaces` | Specify the operation mode of the DUT interface (`aida`, `eudet`, `aidatrig`) given in a list. | List |
| `trigger_threshold` | Threshold setting of each individual trigger input channel given in V | List |
| `trigger_inputs_logic` | Trigger Logic configuration accept a python expression for the trigger inputs. The logic is set by using the variables for the input channels 'CH1', 'CH2', 'CH3', 'CH4', 'CH5' and 'CH6' and the Python bitwise operators `&`, `|`, `not` and so on. Don't forget to use brackets... | String |
| `trigger_polarity` | TLU can trigger on a rising or falling edge. | String |
| `trigger_signal_stretch` | Stretches each individual trigger input by a given number of clock cycles (corresponds to 6.25ns steps) | List |
| `trigger_signal_delay` | Delays each individual trigger input by a given number of clock cycles (corresponds to 6.25ns steps) | List |
| `enable_clock_lemo_output` | Enable the LEMO clock output. | String |
| `pmt_power` | Sets the four PMT control voltages in V | List |
| `save_data` | Enables the creation of output data files. | String |
| `output_data_path` | Specify a custom output data path to save the data to. If no path provided the TLU uses a default output folder. | String |
| `zmq_connection` | Sends status messages via a `ZMQ` address to the online monitor. | String |
| `max_trigger_number` | Automatically stops the TLU after reaching this trigger output number. | Integer |
| `timeout` | Automatically stops TLU after a given number of seconds. | Integer |

You can find an example configuration file in `example_tlu_config.toml`.
