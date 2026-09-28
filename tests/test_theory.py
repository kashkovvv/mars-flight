"""Тесты аналитического перелёта Гомана."""

import unittest

from mars_flight.config import (
    ASTRONOMICAL_UNIT_M,
    DEFAULT_PARAMETERS,
    METRES_PER_KILOMETRE,
    SECONDS_PER_DAY,
    SUN_GRAVITATIONAL_PARAMETER_M3_S2,
    MissionParameters,
)
from mars_flight.theory import HohmannTransfer


EXPECTED_TIME_OF_FLIGHT_DAYS: float = 258.8658
EXPECTED_DEPARTURE_EXCESS_SPEED_KM_S: float = 2.9447
EXPECTED_ARRIVAL_RELATIVE_VELOCITY_KM_S: float = -2.6489
REFERENCE_TOLERANCE: float = 0.001


class MissionParametersTests(unittest.TestCase):
    def test_rejects_invalid_numeric_values(self) -> None:
        invalid_values = (
            0.0,
            -1.0,
            float("nan"),
            float("inf"),
        )

        for invalid_value in invalid_values:
            with self.subTest(value=invalid_value):
                with self.assertRaises(ValueError):
                    MissionParameters(
                        sun_gravitational_parameter_m3_s2=invalid_value,
                        earth_orbit_radius_m=ASTRONOMICAL_UNIT_M,
                        mars_orbit_radius_m=2.0 * ASTRONOMICAL_UNIT_M,
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
            delta=REFERENCE_TOLERANCE,
        )
        self.assertAlmostEqual(
            transfer.departure_excess_speed_m_s / METRES_PER_KILOMETRE,
            EXPECTED_DEPARTURE_EXCESS_SPEED_KM_S,
            delta=REFERENCE_TOLERANCE,
        )
        self.assertAlmostEqual(
            transfer.arrival_relative_velocity_m_s / METRES_PER_KILOMETRE,
            EXPECTED_ARRIVAL_RELATIVE_VELOCITY_KM_S,
            delta=REFERENCE_TOLERANCE,
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
