#!/usr/bin/env python3
import json
import os
import sys
import csv
import pandas as pd
from collections import defaultdict
import re
from pathlib import Path

class ClubSystem:
    def __init__(self):
        """Initialize the club system with data from CSV and JSON files"""
        # Define file paths
        script_dir = os.path.dirname(os.path.abspath(__file__))
        base_dir = Path(script_dir).parent.parent  # Navigate up from AI/categories to root
        
        print(f"Script directory: {script_dir}")
        
        # Use direct paths relative to the script directory
        clubs_csv_path = os.path.join(base_dir,"scrapedData", "campusClubs","uf_organizations.csv")
        clubs_json_path ="./jsonFiles/clubs.json"
    
        # Initialize data structures
        self.clubs = []
        self.category_groups = []
        self.categories = []
        self.matcher_questions = []
        
        # Load clubs data from CSV
        try:
            print(f"Attempting to load clubs from: {clubs_csv_path}")
            if not os.path.exists(clubs_csv_path):
                print(f"CSV file not found: {clubs_csv_path}")
                
            clubs_df = pd.read_csv(clubs_csv_path)
            print(f"CSV file loaded with {len(clubs_df)} rows")
            
            # Display the first few column names for debugging
            if not clubs_df.empty:
                print(f"CSV columns: {', '.join(clubs_df.columns[:5])}...")
            
            for _, row in clubs_df.iterrows():
                club = {col: row[col] for col in clubs_df.columns}
                self.clubs.append(club)
            print(f"Loaded {len(self.clubs)} clubs from {clubs_csv_path}")
            
            # Print first club for debugging if available
            if self.clubs:
                first_club = self.clubs[0]
                print(f"First club: {first_club.get('Organization Name', 'Name not found')} (ID: {first_club.get('ID', 'ID not found')})")
        except Exception as e:
            print(f"Error loading clubs data: {e}")
            import traceback
            traceback.print_exc()
            self.clubs = []
        
        # Load category structure and matcher questions from JSON
        try:
            print(f"Attempting to load category structure from: {clubs_json_path}")
            if not os.path.exists(clubs_json_path):
                print(f"JSON file not found: {clubs_json_path}")
                
            with open(clubs_json_path, 'r') as f:
                club_data = json.load(f)
                self.category_groups = club_data.get('category_groups', [])
                self.categories = club_data.get('categories', [])
                self.matcher_questions = club_data.get('matcher_questions', [])
            print(f"Loaded category structure from {clubs_json_path}")
            print(f"Loaded {len(self.category_groups)} category groups")
            print(f"Loaded {len(self.categories)} categories")
            print(f"Loaded {len(self.matcher_questions)} matcher questions")
        except Exception as e:
            print(f"Error loading category structure: {e}")
            import traceback
            traceback.print_exc()
        
        # Build additional mappings for searching
        self.build_mappings()
    
    def build_mappings(self):
        """Build helpful mappings for searching and filtering"""
        # Create a mapping of category names to subcategories
        self.category_subcategories = {}
        for category in self.categories:
            self.category_subcategories[category['name']] = category['subcategories']
        
        # Create a mapping of group names to categories
        self.group_categories = {}
        for group in self.category_groups:
            self.group_categories[group['group_name']] = group['categories']
        
        # Create a flat list of all categories
        self.all_categories = []
        for group in self.category_groups:
            self.all_categories.extend(group['categories'])
        
        # Create a flat list of all subcategories
        self.all_subcategories = []
        for category in self.categories:
            self.all_subcategories.extend(category['subcategories'])
        
        # Extract organizations by purpose for text search
        self.organization_purposes = {}
        for club in self.clubs:
            org_id = club.get('ID')
            purpose = club.get('Description', '')
            if org_id and purpose:
                self.organization_purposes[org_id] = purpose
    
    def clear_screen(self):
        """Clear the terminal screen."""
        os.system('cls' if os.name == 'nt' else 'clear')
        
    def print_header(self, title):
        """Print a formatted header."""
        self.clear_screen()
        print("=" * 80)
        print(f"{title.center(80)}")
        print("=" * 80)
        print()
        
    def get_selection(self, options, prompt="Select an option", allow_exit=True, allow_multiple=False):
        """Get a valid selection from the user.
        
        If allow_multiple is True, return a list of selections.
        """
        if allow_multiple:
            print(f"\n{prompt} (enter numbers separated by commas):")
            for i, option in enumerate(options, 1):
                print(f"{i}. {option}")
            
            if allow_exit:
                print("\n0. Back to previous menu")
                print("E. Exit program")
            
            choice = input("\nEnter your choices: ").strip().lower()
            
            if choice == 'e':
                self.exit_program()
            
            if allow_exit and choice == '0':
                return None
            
            try:
                selected_indices = [int(idx.strip()) - 1 for idx in choice.split(',') if idx.strip()]
                valid_indices = [idx for idx in selected_indices if 0 <= idx < len(options)]
                if valid_indices:
                    return [options[idx] for idx in valid_indices]
                else:
                    print("\nNo valid selections. Please try again.")
                    return self.get_selection(options, prompt, allow_exit, allow_multiple)
            except ValueError:
                print("\nInvalid selection. Please enter numbers separated by commas.")
                return self.get_selection(options, prompt, allow_exit, allow_multiple)
        else:
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
    
    def display_club_info(self, club, category=None):
        """Display information about a specific club."""
        self.print_header(f"{club['Organization Name']} Information")
        
        if category == "All Information":
            categories = ["Description", "Contact Information"]
        elif category:
            categories = [category]
        else:
            # Let user select a category
            categories = ["Description", "Contact Information", "All Information"]
            selected = self.get_selection(categories, "What information would you like to see?")
            if not selected:
                return
            
            if selected == "All Information":
                categories = ["Description", "Contact Information"]
            else:
                categories = [selected]
        
        for category in categories:
            print(f"\n{category}:")
            
            if category == "Description":
                description = club.get("Description", "No description available")
                # Split long descriptions into multiple lines for better readability
                words = description.split()
                line_length = 0
                formatted_description = ""
                
                for word in words:
                    if line_length + len(word) + 1 > 80:
                        formatted_description += "\n" + word + " "
                        line_length = len(word) + 1
                    else:
                        formatted_description += word + " "
                        line_length += len(word) + 1
                
                print(formatted_description)
            
            elif category == "Contact Information":
                print(f"ID: {club.get('ID', 'Not available')}")
                if 'Organization Name' in club:
                    print(f"Name: {club['Organization Name']}")
        
        input("\nPress Enter to continue...")
        
    def club_info_menu(self):
        """Show the club information menu."""
        while True:
            self.print_header("Club Information")
            
            # Get club names and sort alphabetically
            club_names = sorted([club["Organization Name"] for club in self.clubs])
            
            # Create a paginated menu for the clubs
            self.display_paginated_list(club_names, "clubs", self.show_club_details)
            return  # Return to main menu when user exits pagination
    
    def display_paginated_list(self, items, item_type, action_function, page_size=20):
        """Display a paginated list of items with navigation options."""
        total_items = len(items)
        print(f"Total {item_type}: {total_items}")
        
        if total_items == 0:
            print(f"\nNo {item_type} available to display.")
            input("\nPress Enter to continue...")
            return
            
        total_pages = max(1, (total_items + page_size - 1) // page_size)
        current_page = 1
        
        while True:
            start_idx = (current_page - 1) * page_size
            end_idx = min(start_idx + page_size, total_items)
            
            self.print_header(f"{item_type.title()} (Page {current_page} of {total_pages})")
            
            # Display the current page of items
            for i, item in enumerate(items[start_idx:end_idx], start_idx + 1):
                print(f"{i}. {item}")
            
            # Display navigation options
            print("\nNavigation:")
            nav_options = []
            
            if current_page > 1:
                nav_options.append("P: Previous page")
            
            if current_page < total_pages:
                nav_options.append("N: Next page")
            
            nav_options.extend([
                "G #: Go to page # (e.g., G 3)",
                "S: Search within list",
                "V #: View details for item # (e.g., V 5)",
                "B: Back to previous menu"
            ])
            
            for option in nav_options:
                print(option)
            
            choice = input("\nEnter your choice: ").strip().lower()
            
            if choice == 'b':
                return  # Exit pagination
            elif choice == 'p' and current_page > 1:
                current_page -= 1
            elif choice == 'n' and current_page < total_pages:
                current_page += 1
            elif choice.startswith('g '):
                try:
                    page_num = int(choice[2:])
                    if 1 <= page_num <= total_pages:
                        current_page = page_num
                    else:
                        print(f"Invalid page number. Please enter a number between 1 and {total_pages}.")
                except ValueError:
                    print("Invalid input. Please enter a valid page number.")
            elif choice.startswith('s'):
                search_term = input("\nEnter search term: ").strip().lower()
                filtered_items = [item for item in items if search_term in item.lower()]
                
                if filtered_items:
                    print(f"\nFound {len(filtered_items)} matches.")
                    self.display_paginated_list(filtered_items, f"matching {item_type}", action_function)
                    return  # Return to previous pagination when done with filtered list
                else:
                    print("\nNo matching items found.")
            elif choice.startswith('v '):
                try:
                    item_num = int(choice[2:])
                    if 1 <= item_num <= total_items:
                        action_function(items[item_num - 1])
                    else:
                        print(f"Invalid item number. Please enter a number between 1 and {total_items}.")
                except ValueError:
                    print("Invalid input. Please enter a valid item number.")
            else:
                print("Invalid choice. Please try again.")
    
    def show_club_details(self, club_name):
        """Show details for a club by its name."""
        selected_club = next((club for club in self.clubs if club["Organization Name"] == club_name), None)
        
        if selected_club:
            self.display_club_info(selected_club)
    
    def search_clubs(self):
        """Search for clubs with various criteria."""
        while True:
            self.print_header("Search Clubs")
            
            # Define search options
            search_options = [
                "Search by category group",
                "Search by specific category",
                "Search by keyword",
                "Search by ID"
            ]
            
            selected = self.get_selection(search_options, "How would you like to search?")
            if not selected:
                return
                
            if selected == "Search by category group":
                # Get category groups
                group_names = [group["group_name"] for group in self.category_groups]
                selected_group = self.get_selection(group_names, "Select a category group")
                if not selected_group:
                    continue
                    
                # Get all categories in the selected group
                categories_in_group = self.group_categories.get(selected_group, [])
                category_prompt = f"Select a category within {selected_group}"
                selected_category = self.get_selection(categories_in_group, category_prompt)
                
                if not selected_category:
                    continue
                
                # Get subcategories for the selected category
                subcategories = self.category_subcategories.get(selected_category, [])
                if not subcategories:
                    print(f"No subcategories found for {selected_category}.")
                    continue
                
                subcategory_prompt = f"Select a subcategory within {selected_category}"
                selected_subcategory = self.get_selection(subcategories, subcategory_prompt)
                
                if not selected_subcategory:
                    continue
                
                # Search based on the selected subcategory
                results = self.find_clubs_by_interest(selected_subcategory)
                
            elif selected == "Search by specific category":
                # Get all categories flat
                all_categories = sorted(self.all_categories)
                selected_category = self.get_selection(all_categories, "Select a category")
                if not selected_category:
                    continue
                
                # Get subcategories for the selected category
                subcategories = self.category_subcategories.get(selected_category, [])
                if not subcategories:
                    print(f"No subcategories found for {selected_category}.")
                    continue
                
                subcategory_prompt = f"Select a subcategory within {selected_category}"
                selected_subcategory = self.get_selection(subcategories, subcategory_prompt)
                
                if not selected_subcategory:
                    continue
                
                # Search based on the selected subcategory
                results = self.find_clubs_by_interest(selected_subcategory)
                
            elif selected == "Search by keyword":
                keyword = input("\nEnter a keyword to search for: ").strip()
                if not keyword:
                    print("No keyword entered.")
                    continue
                    
                results = self.find_clubs_by_keyword(keyword)
                
            elif selected == "Search by ID":
                id_input = input("\nEnter the club ID: ").strip()
                if not id_input:
                    print("No ID entered.")
                    continue
                
                try:
                    club_id = int(id_input)
                    club = next((c for c in self.clubs if int(c.get('ID', 0)) == club_id), None)
                    
                    if club:
                        self.display_club_info(club)
                        continue
                    else:
                        print(f"No club found with ID {club_id}.")
                        input("\nPress Enter to continue...")
                        continue
                except ValueError:
                    print("Invalid ID format. Please enter a number.")
                    continue
            
            if results:
                self.display_search_results(results)
            else:
                print("\nNo clubs found matching your criteria.")
                input("\nPress Enter to continue...")
    
    def find_clubs_by_interest(self, interest):
        """Find clubs that match a specific interest."""
        interest_lower = interest.lower()
        results = []
        
        for club in self.clubs:
            description = club.get("Description", "").lower()
            org_name = club.get("Organization Name", "").lower()
            
            # Check if the interest appears in the description or name
            if interest_lower in description or interest_lower in org_name:
                results.append(club)
        
        return results
    
    def find_clubs_by_keyword(self, keyword):
        """Find clubs that match a specific keyword."""
        keyword_lower = keyword.lower()
        results = []
        
        for club in self.clubs:
            description = club.get("Description", "").lower()
            org_name = club.get("Organization Name", "").lower()
            
            # Check if the keyword appears in the description or name
            if keyword_lower in description or keyword_lower in org_name:
                results.append(club)
        
        return results
    
    def display_search_results(self, results):
        """Display a list of clubs with options to view details."""
        if not results:
            print("\nNo clubs found matching your criteria.")
            input("\nPress Enter to continue...")
            return
            
        # Sort results alphabetically by club name
        sorted_results = sorted(results, key=lambda x: x.get("Organization Name", ""))
        
        # Get club names for pagination
        club_names = [club["Organization Name"] for club in sorted_results]
        
        # Create a function to show club details from search results
        def show_search_result_details(club_name):
            selected_club = next((club for club in sorted_results if club["Organization Name"] == club_name), None)
            if selected_club:
                self.display_club_info(selected_club)
        
        # Display paginated results
        self.display_paginated_list(club_names, "matching clubs", show_search_result_details)
    
    def club_matcher(self):
        """Run the club matcher feature to find the best club matches."""
        self.print_header("Club Matcher")
        
        # Initialize answers dictionary
        answers = {}
        
        # Process each matcher question
        for question_data in self.matcher_questions:
            q_id = question_data["id"]
            question = question_data["question"]
            
            # Handle dynamic options for primary_interest based on group selection
            if q_id == "primary_interest" and answers.get("category_group"):
                selected_group = answers["category_group"]
                options = self.group_categories.get(selected_group, [])
            # Handle dynamic options for subcategory_interests based on primary selection
            elif q_id == "subcategory_interests" and answers.get("primary_interest"):
                selected_category = answers["primary_interest"]
                options = self.category_subcategories.get(selected_category, [])
                select_count = question_data.get("select_count", 1)
                
                # Handle multiple selection
                selected = self.get_selection(options, question, allow_multiple=True)
                if not selected:
                    return
                
                # Limit to the specified number if too many selected
                if len(selected) > select_count:
                    selected = selected[:select_count]
                    print(f"\nLimited selection to {select_count} options: {', '.join(selected)}")
                
                answers[q_id] = selected
                continue  # Skip the regular selection logic below
            else:
                options = question_data["options"]
                if isinstance(options, str) and options == "dynamically_populated_based_on_group_selection":
                    continue  # Skip this question as it will be handled dynamically
                if isinstance(options, str) and options == "dynamically_populated_based_on_primary_selection":
                    continue  # Skip this question as it will be handled dynamically
            
            # Handle multiple selection questions
            if question_data.get("multiple", False):
                selected = self.get_selection(options, question, allow_multiple=True)
                if not selected:
                    return
            else:
                selected = self.get_selection(options, question)
                if not selected:
                    return
            
            answers[q_id] = selected
        
        print("\nAnalyzing your preferences to find the best club matches...")
        
        # Calculate matches
        club_matches = self.calculate_club_matches(answers)
        
        # Display the results
        self.display_club_recommendations(club_matches, answers)
    
    def calculate_club_matches(self, preferences):
        """Calculate club matches based on user preferences."""
        matches = []
        
        # Get user's selected interests
        selected_subcategories = preferences.get("subcategory_interests", [])
        if not isinstance(selected_subcategories, list):
            selected_subcategories = [selected_subcategories]
        
        commitment_level = preferences.get("commitment_level", "")
        schedule_preference = preferences.get("schedule_preference", [])
        if not isinstance(schedule_preference, list):
            schedule_preference = [schedule_preference]
        
        experience_level = preferences.get("experience_level", "")
        
        # Calculate match score for each club
        for club in self.clubs:
            score = 0
            match_reasons = []
            
            description = club.get("Description", "").lower()
            org_name = club.get("Organization Name", "").lower()
            
            # Check for matches with selected subcategories
            for subcategory in selected_subcategories:
                subcategory_lower = subcategory.lower()
                if subcategory_lower in description or subcategory_lower in org_name:
                    score += 2
                    match_reasons.append(f"Matches your interest in {subcategory}")
                elif any(word in description for word in subcategory_lower.split()):
                    score += 1
                    match_reasons.append(f"Partially matches your interest in {subcategory}")
            
            # Additional scoring based on commitment level
            if commitment_level:
                commitment_keywords = {
                    "Casual interest (1-2 hours/week)": ["casual", "informal", "social", "occasional"],
                    "Regular involvement (3-5 hours/week)": ["regular", "weekly", "meetings", "participate"],
                    "Dedicated participation (6-10 hours/week)": ["dedicated", "commitment", "competitive", "events"],
                    "Leadership role (10+ hours/week)": ["leadership", "executive", "organize", "manage"]
                }
                
                for keyword in commitment_keywords.get(commitment_level, []):
                    if keyword in description.lower():
                        score += 1
                        match_reasons.append(f"Matches your {commitment_level} preference")
                        break
            
            # Only include clubs with a positive match score
            if score > 0:
                matches.append({
                    "club": club,
                    "score": score,
                    "reasons": match_reasons[:3]  # Limit to top 3 reasons
                })
        
        # Sort by score (descending)
        matches.sort(key=lambda x: x["score"], reverse=True)
        
        return matches
    
    def display_club_recommendations(self, matches, preferences):
        """Display club recommendations based on user preferences."""
        self.print_header("Club Recommendations")
        
        if not matches:
            print("Sorry, I couldn't find any clubs matching your preferences.")
            input("\nPress Enter to continue...")
            return
        
        # Display preference summary
        print("Based on your preferences:")
        primary_interest = preferences.get("primary_interest", "Not specified")
        print(f"- Primary Interest: {primary_interest}")
        
        subcategories = preferences.get("subcategory_interests", [])
        if isinstance(subcategories, list) and subcategories:
            print(f"- Specific Interests: {', '.join(subcategories)}")
        
        commitment = preferences.get("commitment_level", "Not specified")
        print(f"- Commitment Level: {commitment}")
        
        schedule = preferences.get("schedule_preference", [])
        if isinstance(schedule, list) and schedule:
            print(f"- Schedule Preference: {', '.join(schedule)}")
        
        experience = preferences.get("experience_level", "Not specified")
        print(f"- Experience Level: {experience}")
        
        print("\nHere are your top matches:\n")
        
        # Show top 10 matches or fewer if there aren't that many
        top_matches = matches[:min(10, len(matches))]
        
        for i, match in enumerate(top_matches, 1):
            club = match["club"]
            score = match["score"]
            reasons = match["reasons"]
            
            print(f"{i}. {club['Organization Name']}")
            print(f"   Match Score: {score}")
            
            if reasons:
                print("   Why this is a good match:")
                for reason in reasons:
                    print(f"   - {reason}")
            
            print()
        
        # Options for further action
        while True:
            print("\nOptions:")
            print("V #: View detailed information for recommendation # (e.g., V 1)")
            print("S: Show more recommendations")
            print("B: Back to main menu")
            
            choice = input("\nEnter your choice: ").strip().lower()
            
            if choice == 'b':
                return
            elif choice == 's' and len(matches) > 10:
                # Show the next 10 matches
                next_matches = matches[10:min(20, len(matches))]
                
                if next_matches:
                    print("\nMore recommendations:\n")
                    
                    for i, match in enumerate(next_matches, 11):
                        club = match["club"]
                        score = match["score"]
                        reasons = match["reasons"]
                        
                        print(f"{i}. {club['Organization Name']}")
                        print(f"   Match Score: {score}")
                        
                        if reasons:
                            print("   Why this is a good match:")
                            for reason in reasons:
                                print(f"   - {reason}")
                        
                        print()
                else:
                    print("\nNo more recommendations available.")
            elif choice.startswith('v '):
                try:
                    match_num = int(choice[2:]) - 1
                    if 0 <= match_num < len(matches):
                        self.display_club_info(matches[match_num]["club"])
                    else:
                        print("Invalid recommendation number.")
                except ValueError:
                    print("Invalid input. Please enter a valid number.")
            else:
                print("Invalid choice. Please try again.")
    
    def getting_involved(self):
        """Display information about getting involved in clubs."""
        self.print_header("Getting Involved in UF Clubs")
        
        print("How to Get Involved in UF Organizations:\n")
        
        print("1. Explore and Research")
        print("   - Browse organizations through this system or GatorConnect")
        print("   - Attend the Student Organization Fair at the beginning of each semester")
        print("   - Visit organization websites and social media pages\n")
        
        print("2. Attend Meetings and Events")
        print("   - Most organizations welcome new members to their general meetings")
        print("   - Check GatorConnect or organization social media for meeting times and locations")
        print("   - Attend interest meetings at the beginning of the semester\n")
        
        print("3. Application and Membership Process")
        print("   - Some organizations require applications or have selective membership")
        print("   - Professional and Greek organizations may have formal recruitment processes")
        print("   - Check specific organizations for their membership requirements\n")
        
        print("4. Benefits of Joining")
        print("   - Develop leadership skills and gain valuable experience")
        print("   - Build your network and make new friends")
        print("   - Enhance your resume with extracurricular involvement")
        print("   - Contribute to the campus and local community\n")
        
        print("5. Resources for Student Organizations")
        print("   - GatorConnect: https://orgs.studentinvolvement.ufl.edu/")
        print("   - Student Activities and Involvement: https://studentinvolvement.ufl.edu/")
        print("   - Reitz Union Student Activities Resource Center\n")
        
        input("Press Enter to continue...")
    
    def main_menu(self):
        """Display the main menu."""
        while True:
            self.print_header("UF Club Selection System")
            
            options = [
                "Browse All Clubs",
                "Search Clubs",
                "Club Matcher",
                "Getting Involved"
            ]
            
            selected = self.get_selection(options, "Main Menu", allow_exit=True)
            
            if selected == "Browse All Clubs":
                self.club_info_menu()
            elif selected == "Search Clubs":
                self.search_clubs()
            elif selected == "Club Matcher":
                self.club_matcher()
            elif selected == "Getting Involved":
                self.getting_involved()

    def exit_program(self):
        """Exit the program."""
        self.print_header("Thank You")
        print("Thank you for using the UF Club Selection System!")
        print("\nExiting program...")
        sys.exit(0)
        
    def run(self):
        """Run the club system."""
        try:
            self.main_menu()
        except KeyboardInterrupt:
            self.exit_program()


if __name__ == "__main__":
    system = ClubSystem()
    system.run()