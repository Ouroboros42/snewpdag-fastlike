#!/usr/bin/bash

cd ${PROJECT_ROOT:=$(realpath .)} # Set from condor for correct working dir

. snewpdag/data/fastlike/loadenv.sh

RUN_CONFIG=$1 # CSV File to setup DAG
export OUT_DIR=$2 # Directory to read pickle from and put outputs in
PICKLE_PATH=${3:-"$OUT_DIR/jar/PullPickle-0-0.pkl"}

python snewpdag/trials/PicklePayload.py $RUN_CONFIG $PICKLE_PATH