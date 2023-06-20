import argparse
from pathlib import Path
import os
"""
import pandas as pd

from ear_mar_app import ear_mar_extractor
from writer_influx import fetch_data, send_data, delete_data

from perclos import Perclos
from plot_perclos import show_perclos
from pom import POM
from plot_pom import show_pom

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

"""

if __name__ == '__main__':
    arg_parse = argparse.ArgumentParser()
    arg_parse.add_argument("--video_dir", help="Directory of videos", default='./videos')
    arg_parse.add_argument("--output_dir", help="Directory of output csv", default='./csv')
    arg_parse.add_argument("fps", help="FPS", default='20', type=int)

    args = arg_parse.parse_args()
    fps = args.fps
    video_dir = args.video_dir
    # video_dir = Path(args.video_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    print(fps)

    # fps = 20
    segments = True
    export_video = False
    export_landmarks = False

    export_csv = False
    export_animations = False
    video_with_animations = False

    export_perclos = False
    export_pom = False
    for root, dirs, files in os.walk(video_dir):
        for j, video_filename in enumerate(files):
            print(video_filename)

    # folders = [landmarks_vid, per_out, pom_out, segm_out]

    # ear_mar_extractor(video_dir, fps, csv_dir, export_csv, export_video, export_animations, video_with_animations, segments, export_landmarks)

    # Influx
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