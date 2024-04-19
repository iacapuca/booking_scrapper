# Booking Data Scraper

This project provides a set of Python scripts for scraping hotel data from Booking.com using Playwright, processing it, and saving the results to a CSV file. It includes functionalities to scrape various hotel attributes such as amenities, ratings, and availability from specified URLs.

## Project Structure

- `hotels.py`: Main script to initiate the scraping process, handle data aggregation, and export to CSV.
- `amenities.py`: Contains the `HotelAmenities` class responsible for extracting detailed amenities and ratings from a hotel's webpage.
- `main.py`: Fetch hotels and generate a .csv file with a list of hotels
- `utils.py`: Utility functions including price parsing and distance conversions which assist in data handling.
- `requirements.txt`: Lists all the Python dependencies required by the project.

## Features

- Fetch and process hotel data including amenities, pricing, and ratings.
- Export the collected data into a structured CSV format.
- Configurable logging to track the process and handle errors effectively.

## Dependencies

Ensure you have Python 3.7+ installed. This project uses several third-party libraries which can be installed using pip:

```bash
pip install -r requirements.txt
playwright install
```

## Usage
```bash
python hotels.py
```
