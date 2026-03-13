# Final Work — Graph Algorithms

C++ implementation of core graph algorithms, modeled as course dependencies and campus navigation.

## Algorithms & Complexity

| Algorithm | Time | Space | Use Case |
|---|---|---|---|
| BFS | O(V+E) | O(V) | Unweighted shortest path (hop count) |
| Dijkstra | O((V+E) log V) | O(V) | Single-source weighted shortest path |
| Floyd-Warshall | O(V^3) | O(V^2) | All-pairs shortest paths |
| Topological Sort | O(V+E) | O(V) | DAG ordering (course prerequisites) |

## Build & Run

```bash
g++ -std=c++17 -O2 -o finalwork main.cpp
./finalwork
```

## Description

- Weighted graph with adjacency list representation
- 7-node graph representing course dependencies (DAG) and campus distances
- BFS for hop count, Dijkstra for weighted distances, Floyd-Warshall for all-pairs
- Topological sort via Kahn's algorithm for valid course ordering
- Shortest path reconstruction with predecessor tracking
