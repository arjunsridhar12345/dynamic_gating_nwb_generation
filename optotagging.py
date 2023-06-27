import glob
from os.path import join
import os
import logging
import numpy as np
from glob import glob
import pickle

def get_ecephys_optotagging_table_json(module_params):
    """ Writes the relevant optotagging information to the input json
    Parameters
    ----------
    module_params: dict
    Session or probe unique information, used by each module
    Returns
    -------
    module_params: dict
    Session or probe unique information, used by each module
    input_json_write_dict: dict
    A dictionary representing the values that will be written to the input json
    """
    print (module_params['project'])
    if module_params['project'] == 'OpenScopeGlobalLocalOddball':
        print("GLO")
        conditions = {
            "0": {
                "duration": 1.0,
                "name": "fast_pulses",
                "condition": "2.5 ms pulses at 10 Hz"
            },
            "1": {
                "duration": 0.005,
                "name": "pulse",
                "condition": "a single square pulse"
            },
            "2": {
                "duration": 0.01,
                "name": "pulse",
                "condition": "a single square pulse"
            },
            "3": {
                "duration": 1.0,
                "name": "raised_cosine",
                "condition": "half-period of a cosine wave"
            },
            "4": {
                "duration": 1.0,
                "name": "5 hz pulse train",
                "condition": "Each pulse is 10 ms wide"
            },
            "5": {
                "duration": 1.0,
                "name": "40 hz pulse train",
                "condition": "Each pulse is 6 ms wide"
            }
        }
    elif module_params['project'] == 'OpenScopeIllusion':
        conditions = {
            "0": {
                "duration": 1,
                "name": "fast_pulses",
                "condition": "2 ms pulses at 1 Hz"
            },
            "1": {
                "duration": 1,
                "name": "pulse",
                "condition": "a single 10ms pulse"
            },
            "2": {
                "duration": .2,
                "name": "pulse",
                "condition": "1 second of 5Hz pulse train. Each pulse is 2 ms wide"
            },
            "3": {
                "duration": .1,
                "name": "raised_cosine",
                "condition": "half-period of a cosine wave"
            },
            "4": {
                "duration": .05,
                "name": "5 hz pulse train",
                "condition": "Each pulse is 10 ms wide"
            },
            "5": {
                "duration": .033,
                "name": "40 hz pulse train",
                "condition": "Each pulse is 6 ms wide"
            },
            "6": {
                "duration": .025,
                "name": "fast_pulses",
                "condition": "1 second of 40 Hz pulse train. Each pulse is 2 ms wide"
            },
            "7": {
                "duration": 0.02,
                "name": "pulse",
                "condition": "a single square pulse"
            },
            "8": {
                "duration": 0.0167,
                "name": "pulse",
                "condition": "a single square pulse"
            },
            "9": {
                "duration": .0125,
                "name": "raised_cosine",
                "condition": "half-period of a cosine wave"
            },
            "10": {
                "duration": .01,
                "name": "100 hz pulse train",
                "condition": "1 second of 100 Hz pulse train. Each pulse is 2 ms wide"
            },
            "11": {
                "duration": 1.0,
                "name": "Square Pulse",
                "condition": "1 second square pulse: continuously on for 1s"
            }
        }
    try:
        opto_pickle_path = glob(join(module_params['base_directory'],
                                     '*.opto.pkl'))[0]
    except IndexError:
        opto_pickle_path = glob(join(module_params['base_directory'],
                                     '**', '*.opto.pkl'))[0]
    try:
        sync_path = glob(join(module_params['base_directory'],
                              "*.sync"))[0]
    except IndexError:
        sync_path = glob(join(module_params['base_directory'],
                              "**",
                              "*.sync"))[0]
    input_json_write_dict = {
        'opto_pickle_path': opto_pickle_path,
        'sync_h5_path': sync_path,
        'output_opto_table_path': join(module_params['output_path'],
                                       'optotagging_table.csv'),
        #'conditions': conditions

    }
    print(input_json_write_dict)
    return module_params, input_json_write_dict