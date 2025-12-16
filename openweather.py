# openweather.py
import requests
from datetime import datetime
from zoneinfo import ZoneInfo


def build_weather_url(lat, lon, api_key, units="imperial"):
    return (
        f"https://api.openweathermap.org/data/3.0/onecall"
        f"?lat={lat}&lon={lon}&appid={api_key}&units={units}"
    )

def build_geo_url(city, api_key):
    return f"https://api.openweathermap.org/geo/1.0/direct?q={city}&limit=5&appid={api_key}"

def fetch_geo(city, api_key):
    url = build_geo_url(city, api_key)
    resp = requests.get(url, timeout=10)

def build_daily_forecasts_with_hours(weather_data, timezone_str="America/Los_Angeles"):
    tz = ZoneInfo(timezone_str)

    # Localize hourly timestamps
    for hour in weather_data["hourly"]:
        hour["local_dt"] = datetime.utcfromtimestamp(hour["dt"]).replace(
            tzinfo=ZoneInfo("UTC")
        ).astimezone(tz)
        hour["local_date"] = hour["local_dt"].date()

    # Build daily forecasts and attach matching hours
    daily_forecasts = []
    for day in weather_data["daily"]:
        local_dt = datetime.utcfromtimestamp(day["dt"]).replace(
            tzinfo=ZoneInfo("UTC")
        ).astimezone(tz)
        local_date = local_dt.date()

        hours_for_day = []
        for h in weather_data["hourly"]:
            if h["local_date"] == local_date:
                hours_for_day.append({
                    "time": h["local_dt"].strftime("%a %I %p"),
                    "temp": round(h["temp"]),
                    "icon": h["weather"][0]["icon"]
                })

        daily_forecasts.append({
            "date": local_dt.strftime("%A, %b %d"),
            "temp_day": round(day["temp"]["day"]),
            "temp_night": round(day["temp"]["night"]),
            "description": day["weather"][0]["description"],
            "icon": day["weather"][0]["icon"],
            "hours": hours_for_day
        })

    return daily_forecasts

def fetch_onecall(lat, lon, api_key, units="imperial"):
    url = build_weather_url(lat, lon, api_key, units=units)
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    return resp.json()
