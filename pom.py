import os
import pandas as pd

class POM():

    def __init__(self, mar_threshold, fps) -> None:
        self.mar_threshold = mar_threshold
        self.fps = fps
        self.current_frame = 0
        self.running_window = []
        print("Calculating POM")
    
    def evaluate_pom(self, mar):

        pom = 0
        pom_list= []
        blinking_list = []

        mar_loop = mar[self.current_frame:]
        for mar_value in mar_loop:
            if (mar_value > self.mar_threshold):
                self.running_window.append(1)
                blinking_list.append(1)
            else:
                self.running_window.append(0)
                blinking_list.append(0)

            # calculate the pom
            # print(len(self.running_window)) # DEBUG
            pom = round(sum(blinking_list) / len(self.running_window) ,3) # UTARL DD
            # pom = round(sum(blinking_list) / 300,3) # SUST DD

            self.current_frame += 1
            if len(self.running_window) >= 90:
                blinking_list.pop(0)
                self.running_window.pop(0)

            pom_list.append(pom)

        return pom_list


    def get_pom(self, video_dir, csv_dir):

        pom_by_video, clusters, video_names = [], [], [] 

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
                ind = video_name.split('_')[-1]
                # print(ind)

                # print(f" ==== Video filename: {video_name} ==== ")

                video_names.append(base_video_name+"_"+str(ind))
                csv_file = f'ear_mar_timestamps_{base_video_name}_{ind}.csv'
                path_file_csv = os.path.join(csv_dir,base_video_name,csv_file)

                df = pd.read_csv(path_file_csv)
                mar = df['MAR'].values

                pomID = []

                while (self.current_frame < len(mar)):
                    # print(f" CF: {current_frame} Video Frames: {len(video)}")
                    pom = self.evaluate_pom(mar)
                    pomID.append(pom)

                pom_by_video.append(pomID)
        return pom_by_video, clusters, video_names


  