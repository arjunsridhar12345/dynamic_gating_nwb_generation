import subprocess
from subprocess import PIPE, STDOUT
import pathlib
import argparse
from create_module_params_json import generate_sdk_modules
import pandas as pd
import np_session
import logging
import json

parser = argparse.ArgumentParser()
parser.add_argument('--session', help='Session of experiment', required=False)

session_errors: dict = {}

def log_subprocess_output(pipe):
    for line in iter(pipe.readline, b''): # b'\n'-separated lines
        logging.info('got line from subprocess: %r', line)

def run_nwb_pipeline(session:str, non_doc=False):
    session_errors:dict = {session:[]}
    generate_sdk_modules(session, non_doc)

    json_directory = pathlib.Path('//allen/programs/mindscope/workgroups/np-exp', session, 'SDK_jsons')

    #align_timestamps_module = 'python -m allensdk.brain_observatory.ecephys.align_timestamps --input_json {} --output_json {}'.format(pathlib.Path(json_directory, 'align_timestamps_generated_input.json').as_posix(),
                                                                                                                                      #pathlib.Path(json_directory, 'align_timestamps_generated_output.json').as_posix())
    
    stimulus_table_module = 'python -m ecephys_etl.modules.dynamic_gating_create_stim_table --input_json {} --output_json {}'.format(pathlib.Path(json_directory, 'stimulus_table_input.json').as_posix(),
                                                                                                                         pathlib.Path(json_directory, 'stimulus_table_output.json').as_posix())
    stimulus_table_response = subprocess.run(stimulus_table_module, shell=True, text=True, capture_output=True)
    session_errors[session].append(stimulus_table_response.stderr)

    optotagging_module = 'python -m allensdk.brain_observatory.ecephys.optotagging_table --input_json {} --output_json {}'.format(pathlib.Path(json_directory, 'optotagging_input.json').as_posix(),
                                                                                                                            pathlib.Path(json_directory, 'optotagging_output.json').as_posix())
    opto_response = subprocess.run(optotagging_module, shell=True, text=True, capture_output=True)
    session_errors[session].append(opto_response.stderr)

    nwb_module = 'python -m allensdk.brain_observatory.ecephys.write_nwb.dynamic_gating --input_json {} --output_json {}'.format(pathlib.Path(json_directory, 'nwb_input.json').as_posix(),
                                                                                                                                pathlib.Path(json_directory, 'nwb_output.json').as_posix())
    
    nwb_response = subprocess.run(nwb_module, shell=True, text=True)
    session_errors[session].append(nwb_response.stderr)

    with open('./session_errors_with_lfp.json', 'a') as f:
        json.dump(session_errors, f, indent=2)
        f.write('\n\n')

    """
    optotagging_module = 'python -m allensdk.brain_observatory.ecephys.optotagging_table --input_json {} --output_json {}'.format(pathlib.Path(json_directory, 'optotagging_input.json').as_posix(),
                                                                                                                            pathlib.Path(json_directory, 'optotagging_output.json').as_posix())
    #align_timestamps_response = subprocess.run(align_timestamps_module, shell=True)
    #session_errors[session_str].append(align_timestamps_response.stdout)
    #session_errors[session_str].append(align_timestamps_response.stderr)

    stimulus_table_response = subprocess.run(stimulus_table_module, shell=True, text=True)
    #session_errors[session_str].append(stimulus_table_response.stderr)

    optotagging_response = subprocess.run(optotagging_module, shell=True, text=True)
    #session_errors[session_str].append(optotagging_response.stderr)

    nwb_response = subprocess.run(nwb_module, shell=True, text=True)
    #session_errors[session_str].append(nwb_response.stderr)
    
    with open('./session_errors_round2.json', 'w') as f:
        json.dump(session_errors, f, indent=2)
    """
    
def get_empty_sessions():
    nwb_directory = pathlib.Path('//allen/programs/mindscope/workgroups/dynamicrouting/dynamic_gating/nwbs')
    nwb_directory_subdirectories = list(nwb_directory.iterdir())
    sessions_nwb_present = []
    session_empty = []

    for directory in nwb_directory_subdirectories:
        nwb_session_directory = pathlib.Path(nwb_directory, directory)
        if len(list(nwb_session_directory.glob('*'))) > 0:
            sessions_nwb_present.append(directory)
        else:
            session_empty.append(directory)
    
    return session_empty

if __name__ == '__main__':
    args = parser.parse_args()
    dynamic_gating_spreadsheet = pd.read_excel(pathlib.Path(r"\\allen\programs\mindscope\workgroups\dynamicrouting\dynamic_gating\DynamicGatingProduction_final.xlsx"))
    nwb_directory = pathlib.Path('//allen/programs/mindscope/workgroups/dynamicrouting/dynamic_gating/nwbs')
    experiments = dynamic_gating_spreadsheet['exp_id'].values
    doc_experiments = dynamic_gating_spreadsheet.loc[dynamic_gating_spreadsheet['pkl_format'] == 'DoC']['exp_id'].values
    non_doc_experiments = dynamic_gating_spreadsheet.loc[dynamic_gating_spreadsheet['pkl_format'] == 'non-DoC']['exp_id'].values
    empty_sessions = get_empty_sessions()
    """
    for experiment in experiments:
        if experiment in non_doc_experiments:
            run_nwb_pipeline(experiment, non_doc=True)
        else:
            run_nwb_pipeline(experiment)
    
    for non_doc_experiment in non_doc_experiments:
        nwb_session_directory = pathlib.Path(nwb_directory, non_doc_experiment[0:non_doc_experiment.index('_')])
        if nwb_session_directory.exists():
            if len(list(nwb_session_directory.glob('*'))) > 0 and '607660' not in non_doc_experiment:
                run_nwb_pipeline(non_doc_experiment)
    """
    sessions = ['1173741216_604914_20220428']

    for session in sessions:
        print(session)
        if session in non_doc_experiments:
            run_nwb_pipeline(session, non_doc=True)
        else:
            run_nwb_pipeline(session)
    
    """
    for experiment in experiments:
        nwb_session_directory = pathlib.Path(nwb_directory, experiment[0:experiment.index('_')])
        if nwb_session_directory.exists():
                if len(list(nwb_session_directory.glob('*.nwb'))) > 0:
                    print(experiment)
                    if experiment in non_doc_experiments:
                        run_nwb_pipeline(experiment, non_doc=True)
                    else:
                        run_nwb_pipeline(experiment)
    """
    