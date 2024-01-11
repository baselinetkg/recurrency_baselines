# Rule_Baselines



## Getting started

Install all packages from requirements.txt

## What to run

* src/write_baseline_rules.py # to write for each dataset the baseline rules to rules/dataset_name/1_r.json. this is only needed for new datasets.
* optional: parameter_learning.py # to select the best values for alpha and lmbda_psi for each dataset for each relation; is stores in ./configs
* optional: parameter_learning_per_ds.py # to select the best values for alpha and lmbda_psi for each dataset and all relations ./configs
* test.py: to apply the baselines on the test set and compute final mrr and results file; results file is stored in ./results/dataset_name
* src/evaluation/run_evaluation.py


## How to run

TODO: specify the args for each file

## How to evaluate

TODO: describe

## How to cite

Paper

## 