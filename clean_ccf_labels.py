import pandas as pd
import pickle
import np_session
import numpy as np
import pathlib
from typing import Union
import copy

def get_closest_coordinate(coordinate:np.ndarray, ccf_coordinates_areas:np.ndarray):
    distances = np.sum((ccf_coordinates_areas - coordinate)**2, axis=1)
    return np.argmin(distances)

def get_channel_anchor_differences(channel:int, anchors: list):
    anchor_differences = [abs(channel_anchor - channel) for channel_anchor in anchors]
    return anchor_differences

def clean_label(channel_coordinates:pd.DataFrame, channels:list, anchors:list, mouse_id:str, day:str):
    channel_coordinates['region_cleaned'] = channel_coordinates['region']
    y = [channel[1] for channel in channels]
    anchors = [y.index(point) for point in anchors if point in y]

    for index, row in channel_coordinates.iterrows():  
        if pd.isna(row.region):
            if row.channel < 330:
                anchors_modify = copy.deepcopy(anchors)
                anchor_differences = get_channel_anchor_differences(row.channel, anchors)
                coordinate = np.array([row.AP, row.DV, row.ML])
                min_anchor_distance = min(anchor_differences)
                min_anchor_channel = anchors[anchor_differences.index(min_anchor_distance)]

                anchor_differences.remove(min_anchor_distance)
                anchors_modify.remove(min_anchor_channel)

                if len(anchor_differences) != 0:
                    second_closest_distance = min(anchor_differences)
                    second_closest_anchor = anchors_modify[anchor_differences.index(second_closest_distance)]
                else:
                    second_closest_anchor = -1

                if row.channel <= min_anchor_channel:
                    if len(anchor_differences) == 0 or row.channel <= second_closest_anchor:
                        ccf_coordinates_areas = channel_coordinates.loc[(~pd.isna(channel_coordinates['region']))
                                                                     & (channel_coordinates['channel'] < min_anchor_channel)]
                        if len(ccf_coordinates_areas) == 0:
                            ccf_coordinates_areas = channel_coordinates.loc[(~pd.isna(channel_coordinates['region']))
                                                                     & (channel_coordinates['channel'] > min_anchor_channel)]
                    else:
                        no_areas = channel_coordinates.loc[(pd.isna(channel_coordinates['region']))
                                                                     & (channel_coordinates['channel'] < min_anchor_channel)
                                                                     & (channel_coordinates['channel'] > second_closest_anchor)]
                        
                        areas_boundary = channel_coordinates.loc[(channel_coordinates['channel'] < min_anchor_channel)
                                                                     & (channel_coordinates['channel'] > second_closest_anchor)]
                        
                        if len(no_areas) == len(areas_boundary):
                            ccf_coordinates_areas = channel_coordinates.loc[(~pd.isna(channel_coordinates['region']))
                                                                     & (channel_coordinates['channel'] > min_anchor_channel)]
                        else:
                            ccf_coordinates_areas = channel_coordinates.loc[(~pd.isna(channel_coordinates['region']))
                                                                     & (channel_coordinates['channel'] < min_anchor_channel)
                                                                     & (channel_coordinates['channel'] > second_closest_anchor)]
                else:
                    if len(anchor_differences) == 0 or row.channel >= second_closest_anchor:
                        ccf_coordinates_areas = channel_coordinates.loc[(~pd.isna(channel_coordinates['region']))
                                                                     & (channel_coordinates['channel'] > min_anchor_channel)]
                    else:
                        no_areas = channel_coordinates.loc[(pd.isna(channel_coordinates['region']))
                                                                     & (channel_coordinates['channel'] > min_anchor_channel)
                                                                     & (channel_coordinates['channel'] < second_closest_anchor)]
                        
                        areas_boundary = channel_coordinates.loc[(channel_coordinates['channel'] > min_anchor_channel)
                                                                     & (channel_coordinates['channel'] < second_closest_anchor)]
                        
                        if len(no_areas) == len(areas_boundary):
                            ccf_coordinates_areas = channel_coordinates.loc[(~pd.isna(channel_coordinates['region']))
                                                                     & (channel_coordinates['channel'] > second_closest_anchor)]
                        else:
                            ccf_coordinates_areas = channel_coordinates.loc[(~pd.isna(channel_coordinates['region']))
                                                                     & (channel_coordinates['channel'] > min_anchor_channel)
                                                                     & (channel_coordinates['channel'] < second_closest_anchor)]

                
                ccf_coordinates = ccf_coordinates_areas[['AP', 'DV', 'ML']].to_numpy()
                closest_ccf_coord_index = get_closest_coordinate(coordinate, ccf_coordinates)
                area = ccf_coordinates_areas.iloc[closest_ccf_coord_index]['region']
                channel_coordinates.loc[index, 'region_cleaned'] = area
    
    ccf_alignment_path = pathlib.Path('//allen/programs/mindscope/workgroups/np-behavior/tissuecyte', mouse_id, 
                                             'Probe_{}_channels_{}_warped_cleaned.csv'.format(probe+day, mouse_id))
    channel_coordinates.drop(columns=['region'], inplace=True)
    channel_coordinates.rename(columns={'region_cleaned': 'region'}, inplace=True)
    channel_coordinates.fillna('No Area', inplace=True)
    channel_coordinates.to_csv(ccf_alignment_path, index=False)
    #print()

def get_day_from_pickle(session:np_session.Session) -> str:
    npexp_path = session.npexp_path
    behavior_stimulus_file = pathlib.Path(npexp_path, '{}.behavior.pkl'.format(npexp_path.as_posix()[npexp_path.as_posix().rindex('/')+1:]))
    behavior_dict = pd.read_pickle(behavior_stimulus_file)

    ephys_day = behavior_dict['items']['behavior']['params']['stage']
    day = int(ephys_day[ephys_day.index('_') + 1:])

    return str(day)

def get_channel_annotations_anchors_paths(session: np_session.Session, current_probe:str) -> Union[tuple[pathlib.Path, pathlib.Path, str, str], None]:
    session_data_dict = session.data_dict
    # get channel dataframe
    mouse_id = session_data_dict['external_specimen_name']
    probe = current_probe[-1]
    day = session_data_dict['stimulus_name'][-1] if session_data_dict['stimulus_name'] is not None else get_day_from_pickle(session)


    ccf_alignment_path = pathlib.Path('//allen/programs/mindscope/workgroups/np-behavior/tissuecyte', mouse_id, 
                                             'Probe_{}_channels_{}_warped.csv'.format(probe+day, mouse_id))

    if not ccf_alignment_path.exists():
        return None
    
    anchor_path = ccf_alignment_path.parent / 'anchors' / 'Probe_{}_anchors.pickle'.format(probe+day)
    return ccf_alignment_path, anchor_path, mouse_id, day

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
                        channel_coordinates = pd.read_csv(channel_anchors_paths[0])
                        print(channel_anchors_paths[0])
                        with open(channel_anchors_paths[1], 'rb') as f:
                            alignments = pickle.load(f)
                            anchors = alignments[3]
                            channels = alignments[0]

                            if len(anchors) > 0:
                                clean_label(channel_coordinates, channels, anchors, channel_anchors_paths[2], channel_anchors_paths[3]) 
        
        #if experiment == '1183071525_607660_20220609':
        #    break


