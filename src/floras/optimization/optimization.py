'''
Class to set up optimization problem, solve it, and parse the output.
'''
from gurobipy import GRB
import time
import numpy as np
import networkx as nx
from floras.optimization.utils import find_map_G_S
from gurobipy import *
from copy import deepcopy
import os
import json

from ipdb import set_trace as st

class MILP():
    """
    Mixed Integer Linear program class.

    Args:
        GD: GraphData object representing the virtual product graph G.
        SD: GraphData object representing the system virtual graph S.
        type: Type of the optimization to call (default is static).
        callback: If callback function should be used (default 'cb').
    """
    def __init__(self, GD, SD, type = 'static', callback = 'cb'):
        self.type = type
        self.GD = GD
        self.SD = SD
        self.callback = callback
        self.cleaned_intermed = []
        self.model_edges = []
        self.model_nodes = []
        self.src = []
        self.s_sink = []
        self.model_s_edges = []
        self.model_s_nodes = []
        self.model = None
        self.map_G_to_S = None
        self.G, self.S, self.G_minus_I = self.prepare()

    def prepare(self):
        """
        Prepares the edges and nodes needed for the optimization variables.

        Returns:
            G: Networkx virtual product graph.
            S: Networkx virtual system graph.
            G_minus_I: Networkx virtual product graph without I nodes.

        """
        self.cleaned_intermed = [x for x in self.GD.acc_test if x not in self.GD.acc_sys]
        # create G and remove self-loops
        G = self.GD.graph
        to_remove = []
        for i, j in G.edges:
            if i == j:
                to_remove.append((i,j))
        G.remove_edges_from(to_remove)

        # remove intermediate nodes
        G_minus_I = deepcopy(G)
        G_minus_I.remove_nodes_from(self.cleaned_intermed)

        self.model_edges = list(G.edges)
        self.model_nodes = list(G.nodes)

        self.model_edges_without_I = list(G_minus_I.edges)
        self.model_nodes_without_I = list(G_minus_I.nodes)

        self.src = self.GD.init
        self.sink = self.GD.sink
        self.inter = self.cleaned_intermed

        # create S and remove self-loops
        if self.type != 'static':
            S = self.SD.graph
            to_remove = []
            for i, j in S.edges:
                if i == j:
                    to_remove.append((i,j))
            S.remove_edges_from(to_remove)
            self.model_s_edges = list(S.edges)
            self.model_s_nodes = list(S.nodes)
            self.s_sink = self.SD.acc_sys
        else:
            S = None

        return G, S, G_minus_I

    def static_model(self):
        '''
        Set up the model for the static case.
        '''
        self.model = Model()
        # Define variables
        f = self.model.addVars(self.model_edges, name="flow")
        m = self.model.addVars(self.model_nodes_without_I, name="m")
        d = self.model.addVars(self.model_edges, vtype=GRB.BINARY, name="d")

        # Define Objective
        term = sum(f[i,j] for (i, j) in self.model_edges if i in self.src)
        ncuts = sum(d[i,j] for (i, j) in self.model_edges)
        reg = 1/len(self.model_edges)
        self.model.setObjective(term - reg*ncuts, GRB.MAXIMIZE)

        # Add the constraints
        self.bounds_constraints(f,d,m)
        self.conservation_constraints(f)
        self.preserve_flow_constraints(f)
        self.no_flow_in_source_out_sink_constraints(f)
        self.cut_constraints(f,d)
        self.partition_constraints(d,m)
        self.bidirectional_constraints(d)

        if self.GD.custom_map:
            self.custom_static_constraints(d)
        else:
            self.static_constraints(d)

    def reactive_model(self):
        # for the flow on S
        self.map_G_to_S = find_map_G_S(self.GD,self.SD)

        self.model = Model()
        # Define variables
        f = self.model.addVars(self.model_edges, name="flow")
        m = self.model.addVars(self.model_nodes_without_I, name="m")
        d = self.model.addVars(self.model_edges_without_I, vtype=GRB.BINARY, name="d")

        # Define Objective
        term = sum(f[i,j] for (i, j) in self.model_edges if i in self.src)
        ncuts = sum(d[i,j] for (i, j) in self.model_edges_without_I)
        reg = 1/len(self.model_edges)
        self.model.setObjective(term - reg*ncuts, GRB.MAXIMIZE)

        # add constraints
        self.bounds_constraints(f,d,m)
        self.conservation_constraints(f)
        self.preserve_flow_constraints(f)
        self.no_flow_in_source_out_sink_constraints(f)
        self.cut_constraints(f,d)
        self.partition_constraints(d,m)
        self.do_not_cut_edges(d)

        # --------- add feasibility constraints to preserve flow F_s >=1 on S for every q
        node_list = []
        for node in self.G.nodes:
            node_list.append(self.GD.node_dict[node])

        qs = list(set([node[-1] for node in node_list]))

        # get the source/sink pairs (sink always T) for the history variables q
        s_srcs = {}
        for q in qs:
            transition_nodes = []
            for edge in self.G.edges:
                out_edge = self.GD.node_dict[edge[0]]
                in_edge = self.GD.node_dict[edge[1]]
                if in_edge[-1] == q and out_edge[-1] != q:
                    node = edge[1]
                    s_nodes = self.map_G_to_S[node]
                    for target in self.s_sink:
                        for s_node in s_nodes:
                            if nx.has_path(self.S,s_node,target):
                                transition_nodes.append(s_node)
            clean_transition_nodes = list(set(transition_nodes))
            s_srcs.update({q: clean_transition_nodes})
        s_srcs.update({'q0': self.SD.init})


        s_data = []
        for q in qs:
            for k,s in enumerate(s_srcs[q]):
                name = 'fS_'+ str(q) +'_'+ str(k)
                source = s
                s_data.append((name, q, source))

        f_s = [None for entry in s_data]
        for k,entry in enumerate(s_data):
            name = entry[0]
            curr_q = entry[1]
            s_src = [entry[2]]
            if entry[2] not in self.s_sink:

                f_s[k] = self.model.addVars(self.model_s_edges, name=name)

                # nonnegativity for f_s (lower bound)
                self.model.addConstrs((f_s[k][i, j] >= 0 for (i,j) in self.model_s_edges), name= name + '_nonneg')

                # capacity on S (upper bound on f_s)
                self.model.addConstrs((f_s[k][i, j] <= 1 for (i,j) in self.model_s_edges), name=name+ '_capacity')

                # Preserve flow of 1 in S
                self.model.addConstr((1 <= sum(f_s[k][i,j] for (i, j) in self.model_s_edges if j in self.s_sink)), name=name + '_conserve_flow_1')

                # conservation on S
                self.model.addConstrs((sum(f_s[k][i,j] for (i,j) in self.model_s_edges if j == l) == sum(f_s[k][i,j] for (i,j) in self.model_s_edges if i == l) for l in self.model_s_nodes if l not in s_src and l not in self.s_sink), name=name+'_conservation')

                # no flow into sources and out of sinks on S
                self.model.addConstrs((f_s[k][i,j] == 0 for (i,j) in self.model_s_edges if j in s_src or i in self.s_sink), name=name+ '_sink_src')

                # Match the edge cuts from G to S
                for (i,j) in self.model_edges_without_I:
                    if self.GD.node_dict[i][-1] == curr_q:
                        imaps = self.map_G_to_S[i]
                        jmaps = self.map_G_to_S[j]

                        for imap in imaps:
                            for jmap in jmaps:
                                if (imap,jmap) in self.SD.edges:
                                    self.model.addConstr(f_s[k][imap, jmap] + d[i, j] <= 1)

    def bounds_constraints(self,f,d,m):
        # Define constraints
        if self.type == 'static':
            d_domain = self.model_edges
        else:
            d_domain = self.model_edges_without_I
        # Nonnegativity - lower bounds
        self.model.addConstrs((d[i, j] >= 0 for (i,j) in d_domain), name='d_nonneg')
        self.model.addConstrs((m[i] >= 0 for i in self.model_nodes_without_I), name='mu_nonneg')
        self.model.addConstrs((f[i, j] >= 0 for (i,j) in self.model_edges), name='f_nonneg')

        # upper bounds
        self.model.addConstrs((d[i, j] <= 1 for (i,j) in d_domain), name='d_upper_b')
        self.model.addConstrs((m[i] <= 1 for i in self.model_nodes_without_I), name='mu_upper_b')
        # capacity (upper bound for f)
        self.model.addConstrs((f[i, j] <= 1 for (i,j) in self.model_edges), name='capacity')

    def conservation_constraints(self,f):
        # conservation
        self.model.addConstrs((sum(f[i,j] for (i,j) in self.model_edges if j == l) == sum(f[i,j] for (i,j) in self.model_edges if i == l) for l in self.model_nodes if l not in self.src and l not in self.sink), name='conservation')

    def preserve_flow_constraints(self,f):
        # preserve flow of at least 1
        self.model.addConstr((1 <= sum(f[i,j] for (i, j) in self.model_edges if i in self.src)), name='conserve_F')

    def no_flow_in_source_out_sink_constraints(self,f):
        # no flow into source or out of sink
        self.model.addConstrs((f[i,j] == 0 for (i,j) in self.model_edges if j in self.src or i in self.sink), name="no_out_sink_in_src")

    def cut_constraints(self,f,d):
        if self.type == 'static':
            d_domain = self.model_edges
        else:
            d_domain = self.model_edges_without_I
        # cut constraint (cut edges have zero flow)
        self.model.addConstrs((f[i,j] + d[i,j] <= 1 for (i,j) in d_domain), name='cut_cons')

    def partition_constraints(self,d,m):
        # source sink partitions
        for i in self.model_nodes_without_I:
            for j in self.model_nodes_without_I:
                if i in self.src and j in self.sink:
                    self.model.addConstr(m[i] - m[j] >= 1)

        # max flow cut constraint (cut variable d partitions the groups)
        self.model.addConstrs((d[i,j] - m[i] + m[j] >= 0 for (i,j) in self.model_edges_without_I))

    def static_constraints(self,d):
        # --------- map static obstacles to other edges in G
        for count, (i,j) in enumerate(self.model_edges):
            out_state = self.GD.node_dict[i][0]
            in_state = self.GD.node_dict[j][0]
            for (imap,jmap) in self.model_edges[count+1:]:
                if out_state == self.GD.node_dict[imap][0] and in_state == self.GD.node_dict[jmap][0]:
                    self.model.addConstr(d[i, j] == d[imap, jmap])

    def do_not_cut_edges(self,d):
        # ---------- do not cut edges that would introduce dead ends
        do_not_cut = [edge for edge in self.GD.do_not_cut if edge in self.model_edges]
        self.model.addConstrs((d[i, j] == 0 for (i,j) in do_not_cut), name='d_do_not_cut')


    def custom_static_constraints(self,d):
        # st()
        for count, (i,j) in enumerate(self.model_edges):
            out_state = self.GD.custom_map[self.GD.node_dict[i][0]]
            in_state = self.GD.custom_map[self.GD.node_dict[j][0]]
            for (imap,jmap) in self.model_edges[count+1:]:
                if out_state == self.GD.custom_map[self.GD.node_dict[imap][0]] and in_state == self.GD.custom_map[self.GD.node_dict[jmap][0]]:
                    self.model.addConstr(d[i, j] == d[imap, jmap])


    def bidirectional_constraints(self,d):
        # ---------  add bidirectional cuts on G (for static examples)
        if self.GD.custom_map:
            for count, (i,j) in enumerate(self.model_edges):
                out_state = self.GD.custom_map[self.GD.node_dict[i][0]]
                in_state = self.GD.custom_map[self.GD.node_dict[j][0]]
                for (imap,jmap) in self.model_edges[count+1:]:
                    if in_state == self.GD.custom_map[self.GD.node_dict[imap][0]] and out_state == self.GD.custom_map[self.GD.node_dict[jmap][0]]:
                        self.model.addConstr(d[i, j] == d[imap, jmap])
        else:
            for count, (i,j) in enumerate(self.model_edges):
                out_state = self.GD.node_dict[i][0]
                in_state = self.GD.node_dict[j][0]
                for (imap,jmap) in self.model_edges[count+1:]:
                    if in_state == self.GD.node_dict[imap][0] and out_state == self.GD.node_dict[jmap][0]:
                        self.model.addConstr(d[i, j] == d[imap, jmap])


    def setup_model(self):
        """
        Setting up the model for the optimization.
        Declares variables and bounds, adds constraints depending on type.
        """
        if self.type == 'static':
            self.static_model()
        elif self.type == 'reactive':
            self.reactive_model()
        else:
            print('Requested optimization type not available, options are \'static\' or \'reactive\'.')

    def solve_problem(self):
        """
        Solve the model.
        """
        # --------- set parameters
        # store model data for logging
        self.model._data = dict() # Store termination conditions
        self.model._data["term_condition"] = None

        # Last updated objective and time (for callback function)
        self.model._obj_time = time.time()  # Track the last improvement time
        self.model._cur_obj = GRB.INFINITY # Start with an infinite objective
        self.model._time = time.time() # Track when optimization starts
        self.model.Params.Seed = np.random.randint(0,100)
        self.model._data["random_seed"] = self.model.Params.Seed

        self.model.setParam("Method", -1)  # -1 enables automatic algorithm selection
        # self.model.setParam("ConcurrentMIP", 1)  # Enable concurrent MIP mode
        # Set parameters
        # self.model.setParam("Threads", 4)          # Use 4 threads
        # self.model.setParam("Presolve", 2)         # Aggressive presolve
        # self.model.setParam("Cuts", 2)             # Aggressive cuts
        # self.model.setParam("MIPGap", 0.01)        # Accept solutions within 1% of optimal
        # self.model.setParam("TimeLimit", 1800)     # 30 minutes time limit
        # self.model.setParam("Heuristics", 0.5)     # Increase heuristic effort

        # optimize
        if self.callback=="cb":
            t0 = time.time()
            self.model.optimize(callback=cb)
            tf = time.time()
            delt = tf - t0
        else:
            t0 = time.time()
            self.model.optimize()
            tf = time.time()
            delt = tf - t0

    def parse_solution(self, print=False):
        """
        Parse the solution.

        Returns:
            d_vals: Vector of cut values for each edge (d^e=1 is cut).
            flow: Vector of flow values for each edge.
            exit_status: Exit status of the optimization.
        """
        self.model._data["runtime"] = self.model.Runtime
        self.model._data["flow"] = None
        self.model._data["ncuts"] = None
        # Storing problem variables:
        self.model._data["n_bin_vars"] = self.model.NumBinVars
        self.model._data["n_cont_vars"] = self.model.NumVars - self.model.NumBinVars
        self.model._data["n_constrs"] = self.model.NumConstrs
        self.model._data["mip_gap"] = self.model.MIPGap

        f_vals = []
        d_vals = []
        flow = None
        exit_status = None
        f = self.model.getVarByName("flow")
        d = self.model.getVarByName("d")

        if self.model.status == 4:
            self.model.Params.DualReductions = 0
            exit_status = 'inf'
            self.model._data["status"] = "inf/unbounded"
            return 0,0,exit_status
        elif self.model.status == 11 and self.model.SolCount < 1:
            exit_status = 'not solved'
            self.model._data["status"] = "not_solved"
            self.model._data["exit_status"] = exit_status
        elif self.model.status == 2 or (self.model.status == 11 and self.model.SolCount >= 1):
            if self.model.status == 2:
                self.model._data["status"] = "optimal"
                self.model._data["term_condition"] = "optimal found"
            else:
                # feasible. may be optimal.
                self.model._data["status"] = "feasible"

            # --------- parse output
            d_vals = dict()
            f_vals = dict()

            for (i,j) in self.model_edges:
                f_vals.update({(i,j): self.model.getVarByName('flow['+str(i)+','+str(j)+']').X})
            if self.type == 'static':
                for (i,j) in self.model_edges:
                    d_vals.update({(i,j): self.model.getVarByName('d['+str(i)+','+str(j)+']').X})
            elif self.type == 'reactive':
                for (i,j) in self.model_edges_without_I:
                    d_vals.update({(i,j): self.model.getVarByName('d['+str(i)+','+str(j)+']').X})

            flow = sum(self.model.getVarByName('flow['+str(i)+','+str(j)+']').X for (i,j) in self.model_edges if i in self.src)
            self.model._data["flow"] = flow
            ncuts = 0

            d_parsed = {}
            for key in d_vals.keys():
                if d_vals[key] > 0.9:
                    ncuts+=1
                    d_parsed.update({(self.GD.node_dict[key[0]], self.GD.node_dict[key[1]]) : d_vals[key]})
                    if print:
                        print('{0} to {1} at {2}'.format(self.GD.node_dict[key[0]], self.GD.node_dict[key[1]],d_vals[key]))

            self.model._data["ncuts"] = ncuts
            exit_status = 'opt'
            self.model._data["exit_status"] = exit_status
        elif self.model.status == 3:
            exit_status = 'inf'
            self.model._data["status"] = "inf"
        else:
            st()

        if not os.path.exists("log"):
            os.makedirs("log")
        with open('log/opt_data.json', 'w') as fp:
            json.dump(self.model._data, fp)

        return d_parsed, flow, exit_status

    def optimize(self):
        """
        Setup the model, solve the problem, and parse the solution.
        """
        self.setup_model()
        self.solve_problem()
        print(f'model run time: {self.model.Runtime}')
        print(f'model bin vars: {self.model.NumBinVars}')
        print(f'model continuous vars: {self.model.NumVars - self.model.NumBinVars}')
        print(f'model constraints: {self.model.NumConstrs}')
        d_vals, flow, exit_status = self.parse_solution()
        return d_vals, flow, exit_status

def cb_mip(model, where):
    """
    Callback function to terminate the program if:
    1. The objective has not improved significantly.
    2. The MIP gap is below a threshold.
    3. A timeout is reached (default: 12 hours).
    """
    if where == GRB.Callback.MIPNODE:
        # Best known solution at the current node
        obj = model.cbGet(GRB.Callback.MIPNODE_OBJBST)
        sol_count = model.cbGet(GRB.Callback.MIPNODE_SOLCNT)

        # Update incumbent objective and time if improvement occurs
        if sol_count > 0 and abs(obj - model._cur_obj) > 1e-8:
            model._cur_obj = obj
            model._obj_time = time.time()

    elif where == GRB.Callback.MIP:
        # Retrieve best bound and objective
        best_bound = model.cbGet(GRB.Callback.MIP_OBJBND)
        best_obj = model.cbGet(GRB.Callback.MIP_OBJBST)

        # Calculate the MIP gap if feasible
        if best_obj < GRB.INFINITY and best_bound > -GRB.INFINITY:
            mip_gap = abs(best_bound - best_obj) / max(abs(best_obj), 1)
            model._mipgap = mip_gap

            # Terminate if MIP gap is below the threshold (e.g., 5%)
            if mip_gap < 0.05:
                model._data["term_condition"] = "Mipgap low"
                model.terminate()

        # Terminate if total runtime exceeds 12 hours
        elapsed_time = time.time() - model._time
        if elapsed_time > 3600 * 12:
            model._data["term_condition"] = "Timeout"
            model.terminate()

def cb(model, where):
    """
    Callback function to terminate the program if the objective has not
    improved in 1 hour or no solution was found in 12 hours.
    """
    if where == GRB.Callback.MIPNODE:
        obj = model.cbGet(GRB.Callback.MIPNODE_OBJBST) # Current best objective
        sol_count = model.cbGet(GRB.Callback.MIPNODE_SOLCNT) # No. of feasible solns found.

        if abs(obj - model._cur_obj) > 1e-8:
            # If so, update incumbent
            model._cur_obj = obj
            model._obj_time = time.time()

        if sol_count >= 1: # if objective didnt change in 1 hr
            if time.time() - model._obj_time > 3600:
                model._data["term_condition"] = "Obj not changing"
                model.terminate()

        # Total termination time if the optimizer has not found anything in 5 min:
        if time.time() - model._time > 3600*12:
            model._data["term_condition"] = "Timeout"
            model.terminate()
