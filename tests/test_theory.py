"""Тесты аналитического перелета Гомана."""

import unittest
from dataclasses import fields, replace

from mars_flight.config import (
    ASTRONOMICAL_UNIT_M,
    DEFAULT_PARAMETERS,
    METRES_PER_KILOMETRE,
    SECONDS_PER_DAY,
    SUN_GRAVITATIONAL_PARAMETER_M3_S2,
    MissionParameters,
)
from mars_flight.theory import HohmannTransfer


# Контрольное время перелета Гомана, сут.
EXPECTED_TIME_OF_FLIGHT_DAYS: float = 258.8658

# Контрольная скорость ухода относительно Земли, км/с.
EXPECTED_DEPARTURE_EXCESS_SPEED_KM_S: float = 2.9447

# Контрольная проекция скорости относительно Марса, км/с.
EXPECTED_ARRIVAL_RELATIVE_VELOCITY_KM_S: float = -2.6489

# Абсолютная погрешность сравнения времени, сут.
TIME_TOLERANCE_DAYS: float = 0.001

# Абсолютная погрешность сравнения скоростей, км/с.
SPEED_TOLERANCE_KM_S: float = 0.001


class MissionParametersTests(unittest.TestCase):
    def test_rejects_invalid_numeric_values(self) -> None:
        invalid_values = (
            0.0,
            -1.0,
            float("nan"),
            float("inf"),
        )

        for parameter_field in fields(MissionParameters):
            for invalid_value in invalid_values:
                with self.subTest(field=parameter_field.name, value=invalid_value):
                    with self.assertRaises(ValueError):
                        replace(
                            DEFAULT_PARAMETERS,
                            **{parameter_field.name: invalid_value},
                        )

    def test_requires_larger_mars_orbit(self) -> None:
        with self.assertRaises(ValueError):
            MissionParameters(
                sun_gravitational_parameter_m3_s2=SUN_GRAVITATIONAL_PARAMETER_M3_S2,
                earth_orbit_radius_m=ASTRONOMICAL_UNIT_M,
                mars_orbit_radius_m=ASTRONOMICAL_UNIT_M,
            )


class HohmannTransferTests(unittest.TestCase):
    def test_reference_values(self) -> None:
        transfer = HohmannTransfer.from_parameters(DEFAULT_PARAMETERS)

        self.assertAlmostEqual(
            transfer.time_of_flight_s / SECONDS_PER_DAY,
            EXPECTED_TIME_OF_FLIGHT_DAYS,
            delta=TIME_TOLERANCE_DAYS,
        )
        self.assertAlmostEqual(
            transfer.departure_excess_speed_m_s / METRES_PER_KILOMETRE,
            EXPECTED_DEPARTURE_EXCESS_SPEED_KM_S,
            delta=SPEED_TOLERANCE_KM_S,
        )
        self.assertAlmostEqual(
            transfer.arrival_relative_velocity_m_s / METRES_PER_KILOMETRE,
            EXPECTED_ARRIVAL_RELATIVE_VELOCITY_KM_S,
            delta=SPEED_TOLERANCE_KM_S,
        )

    def test_transfer_geometry(self) -> None:
        transfer = HohmannTransfer.from_parameters(DEFAULT_PARAMETERS)

        self.assertGreater(
            transfer.semi_major_axis_m,
            DEFAULT_PARAMETERS.earth_orbit_radius_m,
        )
        self.assertLess(
            transfer.semi_major_axis_m,
            DEFAULT_PARAMETERS.mars_orbit_radius_m,
        )

    def test_energy_and_angular_momentum_conservation(self) -> None:
        parameters = DEFAULT_PARAMETERS
        transfer = HohmannTransfer.from_parameters(parameters)
        mu = parameters.sun_gravitational_parameter_m3_s2
        earth_radius_m = parameters.earth_orbit_radius_m
        mars_radius_m = parameters.mars_orbit_radius_m
        expected_energy_m2_s2 = -mu / (2.0 * transfer.semi_major_axis_m)

        for radius_m, speed_m_s in (
            (earth_radius_m, transfer.departure_heliocentric_speed_m_s),
            (mars_radius_m, transfer.arrival_heliocentric_speed_m_s),
        ):
            with self.subTest(radius_m=radius_m):
                self.assertAlmostEqual(
                    0.5 * speed_m_s**2 - mu / radius_m,
                    expected_energy_m2_s2,
                    delta=1.0e-6,
                )

        self.assertAlmostEqual(
            earth_radius_m * transfer.departure_heliocentric_speed_m_s,
            mars_radius_m * transfer.arrival_heliocentric_speed_m_s,
            delta=1.0,
        )

    def test_frame_velocity_bridge(self) -> None:
        transfer = HohmannTransfer.from_parameters(DEFAULT_PARAMETERS)
        self.assertAlmostEqual(
            transfer.earth_orbital_speed_m_s + transfer.departure_excess_speed_m_s,
            transfer.departure_heliocentric_speed_m_s,
        )
        self.assertAlmostEqual(
            transfer.mars_orbital_speed_m_s + transfer.arrival_relative_velocity_m_s,
            transfer.arrival_heliocentric_speed_m_s,
        )

    def test_speed_and_velocity_conventions(self) -> None:
        transfer = HohmannTransfer.from_parameters(DEFAULT_PARAMETERS)

        self.assertGreater(
            transfer.departure_excess_speed_m_s,
            0.0,
        )
        self.assertLess(
            transfer.arrival_relative_velocity_m_s,
            0.0,
        )
        self.assertEqual(
            transfer.arrival_relative_speed_m_s,
            abs(transfer.arrival_relative_velocity_m_s),
        )
