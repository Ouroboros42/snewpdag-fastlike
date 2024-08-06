#!/usr/bin/bash

cd ${PROJECT_ROOT:=$(realpath .)} # Set from condor for correct working dir

. snewpdag/data/fastlike/loadenv.sh

RUN_CONFIG=$1 # CSV File to setup DAG
OUT_ROOT=$2 # Directory to put outputs in

#Optional args
N_TRIALS=${3:-100} # Number of trials to run
LABEL=${4:-"T@$NOW"} # Subdir of 

# Define output directory based on config file name + timestamp
CONF_BASE=$(basename $RUN_CONFIG)
CONF_NAME=${CONF_BASE%.*}
export OUT_DIR=$OUT_ROOT/$CONF_NAME/$LABEL

echo "Building DAG from: $RUN_CONFIG"
echo "Output in: $OUT_DIR"
echo "Running $N_TRIALS trials"

python snewpdag/trials/Simple.py Control -n $N_TRIALS | \
python -m snewpdag --log $LOG_LEVEL --jsonlines $RUN_CONFIG