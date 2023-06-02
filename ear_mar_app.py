import os
from pathlib import Path
from animations_app import main_plot
import datetime
import time
import gc
import logging

from writer_influx import send_data, fetch_data
from perclos import Perclos
from pom import POM

from spiga.demo.analyze.extract.spiga_processor import SPIGAProcessor
import spiga.demo.analyze.track.get_tracker as tr
from spiga.demo.analyze.analyzer import VideoAnalyzer

from spiga.inference.framework import SPIGAFramework
from spiga.inference.config import ModelConfig
from spiga.demo.visualize.plotter import Plotter

from decord import VideoReader as vr
from decord import cpu
import skvideo.io
import cv2
import numpy as np
import pandas as pd
import tensorflow as tf

# https://github.com/1adrianb/face-alignment/issues/151
FACIAL_LANDMARKS_IDXS = dict([
	("right_eye", list(range(60, 69, 1))), # -1 
	("left_eye",  list(range(68, 77, 1))), # -1 
	("outer_mouth", list(range(76, 89, 1))) # -1
])

font = cv2.FONT_HERSHEY_SIMPLEX

def landmarks_per_frame_spiga(video, faces_analyzer, output = None, unix_timestamps = None):
	landmarks_list = []
	for i, frame in enumerate(video):
		# frame = frame.asnumpy()
		tracked_obj = faces_analyzer.process_frame(frame)
		# landmarks = np.array(np.zeros((98,2)))
		landmarks = np.empty((98,2))
		landmarks.fill(np.nan)
		if unix_timestamps is not None:
			ts, ms = divmod(unix_timestamps[i], 1000)
			ts = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(ts))
			text = ts + "." +f"{ms:03d}"
			cv2.putText(frame, text, (int(frame.shape[0]*0.6), int(frame.shape[1]*0.95)), font, 0.4, (0, 0, 0), 1, cv2.LINE_AA)
		if tracked_obj:
			landmarks = np.array(tracked_obj[-1].landmarks)
			for key,points in FACIAL_LANDMARKS_IDXS.items():
				points_cords = landmarks[points[0]: points[-1]]
				# print(f"Points ({points[0]}, {points[-1]}) & len: {len(points_cords)}")

				for x,y in points_cords:
					cv2.circle(frame, (int(x), int(y)), 1, (0, 255, 0), -1)

			if output is not None:
				output.write(cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))

			landmarks_list.append(landmarks)

		else:
			if output is not None:
				output.write(cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
			landmarks_list.append(landmarks)
			# print("No faces found")
			# logging.warning(f"")

	landmarks = np.stack(landmarks_list, axis=0)
	
	return landmarks, output

def get_ear(landmarks):
	# landmarks: [[left_eye: p0, p1, p2, p3, p4, p5], [right_eye: p0, p1, p2, p3, p4, p5]], with p0=(x0,y0) or p0=(x0,y0,z0)
	# ear: ((p1 - p5) + (p2 - p4)) / (2 * (p0 - p3))
	landmarks = tf.convert_to_tensor(landmarks, dtype=tf.float32)
	ear = tf.map_fn(lambda p: (tf.norm(p[1, :] - p[7, :], ord=2, keepdims=False) + tf.norm(p[3, :] - p[5, :], ord=2, keepdims=False)) / (2.0 * tf.norm(p[0, :] - p[4, :], ord=2, keepdims=False) + 0.0001),
				landmarks, fn_output_signature=tf.TensorSpec(shape=(), dtype=tf.float32))
	return ear

def get_mar(landmarks):
	# landmarks: [p0-p11], with p0=(x0,y0) or p0=(x0,y0,z0)
	# mar: ((p2 - p10) + (p3 - p9) + (p4 - p8)) / (2 * (p0 - p6))
	# https://link.springer.com/chapter/10.1007/978-981-16-5987-4_63#:~:text=Mouth%20aspect%20ratio%20(MAR)%20is,calculation%20is%20as%20shown%20(Figs.
	p = tf.convert_to_tensor(landmarks, dtype=tf.float32)
	mar = (((
				tf.norm(p[1, :] - p[11, :], ord=2, keepdims=False) +
				# tf.norm(p[2, :] - p[10, :], ord=2, keepdims=False) +
				tf.norm(p[3, :] - p[9, :], ord=2, keepdims=False) +
				# tf.norm(p[4, :] - p[8, :], ord=2, keepdims=False) 
				tf.norm(p[5, :] - p[7, :], ord=2, keepdims=False)
			) / 
			(2.0 * tf.norm(p[0, :] - p[6, :], ord=2, keepdims=False) + 0.0001)))
	return mar

def ear_per_frame(landmarks):
	# landmarks [frame_count, landmark_count, landmark_dim]
	# Turn landmarks in format accepted by _get_ear
	ear_landmarks_left_eye = np.take(landmarks, FACIAL_LANDMARKS_IDXS['left_eye'], axis=1)
	ear_landmarks_right_eye = np.take(landmarks, FACIAL_LANDMARKS_IDXS['right_eye'], axis=1)
	
	# [frame_count, eye_count, eye_landmark_count, 2]
	eye_landmarks = np.stack([ear_landmarks_left_eye, ear_landmarks_right_eye], axis=1)

	ear_values = []
	for frame_eye_landmarks in eye_landmarks:                   
		ear_value = get_ear(frame_eye_landmarks)
		ear_value = np.average(ear_value)
		
		ear_values.append(ear_value)
		
	ear = np.stack(ear_values, axis=0)
	
	return ear

def mar_per_frame(landmarks):
	# landmarks [frame_count, landmark_count, 2]
	# Turn landmarks in format accepted by _get_mar
	mouth_landmarks = np.take(landmarks, FACIAL_LANDMARKS_IDXS['outer_mouth'], axis=1)
	
	mar_values = []
	for frame_mouth_landmarks in mouth_landmarks:                   
		mar_value = get_mar(frame_mouth_landmarks)
		mar_value = np.average(mar_value)
		
		mar_values.append(mar_value)
		
	mar = np.stack(mar_values, axis=0)
	
	return mar

def chunks(lst, n):
	"""Yield successive n-sized chunks from lst."""
	for i in range(0, len(lst), n):
		yield lst[i:i + n]

def write_csv(ear, mar, segment_timestamps, video_filename, output_dir, i):
	
	video_name = '_'.join(video_filename.split('.')[:-1])
	save_dir = output_dir.joinpath(video_name)
	save_dir.mkdir(parents=True, exist_ok=True)
	
	df = pd.DataFrame(
		{
			"EAR": ear,
			"MAR": mar,
			"Timestamp": segment_timestamps
		}
	)
	
	save_path = save_dir.joinpath(f'ear_mar_timestamps_{video_name}_{i}.csv')
	df.to_csv(save_path)

def frame_gen(chunk):
	for frame in chunk:
		yield frame

def ear_mar_extractor(video_dir, fps, output_dir, export_csv = False, export_video = False, 
					export_animations = False, video_with_animations = False, 
					segmented = False, export_landmarks = False  ):
	logging.basicConfig(level=logging.INFO ,filename='annotation_app.log', filemode='w')
	
	WIDTH = 480
	HEIGHT = 480
	
	type_timestamp = "unix"
	last_chuck_timestamp = 0
	last_video_timestamp = 0
	
	sp = SPIGAProcessor(dataset='wflw', features=('lnd'), gpus=[0])
	faces_tracker = tr.get_tracker("RetinaSort")
	faces_tracker.detector.set_input_shape(WIDTH,HEIGHT)
	faces_analyzer = VideoAnalyzer(faces_tracker, processor=sp)
	
	video_dir = Path(video_dir)
	output_dir = Path(output_dir)
	
	if output_dir.exists():
		main_plot(video_dir, output_dir, video_with_animations, segmented, fps)

	else:
		# output_dir.mkdir(parents=True, exist_ok=True)
		
		# Start time of the video in Unix timestamp format
		start_time = int(datetime.datetime.now().timestamp() * 1000)
		logging.info(f"Start time of the video: {start_time}")
		for root, dirs, files in os.walk(video_dir):
			for j, video_filename in enumerate(files):
				measurement = "EAR-MAR"
				metadata = [measurement, video_filename,type_timestamp]
				video_path = Path(root).joinpath(video_filename)
				print(video_path)
				videoName = video_path.stem
				
				vid = vr(str(video_path), width = 480, height = 480)
				vid_len = len(vid)
				step = vid_len//10

				index_frames = [x for x in range(vid_len)]
				index_segments = list(chunks(index_frames, step ))

				if j == 0:
					time = start_time
				else:
					time = last_video_timestamp
					logging.info(f"Start video {video_filename}, Timestamp {last_video_timestamp}")
					
				first_timestamp_video = time
				for i,chunk_inx in enumerate(index_segments):
					
					# print(chunk_inx[0], chunk_inx[-1])
					chunk = vid.get_batch(chunk_inx)
					chunk_numpy = list(frame_gen(chunk.asnumpy()))
					# print(vid.get_avg_fps())
					vid.skip_frames(step)
					
					timestamps = np.arange(len(chunk_inx)) * (1 / (fps)) #[0., 0.05, 0.1, 0.15, 0.2, 0.25, 0.3]
					
					if i != 0 :
						time = last_chuck_timestamp
						
					# Convert video timestamps to Unix timestamps in milliseconds
					unix_timestamps = [int((time + ts * 1000)) for ts in timestamps]
					if export_landmarks:
						h,w,c = chunk_numpy[0].shape
						# print(f"frames: {len(chunk_numpy)} height : {h}, width : {w}")
						output = cv2.VideoWriter(f"landmarks//{videoName}_{i}.mp4", cv2.VideoWriter_fourcc(*'mp4v'), float(fps), (w, h))

						# Calculate Landmarks segments
						landmarks, output = landmarks_per_frame_spiga(chunk_numpy, faces_analyzer, output, unix_timestamps)
						if output.isOpened():
							output.release()
					else:
						landmarks, output= landmarks_per_frame_spiga(chunk_numpy, faces_analyzer)

					ear = ear_per_frame(landmarks)
					mar = mar_per_frame(landmarks)

					# Send data in Influxdb
					print(len(ear), len(mar), len(unix_timestamps))
					send_data(ear, mar, unix_timestamps, metadata)

					if export_csv:
						write_csv(ear, mar, unix_timestamps, video_filename, output_dir, i)
						
					last_chuck_timestamp = unix_timestamps[-1]
					# logging.info(f"Last Timestamp {last_chuck_timestamp}, Video {video_filename}, Chunk {i} ")
					
				last_video_timestamp = last_chuck_timestamp
				# logging.info(f"End of video {video_filename}, Last Timestamp {last_video_timestamp}")
    
				print(f"Start time {first_timestamp_video}, Last video TimeStamp {last_video_timestamp}")
				ear, mar, timestamps = fetch_data(int(first_timestamp_video)*1000000, int(last_video_timestamp)*1000000,"EAR-MAR")
				print(len(ear), len(mar), len(timestamps))
				perclos = Perclos(ear_threshold=0.25, fps=fps).evaluate_perclos(ear)
				pom = POM(mar_threshold=0.4, fps=fps).evaluate_pom(mar)
				measurement = "PERCLOS-POM"
				# type_timestamps = "unix"
				type_timestamps = "datetime"
				metadata = [measurement, video_filename, type_timestamps]
				# print(len(perclos), len(pom), len(timestamps))
				send_data(perclos, pom, timestamps, metadata)
				
				del vid, landmarks
				gc.collect()
				# """
				
		if export_animations:
			main_plot(video_dir, output_dir, video_with_animations, segmented, fps)
	