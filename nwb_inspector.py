import pandas as pd
import pathlib
import subprocess

def run_nwb_inspector(nwb_session_directory: pathlib.Path) -> None:
    nwb_inspector_command = f"nwbinspector {nwb_session_directory.as_posix()} --config dandi --report-file-path {(nwb_session_directory / 'nwb_inspector.txt').as_posix()}"
    
    subprocess.run(nwb_inspector_command)

def is_critical_violations(nwb_session_directory) -> bool:
    with open(nwb_session_directory / 'nwb_inspector.txt') as f:
        text = f.read()
        if 'CRITICAL' in text:
            return True
    
    return False
     
if __name__ == '__main__':
    dynamic_gating_spreadsheet = pd.read_excel(pathlib.Path(r"\\allen\programs\mindscope\workgroups\dynamicrouting\dynamic_gating\DynamicGatingProduction_final.xlsx"))
    nwb_directory = pathlib.Path('//allen/programs/mindscope/workgroups/dynamicrouting/dynamic_gating/nwbs')
    experiments = dynamic_gating_spreadsheet['exp_id'].values

    critical_failed_experiments = []
    for experiment in experiments:
        nwb_session_directory = pathlib.Path(nwb_directory, experiment[0:experiment.index('_')])
        if nwb_session_directory.exists():
                if len(list(nwb_session_directory.glob('*.nwb'))) > 1:
                    print(nwb_session_directory)
                    #run_nwb_inspector(nwb_session_directory)
                    if is_critical_violations(nwb_session_directory):
                         critical_failed_experiments.append(experiment)
    
    print(critical_failed_experiments)
                    