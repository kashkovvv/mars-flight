"""Численная модель пассивного перелета в поле тяготения Солнца."""

from dataclasses import dataclass
from math import isfinite, sqrt

import numpy as np
from numpy.typing import NDArray
from scipy.integrate import solve_ivp

from .config import MissionParameters, TransferIntegrationParameters


@dataclass(frozen=True)
class SolarTransferResult:
    """Траектория в гелиоцентрической системе отсчета, единицы СИ."""

    time_s: NDArray[np.float64]
    x_m: NDArray[np.float64]
    y_m: NDArray[np.float64]
    velocity_x_m_s: NDArray[np.float64]
    velocity_y_m_s: NDArray[np.float64]
    radius_m: NDArray[np.float64]
    heliocentric_speed_m_s: NDArray[np.float64]
    specific_energy_m2_s2: NDArray[np.float64]
    specific_angular_momentum_m2_s: NDArray[np.float64]
    mars_orbit_radius_m: float

    @property
    def duration_s(self) -> float:
        return float(self.time_s[-1])

    @property
    def final_radius_m(self) -> float:
        return float(self.radius_m[-1])

    @property
    def final_heliocentric_speed_m_s(self) -> float:
        return float(self.heliocentric_speed_m_s[-1])

    @property
    def final_radial_velocity_m_s(self) -> float:
        return float(
            (
                self.x_m[-1] * self.velocity_x_m_s[-1]
                + self.y_m[-1] * self.velocity_y_m_s[-1]
            )
            / self.radius_m[-1]
        )

    @property
    def final_tangential_velocity_m_s(self) -> float:
        return float(self.specific_angular_momentum_m2_s[-1] / self.radius_m[-1])

    @property
    def mars_orbit_radius_error_m(self) -> float:
        return self.final_radius_m - self.mars_orbit_radius_m


class SolarTransferModel:
    """Движение без тяги в центральном поле Солнца."""

    def __init__(
        self,
        mission_parameters: MissionParameters,
        integration_parameters: TransferIntegrationParameters,
    ) -> None:
        self.mission_parameters: MissionParameters = mission_parameters
        self.integration_parameters: TransferIntegrationParameters = (
            integration_parameters
        )

    def simulate(
        self, departure_earth_relative_excess_speed_m_s: float
    ) -> SolarTransferResult:
        if (
            not isfinite(departure_earth_relative_excess_speed_m_s)
            or departure_earth_relative_excess_speed_m_s < 0.0
        ):
            raise ValueError("Скорость ухода должна быть конечной и неотрицательной")

        mu_sun = self.mission_parameters.sun_gravitational_parameter_m3_s2
        earth_orbit_radius_m = self.mission_parameters.earth_orbit_radius_m
        earth_orbital_speed_m_s = sqrt(mu_sun / earth_orbit_radius_m)
        initial_heliocentric_speed_m_s = (
            earth_orbital_speed_m_s + departure_earth_relative_excess_speed_m_s
        )
        solar_escape_speed_m_s = sqrt(2.0 * mu_sun / earth_orbit_radius_m)

        if initial_heliocentric_speed_m_s >= solar_escape_speed_m_s:
            raise ValueError(
                "Гелиоцентрическая скорость не задает эллиптическую орбиту"
            )

        def opposite_side_event(_time_s: float, state: NDArray[np.float64]) -> float:
            return float(state[1])

        # После старта y сначала растет; первое пересечение сверху вниз
        # соответствует противоположной стороне орбиты.
        setattr(opposite_side_event, "terminal", True)
        setattr(opposite_side_event, "direction", -1.0)

        initial_state = np.array(
            (earth_orbit_radius_m, 0.0, 0.0, initial_heliocentric_speed_m_s),
            dtype=np.float64,
        )
        absolute_tolerance = np.array(
            (
                self.integration_parameters.position_absolute_tolerance_m,
                self.integration_parameters.position_absolute_tolerance_m,
                self.integration_parameters.velocity_absolute_tolerance_m_s,
                self.integration_parameters.velocity_absolute_tolerance_m_s,
            ),
            dtype=np.float64,
        )

        solution = solve_ivp(
            fun=self._derivatives,
            t_span=(0.0, self.integration_parameters.maximum_time_s),
            y0=initial_state,
            method="RK45",
            events=opposite_side_event,
            rtol=self.integration_parameters.relative_tolerance,
            atol=absolute_tolerance,
            max_step=self.integration_parameters.maximum_step_s,
        )

        if not solution.success:
            raise RuntimeError(
                f"Численный расчет перелета завершился ошибкой: {solution.message}"
            )
        if solution.t_events[0].size == 0:
            raise RuntimeError(
                "Противоположная сторона орбиты не достигнута за заданное время"
            )

        time_s = solution.t.astype(np.float64, copy=False)
        x_m = solution.y[0].astype(np.float64, copy=False)
        y_m = solution.y[1].astype(np.float64, copy=False)
        velocity_x_m_s = solution.y[2].astype(np.float64, copy=False)
        velocity_y_m_s = solution.y[3].astype(np.float64, copy=False)

        radius_m = np.hypot(x_m, y_m)
        heliocentric_speed_m_s = np.hypot(velocity_x_m_s, velocity_y_m_s)
        specific_energy_m2_s2 = 0.5 * heliocentric_speed_m_s**2 - mu_sun / radius_m
        specific_angular_momentum_m2_s = x_m * velocity_y_m_s - y_m * velocity_x_m_s

        return SolarTransferResult(
            time_s=time_s,
            x_m=x_m,
            y_m=y_m,
            velocity_x_m_s=velocity_x_m_s,
            velocity_y_m_s=velocity_y_m_s,
            radius_m=radius_m,
            heliocentric_speed_m_s=heliocentric_speed_m_s,
            specific_energy_m2_s2=specific_energy_m2_s2,
            specific_angular_momentum_m2_s=specific_angular_momentum_m2_s,
            mars_orbit_radius_m=self.mission_parameters.mars_orbit_radius_m,
        )

    def _derivatives(
        self, _time_s: float, state: NDArray[np.float64]
    ) -> NDArray[np.float64]:
        x_m, y_m, velocity_x_m_s, velocity_y_m_s = state
        radius_m = float(np.hypot(x_m, y_m))
        mu_sun = self.mission_parameters.sun_gravitational_parameter_m3_s2
        gravity_coefficient_s2 = -mu_sun / radius_m**3

        return np.array(
            (
                velocity_x_m_s,
                velocity_y_m_s,
                gravity_coefficient_s2 * x_m,
                gravity_coefficient_s2 * y_m,
            ),
            dtype=np.float64,
        )
