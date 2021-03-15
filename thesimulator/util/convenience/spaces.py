import networkx as nx
from typing import Tuple


def make_nx_grid(
    dim: Tuple[int, int] = (3, 3),
    periodic: bool = False,
    edge_distance: float = 1,
) -> nx.Graph:
    """
    Return a lattice `nx.Graph`

    Use in conjunction with `spaces.Graph` or `spaces_cython.Graph` like
    ```py
    Graph.from_nx(make_nx_grid())
    ```

    Parameters
    ----------
    dim
        dimensions of the graph: (n, k) for n x k vertices
    periodic
        periodic boundaries
    edge_distance
        edge weight

    Returns
    -------
    graph
    """
    graph = nx.grid_graph(dim=dim, periodic=periodic)
    nx.set_edge_attributes(graph, edge_distance, "distance")
    graph = nx.relabel.convert_node_labels_to_integers(
        graph, label_attribute="location"
    )
    return graph


def make_nx_cycle_graph(
    n_nodes: int = 10,
    edge_distance: float = 1,
) -> nx.Graph:
    """
    Return a cyclic `nx.Graph`

    Use in conjunction with `spaces.Graph` or `spaces_cython.Graph` like
    ```py
    Graph.from_nx(make_nx_cycle_graph())
    ```

    Parameters
    ----------
    n_nodes
        number of vertices to generate
    edge_distance
        edge weight

    Returns
    -------
    graph
    """
    graph = nx.generators.classic.cycle_graph(n=n_nodes)
    nx.set_edge_attributes(graph, edge_distance, "distance")
    return graph
