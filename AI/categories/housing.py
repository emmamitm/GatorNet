#!/usr/bin/env python3
import json
import os
import sys
import csv
import pandas as pd
from collections import defaultdict
import re
from pathlib import Path

class HousingSystem:
    def __init__(self):
        """Initialize the housing system with data from CSV files"""
        # Define file paths - navigate up from AI directory to find scrapedData
        script_dir = os.path.dirname(os.path.abspath(__file__))
        base_dir = Path(script_dir).parent.parent  # Navigate up from AI/categories to root
        
        hall_info_path = os.path.join(base_dir, "scrapedData/housing/hallInfo.csv")
        housing_links_path = os.path.join(base_dir, "scrapedData/housing/housingLinks.csv")
        residence_rates_path = os.path.join(base_dir, "scrapedData/housing/residenceHallRates.csv")
        
        # Initialize data structures
        self.halls = []
        self.rates = {}
        self.links = {}
        
        # Load residence hall data from CSV
        try:
            hall_df = pd.read_csv(hall_info_path)
            for _, row in hall_df.iterrows():
                hall = {col: row[col] for col in hall_df.columns}
                # Clean up the room_types and nearby_locations fields
                self.halls.append(hall)
            print(f"Loaded {len(self.halls)} residence halls from {hall_info_path}")
        except Exception as e:
            print(f"Error loading residence hall data: {e}")
            self.halls = []
        
        # Load rates data from CSV file
        try:
            rates_df = pd.read_csv(residence_rates_path)
            self.rates = {}
            for _, row in rates_df.iterrows():
                hall_name = row['residence_hall']
                room_type = row['room_type']
                fall_spring = row['fall_spring']
                summer_a_b = row['summer_a_b']
                summer_c = row['summer_c']
                
                if hall_name not in self.rates:
                    self.rates[hall_name] = {}
                
                self.rates[hall_name][room_type] = {
                    "fall_spring": fall_spring,
                    "summer_a_b": summer_a_b,
                    "summer_c": summer_c
                }
            print(f"Loaded rental rates for {len(self.rates)} residence halls from {residence_rates_path}")
        except Exception as e:
            print(f"Error loading residence hall rates: {e}")
            self.rates = {}
        
        # Load links data from CSV file
        try:
            links_df = pd.read_csv(housing_links_path)
            self.links = {}
            for _, row in links_df.iterrows():
                description = row['description'].strip('"')
                link = row['link']
                self.links[description] = link
            print(f"Loaded {len(self.links)} housing links from {housing_links_path}")
        except Exception as e:
            print(f"Error loading housing links: {e}")
            self.links = {}
        
        # Process room types and nearby locations correctly
        for hall in self.halls:
            # Process room types - look for actual room types
            room_types_str = hall.get('room_types_str', '')
            actual_room_types = []
            
            # Common room type prefixes to identify actual room types
            room_type_patterns = [
                'Single', 'Double', 'Triple', 'Quad', 'Apartment', 'Suite', 
                'One Bedroom', 'Two Bedroom', 'Efficiency', 'Private Bedroom'
            ]
            
            # Extract the actual room types
            for item in room_types_str.split(', '):
                if any(pattern in item for pattern in room_type_patterns):
                    actual_room_types.append(item)
            
            # Store the processed room types
            hall['actual_room_types'] = actual_room_types
            
            # Process nearby locations - exclude room types
            nearby_str = hall.get('nearby_locations_str', '')
            actual_nearby = []
            
            for item in nearby_str.split(', '):
                if not any(pattern in item for pattern in room_type_patterns):
                    actual_nearby.append(item)
            
            # Store the processed nearby locations
            hall['actual_nearby'] = actual_nearby
            
        # Build mappings
        self.build_mappings()
    
    def build_mappings(self):
        """Build helpful mappings for searching and filtering"""
        # Extract all hall types
        self.hall_types = set()
        for hall in self.halls:
            hall_type = hall.get("hall_type", "")
            if hall_type:
                self.hall_types.add(hall_type)
        
        # Extract all locations
        self.locations = set()
        for hall in self.halls:
            location = hall.get("location", "")
            if location:
                self.locations.add(location)
        
        # Extract all features
        self.all_features = set()
        for hall in self.halls:
            features = hall.get("features_str", "").split(", ")
            for feature in features:
                if feature:
                    self.all_features.add(feature)
        
        # Extract all room types from the processed data
        self.all_room_types = set()
        for hall in self.halls:
            for room_type in hall.get('actual_room_types', []):
                if room_type:
                    self.all_room_types.add(room_type)
        
        # Extract all nearby locations from the processed data
        self.all_nearby = set()
        for hall in self.halls:
            for location in hall.get('actual_nearby', []):
                if location:
                    self.all_nearby.add(location)
        
        # Create matcher questions based on hall data
        self.matcher_questions = [
            {
                "id": "hall_type",
                "question": "What type of housing are you looking for?",
                "options": sorted(list(self.hall_types)) + ["No preference"]
            },
            {
                "id": "room_type",
                "question": "What type of room do you prefer?",
                "options": ["Single", "Double", "Triple", "Quad", "Apartment", "Suite", "No preference"]
            },
            {
                "id": "budget",
                "question": "What is your budget per semester (Fall/Spring)?",
                "options": ["Under $3500", "$3500-$4000", "$4000-$4500", "$4500-$5000", "Over $5000", "No preference"]
            },
            {
                "id": "features",
                "question": "What features are most important to you?",
                "options": ["Fully Furnished", "Private Bathroom", "Kitchen/Kitchenette", "Laundry Facilities", 
                           "Study Spaces", "Social/Game Rooms", "No preference"]
            },
            {
                "id": "location",
                "question": "What campus location do you prefer to be near?",
                "options": ["College of Business", "College of Engineering", "College of Arts", 
                           "Athletics (Stadium/O'Connell Center)", "Reitz Union", "Libraries", "No preference"]
            }
        ]
    
    def clear_screen(self):
        """Clear the terminal screen."""
        os.system('cls' if os.name == 'nt' else 'clear')
        
    def print_header(self, title):
        """Print a formatted header."""
        self.clear_screen()
        print("=" * 60)
        print(f"{title.center(60)}")
        print("=" * 60)
        print()
        
    def get_selection(self, options, prompt="Select an option", allow_exit=True):
        """Get a valid selection from the user."""
        while True:
            print(f"\n{prompt}:")
            for i, option in enumerate(options, 1):
                print(f"{i}. {option}")
            
            if allow_exit:
                print("\n0. Back to previous menu")
                print("E. Exit program")
            
            choice = input("\nEnter your choice: ").strip().lower()
            
            if choice == 'e':
                self.exit_program()
            
            if allow_exit and choice == '0':
                return None
            
            try:
                choice_index = int(choice) - 1
                if 0 <= choice_index < len(options):
                    return options[choice_index]
            except ValueError:
                pass
                
            print("\nInvalid selection. Please try again.")
    
    def display_hall_info(self, hall, category=None):
        """Display information about a specific residence hall."""
        self.print_header(f"{hall['name']} Information")
        
        if category == "All Information":
            categories = ["Description", "Location", "Hall Type", "Features", "Room Types", 
                         "Nearby Locations", "Rental Rates", "Contact Information"]
        elif category:
            categories = [category]
        else:
            # Let user select a category
            categories = ["Description", "Location", "Hall Type", "Features", "Room Types", 
                         "Nearby Locations", "Rental Rates", "Contact Information", "All Information"]
            selected = self.get_selection(categories, "What information would you like to see?")
            if not selected:
                return
            
            if selected == "All Information":
                categories = ["Description", "Location", "Hall Type", "Features", "Room Types", 
                            "Nearby Locations", "Rental Rates", "Contact Information"]
            else:
                categories = [selected]
        
        for category in categories:
            print(f"\n{category}:")
            
            if category == "Description":
                print(hall.get("description", "No description available"))
            
            elif category == "Location":
                print(hall.get("location", "Location not specified"))
            
            elif category == "Hall Type":
                print(hall.get("hall_type", "Type not specified"))
            
            elif category == "Features":
                features = hall.get("features_str", "").split(", ")
                for feature in features:
                    if feature:
                        print(f"- {feature}")
            
            elif category == "Room Types":
                # Use the processed room types instead of the raw data
                room_types = hall.get("actual_room_types", [])
                if room_types:
                    for room_type in room_types:
                        print(f"- {room_type}")
                else:
                    print("Room type information not available")
            
            elif category == "Nearby Locations":
                # Use the processed nearby locations instead of the raw data
                nearby = hall.get("actual_nearby", [])
                if nearby:
                    for location in nearby:
                        print(f"- {location}")
                else:
                    print("Nearby location information not available")
            
            elif category == "Rental Rates":
                hall_name = hall["name"]
                if hall_name in self.rates:
                    print("Room rates per semester:")
                    for room_type, rates in self.rates[hall_name].items():
                        print(f"  {room_type}:")
                        print(f"    Fall/Spring: ${rates['fall_spring']}")
                        print(f"    Summer A/B: ${rates['summer_a_b']}")
                        print(f"    Summer C: ${rates['summer_c']}")
                else:
                    print("Rental rates not available for this hall")
            
            elif category == "Contact Information":
                print(f"Phone: {hall.get('phone', 'Not available')}")
                print(f"Website: {hall.get('url', 'Not available')}")
                if hall.get('email'):
                    print(f"Email: {hall.get('email')}")
        
        input("\nPress Enter to continue...")
        
    def hall_info_menu(self):
        """Show the residence hall information menu."""
        while True:
            self.print_header("Residence Hall Information")
            
            # Get hall names
            hall_names = [hall["name"] for hall in self.halls]
            
            # Let user select a hall
            selected_hall_name = self.get_selection(hall_names, "Select a residence hall for more information")
            if not selected_hall_name:
                return
                
            # Find the selected hall
            selected_hall = next((hall for hall in self.halls if hall["name"] == selected_hall_name), None)
            
            if selected_hall:
                self.display_hall_info(selected_hall)
    
    def search_halls(self):
        """Search for residence halls with various criteria."""
        self.print_header("Search Residence Halls")
        
        # Define search options
        search_options = [
            "Search by hall type",
            "Search by room type",
            "Search by price range",
            "Search by features",
            "Search by location/nearby locations",
            "Search by keyword"
        ]
        
        selected = self.get_selection(search_options, "How would you like to search?")
        if not selected:
            return
            
        if selected == "Search by hall type":
            hall_types = sorted(list(self.hall_types))
            hall_type = self.get_selection(hall_types, "Select a hall type")
            if not hall_type:
                return
                
            results = [hall for hall in self.halls if hall.get("hall_type", "") == hall_type]
            
        elif selected == "Search by room type":
            room_options = ["Single", "Double", "Triple", "Quad", "Apartment", "Suite"]
            room_type = self.get_selection(room_options, "Select a room type")
            if not room_type:
                return
                
            results = []
            for hall in self.halls:
                # Check in the processed room types
                room_types = hall.get("actual_room_types", [])
                if any(room_type.lower() in rt.lower() for rt in room_types):
                    results.append(hall)
            
        elif selected == "Search by price range":
            price_ranges = [
                "Under $3500",
                "$3500-$4000",
                "$4000-$4500",
                "$4500-$5000",
                "Over $5000"
            ]
            price_range = self.get_selection(price_ranges, "Select a price range (per semester)")
            if not price_range:
                return
                
            results = []
            for hall in self.halls:
                hall_name = hall["name"]
                if hall_name in self.rates:
                    for room_type, rates in self.rates[hall_name].items():
                        try:
                            fall_spring_rate = int(rates["fall_spring"])
                            
                            if price_range == "Under $3500" and fall_spring_rate < 3500:
                                results.append(hall)
                                break
                            elif price_range == "$3500-$4000" and 3500 <= fall_spring_rate < 4000:
                                results.append(hall)
                                break
                            elif price_range == "$4000-$4500" and 4000 <= fall_spring_rate < 4500:
                                results.append(hall)
                                break
                            elif price_range == "$4500-$5000" and 4500 <= fall_spring_rate < 5000:
                                results.append(hall)
                                break
                            elif price_range == "Over $5000" and fall_spring_rate >= 5000:
                                results.append(hall)
                                break
                        except (ValueError, TypeError):
                            continue
            
        elif selected == "Search by features":
            # Get most common features
            common_features = ["Fully Furnished", "Laundry Facilities", "High-Speed Internet", 
                             "Study Lounge", "Game Room", "Kitchen/Kitchenette"]
            
            feature = self.get_selection(common_features, "Select a feature")
            if not feature:
                return
                
            results = []
            for hall in self.halls:
                features_str = hall.get("features_str", "")
                if feature in features_str:
                    results.append(hall)
            
        elif selected == "Search by location/nearby locations":
            location_options = [
                "Near College of Business",
                "Near College of Engineering",
                "Near Athletics Facilities",
                "Near Library West",
                "Near Reitz Union"
            ]
            
            location_search = self.get_selection(location_options, "Select a location")
            if not location_search:
                return
                
            search_term = location_search.replace("Near ", "").lower()
            
            results = []
            for hall in self.halls:
                nearby_str = hall.get("nearby_locations_str", "").lower()
                if search_term in nearby_str:
                    results.append(hall)
            
        elif selected == "Search by keyword":
            keyword = input("\nEnter a keyword to search for: ").strip().lower()
            if not keyword:
                print("No keyword entered.")
                input("\nPress Enter to continue...")
                return
                
            results = []
            for hall in self.halls:
                hall_text = (
                    hall.get("name", "").lower() + " " +
                    hall.get("description", "").lower() + " " +
                    hall.get("features_str", "").lower() + " " +
                    hall.get("room_types_str", "").lower() + " " +
                    hall.get("nearby_locations_str", "").lower()
                )
                
                if keyword in hall_text:
                    results.append(hall)
        
        if results:
            self.display_search_results(results)
        else:
            print("\nNo residence halls found matching your criteria.")
            input("\nPress Enter to continue...")
    
    def display_search_results(self, results):
        """Display a list of residence halls with options to view details."""
        while True:
            self.print_header("Search Results")
            print(f"Found {len(results)} residence halls matching your criteria:\n")
            
            for i, hall in enumerate(results, 1):
                hall_type = hall.get("hall_type", "Unknown type")
                print(f"{i}. {hall['name']} - {hall_type}")
            
            print("\nOptions:")
            print("V #: View details for hall number # (e.g., V 1)")
            print("B: Back to search menu")
            
            choice = input("\nEnter your choice: ").strip().lower()
            
            if choice == 'b':
                return
            elif choice.startswith('v '):
                try:
                    hall_num = int(choice[2:]) - 1
                    if 0 <= hall_num < len(results):
                        self.display_hall_info(results[hall_num])
                    else:
                        print("Invalid hall number.")
                except ValueError:
                    print("Invalid input. Please enter a valid hall number.")
            else:
                print("Invalid choice. Please try again.")
    
    def housing_matcher(self):
        """Run the housing matcher feature to find the best residence hall match."""
        self.print_header("Housing Matcher")
        
        # Collect answers to all questions
        answers = {}
        for question_data in self.matcher_questions:
            q_id = question_data["id"]
            question = question_data["question"]
            options = question_data["options"]
            
            selected = self.get_selection(options, question)
            if not selected:
                return
                
            answers[q_id] = selected
        
        print("\nAnalyzing your preferences to find the best housing matches...")
        
        # Calculate matches and scores
        hall_scores, reasons = self.calculate_hall_scores(answers)
        
        # Get top 3 matches
        top_matches = sorted(hall_scores.items(), key=lambda x: x[1], reverse=True)[:3]
        top_halls = []
        
        for hall_name, score in top_matches:
            hall = next((h for h in self.halls if h["name"] == hall_name), None)
            if hall:
                top_halls.append((hall, score, reasons.get(hall_name, [])))
        
        # Display the results
        self.display_hall_recommendations(top_halls, answers)
    
    def calculate_hall_scores(self, preferences):
        """Calculate scores for each residence hall based on user preferences."""
        scores = {hall["name"]: 0 for hall in self.halls}
        reasons = {hall["name"]: [] for hall in self.halls}
        
        hall_type_pref = preferences.get('hall_type', 'No preference')
        room_type_pref = preferences.get('room_type', 'No preference')
        budget_pref = preferences.get('budget', 'No preference')
        features_pref = preferences.get('features', 'No preference')
        location_pref = preferences.get('location', 'No preference')
        
        # Score each residence hall
        for hall in self.halls:
            hall_name = hall["name"]
            hall_type = hall.get("hall_type", "")
            features_str = hall.get("features_str", "")
            room_types = hall.get("actual_room_types", [])
            nearby_locations = hall.get("actual_nearby", [])
            
            # 1. Hall type matching (0-3 points)
            if hall_type_pref != "No preference":
                if hall_type == hall_type_pref:
                    scores[hall_name] += 3
                    reasons[hall_name].append(f"Matches your preferred hall type: {hall_type_pref}")
            
            # 2. Room type matching (0-3 points)
            if room_type_pref != "No preference":
                if any(room_type_pref.lower() in rt.lower() for rt in room_types):
                    scores[hall_name] += 3
                    reasons[hall_name].append(f"Offers your preferred room type: {room_type_pref}")
            
            # 3. Budget matching (0-3 points)
            if budget_pref != "No preference" and hall_name in self.rates:
                min_rate = float('inf')
                for room_type, rates in self.rates[hall_name].items():
                    try:
                        rate = int(rates["fall_spring"])
                        min_rate = min(min_rate, rate)
                    except (ValueError, TypeError):
                        continue
                
                if min_rate != float('inf'):
                    if budget_pref == "Under $3500" and min_rate < 3500:
                        scores[hall_name] += 3
                        reasons[hall_name].append(f"Within your budget range: Under $3500")
                    elif budget_pref == "$3500-$4000" and 3500 <= min_rate < 4000:
                        scores[hall_name] += 3
                        reasons[hall_name].append(f"Within your budget range: $3500-$4000")
                    elif budget_pref == "$4000-$4500" and 4000 <= min_rate < 4500:
                        scores[hall_name] += 3
                        reasons[hall_name].append(f"Within your budget range: $4000-$4500")
                    elif budget_pref == "$4500-$5000" and 4500 <= min_rate < 5000:
                        scores[hall_name] += 3
                        reasons[hall_name].append(f"Within your budget range: $4500-$5000")
                    elif budget_pref == "Over $5000" and min_rate >= 5000:
                        scores[hall_name] += 3
                        reasons[hall_name].append(f"Within your budget range: Over $5000")
                    # Partial matches for slightly outside budget
                    elif budget_pref == "Under $3500" and min_rate < 3700:
                        scores[hall_name] += 1
                        reasons[hall_name].append("Slightly above your budget range")
                    elif budget_pref == "$3500-$4000" and min_rate < 4200:
                        scores[hall_name] += 1
                        reasons[hall_name].append("Slightly above your budget range")
            
            # 4. Features matching (0-3 points)
            if features_pref != "No preference":
                if features_pref in features_str:
                    scores[hall_name] += 3
                    reasons[hall_name].append(f"Has your desired feature: {features_pref}")
                # Check for similar features with partial matching
                elif features_pref == "Private Bathroom" and "Semi-Private Bathroom" in features_str:
                    scores[hall_name] += 2
                    reasons[hall_name].append("Has semi-private bathrooms (shared with suitemates)")
                elif features_pref == "Kitchen/Kitchenette" and "Kitchen" in features_str:
                    scores[hall_name] += 3
                    reasons[hall_name].append("Has kitchen facilities")
            
            # 5. Location matching (0-3 points)
            if location_pref != "No preference":
                # Process the nearby locations to look for matches
                nearby_str = ", ".join(nearby_locations).lower()
                
                if "college of business" in location_pref.lower() and any(
                    "business" in loc.lower() for loc in nearby_locations):
                    scores[hall_name] += 3
                    reasons[hall_name].append(f"Near the College of Business")
                elif "college of engineering" in location_pref.lower() and any(
                    "engineering" in loc.lower() for loc in nearby_locations):
                    scores[hall_name] += 3
                    reasons[hall_name].append(f"Near the College of Engineering")
                elif "college of arts" in location_pref.lower() and any(
                    "arts" in loc.lower() for loc in nearby_locations):
                    scores[hall_name] += 3
                    reasons[hall_name].append(f"Near the College of Arts")
                elif "athletics" in location_pref.lower() and any(
                    loc in nearby_str for loc in ["stadium", "o'connell", "athletics"]):
                    scores[hall_name] += 3
                    reasons[hall_name].append("Near athletics facilities")
                elif "reitz union" in location_pref.lower() and "reitz union" in nearby_str:
                    scores[hall_name] += 3
                    reasons[hall_name].append("Near the Reitz Union")
                elif "libraries" in location_pref.lower() and any(
                    loc in nearby_str for loc in ["library", "marston"]):
                    scores[hall_name] += 3
                    reasons[hall_name].append("Near campus libraries")
            
            # 6. Special bonuses for specific combinations (0-3 points)
            if hall_type_pref == "Apartment Style" and "Kitchen" in features_str:
                scores[hall_name] += 1
                reasons[hall_name].append("Apartment with full kitchen")
                
            if room_type_pref == "Single" and "Private Bedroom" in features_str:
                scores[hall_name] += 1
                reasons[hall_name].append("Single room with privacy")
                
            if features_pref == "Study Spaces" and "Study" in features_str and "Quiet" in features_str:
                scores[hall_name] += 1
                reasons[hall_name].append("Good study environment with quiet areas")
        
        return scores, reasons
    
    def display_hall_recommendations(self, top_halls, preferences):
        """Display the top residence hall recommendations with reasoning."""
        self.print_header("Housing Recommendations")
        
        if not top_halls:
            print("Sorry, I couldn't find any good matches for your preferences.")
            input("\nPress Enter to continue...")
            return
            
        # Print preference summary
        print("Based on your preferences:")
        print(f"- Hall Type: {preferences.get('hall_type', 'No preference')}")
        print(f"- Room Type: {preferences.get('room_type', 'No preference')}")
        print(f"- Budget: {preferences.get('budget', 'No preference')}")
        print(f"- Features: {preferences.get('features', 'No preference')}")
        print(f"- Location: {preferences.get('location', 'No preference')}")
        print("\nHere are your top matches:\n")
        
        # Display each recommendation
        for i, (hall, score, hall_reasons) in enumerate(top_halls, 1):
            hall_name = hall["name"]
            hall_type = hall.get("hall_type", "")
            
            print(f"{i}. {hall_name} - {hall_type}")
            print(f"   Match Score: {score}/15")
            
            # Print top reasons (max 3)
            if hall_reasons:
                print("   Why this is a good match:")
                for reason in hall_reasons[:3]:
                    print(f"   - {reason}")
            
            # Print room types and rates
            if hall_name in self.rates:
                print("   Room options:")
                for room_type, rates in self.rates[hall_name].items():
                    print(f"   - {room_type}: ${rates['fall_spring']}/semester")
            
            print()
        
        # Options for further action
        while True:
            print("\nOptions:")
            print("V #: View detailed information for recommendation # (e.g., V 1)")
            print("C: Compare all recommendations side by side")
            print("B: Back to main menu")
            
            choice = input("\nEnter your choice: ").strip().lower()
            
            if choice == 'b':
                return
            elif choice == 'c':
                self.compare_recommendations(top_halls)
            elif choice.startswith('v '):
                try:
                    hall_num = int(choice[2:]) - 1
                    if 0 <= hall_num < len(top_halls):
                        self.display_hall_info(top_halls[hall_num][0])
                    else:
                        print("Invalid recommendation number.")
                except ValueError:
                    print("Invalid input. Please enter a valid number.")
            else:
                print("Invalid choice. Please try again.")
    
    def compare_recommendations(self, top_halls):
        """Display a side-by-side comparison of recommended halls."""
        self.print_header("Recommendation Comparison")
        
        # Extract just the halls
        halls = [hall for hall, score, reasons in top_halls]
        
        # Comparison categories
        categories = ["Hall Type", "Room Types", "Features", "Nearby Locations", "Price Range"]
        
        # Display hall names as headers
        headers = [hall["name"] for hall in halls]
        print("Comparison of:", " | ".join(headers))
        print("-" * 80)
        
        # Compare each category
        for category in categories:
            print(f"\n{category}:")
            
            if category == "Hall Type":
                values = [hall.get("hall_type", "Not specified") for hall in halls]
                for i, val in enumerate(values):
                    print(f"  {headers[i]}: {val}")
            
            elif category == "Room Types":
                for i, hall in enumerate(halls):
                    room_types = hall.get("actual_room_types", [])
                    if room_types:
                        print(f"  {headers[i]}: {', '.join(room_types[:3])}")
                    else:
                        print(f"  {headers[i]}: Not specified")
            
            elif category == "Features":
                for i, hall in enumerate(halls):
                    features = hall.get("features_str", "").split(", ")
                    print(f"  {headers[i]}: {', '.join(features[:3])}")
            
            elif category == "Nearby Locations":
                for i, hall in enumerate(halls):
                    nearby = hall.get("actual_nearby", [])
                    if nearby:
                        print(f"  {headers[i]}: {', '.join(nearby[:3])}")
                    else:
                        print(f"  {headers[i]}: Not specified")
            
            elif category == "Price Range":
                for i, hall in enumerate(halls):
                    hall_name = hall["name"]
                    if hall_name in self.rates:
                        rates = []
                        for room_type, rate_data in self.rates[hall_name].items():
                            try:
                                fall_spring = int(rate_data["fall_spring"])
                                rates.append(fall_spring)
                            except (ValueError, TypeError):
                                continue
                        
                        if rates:
                            min_rate = min(rates)
                            max_rate = max(rates)
                            print(f"  {headers[i]}: ${min_rate} - ${max_rate}")
                        else:
                            print(f"  {headers[i]}: Rates not available")
                    else:
                        print(f"  {headers[i]}: Rates not available")
        
        input("\nPress Enter to continue...")

    def application_info(self):
        """Display housing application information and links."""
        self.print_header("Housing Application Information")
        
        # Define categories of links to display
        link_categories = {
            "Application Process": [
                "First Year Student Housing Application",
                "Graduate and Family Housing Application",
                "Housing Application Guide",
                "Current Student Housing Application",
                "Housing Frequently Asked Questions"
            ],
            "Housing Options": [
                "Graduate and Family Housing Options",
                "Residence Hall Options for Individuals",
                "Living Learning Communities Information"
            ],
            "Rates and Payments": [
                "Graduate and Family Housing Rental Rates",
                "Residence Hall Rental Rates",
                "Housing Payment Information",
                "Florida Prepaid Housing Plan Information"
            ]
        }
        
        # Display links by category
        for category, link_names in link_categories.items():
            print(f"\n{category}:")
            for i, link_name in enumerate(link_names, 1):
                if link_name in self.links:
                    print(f"  {i}. {link_name}")
        
        print("\nFor more information, visit the Housing & Residence Life website:")
        print("  https://housing.ufl.edu/")
        
        input("\nPress Enter to continue...")

    def main_menu(self):
        """Display the main menu."""
        while True:
            self.print_header("UF Housing Selection System")
            
            options = [
                "View Residence Hall Information",
                "Search Residence Halls",
                "Housing Matcher",
                "Housing Application Information"
            ]
            
            selected = self.get_selection(options, "Main Menu", allow_exit=True)
            
            if selected == "View Residence Hall Information":
                self.hall_info_menu()
            elif selected == "Search Residence Halls":
                self.search_halls()
            elif selected == "Housing Matcher":
                self.housing_matcher()
            elif selected == "Housing Application Information":
                self.application_info()

    def exit_program(self):
        """Exit the program."""
        self.print_header("Thank You")
        print("Thank you for using the UF Housing Selection System!")
        print("\nExiting program...")
        sys.exit(0)
        
    def run(self):
        """Run the housing system."""
        try:
            self.main_menu()
        except KeyboardInterrupt:
            self.exit_program()


if __name__ == "__main__":
    system = HousingSystem()
    system.run()