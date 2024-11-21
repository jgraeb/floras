''' 
The Game class for simulation - consisting of the grid world layout and the system
No dynamic tester or reactive obstacles in this implementation
'''

from ipdb import set_trace as st
from copy import deepcopy
import random
import _pickle as pickle
from floras.simulation.utils import load_opt_from_pkl_file

class Game:
    def __init__(self, grid, sys):
        self.grid = deepcopy(grid)
        self.agent = sys
        self.timestep = 0
        self.trace = []
        self.setup()

    def get_optimization_results(self):
    # Read pickle file - if not there solve optimization and save.
        try:
            print('Checking for the optimization results')
            cuts = load_opt_from_pkl_file()
            print('Optimization results loaded successfully')
        except:
            print('Result file not found, need to run the optimization first')
            # st()
        return cuts

    def setup(self):
        opt_res = self.get_optimization_results()
        self.grid.add_cuts(opt_res['cuts'])
        if not self.agent.controller: # check if agent controller already exists
            self.agent.find_controller(self.grid)

    def print_game_state(self):
        z_old = []
        printline = ""
        for key in self.grid.map:
            z_new = key[0]
            if self.agent.s == key:
                add_str = 'S'
            else:
                add_str = self.grid.map[key]
            if z_new == z_old:
                printline += add_str
            else:
                print(printline)
                printline = add_str
            z_old = z_new
        print(printline)
        printline = self.grid.map[key]

    def agent_take_step(self):
        self.agent.move()

    def is_terminal(self):
        terminal = False
        if self.agent.isterminal:
            terminal = True
        return terminal