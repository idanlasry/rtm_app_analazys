import requests
from itertools import zip_longest


def get_3_day_weather_forecast(city: str = None) -> dict | None:
    """
    Retrieves a 3-day weather forecast for a specified city.

    Args:
        city: City name to search for. If None, prompts user for input.

    Returns:
        dict: Contains city info and forecast data, or None if error occurs
    """
    if city is None:
        city = input("Which city are you looking for? ").strip()

    if not city:
        print("City is required.")
        return None

    # --- 1) Geocode city -> lat/lon ---
    geo_url = "https://geocoding-api.open-meteo.com/v1/search"
    geo_params = {"name": city, "count": 1, "language": "en", "format": "json"}

    try:
        geo_resp = requests.get(geo_url, params=geo_params, timeout=10)
        geo_resp.raise_for_status()
        geo_data = geo_resp.json()
    except requests.RequestException as exc:
        print(f"Failed to reach geocoding service: {exc}")
        return None

    results = geo_data.get("results") or []
    if not results:
        print(f"No results found for '{city}'.")
        return None

    location = results[0]
    lat = location.get("latitude")
    lon = location.get("longitude")
    city_name = location.get("name", city)
    country = location.get("country", "")

    if lat is None or lon is None:
        print("Location coordinates not found.")
        return None

    # --- 2) Forecast ---
    forecast_url = "https://api.open-meteo.com/v1/forecast"
    forecast_params = {
        "latitude": lat,
        "longitude": lon,
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
        "forecast_days": 3,
        "timezone": "auto",
        "temperature_unit": "celsius",
    }

    try:
        forecast_resp = requests.get(forecast_url, params=forecast_params, timeout=10)
        forecast_resp.raise_for_status()
        daily = forecast_resp.json().get("daily") or {}
    except requests.RequestException as exc:
        print(f"Failed to reach weather service: {exc}")
        return None

    dates = daily.get("time") or []
    t_max = daily.get("temperature_2m_max") or []
    t_min = daily.get("temperature_2m_min") or []
    precip = daily.get("precipitation_sum") or []

    if not dates:
        print("No forecast data available.")
        return None

    # Build forecast rows using zip_longest
    forecast_rows = []
    for date, temp_max, temp_min, precipitation in zip_longest(
        dates[:3], t_max[:3], t_min[:3], precip[:3]
    ):
        row = {
            "date": date,
            "temp_max_c": temp_max,
            "temp_min_c": temp_min,
            "precip_mm": precipitation,
        }
        forecast_rows.append(row)

    # Print formatted output
    print(f"\n📍 3-Day Forecast for {city_name}, {country}:\n")
    for row in forecast_rows:
        print(
            f"  {row['date']}: {row['temp_max_c']}°C / {row['temp_min_c']}°C, "
            f"💧 {row['precip_mm']}mm"
        )

    return {
        "city": city_name,
        "country": country,
        "latitude": lat,
        "longitude": lon,
        "forecast": forecast_rows,
    }


def main():
    """Main entry point for the weather forecast application."""
    get_3_day_weather_forecast()


if __name__ == "__main__":
    main()
