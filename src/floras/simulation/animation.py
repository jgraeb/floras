'''
Animate the simulation trace from the saved pkl file.
'''
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.collections import PatchCollection
import os
import glob
from PIL import Image, ImageOps
import _pickle as pickle

TILESIZE = 50

main_dir = os.path.dirname(os.path.dirname(os.path.realpath("__file__")))
robo_figure = main_dir + '/imglib/robot.png'


def draw_grid(grid, merge=False):
    map = grid.map
    size = max(map.keys())
    z_min = 0
    z_max = (size[0] + 1) * TILESIZE
    x_min = 0
    x_max = (size[1] + 1) * TILESIZE
    ax.set_xlim(x_min, x_max)
    ax.set_ylim(z_min, z_max)
    ax.xaxis.set_visible(False)
    ax.yaxis.set_visible(False)
    # fill in the road regions
    road_tiles = []
    x_tiles = np.arange(0, size[1] + 2) * TILESIZE
    y_tiles = np.arange(0, size[0] + 2) * TILESIZE

    for y in np.arange(0, size[0] + 1):
        for x in np.arange(0, size[1] + 1):
            if map[(y, x)] == '*':
                tile = patches.Rectangle(
                    (x_tiles[x], y_tiles[y]), TILESIZE, TILESIZE,
                    fill=True, color='black', alpha=.5
                )
            elif (y, x) in grid.colors:
                tile = patches.Rectangle(
                    (x_tiles[x], y_tiles[y]), TILESIZE, TILESIZE,
                    fill=True, color=grid.colors[(y, x)], alpha=.3
                )
            else:
                tile = patches.Rectangle(
                    (x_tiles[x], y_tiles[y]), TILESIZE, TILESIZE,
                    fill=True, color='#ffffff'
                )
            if (y, x) in grid.labels:
                ax.text(
                    x_tiles[x] + TILESIZE * 0.5, y_tiles[y] + TILESIZE * 0.5,
                    r'$' + grid.labels[(y, x)] + '$', fontsize=25, rotation=0,
                    horizontalalignment='center', verticalalignment='center',
                    rotation_mode='anchor'
                )
            road_tiles.append(tile)

    ax.add_collection(PatchCollection(road_tiles, match_original=True))
    # Add grid lines
    for y in y_tiles:
        plt.plot([x_tiles[0], x_tiles[-1]], [y, y], color='black', alpha=.33)
    for x in x_tiles:
        plt.plot([x, x], [y_tiles[0], y_tiles[-1]], color='black', alpha=.33)

    # Add cuts
    width = TILESIZE / 20
    cut_tiles = []
    for cut in grid.cuts:
        startxy = cut[0]
        endxy = cut[1]
        delx = startxy[0] - endxy[0]
        dely = startxy[1] - endxy[1]
        if delx == 0:
            if dely < 0:
                tile = patches.Rectangle(
                    (
                        startxy[1] * TILESIZE - width / 2 - dely * TILESIZE,
                        startxy[0] * TILESIZE - width / 2
                    ), width, TILESIZE + width,
                    fill=True, color='black', alpha=1.0
                )
            else:
                tile = patches.Rectangle(
                    (
                        startxy[1] * TILESIZE - width / 2,
                        startxy[0] * TILESIZE - width / 2
                    ), width, TILESIZE + width, fill=True, color='black', alpha=1.0
                )
        elif dely == 0:
            if delx < 0:
                tile = patches.Rectangle(
                    (
                        startxy[1] * TILESIZE - width / 2,
                        startxy[0] * TILESIZE - width / 2 - delx * TILESIZE
                    ), TILESIZE + width, width, fill=True, color='black', alpha=1.0
                )
            else:
                tile = patches.Rectangle(
                    (
                        startxy[1] * TILESIZE - width / 2,
                        startxy[0] * TILESIZE - width / 2
                    ), TILESIZE + width, width, fill=True, color='black', alpha=1.0
                )
        cut_tiles.append(tile)

    ax.add_collection(PatchCollection(cut_tiles, match_original=True))
    plt.gca().invert_yaxis()


def draw_timestamp(t):
    ax.text(
        0.3, 0.7, t, transform=plt.gcf().transFigure, fontsize='large',
        bbox={"boxstyle": "circle", "color": "white", "ec": "black"}
    )


def draw_sys(sys_data, theta_d):
    y_tile = sys_data[1]
    x_tile = sys_data[0]
    x = (x_tile) * TILESIZE
    z = (y_tile) * TILESIZE
    robo_fig = Image.open(robo_figure)
    robo_fig = ImageOps.flip(robo_fig)
    robo_fig = robo_fig.rotate(theta_d, expand=False)
    ax.imshow(
        robo_fig, zorder=1, interpolation='bilinear',
        extent=[z + 5, z + TILESIZE - 5, x, x + TILESIZE]
    )


def draw_test(test_data, theta_d):
    y_tile = test_data[1]
    x_tile = test_data[0]
    x = (x_tile) * TILESIZE
    z = (y_tile) * TILESIZE
    robo_fig = Image.open(robo_figure)
    robo_fig = ImageOps.flip(robo_fig)
    robo_fig = robo_fig.rotate(theta_d, expand=False)
    background = patches.Circle(
        (z + TILESIZE / 2, x + TILESIZE / 2),
        (TILESIZE - 10) / 2,
        linewidth=1, facecolor='blue'
    )
    ax.add_artist(background)
    ax.imshow(
        robo_fig, zorder=1, interpolation='bilinear',
        extent=[z + 10, z + TILESIZE - 10, x + 5, x + TILESIZE - 5]
    )


def animate_images(output_dir):
    # Create the frames
    frames = []
    imgs = glob.glob(output_dir + 'plot_'"*.png")
    imgs.sort()
    for i in imgs:
        new_frame = Image.open(i)
        frames.append(new_frame)

    # Save into a GIF file that loops forever
    frames[0].save(
        output_dir + 'png_to_gif.gif', format='GIF',
        append_images=frames[1:],
        save_all=True,
        duration=200, loop=3
    )


def traces_to_animation(filename, output_dir):
    # extract out traces from pickle file
    with open(filename, 'rb') as pckl_file:
        traces = pickle.load(pckl_file)
    # t_start = 0
    t_end = len(traces)
    # grid = traces[0].grid
    # packagelocs = traces[0].snapshot['packagelocs']
    global ax
    fig, ax = plt.subplots()
    t_array = np.arange(t_end)
    # plot the same map
    for t in t_array:
        plt.gca().cla()
        sys_data = traces[t].snapshot['sys']
        # packagelocs = traces[t].snapshot['packagelocs']
        draw_grid(traces[t].grid)
        theta_d = 0
        draw_sys(sys_data, theta_d)
        # if traces[t].snapshot['test']:
        #     test_data = traces[t].snapshot['test']
        #     draw_test(test_data, theta_d)
        plot_name = str(t).zfill(5)
        img_name = output_dir + '/plot_' + plot_name + '.png'
        fig.savefig(img_name, dpi=1200)
    animate_images(output_dir)


def make_animation():
    output_dir = os.getcwd() + '/animations/gifs/'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    traces_file = os.getcwd() + '/saved_traces/sim_trace.p'
    traces_to_animation(traces_file, output_dir)


if __name__ == '__main__':
    make_animation()
