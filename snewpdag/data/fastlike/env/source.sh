#!/usr/bin/bash

MODEL=s27.0co #e.g., s27.0co or s11.2c
SPECIES=nu_e #e.g., nu_e, nu_x, nubar_e, nubar_x

SN_TIME_ROOT="2021-11-01 05:22"
SN_TIME="'$SN_TIME_ROOT:01'"
SN_SAMPLE_START="'$SN_TIME_ROOT:00'"
SN_SAMPLE_STOP="'$SN_TIME_ROOT:16'"

WINDOW=15

DETECTOR_LOCATIONS="$PROJECT_ROOT/snewpdag/data/detector_location.csv"

SIGNAL_FILE="/home/tseng/dev/snews/numodels/ls220-$MODEL/neutrino_signal_$SPECIES-LS220-$MODEL.data"
SIGNAL_FILETYPE="'tng'"
