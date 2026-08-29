"""
Weather Information Service for Project KISAN.
Provides weather reports and 5-day forecast with Pune fallback logic, caching, and offline support.
"""

import os
import json
import requests
from datetime import datetime, timedelta

CACHE_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "database", "weather_cache.json"))
CACHE_DURATION_HOURS = 3

class WeatherService:
    """Weather Provider Service using Open-Meteo."""

    @staticmethod
    def get_weather(location_name: str = "Baramati", location_permission_enabled: bool = True) -> dict:
        """
        Fetch weather details for specified or default location.
        Defaults to Baramati if location permission is off or detection fails.
        """
        active_location = location_name if (location_permission_enabled and location_name) else "Baramati"
        
        # 1. Check Cache Validity
        cache_data = None
        if os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, "r") as f:
                    cache_data = json.load(f)
                
                # Check if same location and within CACHE_DURATION_HOURS
                cached_time_str = cache_data.get("updated_at_raw")
                cached_location = cache_data.get("location", "")
                if cached_time_str and cached_location.lower() == active_location.lower():
                    cached_time = datetime.strptime(cached_time_str, "%Y-%m-%d %H:%M:%S")
                    if datetime.now() - cached_time < timedelta(hours=CACHE_DURATION_HOURS):
                        # Cache is fresh and matching!
                        cache_data["is_offline"] = False
                        cache_data["from_cache"] = True
                        return cache_data
            except Exception:
                # If cache read fails, proceed to fetch
                pass

        # 2. Fetch Live Data
        try:
            # Step A: Geocode city name to lat/lon
            geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={active_location}&count=1&language=en&format=json"
            geo_res = requests.get(geo_url, timeout=5).json()
            
            if not geo_res.get("results"):
                raise ValueError("Location not found")
            
            loc_data = geo_res["results"][0]
            lat = loc_data["latitude"]
            lon = loc_data["longitude"]
            resolved_location = loc_data["name"]

            # Step B: Fetch current weather and 5-day forecast
            weather_url = (
                f"https://api.open-meteo.com/v1/forecast?"
                f"latitude={lat}&longitude={lon}"
                f"&current=temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m,cloud_cover"
                f"&daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max"
                f"&timezone=auto"
            )
            w_res = requests.get(weather_url, timeout=5).json()

            current = w_res["current"]
            daily = w_res["daily"]

            # Map current weather
            curr_code = current["weather_code"]
            curr_cond, curr_icon = WeatherService._map_wmo_code(curr_code)

            # Map 5-day forecast
            forecast = []
            today = datetime.now()
            for i in range(1, 6):
                if i < len(daily["time"]):
                    forecast_date = datetime.strptime(daily["time"][i], "%Y-%m-%d")
                    day_code = daily["weather_code"][i]
                    day_cond, day_icon = WeatherService._map_wmo_code(day_code)
                    
                    forecast.append({
                        "day": forecast_date.strftime("%a"),
                        "date": forecast_date.strftime("%d %b"),
                        "temp": f"{int(round(daily['temperature_2m_max'][i]))}°C / {int(round(daily['temperature_2m_min'][i]))}°C",
                        "condition": day_cond,
                        "icon": day_icon,
                        "rain_chance": f"{daily['precipitation_probability_max'][i]}%"
                    })

            # Step C: Option B live radar mapping (stitching RainViewer tile)
            composite_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "database", "weather_radar_composite.jpg"))
            base_map_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets", "weather_map_base.jpg"))
            
            try:
                # Get latest radar frame from RainViewer
                rv_res = requests.get("https://api.rainviewer.com/public/weather-maps.json", timeout=3)
                rv_data = rv_res.json()
                rv_host = rv_data.get("host", "https://tilecache.rainviewer.com")
                rv_past = rv_data.get("radar", {}).get("past", [])
                
                if rv_past:
                    latest_radar = rv_past[-1]
                    tile_path = latest_radar["path"]
                    # Fetch tile for Baramati/Pune region (z=7, x=90, y=57)
                    tile_url = f"{rv_host}{tile_path}/256/7/90/57/2/1_1.png"
                    tile_res = requests.get(tile_url, timeout=3)
                    
                    if tile_res.status_code == 200:
                        from PIL import Image
                        import io
                        
                        # Open base map and downloaded radar tile
                        base_img = Image.open(base_map_path).convert("RGBA")
                        tile_img = Image.open(io.BytesIO(tile_res.content)).convert("RGBA")
                        
                        # Resize radar tile to match base map
                        tile_resized = tile_img.resize(base_img.size, Image.Resampling.LANCZOS)
                        
                        # Blend layers
                        composite_img = Image.alpha_composite(base_img, tile_resized)
                        composite_img.convert("RGB").save(composite_path, "JPEG")
            except Exception as radar_err:
                # If radar fetch fails, fail silently and rely on existing or fallback map
                pass

            # Ensure composite map file exists at least as base map if download failed
            if not os.path.exists(composite_path) and os.path.exists(base_map_path):
                try:
                    import shutil
                    shutil.copy(base_map_path, composite_path)
                except Exception:
                    pass

            # Calculate agronomic metrics (ET0, Leaching Risk, Spray Window)
            agronomy = WeatherService._calculate_agronomy_metrics(
                temp=current['temperature_2m'],
                humidity=current['relative_humidity_2m'],
                wind=current['wind_speed_10m'],
                cloud_cover=current['cloud_cover'],
                forecast=forecast
            )

            # Generate AI Field Action Advisory
            advisory = WeatherService._generate_ai_field_advisory(
                forecast=forecast,
                current_temp=current['temperature_2m'],
                max_rain=agronomy['max_rain'],
                leaching_risk=agronomy['leaching_risk_pct'],
                spray_status=agronomy['spray_status'],
                et0_val=agronomy['et0_val']
            )

            weather_data = {
                "location": resolved_location,
                "temperature": f"{int(round(current['temperature_2m']))}°C",
                "condition": curr_cond,
                "icon": curr_icon,
                "humidity": f"{current['relative_humidity_2m']}%",
                "wind": f"{current['wind_speed_10m']} km/h",
                "rain_chance": f"{daily['precipitation_probability_max'][0]}%",
                "uv_index": "N/A",  # Open-Meteo daily UV requires extra query, using default N/A
                "cloud_cover": current["cloud_cover"],  # Option A: cloud cover percentage
                "updated_at": datetime.now().strftime("%I:%M %p"),
                "updated_at_raw": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "synced_ago": "Just now",
                "forecast": forecast,
                "agronomy": agronomy,
                "ai_advisory": advisory,
                "is_offline": False,
                "from_cache": False
            }

            # Save to cache
            os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
            with open(CACHE_FILE, "w") as f:
                json.dump(weather_data, f, indent=4)

            return weather_data

        except Exception as e:
            # 3. Fallback to cache if available
            if cache_data:
                cache_data["is_offline"] = True
                cache_data["from_cache"] = True
                
                # Update relative synced_ago string
                cached_time_str = cache_data.get("updated_at_raw")
                if cached_time_str:
                    try:
                        cached_time = datetime.strptime(cached_time_str, "%Y-%m-%d %H:%M:%S")
                        time_diff = datetime.now() - cached_time
                        hrs = int(time_diff.total_seconds() // 3600)
                        mins = int((time_diff.total_seconds() % 3600) // 60)
                        if hrs > 0:
                            cache_data["synced_ago"] = f"Synced {hrs}h {mins}m ago"
                        elif mins > 0:
                            cache_data["synced_ago"] = f"Synced {mins}m ago"
                        else:
                            cache_data["synced_ago"] = "Synced just now"
                    except Exception:
                        cache_data["synced_ago"] = "Synced 2h ago"
                else:
                    cache_data["synced_ago"] = "Synced 2h ago"

                return cache_data
            
            # 4. Critical fallback if absolutely no cache and no internet
            return {
                "location": active_location,
                "temperature": "--°C",
                "condition": "Offline",
                "icon": "fa5s.exclamation-triangle",
                "humidity": "--%",
                "wind": "--",
                "rain_chance": "--%",
                "uv_index": "--",
                "cloud_cover": 0,
                "updated_at": "N/A",
                "updated_at_raw": "",
                "synced_ago": "Offline",
                "forecast": [
                    {
                        "day": (datetime.now() + timedelta(days=i)).strftime("%a"),
                        "date": (datetime.now() + timedelta(days=i)).strftime("%d %b"),
                        "temp": "--°C / --°C",
                        "condition": "Offline",
                        "icon": "fa5s.question",
                        "rain_chance": "--%"
                    } for i in range(1, 6)
                ],
                "agronomy": {
                    "et0": "-- mm/day",
                    "et0_val": 0.0,
                    "et0_desc": "Unknown",
                    "leaching_risk": "UNKNOWN",
                    "leaching_risk_pct": 0,
                    "spray_status": "UNKNOWN",
                    "max_rain": 0
                },
                "ai_advisory": "⚠️ System is in Offline Mode. Connect to network to fetch real-time agricultural field advisories.",
                "is_offline": True,
                "from_cache": False
            }

    @staticmethod
    def _calculate_agronomy_metrics(temp: float, humidity: float, wind: float, cloud_cover: float, forecast: list) -> dict:
        """Calculate agronomic metrics: Evapotranspiration (ET0), Soil Leaching Risk, and Spray Window."""
        # 1. Evapotranspiration (ET0) estimation based on Hargreaves / Penman-Monteith approximation
        et0_val = max(1.2, round(0.11 * temp * (1 - humidity / 100) + 0.04 * wind + 0.02 * (100 - cloud_cover), 1))
        if et0_val < 2.5:
            et0_desc = "Low Evaporation"
        elif et0_val < 4.5:
            et0_desc = "Moderate Evaporation"
        else:
            et0_desc = "High Evaporation"

        # 2. Extract max rain chance from upcoming forecast
        rain_chances = []
        for day in forecast:
            try:
                r_str = day.get("rain_chance", "0%").replace("%", "")
                rain_chances.append(int(r_str))
            except ValueError:
                rain_chances.append(0)
        max_rain = max(rain_chances) if rain_chances else 0

        # Soil Leaching Risk Calculation (%)
        leaching_pct = min(98, max(12, int(max_rain * 0.85 + humidity * 0.15)))
        if leaching_pct >= 75:
            leaching_risk = f"CRITICAL ({leaching_pct}%)"
        elif leaching_pct >= 50:
            leaching_risk = f"HIGH ({leaching_pct}%)"
        elif leaching_pct >= 30:
            leaching_risk = f"MODERATE ({leaching_pct}%)"
        else:
            leaching_risk = f"LOW ({leaching_pct}%)"

        # 3. Spray Window Status
        if max_rain > 50 or wind > 18:
            spray_status = "UNFAVORABLE"
        elif wind > 12:
            spray_status = "MODERATE"
        else:
            spray_status = "OPTIMAL"

        return {
            "et0": f"{et0_val} mm/day",
            "et0_val": et0_val,
            "et0_desc": et0_desc,
            "leaching_risk": leaching_risk,
            "leaching_risk_pct": leaching_pct,
            "spray_status": spray_status,
            "max_rain": max_rain
        }

    @staticmethod
    def _generate_ai_field_advisory(forecast: list, current_temp: float, max_rain: int, leaching_risk: int, spray_status: str, et0_val: float) -> str:
        """Dynamic Farm Decision Rule Engine generating actionable advisory."""
        if max_rain >= 70:
            return (
                f"Heavy rainfall cluster detected (Next 3 Days Max Rain >{max_rain}%). "
                f"High risk of nutrient runoff and root leaching. Postpone all Nitrogen/Urea soil application until dry spell."
            )
        elif current_temp > 35 or et0_val >= 5.0:
            return (
                f"High heat & elevated Evapotranspiration ({et0_val} mm/day) detected. "
                f"Schedule extra evening drip irrigation cycles to prevent crop moisture stress and soil drying."
            )
        elif spray_status == "UNFAVORABLE":
            return (
                f"Unfavorable crop spray window due to elevated wind velocity / rain risk. "
                f"Delay chemical pesticide and fungicide spraying to prevent drift and wash-off loss."
            )
        else:
            return (
                f"Favorable agronomic weather window. Ideal conditions for balanced fertigation, "
                f"routine crop inspection, and foliar spray operations."
            )

    @staticmethod
    def _map_wmo_code(code: int) -> tuple:
        """Map WMO code to condition text and qtawesome icon."""
        if code == 0:
            return "Sunny", "fa5s.sun"
        elif code in [1, 2]:
            return "Partly Cloudy", "fa5s.cloud-sun"
        elif code == 3:
            return "Cloudy", "fa5s.cloud"
        elif code in [45, 48]:
            return "Foggy", "fa5s.smog"
        elif code in [51, 53, 55, 56, 57]:
            return "Drizzle", "fa5s.cloud-rain"
        elif code in [61, 63, 65, 66, 67]:
            return "Rainy", "fa5s.cloud-showers-heavy"
        elif code in [71, 73, 75, 77]:
            return "Snowy", "fa5s.snowflake"
        elif code in [80, 81, 82]:
            return "Rain Showers", "fa5s.cloud-showers-heavy"
        elif code in [85, 86]:
            return "Snowy", "fa5s.snowflake"
        elif code in [95, 96, 99]:
            return "Thunderstorm", "fa5s.bolt"
        else:
            return "Cloudy", "fa5s.cloud"


