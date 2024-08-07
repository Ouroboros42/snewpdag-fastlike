#!/usr/bin/bash

echo "Producing ${MAX_PLOTS:=20} trial plots"
echo "Log Level: ${LOG_LEVEL:=WARNING}"
: ${SAVE_IMG_TYPE:=png}

NOW=$( date '+%F_%H.%M.%S' )
