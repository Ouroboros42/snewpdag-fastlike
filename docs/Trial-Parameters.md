# Trial Parameters
A trial parameter file should have the following fields:
* `detectors`: A list of all detectors to simulate. Currently only accepts: IC, JUNO, SK, LVD, SNOP

* `bin_widths`: A list of different bin widths, in seconds, for detector events to be binned to calculate the likelihood

* `mesh_spacings` A list of different spacings, in seconds, for the array of lag values where the likelihood is evaluated

* `likelihood_methods` : A list of differnet likelihood functions (or similar, eg cross-covariance). Each element is a 3-item list:
    1. A human-readable label
    2. A python-style path to the class implementing the likelihood function, relative to snewpdag/plugins. The class should inherit from `fastlike.likelihoods.LikelihoodBase`.
    3. A dictionary of keyword arguments to pass to the class for instantiation. Note, string values (not keys) may need to be contain quotes to survive the several layers of interpretation they go through.

* `estimator_methods`: A list of estimators that take an array of likelihoods and calculate a lag with uncertainty. Formatted similarly to `likelihood_methods`, but the classes should inherit from `fastlike.estimators.EstimatorBase`.