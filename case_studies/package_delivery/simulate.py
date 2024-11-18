""" Simulated package delivery robot in the static test environment found by package_delivery.py."""
# import sys
# sys.path.append('../..')
import os
import _pickle as pickle
import logging
import networkx as nx
from ipdb import set_trace as st

from floras.components.plotting import Grid
from floras.simulation.agents import Agent
from floras.simulation.game import Game
from floras.simulation.utils import load_opt_from_pkl_file, save_scene, save_trace

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
            if out_pos != in_pos:
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
        return output

def run_sim(gridfile, max_timestep, filepath):
    '''
    Run the simulation.
    '''
    trace=[]

    # load the opt results from pkl file
    opt = load_opt_from_pkl_file()
    cuts = opt['cuts']

    # set up the simulation
    grid = Grid(gridfile)
    sys = Agent('sys', (0,0), [], grid)
    # get the controller and save it to the system
    # get virtual sys from pickle file
    graph_file = os.getcwd()+'/virtual_sys.p'
    with open(graph_file, 'rb') as pckl_file:
        virtual_sys_dict = pickle.load(pckl_file)

    controller = ShortestPathController(virtual_sys_dict, cuts)
    sys.save_controller(controller)

    game = Game(grid, sys)
    trace = save_scene(game,trace)
    game.print_game_state()
    for t in range(1,max_timestep):
        print('Timestep {}'.format(t))
        game.agent_take_step()
        game.print_game_state()
        # save the trace
        trace = save_scene(game,trace)
        if game.is_terminal():
            break
    save_trace(filepath, game.trace)


if __name__ == '__main__':
    max_timestep = 100
    output_dir = os.getcwd()+'/saved_traces/'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    filename = 'sim_trace.p'
    filepath = output_dir + filename

    gridfile = 'grid.txt'
    run_sim(gridfile, max_timestep, filepath)