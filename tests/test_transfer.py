"""Тесты численного пассивного перелёта в поле Солнца."""

import unittest
from dataclasses import fields, replace
from math import pi, sqrt

import numpy as np

from mars_flight.config import (
    DEFAULT_EARTH_ASCENT_PARAMETERS,
    DEFAULT_PARAMETERS,
    DEFAULT_TRANSFER_INTEGRATION_PARAMETERS,
    SECONDS_PER_DAY,
    TransferIntegrationParameters,
)
from mars_flight.earth import EarthAscentModel
from mars_flight.theory import HohmannTransfer
from mars_flight.transfer import SolarTransferModel, SolarTransferResult


class TransferIntegrationParametersTests(unittest.TestCase):
    def test_rejects_invalid_numeric_values(self) -> None:
        for parameter_field in fields(TransferIntegrationParameters):
            for invalid_value in (0.0, -1.0, float("nan"), float("inf")):
                with self.subTest(field=parameter_field.name, value=invalid_value):
                    with self.assertRaises(ValueError):
                        replace(
                            DEFAULT_TRANSFER_INTEGRATION_PARAMETERS,
                            **{parameter_field.name: invalid_value},
                        )

    def test_rejects_invalid_solver_limits(self) -> None:
        parameters = DEFAULT_TRANSFER_INTEGRATION_PARAMETERS
        with self.assertRaises(ValueError):
            replace(parameters, relative_tolerance=1.0)
        with self.assertRaises(ValueError):
            replace(parameters, maximum_step_s=parameters.maximum_time_s + 1.0)


class SolarTransferModelTests(unittest.TestCase):
    def setUp(self) -> None:
        self.benchmark: HohmannTransfer = HohmannTransfer.from_parameters(
            DEFAULT_PARAMETERS
        )
        self.model: SolarTransferModel = SolarTransferModel(
            DEFAULT_PARAMETERS, DEFAULT_TRANSFER_INTEGRATION_PARAMETERS
        )
        self.result: SolarTransferResult = self.model.simulate(
            self.benchmark.departure_excess_speed_m_s
        )

    def test_initial_speed_uses_earth_relative_excess(self) -> None:
        ascent = EarthAscentModel(DEFAULT_EARTH_ASCENT_PARAMETERS).simulate(
            self.benchmark.departure_excess_speed_m_s
        )
        actual_excess_speed_m_s = sqrt(
            2.0 * float(ascent.specific_energy_m2_s2[-1])
        )
        result = self.model.simulate(actual_excess_speed_m_s)

        self.assertAlmostEqual(
            float(result.heliocentric_speed_m_s[0]),
            self.benchmark.earth_orbital_speed_m_s + actual_excess_speed_m_s,
            delta=1.0e-6,
        )
        self.assertGreater(
            abs(
                float(result.heliocentric_speed_m_s[0])
                - ascent.final_radial_velocity_m_s
            ),
            1_000.0,
        )

    def test_reaches_mars_orbit_at_opposite_side(self) -> None:
        self.assertLess(float(self.result.x_m[-1]), 0.0)
        self.assertAlmostEqual(float(self.result.y_m[-1]), 0.0, delta=1.0)
        self.assertAlmostEqual(
            self.result.duration_s,
            self.benchmark.time_of_flight_s,
            delta=10.0,
        )
        self.assertAlmostEqual(
            self.result.final_radius_m,
            DEFAULT_PARAMETERS.mars_orbit_radius_m,
            delta=100.0,
        )
        self.assertAlmostEqual(
            self.result.final_heliocentric_speed_m_s,
            self.benchmark.arrival_heliocentric_speed_m_s,
            delta=0.01,
        )
        self.assertAlmostEqual(
            self.result.final_radial_velocity_m_s,
            0.0,
            delta=0.01,
        )

    def test_circular_orbit_special_case(self) -> None:
        result = self.model.simulate(0.0)
        mu = DEFAULT_PARAMETERS.sun_gravitational_parameter_m3_s2
        radius_m = DEFAULT_PARAMETERS.earth_orbit_radius_m
        expected_half_period_s = pi * sqrt(radius_m**3 / mu)
        expected_speed_m_s = sqrt(mu / radius_m)

        self.assertAlmostEqual(result.duration_s, expected_half_period_s, delta=10.0)
        self.assertAlmostEqual(result.final_radius_m, radius_m, delta=100.0)
        self.assertAlmostEqual(
            result.final_heliocentric_speed_m_s,
            expected_speed_m_s,
            delta=0.01,
        )

    def test_conserves_solar_energy_and_angular_momentum(self) -> None:
        energy = self.result.specific_energy_m2_s2
        angular_momentum = self.result.specific_angular_momentum_m2_s
        self.assertLess(
            float(np.max(np.abs(energy - energy[0])) / abs(energy[0])),
            1.0e-8,
        )
        self.assertLess(
            float(
                np.max(np.abs(angular_momentum - angular_momentum[0]))
                / abs(angular_momentum[0])
            ),
            1.0e-8,
        )
        self.assertTrue(bool(np.all(np.diff(self.result.time_s) > 0.0)))

    def test_mars_relative_velocity_has_expected_sign(self) -> None:
        mars_orbital_speed_m_s = sqrt(
            DEFAULT_PARAMETERS.sun_gravitational_parameter_m3_s2
            / DEFAULT_PARAMETERS.mars_orbit_radius_m
        )
        relative_velocity_m_s = (
            self.result.final_tangential_velocity_m_s - mars_orbital_speed_m_s
        )
        self.assertLess(relative_velocity_m_s, 0.0)
        self.assertAlmostEqual(
            relative_velocity_m_s,
            self.benchmark.arrival_relative_velocity_m_s,
            delta=0.01,
        )

    def test_departure_speed_changes_opposite_side_radius(self) -> None:
        reference = self.benchmark.departure_excess_speed_m_s
        lower = self.model.simulate(0.95 * reference)
        higher = self.model.simulate(1.05 * reference)
        self.assertLess(lower.mars_orbit_radius_error_m, -1.0e9)
        self.assertGreater(higher.mars_orbit_radius_error_m, 1.0e9)

    def test_rejects_invalid_departure_speed(self) -> None:
        for invalid_value in (-1.0, float("nan"), float("inf")):
            with self.subTest(value=invalid_value):
                with self.assertRaises(ValueError):
                    self.model.simulate(invalid_value)

        mu = DEFAULT_PARAMETERS.sun_gravitational_parameter_m3_s2
        radius = DEFAULT_PARAMETERS.earth_orbit_radius_m
        solar_escape_excess_speed_m_s = sqrt(2.0 * mu / radius) - sqrt(mu / radius)
        with self.assertRaises(ValueError):
            self.model.simulate(solar_escape_excess_speed_m_s + 1.0)

    def test_reports_missing_opposite_side_event(self) -> None:
        limited_parameters = replace(
            DEFAULT_TRANSFER_INTEGRATION_PARAMETERS,
            maximum_time_s=SECONDS_PER_DAY,
        )
        model = SolarTransferModel(DEFAULT_PARAMETERS, limited_parameters)
        with self.assertRaisesRegex(RuntimeError, "время"):
            model.simulate(self.benchmark.departure_excess_speed_m_s)
