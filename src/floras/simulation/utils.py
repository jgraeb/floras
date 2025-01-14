import _pickle as pickle
import os


class Scene:
    def __init__(self, timestamp, grid, snapshot):
        self.grid = grid
        self.timestamp = timestamp
        self.snapshot = snapshot


def save_trace(filename, trace):  # save the trace in pickle file for animation
    print('Saving trace in pkl file')
    with open(filename, 'wb') as pckl_file:
        pickle.dump(trace, pckl_file)


def save_scene(game, trace):  # save each scene in trace
    print('Saving scene {}'.format(game.timestep))
    snapshot = {'sys': game.agent.s}
    current_scene = Scene(game.timestep, game.grid, snapshot)
    trace.append(current_scene)
    game.timestep += 1
    game.trace = trace
    return trace


def load_opt_from_pkl_file():
    ''' Load the stored optimization result.
    '''
    opt_file = os.getcwd()+'/stored_optimization_result.p'
    with open(opt_file, 'rb') as pckl_file:
        opt_dict = pickle.load(pckl_file)
    return opt_dict
