#!/usr/bin/bash

cd ${PROJECT_ROOT:=$(realpath .)} # Set from condor for correct working dir

. snewpdag/data/fastlike/loadenv.sh

RUN_CONFIG=$1 # CSV File to setup DAG
OUT_ROOT=$2 # Directory to put outputs in

: ${N_TRIALS:=100} # Number of trials to run

# Define output directory based on config file name + timestamp
CONF_BASE=$(basename $RUN_CONFIG)
CONF_NAME=${CONF_BASE%.*}
OUT_SUBDIR=${LABEL:-"$CONF_NAME/T@$NOW"}

export OUT_DIR=$OUT_ROOT/$OUT_SUBDIR

echo "Building DAG from: $RUN_CONFIG"
echo "Output in: $OUT_DIR"
echo "Running $N_TRIALS trials"

python snewpdag/trials/Simple.py Control -n $N_TRIALS | \
python -m snewpdag --log $LOG_LEVEL --jsonlines $RUN_CONFIG