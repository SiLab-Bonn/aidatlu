# AIDA-TLU
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Repository for controlling the AIDA-2020 Trigger Logic Unit (TLU) with Python using uHAL bindings from [IPbus](https://ipbus.web.cern.ch/).
The Python control software is based on [EUDAQ2](https://github.com/eudaq/eudaq/tree/master/user/tlu).
The software is a lightweight version written in Python with a focus on readability and user-friendliness.
Most user cases can be set with a .yaml configuration file and started by executing a single Python script.
For a more in-depth look at the hardware components please take a look at the official [AIDA-2020 TLU project](https://ohwr.org/project/fmc-mtlu).
Additionally, take a look at the [documentation](https://silab-bonn.github.io/aidatlu/) for this software.
# Installation
## IPbus
You need to install [IPbus](https://ipbus.web.cern.ch/doc/user/html/software/install/compile.html) and its Python bindings to the desired interpreter.
Follow the linked tutorial for prerequisites and general installation.
Install prerequisites.
```bash
sudo apt-get install -y make erlang g++ libboost-all-dev libpugixml-dev python-all-dev rsyslog
sudo touch /usr/lib/erlang/man/man1/x86_64-linux-gnu-gcov-tool.1.gz
sudo touch /usr/lib/erlang/man/man1/gcov-tool.1.gz
```
Checkout from git and compile the repository.
```bash
git clone --depth=1 -b v2.8.12 --recurse-submodules https://github.com/ipbus/ipbus-software.git
cd ipbus-software
make
```
Next install against the current Python environment.
```bash
# Pass current PATH to su shell to build against current environment python
sudo env PATH=$PATH make install
```
Afterwards you should be able to import uhal in your specific Python environment.
When using a custom installation path for IPbus you need to import the library path.
```bash
export LD_LIBRARY_PATH=<install_location>/lib
```
The default install location is located in /opt/cactus/.
Then start the controlhub from ipbus-software/controlhub/scripts.
```bash
./controlhub_start
```
The contolhub needs to run for the working of the AIDA TLU, so needs to be started again each time the controlhub is stopped.
The default IP address of the TLU is:
```
192.168.200.30
```
## Python packages
Install the Python package as usual.
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
This leads to problems in AIDA mode where the clock is powered off shortly during configuration.
To avoid this at the start of runs in AIDA mode the best way is to use the aidatlu_run.py script.
This is started and controlled with the terminal input:
```bash
    python -i aidatlu_run.py
```
This initializes the main tlu.py script. One is now able to control the TLU through the Python terminal interface,
with the following commands:
```bash
    tlu.configure()
    tlu.run()
    tlu.help()
```
Naturally, this also works for any EUDET mode runs.
Runs are stopped with the keyboard interrupt ctr+c.
For more commands take a look at the python script aidatlu.py.

All configurations are done by the use of a yaml file (tlu_configuration.yaml).

# Tests
With pytest (https://docs.pytest.org/en/7.4.x/) the AIDA TLU control program can be tested.
There is also an implemented AIDA-TLU mock, to allow tests and software development without hardware,
which also allows software development and testing without a working IPbus installation.
The mock is used as a default.

```bash
    pytest -sv
```
To test with connected hardware set an environment variable ```HW=True````:

```bash
    HW=True pytest -sv
```
