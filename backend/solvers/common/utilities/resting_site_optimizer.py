import pickle
import numpy as np
import gurobipy as g
from gurobipy import GRB
import networkx as nx
from pyvis.network import Network

from solvers.common.utilities.routing_sites import RoutingSites
from solvers.common.utilities.path_optimizer import PathOptimizer


class RestingSiteOptimizer:
    """
    Optimizes the allocation of waiting tasks to resting sites.
    Identifies optimal places for movers to wait during idle periods.
    """

    def __init__(self, df_arr, path_optimizer, routing_sites):
        self.path_optimizer = path_optimizer
        self.routing_sites = routing_sites
        self.w_tasks = []
        self.all_alternates = []
        self.task_to_alternates = {}
        self.conflict_graph = None
        self.cluster_graph = None
        self.model = None
        self.optimization_result = None
        self.edge_color_map = {
            "same_task": "#FF0000",
            "overlap": "#00FF00",
            "default": "#0000FF",
        }
        self.find_waiting_tasks(df_arr)
        self.generate_alternative_tasks()
        self.build_conflict_graph()
        self.build_condensed_conflict_graph()

    def find_waiting_tasks(self, mover_dataframes):
        """
        Identifies waiting periods in mover schedules where they have idle time.
        """
        self.w_tasks = []
        for mover_id, mover_df in enumerate(mover_dataframes):
            mover_df = mover_df.sort_values(by=['Start'])
            prev = None
            for task_i, task in mover_df.iterrows():
                # Skip first task for each mover
                if prev is None:
                    prev = task
                    continue

                # Find path from previous dispenser to current one
                sub_path = self.path_optimizer.find_balanced_path(
                    tuple(prev['Position']),
                    tuple(task['Position'])
                )[1:]

                # Calculate waiting time
                free_time = task['Start'] - prev['Finish'] - len(sub_path)

                # If there's waiting time, add it to the list
                if free_time > 0:
                    w_task = {
                        'path': [tuple(prev['Position'])] + sub_path[:-1],
                        'free_time': free_time,
                        'id': task_i,
                        'start': prev['Finish']
                    }
                    self.w_tasks.append(w_task)
                prev = task

    def generate_alternative_tasks(self):
        """
        Generates alternative resting site options for each waiting task.
        """
        self.all_alternates = []
        self.task_to_alternates = {}

        # For each waiting transit
        for idx, w_task in enumerate(self.w_tasks):
            alternate_for_w = []
            # For each resting site
            for site in self.routing_sites.resting_sites:
                x, y, _ = site
                site_coord = (x, y)

                # Find the best divergent point to minimize travel distance
                best_div_point = None
                shortest_path_len = np.inf
                shortest_path = None
                pre_travel = 0  # tiles traveled along the path before diverging

                for poss_pre_travel, possible_divergent_point in enumerate(w_task['path']):
                    path = self.path_optimizer.find_shortest_path(possible_divergent_point, site_coord)[:-1]
                    if len(path) < shortest_path_len:
                        shortest_path_len = len(path)
                        shortest_path = path
                        best_div_point = possible_divergent_point
                        pre_travel = poss_pre_travel
                to_div = shortest_path[::-1]
                to_rest = shortest_path
                free_time = w_task['free_time'] + 1  # + 1 because we'd be telling it twice to travel to div_point
                if pre_travel == 0:  # if there is no pretravel we are starting from the start, don't add first step
                    # if start is at (5,0) and wait is at (5,0,_), we don't tell it to move at all, so the +1 is redundant
                    if len(to_rest) == 0:
                        free_time -= 1
                    else:
                        to_rest = to_rest[1:]

                # Calculate cost
                # example: takes me 20 ticks to get there, but I have 5 free ticks - cost is 15
                cost = max(0, shortest_path_len * 2 - free_time)
                cost += shortest_path_len * 0.01  # it's costly to move a lot! try to rest more and move less!

                # Calculate task specifics
                w_alt_task = {
                    'start': w_task['start'] + pre_travel + shortest_path_len,
                    'free_time': free_time,
                    'duration': max(0, free_time - shortest_path_len * 2),
                    'cost': cost,
                    'to_rest': to_rest,
                    'to_div': to_div,
                    'site': site,
                    'best_div_point': best_div_point,
                    'id': w_task['id'],
                    'w_task': idx,
                }
                w_alt_task['finish'] = w_alt_task['start'] + w_alt_task['duration']
                alternate_for_w.append(w_alt_task)

            self.all_alternates.extend(alternate_for_w)

            n = len(self.routing_sites.resting_sites)
            start_index = idx * n
            end_index = start_index + n
            self.task_to_alternates[idx] = list(range(start_index, end_index))

    def build_conflict_graph(self):
        """
        Builds a conflict graph where nodes are alternative tasks and edges represent conflicts.
        """
        full_graph = nx.Graph()

        # Add all alternative tasks as nodes
        for i, alt in enumerate(self.all_alternates):
            full_graph.add_node(i, task=alt)

        # Add edges between alternatives of the same waiting task (can't wait at multiple places)
        for alts in self.task_to_alternates.values():
            for i in range(len(alts)):
                for j in range(i + 1, len(alts)):
                    full_graph.add_edge(alts[i], alts[j], reason="same_task")

        # Add edges between alternatives that overlap in time at the same site
        for i in range(len(self.all_alternates)):
            for j in range(i + 1, len(self.all_alternates)):
                alt_i = self.all_alternates[i]
                alt_j = self.all_alternates[j]

                # Check if they use the same site
                if alt_i['site'] == alt_j['site']:
                    # Check for time overlap
                    if alt_i['start'] <= alt_j['finish'] and alt_j['start'] <= alt_i['finish']:
                        full_graph.add_edge(i, j, reason="overlap")

        self.conflict_graph = full_graph

    def build_condensed_conflict_graph(self):
        # Create a new graph to represent clusters as nodes
        cluster_graph = nx.Graph()

        # Add cluster nodes to the new graph
        for cluster_idx in self.task_to_alternates.keys():
            cluster_graph.add_node(
                cluster_idx,
                label=f"w_task {cluster_idx}",
                color=np.random.rand(3, )
            )

        # Add edges between clusters if there are connections between alternatives
        for u, v, data in self.conflict_graph.edges(data=True):
            cluster_u = self.all_alternates[u]['w_task']
            cluster_v = self.all_alternates[v]['w_task']

            # Only add edges between different clusters
            if cluster_u != cluster_v:
                edge_color, reason = self.get_edge_info(data)
                cluster_graph.add_edge(cluster_u, cluster_v, title=reason, color=edge_color)
        self.cluster_graph = cluster_graph

    def run(self):
        # Create model
        model = g.Model("task_selection")
        model.Params.LogToConsole = 0
        self.model = model

        # Add binary decision variables for each alternative
        x = model.addVars(len(self.all_alternates), vtype=GRB.BINARY, name="select")

        # Constraint: Select exactly one alternative for each waiting task
        for task_idx, alts in self.task_to_alternates.items():
            model.addConstr(g.quicksum(x[i] for i in alts) == 1, f"one_alt_for_task_{task_idx}")

        # Constraint: No overlapping tasks can be selected
        for i, j in self.conflict_graph.edges():
            if self.all_alternates[i]['site'] == self.all_alternates[j]['site']:
                model.addConstr(x[i] + x[j] <= 1, f"conflict_{i}_{j}")

        # Objective: Minimize cost
        teleport_cost = (self.all_alternates[i]['cost'] * x[i] for i in range(len(self.all_alternates)))
        model.setObjective(g.quicksum(teleport_cost), GRB.MINIMIZE)

        # Solve the model
        model.optimize()

        # Extract solution
        if model.status == GRB.OPTIMAL:
            selected_alternatives = [self.all_alternates[i] for i in range(len(self.all_alternates)) if x[i].X > 0.5]
            selected_alt_dict = {task['id']: task for task in selected_alternatives}
            self.optimization_result = {
                'selected': selected_alt_dict,
                'graph': self.conflict_graph,
                'solution_value': model.objVal
            }
            return self.optimization_result
        else:
            print(f"No optimal solution found. Status: {model.status}")
            self.optimization_result = None
            return None

    def visualize_graph(self, output_file='conflict_graph.html', samples_per_cluster=3):
        """
        Visualization where each waiting task is represented by a few of its nodes.
        """

        # Sample representative nodes and assign colors
        representative_nodes, node_colors = self.sample_representative_nodes(samples_per_cluster)

        # Create a subgraph with only the representative nodes
        sub_graph = self.conflict_graph.subgraph(representative_nodes)

        # Create an interactive network visualization
        net = Network(height="800px", width="100%", bgcolor="#222222", font_color="white")

        # Add nodes with colors
        for node in sub_graph.nodes():
            net.add_node(node, label=str(node), color=node_colors.get(node, "#FFFFFF"))

        # Add edges with colors based on reason
        for u, v, data in sub_graph.edges(data=True):
            edge_color, reason = self.get_edge_info(data)
            net.add_edge(u, v, title=reason, color=edge_color)

        # Save as an interactive HTML file
        net.show(output_file, notebook=False)

    def get_edge_info(self, data):
        reason = data.get("reason", "default")
        edge_color = self.edge_color_map.get(reason, self.edge_color_map["default"])
        return edge_color, reason

    def visualize_cluster_graph(self, output_file='cluster_graph.html'):
        """
        Cluster-level visualization where each waiting task is a node.
        """

        # Generate random colors for clusters
        unique_clusters = set(self.task_to_alternates.keys())
        color_map = {
            cluster: f"#{''.join([hex(int(c * 255))[2:].zfill(2) for c in np.random.rand(3)])}"
            for cluster in unique_clusters
        }
        node_colors = {n: color_map[n] for n in unique_clusters}

        # Create an interactive network for clusters
        cnet = Network(height="800px", width="100%", bgcolor="#222222", font_color="white")

        # Add nodes for clusters
        for node, data in self.cluster_graph.nodes(data=True):
            cnet.add_node(node, label=data["label"], color=node_colors.get(node, "#FFFFFF"))

        # Add edges for cluster-to-cluster connections
        for u, v, data in self.cluster_graph.edges(data=True):
            if data:
                edge_color = data["color"]
                cnet.add_edge(u, v, color=edge_color)

        # Save as an interactive HTML file
        cnet.show(output_file, notebook=False)

    def sample_representative_nodes(self, num_samples=3):
        """
        Helper method to sample representative nodes from each waiting task cluster.
        """
        sampled_nodes = []
        cluster_labels = {}  # Store cluster labels for coloring

        for task_idx, alts in self.task_to_alternates.items():
            if alts:
                # Sort nodes by degree (most connected first) and take up to num_samples
                top_nodes = sorted(alts, key=lambda node: self.conflict_graph.degree(node), reverse=True)[:num_samples]
                sampled_nodes.extend(top_nodes)
                for node in top_nodes:
                    cluster_labels[node] = task_idx  # Assign cluster index

        # Generate distinct colors for clusters
        unique_clusters = set(cluster_labels.values())
        color_map = {
            cluster: f"#{''.join([hex(int(c * 255))[2:].zfill(2) for c in np.random.rand(3)])}"
            for cluster in unique_clusters
        }
        node_colors = {n: color_map[cluster_labels[n]] for n in sampled_nodes}

        return sampled_nodes, node_colors


if __name__ == '__main__':
    folder = 'ring_ntiles_50_ninterfaces_4_ndispensers_65_movers_12_2025-02-17T12:16:15.274159'

    with open(f'../results/{folder}/metavis.pkl', 'rb') as f:
        metadata = pickle.load(f)
        meta_vis = metadata['meta_vis']
        size_m = metadata['size']
        rows, cols, filled, machine_info = size_m['rows'], size_m['cols'], size_m['filled'], size_m['machine_info']
    with (open(f'../results/{folder}/positions.pkl', 'rb') as f):
        coordinate_dict = pickle.load(f)
    with open(f'../results/{folder}/sched_res.pkl', 'rb') as f:
        df = pickle.load(f)

    df['Position'] = df.apply(lambda row: coordinate_dict[row['Medicine']][row['Dispenser']], axis=1)
    df_arr = [df[df['Mover'] == mover] for mover in df.Mover.unique()]

    path_optimizer = PathOptimizer(rows, cols, filled)
    routing_sites = RoutingSites(coordinate_dict['interface'], rows, cols, filled)

    # Initialize task optimizer
    optimizer = RestingSiteOptimizer(df_arr, path_optimizer, routing_sites)

    result = optimizer.run()

    if result:
        print(f"Optimization successful. Objective value: {result['solution_value']}")
        print(result['selected'])
    else:
        print("Optimization failed.")
