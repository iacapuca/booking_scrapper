def convert_distance(distance_str):
    """Converts distance string to meters."""
    # Remove commas for thousands separator
    distance_str = distance_str.replace(",", ".")

    if "km" in distance_str:
        return float(distance_str.replace(" km", "")) * 1000
    else:
        return float(distance_str.replace(" m", ""))


def parse_price(value):
    if value == "—":
        return "—"
    if "K" in value:
        return float(value.replace("K", "")) * 1000
    else:
        return float(value)
