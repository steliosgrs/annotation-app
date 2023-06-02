import matplotlib.pyplot as plt
from skimage import io
import collections
from matplotlib.animation import FuncAnimation



def show_landmarks(preds, images):

    def frame_gen():
        for frame_num, image in enumerate(images):
            yield frame_num, image
        
    # 2D-Plot
    plot_style = dict(marker='o',
                    markersize=4,
                    linestyle='-',
                    lw=2)

    pred_type = collections.namedtuple('prediction_type', ['slice', 'color'])
    pred_types = {
                'eye1': pred_type(slice(36, 42), (0.596, 0.875, 0.541, 0.3)),
                'eye2': pred_type(slice(42, 48), (0.596, 0.875, 0.541, 0.3)),
                'lips': pred_type(slice(48, 60), (0.596, 0.875, 0.541, 0.3)),
                }

    fig = plt.figure(figsize=(16,16))
    ax = fig.add_subplot(1, 1, 1)
    line, = ax.plot([], [])

    # ax.axis('off')
    # ax.view_init(elev=90., azim=90.)
    # ax.set_xlim(ax.get_xlim()[::-1])

    # Ploting - Use Animations from plt 
    # create a figure with two subplots
    def animate(images):
        frame, image = images
        # for pred_type in pred_types.values():
        #     ax.plot(preds[pred_type.slice, 0],
        #             preds[pred_type.slice, 1],
        #             color=pred_type.color, **plot_style)
            
        line.set_data(frame,image )
        # line.set_data(frame_num, )
        return line

    # Create animation object
    anim = FuncAnimation(fig, animate, frame_gen, 
                            interval = 20, blit = True)

    anim.save(f'decord/animation.mp4', writer = 'ffmpeg', fps = 30)