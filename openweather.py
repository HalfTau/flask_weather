# openweather.py
import requests

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
    resp.raise_for_status()
    return resp.json()

def fetch_onecall(lat, lon, api_key, units="imperial"):
    url = build_weather_url(lat, lon, api_key, units=units)
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    return resp.json()
