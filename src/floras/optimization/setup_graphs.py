"""Contains GraphData class for optimization and parses the virtual graphs into the required form."""
import networkx as nx

class GraphData:
    def __init__(self, nodes, edges, node_dict, inv_node_dict, acc_sys, acc_test, init, custom_map = None):
        self.nodes = nodes
        self.edges = edges
        self.node_dict = node_dict
        self.inv_node_dict = inv_node_dict
        self.acc_sys = acc_sys
        self.acc_test = acc_test
        self.init = init
        self.graph = self.setup_graph(nodes, edges)
        self.int = self.acc_test
        self.sink = self.acc_sys
        self.custom_map = custom_map
        self.do_not_cut = self.find_do_not_cut_edges()

    def setup_graph(self, nodes, edges):
        G = nx.DiGraph()
        G.add_nodes_from(nodes)
        G.add_edges_from(edges)
        return G

    def find_do_not_cut_edges(self):
        do_not_cut = []
        for edge in self.graph.edges:
            reach_T = False
            reach_I = False
            for accsys in self.acc_sys:
                if nx.has_path(self.graph, edge[0], accsys):
                    reach_T = True
                    break
            if reach_T:
                for acctest in self.acc_test:
                    if nx.has_path(self.graph, edge[0], acctest):
                        reach_I = True
                        break
            if reach_T and not reach_I:
                do_not_cut.append(edge)
        return do_not_cut


def setup_nodes_and_edges(virtual, virtual_sys, b_pi, case = 'static'):
    # setup nodes and map
    nodes = []
    node_dict = {}
    inv_node_dict = {}
    for i, node in enumerate(virtual.G_initial.nodes):
        nodes.append(i)
        node_dict.update({i: virtual.reverse_Sdict[node]})
        inv_node_dict.update({virtual.reverse_Sdict[node]: i})
    # find initial state
    init = []
    for initial in virtual.I:
        init.append(inv_node_dict[initial])
    # find accepting states for system and tester
    acc_sys = []
    acc_test = []
    for node in nodes:
        if node_dict[node] in virtual.sink:
            acc_sys.append(node)
        if node_dict[node] in virtual.int:
            acc_test.append(node)
    # setup edges
    edges = []
    for edge in virtual.G_initial.edges:
        out_node = virtual.reverse_Sdict[edge[0]]
        in_node = virtual.reverse_Sdict[edge[1]]
        edges.append((inv_node_dict[out_node],inv_node_dict[in_node]))

    GD = GraphData(nodes, edges, node_dict, inv_node_dict, acc_sys, acc_test, init, custom_map = virtual.transys.custom_map)

    if case != 'static':
        # setup system graph
        S_nodes = []
        S_node_dict = {}
        S_inv_node_dict = {}
        for i, node in enumerate(virtual_sys.G_initial.nodes):
            S_nodes.append(i)
            S_node_dict.update({i: virtual_sys.reverse_Sdict[node]})
            S_inv_node_dict.update({virtual_sys.reverse_Sdict[node]: i})
        # find initial state
        S_init = []
        for initial in virtual_sys.I:
            S_init.append(S_inv_node_dict[initial])
        # find accepting states for system
        S_acc_sys = []
        for node in S_nodes:
            if S_node_dict[node] in virtual_sys.sink:
                S_acc_sys.append(node)
        # setup edges
        S_edges = []
        for edge in virtual_sys.G_initial.edges:
            out_node = virtual_sys.reverse_Sdict[edge[0]]
            in_node = virtual_sys.reverse_Sdict[edge[1]]
            S_edges.append((S_inv_node_dict[out_node],S_inv_node_dict[in_node]))

        S = GraphData(S_nodes, S_edges, S_node_dict, S_inv_node_dict, S_acc_sys, [], S_init)
    else:
        S = None

    return GD, S
