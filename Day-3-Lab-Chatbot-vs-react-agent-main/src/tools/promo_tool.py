def check_promo(code: str) -> str:
    """Check travel discount code. Input: promo code (string). Returns discount percentage."""
    code = code.strip().upper()
    if code == "SUMMER":
        return "Valid code. Discount: 10%"
    elif code == "WINTER":
        return "Valid code. Discount: 20%"
    return "Invalid code. Discount: 0%"
