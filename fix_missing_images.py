import os
import json
import time
import re
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def scan_json_for_missing_images(data_dir="data"):
    """
    Scan all JSON files in the data directory for cards with missing images.
    
    Args:
        data_dir: Directory containing JSON files
        
    Returns:
        Dictionary mapping Pokémon names to lists of cards with missing images
    """
    missing_images = {}
    
    if not os.path.exists(data_dir):
        print(f"Data directory {data_dir} does not exist.")
        return missing_images
    
    # Get all JSON files in the data directory
    json_files = [f for f in os.listdir(data_dir) if f.endswith('.json')]
    
    for json_file in json_files:
        pokemon_name = os.path.splitext(json_file)[0]  # Get Pokemon name from filename
        file_path = os.path.join(data_dir, json_file)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Check for cards with missing images
            cards_missing_images = []
            for card in data.get('data', []):
                if (not card.get('images', {}).get('small') or 
                    card.get('images', {}).get('small') == ""):
                    # Add the card to our list of cards with missing images
                    cards_missing_images.append(card)
            
            if cards_missing_images:
                print(f"Found {len(cards_missing_images)} cards with missing images in {json_file}")
                missing_images[pokemon_name] = {
                    'file_path': file_path,
                    'cards': cards_missing_images,
                    'all_data': data  # Keep reference to full data for updating later
                }
            else:
                print(f"No missing images in {json_file}")
        
        except Exception as e:
            print(f"Error processing {json_file}: {str(e)}")
    
    return missing_images

def download_missing_images(missing_images_data, headless=False):
    """
    Download missing images for cards.
    
    Args:
        missing_images_data: Dictionary mapping Pokemon names to lists of cards with missing images
        headless: Whether to run in headless mode (default: False)
        
    Returns:
        Number of successfully downloaded images
    """
    if not missing_images_data:
        print("No missing images to download.")
        return 0
    
    # Set up Chrome driver
    chrome_options = Options()
    if headless:
        chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    
    driver = None
    successful_downloads = 0
    
    try:
        print(f"Setting up Chrome driver for image downloads (visible mode)...")
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Visit cardmarket website first to set cookies/session
        driver.get("https://www.cardmarket.com/en/Pokemon")
        time.sleep(2)
        
        # Get cookies for requests session
        cookies = driver.get_cookies()
        session = requests.Session()
        for cookie in cookies:
            session.cookies.set(cookie['name'], cookie['value'])
        
        # Process each Pokemon
        for pokemon_name, pokemon_data in missing_images_data.items():
            file_path = pokemon_data['file_path']
            cards = pokemon_data['cards']
            all_data = pokemon_data['all_data']
            
            print(f"\nProcessing {len(cards)} cards with missing images for {pokemon_name}")
            
            # Create pokemon-specific subfolder if it doesn't exist
            pokemon_dir = os.path.join("images", pokemon_name.lower())
            if not os.path.exists(pokemon_dir):
                os.makedirs(pokemon_dir)
            
            # Track if we made any changes to this Pokemon's data
            changes_made = False
            
            # Process each card with missing image
            for card in cards:
                # Update original full data structure for this card
                # Find the corresponding card in all_data
                card_id = card.get('id')
                
                # Find the card in the original data structure
                original_card = None
                for data_card in all_data.get('data', []):
                    if data_card.get('id') == card_id:
                        original_card = data_card
                        break
                
                if not card.get('cardmarket', {}).get('url'):
                    print(f"Skipping card {card.get('id', 'unknown')} - no URL available")
                    continue
                
                print(f"\nAttempting to download image for {card.get('name', 'unknown')} (ID: {card.get('id', 'unknown')})")
                
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
                local_image_path = os.path.join("images", pokemon_name.lower(), filename)  # Path to use in JSON
                success = False
                
                # METHOD 1: Try direct request using the card's detail page URL
                try:
                    card_url = card.get('cardmarket', {}).get('url', '')
                    print(f"Method 1: Making request to card detail page: {card_url}")
                    
                    if card_url:
                        # Visit the card detail page
                        driver.get(card_url)
                        time.sleep(3)  # Wait for page to load
                        
                        # Update cookies after navigating
                        cookies = driver.get_cookies()
                        session = requests.Session()
                        for cookie in cookies:
                            session.cookies.set(cookie['name'], cookie['value'])
                        
                        # Try to find the image element
                        try:
                            img_elements = driver.find_elements(By.CSS_SELECTOR, "img.card-img")
                            if not img_elements:
                                img_elements = driver.find_elements(By.CSS_SELECTOR, "img.lazy[data-echo]")
                            if not img_elements:
                                img_elements = driver.find_elements(By.CSS_SELECTOR, ".card-image img")
                            
                            if img_elements:
                                print(f"Found {len(img_elements)} image elements")
                                for img in img_elements:
                                    if img.is_displayed():
                                        # Get image source
                                        img_src = img.get_attribute('src')
                                        if not img_src:
                                            img_src = img.get_attribute('data-echo')
                                        
                                        if img_src:
                                            print(f"Found image URL: {img_src}")
                                            # Download image using requests
                                            headers = {
                                                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                                                'Referer': card_url,
                                                'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8'
                                            }
                                            
                                            response = session.get(img_src, headers=headers, stream=True)
                                            
                                            if response.status_code == 200 and int(response.headers.get('Content-Length', 0)) > 1000:
                                                with open(local_path, 'wb') as f:
                                                    for chunk in response.iter_content(1024):
                                                        f.write(chunk)
                                                
                                                if os.path.exists(local_path) and os.path.getsize(local_path) > 5000:
                                                    print(f"Successfully downloaded image to {local_path}")
                                                    # Update card with new image path
                                                    card['images']['small'] = local_image_path
                                                    # Update original card data as well
                                                    if original_card:
                                                        original_card['images']['small'] = local_image_path
                                                    success = True
                                                    successful_downloads += 1
                                                    changes_made = True
                                                    break
                                        else:
                                            print("Image source not found")
                            else:
                                print("No image elements found on page")
                        except Exception as e:
                            print(f"Error finding image element: {str(e)}")
                except Exception as e:
                    print(f"Method 1 error: {str(e)}")
                
                # METHOD 2: Try screenshots if direct download fails
                if not success:
                    try:
                        print("Method 2: Trying screenshot method...")
                        # Make sure we're on the card page
                        card_url = card.get('cardmarket', {}).get('url', '')
                        if card_url and driver.current_url != card_url:
                            driver.get(card_url)
                            time.sleep(3)
                        
                        # Try to find and screenshot just the image element
                        img_elements = driver.find_elements(By.CSS_SELECTOR, "img.card-img, img.lazy[data-echo], .card-image img")
                        
                        if img_elements:
                            for img in img_elements:
                                if img.is_displayed():
                                    # Scroll to the image
                                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", img)
                                    time.sleep(1)
                                    
                                    # Take screenshot of the image element
                                    try:
                                        img.screenshot(local_path)
                                        if os.path.exists(local_path) and os.path.getsize(local_path) > 5000:
                                            print(f"Screenshot method succeeded: {local_path}")
                                            # Update card with new image path
                                            card['images']['small'] = local_image_path
                                            # Update original card data as well
                                            if original_card:
                                                original_card['images']['small'] = local_image_path
                                            success = True
                                            successful_downloads += 1
                                            changes_made = True
                                            break
                                    except Exception as e:
                                        print(f"Error taking screenshot: {str(e)}")
                        else:
                            # Try taking a screenshot of the page area likely to contain the card
                            print("No image elements found, trying to take full page screenshot...")
                            driver.save_screenshot(local_path)
                            if os.path.exists(local_path) and os.path.getsize(local_path) > 10000:
                                print(f"Full page screenshot saved to {local_path}")
                                # Update card with new image path
                                card['images']['small'] = local_image_path
                                # Update original card data as well
                                if original_card:
                                    original_card['images']['small'] = local_image_path
                                success = True
                                successful_downloads += 1
                                changes_made = True
                    except Exception as e:
                        print(f"Method 2 error: {str(e)}")
            
            # If we made changes to this Pokemon's data, save the updated file
            if changes_made:
                try:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(all_data, f, indent=4)
                    print(f"Updated {file_path} with new image paths")
                except Exception as e:
                    print(f"Error saving updated data to {file_path}: {str(e)}")
    
    finally:
        if driver:
            driver.quit()
    
    return successful_downloads

def main():
    """
    Main function to find and download missing images for Pokemon cards.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Fix missing Pokemon card images in JSON files')
    parser.add_argument('--data-dir', default='data', help='Directory containing JSON files')
    parser.add_argument('--headless', action='store_true', help='Run in headless mode (invisible browser)')
    parser.add_argument('--pokemon', help='Process only a specific Pokemon (by name)')
    
    args = parser.parse_args()
    
    print(f"Scanning for JSON files with missing images in {args.data_dir}...")
    missing_images = scan_json_for_missing_images(args.data_dir)
    
    # Filter by specific Pokemon if requested
    if args.pokemon and args.pokemon.lower() in missing_images:
        print(f"Filtering to process only {args.pokemon}")
        missing_images = {args.pokemon.lower(): missing_images[args.pokemon.lower()]}
    
    total_missing = sum(len(data['cards']) for data in missing_images.values())
    print(f"\nFound {total_missing} cards with missing images across {len(missing_images)} Pokemon")
    
    if total_missing > 0:
        successful = download_missing_images(missing_images, args.headless)
        print(f"\nDownloaded {successful} out of {total_missing} missing images")
    else:
        print("No missing images to download")

if __name__ == "__main__":
    main()