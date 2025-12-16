from flask import Flask, render_template, request, session, redirect
import requests
import os
from datetime import datetime
from dotenv import load_dotenv
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from zoneinfo import ZoneInfo
from datetime import datetime
import math


def latlon_to_tile(lat: float, lon: float, z: int = 6) -> tuple[int, int, int]:
    """Web Mercator tile indices for a given lat/lon/zoom."""
    lat_rad = math.radians(lat)
    n = 2 ** z
    x = int((lon + 180.0) / 360.0 * n)
    y = int((1.0 - math.log(math.tan(lat_rad) + 1 / math.cos(lat_rad)) / math.pi) / 2.0 * n)
    return z, x, y


load_dotenv()
openweather_api_key =  os.getenv("OPEN_WEATHER_API")

app = Flask(__name__)
app.secret_key = '2203489023923'

#app_id = '08588f09c1a372a6800949cc83c889a2'

def build_weather_url(lat,lon): 
    return f"https://api.openweathermap.org/data/3.0/onecall?lat={lat}&lon={lon}&appid={openweather_api_key}&units=imperial"

def build_geo_url(city): 
    return f"https://api.openweathermap.org/geo/1.0/direct?q={city}&limit=5&appid={openweather_api_key}"

def day_or_night():
    current_hour = datetime.now().hour
    if 6 <= current_hour < 18:  # Assuming 6 AM to 6 PM as day
        return "d"
    else:
        return "n"

@app.route('/')
def hello_world():
    content = day_or_night()
    return render_template('index.html', content=content)

@app.route('/', methods=['POST'])
def my_form_post():
    content = day_or_night()
    city_query = request.form['text']
    geo_url = build_geo_url(city_query)
    geo_request = requests.get(geo_url)
    geo_data = geo_request.json()
    session['geo_data'] = geo_data
    return render_template('index.html', geo_data=geo_data, content=content)

def generate_current(geo_data, current_weather, city_name):
    weather_info = {
        "name": city_name,  
        "city": city_name,
        "state": geo_data[0].get('state', 'Unknown'),
        "country": geo_data[0].get('country', 'Unknown'),
        "temperature_f": round(current_weather.get('temp', 0)),
        "feels_like_f": round(current_weather.get('feels_like', 0)),
        "humidity": current_weather.get('humidity', 0),
        "description": current_weather.get('weather', [{}])[0].get("description", "No description"),
        "icon": current_weather.get('weather', [{}])[0].get("icon", "No icon")
    }
    return weather_info

def generate_daily(daily_forecasts_raw):
    daily_forecasts = []
    for day in daily_forecasts_raw:
        forecast_date = datetime.utcfromtimestamp(day.get('dt')).strftime('%A, %b %d')
        daily_forecasts.append({
            'dt': day.get('dt'),
            'date': forecast_date,
            'temp_day': round(day.get('temp', {}).get('day', 0)),
            'temp_night': round(day.get('temp', {}).get('night', 0)),
            'description': day.get('weather', [{}])[0].get('description', 'No description'),
            'icon': day.get('weather', [{}])[0].get('icon', '01d')
        }) 
    return daily_forecasts

# for every hour that is returned from the API call, append pertinient information to list
def generate_hourly(weather_data) :
    hourly_forecasts = []
    for hour in weather_data['hourly']:
        daily_forecast_date = datetime.utcfromtimestamp(hour.get('dt')).strftime('%a %I %p')

        hourly_forecasts.append({
            'dt': hour.get('dt'),
            'date': daily_forecast_date,
            'temp': round(hour.get('temp', {})),
            'icon': hour.get('weather', [{}])[0].get('icon', '01d')
        })
    return hourly_forecasts

@app.route('/result', methods=['POST'])
def show_selected():
    selected_index = request.form.get('selected_location')
    geo_data = session.get('geo_data', [])

    if not (selected_index and geo_data):
        return "No selection or geo data available"

    try:
        index = int(selected_index)
        selected_location = geo_data[index]
        lat, lon = selected_location["lat"], selected_location["lon"]
        city_name = selected_location.get("name", "Unknown")

        weather_url = build_weather_url(lat, lon)
        response = requests.get(weather_url)
        weather_data = response.json()

        pacific = ZoneInfo("America/Los_Angeles")

        # Localize hourly timestamps
        for hour in weather_data["hourly"]:
            hour["local_dt"] = datetime.utcfromtimestamp(hour["dt"]).replace(
                tzinfo=ZoneInfo("UTC")
            ).astimezone(pacific)
            hour["local_date"] = hour["local_dt"].date()

        # Build daily forecasts and attach matching hours
        daily_forecasts = []
        for day in weather_data["daily"]:
            local_dt = datetime.utcfromtimestamp(day["dt"]).replace(
                tzinfo=ZoneInfo("UTC")
            ).astimezone(pacific)
            local_date = local_dt.date()

            hours_for_day = []
            for h in weather_data["hourly"]:
                if h["local_date"] == local_date:
                    hour_info = {
                        "time": h["local_dt"].strftime("%a %I %p"),
                        "temp": round(h["temp"]),
                        "icon": h["weather"][0]["icon"]
                    }
                    hours_for_day.append(hour_info)

            daily_forecasts.append({
                "date": local_dt.strftime("%A, %b %d"),
                "temp_day": round(day["temp"]["day"]),
                "temp_night": round(day["temp"]["night"]),
                "description": day["weather"][0]["description"],
                "icon": day["weather"][0]["icon"],
                "hours": hours_for_day
            })

        # Current weather
        current_weather = weather_data.get("current", {})
        weather_info = generate_current(geo_data, current_weather, city_name)

        z, x, y = latlon_to_tile(lat, lon, z=7) # z is zoom, 8 feels good for a city view

        return render_template(
            "result.html",
            today=weather_info,
            forecast=daily_forecasts,
            lat=lat,
            lon=lon,
            z=z, x=x, y=y,
            api_key=openweather_api_key
        )

    except (IndexError, ValueError):
        return "Invalid selection"
