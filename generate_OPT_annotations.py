import pandas as pd
import pathlib
import SimpleITK as sitk
import numpy as np
import pickle

with open(pathlib.Path(r"\\allen\programs\mindscope\workgroups\np-behavior\tissuecyte\field_reference\acrnm_map.pkl"), 'rb') as f:
    ACRONYM_MAP = pickle.load(f)

ANNOTATION_VOLUME = sitk.GetArrayFromImage(sitk.ReadImage(pathlib.Path(r"\\allen\programs\mindscope\workgroups\np-behavior\tissuecyte\field_reference\ccf_ano.mhd")))

ANNOTATION_PATH = pathlib.Path('//allen/programs/mindscope/workgroups/np-behavior/tissuecyte')

def get_closest_channel(probe_ccf_coordinates:pd.DataFrame, channel:int) -> int:
    return (probe_ccf_coordinates['channels']-channel).abs().argsort()[:1]   

def get_structure_acronym(acronym_map:dict[str, int], annotation_volume:np.ndarray, point:tuple[int, int, int]) -> str:
    if point[1] < 0:
        return 'out of brain'
    
    structure_ids = tuple(acronym_map.values())
    labels = tuple(acronym_map.keys())

    structure_id = annotation_volume[point[0], point[1], point[2]]
    if structure_id in structure_ids:
        index = structure_ids.index(structure_id)
        label = labels[index]
    else:
        label = 'root'
    
    return label

def convert_OPT_annotations(opt_coordinates_path:pathlib.Path, mouse_id:str):
    opt_ccf_coordinates = pd.read_csv(opt_coordinates_path)
    probes = opt_ccf_coordinates['probe'].unique()

    for probe in probes:
        probe_day = probe[probe.index(' ')+1:]
        probe_output:dict = {'AP': [], 'DV': [], 'ML': [], 'region': [], 'channel': []}

        probe_ccf_coordinates = opt_ccf_coordinates[opt_ccf_coordinates['probe'] == probe]

        for i in range(384):
            channel_index = get_closest_channel(probe_ccf_coordinates, i)
            probe_ccf_channel = probe_ccf_coordinates.iloc[channel_index]

            ap = int(probe_ccf_channel['A/P'] / 0.025)
            dv = int(probe_ccf_channel['D/V'] / 0.025)
            ml = int(probe_ccf_channel['M/L'] / 0.025)
            ml = 456 - ml

            probe_output['AP'].append(ap)
            probe_output['DV'].append(dv)
            probe_output['ML'].append(ml)
            probe_output['region'].append(get_structure_acronym(ACRONYM_MAP, ANNOTATION_VOLUME, (ap, dv, ml)))
            probe_output['channel'].append(i)
        
        if not (ANNOTATION_PATH / mouse_id).exists():
            (ANNOTATION_PATH / mouse_id).mkdir()

        df_probe = pd.DataFrame(probe_output)
        df_probe.to_csv((ANNOTATION_PATH / mouse_id / f'Probe_{probe_day}_channels_{mouse_id}_warped.csv'), index=False)

if __name__ == '__main__':
    opt_coordinates_path = pathlib.Path(r"\\allen\programs\mindscope\workgroups\np-behavior\SevDR\611166\611166\images\final_ccf_coordinates.csv")
    mouse_id = '611166'
    convert_OPT_annotations(opt_coordinates_path, mouse_id)