from flask import Flask, render_template, request, session
import requests
import os
from dotenv import load_dotenv
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
load_dotenv()
openweather_api_key =  os.getenv("OPEN_WEATHER_API")

app = Flask(__name__)
app.secret_key = '2203489023923'

#app_id = '08588f09c1a372a6800949cc83c889a2'

def build_weather_url(lat,lon): 
    return f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={openweather_api_key}&units=imperial"

def build_geo_url(city): 
    return f"http://api.openweathermap.org/geo/1.0/direct?q={city}&limit=5&appid={openweather_api_key}"

@app.route('/')
def hello_world():
    return render_template('index.html')

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
            city_name = selected_location.get('name')
            weather_url =build_weather_url(lat, lon)
            response = requests.get(weather_url)
            data = response.json()

            return render_template('select.html', results = {
                "name":city_name,
                "city": data.get("name", "Unknown"),
                "country": data["sys"].get("country", "Unknown"),
                "temperature_f": round(data["main"]["temp"]),
                "feels_like_f": round(data["main"]["feels_like"]),
                "humidity": data["main"].get("humidity"),
                "description": data["weather"][0].get("description", "No description"),
                "icon": data["weather"][0].get("icon", "No icon")
            })

            return render_template("select.html", name=name, lat=lat, lon=lon)
            return f"You selected: {name}, {state}, {country}"
        except (IndexError, ValueError):
            return "Invalid selection"

    return "No selection or geo data available"
