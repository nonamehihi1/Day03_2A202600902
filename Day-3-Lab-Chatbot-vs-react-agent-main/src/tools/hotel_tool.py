def check_hotel(city: str) -> str:
    """Check hotel prices in a city. Input: city name (string). Returns hotel name and rate per night."""
    city = city.strip().lower()
    
    if "paris" in city:
        return "Hotel found: Paris Grand Hotel. Rate: 150 per night."
    elif "new york" in city:
        return "Hotel found: NYC Central. Rate: 200 per night."
    elif "da nang" in city:
        return "Hotel found: Ocean View Hotel. Rate: 50 per night."
    else:
        return "Hotel found: City Center Inn. Rate: 100 per night."
