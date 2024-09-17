#!/usr/bin/bash

: ${SIGNAL_FILE:="/home/tseng/dev/snews/numodels/ls220-$MODEL/neutrino_signal_$SPECIES-LS220-$MODEL.data"}
: ${SIGNAL_FILETYPE:="'tng'"}

: ${SN_TIME_ROOT:="2021-11-01 05:22"}
: ${SN_TIME:="'$SN_TIME_ROOT:01'"}
: ${SN_SAMPLE_START:="'$SN_TIME_ROOT:00'"}
: ${SN_SAMPLE_STOP:="'$SN_TIME_ROOT:16'"}

: ${WINDOW:=15}

: ${BG_SNOP:=0.0004}
: ${BG_LVD:=1}
: ${BG_SK:=0.1}
: ${BG_JUNO:=1}
: ${BG_IC:=1500000}