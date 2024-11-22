""" Simulated package delivery robot in the static test environment found by package_delivery.py."""
# import sys
# sys.path.append('../..')
import os
import _pickle as pickle
import logging
import networkx as nx
from ipdb import set_trace as st
from copy import deepcopy

from floras.components.grid import Grid
from floras.simulation.agents import Agent
from floras.simulation.game import Game
from floras.simulation.utils import load_opt_from_pkl_file, save_trace, Scene

class ShortestPathController():
    def __init__(self, virtual_sys_dict, cuts):
        self.nodes = virtual_sys_dict['nodes']
        self.edges = virtual_sys_dict['edges']
        self.cuts = cuts
        self.current_node = virtual_sys_dict['init'][0]
        self.goal_nodes = virtual_sys_dict['goals']
        self.graph = self.update_graph()
        self.path = self._find_path_to_nearest_goal()
        self.path_index = 0  # Tracks the current step in the path
        self.isterminal = False

    def update_graph(self):
        # remove the cut edges from the graph
        G = nx.DiGraph()
        G.add_nodes_from(self.nodes)
        for transition in self.edges:
            out_pos = transition[0][0][0]
            in_pos = self.edges[transition][0][0]
            # if out_pos != in_pos:
            if (out_pos, in_pos) not in self.cuts:
                G.add_edge(transition[0], self.edges[transition])
        return G
    
    def _find_path_to_nearest_goal(self):
        """
        Find the shortest path to the nearest goal node.
        Returns the path as a list of nodes.
        """
        shortest_path = None
        shortest_length = float('inf')
        for goal in self.goal_nodes:
            try:
                path = nx.shortest_path(self.graph, source=self.current_node, target=goal)
                if len(path) < shortest_length:
                    shortest_path = path
                    shortest_length = len(path)
            except nx.NetworkXNoPath:
                # Skip if no path exists to this goal
                continue
        if shortest_path is None:
            raise ValueError("No path to any goal node exists.")
        return shortest_path

    def move(self):
        """
        Move to the next node in the path.
        Returns the next node or a message if the goal is reached.
        """
        output = dict()
        if self.path_index < len(self.path) - 1:
            self.path_index += 1
            self.current_node = self.path[self.path_index]
        else:
            self.isterminal = True

        output = {'y': self.current_node[0][0][0], 'x': self.current_node[0][0][1]}
        # print(f'sys moving to {self.current_node}')
        return output
    
def update_package_locs(current_node, packageloc_dict, packagegoals):
    '''
    Update package location on the grid depending on delivery status and loading status.
    '''
    cur_pos = current_node[0][0]
    loading_status = current_node[0][1]
    delivery_status = current_node[0][2:]
    for key,val in packageloc_dict.items():
        idx = int(key[1:])
        if delivery_status[idx-1] == 1: 
            packageloc_dict.update({key: ((packagegoals[key]), val[-1])}) # keep the color
        elif loading_status == key:
            packageloc_dict.update({key: ((cur_pos), val[-1])}) # keep the color
    return packageloc_dict

def run_sim(gridfile, max_timestep, filepath):
    '''
    Run the simulation.
    '''
    # define locations of interest
    packagelocs = {(2,2): 'p1', (2,4): 'p2', (2,6): 'p3', (2,8): 'p4', (2,10): 'p5'}
    packagegoals = {(0,5): 'p1', (0,7): 'p2', (4,9): 'p3', (0,12): 'p4', (3,12): 'p5'}
    target = (3,0)
    initpos = (0,0)

    # set the labels
    labels_dict = {initpos: 'S', target: 'T'}
    for loc in packagelocs.keys():
        labels_dict.update({loc : 'p_'+str(packagelocs[loc][1:])})
    for goal in packagegoals.keys():
        labels_dict.update({goal : 'd_'+str(packagegoals[goal][1:])})

    package_colors = ['cornflowerblue', 'green', 'yellow', 'red', 'cyan']
    color_dict = {key: package_colors[int(packagelocs[key][1:])-1] for key in packagelocs.keys()}
    color_dict |= {key: package_colors[int(packagegoals[key][1:])-1] for key in packagegoals.keys()}
    color_dict |= {target: '#ffb000'}
    color_dict |= {initpos: '#d02670'}

    trace=[]

    # load the opt results from pkl file
    opt = load_opt_from_pkl_file()
    cuts = opt['cuts']

    # set up the simulation
    grid = Grid(gridfile, labels_dict, color_dict)
    sys = Agent('sys', (0,0), [], grid)
    # get the controller and save it to the system
    # get virtual sys from pickle file
    graph_file = os.getcwd()+'/virtual_sys.p'
    with open(graph_file, 'rb') as pckl_file:
        virtual_sys_dict = pickle.load(pckl_file)

    controller = ShortestPathController(virtual_sys_dict, cuts)
    sys.save_controller(controller)

    game = Game(grid, sys)
    packageloc_dict = {packagelocs[key]: (key, package_colors[int(packagelocs[key][1:])-1]) for key in packagelocs.keys()}
    packagegoals_dict = {packagegoals[key]: (key) for key in packagegoals.keys()}
    
    trace = save_scene(game,trace, packageloc_dict)
    game.print_game_state()
    for t in range(1,max_timestep):
        print('Timestep {}'.format(t))
        game.agent_take_step()
        packageloc_dict = update_package_locs(game.agent.controller.current_node, packageloc_dict, packagegoals_dict)
        game.print_game_state()
        # save the trace
        trace = save_scene(game,trace, packageloc_dict)
        if game.is_terminal():
            break
    save_trace(filepath, game.trace)

def save_scene(game, trace, packageloc_dict): # save each scene in trace
    print('Saving scene {}'.format(game.timestep))
    snapshot = {'sys': game.agent.s, 'packagelocs': deepcopy(packageloc_dict)}
    current_scene = Scene(game.timestep, game.grid, snapshot)
    trace.append(current_scene)
    game.timestep += 1
    game.trace = trace
    return trace

if __name__ == '__main__':
    max_timestep = 100
    output_dir = os.getcwd()+'/saved_traces/'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    filename = 'sim_trace.p'
    filepath = output_dir + filename

    gridfile = 'grid.txt'
    run_sim(gridfile, max_timestep, filepath)