from playwright.sync_api import sync_playwright
import pandas as pd


def generate_csv(hotels_info):
    print("Generating CSV...")
    df = pd.DataFrame(hotels_info)
    df.drop_duplicates(subset="name", inplace=True)
    df.to_csv("hotels.csv", index=False, encoding="utf-8-sig")


def number_of_pages(page):
    pagination = page.locator(
        '[data-testid="pagination"] nav').all_inner_texts()
    numbers = [int(num) for text in pagination for num in text.split('\n')]
    max_value = max(numbers) if numbers else None
    return max_value


def run(p):
    chromium = p.chromium
    browser = chromium.launch(headless=False, slow_mo=50)
    page = browser.new_page()
    page.goto("https://www.booking.com/searchresults.pt-br.html?label=gen173nr-1BCAEoggI46AdIM1gEaCCIAQGYAS24AQfIAQzYAQHoAQGIAgGoAgO4Aua9m6wGwAIB0gIkZTRkMGZhZTgtMzNkMS00YjM4LWI3ZmYtYTMzMWQ3Yzk4MTA32AIF4AIB&sid=bb851cb4cede7a0550c68031704f5f89&aid=304142&ss=Porto+de+Galinhas&ssne=Porto+de+Galinhas&ssne_untouched=Porto+de+Galinhas&lang=pt-br&src=searchresults&dest_id=-663612&dest_type=city&checkin=2024-05-08&checkout=2024-05-09&group_adults=1&no_rooms=1&group_children=0&nflt=ht_id%3D204")
    page.wait_for_selector('[data-testid="pagination"]')
    page.wait_for_selector('[aria-label="Ignorar informações de login."]')
    page.click('[aria-label="Ignorar informações de login."]')
    pages = number_of_pages(page)
    hotels_info = []
    for i in range(1,  pages + 1):
        print(f"Page {i}")
        print(page.locator('.a7c436bd0b').inner_text())
        property_cards = page.get_by_test_id("property-card").all()
        for property_card in property_cards:
            hotel_name = property_card.get_by_test_id("title").inner_text()
            hotel_link = property_card.get_by_test_id(
                "title-link").get_attribute("href")
            hotels_info.append(
                {"name": hotel_name, "link": hotel_link})
        if i != pages:
            page.click('[aria-label="Página seguinte"]')
            page.wait_for_selector('[data-testid="pagination"]')
            page.get_by_test_id("overlay-spinner").wait_for(state='hidden')

    generate_csv(hotels_info)


with sync_playwright() as p:
    run(p)
