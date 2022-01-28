# aidatlu
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Repository for controlling the AIDA-2020 TLU with python using uHAL bindings from [IPbus](https://ipbus.web.cern.ch/).

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
## Python package
Install the python package as usual
```
pip install -e .
```

# Usage
TODO