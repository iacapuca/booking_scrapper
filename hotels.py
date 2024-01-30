import argparse
from playwright.sync_api import sync_playwright, Page
import pandas as pd
from datetime import datetime, timedelta
import logging
from amenities import HotelAmenities
from utils import parse_price


# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# Constants
CSV_FILE_PATH = "hotels.csv"

ammenities_list = [
    "nearest_beach",
    "breakfast",
    "gym",
    "beachfront",
    "free_parking",
    "spa",
    "pool",
    "pet_friendly",
    "bar",
    "transfer",
    "room_service",
    "wifi",
    "restaurant",
    "accessibility",
    "rating",
]


# def main():
#     parser = argparse.ArgumentParser(
#         description="Scrape hotel data and generate insights.")
#     parser.add_argument(
#         "--dryrun", help="Use existing CSV data for chart generation instead of scraping", action='store_true')
#     parser.add_argument(
#         "csv_file", help="Path to the CSV file containing hotel links")
#     parser.add_argument(
#         "--start_date", help="Start date for availability check (YYYY-MM-DD)", required=True)
#     parser.add_argument(
#         "--end_date", help="End date for availability check (YYYY-MM-DD)", required=True)
#     args = parser.parse_args()

#     df = pd.read_csv(args.csv_file)


# if __name__ == "__main__":
#     main()


csv_file_path = "hotels.csv"
df = pd.read_csv(csv_file_path)


def fetch_availability(
    page: Page, start: datetime = None, end: datetime = None
) -> list:
    start = start or datetime.now().date()
    end = end or start + timedelta(days=180)  # 6 months

    if start > end:
        raise ValueError("Start date must be before end date")

    availability_dates = []
    existing_dates = set()

    try:
        # Navigate to the date selector and open it
        page.wait_for_selector(
            '[data-testid="searchbox-dates-container"]', timeout=5000
        )
        page.click('[data-testid="searchbox-dates-container"]')

        # Selectors for previous and next buttons in the calendar
        prev_button_selector = ".a83ed08757.c21c56c305.f38b6daa18.d691166b09.f671049264.deab83296e.f4552b6561.dc72a8413c.c9804790f7"
        next_button_selector = ".a83ed08757.c21c56c305.f38b6daa18.d691166b09.f671049264.deab83296e.f4552b6561.dc72a8413c.f073249358"

        # Adjust the calendar view to the start date
        adjust_calendar_view(page, prev_button_selector, next_button_selector, start)

        # Collect availability data
        while True:
            # Fetch date elements visible in the current calendar view
            date_elements = page.locator('td[role="gridcell"] span[data-date]').all()

            for date_element in date_elements:
                date_value = date_element.get_attribute("data-date")
                date_as_date = datetime.strptime(date_value, "%Y-%m-%d").date()

                if date_as_date > end:
                    return availability_dates

                if start <= date_as_date <= end and date_value not in existing_dates:
                    price = fetch_price_for_date(date_element)
                    availability_dates.append({"date": date_value, "value": price})
                    existing_dates.add(date_value)

            # Move to the next set of dates
            page.click(next_button_selector)
            page.wait_for_timeout(1000)

    except Exception as e:
        logging.error(f"An error occurred while fetching availability: {e}")

    return availability_dates


def adjust_calendar_view(page, prev_button_selector, next_button_selector, target_date):
    """Adjust the calendar view to include the target start date."""
    while True:
        first_date_element = page.query_selector('td[role="gridcell"] span[data-date]')
        first_date_value = first_date_element.get_attribute("data-date")
        first_date = datetime.strptime(first_date_value, "%Y-%m-%d").date()

        if first_date <= target_date:
            break
        page.click(prev_button_selector)
        page.wait_for_timeout(1000)


def fetch_price_for_date(date_element):
    """Fetch the price for a given date element."""
    span_locator = date_element.locator(".b1f25950bd")
    if span_locator.count() > 0:
        return parse_price(span_locator.first.inner_text())
    return None


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


def fetch_ammenities(page):
    try:
        nearest_beach_locator = page.locator(
            'ul[data-location-block-list="true"]'
        ).filter(has=page.locator('li:has-text("Praia")'))
        nearest_beach = find_nearest_beach(nearest_beach_locator)
        print(nearest_beach)
        ammenities_list = (
            page.get_by_test_id("property-most-popular-facilities-wrapper")
            .first.locator("ul.c807d72881.d1a624a1cc.e10711a42e")
            .locator("li")
            .all_inner_texts()
        )

    except Exception as e:
        print(f"An error occurred: {e}")


def export_to_csv(data, filename="availability_data.csv"):
    df = pd.DataFrame(data)
    df.to_csv(filename, index=False)
    print(f"Data exported to {filename}")


def process_hotels(hotels_df):
    with sync_playwright() as p:
        for index, row in hotels_df.iterrows():
            if row.get("fetched", False):
                continue
            browser = p.chromium.launch()
            page = browser.new_page()
            hotel_url = row["url"]
            hotel_name = row["name"]
            hotel_data = fetch_hotel_data(page, hotel_url, hotel_name)
            browser.close()


def fetch_hotel_data(page: Page, url: str, name: str) -> pd.DataFrame:
    logging.info(f"Fetching Hotel data for {url}")
    # Navigate to the hotel's webpage
    page.goto(url)

    # Scrape the hotel's amenities
    # Assuming you have a method in HotelAmenities class to fetch amenities as a list
    hotel_amenities = HotelAmenities(page)
    amenities = hotel_amenities.get_all_amenities_status()
    ratings = hotel_amenities.get_ratings()

    # Fetch availability and prices
    # This is a placeholder for your availability fetching logic
    availability_data = fetch_availability(page)

    # Compile the data into a structured format
    # For example, using a DataFrame. Modify according to your actual data structure.
    hotel_data = pd.DataFrame(
        [
            {
                "Name": name,
                "Date": datetime.strptime(availability["date"], "%Y-%m-%d").date(),
                "Price": availability["value"],
                # **amenities,
            }
            for availability in availability_data
        ]
    )

    return hotel_data


def load_hotels_data(csv_file):
    return pd.read_csv(csv_file, sep=";")


hotels_df = load_hotels_data("hotels.csv")
processed_data = process_hotels(hotels_df)
