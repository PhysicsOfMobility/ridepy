import networkx as nx


def make_nx_grid(
    dim=(3, 3),
    periodic=False,
    edge_distance=1,
):
    graph = nx.grid_graph(dim=dim, periodic=periodic)
    nx.set_edge_attributes(graph, edge_distance, "distance")
    graph = nx.relabel.convert_node_labels_to_integers(
        graph, label_attribute="location"
    )
    return graph


def make_nx_cycle_graph(
    n_nodes=10,
    edge_distance=1,
):
    graph = nx.generators.classic.cycle_graph(n=n_nodes)
    nx.set_edge_attributes(graph, edge_distance, "distance")
    return graph
