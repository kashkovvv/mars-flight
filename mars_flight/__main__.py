"""Запуск аналитического расчета."""

from .config import (
    DEFAULT_PARAMETERS,
    DEFAULT_EARTH_ASCENT_PARAMETERS,
    METRES_PER_KILOMETRE,
    METRES_PER_MILLION_KILOMETRES,
    KILOGRAMS_PER_TONNE,
    SECONDS_PER_DAY,
)
from .theory import HohmannTransfer
from .earth import EarthAscentModel


def main() -> None:
    transfer = HohmannTransfer.from_parameters(DEFAULT_PARAMETERS)
    ascent_model = EarthAscentModel(DEFAULT_EARTH_ASCENT_PARAMETERS)
    ascent = ascent_model.simulate(transfer.departure_excess_speed_m_s)

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

    print("Аналитический перелет Земля — Марс")
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
    print(f"  Время перелета: {time_of_flight_days:.3f} суток")

    final_altitude_km = ascent.final_altitude_m / METRES_PER_KILOMETRE
    final_radial_velocity_km_s = ascent.final_radial_velocity_m_s / METRES_PER_KILOMETRE
    final_mass_tonnes = ascent.final_mass_kg / KILOGRAMS_PER_TONNE

    print()
    print("Вертикальный взлёт с Земли")
    print(f"  Продолжительность: {ascent.duration_s:.3f} с")
    print(f"  Высота выключения двигателя: {final_altitude_km:.3f} км")
    print(
        f"  Радиальная скорость при выключении: {final_radial_velocity_km_s:.3f} км/с"
    )
    print(f"  Конечная масса: {final_mass_tonnes:.3f} т")
    print(f"  Максимальная перегрузка: {ascent.maximum_load_factor:.3f} g")


if __name__ == "__main__":
    main()
