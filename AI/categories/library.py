#!/usr/bin/env python3
import json
import os
import sys
import subprocess
from pathlib import Path
import re
from collections import Counter

class LibrarySystem:
    def __init__(self, json_file):
        # Set the exact path to the Llama model
        self.llama_model_path = "/Users/emmamitchell/Desktop/GatorNet/AI/models/Meta-Llama-3-8B-Instruct-Q8_0.gguf"
        
        with open(json_file, 'r') as f:
            self.data = json.load(f)
        self.libraries = self.data["libraries"]
        self.matcher_questions = self.data["matcher_questions"]
        
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
    
    def ai_library_matcher(self):
        """Run the AI library matcher feature."""
        self.print_header("AI Library Matcher")
        
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
        print("This may take a moment...")
        
        # Use our smart matching algorithm instead of Llama
        result = self.smart_library_matcher(answers)
        
        self.print_header("AI Library Recommendation")
        print(result)
        
        input("\nPress Enter to continue...")
    
    def smart_library_matcher(self, answers):
        """Smart library matching algorithm that mimics AI recommendation."""
        purpose = answers.get('purpose')
        subject = answers.get('subject')
        features = answers.get('features')
        time = answers.get('time')
        
        # Create a scoring system for each library
        scores = {lib["name"]: 0 for lib in self.libraries}
        reasons = {lib["name"]: [] for lib in self.libraries}
        
        # Score based on subject specialization (heaviest weight)
        subject_keywords = {
            "Law": ["law", "legal", "legislation"],
            "Health Sciences/Medicine": ["health", "medical", "medicine", "nursing"],
            "Science/Technology/Engineering/Math": ["science", "engineering", "math", "technology", "stem"],
            "Architecture/Fine Arts": ["architecture", "art", "design", "fine arts"],
            "Education": ["education", "teaching", "learning"],
            "General/Humanities": ["humanities", "general", "liberal arts", "history", "literature"]
        }
        
        subject_keywords_flat = {word: subj for subj, words in subject_keywords.items() for word in words}
        
        for library in self.libraries:
            # Subject matching (0-5 points)
            specializations = " ".join(library.get("specializations", [])).lower()
            
            # Direct subject match
            if any(keyword in specializations for keyword in subject_keywords.get(subject, [])):
                scores[library["name"]] += 5
                reasons[library["name"]].append(f"Specializes in {subject}")
            else:
                # Partial match
                matching_keywords = [keyword for keyword in subject_keywords.get(subject, []) 
                                    if any(keyword in spec.lower() for spec in library.get("specializations", []))]
                if matching_keywords:
                    scores[library["name"]] += 3
                    reasons[library["name"]].append(f"Has some resources for {subject}")
            
            # Feature matching (0-3 points)
            library_features = " ".join(library.get("features", [])).lower()
            
            if features.lower() in library_features:
                scores[library["name"]] += 3
                reasons[library["name"]].append(f"Offers {features}")
            elif any(word in library_features for word in features.lower().split()):
                scores[library["name"]] += 1
                reasons[library["name"]].append(f"Has some features related to {features}")
                
            # Time availability (0-2 points)
            hours = library.get("hours", "").lower()
            
            if time == "Late night (after 10pm)":
                if "24 hours" in hours or any(hour > 22 for hour in self._extract_hours(hours)):
                    scores[library["name"]] += 2
                    reasons[library["name"]].append("Open late at night")
            elif time == "Weekends":
                if "weekend" in hours or "saturday" in hours or "sunday" in hours:
                    scores[library["name"]] += 2
                    reasons[library["name"]].append("Open on weekends")
            elif time == "Weekday daytime":
                # Most libraries are open weekdays, so just a small bonus
                scores[library["name"]] += 1
                reasons[library["name"]].append("Open during regular weekday hours")
                
            # Purpose matching (0-2 points)
            if purpose == "Research":
                if "research" in specializations or "database access" in library_features:
                    scores[library["name"]] += 2
                    reasons[library["name"]].append("Excellent for research purposes")
            elif purpose == "Study":
                if "quiet" in library_features or "study space" in library_features:
                    scores[library["name"]] += 2
                    reasons[library["name"]].append("Good study environment")
            elif purpose == "Group work":
                if "group" in library_features or "collaboration" in library_features:
                    scores[library["name"]] += 2
                    reasons[library["name"]].append("Has spaces for group collaboration")
        
        # Find the highest scoring library
        best_match = max(scores.items(), key=lambda x: x[1])[0]
        
        # In case of a tie, prefer libraries with higher capacity
        tied_libraries = [lib for lib, score in scores.items() if score == scores[best_match]]
        if len(tied_libraries) > 1:
            capacities = {}
            for lib_name in tied_libraries:
                library = next((lib for lib in self.libraries if lib["name"] == lib_name), None)
                capacity_value = library.get("capacity", "0")
                
                # Fix for the bug: handle both string and integer capacity values
                if isinstance(capacity_value, int):
                    capacity = capacity_value
                else:
                    # Try to extract digits from the string
                    try:
                        digits = ''.join(filter(str.isdigit, str(capacity_value)))
                        capacity = int(digits) if digits else 0
                    except:
                        capacity = 0
                
                capacities[lib_name] = capacity
            
            if any(capacities.values()):  # If we have any capacity data
                best_match = max(capacities.items(), key=lambda x: x[1])[0]
        
        # Get the library details
        library = next((lib for lib in self.libraries if lib["name"] == best_match), None)
        
        # Format a response that mimics an AI response
        response = f"Based on your preferences, I recommend **{best_match}**.\n\n"
        
        response += "**Analysis of your preferences:**\n"
        response += f"- Purpose: {purpose}\n"
        response += f"- Subject: {subject}\n"
        response += f"- Desired Features: {features}\n"
        response += f"- Visit Time: {time}\n\n"
        
        response += "**Why this is a good match:**\n"
        # Include the top 3 reasons
        top_reasons = sorted(reasons[best_match], key=lambda x: len(x), reverse=True)[:3]
        for reason in top_reasons:
            response += f"- {reason}\n"
        
        if library:
            response += f"\n**About {best_match}:**\n"
            response += f"- Location: {library.get('location', 'Not specified')}\n"
            response += f"- Hours: {library.get('hours', 'Not specified')}\n"
            
            # Add specializations
            specializations = library.get("specializations", [])
            if specializations:
                response += f"- Specializes in: {', '.join(specializations[:3])}"
                if len(specializations) > 3:
                    response += f" and {len(specializations) - 3} more areas"
                response += "\n"
            
            # Add features
            features_list = library.get("features", [])
            if features_list:
                response += f"- Features: {', '.join(features_list[:3])}"
                if len(features_list) > 3:
                    response += f" and {len(features_list) - 3} more"
                response += "\n"
                
            # Special notes for time preference
            if time == "Late night (after 10pm)" and "Library West" in best_match:
                response += "\n**Special Note:** For late night access to Library West, you'll need an active UF ID or Santa Fe College ID."
        
        # Add alternatives
        second_best = None
        for lib, score in sorted(scores.items(), key=lambda x: x[1], reverse=True):
            if lib != best_match:
                second_best = lib
                break
                
        if second_best:
            response += f"\n\n**Alternative Option:**\nIf {best_match} doesn't work for you, consider {second_best} as an alternative."
            
        return response
    
    def _extract_hours(self, hours_text):
        """Extract hour numbers from hours text."""
        # Handle case when hours_text might not be a string
        if not isinstance(hours_text, str):
            return []
            
        # Simple regex to find time patterns like 8am, 10pm, etc.
        time_patterns = re.findall(r'(\d+)(?::\d+)?\s*(am|pm|a\.m\.|p\.m\.)', hours_text, re.IGNORECASE)
        
        hour_values = []
        for hour, meridiem in time_patterns:
            hour_val = int(hour)
            if any(m in meridiem.lower() for m in ['pm', 'p.m.']):
                if hour_val != 12:  # 12pm is already noon
                    hour_val += 12
            elif any(m in meridiem.lower() for m in ['am', 'a.m.']) and hour_val == 12:
                hour_val = 0  # 12am is midnight
                
            hour_values.append(hour_val)
            
        return hour_values
    
    def main_menu(self):
        """Display the main menu."""
        while True:
            self.print_header("UF Libraries Information System")
            
            options = [
                "Get Library Info",
                "AI Library Matcher"
            ]
            
            selected = self.get_selection(options, "Main Menu", allow_exit=True)
            
            if selected == "Get Library Info":
                self.library_info_menu()
            elif selected == "AI Library Matcher":
                self.ai_library_matcher()
        
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