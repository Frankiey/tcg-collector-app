#!/usr/bin/env python3
import os
import json
import sys
import requests
import time
import random
import signal
import shutil
from pathlib import Path
from urllib.parse import urlparse
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('image_download.log')
    ]
)
logger = logging.getLogger('pokemon_image_downloader')

# Global flag for graceful shutdown
SHUTDOWN_REQUESTED = False

def signal_handler(sig, frame):
    """Handle Ctrl+C and other termination signals gracefully"""
    global SHUTDOWN_REQUESTED
    logger.info("Shutdown requested. Completing current file and exiting...")
    SHUTDOWN_REQUESTED = True

# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def download_pokemon_images(
    data_dir='./data', 
    image_dir='./images', 
    update_json=True,
    min_delay=2.0,
    max_delay=5.0,
    max_retries=3,
    batch_size=10,
    batch_break=30,
    skip_problem_files=True,
    use_placeholder=True,
    placeholder_path=None
):
    """
    Scans JSON files in data_dir, downloads images, and updates JSON file links.
    
    Args:
        data_dir: Directory containing Pokémon JSON files
        image_dir: Base directory to save images
        update_json: Whether to update the JSON files with local paths
        min_delay, max_delay: Delay range between requests (seconds)
        max_retries: Maximum number of retry attempts for failed downloads
        batch_size: Number of files to process before taking a break
        batch_break: Seconds to wait between batches
        skip_problem_files: Whether to skip files that consistently cause errors
        use_placeholder: Use a placeholder image for failed downloads
        placeholder_path: Path to a placeholder image (will create one if None)
    """
    global SHUTDOWN_REQUESTED
    
    # Create the data directory path object
    data_path = Path(data_dir)
    
    if not data_path.exists() or not data_path.is_dir():
        logger.error(f"Error: '{data_dir}' is not a valid directory")
        sys.exit(1)
    
    # Create image directories if they don't exist
    small_image_dir = Path(image_dir) / 'small'
    small_image_dir.mkdir(parents=True, exist_ok=True)
    
    # Create or validate placeholder image
    if use_placeholder:
        if placeholder_path and Path(placeholder_path).exists():
            placeholder_file = Path(placeholder_path)
        else:
            # Create a simple 1x1 pixel placeholder image
            placeholder_file = small_image_dir / "_placeholder.jpg"
            if not placeholder_file.exists():
                logger.info("Creating a placeholder image for failed downloads")
                try:
                    # 1x1 transparent pixel as JPEG
                    with open(placeholder_file, 'wb') as f:
                        f.write(b'\xff\xd8\xff\xe0\x00\x10\x4a\x46\x49\x46\x00\x01\x01\x01\x00\x48\x00\x48\x00\x00\xff\xdb\x00\x43\x00\x03\x02\x02\x03\x02\x02\x03\x03\x03\x03\x04\x03\x03\x04\x05\x08\x05\x05\x04\x04\x05\x0a\x07\x07\x06\x08\x0c\x0a\x0c\x0c\x0b\x0a\x0b\x0b\x0d\x0e\x12\x10\x0d\x0e\x11\x0e\x0b\x0b\x10\x16\x10\x11\x13\x14\x15\x15\x15\x0c\x0f\x17\x18\x16\x14\x18\x12\x14\x15\x14\xff\xdb\x00\x43\x01\x03\x04\x04\x05\x04\x05\x09\x05\x05\x09\x14\x0d\x0b\x0d\x14\x14\x14\x14\x14\x14\x14\x14\x14\x14\x14\x14\x14\x14\x14\x14\x14\x14\x14\x14\x14\x14\x14\x14\x14\x14\x14\x14\x14\x14\x14\x14\x14\x14\x14\x14\x14\x14\x14\x14\x14\x14\x14\x14\x14\x14\x14\x14\x14\x14\xff\xc2\x00\x11\x08\x00\x01\x00\x01\x03\x01\x11\x00\x02\x11\x01\x03\x11\x01\xff\xc4\x00\x15\x00\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\xff\xc4\x00\x14\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xda\x00\x0c\x03\x01\x00\x02\x10\x03\x10\x00\x00\x01\x95\x00\xff\xc4\x00\x14\x10\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xda\x00\x08\x01\x01\x00\x01\x05\x02\x7f\xff\xc4\x00\x14\x11\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xda\x00\x08\x01\x03\x01\x01\x3f\x01\x7f\xff\xc4\x00\x14\x11\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xda\x00\x08\x01\x02\x01\x01\x3f\x01\x7f\xff\xc4\x00\x14\x10\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xda\x00\x08\x01\x01\x00\x06\x3f\x02\x7f\xff\xc4\x00\x14\x10\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xda\x00\x08\x01\x01\x00\x01\x3f\x21\x7f\xff\xda\x00\x0c\x03\x01\x00\x02\x00\x03\x00\x00\x00\x10\xff\x00\xff\xc4\x00\x14\x11\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xda\x00\x08\x01\x03\x01\x01\x3f\x10\x7f\xff\xc4\x00\x14\x11\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xda\x00\x08\x01\x02\x01\x01\x3f\x10\x7f\xff\xc4\x00\x14\x10\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xda\x00\x08\x01\x01\x00\x01\x3f\x10\x7f\xff\xd9')
                except Exception as e:
                    logger.error(f"Error creating placeholder image: {e}")
                    use_placeholder = False
    
    # Create a file to track problematic URLs
    problem_urls_file = Path(image_dir) / 'problem_urls.txt'
    problem_urls = set()
    
    # Load previously identified problem URLs if file exists
    if skip_problem_files and problem_urls_file.exists():
        try:
            with open(problem_urls_file, 'r') as f:
                problem_urls = set(line.strip() for line in f if line.strip())
            logger.info(f"Loaded {len(problem_urls)} known problem URLs to skip")
        except Exception as e:
            logger.error(f"Error loading problem URLs file: {e}")
    
    # Get list of all JSON files
    json_files = list(data_path.glob('*.json'))
    
    if not json_files:
        logger.warning(f"Warning: No JSON files found in '{data_dir}'")
        sys.exit(1)
    
    logger.info(f"Found {len(json_files)} JSON files in '{data_dir}'")
    
    # Track statistics
    total_images = 0
    downloaded_images = 0
    failed_images = 0
    skipped_images = 0
    placeholder_used = 0
    
    # List of different user agents to rotate through
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36'
    ]
    
    # Process files in batches to avoid prolonged connection to Cloudflare
    for batch_index in range(0, len(json_files), batch_size):
        if SHUTDOWN_REQUESTED:
            logger.info("Shutdown requested. Saving progress and exiting...")
            break
            
        batch = json_files[batch_index:batch_index + batch_size]
        logger.info(f"Processing batch {batch_index // batch_size + 1} of {(len(json_files) + batch_size - 1) // batch_size}")
        
        # Process each JSON file in this batch
        for json_file in batch:
            if SHUTDOWN_REQUESTED:
                break
                
            pokemon_name = json_file.stem
            logger.info(f"\nProcessing {pokemon_name}.json...")
            
            try:
                # Load the JSON file
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Extract cards
                cards = data.get('data', [])
                if not isinstance(cards, list):
                    cards = [cards]  # Handle case where data isn't a list
                
                # Track if any changes were made to this file
                file_modified = False
                
                # Process each card
                card_count = len(cards)
                for card_index, card in enumerate(cards):
                    if SHUTDOWN_REQUESTED:
                        break
                        
                    if 'images' not in card:
                        continue
                    
                    # Only process small images - they're more likely to load
                    if 'small' not in card['images'] or not card['images']['small']:
                        continue
                    
                    img_url = card['images']['small']
                    total_images += 1
                    
                    # Skip if already a local path
                    if not img_url.startswith('http'):
                        skipped_images += 1
                        continue
                    
                    # Skip known problem URLs
                    if skip_problem_files and img_url in problem_urls:
                        logger.info(f"Skipping known problem URL: {img_url}")
                        
                        # If we're using placeholders, use one for this image
                        if use_placeholder and update_json:
                            rel_path = f"images/small/_placeholder.jpg"
                            if card['images']['small'] != rel_path:
                                card['images']['small'] = rel_path
                                file_modified = True
                            
                            # Also update large image to use placeholder
                            if 'large' in card['images'] and card['images']['large']:
                                if card['images']['large'] != rel_path:
                                    card['images']['large'] = rel_path
                                    file_modified = True
                            
                            placeholder_used += 1
                        
                        skipped_images += 1
                        continue
                    
                    # Parse URL to get filename
                    try:
                        parsed_url = urlparse(img_url)
                        filename = os.path.basename(parsed_url.path)
                        
                        # Use card ID for more reliable naming if available
                        if 'id' in card and card['id']:
                            # Create a safe filename by replacing problematic chars
                            safe_id = str(card['id']).replace('/', '-').replace('\\', '-').replace(' ', '_')
                            extension = os.path.splitext(filename)[1] or '.jpg'
                            filename = f"{safe_id}_small{extension}"
                    except Exception:
                        # Fallback filename generation if URL parsing fails
                        filename = f"card_{pokemon_name}_{card_index}_small.jpg"
                    
                    # Determine save path
                    save_path = small_image_dir / filename
                    
                    # Skip if image already exists and is not empty
                    if save_path.exists() and save_path.stat().st_size > 100:  # Ensure file isn't empty
                        logger.info(f"Skipping existing image: {filename}")
                        
                        # Update the JSON even if we skipped the download
                        if update_json:
                            # Use local path for small image
                            rel_path = f"images/small/{filename}"
                            if card['images']['small'] != rel_path:
                                card['images']['small'] = rel_path
                                file_modified = True
                            
                            # Also update large image to use small image
                            if 'large' in card['images'] and card['images']['large']:
                                if card['images']['large'] != rel_path:
                                    card['images']['large'] = rel_path  # Just use small image for both
                                    file_modified = True
                        
                        skipped_images += 1
                        continue
                    
                    # Delete empty image file if it exists
                    if save_path.exists() and save_path.stat().st_size <= 100:
                        try:
                            save_path.unlink()
                            logger.info(f"Deleted empty/corrupt image file: {filename}")
                        except Exception as e:
                            logger.error(f"Error deleting empty image file: {e}")
                    
                    # Download the image with retries
                    success = False
                    retry_count = 0
                    
                    while not success and retry_count <= max_retries:
                        if SHUTDOWN_REQUESTED:
                            break
                            
                        try:
                            if retry_count > 0:
                                logger.info(f"Retry attempt {retry_count} for {img_url}")
                            else:
                                logger.info(f"Downloading image ({card_index+1}/{card_count}): {filename}")
                            
                            # Create a new session with random user agent each time
                            session = requests.Session()
                            session.headers.update({
                                'User-Agent': random.choice(user_agents),
                                'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
                                'Accept-Language': 'en-US,en;q=0.9',
                                'Referer': 'https://www.cardmarket.com/',
                                'Connection': 'keep-alive'
                            })
                            
                            # Add a delay with exponential backoff
                            delay = random.uniform(min_delay, max_delay) * (1.5 ** retry_count)
                            logger.info(f"Waiting {delay:.2f} seconds...")
                            time.sleep(delay)
                            
                            # Make the request with a timeout
                            try:
                                response = session.get(img_url, stream=True, timeout=15)
                                response.raise_for_status()
                            except requests.RequestException as e:
                                error_msg = str(e)
                                if "429" in error_msg or "403" in error_msg:
                                    logger.error(f"Rate limited or blocked by Cloudflare: {error_msg}")
                                    # Add an extra long delay due to rate limiting detection
                                    time.sleep(random.uniform(10, 20) * (2 ** retry_count))
                                raise
                            
                            # Check for valid image MIME type
                            content_type = response.headers.get('content-type', '')
                            if not content_type.startswith('image/'):
                                if content_type == "multerS3.AUTO_CONTENT_TYPE":
                                    raise ValueError(f"Amazon S3 returned a placeholder instead of an image (URL may be invalid): {content_type}")
                                else:
                                    raise ValueError(f"Received non-image content type: {content_type}")
                            
                            # Check if the response body is too small (likely an error page)
                            content_length = int(response.headers.get('content-length', '0'))
                            if content_length < 100 and content_length > 0:
                                raise ValueError(f"Response size too small: {content_length} bytes")
                            
                            # Save the image to a temp file first
                            temp_path = save_path.with_suffix('.tmp')
                            try:
                                with open(temp_path, 'wb') as img_file:
                                    for chunk in response.iter_content(chunk_size=8192):
                                        img_file.write(chunk)
                                
                                # Verify file size and try to open it as an image
                                if temp_path.stat().st_size < 100:
                                    raise ValueError("Downloaded file is too small, likely an error")
                                
                                # Rename temp file to actual filename
                                temp_path.rename(save_path)
                                downloaded_images += 1
                                success = True
                                
                            except Exception as e:
                                # Clean up the temp file
                                if temp_path.exists():
                                    try:
                                        temp_path.unlink()
                                    except:
                                        pass
                                raise ValueError(f"Failed to save image: {e}")
                            
                            # Update image paths in JSON if requested
                            if update_json:
                                # Use the same local path for both small and large
                                rel_path = f"images/small/{filename}"
                                
                                # Update small image path
                                card['images']['small'] = rel_path
                                
                                # Also update large image to use the same path
                                if 'large' in card['images'] and card['images']['large']:
                                    card['images']['large'] = rel_path
                                
                                file_modified = True
                            
                        except Exception as e:
                            error_msg = str(e)
                            logger.error(f"Error downloading {img_url}: {error_msg}")
                            retry_count += 1
                            
                            if retry_count > max_retries:
                                logger.error(f"Failed to download {img_url} after {max_retries} retries")
                                failed_images += 1
                                
                                # Add to problem URLs file
                                if skip_problem_files:
                                    problem_urls.add(img_url)
                                    with open(problem_urls_file, 'a') as f:
                                        f.write(f"{img_url}\n")
                                
                                # Use placeholder image if enabled
                                if use_placeholder and update_json:
                                    rel_path = f"images/small/_placeholder.jpg"
                                    card['images']['small'] = rel_path
                                    if 'large' in card['images'] and card['images']['large']:
                                        card['images']['large'] = rel_path
                                    file_modified = True
                                    placeholder_used += 1
                                    logger.info(f"Using placeholder image for {img_url}")
                
                # Save updated JSON file if any changes were made
                if file_modified and update_json:
                    # Create a backup of the original JSON file
                    backup_file = json_file.with_suffix('.json.bak')
                    if not backup_file.exists():
                        shutil.copy2(json_file, backup_file)
                    
                    # Write the updated JSON file
                    with open(json_file, 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=2)
                    logger.info(f"Updated JSON file: {json_file.name}")
                
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing {json_file.name}: {e}")
            except Exception as e:
                logger.error(f"Error processing {json_file.name}: {e}")
        
        # Take a break between batches to avoid triggering Cloudflare
        if batch_index + batch_size < len(json_files) and not SHUTDOWN_REQUESTED:
            sleep_time = random.uniform(batch_break * 0.8, batch_break * 1.2)
            logger.info(f"Taking a break for {sleep_time:.1f} seconds before next batch...")
            time.sleep(sleep_time)
    
    # Print summary
    logger.info("\n--- Summary ---")
    logger.info(f"Total images found: {total_images}")
    logger.info(f"Images downloaded: {downloaded_images}")
    logger.info(f"Images skipped (already existing): {skipped_images}")
    logger.info(f"Failed downloads: {failed_images}")
    logger.info(f"Placeholder images used: {placeholder_used}")
    logger.info(f"Image files saved to: {small_image_dir}")
    
    # After downloading all images, regenerate the combined pokemonData.js
    if update_json and not SHUTDOWN_REQUESTED:
        concat_pokemon_data(data_dir)

def concat_pokemon_data(data_dir='./data', output_file='pokemonData.js'):
    """
    Generates a pokemonData.js file from all JSON files in data_dir.
    """
    logger.info("\nGenerating pokemonData.js from updated JSON files...")
    
    # Dictionary to hold all Pokémon data
    pokemon_data = {}
    
    # Get list of all JSON files
    json_files = list(Path(data_dir).glob('*.json'))
    
    # Process each JSON file
    for json_file in json_files:
        pokemon_name = json_file.stem.lower()  # Get filename without extension
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                file_data = json.load(f)
                
                # Check if the file already has a 'data' key
                if isinstance(file_data, dict) and 'data' in file_data:
                    pokemon_data[pokemon_name] = file_data
                else:
                    # Wrap the data in a 'data' object
                    pokemon_data[pokemon_name] = {"data": file_data}
        except Exception as e:
            logger.error(f"Error reading {json_file.name}: {e}")
    
    # Generate the JavaScript file
    try:
        # First create a backup of the existing file if it exists
        output_path = Path(output_file)
        if output_path.exists():
            backup_path = output_path.with_suffix('.js.bak')
            shutil.copy2(output_path, backup_path)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("// pokemonData.js - Contains all Pokémon card data for local development\n")
            f.write("// This file was automatically generated with updated local image paths\n\n")
            f.write("var pokemonData = ")
            # Indent with 2 spaces for readability
            f.write(json.dumps(pokemon_data, indent=2))
            f.write(";\n\n")
            f.write("console.log('Pokémon data loaded for local development');\n")
        
        logger.info(f"Success! Created {output_file} with data from {len(pokemon_data)} Pokémon")
    except Exception as e:
        logger.error(f"Error writing to {output_file}: {e}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Download Pokémon card images and update JSON files')
    parser.add_argument('--data-dir', default='./data', help='Directory containing JSON files')
    parser.add_argument('--image-dir', default='./images', help='Directory to save images')
    parser.add_argument('--no-update-json', action='store_false', dest='update_json', 
                        help='Do not update JSON files with local paths')
    parser.add_argument('--min-delay', type=float, default=2.0, 
                        help='Minimum delay between requests in seconds')
    parser.add_argument('--max-delay', type=float, default=5.0, 
                        help='Maximum delay between requests in seconds')
    parser.add_argument('--max-retries', type=int, default=3, 
                        help='Maximum number of retries for failed downloads')
    parser.add_argument('--batch-size', type=int, default=10, 
                        help='Number of files to process before taking a break')
    parser.add_argument('--batch-break', type=float, default=30.0, 
                        help='Seconds to wait between batches')
    parser.add_argument('--no-skip-problem-files', action='store_false', dest='skip_problem_files',
                        help='Do not skip files that consistently cause errors')
    parser.add_argument('--no-use-placeholder', action='store_false', dest='use_placeholder',
                        help='Do not use a placeholder image for failed downloads')
    parser.add_argument('--placeholder-path', 
                        help='Path to a custom placeholder image')
    
    args = parser.parse_args()
    
    try:
        download_pokemon_images(
            data_dir=args.data_dir, 
            image_dir=args.image_dir, 
            update_json=args.update_json,
            min_delay=args.min_delay,
            max_delay=args.max_delay,
            max_retries=args.max_retries,
            batch_size=args.batch_size,
            batch_break=args.batch_break,
            skip_problem_files=args.skip_problem_files,
            use_placeholder=args.use_placeholder,
            placeholder_path=args.placeholder_path
        )
    except KeyboardInterrupt:
        logger.info("Process interrupted by user. Progress has been saved.")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)