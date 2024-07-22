#!/usr/bin/bash
cd /home/jesu4059/snewpdag-fastlike
. pyvenv/bin/activate
. snewpdag/data/fastlike/setenv.sh
echo "Environment setup"

python snewpdag/trials/Simple.py Control -n ${2:-$N_TRIALS} | \
python -m snewpdag --log $LOG_LEVEL --jsonlines $1