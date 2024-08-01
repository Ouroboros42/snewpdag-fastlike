#!/usr/bin/bash

: ${N_TRIALS:=100}
: ${LOG_LEVEL:=WARNING}

CONF_BASE=$(basename $RUN_CONFIG)
CONF_NAME=${CONF_BASE%.*}

NOW=$( date '+%F_%H.%M.%S' )

OUT_DIR_NAME=$CONF_NAME/${LABEL:-"T@$NOW"}
OUT_DIR=$OUT_ROOT/$OUT_DIR_NAME

echo "Output in: $OUT_DIR"
