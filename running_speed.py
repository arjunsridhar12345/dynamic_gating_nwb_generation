import glob
from modulefinder import Module
from os.path import join
import os
import logging
import numpy as np
from glob import glob
import json
import pathlib

def get_ecephys_running_speed_json(module_parameters:dict):
    sync_path = list(pathlib.Path(module_parameters['base_directory']).glob('*.sync'))[0].as_posix()
    behavior_path = list(pathlib.Path(module_parameters['base_directory']).glob('*.behavior.pkl'))[0].as_posix()
    mapping_path = list(pathlib.Path(module_parameters['base_directory']).glob('*.mapping.pkl'))[0].as_posix()

    output_path = pathlib.Path(module_parameters['output_path'], 'running_speeds.h5').as_posix()

    input_json_dict = {}
    input_json_dict['sync_h5_path'] = sync_path
    input_json_dict['behavior_pkl_path'] = behavior_path
    input_json_dict['mapping_pkl_path'] = mapping_path
    input_json_dict['output_path'] = output_path

    return module_parameters, input_json_dict
