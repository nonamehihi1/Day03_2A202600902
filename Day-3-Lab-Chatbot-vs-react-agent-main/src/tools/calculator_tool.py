def calculate_trip_cost(flight_price: float, hotel_rate: float, nights: int, discount_percent: float) -> str:
    """Calculate total trip cost. Input: flight price (number), hotel rate (number), nights (number), discount percentage (number). Returns final cost."""
    try:
        flight = float(flight_price)
        hotel = float(hotel_rate)
        n = int(nights)
        discount = float(discount_percent)
        
        base_cost = flight + (hotel * n)
        final_cost = base_cost * (1 - (discount / 100))
        return f"Total cost: ${final_cost:.2f}"
    except ValueError:
        return "Error: Please provide numbers only for calculation arguments."
    except Exception as e:
        return f"Error in calculation: {str(e)}"
