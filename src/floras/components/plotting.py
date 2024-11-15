import sys
sys.path.append('..')
import numpy as np
from ipdb import set_trace as st
import os
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Wedge
import networkx as nx
# import datetime

class Grid():
    def __init__(self,file, labels_dict = []):
        self.labels = labels_dict
        self.map, self.len_y, self.len_x = self.get_map(file)

    def get_map(self, file):
        map = {}
        f = open(file, 'r')
        lines = f.readlines()
        len_z = len(lines)
        for i,line in enumerate(lines):
            for j,item in enumerate(line):
                if item != '\n' and item != '|':
                    map.update({(i,j): item})
                    len_x = j
        len_x += 1
        return map, len_z, len_x

def plot_grid(grid, filename, cuts = []):
    tilesize = 1
    xs = np.linspace(0, grid.len_x*tilesize, grid.len_x+1)
    ys = np.linspace(0, grid.len_y*tilesize, grid.len_y+1)

    fig, ax = plt.subplots()

    ax.xaxis.set_visible(False)
    ax.yaxis.set_visible(False)
    w, h = xs[1] - xs[0], ys[1] - ys[0]
    for i, x in enumerate(xs[:-1]):
        for j, y in enumerate(ys[:-1]):
            if grid.map[j,i]=='*':
                ax.add_patch(Rectangle((x, y), w, h, fill=True, color='black', alpha=.5))
            elif (j,i) in grid.labels:
                if grid.labels[(j,i)] == 'T':
                    ax.add_patch(Rectangle((x, y), w, h, fill=True, color='#ffb000', alpha=.3))
                    ax.text(x+tilesize*0.5, y+tilesize*0.5, r'$T$', fontsize = 25, rotation=0, horizontalalignment='center', verticalalignment='center', rotation_mode='anchor')
                elif grid.labels[(j,i)] == 'S':
                    ax.text(x+tilesize*0.5, y+tilesize*0.5, r'$S$', fontsize = 25, rotation=0, horizontalalignment='center', verticalalignment='center', rotation_mode='anchor')
                else:
                    ax.add_patch(Rectangle((x, y), w, h, fill=True, color='#648fff', alpha=.3))
                    ax.text(x+tilesize*0.5, y+tilesize*0.5, r'$'+grid.labels[(j,i)]+'$', fontsize = 25, rotation=0, horizontalalignment='center', verticalalignment='center', rotation_mode='anchor')
            else:
                ax.add_patch(Rectangle((x, y), w, h, fill=True, color='#ffffff'))

    # grid lines
    for x in xs:
        ax.plot([x, x], [ys[0], ys[-1]], color='black', alpha=.33)
    for y in ys:
        ax.plot([xs[0], xs[-1]], [y, y], color='black', alpha=.33)

    width = tilesize/20

    for cut in cuts:
        startxy = cut[0]
        endxy = cut[1]
        delx = startxy[0] - endxy[0]
        dely = startxy[1] - endxy[1]
        if delx == 0:
            if dely < 0:
                ax.add_patch(Rectangle((startxy[1]- width/2 - dely*tilesize , startxy[0] - width/2), width, tilesize+width, fill=True, color='black', alpha=1.0))
            else:
                ax.add_patch(Rectangle((startxy[1]- width/2 , startxy[0]- width/2), width, tilesize+width, fill=True, color='black', alpha=1.0))
        elif dely == 0:
            if delx < 0:
                ax.add_patch(Rectangle((startxy[1]- width/2, startxy[0]- width/2 - delx*tilesize), tilesize+width, width, fill=True, color='black', alpha=1.0))
            else:
                ax.add_patch(Rectangle((startxy[1]- width/2, startxy[0]- width/2), tilesize + width, width, fill=True, color='black', alpha=1.0))


    ax.invert_yaxis()
    ax.axis('equal')
    plt.show()
    fig.savefig(filename + '.pdf')