#!/usr/bin/bash

export N_TRIALS=100
export LOG_LEVEL=WARNING

export MODEL=s27.0co #e.g., s27.0co or s11.2c
export SPECIES=nu_e #e.g., nu_e, nu_x, nubar_e, nubar_x

export YIELD_SNOP=280
export BG_SNOP=0.0004
export YIELD_LVD=360
export BG_LVD=1
export YIELD_SK=7800
export BG_SK=0.1
export YIELD_JUNO=7200
export BG_JUNO=1
export YIELD_IC=660000
export BG_IC=1500000

export NBINS=7500
export WINDOW=15

export NLAGMESH=100

export SN_RA=-60.0
export SN_DEC=-30.0

TIME_ROOT="2021-11-01 05:22"
export SN_TIME="'$TIME_ROOT:01'"
export SN_SAMPLE_START="'$TIME_ROOT:00'"
export SN_SAMPLE_STOP="'$TIME_ROOT:16'"

export NOW=$( date '+%F_%H.%M.%S' )