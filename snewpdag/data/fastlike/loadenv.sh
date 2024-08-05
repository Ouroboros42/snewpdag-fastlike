#!/usr/bin/bash

. pyvenv/bin/activate

set -a

PYTHONPATH=$PROJECT_ROOT:$PYTHONPATH
for envfile in snewpdag/data/fastlike/env/*.sh; do . $envfile; done

set +a

echo "Environment setup"