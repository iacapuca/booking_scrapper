import argparse
from playwright.sync_api import sync_playwright
import pandas as pd
from datetime import datetime, timedelta
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
import logging

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

ammenities_list = ["nearest_beach", "breakfast", "gym", "beachfront", "free_parking", "spa",
                   "pool", "pet_friendly", "bar", "transfer", "room_service", "wifi", "restaurant", "accessibility"]


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


csv_file_path = 'hotels.csv'
df = pd.read_csv(csv_file_path)


def parse_price(value):
    if value == '—':
        return '—'
    if 'K' in value:
        return float(value.replace('K', '')) * 1000
    else:
        return float(value)


def fetch_availability(page, start=None, end=None):
    if start is None:
        start = datetime.now().date()
    if end is None:
        end = start + timedelta(6*30)

    if start > end:
        raise ValueError("Start date must be before end date")

    availability_dates = []
    existing_dates = set()

    try:
        page.wait_for_selector('[data-testid="searchbox-dates-container"]')
        page.click('[data-testid="searchbox-dates-container"]')

        prev_button_selector = '.a83ed08757.c21c56c305.f38b6daa18.d691166b09.f671049264.deab83296e.f4552b6561.dc72a8413c.c9804790f7'
        next_button_selector = '.a83ed08757.c21c56c305.f38b6daa18.d691166b09.f671049264.deab83296e.f4552b6561.dc72a8413c.f073249358'

        while True:
            first_date_element = page.query_selector(
                'td[role="gridcell"] span[data-date]')
            first_date_value = first_date_element.get_attribute('data-date')
            first_date = datetime.strptime(first_date_value, '%Y-%m-%d').date()

            if first_date <= start:
                break

            page.click(prev_button_selector)
            page.wait_for_timeout(1500)

        while first_date <= end:
            dates = page.locator('td[role="gridcell"] span[data-date]').all()
            for date_element in dates:
                date_value = date_element.get_attribute('data-date')
                date_as_date = datetime.strptime(date_value, '%Y-%m-%d').date()
                if start <= date_as_date <= end and date_value not in existing_dates:
                    span_locator = date_element.locator('.b1f25950bd')
                    if span_locator.count() > 0:
                        value = span_locator.first.inner_text()
                        price = parse_price(value)
                        availability_dates.append({
                            "date": date_value,
                            "value": price
                        })
                        existing_dates.add(date_value)

            page.wait_for_timeout(1500)
            first_date_element = page.query_selector(
                'td[role="gridcell"] span[data-date]')
            first_date_value = first_date_element.get_attribute('data-date')
            first_date = datetime.strptime(first_date_value, '%Y-%m-%d').date()

    except Exception as e:
        print(f"An error occurred: {e}")

    return availability_dates


def find_nearest_beach(beaches_locator):
    def convert_distance(distance_str):
        """Converts distance string to meters."""
        if 'km' in distance_str:
            return int(float(distance_str.replace(' km', '')) * 1000)
        else:
            return int(distance_str.replace(' m', ''))
    beach_data = beaches_locator.inner_text().strip().split('\n')
    beach_pairs = [(beach_data[i], convert_distance(beach_data[i + 1]))
                   for i in range(0, len(beach_data), 2)]
    nearest_beach = min(beach_pairs, key=lambda x: x[1])

    return {'name': nearest_beach[0], 'distance': nearest_beach[1]}


def fetch_ammenities(page):
    try:
        nearest_beach_locator = page.locator('ul[data-location-block-list="true"]').filter(
            has=page.locator('li:has-text("Praia")'))
        nearest_beach = find_nearest_beach(nearest_beach_locator)
        print(nearest_beach)

    except Exception as e:
        print(f"An error occurred: {e}")


def plot_availability_chart(availability_dates):
    dates_available = []
    prices = []
    dates_unavailable = []

    for item in availability_dates:
        date = datetime.strptime(item['date'], '%Y-%m-%d').date()
        price = item['value']
        if isinstance(price, float):
            dates_available.append(date)
            prices.append(price)
        else:
            dates_unavailable.append(date)

    plt.figure(figsize=(10, 6))

    # Plot available dates
    plt.plot(dates_available, prices, marker='o',
             linestyle='-', color='b', label='Available')

    # Plot unavailable dates
    plt.scatter(dates_unavailable, [
                0] * len(dates_unavailable), marker='x', color='r', label='Unavailable')

    plt.title('Price and Availability Over Time')
    plt.xlabel('Date')
    plt.ylabel('Price')
    plt.grid(True)
    plt.xticks(rotation=45)
    plt.legend()
    plt.tight_layout()
    plt.show()


def plot_heatmap(data):
    # Convert data to DataFrame
    df = pd.DataFrame(data)
    df['date'] = pd.to_datetime(df['date'])
    # Convert prices to numbers, '—' becomes NaN
    df['price'] = pd.to_numeric(df['value'], errors='coerce')

    # Ensuring all months and days are covered
    df['month'] = df['date'].dt.month
    df['day'] = df['date'].dt.day

    # Create a complete range of months and days
    all_months = df['month'].unique()
    all_days = df['day'].unique()

    # Pivot the DataFrame for the heatmap
    heatmap_data = df.pivot_table(
        index='day', columns='month', values='price', aggfunc='mean')

    # Fill missing values to ensure complete range
    heatmap_data = heatmap_data.reindex(
        index=all_days, columns=all_months).fillna(0)

    plt.figure(figsize=(12, 9))
    sns.heatmap(heatmap_data, cmap='viridis', annot=True, fmt='.0f')
    plt.title('Hotel Prices Heatmap')
    plt.xlabel('Month')
    plt.ylabel('Day of Month')
    plt.show()


def create_unavailability_and_price_chart(data):
    # Convert data to DataFrame
    df = pd.DataFrame(data)
    df['date'] = pd.to_datetime(df['date'])
    df['day_of_week'] = df['date'].dt.day_name()
    df['is_unavailable'] = df['value'] == '—'
    df['price'] = pd.to_numeric(df['value'], errors='coerce')

    # Ensure days of the week are in order
    ordered_days = ["Monday", "Tuesday", "Wednesday",
                    "Thursday", "Friday", "Saturday", "Sunday"]
    df['day_of_week'] = pd.Categorical(
        df['day_of_week'], categories=ordered_days, ordered=True)

    # Count unavailability and average price per day of the week
    unavailability_counts = df[df['is_unavailable']
                               ].groupby('day_of_week').size()
    average_prices = df.groupby('day_of_week')['price'].mean()

    # Plotting
    fig, ax1 = plt.subplots(figsize=(10, 6))

    # Bar chart for unavailability
    ax1.bar(unavailability_counts.index, unavailability_counts,
            color='tomato', alpha=0.6, label='Unavailability Count')
    ax1.set_xlabel('Day of the Week')
    ax1.set_ylabel('Count of Unavailable Days', color='tomato')
    ax1.tick_params(axis='y', labelcolor='tomato')
    ax1.set_xticklabels(ordered_days, rotation=45)

    # Line chart for average price
    ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis
    ax2.plot(average_prices.index, average_prices,
             color='blue', marker='o', label='Average Price')
    ax2.set_ylabel('Average Price', color='blue')
    ax2.tick_params(axis='y', labelcolor='blue')

    plt.title('Unavailability and Average Price by Day of the Week')
    fig.tight_layout()
    plt.show()


def create_correlation_matrix(data):
    # Convert data to DataFrame
    df = pd.DataFrame(data)
    df['date'] = pd.to_datetime(df['date'])
    # Convert day names to numerical values (Monday=0, Sunday=6)
    df['day_of_week'] = df['date'].dt.dayofweek
    df['price'] = df['value'].apply(lambda x: float(
        x.replace('K', '000')) if 'K' in str(x) else x)
    # Convert prices to numbers, '—' and other non-numerics become NaN
    df['price'] = pd.to_numeric(df['price'], errors='coerce')

    # Drop rows with NaN values in 'price'
    df = df.dropna(subset=['price'])

    # Create dummy variables for each day of the week
    day_dummies = pd.get_dummies(df['day_of_week'])
    df = pd.concat([df, day_dummies], axis=1)

    # Calculate correlation matrix
    df.corr()['price'].drop(
        'price')  # Drop the price-price correlation

    # Plotting the heatmap
    plt.figure(figsize=(8, 6))
    sns.heatmap(df.corr(), annot=True, cmap='coolwarm', fmt='.2f')
    plt.title('Correlation Matrix between Days of the Week and Price')
    plt.show()


def export_to_csv(data, filename="availability_data.csv"):
    df = pd.DataFrame(data)
    df.to_csv(filename, index=False)
    print(f"Data exported to {filename}")


def run(p, url):
    chromium = p.chromium
    browser = chromium.launch(headless=False, slow_mo=100)
    page = browser.new_page()
    print(url)
    page.goto(url)
    fetch_ammenities(page)

    # logging.info(f"Fetching availability for {url} from {start_date} to {end_date}")
    # availability_dates = fetch_availability(page)
    # export_to_csv(availability_dates)
    # plot_availability_chart(availability_dates)
    # create_unavailability_and_price_chart(availability_dates)
    # plot_heatmap(availability_dates)
    # create_correlation_matrix(availability_dates)


first_link = df['link'].iloc[44]

with sync_playwright() as p:
    run(p, url=first_link)

# for link in df['link']:
#     print(link)
#     with sync_playwright() as p:
#         run(p, url=link)
