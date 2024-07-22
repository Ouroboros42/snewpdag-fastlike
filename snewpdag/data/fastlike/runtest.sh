#!/usr/bin/bash
cd /home/jesu4059/snewpdag-fastlike
. pyvenv/bin/activate
. snewpdag/data/fastlike/setenv.sh
N_TRIALS_INPUT=${2:-$N_TRIALS}
echo "Environment setup for $(basename $1), T=$NOW"
echo "Running $N_TRIALS_INPUT trials"
python snewpdag/trials/Simple.py Control -n $N_TRIALS_INPUT | \
python -m snewpdag --log $LOG_LEVEL --jsonlines $1