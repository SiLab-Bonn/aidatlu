# AIDA-TLU
[![tests](https://github.com/SiLab-Bonn/aidatlu/actions/workflows/tests.yml/badge.svg?branch=main)](https://github.com/SiLab-Bonn/aidatlu/actions/workflows/tests.yml)
[![pre-commit](https://github.com/SiLab-Bonn/aidatlu/actions/workflows/pre_commit.yml/badge.svg?branch=main)](https://github.com/SiLab-Bonn/aidatlu/actions/workflows/pre_commit.yml)
[![documentation](https://github.com/SiLab-Bonn/aidatlu/actions/workflows/documentation.yml/badge.svg?branch=main)](https://github.com/SiLab-Bonn/aidatlu/actions/workflows/documentation.yml)

Repository for controlling the AIDA-2020 Trigger Logic Unit (TLU) with Python using uHAL bindings from [IPbus](https://ipbus.web.cern.ch/).
The Python control software is based on [EUDAQ2](https://github.com/eudaq/eudaq/tree/master/user/tlu).
The software is a lightweight version written in Python with a focus on readability and user-friendliness.
Most user cases can be set with a .yaml configuration file and started by executing a single Python script.
For a more in-depth look at the hardware components please take a look at the official [AIDA-2020 TLU project](https://gitlab.com/ohwr/project/fmc-mtlu).
Additionally, take a look at the [documentation](https://silab-bonn.github.io/aidatlu/) for this software.
# Installation
## IPbus
You need to install the ControlHub from the [IPbus](https://ipbus.web.cern.ch/doc/user/html/software/install/compile.html) software.
Follow the linked tutorial for prerequisites and general installation.
Install prerequisites.
```bash
sudo apt-get install -y make erlang
```
Checkout from git and compile the repository.
```bash
git clone --depth=1 -b v2.8.22 https://github.com/ipbus/ipbus-software.git
cd ipbus-software
make Set=controlhub
sudo make Set=controlhub install
```
In case they are errors about missing man pages, you need to create them.
```bash
sudo touch /usr/lib/erlang/man/man1/gcov-tool.1.gz # example
```
The default install location is located in /opt/cactus/.
Then start the ControlHub.
```bash
/opt/cactus/bin/controlhub_start
```
The contolhub needs to run for the working of the AIDA TLU, so needs to be started again each time the controlhub is stopped.
The default IP address of the TLU is:
```
192.168.200.30
```
## Python packages
Install the Python package as usual.
```bash
pip install -e .
```

To connect to the hardware, you need to install the `hw` component as well.
```bash
pip install -e .[bash]
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
With [pytest](https://docs.pytest.org/en/stable/) the AIDA TLU control program can be tested.
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

You can also set the variable ```HW=False```` to test the mock TLU:

```bash
    HW=False pytest -sv
```
