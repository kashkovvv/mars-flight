"""Аналитические ориентиры для численной модели."""

from dataclasses import dataclass
from math import pi, sqrt
from typing import Self

from .config import MissionParameters


@dataclass(frozen=True)
class HohmannTransfer:
    """Параметры перелета Гомана в единицах СИ."""

    semi_major_axis_m: float
    earth_orbital_speed_m_s: float
    mars_orbital_speed_m_s: float
    departure_heliocentric_speed_m_s: float
    arrival_heliocentric_speed_m_s: float
    departure_excess_speed_m_s: float
    arrival_relative_velocity_m_s: float
    arrival_relative_speed_m_s: float
    time_of_flight_s: float

    @classmethod
    def from_parameters(cls, parameters: MissionParameters) -> Self:
        """Рассчитать перелет по заданным параметрам."""

        mu_sun = parameters.sun_gravitational_parameter_m3_s2
        earth_radius = parameters.earth_orbit_radius_m
        mars_radius = parameters.mars_orbit_radius_m

        semi_major_axis = (earth_radius + mars_radius) / 2.0

        earth_orbital_speed = sqrt(mu_sun / earth_radius)
        mars_orbital_speed = sqrt(mu_sun / mars_radius)

        departure_heliocentric_speed = sqrt(
            mu_sun * (2.0 / earth_radius - 1.0 / semi_major_axis)
        )
        arrival_heliocentric_speed = sqrt(
            mu_sun * (2.0 / mars_radius - 1.0 / semi_major_axis)
        )

        departure_excess_speed = departure_heliocentric_speed - earth_orbital_speed
        arrival_relative_velocity = arrival_heliocentric_speed - mars_orbital_speed

        time_of_flight = pi * sqrt(semi_major_axis**3 / mu_sun)

        return cls(
            semi_major_axis_m=semi_major_axis,
            earth_orbital_speed_m_s=earth_orbital_speed,
            mars_orbital_speed_m_s=mars_orbital_speed,
            departure_heliocentric_speed_m_s=departure_heliocentric_speed,
            arrival_heliocentric_speed_m_s=arrival_heliocentric_speed,
            departure_excess_speed_m_s=departure_excess_speed,
            arrival_relative_velocity_m_s=arrival_relative_velocity,
            arrival_relative_speed_m_s=abs(arrival_relative_velocity),
            time_of_flight_s=time_of_flight,
        )
