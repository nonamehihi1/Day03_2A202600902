import requests

def get_weather(city: str) -> str:
    """Get the current weather for a given city. Input: city name (string). Returns a brief weather description."""
    try:
        # 1. First get coordinates for the city using Open-Meteo Geocoding API
        geocode_url = "https://geocoding-api.open-meteo.com/v1/search"
        geocode_params = {
            "name": city.strip(),
            "count": 1,
            "language": "en",
            "format": "json"
        }
        
        geo_response = requests.get(geocode_url, params=geocode_params, timeout=5)
        geo_response.raise_for_status()
        geo_data = geo_response.json()
        
        if "results" not in geo_data or not geo_data["results"]:
            return f"Could not find coordinates for city: '{city}'."
            
        location = geo_data["results"][0]
        lat = location["latitude"]
        lon = location["longitude"]
        name = location["name"]
        country = location.get("country", "")
        
        # 2. Get the weather using the coordinates
        weather_url = "https://api.open-meteo.com/v1/forecast"
        weather_params = {
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,wind_speed_10m",
            "timezone": "auto"
        }
        
        weather_response = requests.get(weather_url, params=weather_params, timeout=5)
        weather_response.raise_for_status()
        weather_data = weather_response.json()
        
        current = weather_data.get("current", {})
        temp = current.get("temperature_2m", "N/A")
        feels_like = current.get("apparent_temperature", "N/A")
        humidity = current.get("relative_humidity_2m", "N/A")
        wind = current.get("wind_speed_10m", "N/A")
        
        return (f"Current weather in {name}, {country}:\n"
                f"- Temperature: {temp}°C (Feels like: {feels_like}°C)\n"
                f"- Humidity: {humidity}%\n"
                f"- Wind Speed: {wind} km/h")
            
    except requests.exceptions.RequestException as e:
        return f"Error connecting to weather service: {str(e)}"
    except Exception as e:
        return f"Error parsing weather data: {str(e)}"
