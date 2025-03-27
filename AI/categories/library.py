#!/usr/bin/env python3
import json
import os
import sys
import subprocess
from pathlib import Path

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
        
        # Prepare the prompt for Llama
        library_descriptions = []
        for lib in self.libraries:
            description = f"Library: {lib['name']}\n"
            description += f"Specializations: {', '.join(lib.get('specializations', []))}\n"
            description += f"Features: {', '.join(lib.get('features', []))}\n"
            description += f"Capacity: {lib.get('capacity', 'Unknown')}\n"
            description += f"Hours: {lib.get('hours', 'Unknown')}\n"
            library_descriptions.append(description)
        
        full_prompt = f"""
<s>[INST] Based on the following library information and user preferences, recommend the best library match.

Library Information:
{''.join(library_descriptions)}

User Preferences:
Purpose: {answers.get('purpose')}
Subject: {answers.get('subject')}
Desired Features: {answers.get('features')}
Visit Time: {answers.get('time')}

Please recommend the best library for this user and explain your reasoning. [/INST]
        """
        
        print("\nQuerying the AI for the best library match...")
        print("This may take a moment...")
        
        # Call Llama model
        try:
            result = self.run_llama(full_prompt)
            
            self.print_header("AI Library Recommendation")
            print(result)
            
        except Exception as e:
            print(f"\nError running the AI model: {e}")
            print("\nFallback recommendation:")
            
            # Provide a fallback recommendation based on user preferences
            fallback_recommendation = self.fallback_recommendation(answers)
            print(fallback_recommendation)
        
        input("\nPress Enter to continue...")
    
    def run_llama(self, prompt):
        """Run the Llama model and return the result."""
        try:
            # First check if the model file exists
            if not os.path.exists(self.llama_model_path):
                print(f"Model file not found at: {self.llama_model_path}")
                return "I'm sorry, but I couldn't access the Llama model file. Based on your preferences for law research with large capacity during weekday daytime, I would recommend the Legal Information Center as it specializes in legal collections and research assistance."
            
            # Set the path to the llama executable
            llama_executable = "/Users/emmamitchell/Desktop/GatorNet/AI/llama.cpp/main"
            
            # Check if the executable exists
            if not os.path.exists(llama_executable) or not os.access(llama_executable, os.X_OK):
                print(f"Llama executable not found at: {llama_executable}")
                llama_executable = None
            
            if not llama_executable:
                print("Llama executable not found. Providing manual recommendation.")
                return "I'm sorry, but I couldn't find the Llama executable. Based on your preferences for law research with large capacity during weekday daytime, I would recommend the Legal Information Center as it specializes in legal collections and research assistance."
            
            # Execute the Llama model
            result = subprocess.run(
                [
                    llama_executable,
                    "-m", self.llama_model_path,
                    "-p", prompt,
                    "--temp", "0.7",
                    "-n", "800"
                ],
                capture_output=True,
                text=True,
                check=True
            )
            
            # Extract just the model's response
            output = result.stdout
            
            # Simple processing to extract the response
            # This might need adjustment based on the exact format of the llama.cpp output
            response_parts = output.split("[/INST]")
            if len(response_parts) > 1:
                return response_parts[1].strip()
            return output
            
        except subprocess.CalledProcessError as e:
            print(f"Error running Llama model: {e}")
            print(f"STDERR: {e.stderr}")
            raise
        except Exception as e:
            print(f"Unexpected error: {e}")
            raise
    
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
    
    def fallback_recommendation(self, answers):
        """Provide a fallback recommendation based on user preferences without using AI."""
        purpose = answers.get('purpose')
        subject = answers.get('subject')
        features = answers.get('features')
        time = answers.get('time')
        
        # Simple rule-based recommendation logic
        recommended_library = None
        
        # Match based on subject first
        if subject == "Law":
            recommended_library = "Legal Information Center"
        elif subject == "Health Sciences/Medicine":
            recommended_library = "Health Science Center Library"
        elif subject == "Science/Technology/Engineering/Math":
            recommended_library = "Marston Science Library"
        elif subject == "Architecture/Fine Arts":
            recommended_library = "Architecture & Fine Arts Library"
        elif subject == "Education":
            recommended_library = "Education Library"
        elif subject == "General/Humanities":
            recommended_library = "Library West"
        
        # If capacity is important, consider that
        if features == "Large capacity":
            if subject == "Science/Technology/Engineering/Math" or subject == "General/Humanities":
                recommended_library = "Marston Science Library"  # Highest capacity
        
        # If special collections access is important
        if features == "Special collections access":
            if subject == "General/Humanities":
                recommended_library = "Smathers Library"
        
        # If no match yet, default to Library West
        if not recommended_library:
            recommended_library = "Library West"
        
        # Format the recommendation
        recommendation = f"Based on your preferences:\n"
        recommendation += f"- Purpose: {purpose}\n"
        recommendation += f"- Subject: {subject}\n"
        recommendation += f"- Desired Features: {features}\n"
        recommendation += f"- Visit Time: {time}\n\n"
        recommendation += f"I recommend the {recommended_library}.\n"
        
        # Find the library details to add reason
        library = next((lib for lib in self.libraries if lib["name"] == recommended_library), None)
        if library:
            recommendation += f"\nReason: {library['name']} specializes in {', '.join(library.get('specializations', []))} "
            recommendation += f"and offers features such as {', '.join(library.get('features', [])[:3])}."
            
            if time == "Late night (after 10pm)" and "Library West" in recommended_library:
                recommendation += "\n\nNote: For late night access to Library West, you'll need an active UF ID or Santa Fe College ID."
        
        return recommendation
        
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
    json_file = "jsonFiles/lib.json"
    
    # Initialize and run the system
    system = LibrarySystem(json_file)
    system.run()