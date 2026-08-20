from app.core.config import get_settings


settings = get_settings()


def tou_period(hour: int) -> str:
    if 18 <= hour < 22:
        return "peak"
    if hour >= 23 or hour < 7:
        return "valley"
    return "flat"


def tou_price(hour: int) -> float:
    period = tou_period(hour)
    mapping = {
        "peak": settings.price_peak,
        "flat": settings.price_flat,
        "valley": settings.price_valley,
    }
    return mapping[period]


def carbon_of(kwh: float) -> float:
    return round(kwh * settings.carbon_kg_per_kwh, 3)


def estimate_bill(kwh: float, avg_price: float | None = None) -> float:
    price = avg_price if avg_price and avg_price > 0 else settings.price_flat
    return round(kwh * price, 2)
