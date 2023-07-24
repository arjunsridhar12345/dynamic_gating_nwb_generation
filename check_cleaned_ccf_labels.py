import pandas as pd
import pathlib
import np_session
from typing import Union
from clean_ccf_labels import get_day_from_pickle
import matplotlib.pyplot as plt
import pickle

def get_channel_annotations_anchors_paths(session: np_session.Session, current_probe:str) -> Union[tuple[pathlib.Path, pathlib.Path, pathlib.Path], None]:
    session_data_dict = session.data_dict
    # get channel dataframe
    mouse_id = session_data_dict['external_specimen_name']
    probe = current_probe[-1]
    day = session_data_dict['stimulus_name'][-1] if session_data_dict['stimulus_name'] is not None else get_day_from_pickle(session)


    ccf_alignment_path_cleaned = pathlib.Path('//allen/programs/mindscope/workgroups/np-behavior/tissuecyte', mouse_id, 
                                             'Probe_{}_channels_{}_warped_cleaned.csv'.format(probe+day, mouse_id))
    
    ccf_alignment_path = pathlib.Path('//allen/programs/mindscope/workgroups/np-behavior/tissuecyte', mouse_id, 
                                             'Probe_{}_channels_{}_warped.csv'.format(probe+day, mouse_id))

    if not ccf_alignment_path.exists():
        return None
    
    anchor_path = ccf_alignment_path.parent / 'anchors' / 'Probe_{}_anchors.pickle'.format(probe+day)
    return ccf_alignment_path_cleaned, ccf_alignment_path, anchor_path

if __name__  == '__main__':
    dynamic_gating_spreadsheet = pd.read_excel(pathlib.Path(r"\\allen\programs\mindscope\workgroups\dynamicrouting\dynamic_gating\DynamicGatingProduction_final.xlsx"))
    nwb_directory = pathlib.Path('//allen/programs/mindscope/workgroups/dynamicrouting/dynamic_gating/nwbs')
    experiments = dynamic_gating_spreadsheet['exp_id'].values

    for experiment in experiments:
        nwb_session_directory = pathlib.Path(nwb_directory, experiment[0:experiment.index('_')])
        if nwb_session_directory.exists():
            if len(list(nwb_session_directory.glob('*.nwb'))) > 0:
                session = np_session.Session(experiment)
                probe_metrics_csv = session.probe_letter_to_metrics_csv_path

                for probe in probe_metrics_csv:
                    current_probe = 'probe' + probe
                    channel_anchors_paths = get_channel_annotations_anchors_paths(session, current_probe)

                    if channel_anchors_paths is not None:
                        channel_coordinates_cleaned = pd.read_csv(channel_anchors_paths[0])
                        channel_coordinates = pd.read_csv(channel_anchors_paths[1])
                        with open(channel_anchors_paths[2], 'rb') as f:
                            anchors = pickle.load(f)[3]

                        fig, ax = plt.subplots(1, 2)
                        for index, row in channel_coordinates.iterrows():
                            if pd.isna(row.channel):
                                if row.channel in anchors:
                                    ax[0].text(0, index, 'No Area', color='C1')
                                else:
                                    ax[0].text(0, index, 'No Area')
                            else:
                                if row.channel in anchors:
                                    ax[0].text(0, index, row.region, color='C1')
                                else:
                                    ax[0].text(0, index, row.region)
                        
                            row_cleaned = channel_coordinates_cleaned.iloc[index]
                            ax[1].text(0, index, row_cleaned['region_cleaned'])

                        ax[0].set_ylim(0, index)
                        ax[1].set_ylim(0, index)
                        plt.show()

