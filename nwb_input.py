import glob
from os.path import join
import os
import logging
import numpy as np
from glob import glob
import json
import pathlib
import np_session
import random
import pandas as pd
import SimpleITK as sitk
from dateutil import parser
from psycopg2 import connect, extras
from typing import Union

def check_and_make_output_path(output_path:pathlib.Path):
    if not output_path.exists():
        output_path.mkdir()

def get_annotation_volume():
    ccf_annotation_array = sitk.GetArrayFromImage(sitk.ReadImage(pathlib.Path('//allen/programs/mindscope/workgroups/np-behavior/tissuecyte/', 
                                                                              'field_reference', 'ccf_ano.mhd')))

    return ccf_annotation_array


def clean_region(region:str):
    if pd.isna(region):
        return 'No Area'
    else:
        return region

def get_day_from_pickle(session:np_session.Session) -> str:
    npexp_path = session.npexp_path
    behavior_stimulus_file = pathlib.Path(npexp_path, '{}.behavior.pkl'.format(npexp_path.as_posix()[npexp_path.as_posix().rindex('/')+1:]))
    behavior_dict = pd.read_pickle(behavior_stimulus_file)

    ephys_day = behavior_dict['items']['behavior']['params']['stage']
    day = int(ephys_day[ephys_day.index('_') + 1:])

    return str(day)

def get_channels_info_for_probe(current_probe:str, session_data_dict:dict, probe_id:int, id_json_dict:dict, session:np_session.Session):
    channels = []

    if len(id_json_dict['channel_ids']) > 0:
        channel_id = id_json_dict['channel_ids'][-1] + 1
    else:
        channel_id = probe_id

    # get channel dataframe
    mouse_id = session_data_dict['external_specimen_name']
    probe = current_probe[-1]
    day = session_data_dict['stimulus_name'][-1] if session_data_dict['stimulus_name'] is not None else get_day_from_pickle(session)

    ccf_alignment_path = pathlib.Path('//allen/programs/mindscope/workgroups/np-behavior/tissuecyte', mouse_id, 
                                             'Probe_{}_channels_{}_warped.csv'.format(probe+day, mouse_id))

    if ccf_alignment_path.exists():
        df_ccf_coords = pd.read_csv(ccf_alignment_path)

        ccf_annotation_array = get_annotation_volume()

        vertical_position = 20
        horizontal_position_even = [43, 59]
        horizontal_position = horizontal_position_even[0]
        horizontal_position_even_index = 0
        horizontal_position_odd = [11, 27]
        horizontal_position_odd_index = 0

        for index, row in df_ccf_coords.iterrows():
            if index != 0 and index % 2 == 0:
                vertical_position += 20
            
            if index == 0:
                horizontal_position = horizontal_position_even[0]
            elif index == 1:
                horizontal_position = horizontal_position_odd[0]
            elif index != 0 and index % 2 == 0:
                if horizontal_position_even_index == 0:
                    horizontal_position_even_index = 1
                    horizontal_position = horizontal_position_even[horizontal_position_even_index]
                else:
                    horizontal_position_even_index = 0
                    horizontal_position = horizontal_position_even[horizontal_position_even_index]
            elif index != 1 and index % 1 == 0:
                if horizontal_position_odd_index == 0:
                    horizontal_position_odd_index = 1
                    horizontal_position = horizontal_position_odd[horizontal_position_odd_index]
                else:
                    horizontal_position_odd_index = 0
                    horizontal_position = horizontal_position_odd[horizontal_position_odd_index]

            channel_dict = {
                'probe_id': probe_id,
                'probe_channel_number': row.channel,
                'structure_id': int(ccf_annotation_array[row.AP, row.DV, row.ML]),
                'structure_acronym': clean_region(row.region),
                'anterior_posterior_ccf_coordinate': row.AP*25,
                'dorsal_ventral_ccf_coordinate': row.DV*25,
                'left_right_ccf_coordinate': row.ML*25,
                'probe_horizontal_position': horizontal_position,
                'probe_vertical_position': vertical_position,
                'id': channel_id,
                'valid_data': True
            }

            channels.append(channel_dict)
            id_json_dict['channel_ids'].append(channel_id)

            channel_id += 1
    else:
        for i in range(384):
            channel_dict = {
                'probe_id': probe_id,
                'probe_channel_number': i,
                'structure_id': -1,
                'structure_acronym': 'No area',
                'anterior_posterior_ccf_coordinate': -1,
                'dorsal_ventral_ccf_coordinate': -1,
                'left_right_ccf_coordinate': -1,
                'probe_horizontal_position': -1,
                'probe_vertical_position': -1,
                'id': channel_id,
                'valid_data': True
            }

            channels.append(channel_dict)
            id_json_dict['channel_ids'].append(channel_id)

            channel_id += 1

    return channels

def get_units_info_for_probe(current_probe:str, session:np_session.Session, channels:list[dict], id_json_dict:dict):
    metrics_csv_files = session.metrics_csv
    probe_metrics_csv_file = [metrics_file for metrics_file in metrics_csv_files if current_probe in metrics_file.as_posix()][0]
    print(probe_metrics_csv_file)
    df_metrics = pd.read_csv(probe_metrics_csv_file)
    df_metrics.fillna(0, inplace=True)

    local_index = 0
    if len(id_json_dict['unit_ids']) > 0:
        unit_id = id_json_dict['unit_ids'][-1] + 1
    else:
        unit_id = 0

    units = []

    for index, row in df_metrics.iterrows():
        unit_dict = {
            'peak_channel_id': channels[row.peak_channel]['id'],
            'cluster_id': row.cluster_id,
            'quality': row.quality if 'quality' in df_metrics.columns else 'good',
            'snr': row.snr if not pd.isna(row.snr) and not np.isinf(row.snr) else 0,
            'firing_rate': row.firing_rate if not pd.isna(row.firing_rate) else 0,
            'isi_violations': row.isi_viol if not pd.isna(row.isi_viol) else 0,
            'presence_ratio': row.presence_ratio if not pd.isna(row.presence_ratio) else 0,
            'amplitude_cutoff': row.amplitude_cutoff if not pd.isna(row.amplitude_cutoff) else 0,
            'isolation_distance': row.isolation_distance if not pd.isna(row.isolation_distance) else 0,
            'l_ratio': row.l_ratio if not pd.isna(row.l_ratio) else 0,
            'd_prime': row.d_prime if not pd.isna(row.d_prime) else 0,
            'nn_hit_rate': row.nn_hit_rate if not pd.isna(row.nn_hit_rate) else 0,
            'nn_miss_rate': row.nn_miss_rate if not pd.isna(row.nn_miss_rate) else 0,
            'silhouette_score': row.silhouette_score if not pd.isna(row.silhouette_score) else 0,
            'max_drift': row.max_drift if not pd.isna(row.max_drift) else 0,
            'cumulative_drift': row.cumulative_drift if not pd.isna(row.cumulative_drift) else 0,
            'waveform_duration': row.duration if not pd.isna(row.duration) else 0,
            'waveform_halfwidth': row.halfwidth if not pd.isna(row.halfwidth) else 0,
            'PT_ratio': row.PT_ratio if not pd.isna(row.PT_ratio) else 0,
            'repolarization_slope': row.repolarization_slope if not pd.isna(row.repolarization_slope) else 0,
            'recovery_slope': row.recovery_slope if not pd.isna(row.recovery_slope) else 0,
            'amplitude': row.amplitude if not pd.isna(row.amplitude) else 0,
            'spread': row.spread if not pd.isna(row.spread) else 0,
            'velocity_above': row.velocity_above if not pd.isna(row.velocity_above) else 0,
            'velocity_below': row.velocity_below if not pd.isna(row.velocity_below) else 0,
            'local_index': local_index,
            'id': unit_id
        }

        id_json_dict['unit_ids'].append(unit_id)
        units.append(unit_dict)
        local_index += 1
        unit_id += 1

    return units

def get_mouse_age(session_mouse_lims:dict):
    return (parser.parse(session_mouse_lims['death_on']) - parser.parse(session_mouse_lims['date_of_birth'])).days

def get_mouse_gender(session_mouse_lims:dict):
    if session_mouse_lims['gender_id'] == 1:
        return 'M'
    else:
        return 'F'

# query lims and return result from given query
def query_lims(query_string):
    con = connect(
    dbname='lims2',
    user='limsreader',
    host='limsdb2',
    password='limsro',
    port=5432,
    )
    con.set_session(
        readonly=True, 
        autocommit=True,
    )
    cursor = con.cursor(
        cursor_factory=extras.RealDictCursor,
    )
    cursor.execute(query_string)
    result = cursor.fetchall()

    return result

# gets the tissuecyte info for the mouse id
def get_behavior_session_id_from_lims(foraging_id:str):
    TISSUECYTE_QRY = '''
            SELECT beh.id
            FROM behavior_sessions beh
            WHERE beh.foraging_id = '{}'
        '''
    print(TISSUECYTE_QRY.format(foraging_id))
    behavior_session_id = dict(query_lims(TISSUECYTE_QRY.format(foraging_id))[0])
    return behavior_session_id['id']

def get_behavior_session_id(session_mouse_lims:dict, ecephys_session_id:str, behavior_pickle_path:str):
    """
    behavior_ecephys_session = [session for session in session_mouse_lims['behavior_sessions'] if str(session['ecephys_session_id']) == ecephys_session_id]

    if len(behavior_ecephys_session) > 0:
        return str(behavior_ecephys_session[0]['id'])
    else:
        return str(session_mouse_lims['behavior_sessions'][-1]['id'])
    """
    behavior_pickle = pd.read_pickle(pathlib.Path(behavior_pickle_path))
    foraging_id = behavior_pickle['items']['behavior']['params']['foraging_id']
    behavior_session_id = get_behavior_session_id_from_lims(foraging_id)
    print('Behavior Session ID', behavior_session_id)
    return behavior_session_id

def get_driver_line(session_mouse_lims:dict):
    full_genotype = session_mouse_lims['full_genotype']

    return full_genotype[0:full_genotype.index('/')]

def get_reporter_line(session_mouse_lims:dict):
    full_genotype = session_mouse_lims['full_genotype']

    if ';' in full_genotype:
        return full_genotype[full_genotype.index(';')+1:full_genotype.rindex('/')]
    else:
        if full_genotype.index('/') == full_genotype.rindex('/'):
            return full_genotype[full_genotype.index('/')+1:]
        else:
            return full_genotype[full_genotype.index('/')+1:full_genotype.rindex('/')]

def get_session_data(session:np_session.Session, module_parameters:dict, non_doc=False):
    session_data_dict = session.data_dict
    session_mouse_lims = session.mouse.lims.info_from_lims()
    npexp_path = session.npexp_path

    behavior_pickle_path = pathlib.Path(npexp_path, '{}.behavior.pkl'.format(npexp_path.as_posix()[npexp_path.as_posix().rindex('/')+1:])).as_posix()
    non_doc_directory = pathlib.Path('//allen/programs/braintv/workgroups/nc-ephys/converted-pickles-060923').as_posix()
    non_doc_behavior_pickle_path = pathlib.Path(non_doc_directory, '{}.behavior.pkl'.format(npexp_path.as_posix()[npexp_path.as_posix().rindex('/')+1:])).as_posix()

    session_data = {
        'behavior_session_id': get_behavior_session_id(session_mouse_lims, session_data_dict['es_id'], behavior_pickle_path),
        'death_on': str(session_mouse_lims['death_on']),
        'date_of_acquisition': str(session_data_dict['date_of_acquisition']),
        'rig_name': session_data_dict['rig'],
        'external_specimen_name': session_data_dict['external_specimen_name'],
        'full_genotype': session_mouse_lims['full_genotype'],
        'sex': get_mouse_gender(session_mouse_lims),
        'date_of_birth': session_mouse_lims['date_of_birth'],
        'age': 'P{}'.format(str(get_mouse_age(session_mouse_lims))),
        'ecephys_session_id': str(session_data_dict['es_id']),
        'behavior_stimulus_file': behavior_pickle_path if not non_doc else non_doc_behavior_pickle_path,
        'mapping_stimulus_file': pathlib.Path(npexp_path, '{}.mapping.pkl'.format(npexp_path.as_posix()[npexp_path.as_posix().rindex('/')+1:])).as_posix(),#session_data_dict['MappingPickle'].as_posix(),
        'raw_eye_tracking_video_meta_data': session_data_dict['RawEyeTrackingVideoMetadata'].as_posix(),
        #'eye_dlc_file': session_data_dict['EyeDlcOutputFile'].as_posix(),
        #'face_dlc_file': session_data_dict['FaceDlcOutputFile'].as_posix() if 'FaceDlcOutputFile' in se,
        #'side_dlc_file': session_data_dict['SideDlcOutputFile'].as_posix(), 
        'eye_tracking_filepath': session_data_dict['EyeTracking Ellipses'].as_posix(),
        'sync_file': pathlib.Path(npexp_path, '{}.sync'.format(npexp_path.as_posix()[npexp_path.as_posix().rindex('/')+1:])).as_posix(), #session_data_dict['sync_file'].as_posix(),
        'stim_table_file': pathlib.Path(module_parameters['output_path'], 'Dynamic_Gating_stimulus_table.csv').as_posix(), 
        'optotagging_table_path': pathlib.Path(module_parameters['output_path'], 'optotagging_table.csv').as_posix(),
        'driver_line': [
          get_driver_line(session_mouse_lims)
        ],
        'reporter_line': [
          get_reporter_line(session_mouse_lims)
        ],
        'eye_tracking_rig_geometry': {
          'led_position': [
            246.0,
            92.3,
            52.6
          ],
          'monitor_position_mm': [
            118.6,
            86.2,
            31.6
          ],
          'monitor_rotation_deg': [
            0.0,
            0.0,
            0.0
          ],
          'camera_position_mm': [
            102.8,
            74.7,
            31.6
          ],
          'camera_rotation_deg': [
            0.0,
            0.0,
            2.8
          ],
          'equipment': session_data_dict['rig']
        }
    }

    return session_data

def get_lfp_information(current_probe:str, module_parameters:dict, output_path:pathlib.Path) -> Union[dict, None]:
    csd_path = pathlib.Path(module_parameters['output_path'], '{}_csd.h5'.format(current_probe))
    if csd_path.exists():
        lfp_dict = {}

        lfp_dict['input_data_path'] = pathlib.Path(module_parameters['output_path'], '{}_lfp.dat'.format(current_probe)).as_posix()
        lfp_dict['input_timestamps_path'] = pathlib.Path(module_parameters['output_path'], '{}_timestamps.npy'.format(current_probe)).as_posix()
        lfp_dict['input_channels_path'] = pathlib.Path(module_parameters['output_path'], '{}_channels.npy'.format(current_probe)).as_posix()
        lfp_dict['output_path'] = pathlib.Path(output_path, 'lfp_{}_{}.nwb'.format(current_probe, str(module_parameters['session_id']))).as_posix()

        return lfp_dict
    else:
        return None
    

def get_csd_information(current_probe:str, module_parameters:dict) -> Union[str, None]:
    csd_path = pathlib.Path(module_parameters['output_path'], '{}_csd.h5'.format(current_probe))
    if csd_path.exists():
        return csd_path.as_posix()
    else:
        return None

def generate_nwb_input_json(module_parameters:dict, session:np_session.Session, non_doc=False):
    current_probe = module_parameters['current_probe']
    output_path = pathlib.Path(module_parameters['nwb_path'], str(module_parameters['session_id']))
    check_and_make_output_path(output_path)
    nwb_path = pathlib.Path(output_path, '{}.nwb'.format(str(module_parameters['session_id']))).as_posix()

    with open(pathlib.Path(module_parameters['base_directory'], 'SDK_jsons', 'align_timestamps_generated_output.json'), 'r') as f:
        align_timestamps_output_json = json.load(f)

    session_data_dict = session.data_dict
    
    #ap_path = list(session_data_dict[current_probe].glob('*/*100.0'))[0].as_posix()

    if current_probe[-1] not in session.probe_letter_to_metrics_csv_path:
        return module_parameters, {}
    
    ap_path = session.probe_letter_to_metrics_csv_path[current_probe[-1]].parent.as_posix()
    #lfp_path = list(session_data_dict[current_probe].glob('*/*100.1'))[0].as_posix()

    id_json_dict = None
    
    id_json_path = pathlib.Path('//allen/programs/mindscope/workgroups/dynamicrouting', 'dynamic_gating', 'unique_ids.json')
    if id_json_path.exists():
        with open(id_json_path, 'r') as f:
            id_json_dict = json.load(f)
            probe_id = id_json_dict['probe_ids'][-1] + 1
    else:
        probe_id = 0

    if id_json_dict is None:
        id_json_dict = {'probe_ids': [], 'channel_ids': [], 'unit_ids': []}

    probe_information = [probe_info for probe_info in align_timestamps_output_json['probe_outputs'] if probe_info['name'] == current_probe][0]
    probe_dict = {
        'name': current_probe,
        'sampling_rate': probe_information['global_probe_sampling_rate'],
        'temporal_subsampling_factor': 2,
        'lfp_sampling_rate': probe_information['global_probe_lfp_sampling_rate'],

        'csd_path': get_csd_information(current_probe, module_parameters),

        'lfp': get_lfp_information(current_probe, module_parameters, output_path),

        'id': probe_id,

        'inverse_whitening_matrix_path': pathlib.Path(ap_path, 'whitening_mat_inv.npy').as_posix(),
        'mean_waveforms_path': pathlib.Path(ap_path, 'mean_waveforms.npy').as_posix(),
        'spike_amplitudes_path': pathlib.Path(ap_path, 'amplitudes.npy').as_posix(),
        'spike_clusters_file': pathlib.Path(ap_path, 'spike_clusters.npy').as_posix(),
        'spike_templates_path': pathlib.Path(ap_path, 'spike_templates.npy').as_posix(),
        'templates_path': pathlib.Path(ap_path, 'templates.npy').as_posix(),
        'spike_times_path': pathlib.Path(module_parameters['output_path'], current_probe, 'spike_times_master_clock.npy').as_posix()
    }

    id_json_dict['probe_ids'].append(probe_id)

    channels = get_channels_info_for_probe(current_probe, session_data_dict, probe_id, id_json_dict, session)
    probe_dict['channels'] = channels
    units = get_units_info_for_probe(current_probe, session, channels, id_json_dict)
    probe_dict['units'] = units

    with open(id_json_path, 'w') as f:
        json.dump(id_json_dict, f, indent=2)

    module_parameters['probe_dict_list'].append(probe_dict)
    if current_probe != module_parameters['final_probe']:
        return module_parameters, probe_dict
    else:
        input_json_write_dict = {
            'log_level': 'INFO',
            'output_path': nwb_path,
        }
        session_data = get_session_data(session, module_parameters, non_doc=non_doc)
        session_data['probes'] = module_parameters['probe_dict_list']

        input_json_write_dict['session_data'] = session_data
        module_parameters['probe_dict_list'] = []

        return module_parameters, input_json_write_dict