#ifndef BOOST_GRAPH_SPACE_H
#define BOOST_GRAPH_SPACE_H
#include <iostream>
#include <boost/graph/graph_traits.hpp>
#include <boost/graph/adjacency_list.hpp>
#include <boost/property_map/property_map.hpp>
#include <boost/graph/dijkstra_shortest_paths.hpp>

#include "cspaces.h"

using namespace std;
using namespace boost;


namespace cstuff {
    template<typename vertex_t>
    class GraphSpace : public TransportSpace<vertex_t> {
        typedef adjacency_list <vecS, vecS, undirectedS, property<vertex_name_t, vertex_t>, property<edge_weight_t, int>>
                Graph;
        typedef pair <vertex_t, vertex_t> Edge;
    private:
        Graph _g;
        map<vertex_t, int> vertex_label2index;
        typename boost::property_map<Graph, vertex_name_t>::type vertex2label;
        typename boost::property_map<Graph, edge_weight_t>::type edge2weight;
        vector<int> _distances, _predecessors;
        vector<double> _weights;

    public:
        double velocity;
        double d(vertex_t src, vertex_t target) override {
            // call dijkstra
            int src_idx = this->vertex_label2index[src];
            dijkstra_shortest_paths(this->_g, src_idx, predecessor_map(&this->_predecessors[0]).distance_map(
                    &this->_distances[0]));
            return this->_distances[this->vertex_label2index[target]];
        }

        double t(vertex_t src, vertex_t target) override {
            return this->d(src, target) / this->velocity;
        }

        pair<vertex_t, double> interp_dist(vertex_t u, vertex_t v, double dist_to_dest) override {
            if (u == v) return make_pair(v, 0);
            // call dijkstra
            int u_idx = this->vertex_label2index[u];
            const int v_idx = this->vertex_label2index[v];
            dijkstra_shortest_paths(this->_g, u_idx, predecessor_map(&this->_predecessors[0]).distance_map(
                    &this->_distances[0]));

            vertex_t predecessor, current_node = v_idx;
            double dist_from_dest, current_edge_weight{0};
            while (current_node != u_idx) {
                predecessor = this->_predecessors[current_node];
                auto[e, is_edge] = edge(current_node, predecessor, this->_g);
                current_edge_weight = get(this->edge2weight, e);
                dist_from_dest += current_edge_weight;
                if (dist_from_dest >= dist_to_dest) break;
                current_node = predecessor;
            }

            if (dist_from_dest > dist_to_dest) {
                return make_pair(get(this->vertex2label, current_node),
                                 dist_to_dest - dist_from_dest + current_edge_weight);
            } else return make_pair(get(this->vertex2label, predecessor), 0);
        }

        pair<vertex_t, double> interp_time(vertex_t u, vertex_t v, double time_to_dest) override {
            double dist_to_dest = time_to_dest * (this->velocity);
            return this->interp_dist(u, v, dist_to_dest);
        }

        GraphSpace(double velocity, vector <vertex_t> vertex_vec, vector <Edge> edge_vec)
                : GraphSpace(velocity, vertex_vec, edge_vec, vector < double > {edge_vec.size(), 1}) {}

        GraphSpace(double velocity, vector <vertex_t> vertex_vec, vector <Edge> edge_vec, vector<double> weight_vec)
                : _g{vertex_vec.size()}, velocity{velocity}, vertex2label{get(vertex_name, _g)},
                  _distances{static_cast<int>(vertex_vec.size())}, _predecessors{static_cast<int>(vertex_vec.size())},
                  _weights{weight_vec}, edge2weight{get(edge_weight, _g)} {
            // this->vertex2label = get(vertex_name, this->_g);
            // add vertex properties
            int idx = 0;
            for (auto &vlabel: vertex_vec) {
                this->vertex_label2index[vlabel] = idx;
                this->vertex2label[idx] = vlabel;

                idx++;
            }
            // add edges
            idx = 0;
            for (auto &e: edge_vec) {
                property<edge_weight_t, int> edge_property(weight_vec[idx]);
                add_edge(this->vertex_label2index[e.first], this->vertex_label2index[e.second], edge_property,
                         this->_g);
                idx++;
            }
        }

        void print_shortest_paths(vertex_t src) {
            // call dijkstra
            int src_idx = this->vertex_label2index[src];

            dijkstra_shortest_paths(this->_g, src_idx, predecessor_map(&this->_predecessors[0]).distance_map(
                    &this->_distances[0]));

            // print the dijkstra shortest paths
            cout << "Shortest paths from node " << this->vertex2label[src_idx] << ":" << endl;
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
                cout << "vertex: " << *(vp.first) << ", label:" << this->vertex2label[*(vp.first)] << endl;
            }
            // print the edge_vec
            for (auto[first, last] = edges(this->_g); first != last; ++first) {
                cout << "Edge(" << this->vertex2label[source(*first, this->_g)] << ","
                     << this->vertex2label[target(*first, this->_g)] << ")" << endl;
            }
        }
    };
}




#endif