# aidatlu
Repository for controlling new AIDA TLU

# Installation
## IPbus
You need to install [IPbus](https://ipbus.web.cern.ch/doc/user/html/software/install/compile.html) and its python bindings to the desired interpreter.
Follow the linked tutorial for pre-requisites and general installation.
The following commands have been proven useful for custom installation and building against current (non-system) python within an environment:
```bash
# Install only uhal core and python bindings, no ControlHub etc.
make -j 4 Set=uhal
# Pass current PATH to sudo shell to build against current python
sudo env PATH=$PATH make install prefix=<install_location>
```
## Python package
Install the python package as usual
```
python setup.py develop
```

# Usage
Only tested and somehow working file is based on `TLU_v1e/scripts/TLU_v1e.py`. An example can be found in `run_aidatlu.py`.
