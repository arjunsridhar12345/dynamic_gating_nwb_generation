import pathlib
import os
import stat
import shutil

NWB_DIRECTORY = pathlib.Path('//allen/programs/mindscope/workgroups/dynamicrouting/dynamic_gating/nwbs_remade/nwbs')

def check_and_update_rescaled_paths(nwb_paths: tuple[pathlib.Path, ...]) -> None:
    rescaled_paths = tuple(path for path in nwb_paths if 'rescaled' in str(path))
    if not rescaled_paths:
        return
    
    non_rescaled_paths = tuple(path for path in nwb_paths if 'rescaled' not in str(path))
    for path in non_rescaled_paths:
        path.unlink()
    
    for path in rescaled_paths:
        str_path = str(path)
        new_path = str_path.replace('_rescaled', '')
        path.rename(new_path)

def remove_readonly(fn, path, excinfo):
    try:
        os.chmod(path, stat.S_IWRITE)
        fn(path)
    except Exception as exc:
        print("Skipped:", path, "because:\n", exc)

def remove_non_nwb_files(nwb_session_path: pathlib.Path) -> None:
    all_paths = tuple(nwb_session_path.glob('*'))
    nwb_paths = tuple(nwb_session_path.glob('*.nwb'))

    non_nwb_paths = tuple(path for path in all_paths if path not in nwb_paths)
    for path in non_nwb_paths:
        if path.is_dir():
            shutil.rmtree(path.as_posix(), onerror=remove_readonly)
            continue

        path.unlink()
    
    check_and_update_rescaled_paths(nwb_paths)

if __name__ == '__main__':
    all_folders_and_files = tuple(NWB_DIRECTORY.glob('*'))

    for path in all_folders_and_files:
        if not path.is_dir():
            continue

        if not tuple(path.glob('*.nwb')):
            shutil.rmtree(path.as_posix(), onerror=remove_readonly)

        remove_non_nwb_files(path)
