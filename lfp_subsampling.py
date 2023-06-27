import glob
from os.path import join
import os
import logging
import numpy as np
from glob import glob
import json
import pathlib

def generate_lfp_timestamps(module_parameters:dict):
    current_probe = module_parameters['current_probe']
    lfp_directory = list(pathlib.Path(module_parameters['base_directory']).glob('*' + current_probe + '*' + '/continuous/Neuropix-*100.1'))[0].as_posix()
    lfp_timestamps_path = list(pathlib.Path(module_parameters['base_directory']).glob('*' + current_probe + '*' + '/continuous/Neuropix-*100.1/lfp_timestamps.npy'))[0].as_posix()

    lfp_timestamps_length = len(np.load(lfp_timestamps_path))
    print(lfp_timestamps_length)
    lfp_timestamps_generated = np.arange(11, lfp_timestamps_length*12, 12)

    np.save(pathlib.Path(lfp_directory, 'lfp_generated_timestamps.npy'), lfp_timestamps_generated)
    

def get_ecephys_lfp_subsampling_json(module_params):
    """ Writes the lfp sampling information to the input json
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
    probe_idx = module_params['current_probe']
    output_path = module_params['output_path']
    print(module_params['base_directory'])
    print(probe_idx)
    print(glob(join(module_params['base_directory'],
                    '*',
                    '*_' + probe_idx)))
    print(glob(join(module_params['base_directory'],
                    '**',
                    probe_idx)))
    try:
        lfp_directory = glob(join(module_params['base_directory'],
                                  '*' + 
                                  probe_idx + '*',
                                  'continuous',
                                  "Neuropix*100.1"))[0]
    except IndexError:
        lfp_directory = glob(join(module_params['base_directory'],
                                  "**",
                                  "*_" +
                                  probe_idx,
                                  'continuous',
                                  '**'
                                  "Neuropix*100.1"))[0]
    try:
        probe_info_file = glob(join(module_params['base_directory'],
                                    '*'
                                    "probe_info.json"))[0]
    except IndexError:
        probe_info_file = glob(join(module_params['base_directory'],
                                    '*' +
                                    probe_idx + '*',
                                    'probe_info.json'))[0]

    print(probe_info_file)
    with open(probe_info_file) as probe_file:
        probe_info = json.load(probe_file)
    module_params['lfp_path'] = lfp_directory
    input_json_write_dict = {
        'name': module_params['current_probe'],
        'lfp_sampling_rate': 2500.,
        'lfp_input_file_path': pathlib.Path(join(lfp_directory, 'continuous.dat')).as_posix()[1:],
        'lfp_timestamps_input_path': pathlib.Path(join(output_path, probe_idx + '_lfp_timestamps_aligned_generated.npy')).as_posix()[1:],
        'lfp_data_path': pathlib.Path(join(output_path, probe_idx + '_lfp.dat')).as_posix()[1:],
        'lfp_timestamps_path': pathlib.Path(join(output_path, probe_idx + '_timestamps.npy')).as_posix()[1:],
        'lfp_channel_info_path': pathlib.Path(join(output_path, probe_idx + '_channels.npy')).as_posix()[1:],
        'surface_channel': probe_info['surface_channel'],
        'reference_channels': [191]
    }
    if probe_idx != module_params['final_probe']:
        module_params['lfp_list'].append(input_json_write_dict)
        return module_params, input_json_write_dict
    else:
        module_params['lfp_list'].append(input_json_write_dict)
        print("PROJECT")
        print(module_params['project'])
        if module_params['project'] == "OpenScopeGlobalLocalOddball":
            input_json_write_dict = \
                {
                    'lfp_subsampling': {
                        'temporal_subsampling_factor': 2,
                        'channel_stride': 1,
                        'start_channel_offset': 0},
                    "probes": module_params['lfp_list'],
                }
        else:
           input_json_write_dict = \
                {
                    'lfp_subsampling': {
                        'temporal_subsampling_factor': 2,
                    },
                    "probes": module_params['lfp_list'],
                }
        return module_params, input_json_write_dict