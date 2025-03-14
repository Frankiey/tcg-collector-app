import os
import time
import random
import logging
from datetime import datetime
from pokemon_scraper import scrape_pokemon_by_name

# Configure logging
log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file = os.path.join(log_dir, f"batch_scraper_{timestamp}.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

def batch_scrape_pokemon(pokemon_list, delay_min=5, delay_max=15):
    """
    Scrape multiple Pokemon from a list with random delays between requests.
    
    Args:
        pokemon_list: List of Pokemon names to scrape
        delay_min: Minimum delay in seconds between requests
        delay_max: Maximum delay in seconds between requests
    """
    logging.info(f"Starting batch scraping for {len(pokemon_list)} Pokemon")
    
    # Create data directory if it doesn't exist
    data_dir = "data"
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    
    successful = 0
    failed = 0
    
    for i, pokemon_name in enumerate(pokemon_list):
        logging.info(f"Processing {i+1}/{len(pokemon_list)}: {pokemon_name}")
        
        try:
            # Check if the file already exists
            output_file = os.path.join(data_dir, f"{pokemon_name.lower()}.json")
            if os.path.exists(output_file):
                logging.info(f"File for {pokemon_name} already exists, skipping...")
                successful += 1
                continue
            
            # Scrape the Pokemon
            result = scrape_pokemon_by_name(pokemon_name, save_to_file=True)
            
            if result:
                logging.info(f"Successfully scraped {pokemon_name}")
                successful += 1
            else:
                logging.error(f"Failed to scrape {pokemon_name}")
                failed += 1
        
        except Exception as e:
            logging.exception(f"Error processing {pokemon_name}: {str(e)}")
            failed += 1
        
        # Don't wait after the last item
        if i < len(pokemon_list) - 1:
            # Random delay to avoid pattern detection
            delay = random.uniform(delay_min, delay_max)
            logging.info(f"Waiting {delay:.2f} seconds before next request...")
            time.sleep(delay)
    
    logging.info(f"Batch scraping completed. Success: {successful}, Failed: {failed}")
    return successful, failed

if __name__ == "__main__":
    # List of Pokemon to scrape
    pokemon_list = [
        'Charizard', 'Charmander', 'Cubone', 'Psyduck', 'Pikachu',
        'Golem', 'Gastly', 'Haunter', 'Gengar', 'Mew', 'Mewtwo',
        'Machop', 'Machoke', 'Machamp', 'Farfetchd'
    ]
    # 'Farfetch\'d' gives an error, need to check why
    batch_scrape_pokemon(pokemon_list)