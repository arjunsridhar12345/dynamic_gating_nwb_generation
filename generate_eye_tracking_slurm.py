import np_session
import pathlib 

def write_eye_tracking_slurm_file(session_id: str, directory_path: pathlib.Path) -> None:
    video_path = tuple(directory_path.glob(f'{session_id}.eye.mp4'))
    if not video_path:
        raise FileNotFoundError(f'{session_id} has no eye tracking video. Check {directory_path.as_posix()}')
    
    sbatch_script = \
    f"""#!/bin/bash
#SBATCH --partition=braintv
#SBATCH --qos=production
#SBATCH --nodes=1 --cpus-per-task=4 --gpus=1 --mem=32G
#SBATCH --time=24:00:00
#SBATCH --export=NONE
#SBATCH --job-name=ECEPHYS_EYE_TRACKING_QUEUE_{session_id}
#SBATCH --output={(directory_path / 'ECEPHYS_EYE_TRACKING_QUEUE.log').as_posix()[1:]}
#SBATCH --mail-type=NONE 
umask 022
source activate /allen/aibs/technology/waynew/conda/dlcPy36/
python /allen/aibs/technology/waynew/eye/bin/eye_dlc_phase1.py {video_path[0].as_posix()[1:]} {(directory_path / f"{session_id}.eyeDeepCut_resnet50_universal_eye_trackingJul10shuffle1_1030000.h5").as_posix()[1:]}
"""

    with open(directory_path / f'ECEPHYS_EYE_TRACKING_JOB_{session_id}.sh', 'wb') as f:
        f.write(bytes(sbatch_script, encoding='utf8').replace(b'\r\n', b'\n'))

def write_ellipse_fit_slurm_file(session_id: str, directory_path: pathlib.Path) -> None:
    eye_tracking_h5_path = tuple(directory_path.glob(f'{session_id}*.h5'))
    if not eye_tracking_h5_path:
        raise FileNotFoundError(f'{session_id} has no eye tracking h5. Most likely has not been run or failed')

    sbatch_script = \
    f"""#!/bin/bash
#SBATCH --partition=braintv
#SBATCH --qos=production
#SBATCH --nodes=1 --cpus-per-task=1 --mem=20G
#SBATCH --time=5:00:00
#SBATCH --export=NONE
#SBATCH --job-name=ECEPHYS_EYE_ELLIPSE_FIT_QUEUE_{session_id}
#SBATCH --output={(directory_path / 'ECEPHYS_EYE_ELLIPSE_FIT_QUEUE.log').as_posix()[1:]}
#SBATCH --mail-type=NONE 
umask 022
source activate /allen/aibs/technology/waynew/conda/dlcPy36/
python /allen/aibs/technology/waynew/eye/bin/eye_dlc_phase2.py {eye_tracking_h5_path[0].as_posix()[1:]} {(directory_path / f"{session_id}_ellipse.h5").as_posix()[1:]}
"""
    with open(directory_path / f'ECEPHYS_EYE_ELLIPSE_FIT_JOB_{session_id}.sh', 'wb') as f:
        f.write(bytes(sbatch_script, encoding='utf8').replace(b'\r\n', b'\n'))

if __name__ == '__main__':
    session_id = '1375871900_725107_20240625'
    session = np_session.Session(session_id)
    write_eye_tracking_slurm_file(session_id, session.npexp_path)
    write_ellipse_fit_slurm_file(session_id, session.npexp_path)