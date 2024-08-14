import json
import pandas as pd
import np_session
from nwb_input import get_day_from_pickle
import pathlib

def get_project_code(session_data:dict) -> str:
    behavior_path = session_data['behavior_stimulus_file']
    if 'np-exp' in behavior_path:
        return 'DynamicGating'
    else:
        return 'DynamicGating_DEV'

def get_unit_channel_count(session_data) -> tuple[int, int]:
    probes = session_data['probes']
    total_units = 0
    total_channels = 0

    for probe_dict in probes:
        total_units += len(probe_dict['units'])

        channels = probe_dict['channels']
        if not all([channel['anterior_posterior_ccf_coordinate'] < 0 for channel in channels]):
            total_channels += len(channels)
    
    return total_channels, total_units

def get_structure_acronyms(session_data:dict) -> list:
    probes = session_data['probes']
    structure_acronyms = set()

    for probe_dict in probes:
        channels = probe_dict['channels']
        for channel in channels:
            structure_acronyms.add(channel['structure_acronym'])
    
    return list(structure_acronyms)

def get_probes_inserted(session_data:dict) -> list:
    probes = session_data['probes']
    probes_inserted: list = []

    for probe in probes:
        channels = probe['channels']
        if not all([channel['anterior_posterior_ccf_coordinate'] < 0 for channel in channels]):
            probes_inserted.append(probe['name'])

    return list(sorted(probes_inserted))

def get_novel_image_id(session: np_session.Session) -> str:
    stimulus_path = session.npexp_path / 'SDK_outputs' / 'Dynamic_Gating_stimulus_table.csv'
    stimulus_table = pd.read_csv(stimulus_path)
    image_names = stimulus_table['image_name'].unique()

    novel_image = [image for image in image_names if not pd.isna(image) and'im047' not in image and 'omitted' not in image 
                    and 'im115' not in image]

    if len(novel_image) > 0:
        return novel_image[0]
    else:
        return 'None'

def add_to_session_table(session:np_session.Session, session_table_dict:dict[str, list]) -> dict:
    nwb_input_json_path = session.npexp_path / 'SDK_jsons' / 'nwb_input.json'
    with open(nwb_input_json_path, 'r') as f:
        nwb_input_json = json.load(f)
    
    session_data = nwb_input_json['session_data']
    session_table_dict['ecephys_session_id'].append(session_data['ecephys_session_id'])
    session_table_dict['behavior_session_id'].append(session_data['behavior_session_id'])
    session_table_dict['date_of_acquisition'].append(session_data['date_of_acquisition'])
    session_table_dict['equipment_name'].append(session_data['eye_tracking_rig_geometry']['equipment'])
    day = get_day_from_pickle(session)
    session_table_dict['session_type'].append('EPHYS_{}'.format(day))
    session_table_dict['mouse_id'].append(session_data['external_specimen_name'])
    session_table_dict['genotype'].append(session_data['full_genotype'])
    session_table_dict['sex'].append(session_data['sex'])
    session_table_dict['project_code'].append(get_project_code(session_data))
    session_table_dict['age_in_days'].append(int(session_data['age'][1:]))

    channel_count, unit_count = get_unit_channel_count(session_data)
    session_table_dict['probes_inserted'].append(get_probes_inserted(session_data))
    session_table_dict['unit_count'].append(unit_count)
    session_table_dict['channel_count'].append(channel_count)
    session_table_dict['structure_acronyms'].append(get_structure_acronyms(session_data))
    session_table_dict['session_number'].append(day)
    session_table_dict['novel_image_id'].append(get_novel_image_id(session))

    return session_table_dict

def generate_session_table() -> None:
    dynamic_gating_spreadsheet = pd.read_excel(pathlib.Path(r"\\allen\programs\mindscope\workgroups\dynamicrouting\dynamic_gating\DynamicGatingProduction_final.xlsx"))
    nwb_directory = pathlib.Path('//allen/programs/mindscope/workgroups/dynamicrouting/dynamic_gating/nwbs')
    experiments = dynamic_gating_spreadsheet['exp_id'].values

    session_table_dict: dict[str, list] = {'ecephys_session_id': [], 'behavior_session_id': [], 'date_of_acquisition': [], 'equipment_name': [], 
                          'session_type': [], 'mouse_id': [], 'genotype': [], 'sex': [], 'project_code': [], 'age_in_days': [],
                          'probes_inserted': [], 'unit_count': [], 'channel_count': [], 'structure_acronyms': [], 'session_number': [], 
                          'novel_image_id': [], 'has_lfp': []
                          }

    for experiment in experiments:
        nwb_session_directory = pathlib.Path(nwb_directory, experiment[0:experiment.index('_')])
        if nwb_session_directory.exists():
            if len(list(nwb_session_directory.glob('*.nwb'))) > 0:
                session = np_session.Session(experiment[0:experiment.index('_')])
                session_table_dict = add_to_session_table(session, session_table_dict)
                
                if len(list(nwb_session_directory.glob('*.nwb'))) > 1:
                    session_table_dict['has_lfp'].append(True)
                else:
                    session_table_dict['has_lfp'].append(False)
    
    session_table_dataframe = pd.DataFrame(session_table_dict)
    session_table_dataframe = session_table_dataframe.set_index('ecephys_session_id')
    session_table_dataframe.to_csv(nwb_directory / 'dynamic_gating_ecephys_sessions_table_06052024.csv')

if __name__ == '__main__':
    generate_session_table()