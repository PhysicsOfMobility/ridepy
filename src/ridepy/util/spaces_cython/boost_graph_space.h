#ifndef BOOST_GRAPH_SPACE_H
#define BOOST_GRAPH_SPACE_H
#include "lru/lru.hpp"
#include <boost/graph/adjacency_list.hpp>
#include <boost/graph/dijkstra_shortest_paths.hpp>
#include <boost/graph/graph_traits.hpp>
#include <boost/property_map/property_map.hpp>
#include <iostream>
#include <utility>

#include "cspaces.h"

using namespace std;
using namespace boost;

namespace ridepy {

template <typename vertex_t>
class GraphSpace : public TransportSpace<vertex_t> {
  // Graph of the adjacency_list type
  typedef adjacency_list<
    vecS,  // OutEdgeList: std::vector
    vecS,  // VertexList: std::vector
    undirectedS,  // Directed: Undirected graph
    property<vertex_name_t, vertex_t>, // Vertex properties: vertex_t, tagged with vertex_name_t, to store the Python node IDs
    property<edge_weight_t, double>  // Edge properties: double, tagged with edge_weight_t to store the edge lengths
   > Graph;

   // Python node ID edge
  typedef pair<vertex_t, vertex_t> Edge;

  // LRU cache for predecessor and distance vectors
  typedef LRU::Cache<int, pair<vector<int>, vector<double>>> pred_cache_t;

  // Boost graph object
  Graph _g;

  // Vertex labels are the templated-type node IDs as used in the simulation space
  // Vertex indices are the integer node IDs used by the boost graph object
  map<vertex_t, int> vertex_label2index;

  // Vertex and edge properties are stored in property maps
  // TODO Why do we need those, isn't this already in the adjacency list?
  // Vertex names/labels are the vertex IDs coming from Python
  typename boost::property_map<Graph, vertex_name_t>::type vertex2label;
  // For edges, their weight (length/distance) is stored
  typename boost::property_map<Graph, edge_weight_t>::type edge2weight;

  vector<int> _predecessors;
  vector<double> _distances;
  vector<double> _weights;

  pred_cache_t pred_cache{
      10000}; // the cache size could be set at initialization

  /**
    * Compute the shortest paths from a source node to all other nodes in the
    * graph and store the results in the predecessor and distance vectors
    *
    * @param u_idx index of the source node
    */
  void cached_dijkstra(int u_idx) {
    if (pred_cache.contains(u_idx)) {
      auto res = pred_cache.lookup(u_idx);
      this->_predecessors = res.first;
      this->_distances = res.second;
    } else {
      // Not in cache, compute
      dijkstra_shortest_paths(
        this->_g,  // Graph
        u_idx,  // Source node
        predecessor_map(&this->_predecessors[0])  // Named parameter: predecessor_map
          .distance_map(&this->_distances[0])  // Named parameter: distance_map
      );
      // Insert into cache
      pred_cache.insert(u_idx, make_pair(this->_predecessors, this->_distances));
    }
  }

public:
  double velocity;

  /**
   * Constructor taking the velocity and vectors of vertices and unweighted edges
   * (all edges will have weight 1)
   *
   * @param velocity vehicle velocity
   * @param vertex_vec vector of vertex Python node IDs
   * @param edge_vec vector of Python node ID pairs representing edges
   */
  GraphSpace(double velocity, vector<vertex_t> vertex_vec,
             vector<Edge> edge_vec)
      : GraphSpace(velocity, vertex_vec, edge_vec,
                   vector<double>(static_cast<int>(edge_vec.size()), 1)) {}

  /**
   * Constructor taking the velocity and vectors of vertices, edges, and
   * float edge weights
   *
   * @param velocity vehicle velocity
   * @param vertex_vec vector of vertex Python node IDs
   * @param edge_vec vector of Python node ID pairs representing edges
   * @param weight_vec vector of edge weights
   */
  GraphSpace(double velocity, vector<vertex_t> vertex_vec,
             vector<Edge> edge_vec, vector<double> weight_vec)
      : TransportSpace<vertex_t>(),
        velocity(velocity),
        _g{vertex_vec.size()},
        vertex2label{get(vertex_name, _g)},
        _distances(static_cast<int>(vertex_vec.size())),
        _predecessors(static_cast<int>(vertex_vec.size())),
        _weights{weight_vec},
        edge2weight{get(edge_weight, _g)} {
    // this->vertex2label = get(vertex_name, this->_g);

    // Add vertex labels
    int idx = 0;
    for (auto &vlabel : vertex_vec) {
      this->vertex_label2index[vlabel] = idx;
      put(this->vertex2label, idx, vlabel);
      idx++;
    }

    // Add edges
    idx = 0;
    for (auto &e : edge_vec) {
      property<edge_weight_t, double> edge_property(weight_vec[idx]);
      add_edge(
        this->vertex_label2index[e.first],
        this->vertex_label2index[e.second],
        edge_property,
        this->_g
      );
      idx++;
    }
  }

  /**
   * Destructor
   */
  ~GraphSpace() {}

  /**
   * Distance between to vertices by node ID
   *
   * @param src source Python node ID
   * @param target target Python node ID
   * @return distance between the two nodes
   */
  double d(vertex_t src, vertex_t target) override {
    // Get the index of the source node
    int src_idx = this->vertex_label2index[src];
    // Call dijkstra on the source node
    cached_dijkstra(src_idx);
    // Return the distance to the target node
    return this->_distances[this->vertex_label2index[target]];
  }

  /**
   * Time to travel between two vertices by node ID
   *
   * @param src source Python node ID
   * @param target target Python node ID
   * @return time to travel between the two nodes
   */
  double t(vertex_t src, vertex_t target) override {
    return this->d(src, target) / this->velocity;
  }

  // Interpolate between two vertices by node ID and distance
  // I.e., find the vertex and remaining distance to that vertex that is
  // dist_to_dest away from the target vertex.
  pair<vertex_t, double> interp_dist(vertex_t u, vertex_t v,
                                     double dist_to_dest) override {
    if (u == v)
      return make_pair(v, 0);
    // call dijkstra
    int u_idx = this->vertex_label2index[u];
    const int v_idx = this->vertex_label2index[v];
    cached_dijkstra(u_idx);

    vertex_t predecessor, current_node = v_idx;
    double dist_from_dest = 0;
    double current_edge_weight = 0;
    while (current_node != u_idx) {
      predecessor = this->_predecessors[current_node];
      auto [e, is_edge] = edge(current_node, predecessor, this->_g);
      current_edge_weight = get(this->edge2weight, e);
      dist_from_dest += current_edge_weight;
      if (dist_from_dest >= dist_to_dest)
        break;
      current_node = predecessor;
    }

    if (dist_from_dest > dist_to_dest) {
      return make_pair(get(this->vertex2label, current_node),
                       dist_to_dest - dist_from_dest + current_edge_weight);
    } else
      return make_pair(get(this->vertex2label, predecessor), 0);
  }

  // Interpolate between two vertices by node ID and time
  pair<vertex_t, double> interp_time(vertex_t u, vertex_t v,
                                     double time_to_dest) override {
    // Compute remaining distance to destination and call interp_dist
    double dist_to_dest = time_to_dest * (this->velocity);
    auto [w, d] = this->interp_dist(u, v, dist_to_dest);
    return make_pair(w, d / this->velocity);
  }

  /**
    * Return a vector of all vertices in the graph
    * @return vector of vertex Python node IDs
    */
  vector<vertex_t> get_vertices() {
    vector<vertex_t> v;
    for (auto vp = vertices(this->_g); vp.first != vp.second; ++vp.first)
      v.push_back(this->vertex2label[*vp.first]);
    return v;
  }

  /**
    * Return a vector of all edges in the graph
    * @return vector of Python node ID pairs
    */
  vector<Edge> get_edges() {
    vector<Edge> e;
    for (auto [first, last] = edges(this->_g); first != last; ++first) {
      e.push_back(make_pair(this->vertex2label[source(*first, this->_g)],
                            this->vertex2label[target(*first, this->_g)]));
    }
    return e;
  }

  /**
    * Return a vector of all edge weights in the graph
    * @return vector of edge weights
    */
  vector<double> get_weights() {
    vector<double> w;
    for (auto [first, last] = edges(this->_g); first != last; ++first) {
      w.push_back(get(this->edge2weight, *first));
    }
    return w;
  }

  void print_shortest_paths(vertex_t src) {
    // Call dijkstra
    int src_idx = this->vertex_label2index[src];

    dijkstra_shortest_paths(this->_g, src_idx,
                            predecessor_map(&this->_predecessors[0])
                                .distance_map(&this->_distances[0]));

    // Print the dijkstra shortest paths
    cout << "Shortest paths from node " << this->vertex2label[src_idx] << ":"
         << endl;
    for (auto vp = vertices(this->_g); vp.first != vp.second; ++vp.first) {
      int vertex = *(vp.first);
      int vertex_label = get(this->vertex2label, vertex);
      cout << "to " << vertex_label << ": " << this->_distances[vertex] << endl;
      cout << "Path: ";
      int j = vertex;
      while (j != src_idx) {
        cout << this->vertex2label[j] << ", ";
        j = this->_predecessors[j];
      }
      cout << this->vertex2label[src_idx] << endl;
    }
  }

  void print_vertices_and_edges() {
    // Print the vertices
    for (auto vp = vertices(this->_g); vp.first != vp.second; ++vp.first) {
      cout << "vertex: " << *vp.first
           << ", label:" << this->vertex2label[*vp.first] << endl;
    }
    // Print the edge_vec
    for (auto [first, last] = edges(this->_g); first != last; ++first) {
      cout << "Edge(" << this->vertex2label[source(*first, this->_g)] << ","
           << this->vertex2label[target(*first, this->_g)] << ")" << endl;
    }
  }
};

} // namespace ridepy

#endif
