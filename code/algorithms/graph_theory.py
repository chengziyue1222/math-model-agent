"""
图论工具箱
==========
包含：Dijkstra最短路径、Floyd最短路径、最小生成树、最大流、关键路径(PERT)、TSP

参考：Algorithms_MathModels/GraphTheory(图论)/
"""

import numpy as np
from typing import Tuple, Dict, List, Optional
from heapq import heappush, heappop


# ============================================================
# 1. Dijkstra 最短路径
# ============================================================
def dijkstra(adj_matrix: np.ndarray, source: int) -> Tuple[np.ndarray, np.ndarray]:
    """
    Dijkstra 最短路径算法

    Parameters
    ----------
    adj_matrix : np.ndarray
        邻接矩阵 (n, n), inf 表示无边
    source : int
        源节点 (0-indexed)

    Returns
    -------
    dist : np.ndarray
        从源到各点的最短距离
    prev : np.ndarray
        前驱节点 (用于重建路径)
    """
    n = adj_matrix.shape[0]
    dist = np.full(n, np.inf)
    prev = np.full(n, -1, dtype=int)
    visited = np.zeros(n, bool)
    dist[source] = 0

    for _ in range(n):
        u = np.argmin(dist[~visited]) if not visited.all() else -1
        # 找未访问的最小距离节点
        min_d = np.inf
        u = -1
        for i in range(n):
            if not visited[i] and dist[i] < min_d:
                min_d = dist[i]
                u = i
        if u == -1:
            break
        visited[u] = True
        for v in range(n):
            if not visited[v] and adj_matrix[u, v] < np.inf:
                new_dist = dist[u] + adj_matrix[u, v]
                if new_dist < dist[v]:
                    dist[v] = new_dist
                    prev[v] = u

    return dist, prev


def get_path(prev: np.ndarray, target: int) -> List[int]:
    """从 prev 数组重建路径"""
    path = []
    while target != -1:
        path.append(target)
        target = prev[target]
    return path[::-1]


# ============================================================
# 2. Floyd 最短路径 (所有节点对)
# ============================================================
def floyd(adj_matrix: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    Floyd-Warshall 全源最短路径

    Parameters
    ----------
    adj_matrix : np.ndarray
        邻接矩阵 (n, n)

    Returns
    -------
    dist : np.ndarray
        最短距离矩阵 (n, n)
    next_node : np.ndarray
        路径重建矩阵
    """
    n = adj_matrix.shape[0]
    dist = adj_matrix.copy()
    next_node = np.full((n, n), -1, dtype=int)

    for i in range(n):
        for j in range(n):
            if i != j and dist[i, j] < np.inf:
                next_node[i, j] = j

    for k in range(n):
        for i in range(n):
            for j in range(n):
                if dist[i, k] + dist[k, j] < dist[i, j]:
                    dist[i, j] = dist[i, k] + dist[k, j]
                    next_node[i, j] = next_node[i, k]

    return dist, next_node


def floyd_get_path(next_node: np.ndarray, i: int, j: int) -> List[int]:
    """Floyd 路径重建"""
    if next_node[i, j] == -1:
        return []
    path = [i]
    while i != j:
        i = next_node[i, j]
        path.append(i)
    return path


# ============================================================
# 3. 最小生成树 (Prim / Kruskal)
# ============================================================
def prim_mst(adj_matrix: np.ndarray) -> Tuple[List[Tuple], float]:
    """
    Prim 最小生成树

    Parameters
    ----------
    adj_matrix : np.ndarray
        邻接矩阵 (n, n), inf 表示无边

    Returns
    -------
    edges : list of (u, v, weight)
        最小生成树的边
    total_weight : float
        总权重
    """
    n = adj_matrix.shape[0]
    in_mst = np.zeros(n, bool)
    key = np.full(n, np.inf)
    parent = np.full(n, -1, dtype=int)
    key[0] = 0

    edges = []
    total = 0.0

    for _ in range(n):
        u = -1
        for i in range(n):
            if not in_mst[i] and (u == -1 or key[i] < key[u]):
                u = i
        if u == -1:
            break
        in_mst[u] = True
        if parent[u] != -1:
            edges.append((parent[u], u, adj_matrix[parent[u], u]))
            total += adj_matrix[parent[u], u]

        for v in range(n):
            if not in_mst[v] and adj_matrix[u, v] < key[v]:
                key[v] = adj_matrix[u, v]
                parent[v] = u

    return edges, total


# ============================================================
# 4. 最大流 (Ford-Fulkerson)
# ============================================================
def max_flow(capacity: np.ndarray, source: int, sink: int) -> Tuple[float, np.ndarray]:
    """
    Ford-Fulkerson 最大流算法 (BFS 增广路径)

    Parameters
    ----------
    capacity : np.ndarray
        容量矩阵 (n, n)
    source : int
        源节点
    sink : int
        汇节点

    Returns
    -------
    max_flow_value : float
        最大流量
    flow_matrix : np.ndarray
        流量分配矩阵
    """
    n = capacity.shape[0]
    flow = np.zeros((n, n))
    residual = capacity.copy()

    max_flow_val = 0

    while True:
        # BFS 找增广路径
        parent = np.full(n, -1, dtype=int)
        queue = [source]
        parent[source] = source

        while queue and parent[sink] == -1:
            u = queue.pop(0)
            for v in range(n):
                if parent[v] == -1 and residual[u, v] > 0:
                    parent[v] = u
                    queue.append(v)

        if parent[sink] == -1:
            break

        # 找瓶颈
        path_flow = np.inf
        v = sink
        while v != source:
            u = parent[v]
            path_flow = min(path_flow, residual[u, v])
            v = u

        # 更新残余图和流量
        v = sink
        while v != source:
            u = parent[v]
            residual[u, v] -= path_flow
            residual[v, u] += path_flow
            flow[u, v] += path_flow
            v = u

        max_flow_val += path_flow

    return max_flow_val, flow


# ============================================================
# 5. 关键路径 (PERT)
# ============================================================
def critical_path(activities: List[Dict]) -> Dict:
    """
    关键路径法 (CPM/PERT)

    Parameters
    ----------
    activities : list of dict
        每个活动包含: 'name', 'duration', 'predecessors'
        predecessors 是前驱活动名称列表

    Returns
    -------
    dict : 关键路径、总工期、各活动的时间参数
    """
    # 构建图
    names = [a['name'] for a in activities]
    n = len(names)
    name_to_idx = {name: i for i, name in enumerate(names)}

    duration = np.array([a['duration'] for a in activities])
    successors = [[] for _ in range(n)]
    in_degree = np.zeros(n, int)

    for i, a in enumerate(activities):
        for pred in a.get('predecessors', []):
            j = name_to_idx[pred]
            successors[j].append(i)
            in_degree[i] += 1

    # 正推: 最早开始/完成
    ES = np.zeros(n)  # Earliest Start
    EF = np.zeros(n)  # Earliest Finish
    order = []
    queue = [i for i in range(n) if in_degree[i] == 0]

    while queue:
        u = queue.pop(0)
        order.append(u)
        EF[u] = ES[u] + duration[u]
        for v in successors[u]:
            ES[v] = max(ES[v], EF[u])
            in_degree[v] -= 1
            if in_degree[v] == 0:
                queue.append(v)

    # 逆推: 最晚开始/完成
    project_duration = max(EF)
    LS = np.full(n, project_duration)  # Latest Start
    LF = np.full(n, project_duration)  # Latest Finish

    for u in reversed(order):
        LF[u] = min([LS[v] for v in successors[u]], default=project_duration)
        LS[u] = LF[u] - duration[u]

    # 总浮动时间
    TF = LS - ES  # Total Float
    critical = np.abs(TF) < 1e-10

    return {
        'project_duration': project_duration,
        'ES': ES, 'EF': EF, 'LS': LS, 'LF': LF,
        'total_float': TF,
        'critical': critical,
        'critical_path': [names[i] for i in range(n) if critical[i]],
        'names': names
    }


# ============================================================
# 使用示例
# ============================================================
def example():
    """图论示例"""
    # 示例1: Dijkstra
    print("=" * 60)
    print("示例1: Dijkstra 最短路径")
    print("=" * 60)
    INF = np.inf
    adj = np.array([
        [0,   10,  INF, INF, 5],
        [INF, 0,   1,   INF, 2],
        [INF, INF, 0,   4,   INF],
        [7,   INF, INF, 0,   INF],
        [INF, 3,   9,   2,   0],
    ])
    dist, prev = dijkstra(adj, 0)
    for i in range(5):
        path = get_path(prev, i)
        print(f"  0 → {i}: 距离={dist[i]:.0f}, 路径={'→'.join(map(str, path))}")

    # 示例2: 最大流
    print("\n" + "=" * 60)
    print("示例2: 最大流")
    print("=" * 60)
    cap = np.array([
        [0, 16, 13, 0, 0, 0],
        [0, 0, 10, 12, 0, 0],
        [0, 4, 0, 0, 14, 0],
        [0, 0, 9, 0, 0, 20],
        [0, 0, 0, 7, 0, 4],
        [0, 0, 0, 0, 0, 0],
    ])
    mf, flow = max_flow(cap, 0, 5)
    print(f"  最大流量: {mf}")

    # 示例3: 关键路径
    print("\n" + "=" * 60)
    print("示例3: 关键路径 (PERT)")
    print("=" * 60)
    activities = [
        {'name': 'A', 'duration': 4, 'predecessors': []},
        {'name': 'B', 'duration': 3, 'predecessors': []},
        {'name': 'C', 'duration': 2, 'predecessors': ['A']},
        {'name': 'D', 'duration': 5, 'predecessors': ['A']},
        {'name': 'E', 'duration': 3, 'predecessors': ['B', 'C']},
        {'name': 'F', 'duration': 2, 'predecessors': ['D', 'E']},
    ]
    result = critical_path(activities)
    print(f"  总工期: {result['project_duration']}")
    print(f"  关键路径: {' → '.join(result['critical_path'])}")


if __name__ == "__main__":
    example()
