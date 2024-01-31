import os
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

column_name_mapping = {
    "Name": "name",
    "Date": "date",
    "Price": "price",
    "Funcionários": "staff_rating",
    "Comodidades": "amenities_rating",
    "Limpeza": "cleaning_rating",
    "Conforto": "comfort_rating",
    "Custo-benefício": "cost-benefit_rating",
    "Localização": "location_rating",
    "WiFi": "wifi_rating",
}


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


def export_to_csv(data, filename="availability_data.csv"):
    df = pd.DataFrame(data)
    df.to_csv(filename, index=False)
    print(f"Data exported to {filename}")


def process_hotels(hotels_df):
    all_hotel_data = []  # List to store each hotel's DataFrame

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, slow_mo=100)
        for index, row in hotels_df.iterrows():
            if row.get("fetched", False):
                continue
            page = browser.new_page()
            hotel_url = row["url"]
            hotel_name = row["name"]
            hotels_df.at[index, "fetched"] = True
            try:
                hotel_data = fetch_hotel_data(page, hotel_url, hotel_name)
                all_hotel_data.append(hotel_data)
            except Exception as e:
                logging.error(
                    f"Error processing hotel {hotel_name} at {hotel_url}: {e}"
                )
            finally:
                page.close()

        browser.close()

    # Save the updated DataFrame back to the original CSV
    hotels_df.to_csv("hotels.csv", sep=";", index=False)

    # Concatenate all hotel data into a single DataFrame
    combined_hotel_data = pd.concat(all_hotel_data, ignore_index=True)
    combined_hotel_data.rename(columns=column_name_mapping, inplace=True)

    return combined_hotel_data


def fetch_hotel_data(page: Page, url: str, name: str) -> pd.DataFrame:
    logging.info(f"Fetching Hotel data for {url}")
    # Navigate to the hotel's webpage
    page.goto(url)

    # Scrape the hotel's amenities
    # Assuming you have a method in HotelAmenities class to fetch amenities as a list
    hotel_amenities = HotelAmenities(page)
    amenities = hotel_amenities.get_all_amenities_status()
    ratings_list = hotel_amenities.get_ratings()
    ratings = {k: v for d in ratings_list for k, v in d.items()}

    # Fetch availability and prices
    availability_data = fetch_availability(page)

    # Compile the data into a structured format
    hotel_data = pd.DataFrame(
        [
            {
                "Name": name,
                "Date": datetime.strptime(availability["date"], "%Y-%m-%d").date(),
                "Price": availability["value"],
                **ratings,
                **amenities,
            }
            for availability in availability_data
        ]
    )

    return hotel_data


def load_hotels_data(csv_file):
    return pd.read_csv(csv_file, sep=";")


hotels_df = load_hotels_data("hotels.csv")
processed_data = process_hotels(hotels_df)
export_to_csv(processed_data, "all_hotels_data.csv")
