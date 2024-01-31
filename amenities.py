import re
from playwright.sync_api import Page, Locator
from typing import List, Dict, Any
from utils import convert_distance


class HotelAmenities:
    def __init__(self, page: Page):
        self.page = page
        self.amenities_list: List[str] = []

    def get_amenities_list(self) -> None:
        """Retrieve all inner texts of li elements for amenities."""
        try:
            self.amenities_list = (
                self.page.locator("ul.c807d72881.d1a624a1cc.e10711a42e")
                .locator("li")
                .all_inner_texts()
            )
        except Exception as e:
            print(f"Error fetching amenities list: {e}")

    def get_all_amenities_status(self) -> Dict[str, Any]:
        """Retrieve the status of all amenities."""
        self.get_amenities_list()

        amenities_status = {
            "breakfast": self.has_amenity("Café da manhã"),
            "gym": self.has_amenity("Academia"),
            "beachfront": self.has_amenity("Beira-mar"),
            "free_parking": self.has_amenity("Estacionamento gratuito"),
            "spa": self.has_amenity("Spa"),
            "pool": self.has_amenity("Piscina"),
            "bar": self.has_amenity("Bar"),
            "transfer": self.has_amenity("Transfer"),
            "room_service": self.has_amenity("Serviço de quarto"),
            "wifi": self.has_amenity("Wi-Fi"),
            "restaurant": self.has_amenity("Restaurante"),
            "accessibility": self.has_amenity(
                "Instalações para pessoas com deficiência"
            ),
            "pet_friendly": self.is_pet_friendly(),
            "hotel_rating": self.get_hotel_rating(),
            "nearest_beach": self.find_nearest_beach(),
        }

        return amenities_status

    def get_ratings(self) -> List[Dict[str, float]]:
        """Retrieve the hotel's ratings from the page."""
        try:
            rating_elements: List[Locator] = (
                self.page.locator(
                    ".aca0ade214.ebac6e22e9.f66f916626.c2931f4182.c27e5d305d.db150fece4"
                )
                .first.locator("[data-testid='review-subscore']")
                .all()
            )

            def process_rating_element(element: Locator) -> Dict[str, float]:
                rating_text = element.inner_text()
                parts = list(filter(None, re.split(r"[\n\s]+", rating_text)))
                if len(parts) >= 2:
                    return {parts[0]: float(parts[-1].replace(",", "."))}
                return {}

            ratings = list(map(process_rating_element, rating_elements))
            # Filter out empty dicts resulting from invalid or incomplete data
            return list(filter(None, ratings))

        except Exception as e:
            print(f"Error fetching ratings: {e}")
            return []

    # Utility Methods as Part of the Class
    def has_amenity(self, amenity_name: str) -> bool:
        """Check if a specific amenity is in the amenities list."""
        return any(amenity_name in amenity for amenity in self.amenities_list)

    def is_pet_friendly(self) -> bool:
        """Check if the hotel is pet-friendly."""
        try:
            pets_locator = self.page.locator(
                ".f8d7936849.b48ab08804.b99b3906eb.f9a93eb27b"
            ).filter(has_text="Aceita pets")
            return pets_locator.count() > 0
        except Exception:
            return False

    def get_hotel_rating(self) -> Any:
        """Retrieve the hotel's rating from the page."""
        try:
            rating_element = self.page.locator('[aria-label^="Com nota"]').first
            aria_label_value = rating_element.get_attribute("aria-label")
            if aria_label_value is not None:
                match = re.search(r"\d+(\.\d+)?", aria_label_value)
                return float(match.group()) if match else None
            return None
        except Exception:
            return None

    def find_nearest_beach(self):
        try:
            nearest_beach_locator = self.page.locator(
                'ul[data-location-block-list="true"]'
            ).filter(has=self.page.locator('li:has-text("Praia")'))
            beach_data = nearest_beach_locator.inner_text().strip().split("\n")
            beach_pairs = [
                (beach_data[i], convert_distance(beach_data[i + 1]))
                for i in range(0, len(beach_data), 2)
            ]
            nearest_beach = min(beach_pairs, key=lambda x: x[1])

            return {"name": nearest_beach[0], "distance": nearest_beach[1]}
        except Exception as e:
            print(f"Error fetching nearest beach: {e}")
            return None
