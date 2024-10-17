#include "boost_graph_space.h"

// Note that the code in this file is just for testing purposes,
// it's not actually used by ridepy.
using namespace ridepy;

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
  const double velocity = 1.0;

  std::vector<double> weights{9, 9, 9, 9, 9};
  GraphSpace<int> g{velocity, vertices, edges, weights};
//  g.print_vertices_and_edges();
//  g.print_shortest_paths(102);
//  g.print_shortest_paths(103);

  for (auto &src : vertices) {
    for (auto &target : vertices) {
      g.d(src, target);
    }
    }
    }
//      std::cout << "d(" << src << "," << target
//                << "): " << g.d(src, target) << std::endl;
//    }
//  }
//  for (auto dtd = 0; dtd < 18; dtd++) {
//    auto [v, rest] = g.interp_dist(102, 104, dtd);
//    std::cout << "interpolate(102, 104, " << dtd << "): " << v << "," << rest
//              << std::endl;
//  }
//  }