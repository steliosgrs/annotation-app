import os
import pandas as pd

class Perclos():

    def __init__(self, ear_threshold=0.25, fps=20) -> None:
        self.ear_threshold = ear_threshold
        self.fps = fps
        # self.time_duration = time_duration
        self.current_frame = 0
        self.running_window = []
        self.total_window_size = 90
        self.sequential_blinks = 0
        self.alert = self.sequential_blinks >= 9
        self.danger = self.sequential_blinks >= 14
        print("Calculating PERCLOS")
    
    def calculate_perclos(self, window):
        # Window of blinks 
        return round(sum(window) / len(window) , 3)
        
    def run_window(self, blinking_list, total_window_size ):
        perclos_values = []
        window = []
        for blink in blinking_list:
            window.append(blink)
            
            if blink == 1:
                self.sequential_blinks+=1
            else:
                self.sequential_blinks = 0

            if self.alert:
                print("Alert")                
                if self.danger:
                    print("Danger")
                    
            perclos_value = self.calculate_perclos(window)
            perclos_values.append(perclos_value)
            if len(window) > total_window_size:
                window.pop(0)
                
        return perclos_values
                
        # blinking_list
        # perclos = calculate_perclos(window)
        # perclos_values.append(perclos)
    def calculate_perclos_running(self, blinking_list ):
        
        
        perclos = 0
        perclos_list = []
        
        # ear_loop = blinking_list[:-self.current_frame]
        for blink in blinking_list:

            self.current_frame += 1
            
            # calculate the perclos
            print(len(self.running_window)) # DEBUG
            perclos = round(sum(blinking_list) / len(self.running_window) , 3)

            if len(self.running_window) >= 90:
                blinking_list.pop(0)
                self.running_window.pop(0)

            perclos_list.append(perclos)

        return perclos_list
    
    def evaluate_perclos(self, ear):

        perclos = 0
        perclos_list= []
        blinking_list = []

        # ear_loop = ear[self.current_frame:]
        # for ear_value in ear_loop:
        for ear_value in ear:
            if (ear_value < self.ear_threshold):
                self.running_window.append(1)
                blinking_list.append(1)
            else:
                self.running_window.append(0)
                blinking_list.append(0)

            # calculate the perclos
            # print(len(self.running_window)) # DEBUG
            perclos = round(sum(blinking_list) / len(self.running_window) ,3) # UTARL DD
            # perclos = round(sum(blinking_list) / 300,3) # SUST DD

            self.current_frame += 1
            if len(self.running_window) >= 90:
                blinking_list.pop(0)
                self.running_window.pop(0)

            perclos_list.append(perclos)

        return perclos_list


    def get_perclos(self, video_dir, csv_dir):

        perclos_by_video, clusters, video_names = [], [], [] 

        for i, (path, dirs, files) in enumerate(os.walk(csv_dir)):
            for i, file in enumerate(files):
                # print(path, file)
                self.running_window = []
                self.current_frame = 0
                file_list = file.split('_')
                video_name = '_'.join((file_list[-2],file_list[-1])).strip()
                # print(video_name)
                video_name = video_name.split('.')[0]
                base_video_name = video_name.split('_')[0]

                print(f" ==== Video filename: {video_name} ==== ")

                video_names.append(base_video_name+"_"+str(i))
                csv_file = f'ear_mar_timestamps_{video_name}.csv'
                path_file_csv = os.path.join(csv_dir,base_video_name,csv_file)

                df = pd.read_csv(path_file_csv)
                ear = df['EAR'].values

                perclosID = []

                while (self.current_frame < len(ear)):
                    # print(f" CF: {current_frame} Video Frames: {len(video)}")
                    perclos = self.evaluate_perclos(ear, self.ear_threshold)
                    perclosID.append(perclos)

                perclos_by_video.append(perclosID)
        return perclos_by_video, clusters, video_names
