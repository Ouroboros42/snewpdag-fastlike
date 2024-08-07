#!/usr/bin/bash

cd ${PROJECT_ROOT:=$(realpath .)} # Set from condor for correct working dir

. snewpdag/data/fastlike/loadenv.sh

export OUT_DIR=$1 # Directory to read pickle from and put outputs in
PICKLE_PATH=${2:-"$OUT_DIR/jar/PullPickle-0-0.pkl"}
PARAM_PATH=${3:-"$OUT_DIR/params.json"}

DAT=snewpdag/data/fastlike
TMP_CONF_PATH=$DAT/configs/temp/T@$NOW-conf.csv
python $DAT/compare.py $TMP_CONF_PATH $PARAM_PATH
python snewpdag/trials/PicklePayload.py $TMP_CONF_PATH $PICKLE_PATH
rm $TMP_CONF_PATH