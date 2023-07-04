#!/bin/sh

export LD_LIBRARY_PATH=/opt/cactus/lib

cd
./git/ipbus-software/controlhub/scripts/controlhub_stop
sleep 1
./git/ipbus-software/controlhub/scripts/controlhub_start
