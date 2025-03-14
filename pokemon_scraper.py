import re
import time
import json
import os
import requests
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

def get_pokemon_page_selenium(pokemon_name, headless=False):
    """
    Navigate to the Cardmarket page for a specific Pokemon using Selenium.
    
    Args:
        pokemon_name: Name of the Pokemon (e.g., "Psyduck", "Charizard")
        headless: Whether to run in headless mode (default: False)
        
    Returns:
        HTML content of the page or None if an error occurs
    """
    base_url = "https://www.cardmarket.com/en/Pokemon/Species/"
    url = f"{base_url}{pokemon_name}"
    
    # Set up Chrome options
    chrome_options = Options()
    if headless:
        chrome_options.add_argument("--headless")  # Run in headless mode only if specified
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    
    try:
        print(f"Setting up Chrome driver (visible mode)...")
        # Use webdriver_manager to handle driver installation
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        print(f"Navigating to {url}")
        driver.get(url)
        
        # Wait for page to load (adjust timeout as needed)
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CLASS_NAME, "d-flex.col-12.col-sm-6.col-md-4.col-lg-3.mb-4"))
        )
        
        # Allow time for lazy-loaded images to load
        print("Waiting for content to load...")
        time.sleep(5)
        
        # Get page source after JavaScript has loaded content
        html_content = driver.page_source
        
        driver.quit()
        return html_content
    
    except Exception as e:
        print(f"Error fetching the page with Selenium: {str(e)}")
        if 'driver' in locals():
            driver.quit()
        return None

def scrape_pokemon_cards(html_content, pokemon_name=None):
    """
    Scrape Pokemon card data from Cardmarket HTML content.
    If pokemon_name is provided, it will filter for cards of that Pokemon.
    """
    if not html_content:
        return []
        
    soup = BeautifulSoup(html_content, 'html.parser')
    cards = []
    
    # Find all card divs
    card_divs = soup.find_all('div', class_='d-flex col-12 col-sm-6 col-md-4 col-lg-3 mb-4')
    
    print(f"Found {len(card_divs)} card listings")
    
    for card_div in card_divs:
        try:
            card = {}
            
            # Get card link and extract ID
            card_link = card_div.find('a')
            if card_link and 'href' in card_link.attrs:
                url = card_link['href']
                card['url'] = f"https://www.cardmarket.com{url}"
                
                # Try to extract ID from URL
                url_parts = url.split('/')
                if len(url_parts) >= 2:
                    set_code = url_parts[-2]
                    card_number = url_parts[-1]
                    if set_code and card_number:
                        card['id'] = f"{set_code.lower()}-{card_number}"
            
            # Get card name
            name_elem = card_div.find('h2', class_='card-title')
            if name_elem:
                card['name'] = name_elem.text.strip()
                
                # Filter by Pokemon name if provided
                if pokemon_name and pokemon_name.lower() not in card['name'].lower():
                    continue
            
            # Get set information
            set_info = {}
            set_name_elem = card_div.find('span', class_='expansion-name')
            if set_name_elem:
                set_name = set_name_elem.text.strip()
                set_info['name'] = set_name
                # Generate an ID from the set name
                set_info['id'] = re.sub(r'[^a-zA-Z0-9]', '', set_name).lower()
            
            # Add set details to card
            if set_info:
                card['set'] = set_info
            
            # Get card number
            number_containers = card_div.find_all('div', class_='d-flex has-content-centered')
            if len(number_containers) > 1:
                number_text = number_containers[1].text
                number_match = re.search(r'Number\s*(.+)', number_text)
                if number_match:
                    card['number'] = number_match.group(1).strip()
            
            # Get rarity
            rarity_svg = card_div.find('svg', {'data-bs-toggle': 'tooltip'})
            if rarity_svg and 'title' in rarity_svg.attrs:
                card['rarity'] = rarity_svg['title']
            
            # Get availability
            card_texts = card_div.find_all('p', class_='card-text text-muted mb-0')
            if card_texts and len(card_texts) > 0:
                avail_span = card_texts[0].find('span', class_='fw-bold')
                if avail_span:
                    try:
                        card['available'] = int(avail_span.text.strip())
                    except ValueError:
                        card['available'] = avail_span.text.strip()
            
            # Get price
            if card_texts and len(card_texts) > 1:
                price_span = card_texts[1].find('b')
                if price_span:
                    price_text = price_span.text.strip()
                    try:
                        price = price_text.replace(',', '.').replace('€', '').strip()
                        if price.lower() != 'n/a':
                            card['price'] = float(price)
                    except ValueError:
                        card['price'] = None  # Set to None if conversion fails
            
            # Get image URL (store original URL temporarily)
            img_elem = card_div.find('img', class_='lazy')
            if img_elem and 'data-echo' in img_elem.attrs:
                small_image = img_elem['data-echo']
                # We'll store the URL temporarily and replace it with local path later
                card['images'] = {
                    "small": small_image,
                    "original_url": small_image  # Keep original URL for reference during download
                }
            
            cards.append(card)
        except Exception as e:
            print(f"Error processing card: {str(e)}")
    
    return cards

def download_card_images(cards, pokemon_name, headless=False):
    """
    Download the card images using a new Chrome session.
    
    Args:
        cards: List of card dictionaries with image URLs
        pokemon_name: Name of the Pokemon for folder structure
        headless: Whether to run in headless mode (default: False)
        
    Returns:
        Updated list of cards with local image paths in 'small' field
    """
    # Create image directory if it doesn't exist
    image_dir = "images"
    if not os.path.exists(image_dir):
        os.makedirs(image_dir)
        
    # Create pokemon-specific subfolder
    pokemon_dir = os.path.join(image_dir, pokemon_name.lower())
    if not os.path.exists(pokemon_dir):
        os.makedirs(pokemon_dir)
    
    # Set up a new Chrome driver
    chrome_options = Options()
    if headless:
        chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    
    driver = None
    try:
        print(f"Setting up Chrome driver for image downloads (visible mode)...")
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Visit cardmarket website first to set cookies/session
        driver.get("https://www.cardmarket.com/en/Pokemon")
        time.sleep(2)
        
        for i, card in enumerate(cards):
            if 'images' in card and 'original_url' in card['images']:
                try:
                    image_url = card['images']['original_url']
                    
                    # Create a filename based on the card ID or name
                    if 'id' in card and card['id']:
                        filename = f"{card['id']}.jpg"
                    elif 'name' in card:
                        # Clean the name to be used as a filename
                        filename = re.sub(r'[^a-zA-Z0-9]', '_', card['name']) + ".jpg"
                    else:
                        # Use a timestamp if no ID or name is available
                        filename = f"card_{int(time.time())}.jpg"
                    
                    local_path = os.path.join(pokemon_dir, filename)
                    
                    # Log the download attempt
                    print(f"Downloading image for {card.get('name', 'unknown card')}")
                    
                    # METHOD 1: Try direct download with Selenium session cookies
                    cookies = driver.get_cookies()
                    s = requests.Session()
                    
                    # Add all the browser's cookies to our requests session
                    for cookie in cookies:
                        s.cookies.set(cookie['name'], cookie['value'])
                    
                    # Set headers to mimic the browser
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                        'Referer': 'https://www.cardmarket.com/en/Pokemon',
                        'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
                        'Accept-Language': 'en-US,en;q=0.9',
                        'Accept-Encoding': 'gzip, deflate, br',
                        'Connection': 'keep-alive',
                        'Cache-Control': 'max-age=0',
                    }
                    
                    response = s.get(image_url, headers=headers, stream=True)
                    
                    if response.status_code == 200 and int(response.headers.get('Content-Length', 0)) > 1000:
                        with open(local_path, 'wb') as f:
                            for chunk in response.iter_content(1024):
                                f.write(chunk)
                        print(f"Successfully downloaded image to {local_path}")
                        # Replace URL with local path
                        card['images']['small'] = local_path
                        continue
                    else:
                        print(f"Method 1 failed: status code {response.status_code} or small file size")
                
                    # METHOD 2: Try navigating to the card detail page and capturing the image directly
                    if 'url' in card:
                        try:
                            driver.get(card['url'])
                            time.sleep(2)  # Wait for page to load
                            
                            # Try to find the image element
                            img_elements = driver.find_elements(By.CSS_SELECTOR, "img.lazy[data-echo]")
                            if img_elements:
                                for img in img_elements:
                                    if img.is_displayed():
                                        # Scroll to make sure the image is in view
                                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", img)
                                        time.sleep(1)  # Wait for image to be fully loaded
                                        
                                        # Take a screenshot of just the image element
                                        img.screenshot(local_path)
                                        
                                        # Verify the image was saved successfully
                                        if os.path.exists(local_path) and os.path.getsize(local_path) > 5000:
                                            print(f"Method 2 succeeded: Captured image from card page to {local_path}")
                                            # Replace URL with local path
                                            card['images']['small'] = local_path
                                            break
                        except Exception as e:
                            print(f"Method 2 error: {str(e)}")
                    
                    # METHOD 3: If still not successful, try to go directly to the image URL
                    if card['images']['small'] == image_url:  # If it's still the original URL
                        try:
                            driver.get(image_url)
                            time.sleep(2)
                            
                            # Take a screenshot of the entire page (which should be just the image)
                            driver.save_screenshot(local_path)
                            
                            # Verify the screenshot
                            if os.path.exists(local_path) and os.path.getsize(local_path) > 10000:
                                print(f"Method 3 succeeded: Screenshot saved to {local_path}")
                                # Replace URL with local path
                                card['images']['small'] = local_path
                        except Exception as e:
                            print(f"Method 3 error: {str(e)}")
                    
                except Exception as e:
                    print(f"Error downloading image: {str(e)}")
                
                # Clean up the original_url field as we don't need it in the final JSON
                if 'original_url' in card['images']:
                    del card['images']['original_url']
        
        # Return the updated cards list with local paths
        return cards
    
    finally:
        if driver:
            driver.quit()

def create_target_json(cards):
    today = datetime.now().strftime("%Y/%m/%d")
    
    transformed_cards = []
    for card in cards:
        # Skip cards with missing critical information
        if not card.get('name') or not card.get('id'):
            continue
        
        # Handle price data - ensure it's a float for calculations
        price = None
        if 'price' in card:
            try:
                if isinstance(card['price'], (int, float)):
                    price = float(card['price'])
                elif isinstance(card['price'], str):
                    # Try to convert string price to float
                    price_str = card['price'].replace(',', '.').replace('€', '').strip()
                    price = float(price_str)
            except (ValueError, TypeError):
                # If conversion fails, leave price as None
                pass
            
        # Prepare images object - the small field now contains the local path
        # and we leave the large field empty as requested
        images = {
            "small": card.get('images', {}).get('small', ""),
            "large": ""  # Empty string as requested
        }
        
        card_data = {
            "id": card.get('id', ''),
            "name": card.get('name', ''),
            "supertype": "Pokémon",
            "subtypes": [],
            "hp": "",
            "types": [],
            "evolvesTo": [],
            "attacks": [],
            "weaknesses": [],
            "retreatCost": [],
            "convertedRetreatCost": 0,
            "set": {
                "id": card.get('set', {}).get('id', ''),
                "name": card.get('set', {}).get('name', ''),
                "series": "",
                "printedTotal": 0,
                "total": 0,
                "legalities": {
                    "unlimited": "Legal"
                },
                "releaseDate": "",
                "updatedAt": today,
                "images": {
                    "symbol": "",
                    "logo": ""
                }
            },
            "number": card.get('number', ''),
            "artist": "",
            "rarity": card.get('rarity', ''),
            "flavorText": "",
            "nationalPokedexNumbers": [],
            "legalities": {
                "unlimited": "Legal"
            },
            "images": images,
            "cardmarket": {
                "url": card.get('url', ''),
                "updatedAt": today,
                "prices": {
                    "averageSellPrice": price * 1.1 if price is not None else None,
                    "lowPrice": price if price is not None else None,
                    "trendPrice": price * 1.2 if price is not None else None,
                    "germanProLow": 0.0,
                    "suggestedPrice": 0.0,
                    "reverseHoloSell": 0.0,
                    "reverseHoloLow": 0.0,
                    "reverseHoloTrend": 0.0,
                    "lowPriceExPlus": price if price is not None else None,
                    "avg1": 0.0,
                    "avg7": 0.0,
                    "avg30": 0.0,
                    "reverseHoloAvg1": 0.0,
                    "reverseHoloAvg7": 0.0,
                    "reverseHoloAvg30": 0.0
                }
            }
        }
        transformed_cards.append(card_data)
    
    result = {
        "data": transformed_cards,
        "page": 1,
        "pageSize": len(transformed_cards),
        "count": len(transformed_cards),
        "totalCount": len(transformed_cards)
    }
    
    return result

def scrape_pokemon_by_name(pokemon_name, save_to_file=True, headless=False):
    """
    Main function to scrape cards for a specific Pokemon.
    
    Args:
        pokemon_name: Name of the Pokemon (e.g., "Psyduck", "Charizard")
        save_to_file: Whether to save results to a JSON file
        headless: Whether to run in headless mode (default: False)
        
    Returns:
        JSON string with formatted card data
    """
    html_content = get_pokemon_page_selenium(pokemon_name, headless)
    
    if not html_content:
        print(f"Failed to get HTML content for {pokemon_name}")
        return None
    
    print(f"Processing {pokemon_name} cards...")
    cards = scrape_pokemon_cards(html_content)
    
    # Download card images
    print(f"Downloading images for {pokemon_name} cards...")
    cards_with_images = download_card_images(cards, pokemon_name, headless)
    
    result = create_target_json(cards_with_images)
    json_result = json.dumps(result, indent=4)
    
    if save_to_file:
        # Create data directory if it doesn't exist
        data_dir = "data"
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
            
        # Create simpler filename without suffix
        filename = os.path.join(data_dir, f"{pokemon_name.lower()}.json")
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(json_result)
        print(f"Results saved to {filename}")
    
    return json_result

def main():
    """
    Command-line interface for the script.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Scrape Pokemon card data from Cardmarket')
    parser.add_argument('pokemon', help='Name of the Pokemon to scrape (e.g., "Psyduck", "Charizard")')
    parser.add_argument('--no-save', action='store_true', help='Do not save results to a file')
    parser.add_argument('--headless', action='store_true', help='Run in headless mode (invisible browser)')
    
    args = parser.parse_args()
    
    result = scrape_pokemon_by_name(args.pokemon, not args.no_save, args.headless)
    if result and args.no_save:
        print(result)

if __name__ == "__main__":
    main()