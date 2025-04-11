from flask import Flask, render_template, jsonify
import json
import os
import glob

app = Flask(__name__)

# Load data from all OSM JSON files in the directory
def load_all_osm_data():
    data = {
        'locations': []
    }
    
    # Find all JSON files in the campus_data_osm directory
    json_files = glob.glob(os.path.join("campus_data_osm", "*.json"))
    print(f"Found {len(json_files)} JSON files: {json_files}")
    
    # First, collect all nodes from all files to get coordinates
    all_nodes = {}
    
    for json_file in json_files:
        try:
            with open(json_file, "r") as f:
                file_data = json.load(f)
                
                # Extract nodes with coordinates
                for element in file_data.get('elements', []):
                    if element['type'] == 'node' and 'lat' in element and 'lon' in element:
                        all_nodes[element['id']] = {
                            'lat': element['lat'],
                            'lon': element['lon']
                        }
        except Exception as e:
            print(f"Error extracting nodes from {json_file}: {e}")
    
    print(f"Extracted coordinates for {len(all_nodes)} nodes from all files")
    
    # Now process all elements with tags
    all_locations = []
    processed_ids = set()  # Track processed IDs to avoid duplicates
    
    for json_file in json_files:
        filename = os.path.basename(json_file)
        print(f"Processing {filename}...")
        
        try:
            with open(json_file, "r") as f:
                file_data = json.load(f)
                
                # Process elements with tags
                file_locations = []
                
                for element in file_data.get('elements', []):
                    # Skip if already processed or has no tags
                    if element['id'] in processed_ids or 'tags' not in element:
                        continue
                    
                    # Create location entry
                    location = {
                        'id': element['id'],
                        'type': element['type'],
                        'source_file': filename
                    }
                    
                    # Set coordinates based on element type
                    if element['type'] == 'node':
                        if 'lat' in element and 'lon' in element:
                            location['lat'] = element['lat']
                            location['lon'] = element['lon']
                        else:
                            continue  # Skip nodes without coordinates
                            
                    elif element['type'] == 'way':
                        # For ways, calculate center point from nodes
                        if 'nodes' not in element:
                            continue
                            
                        valid_nodes = []
                        for node_id in element['nodes']:
                            if node_id in all_nodes:
                                valid_nodes.append(all_nodes[node_id])
                        
                        if not valid_nodes:
                            continue  # Skip if no valid nodes found
                            
                        # Calculate average coordinates
                        lat_sum = sum(node['lat'] for node in valid_nodes)
                        lon_sum = sum(node['lon'] for node in valid_nodes)
                        count = len(valid_nodes)
                        
                        location['lat'] = lat_sum / count
                        location['lon'] = lon_sum / count
                    
                    else:
                        # Skip other types without direct coordinates
                        continue
                    
                    # Copy tags
                    location['tags'] = element['tags']
                    
                    # Determine name
                    if 'name' in location['tags']:
                        location['name'] = location['tags']['name']
                    elif 'official_name' in location['tags']:
                        location['name'] = location['tags']['official_name']
                    else:
                        # Generate descriptive name based on tags
                        key_tags = ['building', 'amenity', 'highway', 'leisure', 'shop']
                        for tag in key_tags:
                            if tag in location['tags']:
                                tag_value = location['tags'][tag]
                                if isinstance(tag_value, str):
                                    location['name'] = f"{tag_value.title()} (ID: {location['id']})"
                                    break
                        else:
                            location['name'] = f"Location {location['id']}"
                    
                    # Determine element type for styling
                    if 'building' in location['tags']:
                        if location['tags']['building'] in ['university', 'college', 'school']:
                            location['element_type'] = 'university'
                        elif location['tags']['building'] in ['residential', 'dormitory', 'apartments']:
                            location['element_type'] = 'residential'
                        else:
                            location['element_type'] = 'building'
                    elif 'amenity' in location['tags']:
                        location['element_type'] = location['tags']['amenity']
                    elif 'highway' in location['tags']:
                        location['element_type'] = 'highway'
                    elif 'leisure' in location['tags']:
                        location['element_type'] = 'leisure'
                    elif 'shop' in location['tags']:
                        location['element_type'] = 'shop'
                    elif 'natural' in location['tags']:
                        location['element_type'] = 'natural'
                    else:
                        location['element_type'] = 'default'
                    
                    # Add to locations and mark as processed
                    file_locations.append(location)
                    processed_ids.add(element['id'])
                
                all_locations.extend(file_locations)
                print(f"Extracted {len(file_locations)} locations from {filename}")
                
        except Exception as e:
            print(f"Error processing {filename}: {e}")
    
    # Update the data with all locations
    data['locations'] = all_locations
    print(f"Total unique locations: {len(all_locations)}")
    
    return data


def get_map_data():
    return load_all_osm_data()