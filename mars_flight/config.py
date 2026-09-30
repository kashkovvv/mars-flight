"""Физические параметры модели."""

from dataclasses import dataclass
from math import isfinite


# Коэффициенты перевода единиц: используются только при выводе.
# Количество секунд в сутках, с/сут.
SECONDS_PER_DAY: float = 86_400.0

# Количество метров в километре, м/км.
METRES_PER_KILOMETRE: float = 1_000.0

# Количество метров в миллионе километров, м/(млн км).
METRES_PER_MILLION_KILOMETRES: float = 1_000_000_000.0

# Количество килограммов в тонне, кг/т.
KILOGRAMS_PER_TONNE: float = 1_000.0

# Параметры круговых орбит Земли и Марса в поле Солнца.
# Астрономическая единица, м.
ASTRONOMICAL_UNIT_M: float = 149_597_870_700.0

# Гравитационный параметр Солнца, м^3/с^2.
SUN_GRAVITATIONAL_PARAMETER_M3_S2: float = 1.327_124_400_18e20

# Радиус круговой орбиты Земли, м.
EARTH_ORBIT_RADIUS_M: float = ASTRONOMICAL_UNIT_M

# Радиус круговой орбиты Марса, м.
MARS_ORBIT_RADIUS_M: float = 1.523_679 * ASTRONOMICAL_UNIT_M

# Физические параметры вертикального взлета с Земли.
# Гравитационный параметр Земли, м^3/с^2.
EARTH_GRAVITATIONAL_PARAMETER_M3_S2: float = 3.986_004_418e14

# Средний радиус Земли, м.
EARTH_RADIUS_M: float = 6_371_000.0

# Стандартное ускорение для расчета перегрузки, м/с^2.
STANDARD_GRAVITY_M_S2: float = 9.806_65

# Начальная масса эффективной модели корабля, кг.
ASCENT_INITIAL_MASS_KG: float = 500_000.0

# Масса корабля без топлива, кг.
ASCENT_DRY_MASS_KG: float = 5_000.0

# Эффективная скорость истечения топлива, м/с.
ASCENT_EXHAUST_VELOCITY_M_S: float = 4_500.0

# Максимальная тяга двигателя, Н.
ASCENT_MAXIMUM_THRUST_N: float = 12_000_000.0

# Предельная перегрузка штатного режима, в единицах g0.
ASCENT_MAXIMUM_LOAD_FACTOR: float = 3.0

# Настройки численного интегрирования взлета.
# Предельная продолжительность расчета взлета, с.
ASCENT_MAXIMUM_TIME_S: float = 1_000.0

# Максимальный шаг численного интегрирования, с.
ASCENT_MAXIMUM_STEP_S: float = 0.5

# Относительная погрешность численного интегрирования.
ASCENT_RELATIVE_TOLERANCE: float = 1.0e-9

# Абсолютная погрешность расстояния, м.
ASCENT_POSITION_ABSOLUTE_TOLERANCE_M: float = 1.0e-3

# Абсолютная погрешность скорости, м/с.
ASCENT_VELOCITY_ABSOLUTE_TOLERANCE_M_S: float = 1.0e-6

# Абсолютная погрешность массы, кг.
ASCENT_MASS_ABSOLUTE_TOLERANCE_KG: float = 1.0e-3


# Настройки численного интегрирования перелета в поле Солнца.
# Предельная продолжительность численного перелета, с.
TRANSFER_MAXIMUM_TIME_S: float = 400.0 * SECONDS_PER_DAY

# Максимальный шаг интегрирования перелета, с.
TRANSFER_MAXIMUM_STEP_S: float = 0.25 * SECONDS_PER_DAY

# Относительная погрешность интегрирования перелета.
TRANSFER_RELATIVE_TOLERANCE: float = 1.0e-10

# Абсолютная погрешность координат перелета, м.
TRANSFER_POSITION_ABSOLUTE_TOLERANCE_M: float = 1.0

# Абсолютная погрешность компонент скорости перелета, м/с.
TRANSFER_VELOCITY_ABSOLUTE_TOLERANCE_M_S: float = 1.0e-6


# Физические параметры посадки на Марс.
# Гравитационный параметр Марса, м^3/с^2.
MARS_GRAVITATIONAL_PARAMETER_M3_S2: float = 4.282_837_362e13

# Средний радиус Марса, м.
MARS_RADIUS_M: float = 3_389_500.0

# Радиус сферы влияния Марса относительно его центра, м.
MARS_INITIAL_RADIUS_M: float = MARS_ORBIT_RADIUS_M * (
    MARS_GRAVITATIONAL_PARAMETER_M3_S2 / SUN_GRAVITATIONAL_PARAMETER_M3_S2
) ** (2.0 / 5.0)

# Допустимое расхождение с радиусом орбиты Марса при соединении этапов, м.
MARS_ORBIT_MATCH_TOLERANCE_M: float = 1_000.0

# Допустимое отклонение точки остановки от поверхности Марса, м.
MARS_CONTACT_ALTITUDE_TOLERANCE_M: float = 1.0

# Максимальная тяга посадочного двигателя, Н.
MARS_MAXIMUM_THRUST_N: float = 1_000_000.0

# Предельная перегрузка при посадке, в единицах g0.
MARS_MAXIMUM_LOAD_FACTOR: float = 3.0

# Настройки численного интегрирования посадки.
# Предельная продолжительность расчета посадки, с.
MARS_MAXIMUM_TIME_S: float = 5.0 * SECONDS_PER_DAY

# Максимальный шаг свободного падения, с.
MARS_COAST_MAXIMUM_STEP_S: float = 300.0

# Максимальный шаг торможения, с.
MARS_BURN_MAXIMUM_STEP_S: float = 1.0

# Относительная погрешность интегрирования посадки.
MARS_RELATIVE_TOLERANCE: float = 1.0e-10

# Абсолютная погрешность координаты, м.
MARS_POSITION_ABSOLUTE_TOLERANCE_M: float = 1.0e-3

# Абсолютная погрешность радиальной скорости, м/с.
MARS_VELOCITY_ABSOLUTE_TOLERANCE_M_S: float = 1.0e-6

# Абсолютная погрешность массы, кг.
MARS_MASS_ABSOLUTE_TOLERANCE_KG: float = 1.0e-3


@dataclass(frozen=True)
class MissionParameters:
    """Параметры круговых орбит и солнечного перелета в единицах СИ."""

    sun_gravitational_parameter_m3_s2: float
    earth_orbit_radius_m: float
    mars_orbit_radius_m: float

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        values: dict[str, float] = {
            "sun_gravitational_parameter_m3_s2": self.sun_gravitational_parameter_m3_s2,
            "earth_orbit_radius_m": self.earth_orbit_radius_m,
            "mars_orbit_radius_m": self.mars_orbit_radius_m,
        }

        for name, value in values.items():
            if not isfinite(value) or value <= 0.0:
                raise ValueError(f"{name}: ожидалось конечное положительное число")

        if self.mars_orbit_radius_m <= self.earth_orbit_radius_m:
            raise ValueError(
                "Радиус орбиты Марса должен быть больше радиуса орбиты Земли"
            )


@dataclass(frozen=True)
class EarthAscentParameters:
    """Параметры вертикального взлета в единицах СИ."""

    earth_gravitational_parameter_m3_s2: float
    earth_radius_m: float
    standard_gravity_m_s2: float
    initial_mass_kg: float
    dry_mass_kg: float
    exhaust_velocity_m_s: float
    maximum_thrust_n: float
    maximum_load_factor: float
    maximum_time_s: float
    maximum_step_s: float
    relative_tolerance: float
    position_absolute_tolerance_m: float
    velocity_absolute_tolerance_m_s: float
    mass_absolute_tolerance_kg: float

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        values: dict[str, float] = {
            "earth_gravitational_parameter_m3_s2": (
                self.earth_gravitational_parameter_m3_s2
            ),
            "earth_radius_m": self.earth_radius_m,
            "standard_gravity_m_s2": self.standard_gravity_m_s2,
            "initial_mass_kg": self.initial_mass_kg,
            "dry_mass_kg": self.dry_mass_kg,
            "exhaust_velocity_m_s": self.exhaust_velocity_m_s,
            "maximum_thrust_n": self.maximum_thrust_n,
            "maximum_load_factor": self.maximum_load_factor,
            "maximum_time_s": self.maximum_time_s,
            "maximum_step_s": self.maximum_step_s,
            "relative_tolerance": self.relative_tolerance,
            "position_absolute_tolerance_m": self.position_absolute_tolerance_m,
            "velocity_absolute_tolerance_m_s": self.velocity_absolute_tolerance_m_s,
            "mass_absolute_tolerance_kg": self.mass_absolute_tolerance_kg,
        }

        for name, value in values.items():
            if not isfinite(value) or value <= 0.0:
                raise ValueError(f"{name}: ожидалось конечное положительное число")

        if self.dry_mass_kg >= self.initial_mass_kg:
            raise ValueError("Сухая масса должна быть меньше начальной массы")

        if self.relative_tolerance >= 1.0:
            raise ValueError("Относительная погрешность должна быть меньше единицы")

        if self.maximum_step_s > self.maximum_time_s:
            raise ValueError("Максимальный шаг не должен превышать время расчета")

        initial_thrust_n = min(
            self.maximum_thrust_n,
            (
                self.initial_mass_kg
                * self.maximum_load_factor
                * self.standard_gravity_m_s2
            ),
        )
        surface_weight_n = (
            self.initial_mass_kg
            * self.earth_gravitational_parameter_m3_s2
            / self.earth_radius_m**2
        )

        if initial_thrust_n <= surface_weight_n:
            raise ValueError("Начальной тяги недостаточно для отрыва от Земли")


@dataclass(frozen=True)
class TransferIntegrationParameters:
    """Параметры численного решения пассивного перелета в СИ."""

    maximum_time_s: float
    maximum_step_s: float
    relative_tolerance: float
    position_absolute_tolerance_m: float
    velocity_absolute_tolerance_m_s: float

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        values: dict[str, float] = {
            "maximum_time_s": self.maximum_time_s,
            "maximum_step_s": self.maximum_step_s,
            "relative_tolerance": self.relative_tolerance,
            "position_absolute_tolerance_m": self.position_absolute_tolerance_m,
            "velocity_absolute_tolerance_m_s": self.velocity_absolute_tolerance_m_s,
        }
        for name, value in values.items():
            if not isfinite(value) or value <= 0.0:
                raise ValueError(f"{name}: ожидалось конечное положительное число")

        if self.relative_tolerance >= 1.0:
            raise ValueError("Относительная погрешность должна быть меньше единицы")
        if self.maximum_step_s > self.maximum_time_s:
            raise ValueError("Максимальный шаг не должен превышать время расчета")


@dataclass(frozen=True)
class MarsLandingParameters:
    """Параметры вертикальной посадки на Марс в единицах СИ."""

    mars_gravitational_parameter_m3_s2: float
    mars_radius_m: float
    initial_radius_m: float
    contact_altitude_tolerance_m: float
    dry_mass_kg: float
    exhaust_velocity_m_s: float
    maximum_thrust_n: float
    maximum_load_factor: float
    standard_gravity_m_s2: float
    maximum_time_s: float
    coast_maximum_step_s: float
    burn_maximum_step_s: float
    relative_tolerance: float
    position_absolute_tolerance_m: float
    velocity_absolute_tolerance_m_s: float
    mass_absolute_tolerance_kg: float

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        values = vars(self)
        for name, value in values.items():
            if not isfinite(value) or value <= 0.0:
                raise ValueError(f"{name}: ожидалось конечное положительное число")
        if self.initial_radius_m <= self.mars_radius_m:
            raise ValueError("Начальный радиус должен превышать радиус Марса")
        if self.relative_tolerance >= 1.0:
            raise ValueError("Относительная погрешность должна быть меньше единицы")
        if (
            max(self.coast_maximum_step_s, self.burn_maximum_step_s)
            > self.maximum_time_s
        ):
            raise ValueError("Шаг интегрирования не должен превышать время расчёта")


# Параметры стандартного перелета Земля — Марс.
DEFAULT_PARAMETERS: MissionParameters = MissionParameters(
    sun_gravitational_parameter_m3_s2=SUN_GRAVITATIONAL_PARAMETER_M3_S2,
    earth_orbit_radius_m=EARTH_ORBIT_RADIUS_M,
    mars_orbit_radius_m=MARS_ORBIT_RADIUS_M,
)

# Параметры стандартного расчета вертикального взлета.
DEFAULT_EARTH_ASCENT_PARAMETERS: EarthAscentParameters = EarthAscentParameters(
    earth_gravitational_parameter_m3_s2=EARTH_GRAVITATIONAL_PARAMETER_M3_S2,
    earth_radius_m=EARTH_RADIUS_M,
    standard_gravity_m_s2=STANDARD_GRAVITY_M_S2,
    initial_mass_kg=ASCENT_INITIAL_MASS_KG,
    dry_mass_kg=ASCENT_DRY_MASS_KG,
    exhaust_velocity_m_s=ASCENT_EXHAUST_VELOCITY_M_S,
    maximum_thrust_n=ASCENT_MAXIMUM_THRUST_N,
    maximum_load_factor=ASCENT_MAXIMUM_LOAD_FACTOR,
    maximum_time_s=ASCENT_MAXIMUM_TIME_S,
    maximum_step_s=ASCENT_MAXIMUM_STEP_S,
    relative_tolerance=ASCENT_RELATIVE_TOLERANCE,
    position_absolute_tolerance_m=ASCENT_POSITION_ABSOLUTE_TOLERANCE_M,
    velocity_absolute_tolerance_m_s=ASCENT_VELOCITY_ABSOLUTE_TOLERANCE_M_S,
    mass_absolute_tolerance_kg=ASCENT_MASS_ABSOLUTE_TOLERANCE_KG,
)

# Настройки стандартного численного перелета.
DEFAULT_TRANSFER_INTEGRATION_PARAMETERS: TransferIntegrationParameters = (
    TransferIntegrationParameters(
        maximum_time_s=TRANSFER_MAXIMUM_TIME_S,
        maximum_step_s=TRANSFER_MAXIMUM_STEP_S,
        relative_tolerance=TRANSFER_RELATIVE_TOLERANCE,
        position_absolute_tolerance_m=TRANSFER_POSITION_ABSOLUTE_TOLERANCE_M,
        velocity_absolute_tolerance_m_s=TRANSFER_VELOCITY_ABSOLUTE_TOLERANCE_M_S,
    )
)

# Параметры стандартной посадки на Марс.
DEFAULT_MARS_LANDING_PARAMETERS: MarsLandingParameters = MarsLandingParameters(
    mars_gravitational_parameter_m3_s2=MARS_GRAVITATIONAL_PARAMETER_M3_S2,
    mars_radius_m=MARS_RADIUS_M,
    initial_radius_m=MARS_INITIAL_RADIUS_M,
    contact_altitude_tolerance_m=MARS_CONTACT_ALTITUDE_TOLERANCE_M,
    dry_mass_kg=ASCENT_DRY_MASS_KG,
    exhaust_velocity_m_s=ASCENT_EXHAUST_VELOCITY_M_S,
    maximum_thrust_n=MARS_MAXIMUM_THRUST_N,
    maximum_load_factor=MARS_MAXIMUM_LOAD_FACTOR,
    standard_gravity_m_s2=STANDARD_GRAVITY_M_S2,
    maximum_time_s=MARS_MAXIMUM_TIME_S,
    coast_maximum_step_s=MARS_COAST_MAXIMUM_STEP_S,
    burn_maximum_step_s=MARS_BURN_MAXIMUM_STEP_S,
    relative_tolerance=MARS_RELATIVE_TOLERANCE,
    position_absolute_tolerance_m=MARS_POSITION_ABSOLUTE_TOLERANCE_M,
    velocity_absolute_tolerance_m_s=MARS_VELOCITY_ABSOLUTE_TOLERANCE_M_S,
    mass_absolute_tolerance_kg=MARS_MASS_ABSOLUTE_TOLERANCE_KG,
)
