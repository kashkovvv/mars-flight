"""Физические параметры модели."""

from dataclasses import dataclass
from math import isfinite


# Количество секунд в сутках, с/сут.
SECONDS_PER_DAY: float = 86_400.0

# Количество метров в километре, м/км.
METRES_PER_KILOMETRE: float = 1_000.0

# Количество метров в миллионе километров, м/(млн км).
METRES_PER_MILLION_KILOMETRES: float = 1_000_000_000.0

# Астрономическая единица, м.
ASTRONOMICAL_UNIT_M: float = 149_597_870_700.0

# Гравитационный параметр Солнца, м^3/с^2.
SUN_GRAVITATIONAL_PARAMETER_M3_S2: float = 1.327_124_400_18e20

# Радиус круговой орбиты Земли, м.
EARTH_ORBIT_RADIUS_M: float = ASTRONOMICAL_UNIT_M

# Радиус круговой орбиты Марса, м.
MARS_ORBIT_RADIUS_M: float = 1.523_679 * ASTRONOMICAL_UNIT_M


@dataclass(frozen=True)
class MissionParameters:
    """Параметры аналитической модели в единицах СИ."""

    sun_gravitational_parameter_m3_s2: float
    earth_orbit_radius_m: float
    mars_orbit_radius_m: float

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        values = {
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


DEFAULT_PARAMETERS: MissionParameters = MissionParameters(
    sun_gravitational_parameter_m3_s2=SUN_GRAVITATIONAL_PARAMETER_M3_S2,
    earth_orbit_radius_m=EARTH_ORBIT_RADIUS_M,
    mars_orbit_radius_m=MARS_ORBIT_RADIUS_M,
)
