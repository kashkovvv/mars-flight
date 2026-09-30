"""Численная модель вертикального взлета с Земли."""

from dataclasses import dataclass
from math import isfinite

import numpy as np
from numpy.typing import NDArray
from scipy.integrate import solve_ivp

from .config import EarthAscentParameters


@dataclass(frozen=True)
class EarthAscentResult:
    """История и итоговые параметры вертикального взлета в СИ."""

    time_s: NDArray[np.float64]
    radius_m: NDArray[np.float64]
    altitude_m: NDArray[np.float64]
    radial_velocity_m_s: NDArray[np.float64]
    mass_kg: NDArray[np.float64]
    load_factor: NDArray[np.float64]
    specific_energy_m2_s2: NDArray[np.float64]
    target_excess_speed_m_s: float

    @property
    def duration_s(self) -> float:
        return float(self.time_s[-1])

    @property
    def final_altitude_m(self) -> float:
        return float(self.altitude_m[-1])

    @property
    def final_radial_velocity_m_s(self) -> float:
        return float(self.radial_velocity_m_s[-1])

    @property
    def final_mass_kg(self) -> float:
        return float(self.mass_kg[-1])

    @property
    def maximum_load_factor(self) -> float:
        return float(np.max(self.load_factor))


class EarthAscentModel:
    """Модель вертикального движения в поле тяготения Земли."""

    def __init__(self, parameters: EarthAscentParameters) -> None:
        self.parameters: EarthAscentParameters = parameters

    def simulate(self, target_excess_speed_m_s: float) -> EarthAscentResult:
        if not isfinite(target_excess_speed_m_s) or target_excess_speed_m_s <= 0.0:
            raise ValueError(
                "Целевая скорость должна быть конечным положительным числом"
            )

        try:
            target_energy_m2_s2 = 0.5 * target_excess_speed_m_s**2
        except OverflowError as exc:
            raise ValueError("Целевая скорость слишком велика для расчета") from exc

        def target_energy_event(_time_s: float, state: NDArray[np.float64]) -> float:
            radius_m, radial_velocity_m_s, _mass_kg = state

            specific_energy_m2_s2 = (
                0.5 * radial_velocity_m_s**2
                - self.parameters.earth_gravitational_parameter_m3_s2 / radius_m
            )

            return float(specific_energy_m2_s2 - target_energy_m2_s2)

        def dry_mass_event(_time_s: float, state: NDArray[np.float64]) -> float:
            return float(state[2] - self.parameters.dry_mass_kg)

        # solve_ivp использует эти атрибуты для обработки событий.
        setattr(target_energy_event, "terminal", True)
        setattr(target_energy_event, "direction", 1.0)
        setattr(dry_mass_event, "terminal", True)
        setattr(dry_mass_event, "direction", -1.0)

        initial_state = np.array(
            (
                self.parameters.earth_radius_m,
                0.0,
                self.parameters.initial_mass_kg,
            ),
            dtype=np.float64,
        )
        absolute_tolerance = np.array(
            (
                self.parameters.position_absolute_tolerance_m,
                self.parameters.velocity_absolute_tolerance_m_s,
                self.parameters.mass_absolute_tolerance_kg,
            ),
            dtype=np.float64,
        )

        solution = solve_ivp(
            fun=self._derivatives,
            t_span=(0.0, self.parameters.maximum_time_s),
            y0=initial_state,
            method="RK45",
            events=(target_energy_event, dry_mass_event),
            rtol=self.parameters.relative_tolerance,
            atol=absolute_tolerance,
            max_step=self.parameters.maximum_step_s,
        )

        if not solution.success:
            raise RuntimeError(
                f"Численный расчет взлета завершился ошибкой: {solution.message}"
            )

        if solution.t_events[0].size == 0:
            if solution.t_events[1].size > 0:
                raise RuntimeError(
                    "Топливо закончилось до достижения требуемой энергии"
                )

            raise RuntimeError("Требуемая энергия не достигнута за заданное время")

        time_s = solution.t.astype(np.float64, copy=False)
        radius_m = solution.y[0].astype(np.float64, copy=False)
        radial_velocity_m_s = solution.y[1].astype(np.float64, copy=False)
        mass_kg = solution.y[2].astype(np.float64, copy=False)

        altitude_m = radius_m - self.parameters.earth_radius_m
        load_factor = np.array(
            [self._load_factor(float(current_mass_kg)) for current_mass_kg in mass_kg],
            dtype=np.float64,
        )
        specific_energy_m2_s2 = (
            0.5 * radial_velocity_m_s**2
            - self.parameters.earth_gravitational_parameter_m3_s2 / radius_m
        )

        return EarthAscentResult(
            time_s=time_s,
            radius_m=radius_m,
            altitude_m=altitude_m,
            radial_velocity_m_s=radial_velocity_m_s,
            mass_kg=mass_kg,
            load_factor=load_factor,
            specific_energy_m2_s2=specific_energy_m2_s2,
            target_excess_speed_m_s=target_excess_speed_m_s,
        )

    def _thrust_n(self, mass_kg: float) -> float:
        if mass_kg <= self.parameters.dry_mass_kg:
            return 0.0

        load_limited_thrust_n = (
            mass_kg
            * self.parameters.maximum_load_factor
            * self.parameters.standard_gravity_m_s2
        )

        return min(self.parameters.maximum_thrust_n, load_limited_thrust_n)

    def _load_factor(self, mass_kg: float) -> float:
        return self._thrust_n(mass_kg) / (
            mass_kg * self.parameters.standard_gravity_m_s2
        )

    def _derivatives(
        self, _time_s: float, state: NDArray[np.float64]
    ) -> NDArray[np.float64]:
        radius_m, radial_velocity_m_s, mass_kg = state
        thrust_n = self._thrust_n(float(mass_kg))

        radial_acceleration_m_s2 = (
            thrust_n / mass_kg
            - self.parameters.earth_gravitational_parameter_m3_s2 / radius_m**2
        )
        mass_rate_kg_s = -thrust_n / self.parameters.exhaust_velocity_m_s

        return np.array(
            (radial_velocity_m_s, radial_acceleration_m_s2, mass_rate_kg_s),
            dtype=np.float64,
        )
