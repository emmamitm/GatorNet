import requests
import json
import os

def fetch_uf_campus_data():
    # Create directory for the data
    os.makedirs("campus_data_osm", exist_ok=True)
    
    # More precise bounding box for UF main campus
    bbox = "29.635,-82.365,29.655,-82.335"
    
    # Overpass API endpoint
    overpass_url = "https://overpass-api.de/api/interpreter"
    
    # More focused queries
    queries = [
        # UF Campus Buildings
        {
            "name": "uf_buildings.json",
            "query": f"""
            [out:json];
            (
              way["building"]["operator"="University of Florida"]({bbox});
              way["building"]["name"*="University of Florida"]({bbox});
              way["building"]["name"*="UF "]({bbox});
            );
            out body;
            >;
            out skel qt;
            """
        },
        # All Buildings on Campus (for completeness)
        {
            "name": "campus_buildings.json",
            "query": f"""
            [out:json];
            (
              way["building"]({bbox});
            );
            out body;
            >;
            out skel qt;
            """
        },
        # Campus Amenities
        {
            "name": "campus_amenities.json",
            "query": f"""
            [out:json];
            (
              node["amenity"]({bbox});
              way["amenity"]({bbox});
            );
            out body;
            >;
            out skel qt;
            """
        },
        # Campus Facilities
        {
            "name": "campus_facilities.json",
            "query": f"""
            [out:json];
            (
              node["leisure"]({bbox});
              way["leisure"]({bbox});
              node["shop"]({bbox});
              way["shop"]({bbox});
            );
            out body;
            >;
            out skel qt;
            """
        },
        # Campus Roads and Paths
        {
            "name": "campus_roads.json",
            "query": f"""
            [out:json];
            (
              way["highway"]({bbox});
            );
            out body;
            >;
            out skel qt;
            """
        }
    ]
    
    # Fetch each query
    for query_info in queries:
        print(f"Fetching {query_info['name']}...")
        try:
            response = requests.post(overpass_url, data={"data": query_info['query']})
            
            if response.status_code == 200:
                data = response.json()
                with open(os.path.join("campus_data_osm", query_info['name']), "w") as f:
                    json.dump(data, f, indent=2)
                print(f"✅ Saved {len(data.get('elements', []))} elements to {query_info['name']}")
            else:
                print(f"❌ Failed to fetch {query_info['name']}: {response.status_code}")
                print(f"Response: {response.text[:200]}...")
        except Exception as e:
            print(f"❌ Error fetching {query_info['name']}: {e}")

if __name__ == "__main__":
    print("Fetching UF campus data from OpenStreetMap...")
    fetch_uf_campus_data()