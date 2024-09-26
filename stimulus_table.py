import glob
from os.path import join
import os
import logging
import numpy as np
import json
import pathlib

def get_ecephys_stimulus_table_json(module_parameters:dict, non_doc=False, is_dynamic_gating:bool=False, is_vbn_opto:bool=False):
    sync_path = list(pathlib.Path(module_parameters['base_directory']).glob('*.sync'))[0].as_posix()
    if not non_doc:
        behavior_directory = module_parameters['base_directory'].as_posix()
    else:
        behavior_directory = pathlib.Path('//allen/programs/braintv/workgroups/nc-ephys/converted-pickles-060923').as_posix()

    base_directory_path = module_parameters['base_directory'].as_posix()[module_parameters['base_directory'].as_posix().rindex('/')+1:]
    behavior_path = pathlib.Path(behavior_directory, base_directory_path + '.behavior.pkl')

    input_json_dict = {}

    input_json_dict['sync_h5_path'] = sync_path
    input_json_dict['behavior_pkl_path'] = behavior_path.as_posix()

    if is_dynamic_gating:
        mapping_path = list(pathlib.Path(module_parameters['base_directory']).glob('*.mapping.pkl'))[0].as_posix()
        input_json_dict['mapping_pkl_path'] = mapping_path
        input_json_dict['output_stimulus_table_path'] = pathlib.Path(module_parameters['output_path'], 'Dynamic_Gating_stimulus_table.csv').as_posix()

    if is_vbn_opto:
        mapping_path = list(pathlib.Path(module_parameters['base_directory']).glob('*.mapping.pkl'))[0].as_posix()
        input_json_dict['mapping_pkl_path'] = mapping_path

        replay_path = list(pathlib.Path(module_parameters['base_directory']).glob('*.replay.pkl'))[0].as_posix()
        input_json_dict['replay_pkl_path'] = replay_path

        input_json_dict['output_stimulus_table_path'] = pathlib.Path(module_parameters['output_path'], 'VBN_stimulus_table.csv').as_posix()

    return module_parameters, input_json_dict