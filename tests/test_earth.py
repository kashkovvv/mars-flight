"""Тесты численной модели вертикального взлета."""

import unittest
from dataclasses import fields, replace

import numpy as np
from numpy.typing import NDArray

from mars_flight.config import (
    DEFAULT_EARTH_ASCENT_PARAMETERS,
    DEFAULT_PARAMETERS,
    EarthAscentParameters,
)
from mars_flight.earth import EarthAscentModel, EarthAscentResult
from mars_flight.theory import HohmannTransfer


# Требуемая остаточная скорость из расчета Гомана, м/с.
TARGET_EXCESS_SPEED_M_S: float = HohmannTransfer.from_parameters(
    DEFAULT_PARAMETERS
).departure_excess_speed_m_s

# Допустимая относительная погрешность удельной энергии.
ENERGY_RELATIVE_TOLERANCE: float = 1.0e-9

# Допустимая абсолютная погрешность коэффициента перегрузки.
LOAD_FACTOR_ABSOLUTE_TOLERANCE: float = 1.0e-12

# Допустимая относительная погрешность истории массы.
MASS_HISTORY_RELATIVE_TOLERANCE: float = 1.0e-8

# Допустимая абсолютная погрешность истории массы, кг.
MASS_HISTORY_ABSOLUTE_TOLERANCE_KG: float = 1.0e-2

# Контрольная продолжительность взлета, с.
EXPECTED_DURATION_S: float = 475.538

# Контрольная высота выключения двигателя, м.
EXPECTED_FINAL_ALTITUDE_M: float = 2_274_604.0

# Контрольная радиальная скорость, м/с.
EXPECTED_FINAL_RADIAL_VELOCITY_M_S: float = 10_043.904

# Контрольная конечная масса, кг.
EXPECTED_FINAL_MASS_KG: float = 22_825.146

# Абсолютная погрешность контрольного времени, с.
DURATION_ABSOLUTE_TOLERANCE_S: float = 0.01

# Абсолютная погрешность контрольной высоты, м.
ALTITUDE_ABSOLUTE_TOLERANCE_M: float = 10.0

# Абсолютная погрешность контрольной скорости, м/с.
VELOCITY_ABSOLUTE_TOLERANCE_M_S: float = 0.01

# Абсолютная погрешность контрольной массы, кг.
MASS_REFERENCE_ABSOLUTE_TOLERANCE_KG: float = 0.1


class EarthAscentParametersTests(unittest.TestCase):
    def test_rejects_invalid_numeric_values(self) -> None:
        invalid_values = (
            0.0,
            -1.0,
            float("nan"),
            float("inf"),
        )

        for parameter_field in fields(EarthAscentParameters):
            for invalid_value in invalid_values:
                with self.subTest(field=parameter_field.name, value=invalid_value):
                    with self.assertRaises(ValueError):
                        replace(
                            DEFAULT_EARTH_ASCENT_PARAMETERS,
                            **{parameter_field.name: invalid_value},
                        )

    def test_requires_dry_mass_below_initial_mass(self) -> None:
        parameters = DEFAULT_EARTH_ASCENT_PARAMETERS

        with self.assertRaises(ValueError):
            replace(
                parameters,
                dry_mass_kg=parameters.initial_mass_kg,
            )

    def test_requires_relative_tolerance_below_one(self) -> None:
        with self.assertRaises(ValueError):
            replace(
                DEFAULT_EARTH_ASCENT_PARAMETERS,
                relative_tolerance=1.0,
            )

    def test_requires_step_not_larger_than_time(self) -> None:
        parameters = DEFAULT_EARTH_ASCENT_PARAMETERS

        with self.assertRaises(ValueError):
            replace(
                parameters,
                maximum_step_s=parameters.maximum_time_s + 1.0,
            )

    def test_requires_enough_initial_thrust(self) -> None:
        with self.assertRaises(ValueError):
            replace(
                DEFAULT_EARTH_ASCENT_PARAMETERS,
                maximum_thrust_n=1.0,
            )


class EarthAscentModelTests(unittest.TestCase):
    def setUp(self) -> None:
        self.model: EarthAscentModel = EarthAscentModel(DEFAULT_EARTH_ASCENT_PARAMETERS)
        self.result: EarthAscentResult = self.model.simulate(TARGET_EXCESS_SPEED_M_S)

    def test_rejects_invalid_target_speed(self) -> None:
        invalid_values = (
            0.0,
            -1.0,
            float("nan"),
            float("inf"),
        )

        for invalid_value in invalid_values:
            with self.subTest(value=invalid_value):
                with self.assertRaises(ValueError):
                    self.model.simulate(invalid_value)

    def test_rejects_unrepresentable_target_energy(self) -> None:
        with self.assertRaisesRegex(ValueError, "слишком велика"):
            self.model.simulate(1.0e155)

    def test_reaches_target_energy(self) -> None:
        target_energy_m2_s2 = 0.5 * TARGET_EXCESS_SPEED_M_S**2
        energy_tolerance_m2_s2 = target_energy_m2_s2 * ENERGY_RELATIVE_TOLERANCE

        self.assertAlmostEqual(
            float(self.result.specific_energy_m2_s2[-1]),
            target_energy_m2_s2,
            delta=energy_tolerance_m2_s2,
        )

    def test_respects_mass_and_load_limits(self) -> None:
        parameters = DEFAULT_EARTH_ASCENT_PARAMETERS

        self.assertGreater(
            self.result.final_mass_kg,
            parameters.dry_mass_kg,
        )
        self.assertLessEqual(
            self.result.maximum_load_factor,
            (parameters.maximum_load_factor + LOAD_FACTOR_ABSOLUTE_TOLERANCE),
        )
        self.assertEqual(self.result.thrust_n.shape, self.result.time_s.shape)
        self.assertAlmostEqual(
            float(self.result.thrust_n[0]),
            parameters.maximum_thrust_n,
            delta=1.0e-6,
        )
        self.assertLessEqual(
            float(np.max(self.result.thrust_n)),
            parameters.maximum_thrust_n + 1.0e-6,
        )
        self.assertLess(
            float(self.result.thrust_n[-1]),
            float(self.result.thrust_n[0]),
        )
        self.assertGreater(
            self.result.final_altitude_m,
            0.0,
        )
        self.assertGreater(
            self.result.final_radial_velocity_m_s,
            0.0,
        )

    def test_mass_matches_analytical_solution(self) -> None:
        parameters = DEFAULT_EARTH_ASCENT_PARAMETERS

        switch_mass_kg = parameters.maximum_thrust_n / (
            parameters.maximum_load_factor * parameters.standard_gravity_m_s2
        )
        switch_time_s = (
            (parameters.initial_mass_kg - switch_mass_kg)
            * parameters.exhaust_velocity_m_s
            / parameters.maximum_thrust_n
        )

        expected_mass_kg: NDArray[np.float64] = np.where(
            self.result.time_s <= switch_time_s,
            (
                parameters.initial_mass_kg
                - (
                    parameters.maximum_thrust_n
                    * self.result.time_s
                    / parameters.exhaust_velocity_m_s
                )
            ),
            (
                switch_mass_kg
                * np.exp(
                    -(
                        parameters.maximum_load_factor
                        * parameters.standard_gravity_m_s2
                        * (self.result.time_s - switch_time_s)
                        / parameters.exhaust_velocity_m_s
                    )
                )
            ),
        )

        np.testing.assert_allclose(
            self.result.mass_kg,
            expected_mass_kg,
            rtol=MASS_HISTORY_RELATIVE_TOLERANCE,
            atol=MASS_HISTORY_ABSOLUTE_TOLERANCE_KG,
        )

    def test_velocity_matches_rocket_equation_with_gravity_loss(self) -> None:
        parameters = DEFAULT_EARTH_ASCENT_PARAMETERS
        gravity_m_s2 = (
            parameters.earth_gravitational_parameter_m3_s2 / self.result.radius_m**2
        )
        gravity_loss_m_s = float(
            np.sum(
                0.5
                * (gravity_m_s2[1:] + gravity_m_s2[:-1])
                * np.diff(self.result.time_s)
            )
        )
        predicted_velocity_m_s = (
            parameters.exhaust_velocity_m_s
            * np.log(parameters.initial_mass_kg / self.result.final_mass_kg)
            - gravity_loss_m_s
        )
        self.assertAlmostEqual(
            self.result.final_radial_velocity_m_s,
            predicted_velocity_m_s,
            delta=0.01,
        )

    def test_initial_load_comes_only_from_thrust(self) -> None:
        parameters = DEFAULT_EARTH_ASCENT_PARAMETERS
        thrust_n = min(
            parameters.maximum_thrust_n,
            parameters.initial_mass_kg
            * parameters.maximum_load_factor
            * parameters.standard_gravity_m_s2,
        )
        thrust_acceleration_m_s2 = thrust_n / parameters.initial_mass_kg
        gravitational_acceleration_m_s2 = (
            parameters.earth_gravitational_parameter_m3_s2
            / parameters.earth_radius_m**2
        )
        self.assertAlmostEqual(
            float(self.result.load_factor[0]),
            thrust_acceleration_m_s2 / parameters.standard_gravity_m_s2,
        )
        self.assertGreater(
            float(self.result.load_factor[0]),
            (thrust_acceleration_m_s2 - gravitational_acceleration_m_s2)
            / parameters.standard_gravity_m_s2,
        )

    def test_reference_values(self) -> None:
        self.assertAlmostEqual(
            self.result.duration_s,
            EXPECTED_DURATION_S,
            delta=DURATION_ABSOLUTE_TOLERANCE_S,
        )
        self.assertAlmostEqual(
            self.result.final_altitude_m,
            EXPECTED_FINAL_ALTITUDE_M,
            delta=ALTITUDE_ABSOLUTE_TOLERANCE_M,
        )
        self.assertAlmostEqual(
            self.result.final_radial_velocity_m_s,
            EXPECTED_FINAL_RADIAL_VELOCITY_M_S,
            delta=VELOCITY_ABSOLUTE_TOLERANCE_M_S,
        )
        self.assertAlmostEqual(
            self.result.final_mass_kg,
            EXPECTED_FINAL_MASS_KG,
            delta=MASS_REFERENCE_ABSOLUTE_TOLERANCE_KG,
        )

    def test_reports_time_limit(self) -> None:
        parameters = replace(
            DEFAULT_EARTH_ASCENT_PARAMETERS,
            maximum_time_s=1.0,
        )
        with self.assertRaisesRegex(RuntimeError, "время"):
            EarthAscentModel(parameters).simulate(TARGET_EXCESS_SPEED_M_S)

    def test_reports_fuel_exhaustion(self) -> None:
        insufficient_parameters = replace(
            DEFAULT_EARTH_ASCENT_PARAMETERS,
            dry_mass_kg=490_000.0,
        )
        model = EarthAscentModel(insufficient_parameters)

        with self.assertRaisesRegex(RuntimeError, "Топливо"):
            model.simulate(TARGET_EXCESS_SPEED_M_S)
