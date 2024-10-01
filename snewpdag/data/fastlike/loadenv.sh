#!/usr/bin/bash

. pyvenv/bin/activate

set -a

PYTHONPATH=$PROJECT_ROOT:$PYTHONPATH

echo "Producing ${MAX_PLOTS:=20} trial plots"
echo "Log Level: ${LOG_LEVEL:=WARNING}"

: ${SAVE_IMG_TYPE:=png}

NOW=$( date '+%F_%H.%M.%S' )

: ${DETECTOR_LOCATIONS:="$PROJECT_ROOT/snewpdag/data/detector_location.csv"}
: ${MAX_LAG:=0.05}

echo Sampling ${SN_CASE:=27M} supernova

. $PROJECT_ROOT/snewpdag/data/fastlike/cases/$SN_CASE.sh

set +a

echo "Environment setup"