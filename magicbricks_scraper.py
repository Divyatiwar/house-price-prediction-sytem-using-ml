import re
import os
import requests
from bs4 import BeautifulSoup
import csv
import time
import random

HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
        '(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    ),
    'Accept-Language': 'en-US,en;q=0.9'
}
MAX_PAGES = 5
TIMEOUT = 30

CITIES = [
    "Bangalore",
    "Pune",
    "Mumbai",
    "New Delhi",
    "Chennai",
    "Hyderabad"
]

FIELDNAMES = [
    'bhk',
    'area',
    'furnishing',
    'car_parking',
    'bathroom',
    'price',
    'address'
]

def get_page(url, page_num=1):
    for attempt in range(3):
        try:
            params = {'page': page_num} if page_num > 1 else {}
            response = requests.get(url, headers=HEADERS, params=params, timeout=TIMEOUT)
            response.raise_for_status()
            text = response.text.lower()
            if "captcha" in text or "access denied" in text:
                print(f"Blocking detected (attempt {attempt + 1}/3). Retrying...")
                time.sleep(random.uniform(10, 15))
                continue
            return response.text
        except requests.exceptions.RequestException as e:
            print(f"Attempt {attempt + 1}/3 failed: {e}")
            time.sleep(random.uniform(5, 10))
    return None

def safe_extract(element, selector=None, attribute=None, default=None):
    try:
        if selector:
            found = element.select_one(selector)
            if not found:
                return default
            if attribute:
                return found.get(attribute, default)
            return found.get_text(strip=True)
        return element.get_text(strip=True) if element else default
    except Exception:
        return default

def parse_price(price_str):
    if not price_str:
        return None

    price_str = price_str.replace("₹", "").replace(",", "").strip()

    if "Cr" in price_str:
        number = re.search(r'([\d.]+)', price_str)
        if number:
            return int(float(number.group(1)) * 1e7)

    if "Lac" in price_str:
        number = re.search(r'([\d.]+)', price_str)
        if number:
            return int(float(number.group(1)) * 1e5)

    number = re.search(r'([\d.]+)', price_str)
    if number:
        return int(float(number.group(1)))

    return None

def extract_bhk_and_city(title):
    bhk = None
    city = None
    
    # Extract BHK
    bhk_match = re.search(r'(\d+)\s*BHK', title, re.IGNORECASE)
    if bhk_match:
        bhk = bhk_match.group(1).strip()
    
    # Extract city name from title
    for city_name in CITIES:
        # Look for city name in the title
        city_pattern = r'\b' + re.escape(city_name) + r'\b'
        if re.search(city_pattern, title, re.IGNORECASE):
            city = city_name
            break
    
    # If city not found in title, try to find it in the full address context
    if not city:
        addr_match = re.search(r'\b(?:in|at)\s+(.+)', title, re.IGNORECASE)
        if addr_match:
            full_address = addr_match.group(1).strip()
            for city_name in CITIES:
                if city_name.lower() in full_address.lower():
                    city = city_name
                    break
    
    return bhk, city

def extract_city_from_card(card):
    """Extract only the city name from various possible sources"""
    
    # List of possible selectors that might contain location/address
    location_selectors = [
        '.mb-srp__card__location',
        '.mb-srp__card__address',
        '.mb-srp__card--title'
    ]
    
    for selector in location_selectors:
        element = card.select_one(selector)
        if element:
            text = element.get_text(strip=True)
            
            # Check for city names in the text
            for city in CITIES:
                if city.lower() in text.lower():
                    return city
    
    # Try summary items
    summary_items = card.select('.mb-srp__card__summary__item')
    for item in summary_items:
        label = item.select_one('.mb-srp__card__summary__key')
        if label and ('location' in label.get_text(strip=True).lower() or 
                     'address' in label.get_text(strip=True).lower()):
            value = item.select_one('.mb-srp__card__summary__value')
            if value:
                text = value.get_text(strip=True)
                for city in CITIES:
                    if city.lower() in text.lower():
                        return city
    
    return None

def parse_listing(card):
    data = {}
    
    # First try to get title for BHK and city
    title_text = safe_extract(card, '.mb-srp__card--title')
    bhk, city_from_title = extract_bhk_and_city(title_text)
    if bhk:
        data['bhk'] = bhk
    
    # Try to get city from other elements on the card
    city = extract_city_from_card(card)
    
    # Use city from title if not found elsewhere
    if not city and city_from_title:
        city = city_from_title
    
    # Set the address field to just the city name
    if city:
        data['address'] = city
    else:
        # If no city found, try to extract from URL or set default
        data['address'] = "Unknown"
    
    # Price extraction
    price_text = safe_extract(card, '.mb-srp__card__price--amount')
    if price_text:
        numeric_price = parse_price(price_text)
        if numeric_price:
            data['price'] = numeric_price
    
    # Area
    area = safe_extract(card, 'div[data-summary="carpet-area"] .mb-srp__card__summary--value')
    if not area:
        area = safe_extract(card, 'div[data-summary="super-area"] .mb-srp__card__summary--value')
    if area:
        # Extract only the number from area (remove sqft, sq ft, etc.)
        area_match = re.search(r'(\d+(?:\.\d+)?)', area)
        if area_match:
            data['area'] = area_match.group(1)
        else:
            data['area'] = area.replace('sqft', '').replace('sq ft', '').strip()
    
    # Furnishing
    furnishing = safe_extract(card, 'div[data-summary="furnishing"] .mb-srp__card__summary--value')
    if furnishing:
        data['furnishing'] = furnishing
    
    # Car Parking
    car_parking = safe_extract(card, 'div[data-summary="parking"] .mb-srp__card__summary--value')
    if car_parking:
        car_parking = car_parking.replace('Covered', '').replace('Open', '').replace(',', '').strip()
        if car_parking:
            data['car_parking'] = car_parking
    
    # Bathroom
    bathroom = safe_extract(card, 'div[data-summary="bathroom"] .mb-srp__card__summary--value')
    if bathroom:
        data['bathroom'] = bathroom
    
    return {k: v for k, v in data.items() if v}

def scrape_magicbricks(city):
    all_listings = []

    BASE_URL = (
        "https://www.magicbricks.com/property-for-sale/residential-real-estate"
        "?proptype=Multistorey-Apartment,Builder-Floor-Apartment,Penthouse,"
        "Studio-Apartment,Residential-House,Villa"
        f"&cityName={city}"
    )

    for page_num in range(1, MAX_PAGES + 1):
        print(f"\nScraping {city} - page {page_num}...")
        html = get_page(BASE_URL, page_num)
        if not html:
            print(f"Failed to get page {page_num} for {city}")
            continue

        soup = BeautifulSoup(html, 'html.parser')
        cards = soup.select('.mb-srp__card')

        if not cards:
            print(f"No listings found for {city} on page {page_num}.")
            break

        page_count = 0
        for card in cards:
            try:
                listing = parse_listing(card)
                if listing:
                    # Ensure the address is set to the city we're scraping
                    listing['address'] = city
                    all_listings.append(listing)
                    page_count += 1
            except Exception as e:
                print(f"Error parsing listing: {e}")
                continue

        print(f"{city} - Page {page_num}: Found {page_count} listings.")
        
        # Be respectful to the server
        time.sleep(random.uniform(5, 8))

    return all_listings

def save_to_csv(data, filename='magicbricks.csv'):
    if not data:
        print("No data to save.")
        return

    file_exists = os.path.isfile(filename)

    try:
        with open(filename, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            if not file_exists:
                writer.writeheader()

            writer.writerows(data)
        print(f"\nAppended {len(data)} listings to {filename}")
    except Exception as e:
        print(f"Error saving CSV: {e}")

def print_sample_data(data, num_samples=5):
    """Print sample data to verify quality"""
    if not data:
        print("No data to preview.")
        return
    
    print("\n" + "="*80)
    print(f"SAMPLE DATA (first {min(num_samples, len(data))} listings):")
    print("="*80)
    
    for i, listing in enumerate(data[:num_samples]):
        print(f"\nListing {i+1}:")
        for key, value in listing.items():
            print(f"  {key}: {value}")
    print("="*80 + "\n")

if __name__ == "__main__":
    print("Starting MagicBricks multi-city scraper...")
    print(f"Target cities: {', '.join(CITIES)}")
    print(f"Max pages per city: {MAX_PAGES}")
    start_time = time.time()
    
    # Remove old file if exists
    if os.path.exists("magicbricks.csv"):
        os.remove("magicbricks.csv")
        print("Deleted old magicbricks.csv")
    
    total_listings = 0
    all_scraped_data = []

    for city in CITIES:
        print(f"\n{'='*60}")
        print(f"Scraping city: {city}")
        print(f"{'='*60}")
        
        listings = scrape_magicbricks(city)
        
        if listings:
            all_scraped_data.extend(listings)
            save_to_csv(listings)
            total_listings += len(listings)
            print(f"Successfully scraped {len(listings)} listings from {city}")
        else:
            print(f"No listings found for {city}")
        
        # Add a longer delay between cities
        if city != CITIES[-1]:  # Don't sleep after the last city
            print(f"Waiting 10 seconds before next city...")
            time.sleep(10)
    
    # Print summary
    print(f"\n{'='*60}")
    print("SCRAPING COMPLETE")
    print(f"{'='*60}")
    print(f"Total listings scraped: {total_listings}")
    print(f"Total execution time: {time.time() - start_time:.2f} seconds")
    print(f"Data saved to: magicbricks.csv")
    
    # Print sample data for verification
    if all_scraped_data:
        print_sample_data(all_scraped_data, min(5, len(all_scraped_data)))
        
        # Show unique addresses to verify
        unique_addresses = set([listing.get('address', 'Unknown') for listing in all_scraped_data])
        print(f"\nUnique cities in data: {', '.join(sorted(unique_addresses))}")
    else:
        print("\nNo data was scraped. Please check:")
        print("1. Internet connection")
        print("2. Website accessibility")
        print("3. CSS selectors (they might have changed)")