import subprocess
import pathlib
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--session', help='Session of experiment', required=True)

def run_align_timestamps(session:str):
    json_directory = pathlib.Path('//allen/programs/mindscope/workgroups/np-exp', session, 'SDK_jsons')

    align_timestamps_module = 'python -m allensdk.brain_observatory.ecephys.align_timestamps --input_json {} --output_json {}'.format(pathlib.Path(json_directory, 'align_timestamps_generated_input.json').as_posix(),
                                                                                                                                      pathlib.Path(json_directory, 'align_timestamps_generated_output.json').as_posix())
    
    subprocess.run(align_timestamps_module, shell=True)

if __name__ == '__main__':
    args = parser.parse_args()

    run_align_timestamps(args.session)