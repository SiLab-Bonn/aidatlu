---
# SPDX-FileCopyrightText: 2024 DESY and the Constellation authors
# SPDX-License-Identifier: CC-BY-4.0 OR EUPL-1.2
title: "AidaTLU"
description: "Satellite for the AIDA-2020 TLU using a Python based control software"
---

## Description

The AIDA-2020 Trigger Logic Unit is designed to proved flexible trigger configurations in test beam settings (https://doi.org/10.48550/arXiv.2005.00310).

The Python-based control software for the AIDA-2020 TLU provides a comprehensive interface for controlling the TLU.
The software establishes a connection to the hardware and allows easy configuration of different trigger setups.
Information over each individual trigger signal is saved in a compressed and human-readable HDF5 format.

The satellite to connect the AIDA-2020 TLU to the [Constellation](https://constellation.pages.desy.de/) control and data acquisition framework.


Start the satellite with:
```bash
SatelliteAidaTLU
```

The AIDA-TLU satellite can be tested using a
TLU mock. By default, the hardware will be used, but the mock can be selected using an environmental variable.

```bash
TLU_MOCK=True SatelliteAidaTLU
```

## Building

After installing [IPbus](https://ipbus.web.cern.ch/doc/user/html/software/install/compile.html), also install the Python bindings and possible constellation requirement from the top file in the [Aida-TLU](https://github.com/SiLab-Bonn/aidatlu) repository.

```bash
pip install .[constellation]
```

A more detailed description of the prerequisite can also be found [here](https://github.com/SiLab-Bonn/aidatlu/blob/main/README.md).

## Parameters

| Configuration | Description | Type | Default Value |
|-----------|-------------|------| ------|
| `internal_trigger_rate` | Generates internal trigger with a given frequency given in Hz | Integer | None |
| `dut_interfaces` | Specify the operation mode of the DUT interface (`aida`, `eudet`, `aidatrig`) given in a list. | List | None |
| `trigger_threshold` | Threshold setting of each individual trigger input channel given in V | List | None |
| `trigger_inputs_logic` | Trigger Logic configuration accept a python expression for the trigger inputs. The logic is set by using the variables for the input channels 'CH1', 'CH2', 'CH3', 'CH4', 'CH5' and 'CH6' and the Python bitwise operators `and`, `or`, `not` and so on. Don't forget to use brackets... | String | None |
| `trigger_polarity` | TLU can trigger on a rising or falling edge. | String | None |
| `trigger_signal_stretch` | Stretches each individual trigger input by a given number of clock cycles (corresponds to 6.25ns steps) | List | None |
| `trigger_signal_delay` | Delays each individual trigger input by a given number of clock cycles (corresponds to 6.25ns steps) | List | None |
| `enable_clock_lemo_output` | Enable the LEMO clock output. | String | None |
| `pmt_power` | Sets the four PMT control voltages in V | List | None |
| `save_data` | Enables the creation of output data files. | String | None |
| `output_data_path` | Specify a custom output data path to save the data to. If no path provided the TLU uses a default output folder. | String | None |
| `zmq_connection` | Sends status messages via a `ZMQ` address to the online monitor. | String | None |
| `max_trigger_number` | Automatically stops the TLU after reaching this trigger output number. | Integer | None |
| `timeout` | Automatically stops TLU after a given number of seconds. | Integer | None |

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

enable_clock_lemo_output = true
pmt_power = [0.8, 0.8, 0.0, 0.0]
save_data = true
output_data_path = 'None'
zmq_connection = false

max_trigger_number = 'None'
timeout = 'None'
```

## Metrics

The following metrics are distributed by this satellite and can be subscribed to. Timed metrics provide an interval in units of time, triggered metrics in number of calls.

| Metric | Description | Value Type | Metric Type | Interval |
|--------|-------------|------------|-------------|----------|
| `TRIGGER_IN_RATE` | Incoming trigger rate in Hertz | Integer | `LAST_VALUE` | 1s |
| `TRIGGER_OUT_RATE` | Outgoing trigger rate in Hertz | Integer | `LAST_VALUE` | 1s |
| `TRIGGER_TOTAL_TRIGGER_NR` | Total trigger number | Integer | `LAST_VALUE` | 1s |
| `SC0` | Total number that trigger input 1 received a valid signal | Integer | `LAST_VALUE` | 1s |
| `SC1` | Total number that trigger input 2 received a valid signal | Integer | `LAST_VALUE` | 1s |
| `SC2` | Total number that trigger input 3 received a valid signal | Integer | `LAST_VALUE` | 1s |
| `SC3` | Total number that trigger input 4 received a valid signal | Integer | `LAST_VALUE` | 1s |
| `SC4` | Total number that trigger input 5 received a valid signal | Integer | `LAST_VALUE` | 1s |
| `SC5` | Total number that trigger input 6 received a valid signal | Integer | `LAST_VALUE` | 1s |
