#!/usr/bin/bash

: ${MODEL:=s27.0co} #e.g., s27.0co or s11.2c
: ${SPECIES:=nu_e} #e.g., nu_e, nu_x, nubar_e, nubar_x

# Depends on Model and Species variables
. $PROJECT_ROOT/snewpdag/data/fastlike/cases/shared.sh

: ${YIELD_SNOP:=280}
: ${YIELD_LVD:=360}
: ${YIELD_SK:=7800}
: ${YIELD_JUNO:=7200}
: ${YIELD_IC:=660000}
