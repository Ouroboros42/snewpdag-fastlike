#!/usr/bin/bash

set -a

for envfile in snewpdag/data/fastlike/env/*.sh; do . $envfile; done

set +a