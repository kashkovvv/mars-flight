"""Последовательный расчёт этапов миссии Земля — Марс."""

from dataclasses import dataclass
from math import hypot, isfinite, sqrt

from .config import (
    EarthAscentParameters,
    MarsLandingParameters,
    MissionParameters,
    TransferIntegrationParameters,
)
from .earth import EarthAscentModel, EarthAscentResult
from .mars import MarsLandingModel, MarsLandingResult
from .theory import HohmannTransfer
from .transfer import SolarTransferModel, SolarTransferResult


@dataclass(frozen=True)
class MissionResult:
    """Результаты этапов и скорости на границах систем отсчёта, в СИ."""

    benchmark: HohmannTransfer
    ascent: EarthAscentResult
    transfer: SolarTransferResult
    landing: MarsLandingResult
    actual_departure_excess_speed_m_s: float
    arrival_relative_speed_m_s: float


@dataclass(frozen=True)
class MissionModel:
    """Связать взлёт, солнечный перелёт и посадку общими параметрами."""

    mission_parameters: MissionParameters
    earth_ascent_parameters: EarthAscentParameters
    transfer_integration_parameters: TransferIntegrationParameters
    mars_landing_parameters: MarsLandingParameters
    mars_orbit_match_tolerance_m: float

    def __post_init__(self) -> None:
        if (
            not isfinite(self.mars_orbit_match_tolerance_m)
            or self.mars_orbit_match_tolerance_m < 0.0
        ):
            raise ValueError("Допуск стыковки по радиусу должен быть неотрицательным")

    def simulate(self) -> MissionResult:
        """Рассчитать этапы и передать физически нужные величины между ними."""
        benchmark = HohmannTransfer.from_parameters(self.mission_parameters)
        ascent = EarthAscentModel(self.earth_ascent_parameters).simulate(
            benchmark.departure_excess_speed_m_s
        )

        final_earth_specific_energy_m2_s2 = float(ascent.specific_energy_m2_s2[-1])
        if (
            not isfinite(final_earth_specific_energy_m2_s2)
            or final_earth_specific_energy_m2_s2 <= 0.0
        ):
            raise RuntimeError("Взлет не обеспечил положительную энергию ухода")
        actual_departure_excess_speed_m_s = sqrt(
            2.0 * final_earth_specific_energy_m2_s2
        )

        transfer = SolarTransferModel(
            self.mission_parameters, self.transfer_integration_parameters
        ).simulate(actual_departure_excess_speed_m_s)
        radius_error_m = transfer.mars_orbit_radius_error_m
        if (
            not isfinite(radius_error_m)
            or abs(radius_error_m) > self.mars_orbit_match_tolerance_m
        ):
            raise RuntimeError(
                "Радиус корабля отличается от радиуса орбиты Марса "
                f"на {radius_error_m:+.3f} м — больше заданного допуска"
            )

        mars_orbital_speed_m_s = sqrt(
            self.mission_parameters.sun_gravitational_parameter_m3_s2
            / self.mission_parameters.mars_orbit_radius_m
        )
        arrival_relative_speed_m_s = hypot(
            transfer.final_radial_velocity_m_s,
            transfer.final_tangential_velocity_m_s - mars_orbital_speed_m_s,
        )
        landing = MarsLandingModel(self.mars_landing_parameters).simulate(
            arrival_relative_speed_m_s, ascent.final_mass_kg
        )

        return MissionResult(
            benchmark=benchmark,
            ascent=ascent,
            transfer=transfer,
            landing=landing,
            actual_departure_excess_speed_m_s=actual_departure_excess_speed_m_s,
            arrival_relative_speed_m_s=arrival_relative_speed_m_s,
        )
