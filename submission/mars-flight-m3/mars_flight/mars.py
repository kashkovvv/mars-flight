"""Численная модель радиальной посадки в поле тяготения Марса."""

from dataclasses import dataclass
from math import isfinite, sqrt

import numpy as np
from numpy.typing import NDArray
from scipy.integrate import solve_ivp

from .config import MarsLandingParameters


@dataclass(frozen=True)
class MarsLandingResult:
    """История снижения и состояние при остановке у поверхности в СИ."""

    time_s: NDArray[np.float64]
    radius_m: NDArray[np.float64]
    altitude_m: NDArray[np.float64]
    radial_velocity_m_s: NDArray[np.float64]
    mass_kg: NDArray[np.float64]
    thrust_n: NDArray[np.float64]
    load_factor: NDArray[np.float64]
    specific_energy_m2_s2: NDArray[np.float64]
    ignition_time_s: float
    ignition_altitude_m: float
    initial_excess_speed_m_s: float

    @property
    def duration_s(self) -> float:
        return float(self.time_s[-1])

    @property
    def burn_duration_s(self) -> float:
        return self.duration_s - self.ignition_time_s

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


class MarsLandingModel:
    """Свободное падение, затем торможение с постоянным ускорением от тяги."""

    def __init__(self, parameters: MarsLandingParameters) -> None:
        self.parameters: MarsLandingParameters = parameters

    def simulate(
        self, arrival_relative_speed_m_s: float, initial_mass_kg: float
    ) -> MarsLandingResult:
        if not isfinite(arrival_relative_speed_m_s) or arrival_relative_speed_m_s < 0.0:
            raise ValueError("Скорость подлёта должна быть конечной и неотрицательной")
        if (
            not isfinite(initial_mass_kg)
            or initial_mass_kg <= self.parameters.dry_mass_kg
        ):
            raise ValueError("Начальная масса должна превышать сухую массу")

        p = self.parameters
        mu = p.mars_gravitational_parameter_m3_s2
        radius = p.mars_radius_m
        thrust_acceleration = min(
            p.maximum_thrust_n / initial_mass_kg,
            p.maximum_load_factor * p.standard_gravity_m_s2,
        )
        if thrust_acceleration <= mu / radius**2:
            raise ValueError("Тяги недостаточно для остановки у поверхности Марса")

        try:
            speed_squared = arrival_relative_speed_m_s**2
        except OverflowError as exc:
            raise ValueError("Скорость подлёта слишком велика") from exc
        if not isfinite(speed_squared):
            raise ValueError("Скорость подлёта слишком велика")

        ignition_altitude = (0.5 * speed_squared + mu / radius) / thrust_acceleration
        ignition_radius = radius + ignition_altitude
        if ignition_radius >= p.initial_radius_m:
            raise ValueError("Высоты для торможения при заданной тяге недостаточно")

        initial_velocity = -sqrt(
            speed_squared + 2.0 * mu / p.initial_radius_m
        )
        initial_state = np.array(
            (p.initial_radius_m, initial_velocity, initial_mass_kg),
            dtype=np.float64,
        )
        absolute_tolerance = np.array(
            (
                p.position_absolute_tolerance_m,
                p.velocity_absolute_tolerance_m_s,
                p.mass_absolute_tolerance_kg,
            ),
            dtype=np.float64,
        )

        def ignition_event(_time_s: float, state: NDArray[np.float64]) -> float:
            return float(state[0] - ignition_radius)

        setattr(ignition_event, "terminal", True)
        setattr(ignition_event, "direction", -1.0)

        coast = solve_ivp(
            fun=lambda time_s, state: self._derivatives(time_s, state, 0.0),
            t_span=(0.0, p.maximum_time_s),
            y0=initial_state,
            method="RK45",
            events=ignition_event,
            rtol=p.relative_tolerance,
            atol=absolute_tolerance,
            max_step=p.coast_maximum_step_s,
        )
        if not coast.success:
            raise RuntimeError(
                f"Расчёт свободного падения завершился ошибкой: {coast.message}"
            )
        if coast.t_events[0].size == 0:
            raise RuntimeError(
                "Высота включения двигателя не достигнута за заданное время"
            )

        def velocity_zero_event(_time_s: float, state: NDArray[np.float64]) -> float:
            return float(state[1])

        def dry_mass_event(_time_s: float, state: NDArray[np.float64]) -> float:
            return float(state[2] - p.dry_mass_kg)

        setattr(velocity_zero_event, "terminal", True)
        setattr(velocity_zero_event, "direction", 1.0)
        setattr(dry_mass_event, "terminal", True)
        setattr(dry_mass_event, "direction", -1.0)

        burn = solve_ivp(
            fun=lambda time_s, state: self._derivatives(
                time_s, state, thrust_acceleration
            ),
            t_span=(float(coast.t[-1]), p.maximum_time_s),
            y0=coast.y[:, -1],
            method="RK45",
            events=(velocity_zero_event, dry_mass_event),
            rtol=p.relative_tolerance,
            atol=absolute_tolerance,
            max_step=p.burn_maximum_step_s,
        )
        if not burn.success:
            raise RuntimeError(f"Расчёт торможения завершился ошибкой: {burn.message}")
        if burn.t_events[1].size > 0:
            raise RuntimeError("Топливо закончилось до мягкой посадки")
        if burn.t_events[0].size == 0:
            raise RuntimeError("Скорость не обнулилась за заданное время")
        if (
            abs(float(burn.y[0, -1]) - radius)
            > p.contact_altitude_tolerance_m
        ):
            raise RuntimeError("Скорость обнулилась вне поверхности Марса")

        time_s = np.concatenate((coast.t, burn.t[1:])).astype(np.float64, copy=False)
        radius_m = np.concatenate((coast.y[0], burn.y[0, 1:]))
        radial_velocity_m_s = np.concatenate((coast.y[1], burn.y[1, 1:]))
        mass_kg = np.concatenate((coast.y[2], burn.y[2, 1:]))
        thrust_n = np.concatenate(
            (
                np.zeros(coast.t.size, dtype=np.float64),
                burn.y[2, 1:] * thrust_acceleration,
            )
        )
        load_factor = thrust_n / (mass_kg * p.standard_gravity_m_s2)
        specific_energy_m2_s2 = 0.5 * radial_velocity_m_s**2 - mu / radius_m

        return MarsLandingResult(
            time_s=time_s,
            radius_m=radius_m,
            altitude_m=radius_m - radius,
            radial_velocity_m_s=radial_velocity_m_s,
            mass_kg=mass_kg,
            thrust_n=thrust_n,
            load_factor=load_factor,
            specific_energy_m2_s2=specific_energy_m2_s2,
            ignition_time_s=float(coast.t[-1]),
            ignition_altitude_m=float(coast.y[0, -1] - radius),
            initial_excess_speed_m_s=arrival_relative_speed_m_s,
        )

    def _derivatives(
        self,
        _time_s: float,
        state: NDArray[np.float64],
        thrust_acceleration_m_s2: float,
    ) -> NDArray[np.float64]:
        radius_m, radial_velocity_m_s, mass_kg = state
        return np.array(
            (
                radial_velocity_m_s,
                thrust_acceleration_m_s2
                - self.parameters.mars_gravitational_parameter_m3_s2 / radius_m**2,
                -mass_kg * thrust_acceleration_m_s2
                / self.parameters.exhaust_velocity_m_s,
            ),
            dtype=np.float64,
        )
