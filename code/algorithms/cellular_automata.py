"""
元胞自动机工具箱
================
包含：生命游戏、森林火灾、扩散聚集(DLA)、初等元胞自动机、SIRS 模型

参考：Algorithms_MathModels/CellularAutomata元胞向量机/
"""

import numpy as np
from typing import Tuple, Dict, Optional, List
import matplotlib.pyplot as plt


# ============================================================
# 1. 生命游戏 (Game of Life)
# ============================================================
class GameOfLife:
    """
    Conway 生命游戏

    规则：
    - 活细胞周围 2-3 个邻居 → 存活
    - 活细胞周围 <2 或 >3 个邻居 → 死亡
    - 死细胞周围恰好 3 个邻居 → 复活
    """

    def __init__(self, size: Tuple[int, int] = (50, 50)):
        self.h, self.w = size
        self.grid = np.zeros((self.h, self.w), dtype=int)
        self.history = []

    def random_init(self, density: float = 0.3):
        """随机初始化"""
        self.grid = (np.random.rand(self.h, self.w) < density).astype(int)
        self.history = [self.grid.copy()]

    def add_pattern(self, pattern: np.ndarray, pos: Tuple[int, int] = (10, 10)):
        """添加预设图案"""
        r, c = pos
        h, w = pattern.shape
        self.grid[r:r+h, c:c+w] = pattern

    def step(self) -> np.ndarray:
        """执行一步"""
        from scipy.signal import convolve2d
        kernel = np.array([[1,1,1],[1,0,1],[1,1,1]])
        neighbors = convolve2d(self.grid, kernel, mode='same', boundary='wrap')
        # 规则
        new_grid = np.zeros_like(self.grid)
        new_grid[(self.grid == 1) & ((neighbors == 2) | (neighbors == 3))] = 1
        new_grid[(self.grid == 0) & (neighbors == 3)] = 1
        self.grid = new_grid
        self.history.append(self.grid.copy())
        return self.grid

    def run(self, n_steps: int = 100) -> np.ndarray:
        """运行多步"""
        for _ in range(n_steps):
            self.step()
        return self.grid

    def plot(self, step: int = -1):
        """可视化"""
        plt.figure(figsize=(8, 8))
        plt.imshow(self.history[step], cmap='binary')
        plt.title(f'Game of Life - Step {step}')
        plt.show()


# ============================================================
# 2. 森林火灾模型 (Forest Fire)
# ============================================================
class ForestFire:
    """
    森林火灾元胞自动机

    状态: 0=空地, 1=树木, 2=燃烧中
    规则:
    - 燃烧 → 空地
    - 树木 + 邻居燃烧 → 燃烧
    - 空地 → 以概率 p 长出树木
    - 树木 → 以概率 f 自燃
    """

    def __init__(self, size: Tuple[int, int] = (100, 100),
                 p: float = 0.01, f: float = 0.0001):
        self.h, self.w = size
        self.p = p  # 生长概率
        self.f = f  # 自燃概率
        self.grid = np.ones((self.h, self.w), dtype=int)  # 初始全是树
        self.history = []

    def step(self) -> np.ndarray:
        new_grid = self.grid.copy()

        # 燃烧中 → 空地
        new_grid[self.grid == 2] = 0

        # 树木被邻居点燃
        burning = (self.grid == 2)
        from scipy.signal import convolve2d
        kernel = np.array([[0,1,0],[1,0,1],[0,1,0]])
        neighbor_burning = convolve2d(burning.astype(int), kernel, mode='same', boundary='wrap')
        ignite = (self.grid == 1) & (neighbor_burning > 0)
        new_grid[ignite] = 2

        # 自燃
        spontaneous = (self.grid == 1) & (np.random.rand(self.h, self.w) < self.f)
        new_grid[spontaneous] = 2

        # 生长
        grow = (self.grid == 0) & (np.random.rand(self.h, self.w) < self.p)
        new_grid[grow] = 1

        self.grid = new_grid
        self.history.append(self.grid.copy())
        return self.grid

    def run(self, n_steps: int = 100):
        for _ in range(n_steps):
            self.step()
        return self.grid


# ============================================================
# 3. 初等元胞自动机 (Elementary CA)
# ============================================================
class ElementaryCA:
    """
    一维初等元胞自动机 (Wolfram 规则)

    支持全部 256 种规则
    """

    def __init__(self, rule: int = 30, size: int = 101):
        self.rule = rule
        self.size = size
        self.state = np.zeros(size, dtype=int)
        self.state[size // 2] = 1  # 中间一个活细胞
        self.history = [self.state.copy()]

    def step(self) -> np.ndarray:
        new_state = np.zeros(self.size, dtype=int)
        for i in range(self.size):
            # 三元组
            left = self.state[(i - 1) % self.size]
            center = self.state[i]
            right = self.state[(i + 1) % self.size]
            idx = left * 4 + center * 2 + right
            new_state[i] = (self.rule >> idx) & 1
        self.state = new_state
        self.history.append(self.state.copy())
        return self.state

    def run(self, n_steps: int = 50):
        for _ in range(n_steps):
            self.step()
        return np.array(self.history)

    def plot(self):
        plt.figure(figsize=(12, 6))
        plt.imshow(np.array(self.history), cmap='binary', aspect='auto')
        plt.title(f'Elementary CA - Rule {self.rule}')
        plt.xlabel('Position')
        plt.ylabel('Time')
        plt.show()


# ============================================================
# 4. 扩散限制聚集 (DLA)
# ============================================================
class DLA:
    """
    扩散限制聚集模型 (Diffusion-Limited Aggregation)

    模拟分形生长现象
    """

    def __init__(self, size: int = 200):
        self.size = size
        self.grid = np.zeros((size, size), dtype=int)
        self.grid[size // 2, size // 2] = 1  # 中心种子
        self.n_particles = 1

    def add_particle(self) -> bool:
        """添加一个随机游走粒子, 直到被聚集或逃逸"""
        # 从边界出发
        edge = np.random.randint(4)
        if edge == 0:
            x, y = 0, np.random.randint(self.size)
        elif edge == 1:
            x, y = self.size - 1, np.random.randint(self.size)
        elif edge == 2:
            x, y = np.random.randint(self.size), 0
        else:
            x, y = np.random.randint(self.size), self.size - 1

        max_steps = self.size * self.size
        for _ in range(max_steps):
            # 检查是否邻近聚集
            for dx, dy in [(0,1),(0,-1),(1,0),(-1,0)]:
                nx, ny = (x+dx) % self.size, (y+dy) % self.size
                if self.grid[nx, ny] == 1:
                    self.grid[x, y] = 1
                    self.n_particles += 1
                    return True

            # 随机游走
            direction = np.random.randint(4)
            if direction == 0: x = (x + 1) % self.size
            elif direction == 1: x = (x - 1) % self.size
            elif direction == 2: y = (y + 1) % self.size
            else: y = (y - 1) % self.size

        return False

    def grow(self, n_particles: int = 1000):
        """生长 n 个粒子"""
        for _ in range(n_particles):
            self.add_particle()
        return self.grid

    def plot(self):
        plt.figure(figsize=(8, 8))
        plt.imshow(self.grid, cmap='hot')
        plt.title(f'DLA - {self.n_particles} particles')
        plt.show()


# ============================================================
# 5. SIRS 传染病模型
# ============================================================
class SIRSModel:
    """
    SIRS 元胞自动机传染病模型

    状态: 0=S(易感), 1=I(感染), 2=R(恢复)
    规则:
    - S + 邻居I → 以概率 β 感染
    - I → 以概率 γ 恢复为 R
    - R → 以概率 δ 重新变为 S
    """

    def __init__(self, size: Tuple[int, int] = (100, 100),
                 beta: float = 0.3, gamma: float = 0.1, delta: float = 0.01):
        self.h, self.w = size
        self.beta = beta
        self.gamma = gamma
        self.delta = delta
        self.grid = np.zeros((self.h, self.w), dtype=int)
        self.history = []
        self.stats = []

    def random_init(self, infected_ratio: float = 0.01):
        """随机初始化"""
        self.grid = np.zeros((self.h, self.w), dtype=int)
        infected = np.random.rand(self.h, self.w) < infected_ratio
        self.grid[infected] = 1

    def step(self) -> Dict:
        from scipy.signal import convolve2d
        new_grid = self.grid.copy()

        # I → R
        recover = (self.grid == 1) & (np.random.rand(self.h, self.w) < self.gamma)
        new_grid[recover] = 2

        # R → S
        wane = (self.grid == 2) & (np.random.rand(self.h, self.w) < self.delta)
        new_grid[wane] = 0

        # S + 邻居I → I
        kernel = np.array([[0,1,0],[1,0,1],[0,1,0]])
        infected_neighbors = convolve2d((self.grid == 1).astype(int), kernel, mode='same', boundary='wrap')
        infect = (self.grid == 0) & (infected_neighbors > 0) & (np.random.rand(self.h, self.w) < self.beta)
        new_grid[infect] = 1

        self.grid = new_grid
        self.history.append(self.grid.copy())

        # 统计
        S = np.sum(self.grid == 0)
        I = np.sum(self.grid == 1)
        R = np.sum(self.grid == 2)
        total = self.h * self.w
        stats = {'S': S/total, 'I': I/total, 'R': R/total}
        self.stats.append(stats)
        return stats

    def run(self, n_steps: int = 200) -> List[Dict]:
        for _ in range(n_steps):
            self.step()
        return self.stats


# ============================================================
# 使用示例
# ============================================================
def example():
    """元胞自动机示例"""
    # 生命游戏
    print("=" * 60)
    print("示例1: 生命游戏 — 滑翔机")
    print("=" * 60)
    gol = GameOfLife((30, 30))
    glider = np.array([[0,1,0],[0,0,1],[1,1,1]])
    gol.add_pattern(glider, (5, 5))
    gol.run(20)
    print(f"  最终活细胞数: {gol.grid.sum()}")

    # 初等元胞自动机
    print("\n" + "=" * 60)
    print("示例2: 初等元胞自动机 Rule 30")
    print("=" * 60)
    eca = ElementaryCA(rule=30, size=101)
    eca.run(50)
    print(f"  生成了 {len(eca.history)} 步")

    # 森林火灾
    print("\n" + "=" * 60)
    print("示例3: 森林火灾模型")
    print("=" * 60)
    ff = ForestFire((50, 50), p=0.02, f=0.001)
    # 放一把火
    ff.grid[25, 25] = 2
    ff.run(50)
    trees = np.sum(ff.grid == 1)
    empty = np.sum(ff.grid == 0)
    print(f"  树木: {trees}, 空地: {empty}")

    # SIRS
    print("\n" + "=" * 60)
    print("示例4: SIRS 传染病模型")
    print("=" * 60)
    sirs = SIRSModel((50, 50), beta=0.3, gamma=0.1, delta=0.02)
    sirs.random_init(0.05)
    stats = sirs.run(100)
    print(f"  最终: S={stats[-1]['S']:.2%}, I={stats[-1]['I']:.2%}, R={stats[-1]['R']:.2%}")


if __name__ == "__main__":
    example()
