"""Compares results of the stateEstimation module to dataSet.json."""
import json
from glob import glob
from stateEstimation import analyze


def error(exp, real):
    """
    Calculate percent error of an experimental value.

    :param exp: experimental value
    :param real: precise value
    :return: Percent error err such that 0 <= err <= 100.
    """
    return float(abs(exp - real)) / abs(real) * 100


# TODO
refs = []
for file in glob('dataset/img/*.jpg'):
    refs.append(analyze(file)[1])
print json.dumps(refs, sort_keys=True, indent=3)
