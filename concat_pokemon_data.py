#!/usr/bin/env python3
import os
import json
import sys
from pathlib import Path

def concat_pokemon_data(data_dir='./data', output_file='pokemonData.js'):
    """
    Scans a directory for JSON files and concatenates them into a single JavaScript file.
    
    Args:
        data_dir: Directory containing Pokémon JSON files
        output_file: Output JavaScript file path
    """
    # Create the data directory path object
    data_path = Path(data_dir)
    
    if not data_path.exists() or not data_path.is_dir():
        print(f"Error: '{data_dir}' is not a valid directory")
        sys.exit(1)
    
    # Dictionary to hold all Pokémon data
    pokemon_data = {}
    
    # Get list of all JSON files
    json_files = list(data_path.glob('*.json'))
    
    if not json_files:
        print(f"Warning: No JSON files found in '{data_dir}'")
        sys.exit(1)
    
    print(f"Found {len(json_files)} JSON files in '{data_dir}'")
    
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
                
                print(f"Processed {pokemon_name}.json")
        except json.JSONDecodeError as e:
            print(f"Error parsing {json_file.name}: {e}")
        except Exception as e:
            print(f"Error reading {json_file.name}: {e}")
    
    # Generate the JavaScript file
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("// pokemonData.js - Contains all Pokémon card data for local development\n")
            f.write("// This file was automatically generated from JSON files in the data directory\n\n")
            f.write("var pokemonData = ")
            # Indent with 2 spaces for readability
            f.write(json.dumps(pokemon_data, indent=2))
            f.write(";\n\n")
            f.write("console.log('Pokémon data loaded for local development');\n")
        
        print(f"\nSuccess! Created {output_file} with data from {len(pokemon_data)} Pokémon")
    except Exception as e:
        print(f"Error writing to {output_file}: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Get command line arguments
    if len(sys.argv) > 1:
        data_dir = sys.argv[1]
    else:
        data_dir = './data'
    
    if len(sys.argv) > 2:
        output_file = sys.argv[2]
    else:
        output_file = 'pokemonData.js'
    
    concat_pokemon_data(data_dir, output_file)