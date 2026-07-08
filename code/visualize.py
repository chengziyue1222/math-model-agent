"""
波浪能最大输出功率 - 可视化代码
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib
from scipy.integrate import odeint
import json

# 中文字体设置
matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
matplotlib.rcParams['axes.unicode_minus'] = False
matplotlib.rcParams['figure.dpi'] = 150
matplotlib.rcParams['savefig.dpi'] = 300
matplotlib.rcParams['savefig.bbox'] = 'tight'

PI = np.pi
RHO = 1025.0
G = 9.8

# 加载结果
with open("results.json", "r") as f:
    res = json.load(f)

r = res['optimal_params']['r']
d = res['optimal_params']['d']
ks = res['optimal_params']['ks']
cd = res['optimal_params']['cd']
H = res['wave_params']['H']
T_wave = res['wave_params']['T']
h = res['wave_params']['h']
omega = res['wave_params']['omega']
kw = res['wave_params']['kw']
best_P = res['max_power_W']
A = res['derived']['A']
F0 = res['derived']['F0']
ma = res['derived']['ma']
cr = res['derived']['cr']
m = RHO * PI * r**2 * d

# ============ 图1：浮子运动时间历程 ============
M_total = m + ma
C_total = cr + cd
K_total = ks + RHO * G * PI * r**2

def motion_eq(y, t, M, C, K, F0, omega):
    z, zdot = y
    zddot = (F0 * np.cos(omega * t) - C * zdot - K * z) / M
    return [zdot, zddot]

t = np.linspace(0, 6 * T_wave, 2000)
y0 = [0, 0]
sol = odeint(motion_eq, y0, t, args=(M_total, C_total, K_total, F0, omega))
z_t = sol[:, 0]
zdot_t = sol[:, 1]
P_inst = cd * zdot_t**2
z_w = (H / 2) * np.cos(omega * t)

fig, axes = plt.subplots(3, 1, figsize=(12, 10), sharex=True)

# 波面位移
axes[0].plot(t, z_w, 'b-', linewidth=1.5, label='波面位移')
axes[0].set_ylabel('位移 (m)')
axes[0].set_title('波面位移', fontsize=14)
axes[0].legend()
axes[0].grid(True, alpha=0.3)

# 浮子位移
axes[1].plot(t, z_t, 'r-', linewidth=1.5, label='浮子位移')
axes[1].set_ylabel('位移 (m)')
axes[1].set_title('浮子垂荡位移', fontsize=14)
axes[1].legend()
axes[1].grid(True, alpha=0.3)

# 瞬时功率
axes[2].plot(t, P_inst, 'g-', linewidth=1.5, label='瞬时功率')
axes[2].axhline(y=best_P, color='r', linestyle='--', label=f'平均功率 = {best_P:.1f} W')
axes[2].set_xlabel('时间 (s)')
axes[2].set_ylabel('功率 (W)')
axes[2].set_title('瞬时输出功率', fontsize=14)
axes[2].legend()
axes[2].grid(True, alpha=0.3)

plt.suptitle('波浪能转换装置运动与功率特性', fontsize=16, fontweight='bold')
plt.tight_layout()
plt.savefig('../figures/fig01_time_history.png')
plt.close()
print("图1: 时间历程 → fig01_time_history.png")

# ============ 图2：功率 vs 阻尼系数 ============
cd_range = np.linspace(100, 50000, 500)
P_cd = []
for cdi in cd_range:
    C_i = cr + cdi
    A_i = F0 / np.sqrt((K_total - M_total * omega**2)**2 + (C_i * omega)**2)
    P_i = 0.5 * cdi * omega**2 * A_i**2
    P_cd.append(P_i)

fig, ax = plt.subplots(figsize=(10, 6))
ax.plot(cd_range, P_cd, 'b-', linewidth=2)
ax.axvline(x=cd, color='r', linestyle='--', label=f'最优 cd = {cd:.0f} N·s/m')
ax.axhline(y=best_P, color='g', linestyle=':', label=f'最大功率 = {best_P:.1f} W')
ax.set_xlabel('阻尼系数 $c_d$ (N·s/m)', fontsize=14)
ax.set_ylabel('平均输出功率 $\\bar{P}$ (W)', fontsize=14)
ax.set_title('平均输出功率 vs 阻尼系数', fontsize=16)
ax.legend(fontsize=12)
ax.grid(True, alpha=0.3)
plt.savefig('../figures/fig02_power_vs_damping.png')
plt.close()
print("图2: 功率-阻尼 → fig02_power_vs_damping.png")

# ============ 图3：功率热力图（r vs d）============
r_range = np.linspace(0.5, 5.0, 50)
d_range = np.linspace(0.5, 10.0, 50)
R, D = np.meshgrid(r_range, d_range)
P_grid = np.zeros_like(R)

for i in range(len(d_range)):
    for j in range(len(r_range)):
        ri, di = R[i, j], D[i, j]
        mi = RHO * PI * ri**2 * di
        mai = RHO * PI * ri**2 * di * 1.0
        Mi = mi + mai
        cri = RHO * G * PI * ri**2 / omega * 0.5
        F0i = RHO * G * PI * ri**2 * (H/2) * np.sinh(kw * di) / np.cosh(kw * h)
        Ki = ks + RHO * G * PI * ri**2
        Ci = cri + cd
        Ai = F0i / np.sqrt((Ki - Mi * omega**2)**2 + (Ci * omega)**2)
        P_grid[i, j] = 0.5 * cd * omega**2 * Ai**2

fig, ax = plt.subplots(figsize=(10, 8))
im = ax.pcolormesh(R, D, P_grid, cmap='hot', shading='auto')
ax.plot(r, d, 'w*', markersize=20, label=f'最优点 ({r:.2f}, {d:.2f})')
ax.set_xlabel('浮子半径 $r$ (m)', fontsize=14)
ax.set_ylabel('吃水深度 $d$ (m)', fontsize=14)
ax.set_title('平均输出功率热力图 ($r$ vs $d$)', fontsize=16)
ax.legend(fontsize=12, loc='upper left')
plt.colorbar(im, ax=ax, label='功率 (W)')
plt.savefig('../figures/fig03_power_heatmap.png')
plt.close()
print("图3: 功率热力图 → fig03_power_heatmap.png")

# ============ 图4：灵敏度分析（龙卷风图）============
param_names = ['半径 $r$', '吃水 $d$', '刚度 $k_s$', '阻尼 $c_d$']
params = [r, d, ks, cd]
bounds = [(0.5, 5.0), (0.5, 10.0), (1000, 1e6), (100, 1e5)]
sens_neg = []
sens_pos = []

for idx in range(4):
    for delta, store in [(-10, sens_neg), (10, sens_pos)]:
        p_test = list(params)
        p_test[idx] = params[idx] * (1 + delta / 100)
        p_test[idx] = np.clip(p_test[idx], bounds[idx][0], bounds[idx][1])
        P_test = 0.5 * p_test[3] * omega**2 * (
            F0 / np.sqrt((K_total - M_total * omega**2)**2 + ((cr + p_test[3]) * omega))**2
        )
        # Recalculate properly
        ri, di, ksi, cdi = p_test
        mi = RHO * PI * ri**2 * di
        mai = RHO * PI * ri**2 * di * 1.0
        Mi = mi + mai
        cri = RHO * G * PI * ri**2 / omega * 0.5
        F0i = RHO * G * PI * ri**2 * (H/2) * np.sinh(kw * di) / np.cosh(kw * h)
        Ki = ksi + RHO * G * PI * ri**2
        Ci = cri + cdi
        Ai = F0i / np.sqrt((Ki - Mi * omega**2)**2 + (Ci * omega)**2)
        P_i = 0.5 * cdi * omega**2 * Ai**2
        store.append((P_i - best_P) / best_P * 100)

fig, ax = plt.subplots(figsize=(10, 6))
y_pos = np.arange(len(param_names))
ax.barh(y_pos, sens_pos, height=0.4, color='steelblue', label='+10%')
ax.barh(y_pos, sens_neg, height=0.4, color='coral', label='-10%')
ax.set_yticks(y_pos)
ax.set_yticklabels(param_names, fontsize=13)
ax.set_xlabel('功率变化 (%)', fontsize=14)
ax.set_title('参数灵敏度分析', fontsize=16)
ax.legend(fontsize=12)
ax.grid(True, alpha=0.3, axis='x')
ax.axvline(x=0, color='black', linewidth=0.8)
plt.savefig('../figures/fig04_sensitivity.png')
plt.close()
print("图4: 灵敏度分析 → fig04_sensitivity.png")

print("\n所有图表已生成完毕!")
