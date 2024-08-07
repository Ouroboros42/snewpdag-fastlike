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

RUN_PARAMS=${3:-"snewpdag/data/fastlike/metaparams/$CONF_NAME.json"}  

export OUT_DIR=$OUT_ROOT/$OUT_SUBDIR

mkdir $OUT_DIR
cp $RUN_PARAMS $OUT_DIR/params.json

echo Building DAG from: $(realpath $RUN_CONFIG)
echo Output in: $(realpath $OUT_DIR)
echo Running $N_TRIALS trials

python snewpdag/trials/Simple.py Control -n $N_TRIALS | \
python -m snewpdag --log $LOG_LEVEL --jsonlines $RUN_CONFIG