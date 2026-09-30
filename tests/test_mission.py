"""Проверки передачи состояния между этапами миссии."""

import unittest
from math import hypot, sqrt
from unittest.mock import patch

from mars_flight.config import (
    DEFAULT_EARTH_ASCENT_PARAMETERS,
    DEFAULT_MARS_LANDING_PARAMETERS,
    DEFAULT_PARAMETERS,
    DEFAULT_TRANSFER_INTEGRATION_PARAMETERS,
    MARS_ORBIT_MATCH_TOLERANCE_M,
)
from mars_flight.mission import MissionModel


class MissionModelTests(unittest.TestCase):
    def test_connects_stage_results(self) -> None:
        result = MissionModel(
            mission_parameters=DEFAULT_PARAMETERS,
            earth_ascent_parameters=DEFAULT_EARTH_ASCENT_PARAMETERS,
            transfer_integration_parameters=DEFAULT_TRANSFER_INTEGRATION_PARAMETERS,
            mars_landing_parameters=DEFAULT_MARS_LANDING_PARAMETERS,
            mars_orbit_match_tolerance_m=MARS_ORBIT_MATCH_TOLERANCE_M,
        ).simulate()

        self.assertAlmostEqual(
            result.actual_departure_excess_speed_m_s,
            sqrt(2.0 * float(result.ascent.specific_energy_m2_s2[-1])),
            delta=1.0e-6,
        )
        self.assertAlmostEqual(
            float(result.transfer.heliocentric_speed_m_s[0]),
            result.benchmark.earth_orbital_speed_m_s
            + result.actual_departure_excess_speed_m_s,
            delta=1.0e-6,
        )
        mars_orbital_speed_m_s = sqrt(
            DEFAULT_PARAMETERS.sun_gravitational_parameter_m3_s2
            / DEFAULT_PARAMETERS.mars_orbit_radius_m
        )
        self.assertAlmostEqual(
            result.arrival_relative_speed_m_s,
            hypot(
                result.transfer.final_radial_velocity_m_s,
                result.transfer.final_tangential_velocity_m_s
                - mars_orbital_speed_m_s,
            ),
            delta=1.0e-6,
        )
        self.assertEqual(
            result.landing.initial_excess_speed_m_s,
            result.arrival_relative_speed_m_s,
        )
        self.assertAlmostEqual(
            float(result.landing.mass_kg[0]),
            result.ascent.final_mass_kg,
            delta=1.0e-6,
        )

    def test_rejects_radius_miss_before_landing(self) -> None:
        for radius_error_m in (
            MARS_ORBIT_MATCH_TOLERANCE_M + 1.0,
            -MARS_ORBIT_MATCH_TOLERANCE_M - 1.0,
            float("nan"),
        ):
            with self.subTest(radius_error_m=radius_error_m):
                with patch("mars_flight.mission.SolarTransferModel") as transfer_model:
                    with patch("mars_flight.mission.MarsLandingModel") as landing_model:
                        transfer_result = (
                            transfer_model.return_value.simulate.return_value
                        )
                        transfer_result.mars_orbit_radius_error_m = radius_error_m
                        model = MissionModel(
                            mission_parameters=DEFAULT_PARAMETERS,
                            earth_ascent_parameters=DEFAULT_EARTH_ASCENT_PARAMETERS,
                            transfer_integration_parameters=(
                                DEFAULT_TRANSFER_INTEGRATION_PARAMETERS
                            ),
                            mars_landing_parameters=DEFAULT_MARS_LANDING_PARAMETERS,
                            mars_orbit_match_tolerance_m=(
                                MARS_ORBIT_MATCH_TOLERANCE_M
                            ),
                        )
                        with self.assertRaisesRegex(RuntimeError, "Радиус корабля"):
                            model.simulate()
                        landing_model.assert_not_called()

    def test_rejects_invalid_orbit_match_tolerance(self) -> None:
        for tolerance in (-1.0, float("nan"), float("inf")):
            with self.subTest(tolerance=tolerance):
                with self.assertRaises(ValueError):
                    MissionModel(
                        mission_parameters=DEFAULT_PARAMETERS,
                        earth_ascent_parameters=DEFAULT_EARTH_ASCENT_PARAMETERS,
                        transfer_integration_parameters=(
                            DEFAULT_TRANSFER_INTEGRATION_PARAMETERS
                        ),
                        mars_landing_parameters=DEFAULT_MARS_LANDING_PARAMETERS,
                        mars_orbit_match_tolerance_m=tolerance,
                    )


if __name__ == "__main__":
    unittest.main()
