# Test Run
To test everything is working, from the project root, run:
```bash
make testfastlike TEST_CONF=simple-poly
```
This should simulate 2 alerts, for only 2 detectors. The output files should appear in [output/](../output/) in a time-stamped directory.

To run more configurable trials, use [runtest.sh](../snewpdag/data/fastlike/runtest.sh).

# Trial Configuration
Trial configurations are defined by json files located in [metaparams](../snewpdag/data/fastlike/metaparams). Each file has the same 5 fields, defining various parameters for the lag estimation process. Every combination of each of the 5 parameters will be run in parallel for each trial. For more information about this see [Trial-Parameters](Trial-Parameters.md)

Json trial parameters must be converted into a snewpdag graph, which is done by [compare.py](../snewpdag/data/fastlike/compare.py). To convert all configs in [metaparams](../snewpdag/data/fastlike/metaparams) into snewdag CSVs, just run:
```shell
make fastlikeconfig
``` 
The outputs will be located in [configs](../snewpdag/data/fastlike/configs). This only needs to be run whenever a change is made to a json config file.

Once the snewpdag csv is generated, it can be run using [runtest.sh](../snewpdag/data/fastlike/runtest.sh). This script takes two arguments: the path to the config csv, and the path to a directory to put outputs in.

All other configuration is done via environment variables. The default values for all environment variables are defined in [loadenv.sh](../snewpdag/data/fastlike/loadenv.sh), and the model-specific values are defined in the scripts in [cases](../snewpdag/data/fastlike/cases). Depending on the value of the variable `$SN_CASE`, the corresponding file in [cases](../snewpdag/data/fastlike/cases) is run (don't include `.sh`). The default case is `27M`.

Other noteworthy environment variables are:
* `$PROJECT_ROOT`: Should not need to be manually set except when using condor, must point to the project root for scripts to work properly.
* `$N_TRIALS`: Specifies how many trials to run. 
* `$LABEL`: The name for the output directory. Defaults to a timestamp.
* `$MEDIUM_OVERRIDE`: Model all detectors as the same medium (eg scint, wc) instead of using the configuration in [shared.sh](../snewpdag/data/fastlike/cases/shared.sh)
* `$MAX_LAG`: Largest possible time difference between detectors, defining the range of the likelihood scan.

Changing environment variables does not require a rebuild of the config files.