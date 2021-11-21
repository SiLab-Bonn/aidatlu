# TLU Software


This repository contains software for AIDA-2020 TLU. I can be used with all variants: V1C (T-shaped pcb) , V1E and V1F (rectangular PCBs; the one most likely to be used outside the UoB lab).

The repository contains Python scripts used to test the hardware (the firm(gate)ware is contained in the fmc-mtlu-gw repository). These scripts rely on a few libraries contained in the "packages" folder as well as on uHAL.
Ensure your python environmental variable is set to include the packages folder and that uHAL is installed on the machine.
uHAL can be installed from here:

http://ipbus.web.cern.ch/ipbus/doc/user/html/software/index.html

## Controlling AIDA TLU with Python Script

```
cd TLU_v1e/scripts
python2 ./startTLU_v1e.py
```

Connects to TLU. Allows interactive control.

Reads initialization (start up) parameters from `localIni.ini`  ( default clock generator configuration file in `localClock.txt`)

Reads configuration parameters from `localConf.conf`

Initialization and configuration files are in EUDAQ2 format.


# EUDAQ2
The best way to control and read out data from the TLU is by using the EUDAQ2 tools.
Refer to the official EUDAQ2 page for instructions on how to install them.
https://github.com/eudaq/eudaq
