#!/usr/bin/env python3
import json
import os
import sys
import re
from collections import Counter

class LibrarySystem:
    def __init__(self, json_file):
        try:
            with open(json_file, 'r') as f:
                self.data = json.load(f)
            self.libraries = self.data["libraries"]
            self.matcher_questions = self.data["matcher_questions"]
        except FileNotFoundError:
            print(f"Error: Could not find the JSON file '{json_file}'")
            sys.exit(1)
        except json.JSONDecodeError:
            print(f"Error: '{json_file}' is not a valid JSON file")
            sys.exit(1)
        
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
    
    def display_library_info(self, library, category=None):
        """Display information about a specific library."""
        self.print_header(f"{library['name']} Information")
        
        if category == "All Information":
            categories = ["Location", "Capacity", "Hours", "Special Notes", "URL", "Phone", "Email", "Features", "Specializations"]
        elif category:
            categories = [category]
        else:
            # Let user select a category
            categories = ["Location", "Capacity", "Hours", "Special Notes", "URL", "Phone", "Email", "Features", "Specializations", "All Information"]
            selected = self.get_selection(categories, "What information would you like to see?")
            if not selected:
                return
            
            if selected == "All Information":
                categories = ["Location", "Capacity", "Hours", "Special Notes", "URL", "Phone", "Email", "Features", "Specializations"]
            else:
                categories = [selected]
        
        for category in categories:
            print(f"\n{category}:")
            if category.lower() == "features":
                for item in library.get("features", ["No information available"]):
                    print(f"- {item}")
            elif category.lower() == "specializations":
                for item in library.get("specializations", ["No information available"]):
                    print(f"- {item}")
            else:
                key = category.lower().replace(" ", "_")
                value = library.get(key, "No information available")
                if value is None:
                    value = "Information not available"
                print(f"{value}")
        
        input("\nPress Enter to continue...")
        
    def library_info_menu(self):
        """Show the library information menu."""
        while True:
            self.print_header("Library Information")
            
            # Get library names
            library_names = [lib["name"] for lib in self.libraries]
            
            # Let user select a library
            selected_library_name = self.get_selection(library_names, "Select a library for more information")
            if not selected_library_name:
                return
                
            # Find the selected library
            selected_library = next((lib for lib in self.libraries if lib["name"] == selected_library_name), None)
            
            if selected_library:
                self.display_library_info(selected_library)
    
    def library_matcher(self):
        """Run the library matcher feature using intelligent hardcoded criteria."""
        self.print_header("Library Matcher")
        
        # Get answers to all questions
        answers = {}
        for question_data in self.matcher_questions:
            q_id = question_data["id"]
            question = question_data["question"]
            options = question_data["options"]
            
            selected = self.get_selection(options, question)
            if not selected:
                return
                
            answers[q_id] = selected
        
        print("\nAnalyzing your preferences to find the best library match...")
        
        # Calculate matches and scores
        library_scores, reasons = self.calculate_library_scores(answers)
        
        # Find the best library match
        best_match = self.get_best_library_match(library_scores, reasons)
        
        # Display the results
        self.display_library_recommendation(best_match, answers, library_scores, reasons)
        
    def calculate_library_scores(self, preferences):
        """Calculate scores for each library based on user preferences."""
        scores = {lib["name"]: 0 for lib in self.libraries}
        reasons = {lib["name"]: [] for lib in self.libraries}
        
        purpose = preferences.get('purpose', '')
        subject = preferences.get('subject', '')
        desired_features = preferences.get('features', '')
        visit_time = preferences.get('time', '')
        
        # Define purpose keywords mapping
        purpose_keywords = {
            "General study": ["study spaces", "quiet study", "study areas"],
            "Research": ["research assistance", "special collections", "reference"],
            "Group project": ["group study", "collaboration", "group spaces"],
            "Access special collections": ["rare books", "archives", "special collections"],
            "Use specialized equipment": ["makerspace", "equipment", "computers", "technology"],
            "Quiet reading": ["quiet", "reading", "quiet areas"]
        }
        
        # Define subject keywords mapping
        subject_keywords = {
            "General/Humanities": ["general", "humanities", "history", "literature", "philosophy"],
            "Science/Technology/Engineering/Math": ["science", "technology", "engineering", "mathematics", "stem"],
            "Health Sciences/Medicine": ["health", "medical", "medicine", "nursing", "pharmacy"],
            "Law": ["law", "legal", "government"],
            "Architecture/Fine Arts": ["architecture", "fine arts", "design", "art", "visual"],
            "Education": ["education", "teaching", "learning", "educational"]
        }
        
        # Score each library
        for library in self.libraries:
            # Score based on subject specialization (weight: 0-5 points)
            specializations = " ".join(library.get("specializations", [])).lower()
            features_list = library.get("features", [])
            features_text = " ".join(features_list).lower()
            
            # 1. Subject matching (0-5 points)
            subject_match_score = 0
            
            # Direct subject match with specializations
            if any(keyword in specializations for keyword in subject_keywords.get(subject, [])):
                subject_match_score = 5
                reasons[library["name"]].append(f"Specializes in {subject}")
            # Partial match with specializations
            elif any(subj_term in specializations for subj_term in subject.lower().split("/")):
                subject_match_score = 3
                reasons[library["name"]].append(f"Has relevant resources for {subject}")
            
            scores[library["name"]] += subject_match_score
            
            # 2. Purpose matching (0-3 points)
            purpose_match_score = 0
            purpose_keywords_list = purpose_keywords.get(purpose, [])
            
            if any(keyword in features_text for keyword in purpose_keywords_list):
                purpose_match_score = 3
                reasons[library["name"]].append(f"Excellent for {purpose.lower()}")
            # Check special cases
            elif purpose == "Research" and "research assistance" in features_list:
                purpose_match_score = 3
                reasons[library["name"]].append("Provides research assistance")
            elif purpose == "Group project" and "group study rooms" in features_list:
                purpose_match_score = 3
                reasons[library["name"]].append("Has group study rooms")
            elif purpose == "Quiet reading" and "quiet study areas" in features_list:
                purpose_match_score = 3
                reasons[library["name"]].append("Has quiet study areas")
            
            scores[library["name"]] += purpose_match_score
            
            # 3. Specific features matching (0-4 points)
            feature_match_score = 0
            
            # Direct match with the desired feature
            if desired_features == "Group study spaces" and "group study rooms" in features_list:
                feature_match_score = 4
                reasons[library["name"]].append("Has dedicated group study rooms")
            elif desired_features == "Quiet study areas" and "quiet study areas" in features_list:
                feature_match_score = 4
                reasons[library["name"]].append("Has designated quiet study areas")
            elif desired_features == "Special collections access" and any("special collections" in feature.lower() for feature in features_list):
                feature_match_score = 4
                reasons[library["name"]].append("Provides access to special collections")
            elif desired_features == "Computers and technology" and "computers" in features_list:
                feature_match_score = 4
                reasons[library["name"]].append("Offers computer and technology resources")
            elif desired_features == "Research assistance" and "research assistance" in features_list:
                feature_match_score = 4
                reasons[library["name"]].append("Provides dedicated research assistance")
            elif desired_features == "Large capacity" and library.get("capacity") and self._is_large_capacity(library.get("capacity")):
                feature_match_score = 4
                reasons[library["name"]].append("Has large seating capacity")
            
            scores[library["name"]] += feature_match_score
            
            # 4. Time availability matching (0-2 points)
            time_match_score = 0
            hours = library.get("hours", "").lower()
            
            if visit_time == "Late night (after 10pm)" and ("2am" in hours or "24" in hours):
                time_match_score = 2
                reasons[library["name"]].append("Open late at night")
            elif visit_time == "Weekend" and any(day in hours for day in ["sat", "sun", "weekend"]):
                time_match_score = 2
                reasons[library["name"]].append("Open on weekends")
            elif visit_time == "Weekday daytime":
                # Most libraries are open weekdays, so everyone gets this
                time_match_score = 1
            elif visit_time == "Weekday evening (after 5pm)" and any(term in hours for term in ["10pm", "evening", "night"]):
                time_match_score = 2
                reasons[library["name"]].append("Open during evening hours")
            
            scores[library["name"]] += time_match_score
            
            # 5. Special bonuses for specific combinations (0-2 points)
            if "special collections" in specializations and purpose == "Access special collections":
                scores[library["name"]] += 2
                reasons[library["name"]].append("Specializes in rare and special collections")
                
            if "makerspace" in features_text and purpose == "Use specialized equipment":
                scores[library["name"]] += 2
                reasons[library["name"]].append("Has a makerspace with specialized equipment")
                
            if "health" in specializations and subject == "Health Sciences/Medicine":
                scores[library["name"]] += 1
                reasons[library["name"]].append("Dedicated to health sciences resources")
                
            if "law" in specializations and subject == "Law":
                scores[library["name"]] += 1
                reasons[library["name"]].append("Specializes in legal resources")
        
        return scores, reasons
    
    def _is_large_capacity(self, capacity):
        """Determine if a library has large capacity."""
        if capacity is None:
            return False
            
        # If it's already a number, use it directly
        if isinstance(capacity, int):
            return capacity > 1000
            
        # Try to extract a number from a string
        try:
            if isinstance(capacity, str):
                # Extract digits
                digits = ''.join(filter(str.isdigit, capacity))
                if digits:
                    return int(digits) > 1000
            return False
        except:
            return False
        
    def get_best_library_match(self, scores, reasons):
        """Find the best library match based on scores."""
        # Find the highest scoring library(s)
        max_score = max(scores.values())
        best_matches = [lib for lib, score in scores.items() if score == max_score]
        
        # If there's a tie, prefer libraries with more reasons
        if len(best_matches) > 1:
            reason_counts = {lib: len(reasons[lib]) for lib in best_matches}
            most_reasons = max(reason_counts.values())
            best_matches = [lib for lib, count in reason_counts.items() if count == most_reasons]
        
        # If still tied, prefer libraries with higher capacity
        if len(best_matches) > 1:
            capacities = {}
            for lib_name in best_matches:
                library = next((lib for lib in self.libraries if lib["name"] == lib_name), None)
                capacity = library.get("capacity")
                
                # Handle various capacity formats
                if isinstance(capacity, int):
                    capacities[lib_name] = capacity
                elif isinstance(capacity, str) and capacity.isdigit():
                    capacities[lib_name] = int(capacity)
                else:
                    capacities[lib_name] = 0
            
            if any(capacities.values()):  # If we have any capacity data
                best_match = max(capacities.items(), key=lambda x: x[1])[0]
            else:
                # If no capacity data, just take the first match
                best_match = best_matches[0]
        else:
            best_match = best_matches[0]
            
        return best_match
        
    def display_library_recommendation(self, best_match, preferences, scores, reasons):
        """Display the library recommendation with reasoning."""
        self.print_header("Library Recommendation")
        
        # Get the library details
        library = next((lib for lib in self.libraries if lib["name"] == best_match), None)
        
        if not library:
            print("Sorry, I couldn't find a matching library.")
            input("\nPress Enter to continue...")
            return
            
        # Format and display the recommendation
        print(f"Based on your preferences, I recommend **{best_match}**.\n")
        
        print("Analysis of your preferences:")
        print(f"- Purpose: {preferences.get('purpose', 'Not specified')}")
        print(f"- Subject: {preferences.get('subject', 'Not specified')}")
        print(f"- Desired Features: {preferences.get('features', 'Not specified')}")
        print(f"- Visit Time: {preferences.get('time', 'Not specified')}\n")
        
        print(f"Match Score: {scores[best_match]}/14")
        
        print("\nWhy this is a good match:")
        # Include the top 3 reasons (or all if fewer than 3)
        top_reasons = reasons[best_match][:3]
        for reason in top_reasons:
            print(f"- {reason}")
        
        print(f"\nAbout {best_match}:")
        print(f"- Location: {library.get('location', 'Not specified')}")
        print(f"- Hours: {library.get('hours', 'Not specified')}")
        
        # Add specializations
        specializations = library.get("specializations", [])
        if specializations:
            print(f"- Specializes in: {', '.join(specializations[:3])}", end="")
            if len(specializations) > 3:
                print(f" and {len(specializations) - 3} more areas")
            else:
                print()
        
        # Add features
        features_list = library.get("features", [])
        if features_list:
            print(f"- Features: {', '.join(features_list[:3])}", end="")
            if len(features_list) > 3:
                print(f" and {len(features_list) - 3} more")
            else:
                print()
            
        # Special notes for time preference
        if preferences.get('time') == "Late night (after 10pm)" and "Library West" in best_match:
            print("\nSpecial Note: For late night access to Library West, you'll need an active UF ID or Santa Fe College ID.")
        
        # Find second best match for alternative
        second_best = None
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        for lib, score in sorted_scores:
            if lib != best_match:
                second_best = lib
                break
                
        if second_best:
            print(f"\nAlternative Option:")
            print(f"If {best_match} doesn't work for you, consider {second_best} as an alternative.")
            print(f"(Match score: {scores[second_best]}/14)")
            
        input("\nPress Enter to continue...")
    
    def main_menu(self):
        """Display the main menu."""
        while True:
            self.print_header("UF Libraries Information System")
            
            options = [
                "Get Library Info",
                "Library Matcher"
            ]
            
            selected = self.get_selection(options, "Main Menu", allow_exit=True)
            
            if selected == "Get Library Info":
                self.library_info_menu()
            elif selected == "Library Matcher":
                self.library_matcher()
        
    def exit_program(self):
        """Exit the program."""
        self.print_header("Thank You")
        print("Thank you for using the UF Libraries Information System!")
        print("\nExiting program...")
        sys.exit(0)
        
    def run(self):
        """Run the library system."""
        try:
            self.main_menu()
        except KeyboardInterrupt:
            self.exit_program()

if __name__ == "__main__":
    # Get the path to the script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    json_file = os.path.join(script_dir, "jsonfiles/lib.json")
    
    # Initialize and run the system
    system = LibrarySystem(json_file)
    system.run()