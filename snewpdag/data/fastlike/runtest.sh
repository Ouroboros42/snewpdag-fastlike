#!/usr/bin/bash

RUN_CONFIG=$1 # CSV File to setup DAG
OUT_ROOT=$2 # Directory to put outputs in

# Defaults defined in env/runparams.sh
N_TRIALS=${3:-$N_TRIALS} # Number of trials to run
LABEL=${4:-$LABEL} # Subdir of 

cd ${PROJECT_ROOT:=.} # Set from condor for correct working dir

. pyvenv/bin/activate
. snewpdag/data/fastlike/loadenv.sh

echo "Environment setup"
echo "Running $N_TRIALS trials"

python snewpdag/trials/Simple.py Control -n $N_TRIALS | \
python -m snewpdag --log $LOG_LEVEL --jsonlines $RUN_CONFIG