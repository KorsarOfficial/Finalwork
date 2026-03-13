#include <iostream>
#include <vector>
#include <queue>
#include <stack>
#include <algorithm>
#include <iomanip>
#include <limits>
#include <optional>
#include <ranges>
#include <string_view>

// adj[u] = {(v, w) : edge u->v with weight w}
template<typename W = int>
struct Graph {
    int V;
    std::vector<std::vector<std::pair<int, W>>> adj;

    explicit Graph(int v) : V(v), adj(v) {}

    void add_edge(int u, int v, W w = W{1}) {
        adj[u].emplace_back(v, w);
    }

    void add_undirected(int u, int v, W w = W{1}) {
        adj[u].emplace_back(v, w);
        adj[v].emplace_back(u, w);
    }
};

// d[v] = min{d[u] + 1 : (u,v) in E}, O(V+E)
template<typename W>
[[nodiscard]] auto bfs(const Graph<W>& g, int src) -> std::vector<int> {
    std::vector<int> dist(g.V, -1);
    std::queue<int> q;
    dist[src] = 0;
    q.push(src);
    while (!q.empty()) {
        const int u = q.front();
        q.pop();
        for (const auto& [v, w] : g.adj[u]) {
            if (dist[v] == -1) {
                dist[v] = dist[u] + 1;
                q.push(v);
            }
        }
    }
    return dist;
}

// d[v] = min_{u in N(v)} (d[u] + w(u,v)), O((V+E) log V)
template<typename W>
[[nodiscard]] auto dijkstra(const Graph<W>& g, int src)
    -> std::pair<std::vector<W>, std::vector<int>> {
    constexpr W INF = std::numeric_limits<W>::max();
    std::vector<W> dist(g.V, INF);
    std::vector<int> prev(g.V, -1);
    // min-heap: (distance, vertex)
    std::priority_queue<std::pair<W, int>,
                        std::vector<std::pair<W, int>>,
                        std::greater<>> pq;
    dist[src] = W{0};
    pq.emplace(W{0}, src);
    while (!pq.empty()) {
        const auto [d, u] = pq.top();
        pq.pop();
        if (d > dist[u]) continue;
        for (const auto& [v, w] : g.adj[u]) {
            // relax: d[v] = min(d[v], d[u] + w(u,v))
            if (dist[u] + w < dist[v]) {
                dist[v] = dist[u] + w;
                prev[v] = u;
                pq.emplace(dist[v], v);
            }
        }
    }
    return {std::move(dist), std::move(prev)};
}

// reconstruct path from prev[], nullopt if unreachable
[[nodiscard]] auto reconstruct_path(const std::vector<int>& prev, int src, int dst)
    -> std::optional<std::vector<int>> {
    if (dst < 0 || dst >= static_cast<int>(prev.size())) {
        return std::nullopt;
    }
    if (dst != src && prev[dst] == -1) {
        return std::nullopt;
    }
    std::vector<int> path;
    for (int v = dst; v != -1; v = prev[v]) {
        path.push_back(v);
    }
    std::ranges::reverse(path);
    return path;
}

// dp: d^k[i][j] = min(d^{k-1}[i][j], d^{k-1}[i][k] + d^{k-1}[k][j]), O(V^3)
template<typename W>
[[nodiscard]] auto floyd_warshall(const Graph<W>& g)
    -> std::vector<std::vector<W>> {
    constexpr W INF = std::numeric_limits<W>::max();
    const int n = g.V;
    std::vector<std::vector<W>> d(n, std::vector<W>(n, INF));

    for (int i = 0; i < n; ++i) d[i][i] = W{0};
    for (int u = 0; u < n; ++u) {
        for (const auto& [v, w] : g.adj[u]) {
            d[u][v] = std::min(d[u][v], w);
        }
    }

    for (int k = 0; k < n; ++k)
        for (int i = 0; i < n; ++i)
            for (int j = 0; j < n; ++j)
                if (d[i][k] < INF && d[k][j] < INF)
                    d[i][j] = std::min(d[i][j], d[i][k] + d[k][j]);

    return d;
}

// Kahn's algorithm: O(V+E), nullopt if cycle detected
template<typename W>
[[nodiscard]] auto topological_sort(const Graph<W>& g)
    -> std::optional<std::vector<int>> {
    std::vector<int> in_deg(g.V, 0);
    for (int u = 0; u < g.V; ++u)
        for (const auto& [v, w] : g.adj[u])
            ++in_deg[v];

    std::queue<int> q;
    for (int i = 0; i < g.V; ++i)
        if (in_deg[i] == 0)
            q.push(i);

    std::vector<int> order;
    order.reserve(g.V);
    while (!q.empty()) {
        const int u = q.front();
        q.pop();
        order.push_back(u);
        for (const auto& [v, w] : g.adj[u]) {
            if (--in_deg[v] == 0) q.push(v);
        }
    }

    if (static_cast<int>(order.size()) != g.V) {
        return std::nullopt;
    }
    return order;
}

// DFS cycle detection, O(V+E)
template<typename W>
[[nodiscard]] auto has_cycle(const Graph<W>& g) -> bool {
    // 0=white, 1=gray, 2=black
    std::vector<int> color(g.V, 0);
    std::function<bool(int)> dfs = [&](int u) -> bool {
        color[u] = 1;
        for (const auto& [v, w] : g.adj[u]) {
            if (color[v] == 1) return true;
            if (color[v] == 0 && dfs(v)) return true;
        }
        color[u] = 2;
        return false;
    };
    for (int i = 0; i < g.V; ++i)
        if (color[i] == 0 && dfs(i))
            return true;
    return false;
}

// |{C : C is connected component}|, O(V+E)
template<typename W>
[[nodiscard]] auto connected_components(const Graph<W>& g) -> int {
    std::vector<bool> visited(g.V, false);
    int count = 0;
    for (int i = 0; i < g.V; ++i) {
        if (visited[i]) continue;
        ++count;
        std::queue<int> q;
        q.push(i);
        visited[i] = true;
        while (!q.empty()) {
            const int u = q.front();
            q.pop();
            for (const auto& [v, w] : g.adj[u]) {
                if (!visited[v]) {
                    visited[v] = true;
                    q.push(v);
                }
            }
        }
    }
    return count;
}

int main() {
    constexpr std::string_view names[] = {
        "Math", "LinAlg", "Probability",
        "ML", "Optimization", "DeepLearning", "Thesis"
    };
    constexpr int V = 7;

    // --- DAG: 0:Math->1:LinAlg->3:ML, 0->2:Prob->3, 1->4:Opt, 3->5:DL, 4->5, 5->6:Thesis ---
    Graph<> dag(V);
    dag.add_edge(0, 1);
    dag.add_edge(0, 2);
    dag.add_edge(1, 3);
    dag.add_edge(2, 3);
    dag.add_edge(1, 4);
    dag.add_edge(3, 5);
    dag.add_edge(4, 5);
    dag.add_edge(5, 6);

    std::cout << "=== Topological Sort ===\n";
    if (const auto topo = topological_sort(dag)) {
        std::cout << "Order: ";
        for (int i = 0; i < static_cast<int>(topo->size()); ++i) {
            if (i) std::cout << " -> ";
            std::cout << names[(*topo)[i]];
        }
        std::cout << "\n\n";
    } else {
        std::cout << "Cycle detected!\n\n";
    }

    std::cout << "has_cycle(dag) = " << std::boolalpha << has_cycle(dag) << "\n\n";

    // --- Weighted undirected graph ---
    Graph<int> wg(V);
    wg.add_undirected(0, 1, 4);
    wg.add_undirected(0, 2, 2);
    wg.add_undirected(1, 2, 5);
    wg.add_undirected(1, 3, 10);
    wg.add_undirected(2, 3, 3);
    wg.add_undirected(2, 4, 8);
    wg.add_undirected(3, 4, 7);
    wg.add_undirected(3, 5, 6);
    wg.add_undirected(4, 5, 1);
    wg.add_undirected(4, 6, 9);
    wg.add_undirected(5, 6, 2);

    // BFS: d[v] = min hops from 0
    std::cout << "=== BFS from node 0 ===\n";
    const auto bfs_dist = bfs(wg, 0);
    for (int i = 0; i < V; ++i)
        std::cout << "  " << names[i] << ": " << bfs_dist[i] << " hops\n";
    std::cout << "\n";

    // Dijkstra: d[v] = min_{path} sum(w)
    std::cout << "=== Dijkstra from node 0 ===\n";
    const auto [dijk_dist, dijk_prev] = dijkstra(wg, 0);
    constexpr int INF = std::numeric_limits<int>::max();
    for (int i = 0; i < V; ++i) {
        std::cout << "  " << names[i] << ": ";
        if (dijk_dist[i] == INF) std::cout << "INF";
        else std::cout << dijk_dist[i];
        std::cout << "\n";
    }
    std::cout << "\n";

    // path reconstruction: 0 -> 6
    std::cout << "=== Shortest path 0 -> 6 ===\n";
    if (const auto path = reconstruct_path(dijk_prev, 0, 6)) {
        std::cout << "  path: ";
        for (int i = 0; i < static_cast<int>(path->size()); ++i) {
            if (i) std::cout << " -> ";
            std::cout << names[(*path)[i]];
        }
        std::cout << " (cost=" << dijk_dist[6] << ")\n\n";
    } else {
        std::cout << "  unreachable\n\n";
    }

    // Floyd-Warshall: d[i][j] = min_k (d[i][k] + d[k][j])
    std::cout << "=== Floyd-Warshall ===\n";
    auto fw = floyd_warshall(wg);
    std::cout << std::setw(14) << " ";
    for (int j = 0; j < V; ++j)
        std::cout << std::setw(6) << names[j];
    std::cout << "\n";
    for (int i = 0; i < V; ++i) {
        std::cout << std::setw(14) << names[i];
        for (int j = 0; j < V; ++j) {
            if (fw[i][j] >= INF) std::cout << std::setw(6) << "INF";
            else std::cout << std::setw(6) << fw[i][j];
        }
        std::cout << "\n";
    }

    std::cout << "\nconnected_components(wg) = " << connected_components(wg) << "\n";

    // --- Interactive menu ---
    std::cout << "\n=== Interactive Menu ===\n";
    int choice = -1;
    while (choice != 0) {
        std::cout << "\n1) BFS  2) Dijkstra  3) Floyd-Warshall  4) Topo sort  "
                     "5) Has cycle  6) Components  0) Exit\n> ";
        std::cin >> choice;
        switch (choice) {
            case 1: {
                int src;
                std::cout << "src: ";
                std::cin >> src;
                const auto d = bfs(wg, src);
                for (int i = 0; i < V; ++i)
                    std::cout << "  " << names[i] << ": " << d[i] << "\n";
                break;
            }
            case 2: {
                int src, dst;
                std::cout << "src dst: ";
                std::cin >> src >> dst;
                const auto [dd, pp] = dijkstra(wg, src);
                std::cout << "  dist=" << dd[dst] << "\n";
                if (const auto p = reconstruct_path(pp, src, dst)) {
                    std::cout << "  path: ";
                    for (int i = 0; i < static_cast<int>(p->size()); ++i) {
                        if (i) std::cout << "->";
                        std::cout << names[(*p)[i]];
                    }
                    std::cout << "\n";
                }
                break;
            }
            case 3: {
                auto m = floyd_warshall(wg);
                for (int i = 0; i < V; ++i) {
                    for (int j = 0; j < V; ++j)
                        std::cout << std::setw(6) << (m[i][j] >= INF ? -1 : m[i][j]);
                    std::cout << "\n";
                }
                break;
            }
            case 4: {
                if (const auto t = topological_sort(dag)) {
                    for (const int x : *t) std::cout << names[x] << " ";
                    std::cout << "\n";
                } else {
                    std::cout << "cycle\n";
                }
                break;
            }
            case 5:
                std::cout << std::boolalpha << has_cycle(dag) << "\n";
                break;
            case 6:
                std::cout << connected_components(wg) << "\n";
                break;
            case 0:
                break;
            default:
                std::cout << "invalid\n";
        }
    }

    return 0;
}
