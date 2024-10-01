#!/usr/bin/bash

: ${MODEL:=s11} #e.g., s27.0co or s11.2c
: ${SPECIES:=nu_e} #e.g., nu_e, nu_x, nubar_e, nubar_x

# Depends on Model and Species variables
. $PROJECT_ROOT/snewpdag/data/fastlike/cases/shared.sh

: ${YIELD_SNOP:=140}
: ${YIELD_LVD:=180}
: ${YIELD_SK:=3900}
: ${YIELD_JUNO:=3600}
: ${YIELD_IC:=330000}
