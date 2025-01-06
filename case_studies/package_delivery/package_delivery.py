"""Package delivery robot case study."""

import sys
sys.path.append('../../')
import os
import _pickle as pickle
from ipdb import set_trace as st
import time

from floras.components.transition_system import TransitionSystemInput, TranSys
from floras.components.grid import Grid
from floras.components.plotting import plot_grid
from floras.components.automata import get_system_automaton, get_tester_automaton, get_product_automaton
from floras.components.product import sync_prod
from floras.optimization.optimize import solve

def istarget(target, state):
    if state[0]==target and state[1]=='Idle':
        if all(item == 1 for item in state[2:]):
            return True
    return False

def update_load(cur_p, cur_delivery, pos_p):
    newp = cur_p
    if cur_p == 'Idle': # pick it up
        if cur_delivery[int(pos_p[1:])-1] == 0: # if not delivered yet
            newp = pos_p
    elif cur_p == pos_p: # drop it off
        newp = 'Idle'
    return newp

def update_delivery_status(cur_p, cur_delivery):
    new_delivery = [1 if (i + 1) == int(cur_p[1:]) else k for i, k in enumerate(cur_delivery)]
    newp = 'Idle'
    return newp, new_delivery

def build_transition_system_automatic(grid, packagelocs, packagegoals, target, initpos):
    '''
    Build the states and transitions for multiple agents in a grid world, with states
    where packages can be picked up and dropped off.
    '''
    map = grid.map
    num_packages = len(packagelocs)

    # get all possible robot positions
    possible_states = []
    for state in map:
        if map[state] !='*':
            possible_states.append(state)
    rmoves = [(0,0),(-1,0),(1,0), (0,-1), (0,1)] # robot can always move horizontally or vertically

    # build up the states and transitions
    initstate = (initpos, 'Idle') + tuple([0 for item in range(0, num_packages)]) # does the robot have a package loaded - Idle is No package
    transitions_dict = dict()
    states_list = []

    # get all transitions
    goals = []
    states_list = []
    states_to_add = [initstate]
    while len(states_to_add) > 0:
        new_states = []
        for state in states_to_add:
            # state = (r,p,deliveries...)
            r = state[0] # robot position
            p = state[1] # robot load
            delivery_tracker = state[2:] # package delivery status
            next_states = [state] # always can stay the same
            # if goal is reached stop moving
            if istarget(target, state):
                goals.append(state)
            else:
                # or move
                for rmove in rmoves: # robot moves
                    newr = (r[0]+rmove[0],r[1]+rmove[1])
                    if newr in possible_states: # if the move is not out of bounds
                        # if nothing updates,p, d1, and d2 stay the same
                        newp = p
                        newdelivery = delivery_tracker
                        valid = True
                        if newr in packagelocs: # pick up package
                            # st()
                            pos_p = packagelocs[newr]
                            if p == 'Idle':
                                newp = update_load(p, delivery_tracker, pos_p) # update loaded package status
                            elif p == pos_p:
                                newp = update_load(p, delivery_tracker, pos_p) # update loaded package status
                            elif delivery_tracker[int(pos_p[1:])-1] == 0:
                                valid = False
                        elif newr in packagegoals and p == packagegoals[newr]: # drop off package
                            # update loaded package and delivery tracker
                            newp, newdelivery = update_delivery_status(p, delivery_tracker)
                        newstate = (newr,newp)+tuple(newdelivery)
                        if valid:
                            if newstate not in next_states:
                                next_states.append(newstate)
                                if newstate not in states_list:
                                    new_states.append(newstate)
                                    states_list.append(newstate)
            # update transition dict for that state
            transitions_dict.update({state: next_states})
        states_to_add = new_states

    # setting the labels
    packagegoals_rev = {packagegoals[key]: key for key in packagegoals.keys()}
    labels_dict = {p: ['goal'] for p in set(goals)}
    for key,val in packagegoals_rev.items():
        i = int(key[1:])-1
        states = [(val, 'Idle') + tuple([0 for k in range(0, i)])+  tuple([1 for k in range(i, num_packages)])]
        labels_dict.update({s: [key+'d'] for s in states})

    init_list = [initstate]
    custom_map = {state: state[0] for state in states_list}

    transition_system_input = TransitionSystemInput(states_list, transitions_dict, labels_dict, init_list, custom_map)
    return transition_system_input

def run_example():
    plot_graphs = False # False is recommended for large problems
    save_sys = False

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

    # set the colors for plotting
    package_colors = ['cornflowerblue', 'green', 'yellow', 'red', 'cyan']
    color_dict = {key: package_colors[int(packagelocs[key][1:])-1] for key in packagelocs.keys()}
    color_dict |= {key: package_colors[int(packagegoals[key][1:])-1] for key in packagegoals.keys()}
    color_dict |= {target: '#ffb000'}
    color_dict |= {initpos: '#d02670'}

    # define the grid and plot the layout
    grid = Grid('grid.txt', labels_dict, color_dict)
    if not os.path.exists('imgs'):
        os.makedirs('imgs')
    plot_grid(grid, 'imgs/layout')

    transition_system_input = build_transition_system_automatic(grid, packagelocs, packagegoals, target, initpos)

    sys_formula = 'F(goal)'
    test_formula = 'F(p5d & F(p4d & F(p3d & F(p2d & F(p1d)))))'

    # get automata
    sys_aut, spot_aut_sys = get_system_automaton(sys_formula)
    test_aut, spot_aut_test = get_tester_automaton(test_formula)
    prod_aut = get_product_automaton(spot_aut_sys, spot_aut_test)

    print("==========================")
    print(f"System objective: {sys_formula}")
    print(f"Test objective: {test_formula}")
    print("==========================")
    print("Sizes of the automata/graphs:")
    print(f"B_sys: ({len(sys_aut.Q), len(sys_aut.delta)})")
    print(f"B_test: ({len(test_aut.Q), len(test_aut.delta)})")
    print(f"A_pi: ({len(prod_aut.Q), len(prod_aut.delta)})")

    # get transition system
    transys = TranSys(transition_system_input)
    print(f"T: ({len(transys.S), len(transys.E)})")

    if save_sys:
        # finding virtual sys (for system controller)
        t0 = time.time()
        virtual_sys = sync_prod(transys, sys_aut)
        tf = time.time()
        Gsys_runtime = tf-t0
        print(f"Gsys: ({len(virtual_sys.S), len(virtual_sys.E)}) --- runtime {Gsys_runtime} s")
        # Pickle the graph to a file
        virtual_sys_dict = {'nodes': virtual_sys.S, 'edges': virtual_sys.E, 'goals': virtual_sys.sink, 'init': virtual_sys.src}
        with open("virtual_sys.p", "wb") as f:
            pickle.dump(virtual_sys_dict, f)
    else:
        virtual_sys = None
        print("G_sys: skipped")

    # get virtual graphs
    t0 = time.time()
    virtual = sync_prod(transys, prod_aut)
    tf = time.time()
    G_runtime = tf-t0
    print(f"G: ({len(virtual.S), len(virtual.E)}) --- runtime {G_runtime} s")
    
    if virtual.int == []:
        print('Unrealizable - No intermediate nodes on the graph!')

    print("==========================")

    if plot_graphs:
        sys_aut.save_plot('sys')
        test_aut.save_plot('test')
        prod_aut.save_plot('prod')
        transys.save_plot('ts')
        virtual.save_plot('virtual')
        if virtual_sys:
            virtual_sys.save_plot('virtual_sys')

    d, flow = solve(virtual, transys, prod_aut, virtual_sys, case = 'static', plot_results = False, callback = None)


    cuts = [(cut[0][0][0],cut[1][0][0]) for cut in d.keys()]
    print("==========================")
    print(f"Number of cuts on G: {len(cuts)}")
    print(f"Number of cuts on T: {len(list(set(cuts)))}")
    print("==========================")
    cut_dict = {'cuts': cuts, 'd': d, 'flow': flow}
    with open('stored_optimization_result.p', 'wb') as pkl_file:
        pickle.dump(cut_dict, pkl_file)

    plot_grid(grid, 'imgs/result', list(set(cuts)))

if __name__=='__main__':
    run_example()
