from pathlib import Path

import pandas as pd

from ear_mar_app import ear_mar_extractor
from perclos import Perclos
from plot_perclos import show_perclos
from pom import POM
from plot_pom import show_pom
from writer_influx import fetch_data, send_data, delete_data
# CSV EAR - MAR
csv_dir = 'artifacts_app/'

# PERCLOS
per_out = 'perclos_output/'
pom_out = 'pom_output/'
# per_vid = 'perclos_animations/'

# Videos
segm_out = 'output/seg/'
video_dir = 'uta/'
landmarks_vid = 'landmarks/'

if __name__ == '__main__':

    fps = 20
    segments = True
    export_video = False
    export_landmarks = False

    export_csv = False
    export_animations = False
    video_with_animations = False

    export_perclos = False
    export_pom = False

    folders = [landmarks_vid, per_out, pom_out, segm_out]

    ear_mar_extractor(video_dir, fps, csv_dir, export_csv, export_video, export_animations, video_with_animations, segments, export_landmarks)

    """
    ear, mar, timestamps = fetch_data("2023-05-19T12:14:15Z","x","EAR-MAR")
    print(len(ear), len(mar))
    perclos = Perclos(ear_threshold=0.25, fps=fps).evaluate_perclos(ear)
    pom = POM(mar_threshold=0.4, fps=fps).evaluate_pom(mar)
    measurement = "PERCLOS-POM"
    type_timestamps = "unix"
    type_timestamps = "datetime"
    metadata = [measurement, None, type_timestamps]
    # print(len(perclos), len(pom), len(timestamps))
    print(len(perclos), len(pom), len(timestamps))
    send_data(perclos, pom, timestamps, metadata)
    """
    # calculate_perclos(fps, video_with_animations, segments, export_csv, export_perclos)
    # calculate_pom(fps, video_with_animations, segments, export_csv, export_pom)