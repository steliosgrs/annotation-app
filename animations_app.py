from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from moviepy.editor import VideoFileClip, CompositeVideoClip, vfx

# Paths Folder
output_animations = 'output/animations/'
output_videos = 'output/video_with_animation/'


def main_plot(video_dir, output_dir, video_with_animations, segmented, fps):
    # Initialize data and values
    print("Generating animations for EAR MAR")
    for file in output_dir.glob('*/*.csv'):

        data = pd.read_csv(file)

        print(Path(file).parent.name)
        filename = Path(file).parent.name
        i = str(file.stem).split('_')[-1]
        # i = file.stem[-1]
        # Get Values from dataframe
        Timestamp_values = list(data.index.values)
        # Timestamp_values = list(data.Timestamp.values)
        Mar_values = list(data.MAR.values)
        Ear_values = list(data.EAR.values)

        # Ploting - Use Animations from plt 
        fig, (ax1, ax2) = plt.subplots(2,1)

        # intialize two line objects (one in each axes)
        line1, = ax1.plot([], [], lw=1)
        line2, = ax2.plot([], [], lw=1, color='r')
        line = [line1, line2]

        # initalizations axes 
        for ax in [ax1, ax2]:
            ax.set_xlim(0, float(Timestamp_values[-1]))
            ax.grid()

        ax1.set_ylim(0, 1.1)
        ax1.set_title("MAR")
        ax2.set_ylim(0, 0.5)
        ax2.set_title("EAR")

        def animate(frame_num):
            x = Timestamp_values[:frame_num]
            y1 = Mar_values[:frame_num]
            y2 = Ear_values[:frame_num]

            # update the data of both line objects
            line[0].set_data(x, y1)
            line[1].set_data(x, y2)
            return line

        # Create animation object
        anim = FuncAnimation(fig, animate, frames = len(Timestamp_values))
                            #  ,interval = 20, blit = True)
        
        # print(filename)
        if not Path(output_animations).exists():
            Path(output_animations).mkdir(parents=True, exist_ok=True)

        output_videos_path = Path(output_videos)
        if not output_videos_path.exists():
            output_videos_path.mkdir(parents=True, exist_ok=True)

        path_animation = f"{output_animations}animation-{filename}_{i}"

        # Save animation with ffmpeg
        anim.save(f'{path_animation}.mp4', writer = 'ffmpeg', fps = int(fps))

        if video_with_animations:
            # Read video and animation
            # video = VideoFileClip(f"uta/{filename}.mp4")

            video = VideoFileClip(f"landmarks/{filename}_{i}.mp4")
            # if segmented:
            #     video = VideoFileClip(f"output/seg/{filename}/{i}.mp4")
            # else:
            #     video = VideoFileClip(f"uta/{filename}.mp4")
            graph_animation = VideoFileClip(f"{path_animation}.mp4")
        
            # Rescale animation
            graph_animation = graph_animation.fx(vfx.resize, 1.1)

            width, height = video.size
            extra_width , extra_height = graph_animation.size
            
            # Video union
            graph_video = CompositeVideoClip([video,
                                            graph_animation.set_position(('right','top')) ], 
                                            size=[width+extra_width, height]
                                            )
            
            # graph_video.write_videofile(f"{output_videos}{filename}-EAR-MAR.mp4") # Segments = False

            save_dir = Path(output_videos_path.joinpath(filename))
            if not save_dir.exists():
                save_dir.mkdir(parents=True, exist_ok=True)
            graph_video.write_videofile(f"{output_videos}{filename}/EAR-MAR_{i}.mp4") # Segments = True
        
