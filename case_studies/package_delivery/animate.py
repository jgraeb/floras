'''
Animate.
'''
import os
import numpy as np
import _pickle as pickle
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.collections import PatchCollection
from PIL import Image, ImageOps
from floras.simulation.animation import animate_images

TILESIZE = 50

main_dir = os.path.dirname(os.path.dirname(os.path.realpath("__file__")))
robo_figure = main_dir + '/imglib/robot.png'

def draw_packages(grid, packagelocs):
    packages = []
    for p in packagelocs:
        ((y,x),color) = packagelocs[p]
        tile = patches.Rectangle((x*TILESIZE+TILESIZE/4, y*TILESIZE+TILESIZE/4), TILESIZE/2, TILESIZE/2, fill=True, facecolor=color, edgecolor='black', alpha=1.0)
        ax.text(x*TILESIZE+TILESIZE/2, y*TILESIZE+TILESIZE/2, r'$p_'+p[1:]+'$', fontsize = 10, rotation=0, horizontalalignment='center', verticalalignment='center', rotation_mode='anchor')
        packages.append(tile)
    ax.add_collection(PatchCollection(packages, match_original=True)) 

def draw_sys(sys_data, theta_d, merge = False):
    y_tile = sys_data[1]
    x_tile = sys_data[0]
    x = (x_tile) * TILESIZE
    z = (y_tile) * TILESIZE
    robo_fig = Image.open(robo_figure)
    robo_fig = ImageOps.flip(robo_fig)
    robo_fig = robo_fig.rotate(theta_d, expand=False)
    offset = 0.1
    ax.imshow(robo_fig, zorder=1, interpolation='bilinear', extent=[z+5, z+TILESIZE-5, x, x+TILESIZE])

def draw_grid(grid):
    map = grid.map
    size = max(map.keys())
    z_min = 0
    z_max = (size[0]+1) * TILESIZE
    x_min = 0
    x_max = (size[1]+1) * TILESIZE
    ax.set_xlim(x_min, x_max)
    ax.set_ylim(z_min, z_max)
    ax.xaxis.set_visible(False)
    ax.yaxis.set_visible(False)
    # fill in the road regions
    road_tiles = []
    x_tiles = np.arange(0,size[1]+2)*TILESIZE
    y_tiles = np.arange(0,size[0]+2)*TILESIZE
        
    for y in np.arange(0,size[0]+1):
        for x in np.arange(0,size[1]+1):
            if map[(y,x)]=='*':
                tile = patches.Rectangle((x_tiles[x], y_tiles[y]), TILESIZE, TILESIZE, fill=True, color='black', alpha=.5)
            elif (y,x) in grid.colors:
                if grid.labels[(y,x)][0] == 'p':
                    shade = 0.0
                else:
                    shade = 0.2
                tile = patches.Rectangle((x_tiles[x], y_tiles[y]), TILESIZE, TILESIZE, fill=True, color=grid.colors[(y,x)], alpha=shade)
            else:
                tile = patches.Rectangle((x_tiles[x], y_tiles[y]), TILESIZE, TILESIZE, fill=True, color='#ffffff')
            road_tiles.append(tile)

    ax.add_collection(PatchCollection(road_tiles, match_original=True))
    # Add grid lines
    for y in y_tiles:
        plt.plot([x_tiles[0], x_tiles[-1]], [y,y], color='black', alpha=.33)
    for x in x_tiles:
        plt.plot([x, x],[y_tiles[0], y_tiles[-1]], color='black', alpha=.33)

    # Add cuts
    width = TILESIZE/20
    cut_tiles = []
    for cut in grid.cuts:
        startxy = cut[0]
        endxy = cut[1]
        delx = startxy[0] - endxy[0]
        dely = startxy[1] - endxy[1]
        if delx == 0:
            if dely < 0:
                tile = patches.Rectangle((startxy[1]*TILESIZE- width/2 - dely*TILESIZE , startxy[0]*TILESIZE - width/2), width, TILESIZE+width, fill=True, color='black', alpha=1.0)
            else:
                tile = patches.Rectangle((startxy[1]*TILESIZE- width/2 , startxy[0]*TILESIZE- width/2), width, TILESIZE+width, fill=True, color='black', alpha=1.0)
        elif dely == 0:
            if delx < 0:
                tile = patches.Rectangle((startxy[1]*TILESIZE- width/2, startxy[0]*TILESIZE- width/2 - delx*TILESIZE), TILESIZE+width, width, fill=True, color='black', alpha=1.0)
            else:
                tile = patches.Rectangle((startxy[1]*TILESIZE- width/2, startxy[0]*TILESIZE- width/2), TILESIZE + width, width, fill=True, color='black', alpha=1.0)
        cut_tiles.append(tile)

    ax.add_collection(PatchCollection(cut_tiles, match_original=True))    
    plt.gca().invert_yaxis()

def make_animation():
    output_dir = os.getcwd()+'/animations/gifs/'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    traces_file = os.getcwd()+'/saved_traces/sim_trace.p'
    traces_to_animation(traces_file, output_dir)

def traces_to_animation(filename, output_dir):
    # extract out traces from pickle file
    with open(filename, 'rb') as pckl_file:
        traces = pickle.load(pckl_file)
    t_start = 0
    t_end = len(traces)
    grid = traces[0].grid
    # packagelocs = traces[0].snapshot['packagelocs']
    global ax
    fig, ax = plt.subplots()
    t_array = np.arange(t_end)
    # plot the same map
    for t in t_array:
        plt.gca().cla()
        sys_data = traces[t].snapshot['sys']
        packagelocs = traces[t].snapshot['packagelocs']
        draw_grid(traces[t].grid)
        theta_d = 0
        draw_sys(sys_data, theta_d)
        draw_packages(grid, packagelocs)
        plot_name = str(t).zfill(5)
        img_name = output_dir+'/plot_'+plot_name+'.png'
        fig.savefig(img_name, dpi=1200)
    animate_images(output_dir)

if __name__ == '__main__':
    make_animation()