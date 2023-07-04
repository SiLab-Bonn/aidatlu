#!/bin/sh

CUR_DIR=$(pwd)
source ~/anaconda3/etc/profile.d/conda.sh
conda activate aidatlu
export LD_LIBRARY_PATH=/opt/cactus/lib

cd
./git/ipbus-software/controlhub/scripts/controlhub_start
cd $CUR_DIR
cd .. 
