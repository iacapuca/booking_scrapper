import re
from playwright.sync_api import Page, Locator
from typing import List, Dict, Any


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

        return {"breakfast": self.has_amenity("Café da manhã")}
        amenities_status = {
            "breakfast": has_breakfast(self.amenities_list),
            "gym": has_gym(self.amenities_list),
            "beachfront": has_beachfront(self.amenities_list),
            "free_parking": has_free_parking(self.amenities_list),
            "spa": has_spa(self.amenities_list),
            "pool": has_pool(self.amenities_list),
            "bar": has_bar(self.amenities_list),
            "transfer": has_transfer(self.amenities_list),
            "room_service": has_room_service(self.amenities_list),
            "wifi": has_wifi(self.amenities_list),
            "restaurant": has_restaurant(self.amenities_list),
            "accessibility": has_accessibility(self.amenities_list),
            "pet_friendly": is_pet_friendly(self.page),
            "hotel_rating": get_hotel_rating(self.page),
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


# Utility Functions for Checking Specific Amenities


def has_breakfast(ammenities_list):
    """Check if 'Café da manhã' is in the amenities list."""
    return any("Café da manhã" in amenity for amenity in ammenities_list)


def has_gym(ammenities_list):
    """Check if 'Academia' is in the amenities list."""
    return any("Academia" in amenity for amenity in ammenities_list)


def has_beachfront(ammenities_list):
    """Check if 'Beira-mar' is in the amenities list."""
    return any("Beira-mar" in amenity for amenity in ammenities_list)


def has_free_parking(ammenities_list):
    """Check if 'Estacionamento gratuito' is in the amenities list."""
    return any("Estacionamento gratuito" in amenity for amenity in ammenities_list)


def has_spa(ammenities_list):
    """Check if 'Spa' is in the amenities list."""
    return any("Spa" in amenity for amenity in ammenities_list)


def has_pool(ammenities_list):
    """Check if 'Piscina' is in the amenities list."""
    return any("Piscina" in amenity for amenity in ammenities_list)


def has_bar(ammenities_list):
    """Check if 'Bar' is in the amenities list."""
    return any("Bar" in amenity for amenity in ammenities_list)


def has_transfer(ammenities_list):
    """Check if 'Transfer' is in the amenities list."""
    return any("Transfer" in amenity for amenity in ammenities_list)


def has_room_service(ammenities_list):
    """Check if 'Serviço de quarto' is in the amenities list."""
    return any("Serviço de quarto" in amenity for amenity in ammenities_list)


def has_wifi(ammenities_list):
    """Check if 'Wi-Fi' is in the amenities list."""
    return any("Wi-Fi" in amenity for amenity in ammenities_list)


def has_restaurant(ammenities_list):
    """Check if 'Restaurante' is in the amenities list."""
    return any("Restaurante" in amenity for amenity in ammenities_list)


def has_accessibility(ammenities_list):
    """Check if 'Instalações para pessoas com deficiência' is in the amenities list."""
    return any(
        "Instalações para pessoas com deficiência" in amenity
        for amenity in ammenities_list
    )


def is_pet_friendly(page):
    """Check if the hotel is pet-friendly."""
    pets_locator = page.locator(".f8d7936849.b48ab08804.b99b3906eb.f9a93eb27b").filter(
        has_text="Aceita pets"
    )
    return pets_locator.count() > 0


def get_hotel_rating(page):
    """Retrieve the hotel's rating from the page."""
    rating_elements = page.locator('[aria-label^="Com nota"]')
    if rating_elements.count() > 0:
        aria_label_value = rating_elements.first.get_attribute("aria-label")
        match = re.search(r"\d+(\.\d+)?", aria_label_value)
        return (
            float(match.group())
            if match
            else "Rating number not found in the aria-label"
        )
    return "Rating element not found"
