"""Графики рассчитанных этапов полёта без повторного моделирования."""

from math import pi

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from numpy.typing import NDArray

from .config import (
    KILOGRAMS_PER_TONNE,
    METRES_PER_KILOMETRE,
    METRES_PER_MILLION_KILOMETRES,
    NEWTONS_PER_KILONEWTON,
    SECONDS_PER_DAY,
    MissionParameters,
)
from .earth import EarthAscentResult
from .mars import MarsLandingResult
from .transfer import SolarTransferResult


def create_mission_figures(
    ascent: EarthAscentResult,
    transfer: SolarTransferResult,
    landing: MarsLandingResult,
    mission: MissionParameters,
) -> dict[str, Figure]:
    """Создать три фигуры по уже рассчитанным историям состояний."""
    return {
        "ascent": _plot_ascent(ascent),
        "transfer": _plot_transfer(transfer, mission),
        "landing": _plot_landing(landing),
    }


def _format_axis(axis: Axes, x_label: str, y_label: str) -> None:
    axis.set_xlabel(x_label)
    axis.set_ylabel(y_label)
    axis.grid(alpha=0.25)


def _plot_active_stage(
    time_s: NDArray[np.float64],
    altitude_m: NDArray[np.float64],
    speed_m_s: NDArray[np.float64],
    mass_kg: NDArray[np.float64],
    thrust_n: NDArray[np.float64],
    title: str,
) -> Figure:
    figure, axes = plt.subplots(2, 2, figsize=(11, 7), layout="constrained")
    x_label = "Время работы двигателя, с"

    axes[0, 0].plot(time_s, altitude_m / METRES_PER_KILOMETRE)
    axes[0, 0].set_title("Высота")
    _format_axis(axes[0, 0], x_label, "Высота, км")
    axes[0, 0].set_ylim(bottom=0.0)

    axes[0, 1].plot(time_s, speed_m_s / METRES_PER_KILOMETRE)
    axes[0, 1].set_title("Скорость")
    _format_axis(axes[0, 1], x_label, "Скорость, км/с")
    axes[0, 1].set_ylim(bottom=0.0)

    axes[1, 0].plot(time_s, mass_kg / KILOGRAMS_PER_TONNE)
    axes[1, 0].set_title("Масса корабля")
    _format_axis(axes[1, 0], x_label, "Масса, т")

    axes[1, 1].plot(time_s, thrust_n / NEWTONS_PER_KILONEWTON)
    axes[1, 1].set_title("Тяга двигателя")
    _format_axis(axes[1, 1], x_label, "Тяга, кН")

    for axis in axes.flat:
        axis.set_xlim(0.0, float(time_s[-1]))

    figure.suptitle(title)
    return figure


def _plot_ascent(result: EarthAscentResult) -> Figure:
    return _plot_active_stage(
        time_s=result.time_s,
        altitude_m=result.altitude_m,
        speed_m_s=result.radial_velocity_m_s,
        mass_kg=result.mass_kg,
        thrust_n=result.thrust_n,
        title="Вертикальный взлёт с Земли",
    )


def _plot_transfer(
    result: SolarTransferResult, mission: MissionParameters
) -> Figure:
    figure = plt.figure(figsize=(12, 7), layout="constrained")
    grid = figure.add_gridspec(
        3, 2, width_ratios=(1.3, 1.0), height_ratios=(1.0, 1.0, 0.14)
    )
    orbit_axis = figure.add_subplot(grid[:2, 0])
    radius_axis = figure.add_subplot(grid[0, 1])
    speed_axis = figure.add_subplot(grid[1, 1])
    legend_axis = figure.add_subplot(grid[2, :])
    legend_axis.set_axis_off()

    angle = np.linspace(0.0, 2.0 * pi, 720)
    for radius_m, label, color in (
        (mission.earth_orbit_radius_m, "Орбита Земли", "#8b8b8b"),
        (mission.mars_orbit_radius_m, "Орбита Марса", "#b7b7b7"),
    ):
        orbit_axis.plot(
            radius_m * np.cos(angle) / METRES_PER_MILLION_KILOMETRES,
            radius_m * np.sin(angle) / METRES_PER_MILLION_KILOMETRES,
            linestyle="--",
            color=color,
            label=label,
        )

    orbit_axis.plot(
        result.x_m / METRES_PER_MILLION_KILOMETRES,
        result.y_m / METRES_PER_MILLION_KILOMETRES,
        color="#1967ad",
        linewidth=2,
        label="Траектория корабля",
    )
    orbit_axis.scatter(0.0, 0.0, s=90, color="#d59e21", label="Солнце")
    orbit_axis.scatter(
        result.x_m[0] / METRES_PER_MILLION_KILOMETRES,
        result.y_m[0] / METRES_PER_MILLION_KILOMETRES,
        s=35,
        color="#15803d",
        zorder=3,
        label="Начало перелёта",
    )
    orbit_axis.scatter(
        result.x_m[-1] / METRES_PER_MILLION_KILOMETRES,
        result.y_m[-1] / METRES_PER_MILLION_KILOMETRES,
        s=35,
        color="#d65f45",
        zorder=3,
        label="Конец перелёта",
    )
    orbit_axis.set_aspect("equal", adjustable="box")
    orbit_axis.set_title("Гелиоцентрическая траектория")
    _format_axis(orbit_axis, "x, млн км", "y, млн км")
    handles, labels = orbit_axis.get_legend_handles_labels()
    legend_axis.legend(handles, labels, loc="center", ncol=3, fontsize=8)

    time_days = result.time_s / SECONDS_PER_DAY
    radius_axis.plot(
        time_days,
        result.radius_m / METRES_PER_MILLION_KILOMETRES,
        color="#1967ad",
        label="Корабль",
    )
    radius_axis.axhline(
        mission.mars_orbit_radius_m / METRES_PER_MILLION_KILOMETRES,
        color="#d65f45",
        linestyle="--",
        label="Орбита Марса",
    )
    radius_axis.set_title("Расстояние от Солнца")
    _format_axis(radius_axis, "Время перелёта, сутки", "Радиус, млн км")
    radius_axis.legend(fontsize=8)

    speed_axis.plot(
        time_days,
        result.heliocentric_speed_m_s / METRES_PER_KILOMETRE,
        color="#15803d",
    )
    speed_axis.set_title("Гелиоцентрическая скорость")
    _format_axis(speed_axis, "Время перелёта, сутки", "Скорость, км/с")

    figure.suptitle("Пассивный перелёт в поле Солнца")
    return figure


def _plot_landing(result: MarsLandingResult) -> Figure:
    powered = result.time_s > result.ignition_time_s
    return _plot_active_stage(
        time_s=result.time_s[powered] - result.ignition_time_s,
        altitude_m=result.altitude_m[powered],
        speed_m_s=np.abs(result.radial_velocity_m_s[powered]),
        mass_kg=result.mass_kg[powered],
        thrust_n=result.thrust_n[powered],
        title="Торможение и посадка на Марс",
    )
