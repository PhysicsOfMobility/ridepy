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
  typedef adjacency_list<vecS, vecS, undirectedS,
                         property<vertex_name_t, vertex_t>,
                         property<edge_weight_t, double>>
      Graph;
  typedef pair<vertex_t, vertex_t> Edge;
  typedef LRU::Cache<int, pair<vector<int>, vector<double>>> pred_cache_t;

private:
  Graph _g;
  map<vertex_t, int> vertex_label2index;
  typename boost::property_map<Graph, vertex_name_t>::type vertex2label;
  typename boost::property_map<Graph, edge_weight_t>::type edge2weight;
  vector<double> _distances;
  vector<int> _predecessors;
  vector<double> _weights;
  pred_cache_t pred_cache{
      10000}; // the cache size could be set at initialization

  void cached_dijkstra(int u_idx) {
    if (pred_cache.contains(u_idx)) {
      auto res = pred_cache.lookup(u_idx);
      this->_predecessors = res.first;
      this->_distances = res.second;
    } else {
      // not in cache, compute
      dijkstra_shortest_paths(this->_g, u_idx,
                              predecessor_map(&this->_predecessors[0])
                                  .distance_map(&this->_distances[0]));
      // insert into cache
      pred_cache.insert(u_idx,
                        make_pair(this->_predecessors, this->_distances));
    }
  }

public:
  double velocity;

  double d(vertex_t src, vertex_t target) override {
    // call dijkstra
    int src_idx = this->vertex_label2index[src];
    cached_dijkstra(src_idx);
    return this->_distances[this->vertex_label2index[target]];
  }

  double t(vertex_t src, vertex_t target) override {
    return this->d(src, target) / this->velocity;
  }

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

  pair<vertex_t, double> interp_time(vertex_t u, vertex_t v,
                                     double time_to_dest) override {
    double dist_to_dest = time_to_dest * (this->velocity);
    auto [w, d] = this->interp_dist(u, v, dist_to_dest);
    return make_pair(w, d / this->velocity);
  }

  GraphSpace(double velocity, vector<vertex_t> vertex_vec,
             vector<Edge> edge_vec)
      : GraphSpace(velocity, vertex_vec, edge_vec,
                   vector<double>(static_cast<int>(edge_vec.size()), 1)) {}

  GraphSpace(double velocity, vector<vertex_t> vertex_vec,
             vector<Edge> edge_vec, vector<double> weight_vec)
      : TransportSpace<vertex_t>(),
        velocity(velocity), _g{vertex_vec.size()}, vertex2label{get(vertex_name,
                                                                    _g)},
        _distances(static_cast<int>(vertex_vec.size())),
        _predecessors(static_cast<int>(vertex_vec.size())),
        _weights{weight_vec}, edge2weight{get(edge_weight, _g)} {
    // this->vertex2label = get(vertex_name, this->_g);
    // add vertex properties
    int idx = 0;
    for (auto &vlabel : vertex_vec) {
      this->vertex_label2index[vlabel] = idx;
      put(this->vertex2label, idx, vlabel);
      idx++;
    }
    // add edges
    idx = 0;
    for (auto &e : edge_vec) {
      property<edge_weight_t, double> edge_property(weight_vec[idx]);
      add_edge(this->vertex_label2index[e.first],
               this->vertex_label2index[e.second], edge_property, this->_g);
      idx++;
    }
  }
  ~GraphSpace() {}

  void print_shortest_paths(vertex_t src) {
    // call dijkstra
    int src_idx = this->vertex_label2index[src];

    dijkstra_shortest_paths(this->_g, src_idx,
                            predecessor_map(&this->_predecessors[0])
                                .distance_map(&this->_distances[0]));

    // print the dijkstra shortest paths
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
    // print the vertices
    for (auto vp = vertices(this->_g); vp.first != vp.second; ++vp.first) {
      cout << "vertex: " << *vp.first
           << ", label:" << this->vertex2label[*vp.first] << endl;
    }
    // print the edge_vec
    for (auto [first, last] = edges(this->_g); first != last; ++first) {
      cout << "Edge(" << this->vertex2label[source(*first, this->_g)] << ","
           << this->vertex2label[target(*first, this->_g)] << ")" << endl;
    }
  }

  vector<vertex_t> get_vertices() {
    vector<vertex_t> v;
    for (auto vp = vertices(this->_g); vp.first != vp.second; ++vp.first)
      v.push_back(this->vertex2label[*vp.first]);
    return v;
  }
  vector<Edge> get_edges() {
    vector<Edge> e;
    for (auto [first, last] = edges(this->_g); first != last; ++first) {
      e.push_back(make_pair(this->vertex2label[source(*first, this->_g)],
                            this->vertex2label[target(*first, this->_g)]));
    }
    return e;
  }
  vector<double> get_weights() {
    vector<double> w;
    for (auto [first, last] = edges(this->_g); first != last; ++first) {
      w.push_back(get(this->edge2weight, *first));
    }
    return w;
  }
};

} // namespace ridepy

#endif
