"""Запуск аналитического расчета."""

from .config import (
    DEFAULT_PARAMETERS,
    METRES_PER_KILOMETRE,
    METRES_PER_MILLION_KILOMETRES,
    SECONDS_PER_DAY,
)
from .theory import HohmannTransfer


def main() -> None:
    transfer = HohmannTransfer.from_parameters(DEFAULT_PARAMETERS)

    semi_major_axis_million_km = (
        transfer.semi_major_axis_m / METRES_PER_MILLION_KILOMETRES
    )
    earth_orbital_speed_km_s = transfer.earth_orbital_speed_m_s / METRES_PER_KILOMETRE
    mars_orbital_speed_km_s = transfer.mars_orbital_speed_m_s / METRES_PER_KILOMETRE
    departure_heliocentric_speed_km_s = (
        transfer.departure_heliocentric_speed_m_s / METRES_PER_KILOMETRE
    )
    arrival_heliocentric_speed_km_s = (
        transfer.arrival_heliocentric_speed_m_s / METRES_PER_KILOMETRE
    )
    departure_excess_speed_km_s = (
        transfer.departure_excess_speed_m_s / METRES_PER_KILOMETRE
    )
    arrival_relative_velocity_km_s = (
        transfer.arrival_relative_velocity_m_s / METRES_PER_KILOMETRE
    )
    arrival_relative_speed_km_s = (
        transfer.arrival_relative_speed_m_s / METRES_PER_KILOMETRE
    )
    time_of_flight_days = transfer.time_of_flight_s / SECONDS_PER_DAY

    print("Аналитический перелёт Земля — Марс")
    print(f"  Большая полуось перехода: {semi_major_axis_million_km:.3f} млн км")
    print(f"  Орбитальная скорость Земли: {earth_orbital_speed_km_s:.3f} км/с")
    print(
        "  Гелиоцентрическая скорость при старте: "
        f"{departure_heliocentric_speed_km_s:.3f} км/с"
    )
    print(f"  Избыточная скорость ухода v_inf: {departure_excess_speed_km_s:+.3f} км/с")
    print(f"  Орбитальная скорость Марса: {mars_orbital_speed_km_s:.3f} км/с")
    print(
        "  Гелиоцентрическая скорость при прибытии: "
        f"{arrival_heliocentric_speed_km_s:.3f} км/с"
    )
    print(
        "  Проекция скорости относительно Марса: "
        f"{arrival_relative_velocity_km_s:+.3f} км/с"
    )
    print(
        f"  Модуль скорости относительно Марса: {arrival_relative_speed_km_s:.3f} км/с"
    )
    print(f"  Время перелёта: {time_of_flight_days:.3f} суток")


if __name__ == "__main__":
    main()
