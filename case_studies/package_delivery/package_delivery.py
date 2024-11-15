"""Robot relay case study."""

import sys
sys.path.append('../../')
import os
from floras.components.automata import get_system_automaton, get_tester_automaton, get_product_automaton
from floras.components.transition_system import TransitionSystemInput, TranSys
from floras.components.plotting import Grid, plot_grid
from floras.components.product import sync_prod
from floras.optimization.optimize import solve

from ipdb import set_trace as st


def istarget(target, state): # for one package
    if state[0]==target and state[1]=='Idle':
        if all(item == 1 for item in state[2:]):
            return True
    return False


def build_transition_system(grid):
    '''
    Build the states and transitions for multiple agents in a grid world, with states
    where packages can be picked up and dropped off.
    Simple 5x10 grid for now.

    '''
    map = grid.map

    num_packages = 2
    pkgs = ['p'+str(k+1) for k in range(num_packages)]
    packagelocs = {(1,0): 'p1', (2,0): 'p2'}
    packagegoals = {(4,1): 'p1', (4,0): 'p2'}
    target = (2,1)
    initpos = (0,0)
    possible_states = []
    for state in map:
        if map[state] !='*':
            possible_states.append(state)

    rmoves = [(0,0),(-1,0),(1,0), (0,-1), (0,1)] # robot can always move horizontally or vertically

    # build up the states and transitions
    initstate = (initpos, 'Idle', 0, 0) # does the robot have a package loaded - Idle is No package
    transitions_dict = dict()
    states_list = []

    # get all transitions
    goals = []
    states_list = []
    states_to_add = [initstate]
    while len(states_to_add) > 0:
        new_states = []
        for (r,p,d1, d2) in states_to_add:
            state = (r,p,d1, d2)
            states_list.append(state)
            next_states = [state] # always can stay the same
            # if goal is reached stop moving
            if istarget(target, state): # update for more packages
                goals.append(state)
            else:
                # or move
                for rmove in rmoves: # robot moves
                    newr = (r[0]+rmove[0],r[1]+rmove[1])
                    # if nothing updates,p, d1, and d2 stay the same
                    newp = p
                    newd1 = d1
                    newd2 = d2
                    if newr in packagelocs:
                        if p == 'Idle' and packagelocs[newr] == 'p1' and d1 == 0:
                            newp = packagelocs[newr]
                        elif p == 'Idle' and packagelocs[newr] == 'p2' and d2 == 0:
                            newp = packagelocs[newr]
                        elif p == 'p1' and packagelocs[newr] == 'p1':
                            newp == 'Idle'
                        elif p == 'p2' and packagelocs[newr] == 'p2':
                            newp == 'Idle'
                    elif newr in packagegoals and p == packagegoals[newr]:
                        newp = 'Idle'
                        if p == 'p1':
                            newd1 = 1
                        if p == 'p2':
                            newd2 = 1
                    if newr in possible_states:
                        if (newr,newp,newd1,newd2) not in next_states:
                            next_states.append((newr,newp,newd1,newd2))
                            if (newr,newp,newd1,newd2) not in states_list:
                                new_states.append((newr,newp,newd1,newd2))
            # update transition dict for that state
            transitions_dict.update({state: next_states})
        states_to_add = new_states
    st()

    p1droppedoff = [((2,0), 'Idle', 1, k) for k in [0,1]]
    p2droppedoff = [((4,0), 'Idle', k, 1) for k in [0,1]]

    labels_dict = {p: ['goal'] for p in set(goals)}
    # labels_dict.update({intt: ['int'] for intt in ints})
    labels_dict.update({p1d: ['p1d'] for p1d in p1droppedoff})
    labels_dict.update({p2d: ['p2d'] for p2d in p2droppedoff})
    init_list = [initstate]

    custom_map = {state: state[0] for state in states_list}

    transition_system_input = TransitionSystemInput(states_list, transitions_dict, labels_dict, init_list, custom_map)
    return transition_system_input

def update_load(cur_p, cur_delivery, pos_p):
    newp = cur_p
    if cur_p == 'Idle': # pick it up
        if cur_delivery[int(pos_p[1:])-1] == 0: # if not delivered yet
            newp = pos_p
    elif cur_p == pos_p: # drop it off
        # drop it off
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
    Simple 5x10 grid for now.

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
            # states_list.append(state)
            next_states = [state] # always can stay the same
            # if goal is reached stop moving
            if istarget(target, state): # update for more packages
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
                        if newr in packagelocs and newr != r: # pick up package
                            # st()
                            pos_p = packagelocs[newr]
                            if p == 'Idle' or p == pos_p or delivery_tracker[int(pos_p[1:])-1] == 1: # current load or already delivered
                                newp = update_load(p, delivery_tracker, pos_p) # update loaded package status
                            else:
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

    packagegoals_rev = {packagegoals[key]: key for key in packagegoals.keys()}

    p1droppedoff = [(packagegoals_rev['p1'], 'Idle', 1, 1, 1, 1, 1)]# for k in [0,1]]
    p2droppedoff = [(packagegoals_rev['p2'], 'Idle', 0, 1, 1, 1, 1)]# for k in [0,1]]
    p3droppedoff = [(packagegoals_rev['p3'], 'Idle', 0, 0, 1, 1, 1)]#for k in [0,1] for j in [0,1]]
    p4droppedoff = [(packagegoals_rev['p4'], 'Idle', 0, 0, 0, 1, 1)]
    p5droppedoff = [(packagegoals_rev['p5'], 'Idle', 0, 0, 0, 0, 1)]

    labels_dict = {p: ['goal'] for p in set(goals)}
    labels_dict.update({p1d: ['p1d'] for p1d in p1droppedoff})
    labels_dict.update({p2d: ['p2d'] for p2d in p2droppedoff})
    labels_dict.update({p3d: ['p3d'] for p3d in p3droppedoff})
    labels_dict.update({p4d: ['p4d'] for p4d in p4droppedoff})
    labels_dict.update({p5d: ['p5d'] for p5d in p5droppedoff})
    # labels_dict.update({p6d: ['p6d'] for p6d in p6droppedoff})
    init_list = [initstate]

    custom_map = {state: state[0] for state in states_list}

    transition_system_input = TransitionSystemInput(states_list, transitions_dict, labels_dict, init_list, custom_map)
    return transition_system_input

def run_example():
    plot_graphs = False

    packagelocs = {(2,2): 'p1', (2,4): 'p2', (2,6): 'p3', (2,8): 'p4', (2,10): 'p5'}
    packagegoals = {(0,5): 'p1', (0,7): 'p2', (4,9): 'p3', (0,12): 'p4', (3,12): 'p5'}
    target = (3,0)
    initpos = (0,0)
    #
    labels_dict = {initpos: 'S', target: 'T'}
    for loc in packagelocs.keys():
        labels_dict.update({loc : 'p_'+str(packagelocs[loc][1:])})
    for goal in packagegoals.keys():
        labels_dict.update({goal : 'd_'+str(packagegoals[goal][1:])})
    grid = Grid('grid.txt', labels_dict)

    if not os.path.exists('imgs'):
        os.makedirs('imgs')
    plot_grid(grid, 'imgs/layout')

    transition_system_input = build_transition_system_automatic(grid, packagelocs, packagegoals, target, initpos)

    sys_formula = 'F(goal)'
    test_formula = 'F(p1d) & F(p2d) & F(p3d) & F(p4d)'#' & F(p5d) & F(p6d)'

    # get automata
    sys_aut, spot_aut_sys = get_system_automaton(sys_formula)
    test_aut, spot_aut_test = get_tester_automaton(test_formula)
    prod_aut = get_product_automaton(spot_aut_sys, spot_aut_test)

    # get transition system
    transys = TranSys(transition_system_input)

    # get virtual graphs
    virtual = sync_prod(transys, prod_aut)
    virtual_sys = None

    if plot_graphs:
        sys_aut.save_plot('sys_aut')
        test_aut.save_plot('test_aut')
        prod_aut.save_plot('prod_aut')
        transys.save_plot('ts')
        virtual.save_plot('virtual')
        # virtual_sys.save_plot('virtual_sys')

    d, flow = solve(virtual, transys, prod_aut, virtual_sys, case = 'static', plot_results = False)

    cuts = [(cut[0][0][0],cut[1][0][0]) for cut in d.keys()]
    plot_grid(grid, 'imgs/result', cuts)

if __name__=='__main__':
    run_example()
