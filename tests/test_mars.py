"""Проверки радиального торможения и посадки на Марс."""

import unittest
from dataclasses import fields, replace
from math import exp, sqrt

import numpy as np

from mars_flight.config import (
    DEFAULT_EARTH_ASCENT_PARAMETERS,
    DEFAULT_MARS_LANDING_PARAMETERS,
    DEFAULT_PARAMETERS,
    DEFAULT_TRANSFER_INTEGRATION_PARAMETERS,
    MarsLandingParameters,
)
from mars_flight.earth import EarthAscentModel
from mars_flight.mars import MarsLandingModel, MarsLandingResult
from mars_flight.theory import HohmannTransfer
from mars_flight.transfer import SolarTransferModel


class MarsLandingParametersTests(unittest.TestCase):
    def test_rejects_invalid_numeric_values(self) -> None:
        for field in fields(MarsLandingParameters):
            for value in (0.0, -1.0, float("nan"), float("inf")):
                with self.subTest(field=field.name, value=value):
                    with self.assertRaises(ValueError):
                        replace(
                            DEFAULT_MARS_LANDING_PARAMETERS,
                            **{field.name: value},
                        )

    def test_rejects_invalid_geometry_and_solver_limits(self) -> None:
        p = DEFAULT_MARS_LANDING_PARAMETERS
        for change in (
            {"initial_radius_m": p.mars_radius_m},
            {"relative_tolerance": 1.0},
            {"coast_maximum_step_s": p.maximum_time_s + 1.0},
            {"burn_maximum_step_s": p.maximum_time_s + 1.0},
        ):
            with self.subTest(change=change):
                with self.assertRaises(ValueError):
                    replace(p, **change)


class MarsLandingModelTests(unittest.TestCase):
    arrival_relative_speed_m_s: float
    initial_mass_kg: float
    result: MarsLandingResult

    @classmethod
    def setUpClass(cls) -> None:
        p = DEFAULT_PARAMETERS
        benchmark = HohmannTransfer.from_parameters(p)
        ascent = EarthAscentModel(DEFAULT_EARTH_ASCENT_PARAMETERS).simulate(
            benchmark.departure_excess_speed_m_s
        )
        transfer = SolarTransferModel(
            p, DEFAULT_TRANSFER_INTEGRATION_PARAMETERS
        ).simulate(sqrt(2.0 * float(ascent.specific_energy_m2_s2[-1])))
        mars_orbital_speed_m_s = sqrt(
            p.sun_gravitational_parameter_m3_s2 / p.mars_orbit_radius_m
        )
        cls.arrival_relative_speed_m_s = sqrt(
            transfer.final_radial_velocity_m_s**2
            + (transfer.final_tangential_velocity_m_s - mars_orbital_speed_m_s) ** 2
        )
        cls.initial_mass_kg = ascent.final_mass_kg
        cls.result = MarsLandingModel(DEFAULT_MARS_LANDING_PARAMETERS).simulate(
            cls.arrival_relative_speed_m_s, cls.initial_mass_kg
        )

    def test_soft_landing_with_mass_and_load_limits(self) -> None:
        result = self.result
        p = DEFAULT_MARS_LANDING_PARAMETERS
        self.assertLess(
            abs(result.final_altitude_m), p.contact_altitude_tolerance_m
        )
        self.assertLess(abs(result.final_radial_velocity_m_s), 0.1)
        self.assertAlmostEqual(float(result.mass_kg[0]), self.initial_mass_kg)
        self.assertGreater(result.final_mass_kg, p.dry_mass_kg)
        self.assertLessEqual(result.maximum_load_factor, p.maximum_load_factor + 1e-9)
        self.assertAlmostEqual(result.final_mass_kg, 5_938.3, delta=10.0)
        self.assertAlmostEqual(result.burn_duration_s, 205.95, delta=1.0)
        self.assertTrue(bool(np.all(np.diff(result.time_s) > 0.0)))
        self.assertTrue(bool(np.all(np.diff(result.mass_kg) <= 1e-7)))

    def test_coast_conserves_energy_and_mass(self) -> None:
        result = self.result
        coast_mask = result.time_s <= result.ignition_time_s
        energy = result.specific_energy_m2_s2[coast_mask]
        mass = result.mass_kg[coast_mask]
        self.assertLess(float(np.max(np.abs(energy - energy[0]))), 0.1)
        self.assertLess(float(np.max(np.abs(mass - mass[0]))), 1e-6)
        self.assertTrue(bool(np.all(result.thrust_n[coast_mask] == 0.0)))

    def test_burn_mass_matches_rocket_flow(self) -> None:
        p = DEFAULT_MARS_LANDING_PARAMETERS
        acceleration = min(
            p.maximum_thrust_n / self.initial_mass_kg,
            p.maximum_load_factor * p.standard_gravity_m_s2,
        )
        expected_mass_kg = self.initial_mass_kg * exp(
            -acceleration * self.result.burn_duration_s / p.exhaust_velocity_m_s
        )
        self.assertAlmostEqual(self.result.final_mass_kg, expected_mass_kg, delta=0.1)

    def test_faster_arrival_requires_more_braking(self) -> None:
        model = MarsLandingModel(DEFAULT_MARS_LANDING_PARAMETERS)
        slower = model.simulate(
            0.95 * self.arrival_relative_speed_m_s, self.initial_mass_kg
        )
        faster = model.simulate(
            1.05 * self.arrival_relative_speed_m_s, self.initial_mass_kg
        )
        self.assertLess(slower.ignition_altitude_m, self.result.ignition_altitude_m)
        self.assertGreater(faster.ignition_altitude_m, self.result.ignition_altitude_m)
        self.assertGreater(slower.final_mass_kg, self.result.final_mass_kg)
        self.assertLess(faster.final_mass_kg, self.result.final_mass_kg)

    def test_rejects_infeasible_inputs(self) -> None:
        model = MarsLandingModel(DEFAULT_MARS_LANDING_PARAMETERS)
        for speed in (-1.0, float("nan"), float("inf"), 1e200):
            with self.subTest(speed=speed):
                with self.assertRaises(ValueError):
                    model.simulate(speed, self.initial_mass_kg)
        for mass in (0.0, float("nan"), float("inf"), 5_000.0):
            with self.subTest(mass=mass):
                with self.assertRaises(ValueError):
                    model.simulate(self.arrival_relative_speed_m_s, mass)

    def test_previous_20_tonne_dry_mass_exhausts_fuel(self) -> None:
        p = replace(DEFAULT_MARS_LANDING_PARAMETERS, dry_mass_kg=20_000.0)
        with self.assertRaisesRegex(RuntimeError, "Топливо закончилось"):
            MarsLandingModel(p).simulate(
                self.arrival_relative_speed_m_s, self.initial_mass_kg
            )

    def test_rejects_insufficient_thrust_and_altitude(self) -> None:
        p = DEFAULT_MARS_LANDING_PARAMETERS
        surface_gravity = p.mars_gravitational_parameter_m3_s2 / p.mars_radius_m**2
        weak = replace(
            p, maximum_thrust_n=0.9 * self.initial_mass_kg * surface_gravity
        )
        with self.assertRaisesRegex(ValueError, "Тяги недостаточно"):
            MarsLandingModel(weak).simulate(
                self.arrival_relative_speed_m_s, self.initial_mass_kg
            )
        low = replace(p, initial_radius_m=p.mars_radius_m + 100_000.0)
        with self.assertRaisesRegex(ValueError, "Высоты"):
            MarsLandingModel(low).simulate(
                self.arrival_relative_speed_m_s, self.initial_mass_kg
            )

    def test_reports_time_limit(self) -> None:
        p = replace(
            DEFAULT_MARS_LANDING_PARAMETERS,
            maximum_time_s=100.0,
            coast_maximum_step_s=10.0,
        )
        with self.assertRaisesRegex(RuntimeError, "время"):
            MarsLandingModel(p).simulate(
                self.arrival_relative_speed_m_s, self.initial_mass_kg
            )
