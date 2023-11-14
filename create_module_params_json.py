import np_session
import pathlib
from align_timestamps import get_ecephys_align_timestamps_json
from lfp_subsampling import get_ecephys_lfp_subsampling_json, generate_lfp_timestamps
from optotagging import get_ecephys_optotagging_table_json
from running_speed import get_ecephys_running_speed_json
import json
from current_source_density import get_ecephys_current_source_density_json
from stimulus_table import get_ecephys_stimulus_table_json
from nwb_input import generate_nwb_input_json
import argparse
from generate_align_timestamps import run_align_timestamps
import pandas as pd

parser = argparse.ArgumentParser()
parser.add_argument('--session', help='Session of experiment', required=True)

def get_module_types(modules: list):
    """Creates a list of modules, sorted by project or session level
    Parameters
    ----------
    project_dict: dict
    A dictionary containing all the project's json values
    Returns
    -------
    session_modules: list
    a list of the session level modules used by the project
    probe_modules: list
    a list of the probe level modules used by the project
    """
    session_modules = []
    probe_modules = []
    for module in modules:
        if module == 'allensdk.brain_observatory.extract_running_speed' or module == 'allensdk.brain_observatory.ecephys.optotagging_table':
            session_modules.append(module)
        else:
            probe_modules.append(module)
    return session_modules, probe_modules

# generates the session parameters given the session object
def generate_session_parameters(session: np_session.Session) -> dict:
    #print(session.lims_path)
    np_exp_path = pathlib.Path(session.npexp_path)
    lims_path = pathlib.Path(session.lims_path)
    #print(session.npexp_path)
    project = session.project
    probes = ['probe{}'.format(probe) for probe in list(session.probes_inserted)]
    #probes = ['probeA']
    first_probe = probes[0]
    final_probe = probes[-1]
    probe_count = len(probes)
    trim = False

    output_path = np_exp_path / 'SDK_outputs'
    if not output_path.exists():
        output_path.mkdir()

    nwb_path = pathlib.Path('//allen/programs/mindscope/workgroups/dynamicrouting/dynamic_gating', 'nwbs')
    input_json = pathlib.Path(np_exp_path, 'SDK_jsons')
    output_json = pathlib.Path(np_exp_path, 'SDK_jsons')

    allen_sdk_modules = [
        "allensdk.brain_observatory.ecephys.align_timestamps",
        "allensdk.brain_observatory.ecephys.stimulus_table",
        "allensdk.brain_observatory.extract_running_speed",
        'allensdk.brain_observatory.ecephys.lfp_subsampling',
        'allensdk.brain_observatory.ecephys.optotagging_table',
        "allensdk.brain_observatory.ecephys.write_nwb"
	]

    session_modules, probe_modules = get_module_types(allen_sdk_modules)

    session_parameters = {
        'session_id': session.id,
        'base_directory': np_exp_path,
        'storage_directory': lims_path,
        'project': project,
        'output_path': output_path,
        'nwb_path': nwb_path,
        'ellipse_path': "",
        'data_json': "",
        'last_unit_id': probe_count,
        'probes': probes,
        'first_probe': first_probe,
        'final_probe': final_probe,
        'probe_dict_list': [],
        'lfp_list': [],
        'lfp_path': "",
        "sync_path": "",
        'trim': trim,
        'session_modules': session_modules,
        'probe_modules': probe_modules,
        'input_json_path': input_json
    }

    return session_parameters


def save_align_timestamps_json(session_parameters: dict):
    for probe in session_parameters['probes']:
        session_parameters['current_probe'] = probe
        session_parameters, input_json = get_ecephys_align_timestamps_json(session_parameters)

        output_dir_path = pathlib.Path(session_parameters['base_directory'], 'SDK_outputs', probe)

        if not output_dir_path.exists():
            output_dir_path.mkdir()

    if not session_parameters['input_json_path'].exists():
        session_parameters['input_json_path'].mkdir()

    with open(pathlib.Path(session_parameters['input_json_path'], 'align_timestamps_generated_input.json'), 'w') as f:
        json.dump(input_json, f, indent=2)

def lfp_timestamps_generation(session_parameters:dict):
    for probe in session_parameters['probes']:
        session_parameters['current_probe'] = probe
        generate_lfp_timestamps(session_parameters)

def save_lfp_subsampling_json(session_parameters: dict):
    for probe in session_parameters['probes']:
        session_parameters['current_probe'] = probe
        session_parameters, input_json = get_ecephys_lfp_subsampling_json(session_parameters)

        output_dir_path = pathlib.Path(session_parameters['base_directory'], 'SDK_outputs', probe)
        if not output_dir_path.exists():
            output_dir_path.mkdir()

    if not session_parameters['input_json_path'].exists():
        session_parameters['input_json_path'].mkdir()

    with open(pathlib.Path(session_parameters['input_json_path'], 'lfp_subsampling_input.json'), 'w') as f:
        json.dump(input_json, f, indent=2)

def save_current_source_density_json(session_parameters: dict):
    for probe in session_parameters['probes']:
        session_parameters['current_probe'] = probe
        session_parameters, input_json = get_ecephys_current_source_density_json(session_parameters)

        output_dir_path = pathlib.Path(session_parameters['base_directory'], 'SDK_outputs', probe)
        if not output_dir_path.exists():
            output_dir_path.mkdir()

    if not session_parameters['input_json_path'].exists():
        session_parameters['input_json_path'].mkdir()

    with open(pathlib.Path(session_parameters['input_json_path'], 'current_source_density_input.json'), 'w') as f:
        json.dump(input_json, f, indent=2)

def save_optotagging_json(session_parameters: dict):
    session_parameters, input_json = get_ecephys_optotagging_table_json(session_parameters)

    if not session_parameters['input_json_path'].exists():
        session_parameters['input_json_path'].mkdir()

    with open(pathlib.Path(session_parameters['input_json_path'], 'optotagging_input.json'), 'w') as f:
        json.dump(input_json, f, indent=2)

def save_stimulus_table_json(session_parameters:dict, non_doc=False):
    session_parameters, input_json = get_ecephys_stimulus_table_json(session_parameters, non_doc=non_doc)

    if not session_parameters['input_json_path'].exists():
        session_parameters['input_json_path'].mkdir()

    with open(pathlib.Path(session_parameters['input_json_path'], 'stimulus_table_input.json'), 'w') as f:
        json.dump(input_json, f, indent=2)

def save_running_speed_json(session_parameters:dict):
    session_parameters, input_json = get_ecephys_running_speed_json(session_parameters)

    if not session_parameters['input_json_path'].exists():
        session_parameters['input_json_path'].mkdir()

    with open(pathlib.Path(session_parameters['input_json_path'], 'running_speeds_input.json'), 'w') as f:
        json.dump(input_json, f, indent=2)

def save_nwb_json(session_parameters: dict, session:np_session.Session, probe_lookup_table_path:pathlib.Path, 
                  channel_lookup_table_path: pathlib.Path, units_lookup_table_path: pathlib.Path,
                  non_doc=False, is_dynamic_gating=False, is_vbn_opto=False):
    structure_tree = pd.read_csv(r"\\allen\programs\mindscope\workgroups\dynamicrouting\dynamic_gating_insertions\ccf_structure_tree_2017.csv")
    isi_areas = pd.read_excel(pathlib.Path('//allen/programs/mindscope/workgroups/dynamicrouting/dynamic_gating/dg_vis_areas_hmc_071223.xlsx'))

    if probe_lookup_table_path.exists():
        probe_lookup_table = pd.read_csv(probe_lookup_table_path)
    else:
        probe_lookup_table = pd.DataFrame()

    if session.id in probe_lookup_table['session'].values:
        probe_in_lookup = True
        probe_ids = probe_lookup_table[probe_lookup_table['session'] == session.id]['index'].values
    else:
        probe_in_lookup = False
        new_probe_lookup_table = {}
        max_probe_id = probe_lookup_table['index'].max()
        probe_ids = []
        sessions = probe_lookup_table['session'].values.tolist()
        probe_indices = probe_lookup_table['index'].values.tolist()

        for i in range(len(session_parameters['probes'])):
            max_probe_id += 1
            probe_ids.append(max_probe_id)
            sessions.append(session.id)
            probe_indices.append(max_probe_id)
        
        new_probe_lookup_table['session'] = sessions
        new_probe_lookup_table['index'] = probe_indices
        df_new_probe_lookup_table = pd.DataFrame(new_probe_lookup_table)
        df_new_probe_lookup_table.to_csv(probe_lookup_table_path,
                                         index=False)

    channel_start = 0
    unit_start = 0
    for probe in session_parameters['probes']:
        channel_lookup_table = pd.read_csv(channel_lookup_table_path)
        unit_lookup_table = pd.read_csv(units_lookup_table_path)
        probe_index = session_parameters['probes'].index(probe)
        probe_id = int(probe_ids[probe_index])

        session_parameters['current_probe'] = probe
        session_parameters, input_json, channel_start, unit_start = generate_nwb_input_json(session_parameters, session, isi_areas, structure_tree, 
                                                                 probe_id, channel_lookup_table, unit_lookup_table, 
                                                                 channel_start, unit_start,
                                                                 non_doc=non_doc, probe_in_lookup=probe_in_lookup,
                                                                 is_dynamic_gating=is_dynamic_gating,
                                                                 is_vbn_opto=is_vbn_opto)

        output_dir_path = pathlib.Path(session_parameters['base_directory'], 'SDK_outputs', probe)
        if not output_dir_path.exists():
            output_dir_path.mkdir()

    if not session_parameters['input_json_path'].exists():
        session_parameters['input_json_path'].mkdir()

    with open(pathlib.Path(session_parameters['input_json_path'], 'nwb_input.json'), 'w') as f:
        json.dump(input_json, f, indent=2)

def generate_sdk_modules(session_str: str, is_dynamic_gating=False, is_vbn_opto=False, non_doc=False):
    session = np_session.Session(session_str)
    session_parameters = generate_session_parameters(session)

    #lfp_timestamps_generation(session_parameters)
    #save_lfp_subsampling_json(session_parameters)
    save_align_timestamps_json(session_parameters)
    run_align_timestamps(session_str)
    if is_dynamic_gating:
        save_optotagging_json(session_parameters)
    
    save_stimulus_table_json(session_parameters, non_doc=non_doc)
    #save_current_source_density_json(session_parameters)
    if is_dynamic_gating:
        probe_lookup_table_path = pathlib.Path('//allen/programs/mindscope/workgroups/dynamicrouting/dynamic_gating/nwbs/probes_lookup_table.csv')
        channel_lookup_table_path = pathlib.Path('//allen/programs/mindscope/workgroups/dynamicrouting/dynamic_gating/nwbs/channels_lookup_table.csv')
        units_lookup_table_path = pathlib.Path('//allen/programs/mindscope/workgroups/dynamicrouting/dynamic_gating/nwbs/units_lookup_table.csv')
    
    save_nwb_json(session_parameters, session, probe_lookup_table_path, channel_lookup_table_path, units_lookup_table_path, non_doc=non_doc)

if __name__ == '__main__':
    """
    #session = np_session.Session('1202644967')
    nwb_path = pathlib.Path('//allen/programs/mindscope/workgroups/dynamicrouting/dynamic_gating/nwbs')
    nwb_directories = list(nwb_path.iterdir())

    for nwb_directory in nwb_directories:
        if nwb_directory.is_dir():
            if len(list(nwb_directory.glob('*'))) > 0:
                session = nwb_directory.as_posix()[nwb_directory.as_posix().rindex('/')+1:]
                session = np_session.Session(session)

                if '611166' not in str(session.mouse):
                    session_parameters = generate_session_parameters(session)
                    #lfp_timestamps_generation(session_parameters)
                    #save_lfp_subsampling_json(session_parameters)
                    save_current_source_density_json(session_parameters)
    """
    #session = np_session.Session('1179670730_612090_20220524')
    #session_parameters = generate_session_parameters(session)

    sessions = ['1182427414_607660_20220606']

    for session in sessions:
        generate_sdk_modules(session)