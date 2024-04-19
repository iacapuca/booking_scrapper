import sys
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
PREV_BUTTON_SELECTOR = ".a83ed08757.c21c56c305.f38b6daa18.d691166b09.f671049264.deab83296e.f4552b6561.dc72a8413c.c9804790f7"
NEXT_BUTTON_SELECTOR = ".a83ed08757.c21c56c305.f38b6daa18.d691166b09.f671049264.deab83296e.f4552b6561.dc72a8413c.f073249358"

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


def navigate_to_calendar(page: Page):
    try:
        page.wait_for_selector(
            '[data-testid="searchbox-dates-container"]', timeout=5000
        )
        page.click('[data-testid="searchbox-dates-container"]')
        if not page.wait_for_selector(
            '[data-testid="searchbox-datepicker-calendar"]',
            state="visible",
            timeout=5000,
        ):
            raise TimeoutError(
                "Calendar did not become visible after clicking date container."
            )
        logging.info("Calendar is now visible.")
    except TimeoutError as te:
        logging.error(f"Navigation error: {te}")
        raise
    except Exception as e:
        logging.error(f"Failed to navigate to calendar due to an unexpected error: {e}")
        raise


def adjust_calendar_view(page, target_date):
    """Adjust the calendar view to include the target start date by clicking the navigation buttons."""
    current_date = page.query_selector(
        'td[role="gridcell"] span[data-date]'
    ).get_attribute("data-date")

    while datetime.strptime(current_date, "%Y-%m-%d").date() > target_date:
        page.click(PREV_BUTTON_SELECTOR)
        page.wait_for_selector('td[role="gridcell"] span[data-date]', state="visible")
        current_date = page.query_selector(
            'td[role="gridcell"] span[data-date]'
        ).get_attribute("data-date")
        logging.debug(f"Adjusted calendar to {current_date}.")


def fetch_availability(
    page: Page, start: datetime = None, end: datetime = None
) -> list:
    """Fetch availability data within the given date range from the hotel's booking page."""

    start = start or datetime.now().date()
    end = end or start + timedelta(days=180)  # 6 months

    if start > end:
        raise ValueError("Start date must be before end date")

    navigate_to_calendar(page)
    adjust_calendar_view(page, start)
    availability_dates = []

    try:
        while True:
            date_elements = page.locator('td[role="gridcell"] span[data-date]').all()
            for date_element in date_elements:
                process_date_element(date_element, start, end, availability_dates)
            if not navigate_calendar_next(page, end):
                break
    except Exception as e:
        logging.error(f"Error during availability fetch: {e}")
        raise

    return availability_dates


def process_date_element(date_element, start, end, availability_dates):
    date_value = date_element.get_attribute("data-date")
    date_as_date = datetime.strptime(date_value, "%Y-%m-%d").date()
    if date_as_date > end:
        return False
    if date_as_date >= start:
        price = fetch_price_for_date(date_element)
        availability_dates.append({"date": date_value, "value": price or None})
    return True


def navigate_calendar_next(page, end):
    page.click(NEXT_BUTTON_SELECTOR)
    page.wait_for_selector('td[role="gridcell"] span[data-date]', state="visible")
    logging.debug("Navigated to next set of dates.")
    current_date = datetime.strptime(
        page.query_selector('td[role="gridcell"] span[data-date]').get_attribute(
            "data-date"
        ),
        "%Y-%m-%d",
    ).date()
    return current_date <= end


def fetch_price_for_date(date_element):
    """Fetch the price for a given date element."""
    span_locator = date_element.locator(".b1f25950bd")
    if span_locator.count() > 0:
        return parse_price(span_locator.first.inner_text())
    return None


def export_to_csv(data, filename="availability_data.csv"):
    """Export data to a CSV file."""
    df = pd.DataFrame(data)
    df.to_csv(filename, index=False)
    logging.info(f"Data exported to {filename}")


def process_hotels(hotels_df):

    if not hotels_df["fetched"].eq(False).any():
        logging.info("No hotels left to process. Exiting program.")
        return sys.exit(0)

    all_hotel_data = []  # List to store each hotel's DataFrame

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, slow_mo=300)
        for index, row in hotels_df.iterrows():
            if row.get("fetched", False):
                continue
            page = browser.new_page()
            hotel_url = row["url"]
            hotel_name = row["name"]
            try:
                hotel_data = fetch_hotel_data(page, hotel_url, hotel_name)
                all_hotel_data.append(hotel_data)
                hotels_df.at[index, "fetched"] = True
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
    print(ratings_list)
    ratings = {k: v for d in ratings_list for k, v in d.items()}
    print(ratings)

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


def main():
    # Load the data
    try:
        hotels_df = load_hotels_data(CSV_FILE_PATH)
        logging.info("Data loaded successfully.")
    except Exception as e:
        logging.error(f"Failed to load data: {e}")
        sys.exit(1)

    # Process the data
    try:
        processed_data = process_hotels(hotels_df)
        logging.info("Hotels processed successfully.")
    except Exception as e:
        logging.error(f"Error during processing: {e}")
        sys.exit(1)

    # Export results
    try:
        export_to_csv(processed_data, "all_hotels_data.csv")
        logging.info("Data exported successfully.")
    except Exception as e:
        logging.error(f"Failed to export data: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
