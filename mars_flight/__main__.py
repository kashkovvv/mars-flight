"""Запуск расчетов для реализованных этапов полета."""

from math import hypot, sqrt

from .config import (
    DEFAULT_EARTH_ASCENT_PARAMETERS,
    DEFAULT_MARS_LANDING_PARAMETERS,
    DEFAULT_PARAMETERS,
    DEFAULT_TRANSFER_INTEGRATION_PARAMETERS,
    KILOGRAMS_PER_TONNE,
    MARS_ORBIT_MATCH_TOLERANCE_M,
    METRES_PER_KILOMETRE,
    METRES_PER_MILLION_KILOMETRES,
    SECONDS_PER_DAY,
)
from .earth import EarthAscentModel
from .mars import MarsLandingModel
from .theory import HohmannTransfer
from .transfer import SolarTransferModel


def main() -> None:
    benchmark = HohmannTransfer.from_parameters(DEFAULT_PARAMETERS)
    ascent = EarthAscentModel(DEFAULT_EARTH_ASCENT_PARAMETERS).simulate(
        benchmark.departure_excess_speed_m_s
    )

    final_earth_specific_energy_m2_s2 = float(ascent.specific_energy_m2_s2[-1])
    if final_earth_specific_energy_m2_s2 <= 0.0:
        raise RuntimeError("Взлет не обеспечил положительную энергию ухода")
    actual_excess_speed_m_s = sqrt(2.0 * final_earth_specific_energy_m2_s2)

    numerical_transfer = SolarTransferModel(
        DEFAULT_PARAMETERS, DEFAULT_TRANSFER_INTEGRATION_PARAMETERS
    ).simulate(actual_excess_speed_m_s)

    if (
        abs(numerical_transfer.mars_orbit_radius_error_m)
        > MARS_ORBIT_MATCH_TOLERANCE_M
    ):
        raise RuntimeError("Корабль не достиг радиуса орбиты Марса")

    mars_orbital_speed_m_s = sqrt(
        DEFAULT_PARAMETERS.sun_gravitational_parameter_m3_s2
        / DEFAULT_PARAMETERS.mars_orbit_radius_m
    )
    arrival_relative_speed_m_s = hypot(
        numerical_transfer.final_radial_velocity_m_s,
        numerical_transfer.final_tangential_velocity_m_s - mars_orbital_speed_m_s,
    )
    landing = MarsLandingModel(DEFAULT_MARS_LANDING_PARAMETERS).simulate(
        arrival_relative_speed_m_s, ascent.final_mass_kg
    )

    print("Аналитический перелет Земля — Марс")
    print(
        "  Большая полуось перехода: "
        f"{benchmark.semi_major_axis_m / METRES_PER_MILLION_KILOMETRES:.3f} млн км"
    )
    print(
        "  Орбитальная скорость Земли: "
        f"{benchmark.earth_orbital_speed_m_s / METRES_PER_KILOMETRE:.3f} км/с"
    )
    print(
        "  Гелиоцентрическая скорость при старте: "
        f"{benchmark.departure_heliocentric_speed_m_s / METRES_PER_KILOMETRE:.3f} км/с"
    )
    print(
        "  Избыточная скорость ухода v_inf: "
        f"{benchmark.departure_excess_speed_m_s / METRES_PER_KILOMETRE:.3f} км/с"
    )
    print(
        "  Орбитальная скорость Марса: "
        f"{benchmark.mars_orbital_speed_m_s / METRES_PER_KILOMETRE:.3f} км/с"
    )
    print(
        "  Гелиоцентрическая скорость при прибытии: "
        f"{benchmark.arrival_heliocentric_speed_m_s / METRES_PER_KILOMETRE:.3f} км/с"
    )
    print(
        "  Проекция скорости относительно Марса: "
        f"{benchmark.arrival_relative_velocity_m_s / METRES_PER_KILOMETRE:+.3f} км/с"
    )
    print(
        "  Модуль скорости относительно Марса: "
        f"{benchmark.arrival_relative_speed_m_s / METRES_PER_KILOMETRE:.3f} км/с"
    )
    print(f"  Время перелета: {benchmark.time_of_flight_s / SECONDS_PER_DAY:.3f} суток")

    print()
    print("Вертикальный взлет с Земли")
    print(f"  Продолжительность: {ascent.duration_s:.3f} с")
    print(
        "  Высота выключения двигателя: "
        f"{ascent.final_altitude_m / METRES_PER_KILOMETRE:.3f} км"
    )
    print(
        "  Радиальная скорость при выключении: "
        f"{ascent.final_radial_velocity_m_s / METRES_PER_KILOMETRE:.3f} км/с"
    )
    print(f"  Конечная масса: {ascent.final_mass_kg / KILOGRAMS_PER_TONNE:.3f} т")
    print(f"  Максимальная перегрузка: {ascent.maximum_load_factor:.3f} g")

    print()
    print("Численный перелет в поле Солнца")
    print(
        "  Продолжительность: "
        f"{numerical_transfer.duration_s / SECONDS_PER_DAY:.3f} суток"
    )
    print(
        "  Радиус в противоположной точке: "
        f"{numerical_transfer.final_radius_m / METRES_PER_MILLION_KILOMETRES:.3f}"
        " млн км"
    )
    print(
        "  Гелиоцентрическая скорость: "
        f"{numerical_transfer.final_heliocentric_speed_m_s / METRES_PER_KILOMETRE:.3f}"
        " км/с"
    )
    print(
        "  Разность радиусов в противоположной точке: "
        f"{numerical_transfer.mars_orbit_radius_error_m:+.3f} м"
    )

    print()
    print("Радиальная посадка на Марс")
    print(
        "  Скорость подлета относительно Марса: "
        f"{arrival_relative_speed_m_s / METRES_PER_KILOMETRE:.3f} км/с"
    )
    print(
        "  Начальная высота: "
        f"{landing.altitude_m[0] / METRES_PER_KILOMETRE:.3f} км"
    )
    print(
        "  Высота включения двигателя: "
        f"{landing.ignition_altitude_m / METRES_PER_KILOMETRE:.3f} км"
    )
    print(
        "  Продолжительность снижения: "
        f"{landing.duration_s / SECONDS_PER_DAY:.3f} суток"
    )
    print(f"  Время работы двигателя: {landing.burn_duration_s:.3f} с")
    print(f"  Скорость контакта: {abs(landing.final_radial_velocity_m_s):.6f} м/с")
    print(f"  Конечная масса: {landing.final_mass_kg / KILOGRAMS_PER_TONNE:.3f} т")
    print(f"  Максимальная перегрузка: {landing.maximum_load_factor:.3f} g")


if __name__ == "__main__":
    main()
