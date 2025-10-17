from flask import Flask, render_template, request, session
import requests
import os
from datetime import datetime
from dotenv import load_dotenv
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

load_dotenv()
openweather_api_key =  os.getenv("OPEN_WEATHER_API")

app = Flask(__name__)
app.secret_key = '2203489023923'

#app_id = '08588f09c1a372a6800949cc83c889a2'

def build_weather_url(lat,lon): 
    return f"https://api.openweathermap.org/data/3.0/onecall?lat={lat}&lon={lon}&appid={openweather_api_key}&units=imperial"

def build_geo_url(city): 
    return f"http://api.openweathermap.org/geo/1.0/direct?q={city}&limit=5&appid={openweather_api_key}"

@app.route('/')
def hello_world():
    content = 'hello'
    return render_template('index.html', content=content)

@app.route('/', methods=['POST'])
def my_form_post():
    city_query = request.form['text']
    geo_url = build_geo_url(city_query)
    geo_request = requests.get(geo_url)
    geo_data = geo_request.json()
    session['geo_data'] = geo_data
    return render_template('index.html', geo=geo_data)

def generate_current(geo_data, current_weather, city_name):
    weather_info = {
        "name": city_name,  
        "city": city_name,
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

    if selected_index is not None and geo_data:
        try:
            index = int(selected_index)
            selected_location = geo_data[index]
            lat = selected_location.get('lat')
            lon = selected_location.get('lon')
            city_name = selected_location.get('name', "Unknown") 
            weather_url = build_weather_url(lat, lon)
            response = requests.get(weather_url)
            weather_data = response.json()


            # Extract the necessary information from the One Call API response
            current_weather = weather_data.get('current', {})
            weather_info = generate_current(geo_data, current_weather, city_name)

            daily_forecasts_raw = weather_data.get("daily", [])
            daily_forecasts = generate_daily(daily_forecasts_raw)
            hourly_forecasts = generate_hourly(weather_data)
            

            return render_template('result.html', results=weather_info, forecast = daily_forecasts, hourly = hourly_forecasts)

        except (IndexError, ValueError):
            return "Invalid selection"

    return "No selection or geo data available"
