import gurobipy as g
import numpy as np
import pandas as pd

from solvers.common.utilities.path_optimizer import PathOptimizer
from solvers.cplex_medicine.models import CplexExperimentModel, CplexLayout


def load_real_patients(data: CplexExperimentModel):
    """Extracts patient data.

    Args:
        data: Experiment data.

    Returns:
        patient_list: List of patient data.
        dosage_list: List of dosage data.
    """
    patient_list = []
    dosage_list = []

    for order in data.orders:
        patient_list.append(set(order.drug_names))
        dosage_list.append(order.dosages)

    return patient_list, dosage_list


"""
Lazy subtour elimination TSP model.
"""


def solve_tsp(c, num_sites, bigM):
    def detect_tour(sol, n_nodes):
        visited = [False] * n_nodes
        cycles = []
        lengths = []
        selected = [[] for i in range(n_nodes)]

        for x, y in sol:
            selected[x].append(y)
        while True:
            current = visited.index(False)
            currcycle = [current]
            while True:
                visited[current] = True
                neighbors = [x for x in selected[current] if not visited[x]]
                if len(neighbors) == 0:
                    break
                current = neighbors[0]
                currcycle.append(current)
            cycles.append(currcycle)
            lengths.append(len(currcycle))
            if sum(lengths) == n_nodes:
                break
        return cycles[lengths.index(min(lengths))]

    def subtour_cut(model, where):
        if where == g.GRB.callback.MIPSOL:
            sol = []
            n_nodes = model._n_nodes
            for i in range(n_nodes):
                s = model.cbGetSolution([model._x[i, j] for j in range(n_nodes)])
                sol += [(i, j) for j in range(n_nodes) if s[j] > 0.5]
            S = detect_tour(sol, n_nodes)
            if len(S) < n_nodes:
                cut_plane = 0
                for i in S:
                    for j in S:
                        if i != j:
                            cut_plane += model._x[i, j]

                model.cbLazy(cut_plane <= len(S) - 1)

    n_nodes = c.shape[0]

    model = g.Model()
    x = model.addVars(n_nodes, n_nodes, vtype=g.GRB.BINARY)
    for i in range(n_nodes):
        model.addConstr(g.quicksum([x[i, j] for j in range(n_nodes)]) == 1)
        x[i, i].ub = 0
    for j in range(n_nodes):
        model.addConstr(g.quicksum([x[i, j] for i in range(n_nodes)]) == 1)

    model.setObjective(
        g.quicksum([x[i, j] * c[i, j] for i in range(n_nodes) for j in range(n_nodes)]) - len(num_sites.keys()) * bigM)

    model._n_nodes = n_nodes
    model._x = x
    model.params.OutputFlag = 0
    model.params.LazyConstraints = 1
    model.optimize(subtour_cut)

    # reconstruct solution
    sol = []
    for i in range(n_nodes):
        s = [x[i, j].x for j in range(n_nodes)]
        sol += [(i, j) for j in range(n_nodes) if s[j] > 0.5]

    return int(round(model.objVal)), detect_tour(sol, n_nodes)


"""
Solves relaxation for the given patient using TSP with neighborhoods using Noon-Bean transform to ordinary TSP.
"""


def patient_tsp_lb(drug_list, dosage_list, layout: CplexLayout, interface_time, dosage_ratio,
                   path_optimizer: PathOptimizer):
    # number of sites
    num_sites = {}
    for d in drug_list:
        num_sites[d] = sum([(d in pack) for id, pack in layout.packer_result.items()])

    num_sites["interface_s"] = layout.interface_amount
    num_sites["interface_t"] = layout.interface_amount

    # coordinates for each site
    placement = layout.placement
    sites_coordinates = {}
    idx_counter = 0
    site_id_to_vertex_idx = {}
    vertex_id_to_site_id = {}
    for site in num_sites.keys():
        look_for_site = site if not site.startswith("interface") else site[:-2]
        sites_coordinates[site] = []
        for i in range(len(placement)):
            locs = [(i, j) for j in range(len(placement[i])) if look_for_site in placement[i][j].split(",")]
            sites_coordinates[site] += locs

        for id in range(len(sites_coordinates[site])):
            site_id_to_vertex_idx[(site, id)] = idx_counter
            vertex_id_to_site_id[idx_counter] = (site, id)
            idx_counter += 1

    # original distance matrix calculation
    total_sites = sum(num_sites.values())
    orig_distances = np.zeros(shape=(total_sites, total_sites))

    for da in range(total_sites):
        for db in range(total_sites):
            site_a, id_a = vertex_id_to_site_id[da]
            loc_a = sites_coordinates[site_a][id_a]
            site_b, id_b = vertex_id_to_site_id[db]
            loc_b = sites_coordinates[site_b][id_b]
            orig_distances[da, db] = len(path_optimizer.find_shortest_path(loc_a, loc_b))

    bigM = np.sum(orig_distances[:, :])
    gtsp_distances = total_sites * bigM * np.ones(shape=(total_sites, total_sites))  # + bigM*np.eye(total_sites)
    # zero cycles within cluster
    for site in num_sites:
        cycle_site = [site_id_to_vertex_idx[(site, id)] for id in range(num_sites[site])]
        if len(cycle_site) > 1:
            gtsp_distances[cycle_site[len(cycle_site) - 1], cycle_site[0]] = 0
            for k in range(len(cycle_site) - 1):
                gtsp_distances[cycle_site[k], cycle_site[k + 1]] = 0

    # edges between clusters
    for da in range(total_sites):
        for db in range(total_sites):
            site_a, id_a = vertex_id_to_site_id[da]
            loc_a = sites_coordinates[site_a][id_a]
            site_b, id_b = vertex_id_to_site_id[db]
            if site_a != site_b and (not site_a.startswith("interface") or not site_b.startswith("interface")) and \
                    site_a != "interface_t" and site_b != "interface_s":  # for edges between clusters
                parent_id_b = (id_b + 1) % num_sites[site_b]
                parent_b_idx = site_id_to_vertex_idx[(site_b, parent_id_b)]

                gtsp_distances[da, parent_b_idx] = orig_distances[da, db] + bigM

    # "zero" edges from interface_t to interface_s
    for i in range(num_sites["interface_t"]):
        vertex_idx_from = site_id_to_vertex_idx[("interface_t", i)]
        for j in range(num_sites["interface_s"]):
            vertex_idx_to = site_id_to_vertex_idx[("interface_s", j)]
            gtsp_distances[vertex_idx_from, vertex_idx_to] = 0 + bigM

    setup_cost, solution = solve_tsp(gtsp_distances, num_sites, bigM)
    patient_sequence = []
    last_site, last_id = vertex_id_to_site_id[solution[0]]
    for k in solution[1:]:
        site, id = vertex_id_to_site_id[k]
        if site != last_site:
            id = (id - 1) % num_sites[site]  # inverse transform
            patient_sequence += [(last_site, sites_coordinates[last_site][last_id]),
                                 (site, sites_coordinates[site][id])]

        last_site = site
        last_id = id

    # canonical form of the sequence
    k = 0
    site = patient_sequence[k][0]
    while site != "interface_s":
        k += 1
        site = patient_sequence[k][0]

    canonical_seq = patient_sequence[k:] + patient_sequence[0:k]
    canonical_seq_unique = []
    k = 0
    last_site = None
    while k < len(canonical_seq):
        if canonical_seq[k][0] != last_site:
            canonical_seq_unique += [canonical_seq[k]]
        last_site = canonical_seq[k][0]
        k += 1

    assert canonical_seq_unique[0][0] == "interface_s"
    assert canonical_seq_unique[-1][0] == "interface_t"
    assert len(canonical_seq_unique) == 2 + len(dosage_list)

    return 2 * interface_time + dosage_ratio * sum(dosage_list) + setup_cost, canonical_seq_unique


def patient_static_lb(drug_list, dosage_list, topology, interface_time, dosage_ratio):
    return 2 * interface_time + 2 + dosage_ratio * sum(dosage_list), None


def get_patient_lbs(n_patients, patient_list, dosage_list, interface_time, dosage_ratio, layout: CplexLayout,
                    path_optimizer):
    lbs = []
    for j in range(n_patients):
        lb, _ = patient_tsp_lb(patient_list[j], dosage_list[j], layout, interface_time, dosage_ratio, path_optimizer)
        lbs += [lb]
    return lbs


def warm_up(n_patients, layout: CplexLayout, dosage_ratio, patient_list, dosage_list, path_optimizer):
    interface_time = 3
    patient_time = get_patient_lbs(n_patients, patient_list, dosage_list, interface_time, dosage_ratio, layout,
                                   path_optimizer)
    return patient_time


def optimize(n_movers, n_patients, patient_time):
    m = g.Model()
    x = m.addVars(n_movers, n_patients, vtype=g.GRB.BINARY)
    Cmax = m.addVar(vtype=g.GRB.CONTINUOUS, obj=1)

    for j in range(n_patients):
        m.addConstr(g.quicksum([x[i, j] for i in range(n_movers)]) == 1)

    for i in range(n_movers):
        m.addConstr(g.quicksum([x[i, j] * patient_time[j] for j in range(n_patients)]) <= Cmax)

    m.params.timelimit = 20
    m.optimize()
    return m, x


def parse_results(n_movers, n_patients, patient_time, x):
    activity_list = []
    for i in range(n_movers):
        start_time = 0
        for j in range(n_patients):
            if x[i, j].x > 0.5:
                activity_list += [dict(Task=f"patient_{j}", Start=start_time, Finish=start_time + patient_time[j],
                                       Resource=f"mover{i}")]
                start_time += patient_time[j]

    df = pd.DataFrame(activity_list)
    df['delta'] = df['Finish'] - df['Start']
    return df


def get_patient_arrangement(path_optimizer: PathOptimizer, data: CplexExperimentModel):
    patient_list, dosage_list = load_real_patients(data)
    patient_time = warm_up(len(data.orders), data.layout, data.dispensing_time, patient_list, dosage_list,
                           path_optimizer)
    model, x = optimize(data.mover_amount, len(data.orders), patient_time)
    df = parse_results(data.mover_amount, len(data.orders), patient_time, x)
    return model, df, x
