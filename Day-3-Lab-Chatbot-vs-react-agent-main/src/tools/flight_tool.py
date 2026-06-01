def search_flights(origin: str, destination: str) -> str:
    """Search for flights between two cities. Input: origin city (string), destination city (string). Returns flight info and price."""
    origin = origin.strip().lower()
    destination = destination.strip().lower()
    
    if "hanoi" in origin and "paris" in destination:
        return "Flight found: VN Airlines. Price: 800"
    elif "ho chi minh" in origin and "new york" in destination:
        return "Flight found: Emirates. Price: 1200"
    elif "hanoi" in origin and "da nang" in destination:
        return "Flight found: Vietjet. Price: 100"
    else:
        return "Flight found: Generic Airlines. Price: 500"
