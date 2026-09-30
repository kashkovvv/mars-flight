"""Воспроизвести рисунки расчётных экспериментов для отчёта."""

from math import pi, sqrt
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.figure import Figure

from mars_flight.config import (
    DEFAULT_EARTH_ASCENT_PARAMETERS,
    DEFAULT_MARS_LANDING_PARAMETERS,
    DEFAULT_PARAMETERS,
    DEFAULT_TRANSFER_INTEGRATION_PARAMETERS,
    KILOGRAMS_PER_TONNE,
    MARS_ORBIT_MATCH_TOLERANCE_M,
    METRES_PER_KILOMETRE,
    METRES_PER_MILLION_KILOMETRES,
)
from mars_flight.earth import EarthAscentModel
from mars_flight.mars import MarsLandingModel
from mars_flight.mission import MissionModel
from mars_flight.theory import HohmannTransfer
from mars_flight.transfer import SolarTransferModel


FACTORS = (0.95, 1.0, 1.05)
COLORS = ("#1f77b4", "#15803d", "#d65f45")
LABELS = ("−5 %", "Номинал", "+5 %")
FIGURES_DIR = Path(__file__).resolve().parent / "figures"


def _save(figure: Figure, name: str) -> None:
    figure.savefig(FIGURES_DIR / name, dpi=180)
    plt.close(figure)


def _plot_transfer_sensitivity(departure_speed_m_s: float) -> None:
    figure = plt.figure(figsize=(12, 6), layout="constrained")
    grid = figure.add_gridspec(2, 2, height_ratios=(1.0, 0.14))
    orbit_axis = figure.add_subplot(grid[0, 0])
    radius_axis = figure.add_subplot(grid[0, 1])
    legend_axis = figure.add_subplot(grid[1, :])
    legend_axis.set_axis_off()

    angle = np.linspace(0.0, 2.0 * pi, 720)
    for radius_m, label, color in (
        (DEFAULT_PARAMETERS.earth_orbit_radius_m, "Орбита Земли", "#888888"),
        (DEFAULT_PARAMETERS.mars_orbit_radius_m, "Орбита Марса", "#bbbbbb"),
    ):
        orbit_axis.plot(
            radius_m * np.cos(angle) / METRES_PER_MILLION_KILOMETRES,
            radius_m * np.sin(angle) / METRES_PER_MILLION_KILOMETRES,
            linestyle="--",
            color=color,
            label=label,
        )

    departures_km_s: list[float] = []
    radius_errors_million_km: list[float] = []
    for factor, color, label in zip(FACTORS, COLORS, LABELS):
        ascent = EarthAscentModel(DEFAULT_EARTH_ASCENT_PARAMETERS).simulate(
            factor * departure_speed_m_s
        )
        actual_departure_speed_m_s = sqrt(
            2.0 * float(ascent.specific_energy_m2_s2[-1])
        )
        transfer = SolarTransferModel(
            DEFAULT_PARAMETERS, DEFAULT_TRANSFER_INTEGRATION_PARAMETERS
        ).simulate(actual_departure_speed_m_s)
        orbit_axis.plot(
            transfer.x_m / METRES_PER_MILLION_KILOMETRES,
            transfer.y_m / METRES_PER_MILLION_KILOMETRES,
            color=color,
            label=label,
        )
        departures_km_s.append(actual_departure_speed_m_s / METRES_PER_KILOMETRE)
        radius_errors_million_km.append(
            transfer.mars_orbit_radius_error_m / METRES_PER_MILLION_KILOMETRES
        )

    orbit_axis.scatter(0.0, 0.0, s=75, color="#d59e21", label="Солнце")
    orbit_axis.set_aspect("equal", adjustable="box")
    orbit_axis.set_title("Солнечный участок")
    orbit_axis.set_xlabel("x, млн км")
    orbit_axis.set_ylabel("y, млн км")
    orbit_axis.grid(alpha=0.25)
    handles, labels = orbit_axis.get_legend_handles_labels()
    legend_axis.legend(handles, labels, loc="center", ncol=3, fontsize=8)

    radius_axis.plot(departures_km_s, radius_errors_million_km, color="#334155")
    for x, y, color, label in zip(
        departures_km_s, radius_errors_million_km, COLORS, LABELS
    ):
        radius_axis.scatter(x, y, s=36, color=color, zorder=3)
        radius_axis.annotate(label, (x, y), xytext=(5, 5), textcoords="offset points")
    radius_axis.axhline(0.0, color="#888888", linestyle="--", linewidth=1)
    radius_axis.set_title("Чувствительность конечного радиуса")
    radius_axis.set_xlabel("Скорость ухода от Земли, км/с")
    radius_axis.set_ylabel("Разность радиусов, млн км")
    radius_axis.margins(x=0.1, y=0.15)
    radius_axis.grid(alpha=0.25)

    _save(figure, "solar_transfer_sensitivity.png")


def _plot_landing_sensitivity(
    arrival_speed_m_s: float, initial_mass_kg: float
) -> None:
    figure, axes = plt.subplots(1, 2, figsize=(12, 5), layout="constrained")
    maximum_ignition_altitude_km = 0.0
    for factor, color, label in zip(FACTORS, COLORS, LABELS):
        landing = MarsLandingModel(DEFAULT_MARS_LANDING_PARAMETERS).simulate(
            factor * arrival_speed_m_s, initial_mass_kg
        )
        powered = landing.time_s > landing.ignition_time_s
        altitude_km = landing.altitude_m[powered] / METRES_PER_KILOMETRE
        axes[0].plot(
            altitude_km,
            np.abs(landing.radial_velocity_m_s[powered]) / METRES_PER_KILOMETRE,
            color=color,
            label=label,
        )
        axes[1].plot(
            altitude_km,
            landing.mass_kg[powered] / KILOGRAMS_PER_TONNE,
            color=color,
        )
        maximum_ignition_altitude_km = max(
            maximum_ignition_altitude_km,
            landing.ignition_altitude_m / METRES_PER_KILOMETRE,
        )

    axes[0].set_title("Скорость снижения")
    axes[0].set_ylabel("Скорость снижения, км/с")
    axes[0].legend(fontsize=8)
    axes[1].set_title("Масса корабля")
    axes[1].set_ylabel("Масса корабля, т")
    for axis in axes:
        axis.set_xlabel("Высота над Марсом, км")
        axis.set_xlim(maximum_ignition_altitude_km, 0.0)
        axis.grid(alpha=0.25)

    _save(figure, "mars_descent_sensitivity.png")


def main() -> None:
    FIGURES_DIR.mkdir(exist_ok=True)
    benchmark = HohmannTransfer.from_parameters(DEFAULT_PARAMETERS)
    _plot_transfer_sensitivity(benchmark.departure_excess_speed_m_s)

    mission = MissionModel(
        mission_parameters=DEFAULT_PARAMETERS,
        earth_ascent_parameters=DEFAULT_EARTH_ASCENT_PARAMETERS,
        transfer_integration_parameters=DEFAULT_TRANSFER_INTEGRATION_PARAMETERS,
        mars_landing_parameters=DEFAULT_MARS_LANDING_PARAMETERS,
        mars_orbit_match_tolerance_m=MARS_ORBIT_MATCH_TOLERANCE_M,
    ).simulate()
    _plot_landing_sensitivity(
        mission.arrival_relative_speed_m_s, mission.ascent.final_mass_kg
    )


if __name__ == "__main__":
    main()
