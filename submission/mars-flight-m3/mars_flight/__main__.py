"""Запуск расчетов для реализованных этапов полета."""

from dataclasses import asdict
from datetime import datetime
import json
from pathlib import Path

from matplotlib import pyplot as plt

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
from .mission import MissionModel
from .plots import create_mission_figures


def main() -> None:
    model = MissionModel(
        mission_parameters=DEFAULT_PARAMETERS,
        earth_ascent_parameters=DEFAULT_EARTH_ASCENT_PARAMETERS,
        transfer_integration_parameters=DEFAULT_TRANSFER_INTEGRATION_PARAMETERS,
        mars_landing_parameters=DEFAULT_MARS_LANDING_PARAMETERS,
        mars_orbit_match_tolerance_m=MARS_ORBIT_MATCH_TOLERANCE_M,
    )
    result = model.simulate()
    benchmark = result.benchmark
    ascent = result.ascent
    numerical_transfer = result.transfer
    landing = result.landing
    arrival_relative_speed_m_s = result.arrival_relative_speed_m_s

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
        "  Избыточная скорость ухода: "
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

    figures = create_mission_figures(
        ascent, numerical_transfer, landing, model.mission_parameters
    )
    try:
        generated_at = datetime.now().astimezone()
        run_directory = Path("results") / generated_at.strftime(
            "%Y-%m-%d_%H-%M-%S_%f"
        )
        run_directory.mkdir(parents=True)

        for name, figure in figures.items():
            figure.savefig(run_directory / f"{name}.png", dpi=180)

        parameters = {
            "generated_at": generated_at.isoformat(timespec="microseconds"),
            "mission": asdict(model.mission_parameters),
            "earth_ascent": asdict(model.earth_ascent_parameters),
            "solar_transfer": asdict(model.transfer_integration_parameters),
            "mars_landing": asdict(model.mars_landing_parameters),
            "mars_orbit_match_tolerance_m": model.mars_orbit_match_tolerance_m,
        }
        with (run_directory / "parameters.json").open(
            "w", encoding="utf-8"
        ) as stream:
            json.dump(parameters, stream, ensure_ascii=False, indent=2)
            stream.write("\n")

        print(f"\nГрафики и параметры сохранены в {run_directory}")
        if plt.get_backend().lower() != "agg":
            plt.show()
    finally:
        for figure in figures.values():
            plt.close(figure)


if __name__ == "__main__":
    main()
