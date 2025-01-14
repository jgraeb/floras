from floras.optimization.setup_graphs import setup_nodes_and_edges
from floras.optimization.optimization import MILP


def solve(virtual, system, b_pi, virtual_sys, case='static',
          print_solution=True, plot_results=False, callback='cb'):
    GD, SD = setup_nodes_and_edges(virtual, virtual_sys, b_pi, case=case)

    milp = MILP(GD, SD, case, callback=callback)
    d, flow, exit_status = milp.optimize()
    if exit_status == 'opt':
        if plot_results:
            cuts = [x for x in d.keys() if d[x] >= 0.9]
            virtual.save_result_plot(cuts, 'virtual_with_cuts')
        return d, flow
