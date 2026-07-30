"""
Weather Information Service for Project KISAN.
Provides weather reports and 5-day forecast with Pune fallback logic.
"""

from datetime import datetime, timedelta


class WeatherService:
    """Weather Provider Service."""

    @staticmethod
    def get_weather(location_name: str = "Pune", location_permission_enabled: bool = True) -> dict:
        """
        Fetch weather details for specified or default location.
        Defaults to Pune if location permission is off or detection fails.
        """
        active_location = location_name if (location_permission_enabled and location_name) else "Pune"

        # Mock weather payload
        today = datetime.now()
        forecast = []
        for i in range(1, 6):
            day_date = today + timedelta(days=i)
            forecast.append({
                "day": day_date.strftime("%a"),
                "date": day_date.strftime("%d %b"),
                "temp": f"{random_range(28, 33, i)}°C / {random_range(18, 22, i)}°C",
                "condition": "Partly Cloudy" if i % 2 == 0 else "Sunny",
                "icon": "fa5s.cloud-sun" if i % 2 == 0 else "fa5s.sun",
                "rain_chance": f"{10 + i * 5}%"
            })

        return {
            "location": active_location,
            "temperature": "29°C",
            "condition": "Partly Cloudy",
            "icon": "fa5s.cloud-sun",
            "humidity": "62%",
            "wind": "14 km/h SW",
            "rain_chance": "15%",
            "uv_index": "6 (Moderate)",
            "updated_at": datetime.now().strftime("%I:%M %p"),
            "forecast": forecast
        }


def random_range(base, spread, seed):
    return base + ((seed * 3) % spread)
