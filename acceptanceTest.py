"""Compares results of the stateEstimation module to dataSet.json."""
import json
from glob import glob
from stateEstimation import analyze

# TODO
refs = []
for file in glob('dataset/img/*.jpg'):
    refs.append(analyze(file)[1])
print json.dumps(refs, sort_keys=True, indent=3)
