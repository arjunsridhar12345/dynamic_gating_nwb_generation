import glob
from os.path import join
import os
import logging
import numpy as np
from glob import glob
import pathlib

def get_ecephys_align_timestamps_json(module_params):
    """Returns the dict for the timestamps json
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
    file_in_base_folder = False
    probe_idx = module_params['current_probe']
    print(module_params['base_directory'])
    print(probe_idx)
    print(glob(os.path.join(
        module_params['base_directory'], '*' + probe_idx + '*_sorted')))
    base_directory = glob(os.path.join(
        module_params['base_directory'], '*' + probe_idx + '*_sorted'))
    queue_directory = []
    if base_directory != []:
        base_directory = base_directory[0]
        events_directory = glob(os.path.join(
            base_directory, 'events', 'Neuropix*', 'TTL*'))[0]
        probe_directory = glob(os.path.join(
            base_directory, 'continuous', 'Neuropix*'))[0]
        queue_directory = glob(os.path.join(
            base_directory, 'EUR_QUEUE*', 'continuous', 'Neuropix*'))
        file_in_base_folder = True

    alt_probe_directory = glob(join(module_params['base_directory'],
                                    "**", '*' + probe_idx,
                                    'continuous',
                                    'Neuropix*'))
    print(alt_probe_directory)
    test_probe_directory = glob(join(module_params['base_directory'],
                                     "**", '*' + probe_idx))
    print(test_probe_directory)
    if alt_probe_directory != []:
        alt_probe_directory = alt_probe_directory[0]

    if queue_directory != []:
        queue_directory = queue_directory[0]

    output_directory = module_params['output_path']
    spike_directory = ""
    if file_in_base_folder:
        logging.debug("Current directory is: " + probe_directory)
    timestamp_files = []

    file_found = False
    file_in_probe_folder = False
    file_in_parent_folder = False
    file_in_queue_folder = False
    if file_in_base_folder:
        try:
            np.load(join(probe_directory, 'spike_times.npy'))
            file_found = True
            file_in_probe_folder = True
        except FileNotFoundError:
            logging.debug(' Spikes not found for ' + probe_directory)
            file_found = False
            file_in_probe_folder = False

    if alt_probe_directory != []:
        try:
            print(alt_probe_directory)
            print(glob(join(alt_probe_directory, "spike_times.npy")))
            np.load(glob(join(module_params['base_directory'],
                              "**", '*' + probe_idx,
                                    'continuous',
                                    'Neuropix*',
                                    'spike_times.npy'))[0])
            spike_directory = glob(join(module_params['base_directory'],
                                        "**", '*' + probe_idx,
                                        'continuous',
                                        'Neuropix*',
                                        'spike_times.npy'))[0]
#            np.load(glob(join(alt_probe_directory,
#                    "spike_times.npy"))[0])
#            spike_directory = glob(join(
 #                                  alt_probe_directory,
#                                   "spike_times.npy"))[0]
            print(alt_probe_directory)
            print(spike_directory)
            try:
                events_directory = glob(join(module_params['base_directory'],
                                        '*', "*" + probe_idx, 'events',
                                             'Neuropix*', 'TTL*'))[0]
            except IndexError:
                events_directory = glob(os.path.join(
                    base_directory, 'events', 'Neuropix*',
                    'TTL*'))[0]
            print(events_directory)
            file_found = True
            file_in_parent_folder = True

        except FileNotFoundError:
            logging.debug(' Spikes not found for ' +
                          join(module_params['base_directory'],
                               module_params['session_id'] +
                               "_" +
                               probe_idx +
                               "_aligned_" +
                               "spike_times.npy"))
            file_found = False
            file_in_parent_folder = False

    if (queue_directory != []) and not file_in_parent_folder:
        try:
            np.load(join(queue_directory, 'spike_times.npy'))
            alt_spike_directory = glob(join(queue_directory,
                                            "spike_times.npy"))[0]
            file_found = True
            file_in_queue_folder = True

        except FileNotFoundError:
            logging.debug(' Spikes not found for ' + queue_directory)
            file_found = False
            file_in_queue_folder = False

    if (file_in_probe_folder):
        timestamp_files.append({
            'name': 'spike_timestamps',
            'input_path': join(probe_directory, 'spike_times.npy'),
            'output_path': join(output_directory, probe_idx,
                                'spike_times_master_clock.npy')
        })

    elif (file_in_parent_folder):
        timestamp_files.append({
            'name': 'spike_timestamps',
            'input_path': spike_directory,
            'output_path': join(output_directory, probe_idx,
                                'spike_times_master_clock.npy')
        })

    elif (file_in_queue_folder):
        timestamp_files.append({
            'name': 'spike_timestamps',
            'input_path': alt_spike_directory,
            'output_path': join(output_directory, probe_idx,
                                'spike_times_master_clock.npy')
        })
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

    timestamp_files.append({
        'name': 'lfp_timestamps',
        'input_path': join(lfp_directory, 'lfp_timestamps.npy'),
        'output_path': join(module_params['output_path'], probe_idx + '_lfp_timestamps_aligned_generated.npy')
    })
    print("File was found: " + str(file_found))
    if (file_found):
        probe_dict = {
            'name': probe_idx,
            'sampling_rate': 30000.,
            'lfp_sampling_rate': 2500.,
            'barcode_channel_states_path': join(events_directory,
                                                'channel_states.npy'),
            'barcode_timestamps_path': join(
                events_directory,
                'event_timestamps.npy'),
            'mappable_timestamp_files': timestamp_files
        }

        module_params['probe_dict_list'].append(probe_dict)
        if probe_idx != module_params['final_probe']:
            print(module_params, probe_dict)
            return module_params, probe_dict
        else:
            print(module_params['base_directory'])
            print(glob(join(
                module_params['base_directory'], '**',
                '*.sync')))
            print(glob(join(
                module_params['base_directory'], '*',
                '*.sync')))
            print(glob(join(
                module_params['base_directory'],
                '*.sync')))

            try:
                sync_path = glob(join(
                    module_params['base_directory'],
                    '*.sync'))[0]
                
            except IndexError:
                sync_path = glob(join(
                    module_params['base_directory'], '**',
                    '*.sync'))[0]
            input_json_write_dict = {
                'sync_h5_path': sync_path,
                "probes": module_params['probe_dict_list']
            }
            module_params['sync_path'] = sync_path
            module_params['probe_dict_list'] = []
            print(module_params, input_json_write_dict)
            return module_params, input_json_write_dict