"""Weather stats collector using wttr.in API."""

import requests
from urllib.parse import quote
from typing import Optional, Dict, Any
from .base import BaseCollector
from config import USE_MOCKS


class WeatherCollector(BaseCollector):
    """Collector for weather statistics from wttr.in."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config, config.get("poll_interval", 600))
        self.city = config.get("city", "New York")
    
    def get_data_for_city(self, city: str = None) -> Optional[Dict[str, Any]]:
        """
        Fetch weather data for a specific city.
        
        Args:
            city: City name (overrides config city if provided)
        
        Returns:
            Weather data dictionary or None
        """
        if USE_MOCKS:
            return self._fetch_mock_data()
        
        target_city = city or self.city
        if not target_city:
            return None
        
        return self._fetch_weather_data(target_city)
    
    def _fetch_data(self) -> Optional[Dict[str, Any]]:
        """Fetch weather data from wttr.in API using configured city."""
        return self.get_data_for_city(self.city)
    
    def _fetch_weather_data(self, city: str) -> Optional[Dict[str, Any]]:
        """Internal method to fetch weather data for a given city."""
        try:
            # Fetch JSON format data from wttr.in
            # URL encode city name to handle spaces and special characters
            city_encoded = quote(city)
            url = f"https://wttr.in/{city_encoded}"
            params = {
                "format": "j1",  # JSON format
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Parse current conditions
            current = data.get("current_condition", [{}])[0]
            if not current:
                return None
            
            # Parse forecast (next 3 days)
            forecast_data = data.get("weather", [])
            forecast = []
            for i, day in enumerate(forecast_data[:3]):  # Limit to 3 days
                # Get the daily summary (first item in hourly data)
                day_data = day.get("hourly", [{}])[0]
                forecast.append({
                    "date": day.get("date", ""),
                    "maxtemp_c": float(day_data.get("tempC", 0)),
                    "mintemp_c": float(day_data.get("tempC", 0)),  # wttr.in format uses hourly, use tempC
                    "condition": day_data.get("weatherDesc", [{}])[0].get("value", "Unknown"),
                    "daily_chance_of_rain": int(day_data.get("chanceofrain", 0)),
                })
            
            # For min/max temps, check the actual min/max from the day data
            # wttr.in provides maxtempC and mintempC in the weather array
            for i, day in enumerate(forecast_data[:3]):
                if i < len(forecast):
                    forecast[i]["maxtemp_c"] = float(day.get("maxtempC", forecast[i]["maxtemp_c"]))
                    forecast[i]["mintemp_c"] = float(day.get("mintempC", forecast[i]["mintemp_c"]))
            
            return {
                "current": {
                    "temp_c": float(current.get("temp_C", 0)),
                    "condition": current.get("weatherDesc", [{}])[0].get("value", "Unknown"),
                    "humidity": int(current.get("humidity", 0)),
                    "wind_kph": float(current.get("windspeedKmph", 0)),
                    "feelslike_c": float(current.get("FeelsLikeC", 0)),
                },
                "forecast": forecast,
            }
        except requests.exceptions.RequestException as e:
            print(f"Weather API request failed: {e}")
            return None
        except (KeyError, ValueError, IndexError) as e:
            print(f"Weather API response parse error: {e}")
            return None
    
    def _fetch_mock_data(self) -> Optional[Dict[str, Any]]:
        """Fetch mock data for testing."""
        # Return default mock data
        return {
            "current": {
                "temp_c": 22.5,
                "condition": "Partly Cloudy",
                "humidity": 65,
                "wind_kph": 12.3,
                "feelslike_c": 23.0,
            },
            "forecast": [
                {
                    "date": "2024-01-15",
                    "maxtemp_c": 24.0,
                    "mintemp_c": 18.0,
                    "condition": "Clear",
                    "daily_chance_of_rain": 10,
                },
                {
                    "date": "2024-01-16",
                    "maxtemp_c": 26.0,
                    "mintemp_c": 20.0,
                    "condition": "Sunny",
                    "daily_chance_of_rain": 0,
                },
                {
                    "date": "2024-01-17",
                    "maxtemp_c": 23.0,
                    "mintemp_c": 17.0,
                    "condition": "Cloudy",
                    "daily_chance_of_rain": 60,
                },
            ],
        }

