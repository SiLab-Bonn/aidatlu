---
title: "AidaTLU"
description: "Satellite for the AIDA-2020 TLU using a Python based control software"
language: "Python"
category: "External"
---

## Description

The AIDA-2020 Trigger Logic Unit is designed to provide flexible trigger configurations in test beam setups (https://doi.org/10.48550/arXiv.2005.00310).

The Python-based control software for the AIDA-2020 TLU provides a comprehensive interface for controlling the TLU.
The software establishes a connection to the hardware and allows for easy configuration of different trigger setups.
Information over each individual trigger signal is saved in a compressed and human-readable HDF5 format.

The satellite connects the AIDA-2020 TLU to the [Constellation](https://constellation.pages.desy.de/) control and data acquisition framework.


## Building

After installing [IPbus](https://ipbus.web.cern.ch/doc/user/html/software/install/compile.html), with Python bindings (uhal), install the [Aida-TLU](https://github.com/SiLab-Bonn/aidatlu) package with the constellation requirement.

```bash
pip install .[constellation]
```

A more detailed description of the prerequisites can also be found [here](https://silab-bonn.github.io/aidatlu/Introduction.html#installation).

## Usage

Add the chosen cactus library path, where the default installation location is `/opt/cactus/`:

```bash
export LD_LIBRARY_PATH=<install_location>/lib
```

You also need to start the control hub:
```bash
<install_location>/bin/controlhub_start
```

Finally, start the satellite with:
```bash
SatelliteAidaTLU -g testbeam -n TLU
```

> [!NOTE]
> The TLU configuration resets during launching and landing.
> This means DUT interface signals (e.g. clock signals) are disrupted during these transitions.

## Parameters

| Configuration | Description | Type | Default Value |
|-----------|-------------|------| ------|
| `internal_trigger_rate` | (Optional) Generates internal triggers with a given frequency given in Hz | Integer | 0 |
| `dut_interfaces` | (Required) Specify the operation mode of the DUT interface (`aida`, `eudet`, `aidatrig`, `off`) given as list with a required length of 4. Where `aida` and `eudet` corresponds to the classic AIDA and EUDET mode respectively and `aidatrig` to the AIDA-mode with handshake. Disable a DUT interface with `off`. | List | None |
| `trigger_threshold` | (Required) Threshold setting of each individual trigger input channel given in V | List | None |
| `trigger_inputs_logic` | (Required) Trigger Logic configuration accept a Python expression for the trigger inputs. The logic is set by using the variables for the input channels `CH1`, `CH2`, `CH3`, `CH4`, `CH5` and `CH6` and the Python logic operators `and`, `or`, `not` and so on. Don't forget to use brackets... | String | None |
| `trigger_polarity` | (Optional) TLU can trigger on a rising or falling edge. Set to `rising` or `falling` | String | `falling` |
| `trigger_signal_stretch` | (Required) Stretches each individual trigger input by a given number of clock cycles (corresponds to 6.25ns steps) | List | None |
| `trigger_signal_delay` | (Required) Delays each individual trigger input by a given number of clock cycles (corresponds to 6.25ns steps) | List | None |
| `enable_clock_lemo_output` | (Optional) Enable the LEMO clock output. | String | False |
| `pmt_power` | (Required) Sets the four PMT control voltages in V | List | None |
| `output_data_path` | (Optional) Specify a custom output data path to save the data to. If no path provided the TLU uses a default output folder. | String | `aidatlu/tlu_data/` |

### Configuration Example
An example configuration for the AIDA-TLU satellite which could be dropped into a Constellation configuration as a starting point.

```toml
[satellites.AidaTLU]

internal_trigger_rate = 0
dut_interfaces = ['aida', 'aida', 'eudet', 'off']

trigger_threshold = [-0.1, -0.1, -0.1, -0.1, -0.1, -0.1]
trigger_inputs_logic = 'CH1 and CH2'
trigger_polarity = 'falling'
trigger_signal_stretch = [2, 2, 2, 2, 2, 2]
trigger_signal_delay = [0, 0, 0, 0, 0, 0]

enable_clock_lemo_output = false
pmt_power = [0.8, 0.8, 0.0, 0.0]
output_data_path = ''
```

## Metrics

The following metrics are distributed by this satellite and can be subscribed to. Timed metrics provide an interval in units of time, triggered metrics in number of calls.

| Metric | Description | Value Type | Metric Type | Interval |
|--------|-------------|------------|-------------|----------|
| `PRE_VETO_RATE` | Trigger rate after trigger logic (before DUT veto) in Hertz | Integer | `LAST_VALUE` | 1s |
| `POST_VETO_RATE` | Outgoing trigger rate to the devices (after DUT veto) in Hertz | Integer | `LAST_VALUE` | 1s |
| `TOTAL_PRE_VETO` | Total number of pre veto trigger | Integer | `LAST_VALUE` | 1s |
| `TOTAL_POST_VETO` | Total number of post veto trigger | Integer | `LAST_VALUE` | 1s |
| `SC0` | Total number that trigger input 1 received a valid signal | Integer | `LAST_VALUE` | 1s |
| `SC1` | Total number that trigger input 2 received a valid signal | Integer | `LAST_VALUE` | 1s |
| `SC2` | Total number that trigger input 3 received a valid signal | Integer | `LAST_VALUE` | 1s |
| `SC3` | Total number that trigger input 4 received a valid signal | Integer | `LAST_VALUE` | 1s |
| `SC4` | Total number that trigger input 5 received a valid signal | Integer | `LAST_VALUE` | 1s |
| `SC5` | Total number that trigger input 6 received a valid signal | Integer | `LAST_VALUE` | 1s |
