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
    return f"https://api.openweathermap.org/data/3.0/onecall?lat={lat}&lon={lon}&exclude=hourly&appid={openweather_api_key}&units=imperial"

def build_geo_url(city): 
    return f"http://api.openweathermap.org/geo/1.0/direct?q={city}&limit=5&appid={openweather_api_key}"

@app.route('/')
def hello_world():
    content = 'hello'
    return render_template('index.html', content=content)

@app.route('/', methods=['POST'])
def my_form_post():
    text = request.form['text']
    geo_url = build_geo_url(text)
    geo_request = requests.get(geo_url)
    geo_data = geo_request.json()
    session['geo_data'] = geo_data
    return render_template('index.html', geo=geo_data)

@app.route('/select', methods=['POST'])
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
            data = response.json()
            #print(session['geo_data'].get('country'))

            # Extract the necessary information from the One Call API response
            current_weather = data.get('current', {})
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
            daily_forecasts_raw = data.get("daily", [])

            daily_forecasts = []
            for day in daily_forecasts_raw:
                forecast_date = datetime.utcfromtimestamp(day.get('dt')).strftime('%A, %b %d')
                daily_forecasts.append({
                    'date': forecast_date,
                    'temp_day': round(day.get('temp', {}).get('day', 0)),
                    'temp_night': round(day.get('temp', {}).get('night', 0)),
                    'description': day.get('weather', [{}])[0].get('description', 'No description'),
                    'icon': day.get('weather', [{}])[0].get('icon', '01d')
                })
            
            return render_template('select.html', results=weather_info, forecast = daily_forecasts)

        except (IndexError, ValueError):
            return "Invalid selection"

    return "No selection or geo data available"
