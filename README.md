# AIDA-TLU
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Repository for controlling the AIDA-2020 Trigger Logic Unit (TLU) with python using uHAL bindings from [IPbus](https://ipbus.web.cern.ch/).
The python control software is based upon [EUDAQ2](https://github.com/eudaq/eudaq/tree/master/user/tlu).
The software is a lightweight version written in python with a strong focus on readability and user-friendliness.
Most user cases can be set with a .yaml configuration file and started by executing a single python script. 
For a more in depth look at the hardware components please take a look at the official [AIDA-2020 TLU project](https://ohwr.org/project/fmc-mtlu).
# Installation
## IPbus
You need to install [IPbus](https://ipbus.web.cern.ch/doc/user/html/software/install/compile.html) and its python bindings to the desired interpreter.
Follow the linked tutorial for pre-requisites and general installation.
The following commands have been proven useful for custom installation and building against current (non-system) python within an environment:
```bash
make -j $((`nproc`-1))
# Pass current PATH to su shell to build against current environment python
sudo env PATH=$PATH make install prefix=<install_location>
```
One needs then to import the library path
```bash
export LD_LIBRARY_PATH=/opt/cactus/lib
```
and start the controlhub
```bash
controlhub_start
```
in the according directory.
## Python packages
Install the python package as usual
```
pip install -e .
```

# Usage
There are multiple ways to use the control software of the AIDA 2020 TLU.
If one executes tlu.py in the main directory, the TLU is initialized, configured and starts a run automatically.
```bash
    python tlu.py
```
The TLU is configured with the standard tlu_configuration file. To stop the run use ctrl+c.


While configuring the TLU outputs are powered on and off. 
This leads to problems in AIDA mode where the clock is powered off shortly during configuring.
To avoid configuration at the start of runs in AIDA mode the best way is to use the aidatlu.py script.
This is started and controlled with the terminal input:
```bash
    python -i aidatlu.py
```
This initializes the main tlu.py script. One is now able to control the TLU through the python terminal interface,
with the following commands:
```bash
    tlu.configure
    tlu.run
    tlu.help
```
Runs are stopped with the keyboard interrupt ctr+c.
For more commands take a look at the python script aidatlu.py.

All configurations are done by the use of a yaml file (tlu_configuration.yaml).