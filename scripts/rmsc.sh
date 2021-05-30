#!/bin/bash

seed=123456789
config=rmsc01
log=rmsc01

if [ $# -eq 0 ]; then
    python3 -u abides.py -c $config -l $log -s $seed 
else
  agent=$1
  python3 -u abides.py -c $config -l $log -s $seed -a $agent 
fi

