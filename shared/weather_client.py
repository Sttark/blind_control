import requests
from typing import Tuple, Optional
from datetime import datetime, timedelta
from astral import Location, Astral
from zoneinfo import ZoneInfo

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
    
    def __init__(self, api_key: str, location_query: str, fallback_city: str = 'New York'):
        self.api_key = api_key
        self.location_query = location_query
        self.fallback_city = fallback_city
        self._location_details = None
        self._location = None
        self._astral = Astral()
    
    def _get_location_details(self) -> dict:
        if self._location_details:
            return self._location_details
        
        try:
            url = f"http://api.weatherapi.com/v1/current.json?key={self.api_key}&q={self.location_query}&aqi=no"
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            data = response.json()
            location_info = data.get('location', {})
            
            latitude = location_info.get('lat')
            longitude = location_info.get('lon')
            timezone_id = location_info.get('tz_id')
            
            if latitude is None or longitude is None or timezone_id is None:
                raise ValueError("Incomplete location information in weather API response")
            
            self._location_details = {
                "latitude": float(latitude),
                "longitude": float(longitude),
                "timezone": timezone_id
            }
            
            print(f"[SunsetScheduler] Loaded location data: lat={latitude}, lon={longitude}, tz={timezone_id}")
        except Exception as e:
            print(f"[SunsetScheduler] Error retrieving location info for {self.location_query}: {e}")
            print(f"[SunsetScheduler] Falling back to default {self.fallback_city} coordinates.")
            
            fallback_city = self._astral[self.fallback_city]
            self._location_details = {
                "latitude": fallback_city.latitude,
                "longitude": fallback_city.longitude,
                "timezone": fallback_city.timezone
            }
        
        return self._location_details
    
    def _get_location(self) -> Location:
        if self._location:
            return self._location
        
        details = self._get_location_details()
        location = Location()
        location.name = "Configured Location"
        location.region = str(self.location_query)
        location.latitude = details['latitude']
        location.longitude = details['longitude']
        location.timezone = details['timezone']
        location.elevation = 0
        
        self._location = location
        return self._location
    
    def _ensure_timezone_datetime(self, date: datetime, tz_name: str) -> datetime:
        tz = ZoneInfo(tz_name)
        if date.tzinfo is None:
            return date.replace(tzinfo=tz)
        return date.astimezone(tz)
    
    def get_sunset_time(self, date: datetime = None) -> datetime:
        """Get sunset time for the specified date (default: today)"""
        location = self._get_location()
        tz_name = location.timezone
        
        if date is None:
            target_datetime = datetime.now(ZoneInfo(tz_name))
        else:
            target_datetime = self._ensure_timezone_datetime(date, tz_name)
        
        sun_info = location.sun(date=target_datetime, local=True)
        sunset = sun_info['sunset']
        
        print(f"Sunset time for {target_datetime.strftime('%Y-%m-%d')} ({tz_name}): {sunset.strftime('%H:%M:%S')}")
        return sunset
    
    def calculate_schedule_times(self, lower_offset_minutes: int, raise_offset_minutes: int, 
                                date: datetime = None, sunset: datetime = None) -> Tuple[datetime, datetime]:
        """Calculate the times to lower and raise blinds based on sunset"""
        if sunset is None:
            sunset = self.get_sunset_time(date)
        
        lower_time = sunset - timedelta(minutes=lower_offset_minutes)
        raise_time = sunset + timedelta(minutes=raise_offset_minutes)
        
        return lower_time, raise_time
    
    def format_schedule_times(self, lower_offset_minutes: int, raise_offset_minutes: int,
                             date: datetime = None) -> dict:
        """Get formatted schedule times for display"""
        sunset = self.get_sunset_time(date)
        lower_time, raise_time = self.calculate_schedule_times(
            lower_offset_minutes, raise_offset_minutes, date, sunset)
        timezone = self._get_location_details().get('timezone')
        
        return {
            'sunset_time': sunset.strftime("%I:%M %p"),
            'lower_time': lower_time.strftime("%I:%M %p"),
            'raise_time': raise_time.strftime("%I:%M %p"),
            'lower_offset': lower_offset_minutes,
            'raise_offset': raise_offset_minutes,
            'timezone': timezone
        }
