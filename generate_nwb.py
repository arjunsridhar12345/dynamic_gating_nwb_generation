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

def run_nwb_pipeline(session:str, non_doc=False, is_dynamic_gating:bool=False, is_vbn_opto:bool=False, scale=1):
    session_errors:dict = {session:[]}
    generate_sdk_modules(session, is_dynamic_gating=is_dynamic_gating, non_doc=non_doc, scale=scale)
    
    json_directory = pathlib.Path('//allen/programs/mindscope/workgroups/np-exp', session, 'SDK_jsons')

    #align_timestamps_module = 'python -m allensdk.brain_observatory.ecephys.align_timestamps --input_json {} --output_json {}'.format(pathlib.Path(json_directory, 'align_timestamps_generated_input.json').as_posix(),
                                                                                                                                      #pathlib.Path(json_directory, 'align_timestamps_generated_output.json').as_posix())
    
    if is_dynamic_gating:
        stimulus_table_module = 'python -m ecephys_etl.modules.dynamic_gating_create_stim_table --input_json {} --output_json {}'.format(pathlib.Path(json_directory, 'stimulus_table_input.json').as_posix(),
                                                                                                                  pathlib.Path(json_directory, 'stimulus_table_output.json').as_posix())
    
    if is_vbn_opto:
        stimulus_table_module = 'python -m ecephys_etl.modules.vbn_opto_stimulus_table --input_json {} --output_json {}'.format(pathlib.Path(json_directory, 'stimulus_table_input.json').as_posix(),
                                                                                                                        pathlib.Path(json_directory, 'stimulus_table_output.json').as_posix())
    
    stimulus_table_response = subprocess.run(stimulus_table_module, shell=True, text=True, capture_output=True)
    session_errors[session].append(stimulus_table_response.stderr)

    if is_dynamic_gating:
        optotagging_module = 'python -m allensdk.brain_observatory.ecephys.optotagging_table --input_json {} --output_json {}'.format(pathlib.Path(json_directory, 'optotagging_input.json').as_posix(),
                                                                                                                            pathlib.Path(json_directory, 'optotagging_output.json').as_posix())
        opto_response = subprocess.run(optotagging_module, shell=True, text=True, capture_output=True)
        session_errors[session].append(opto_response.stderr)

    if is_dynamic_gating:
        nwb_module = 'python -m allensdk.brain_observatory.ecephys.write_nwb.dynamic_gating --input_json {} --output_json {}'.format(pathlib.Path(json_directory, 'nwb_input.json').as_posix(),
                                                                                                                                    pathlib.Path(json_directory, 'nwb_output.json').as_posix())
    if is_vbn_opto:
        nwb_module = 'python -m allensdk.brain_observatory.ecephys.write_nwb.vbn_opto --input_json {} --output_json {}'.format(pathlib.Path(json_directory, 'nwb_input.json').as_posix(),
                                                                                                                                    pathlib.Path(json_directory, 'nwb_output.json').as_posix())
    nwb_response = subprocess.run(nwb_module, shell=True, text=True)
    session_errors[session].append(nwb_response.stderr)

    with open('./session_errors.json', 'a') as f:
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
    
    session_ids_rescaled= [1174553025, 1174790219, 1175067685, 1175253205, 1176580734,
       1176791184, 1176989662, 1177900858, 1178173272, 1178460518,
       1178693650, 1179670730, 1179911454, 1180107381, 1180266229,
       1181096406, 1181324124, 1181731440, 1182427414, 1182628226,
       1182871514, 1183071525]
    
    sessions_rescaled = ['1174553025_608672_20220502' ,'1174790219_608672_20220503', '1175067685_608672_20220504', '1175253205_608672_20220505', 
                '1176580734_611160_20220511', '1176791184_611160_20220512', '1176989662_611160_20220513',
                '1177900858_608671_20220517', '1178173272_608671_20220518', '1178460518_608671_20220519', 
                '1178693650_608671_20220520', '1179670730_612090_20220524', '1179911454_612090_20220525', '1180107381_612090_20220526',
                '1180266229_612090_20220527', '1181096406_614547_20220531', '1181324124_614547_20220601',
                '1181731440_614547_20220603', '1182427414_607660_20220606', '1182628226_607660_20220607', '1182871514_607660_20220608',
                '1183071525_607660_20220609']
    
    for experiment in ['1176580734_611160_20220511']:
        nwb_session_directory = pathlib.Path(nwb_directory, experiment[0:experiment.index('_')])
        if nwb_session_directory.exists():
                if len(list(nwb_session_directory.glob('*.nwb'))) > 0:
                    print(experiment)
                    if experiment in non_doc_experiments:
                        if experiment in sessions_rescaled:
                            run_nwb_pipeline(experiment, non_doc=True, is_dynamic_gating=True, scale=2)
                        else:
                            run_nwb_pipeline(experiment, non_doc=True, is_dynamic_gating=True)
                    else:
                        if experiment in sessions_rescaled:
                            run_nwb_pipeline(experiment, is_dynamic_gating=True, scale=2)
                        else:
                            run_nwb_pipeline(experiment, is_dynamic_gating=True)
    
    