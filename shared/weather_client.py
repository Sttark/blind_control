import requests
from typing import Tuple, Optional
from datetime import datetime, timedelta
from astral import Astral

class WeatherClient:
    """Weather API client for blind control system"""
    
    def __init__(self, api_key: str, location: str, cloud_threshold: int = 15):
        self.api_key = api_key
        self.location = location
        self.cloud_threshold = cloud_threshold
    
    def get_cloud_cover(self) -> Tuple[Optional[int], Optional[str]]:
        """Get current cloud cover percentage and condition"""
        try:
            url = f"http://api.weatherapi.com/v1/current.json?key={self.api_key}&q={self.location}&aqi=no"
            response = requests.get(url)
            data = response.json()
            
            # Get cloud cover percentage (0-100)
            cloud_cover = data['current']['cloud']
            
            # Also get condition text for logging
            condition = data['current']['condition']['text']
            
            print(f"Current conditions: {condition}, Cloud cover: {cloud_cover}%")
            return cloud_cover, condition
        except Exception as e:
            print(f"Error checking weather: {e}")
            return None, None
    
    def is_overcast(self) -> bool:
        """Determine if it's overcast based on cloud threshold"""
        cloud_cover, _ = self.get_cloud_cover()
        if cloud_cover is not None:
            return cloud_cover >= self.cloud_threshold
        return False
    
    def should_lower_blinds(self) -> bool:
        """Determine if blinds should be lowered based on weather"""
        return not self.is_overcast()
    
    def should_raise_blinds(self) -> bool:
        """Determine if blinds should be raised based on weather"""
        return self.is_overcast()

class SunsetScheduler:
    """Sunset-based scheduling for blind control"""
    
    def __init__(self, city_name: str = 'New York'):
        self.astral = Astral()
        self.city = self.astral[city_name]
    
    def get_sunset_time(self, date: datetime = None) -> datetime:
        """Get sunset time for the specified date (default: today)"""
        if date is None:
            date = datetime.now()
        
        sun_info = self.city.sun(date=date, local=True)
        sunset = sun_info['sunset']
        
        print(f"Sunset time for {date.strftime('%Y-%m-%d')}: {sunset.strftime('%H:%M:%S')}")
        return sunset
    
    def calculate_schedule_times(self, lower_offset_minutes: int, raise_offset_minutes: int, 
                                date: datetime = None) -> Tuple[datetime, datetime]:
        """Calculate the times to lower and raise blinds based on sunset"""
        sunset = self.get_sunset_time(date)
        
        lower_time = sunset - timedelta(minutes=lower_offset_minutes)
        raise_time = sunset - timedelta(minutes=raise_offset_minutes)
        
        return lower_time, raise_time
    
    def format_schedule_times(self, lower_offset_minutes: int, raise_offset_minutes: int,
                             date: datetime = None) -> dict:
        """Get formatted schedule times for display"""
        sunset = self.get_sunset_time(date)
        lower_time, raise_time = self.calculate_schedule_times(lower_offset_minutes, raise_offset_minutes, date)
        
        return {
            'sunset_time': sunset.strftime("%I:%M %p"),
            'lower_time': lower_time.strftime("%I:%M %p"),
            'raise_time': raise_time.strftime("%I:%M %p"),
            'lower_offset': lower_offset_minutes,
            'raise_offset': raise_offset_minutes
        }
