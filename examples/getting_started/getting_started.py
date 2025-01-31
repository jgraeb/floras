from floras.components.automata import (
    get_system_automaton,
    get_tester_automaton,
    get_product_automaton
)
from floras.components.transition_system import TransitionSystemInput, TranSys
from floras.components.product import sync_prod
from floras.optimization.optimize import solve
from floras.components.utils import get_states_and_transitions_from_file
from floras.components.grid import Grid
from floras.components.plotting import plot_grid

rows = 3
cols = 5

# defining the state for each cell on the grid
states_list = [(i, j) for i in range(0, rows) for j in range(0, cols)]

# defining the transitions from each cell on the grid
transitions_dict = {}
for i in range(rows):
    for j in range(cols):
        cell = (i, j)
        neighbors = [
                (i + di, j + dj) for di, dj in
                [(-1, 0), (1, 0), (0, -1), (0, 1), (0, 0)]
                if 0 <= i + di < rows and 0 <= j + dj < cols
        ]
        transitions_dict[cell] = neighbors

# alternatively, you can use the gridfile
gridfile = "gridworld.txt"
states_list, transitions_dict = get_states_and_transitions_from_file(gridfile)

# defining the labeled states
labels_dict = {
      (2, 0): ['I'], (0, 2): ['I'], (2, 4): ['I'],
      (0, 0): ['T'], (0, 4): ['T']
    }

# defining the initial state
init_list = [(2, 2)]

# creating the transition system input
transition_system_input = TransitionSystemInput(
    states_list, transitions_dict, labels_dict, init_list
)

# get transition system
transys = TranSys(transition_system_input)

# system objective
sys_formula = 'F(T)'  # 'F(T)' or '<> T' for 'eventually T'
sys_aut, spot_aut_sys = get_system_automaton(sys_formula)

# test objective
test_formula = 'F(I)'
test_aut, spot_aut_test = get_tester_automaton(test_formula)

# product automaton
prod_aut = get_product_automaton(spot_aut_sys, spot_aut_test)

# get virtual graphs
virtual_sys = sync_prod(transys, sys_aut)
virtual = sync_prod(transys, prod_aut)

# set up and solve the optimization problem
d, flow = solve(virtual, transys, prod_aut, virtual_sys, case='static')

# Set up to plot the result
colors_dict = {(0,0): '#ffb000', (0,4): '#ffb000', (2,0): '#648fff', (0,2): '#648fff', (2,4): '#648fff'}
gridfile = "gridworld.txt"
grid = Grid(gridfile, labels_dict, colors_dict)
obstacles = [(cut[0][0],cut[1][0]) for cut in d]

# plot and save the result
resultfile = 'resultfile'
plot_grid(grid, resultfile, obstacles)
