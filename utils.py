def find_nearest_beach(beaches_locator):
    def convert_distance(distance_str):
        """Converts distance string to meters."""
        if "km" in distance_str:
            return int(float(distance_str.replace(" km", "")) * 1000)
        else:
            return int(distance_str.replace(" m", ""))

    beach_data = beaches_locator.inner_text().strip().split("\n")
    beach_pairs = [
        (beach_data[i], convert_distance(beach_data[i + 1]))
        for i in range(0, len(beach_data), 2)
    ]
    nearest_beach = min(beach_pairs, key=lambda x: x[1])

    return {"name": nearest_beach[0], "distance": nearest_beach[1]}


def parse_price(value):
    if value == "—":
        return "—"
    if "K" in value:
        return float(value.replace("K", "")) * 1000
    else:
        return float(value)
