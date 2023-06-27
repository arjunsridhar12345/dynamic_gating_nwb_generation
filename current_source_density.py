import glob
from os.path import join
import os
import logging
import numpy as np
from glob import glob
import json
import pathlib


def get_ecephys_current_source_density_json(module_parameters:dict):
    with open(pathlib.Path(module_parameters['base_directory'], 'SDK_jsons', 'align_timestamps_generated_output.json'), 'r') as f:
        align_timestamps_output_json = json.load(f)

    current_probe = module_parameters['current_probe']
    stimulus_table_path = pathlib.Path(module_parameters['output_path'], 'Dynamic_Gating_stimulus_table.csv').as_posix()[1:]
    
    probe_information = [probe_info for probe_info in align_timestamps_output_json['probe_outputs'] if probe_info['name'] == current_probe]
    lfp_data_path = list(pathlib.Path(module_parameters['base_directory']).glob('*' + current_probe + '*' + '/continuous/Neuropix-*100.1/continuous.dat'))
    if len(probe_information) > 0 and len(lfp_data_path) > 0:
        probe_information = probe_information[0]
        output_path = module_parameters['output_path']

        lfp_directory = list(pathlib.Path(module_parameters['base_directory']).glob('*' + current_probe + '*' + '/continuous/Neuropix-*100.1'))[0].as_posix()[1:]
        #lfp_data_path = list(pathlib.Path(module_parameters['base_directory']).glob('*' + current_probe + '*' + '/continuous/Neuropix-*100.1/continuous.dat'))[0].as_posix()[1:]
        lfp_data_path = lfp_data_path[0].as_posix()[1:]
        probe_info_file = list(pathlib.Path(module_parameters['base_directory']).glob('*' + current_probe + '*' + '/probe_info.json'))[0]
        with open(str(probe_info_file), 'r') as f:
            probe_info = json.load(f)

        lfp_timestamp_path = list(pathlib.Path(module_parameters['output_path']).glob(current_probe + '_lfp_timestamps_aligned_generated.npy'))[0].as_posix()[1:]

        output_csd_path = pathlib.Path(module_parameters['output_path'], current_probe + '_csd.h5').as_posix()[1:]

        probe_dict = {
            'name': current_probe,
            'lfp_data_path': lfp_data_path,
            'lfp_timestamps_path': lfp_timestamp_path,
            'surface_channel': probe_info['surface_channel'],
            'reference_channels': [191],
            'csd_output_path': output_csd_path,
            'sampling_rate': probe_information['global_probe_lfp_sampling_rate'],
            'surface_channel_adjustment': 40,
            'phase': '1.0'
        }

        module_parameters['probe_dict_list'].append(probe_dict)
        if current_probe != module_parameters['final_probe']:
            return module_parameters, probe_dict
        else:
            input_json_write_dict = {
            'memmap': False,
            'num_trials': None,
            'start_field': 'start_time',
            'memmap_thresh': 999999999999999,
            'pre_stimulus_time': 0.1,
            'post_stimulus_time': 0.25,
            'stimulus': {
                'stimulus_table_path': stimulus_table_path,
                'key': 'C:/ProgramData/StimulusFiles/dev/flash_250ms',
            },
            'probes': module_parameters['probe_dict_list']
            }
            module_parameters['probe_dict_list'] = []

            return module_parameters, input_json_write_dict
    else:
        if current_probe != module_parameters['final_probe']:
            return module_parameters, {}
        else:
            input_json_write_dict = {
            'memmap': False,
            'num_trials': None,
            'start_field': 'start_time',
            'memmap_thresh': 999999999999999,
            'pre_stimulus_time': 0.1,
            'post_stimulus_time': 0.25,
            'stimulus': {
                'stimulus_table_path': stimulus_table_path,
                'key': 'C:/ProgramData/StimulusFiles/dev/flash_250ms',
            },
            'probes': module_parameters['probe_dict_list']
            }
            module_parameters['probe_dict_list'] = []

            return module_parameters, input_json_write_dict

