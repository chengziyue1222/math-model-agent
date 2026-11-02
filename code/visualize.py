"""Generate figures for the wave-energy optimization example."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from scipy.integrate import solve_ivp

from solve import (
    G,
    PI,
    RHO,
    added_mass_and_damping,
    average_power,
    excitation_force,
    wave_params,
)


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_RESULTS_PATH = Path(__file__).resolve().with_name("results.json")
DEFAULT_OUTPUT_DIR = ROOT / "figures"
PARAMETER_BOUNDS = (
    (0.5, 5.0),
    (0.5, 10.0),
    (1_000.0, 1_000_000.0),
    (100.0, 100_000.0),
)

from algorithms.sci_figures import (
    FigureContract, FigureDesignBrief, publication_size, paper_figure_rc_params,
    export_publication_figure, get_modeling_palette,
)
from algorithms.figure_config import load_figure_config


def load_results(path: str | Path = DEFAULT_RESULTS_PATH) -> dict:
    """Load a saved optimization result."""
    with Path(path).open(encoding="utf-8") as stream:
        return json.load(stream)


def _problem_values(
    results: dict,
) -> tuple[np.ndarray, float, float, float, float, float, float]:
    optimal = results["optimal_params"]
    wave = results["wave_params"]
    params = np.array(
        [optimal["r"], optimal["d"], optimal["ks"], optimal["cd"]], dtype=float
    )
    height = float(wave["H"])
    period = float(wave["T"])
    depth = float(wave["h"])
    omega, wave_number = wave_params(height, period, depth)
    power = average_power(params, omega, wave_number, height, depth)
    return params, height, period, depth, omega, wave_number, power


def _time_history_figure(
    params: np.ndarray,
    height: float,
    period: float,
    depth: float,
    omega: float,
    wave_number: float,
    best_power: float,
) -> plt.Figure:
    radius, draft, stiffness, damping = params
    mass = RHO * PI * radius**2 * draft
    added_mass, radiation_damping = added_mass_and_damping(
        radius, draft, omega, wave_number
    )
    total_mass = mass + added_mass
    total_damping = radiation_damping + damping
    total_stiffness = stiffness + RHO * G * PI * radius**2
    force = excitation_force(radius, draft, height, wave_number, depth)

    def motion_equation(time: float, state: np.ndarray) -> list[float]:
        displacement, velocity = state
        acceleration = (
            force * np.cos(omega * time)
            - total_damping * velocity
            - total_stiffness * displacement
        ) / total_mass
        return [velocity, acceleration]

    time = np.linspace(0.0, 6.0 * period, 2_000)
    solution = solve_ivp(
        motion_equation,
        (float(time[0]), float(time[-1])),
        [0.0, 0.0],
        t_eval=time,
        method="RK45",
    )
    displacement = solution.y[0]
    velocity = solution.y[1]
    instantaneous_power = damping * velocity**2
    wave_displacement = (height / 2.0) * np.cos(omega * time)

    fig, axes = plt.subplots(3, 1, figsize=publication_size(None, 145), constrained_layout=True, sharex=True)
    axes[0].plot(time, wave_displacement, "-", linewidth=1.5, label="波面位移")
    axes[0].set_ylabel("位移 (m)")
    axes[0].set_title("波面位移")
    axes[1].plot(time, displacement, "-", linewidth=1.5, label="浮子位移")
    axes[1].set_ylabel("位移 (m)")
    axes[1].set_title("浮子垂荡位移")
    axes[2].plot(time, instantaneous_power, "-", linewidth=1.5, label="瞬时功率")
    axes[2].axhline(
        best_power, color="#A6534C", linestyle="--", label=f"解析平均功率 = {best_power:.1f} W"
    )
    axes[2].set_xlabel("时间 (s)")
    axes[2].set_ylabel("功率 (W)")
    axes[2].set_title("瞬时输出功率")
    axes[2].legend(loc="upper left")
    for axis in axes:
        axis.grid(True, alpha=0.3)
    fig.suptitle("波浪能转换装置运动与功率特性", fontweight="bold")
    return fig


def _damping_figure(
    params: np.ndarray,
    height: float,
    depth: float,
    omega: float,
    wave_number: float,
    best_power: float,
) -> plt.Figure:
    damping_values = np.linspace(100.0, 140_000.0, 500)
    powers = [
        average_power(
            [params[0], params[1], params[2], damping],
            omega,
            wave_number,
            height,
            depth,
        )
        for damping in damping_values
    ]

    fig, axis = plt.subplots(figsize=publication_size(None, 90), constrained_layout=True)
    axis.plot(damping_values, powers, "-", linewidth=2)
    axis.axvline(
        params[3], color="#A6534C", linestyle="--", label=f"保存参数 c_d = {params[3]:.0f} N·s/m"
    )
    axis.axhline(best_power, color="#5B8C6A", linestyle=":", label=f"功率 = {best_power:.1f} W")
    axis.set_xlabel("阻尼系数 c_d (N·s/m)")
    axis.set_ylabel("平均输出功率 P (W)")
    axis.set_title("平均输出功率 vs 阻尼系数")
    axis.legend()
    axis.grid(True, alpha=0.3)
    return fig


def _heatmap_figure(
    params: np.ndarray,
    height: float,
    depth: float,
    omega: float,
    wave_number: float,
) -> plt.Figure:
    radius_values = np.linspace(*PARAMETER_BOUNDS[0], 50)
    draft_values = np.linspace(*PARAMETER_BOUNDS[1], 50)
    radii, drafts = np.meshgrid(radius_values, draft_values)
    power_grid = np.empty_like(radii)
    for row in range(power_grid.shape[0]):
        for column in range(power_grid.shape[1]):
            power_grid[row, column] = average_power(
                [radii[row, column], drafts[row, column], params[2], params[3]],
                omega,
                wave_number,
                height,
                depth,
            )

    fig, axis = plt.subplots(figsize=publication_size(None, 100), constrained_layout=True)
    from matplotlib.colors import LinearSegmentedColormap
    palette = get_modeling_palette("modeling-default")
    cmap = LinearSegmentedColormap.from_list("power-sequential", palette["sequential"])
    axis.grid(False)
    image = axis.pcolormesh(radii, drafts, power_grid, cmap=cmap, shading="auto",
                            vmin=power_grid.min(), vmax=power_grid.max(), rasterized=True)
    contours = axis.contour(radii, drafts, power_grid, levels=[2000, 4000, 6000],
                 colors="#65777F", linewidths=.45, alpha=.7)
    import matplotlib.patheffects as pe
    contour_labels = axis.clabel(contours, fmt="%d W", fontsize=7, colors="#262626")
    for label in contour_labels:
        label.set_alpha(1)
        label.set_path_effects([pe.withStroke(linewidth=2, foreground="white")])
    fig._power_grid = power_grid.copy()
    axis.plot(
        params[0], params[1], "*", color="#D79A37", markeredgecolor="#262626", markeredgewidth=.9, markersize=10, clip_on=False, label=f"保存参数 ({params[0]:.2f}, {params[1]:.2f})"
    )
    axis.set_xlabel("浮子半径 r (m)")
    axis.set_ylabel("吃水深度 d (m)")

    axis.legend(loc="lower left", bbox_to_anchor=(0, 1.01), borderaxespad=0)
    axis.set_ylim(draft_values.min()-.12, draft_values.max()+.45)
    fig.colorbar(image, ax=axis, label="功率 (W)")
    return fig


def _sensitivity_figure(
    params: np.ndarray,
    height: float,
    depth: float,
    omega: float,
    wave_number: float,
    best_power: float,
) -> plt.Figure:
    names = ["半径 r", "吃水 d", "刚度 k_s", "阻尼 c_d"]
    negative_changes = []
    positive_changes = []
    for index, bounds in enumerate(PARAMETER_BOUNDS):
        for factor, changes in ((0.9, negative_changes), (1.1, positive_changes)):
            trial = params.copy()
            trial[index] = np.clip(trial[index] * factor, *bounds)
            trial_power = average_power(trial, omega, wave_number, height, depth)
            changes.append((trial_power - best_power) / best_power * 100.0)

    fig, axis = plt.subplots(figsize=publication_size(None, 90), constrained_layout=True)
    positions = np.arange(len(names))
    axis.barh(positions + .2, positive_changes, height=0.4, color="steelblue", label="+10%（边界裁剪）")
    axis.barh(positions - .2, negative_changes, height=0.4, color="coral", label="-10%（边界裁剪）")
    axis.set_yticks(positions, labels=names)
    axis.set_xlabel("功率变化 (%)")
    axis.set_title("参数局部敏感度分析")
    axis.legend()
    axis.grid(True, alpha=0.3, axis="x")
    axis.axvline(0, color="black", linewidth=0.8)
    return fig


@matplotlib.rc_context(paper_figure_rc_params())
def generate_figures(
    results_path: str | Path = DEFAULT_RESULTS_PATH,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
) -> list[Path]:
    """Generate all four example figures and return their paths."""
    results = load_results(results_path)
    params, height, period, depth, omega, wave_number, best_power = _problem_values(results)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    figures = (
        ("fig01_time_history.png", _time_history_figure(
            params, height, period, depth, omega, wave_number, best_power
        )),
        ("fig02_power_vs_damping.png", _damping_figure(
            params, height, depth, omega, wave_number, best_power
        )),
        ("fig03_power_heatmap.png", _heatmap_figure(
            params, height, depth, omega, wave_number
        )),
        ("fig04_sensitivity.png", _sensitivity_figure(
            params, height, depth, omega, wave_number, best_power
        )),
    )
    paths = []
    for filename, figure in figures:
        if hasattr(figure, "_power_grid"):
            claim = f"固定刚度与阻尼的50×50网格功率为{figure._power_grid.min():.2f}至{figure._power_grid.max():.2f} W；星标为保存参数点"
            evidence = ("50×50原始参数网格", "保存参数点；不宣称全局最优")
        elif "time_history" in filename:
            claim = f"保存参数下解析稳态平均功率为{best_power:.2f} W；时域曲线包含零初始条件下的瞬态"
            evidence = ("波面", "浮子位移", "瞬时功率及解析均值")
        elif "damping" in filename:
            claim = f"保存阻尼{params[3]:.0f} N·s/m对应解析平均功率{best_power:.2f} W"
            evidence = ("500个阻尼取值", "保存参数参考线")
        else:
            claim = "待检验：逐参数±10%扰动（按约束裁剪）如何改变保存参数下的功率？"
            evidence = ("4个参数的正负扰动",)
        figure._figure_config = load_figure_config()
        contract = FigureContract(
            claim, evidence, source_paths=(str(Path(results_path).resolve()),),
            plotting_code=(str(Path(__file__).resolve()), str(Path(__file__).with_name("solve.py").resolve())),
            width_mm=figure.get_figwidth()*25.4, height_mm=figure.get_figheight()*25.4,
            question="保存参数下的响应和参数敏感性如何？", units="m, s, W, N·s/m",
            claim_status="question" if "sensitivity" in filename else "verified",
            model_name="wave energy: solve.average_power + solve_ivp RK45", scenario="saved wave parameters",
            parameter_source=str(results_path), randomness="deterministic; no random sampling",
            n_definition="heatmap: 2500 grid points; time history: 2000 times; damping: 500 values; sensitivity: 8 perturbations",
            statistic="analytic steady-state average power; time integration for transients",
            uncertainty="none estimated; deterministic parameter sweep",
            data_transformations=("linear scale; no smoothing; heatmap color only changed", "sensitivity: ±10% clipped to parameter bounds; relative percent change", "heatmap: contours at 2000/4000/6000 W; contour algorithm locates crossings between saved grid samples; no resampling of the heatmap"),
            panel_evidence=evidence,
            design_brief=FigureDesignBrief(claim) if len(figure.axes)>1 else None,
            review_risks=("saved point is not asserted to be a global optimum",),
        )
        bundle = export_publication_figure(figure, output / Path(filename).stem, contract, close=True)
        paths.append(Path(bundle["png"]))
    return paths


def main() -> None:
    for path in generate_figures():
        print(f"已生成: {path}")


if __name__ == "__main__":
    main()
