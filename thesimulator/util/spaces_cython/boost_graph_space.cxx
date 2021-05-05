#include "boost_graph_space.h"

int main(int, char *[]) {
  // declare graph type
  const std::vector<int> vertices{101, 102, 103, 104};
  const int num_vertices = vertices.size();
  // declare edge type (vertices are ints)
  typedef std::pair<int, int> Edge;
  // declare edge set
  const std::vector<Edge> edges{Edge(101, 102), Edge(102, 103), Edge(103, 104),
                                Edge(104, 101), Edge(101, 103)};
  const int num_edges = edges.size();

  std::vector<double> weights{9, 9, 9, 9, 9};
  GraphSpace<int> g{vertices, edges, weights};
  g.print_vertices_and_edges();
  g.print_shortest_paths(102);
  g.print_shortest_paths(103);

  for (auto &src : vertices) {
    for (auto &target : vertices) {
      std::cout << "d(" << src << "," << target
                << "): " << g.distance(src, target) << std::endl;
    }
  }
  for (auto dtd = 0; dtd < 18; dtd++) {
    auto [v, rest] = g.interpolate(102, 104, dtd);
    std::cout << "interpolate(102, 104, " << dtd << "): " << v << "," << rest
              << std::endl;
  }
}