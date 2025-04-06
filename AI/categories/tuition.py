#!/usr/bin/env python3
import json
import os
import sys

class TuitionCalculator:
    def __init__(self, json_data):
        """Initialize the tuition calculator with JSON data"""
        self.data = json_data
        
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
    
    def display_tuition_results(self, result):
        """Display the tuition breakdown and total cost."""
        self.print_header("Tuition Cost Breakdown")
        
        # Display the breakdown
        print("Cost Breakdown:")
        print("-" * 60)
        print(f"{'Item':<40}{'Amount':>20}")
        print("-" * 60)
        
        for item in result["breakdown"]:
            item_type = item["type"]
            amount = item["amount"]
            print(f"{item_type:<40}${amount:>19,.2f}")
        
        print("-" * 60)
        print(f"{'Total Cost':<40}${result['total']:>19,.2f}")
        print("-" * 60)
        
        # Display additional information
        print("\nNotes:")
        print("- Tuition amounts are for the full academic year (Fall and Spring semesters)")
        print("- Living expenses are based on on-campus housing and meal plan estimates")
        print("- All amounts are subject to change without notice")
        
        input("\nPress Enter to continue...")
    
    def navigate_decision_tree(self, node):
        """Navigate through the decision tree based on user selections."""
        # If we've reached a result node, display it
        if "result" in node:
            self.display_tuition_results(node["result"])
            return
        
        # Otherwise, ask the current question
        question = node["question"]
        options = [option["label"] for option in node["options"]]
        
        selected = self.get_selection(options, question)
        if not selected:
            return
        
        # Find the selected option and navigate to the next node
        for option in node["options"]:
            if option["label"] == selected:
                if "next" in option:
                    self.navigate_decision_tree(option["next"])
                elif "result" in option:
                    self.display_tuition_results(option["result"])
                break
    
    def main_menu(self):
        """Display the main menu."""
        while True:
            self.print_header(self.data["name"])
            print(self.data["description"])
            print("\nThis tool helps you estimate university costs based on your status and academic year.")
            
            options = [
                "Calculate Tuition Costs",
                "About This Calculator"
            ]
            
            selected = self.get_selection(options, "Main Menu", allow_exit=True)
            
            if selected == "Calculate Tuition Costs":
                self.navigate_decision_tree(self.data["root"])
            elif selected == "About This Calculator":
                self.show_about()
    
    def show_about(self):
        """Display information about the calculator."""
        self.print_header("About This Calculator")
        
        print("The University Tuition Cost Calculator provides estimated costs")
        print("for attending the university based on your residency status and")
        print("the academic year you plan to attend.")
        print("\nThese estimates include:")
        print("- Tuition and mandatory fees")
        print("- Books and supplies")
        print("- Transportation expenses")
        print("- Living expenses (housing and food)")
        print("- Miscellaneous personal expenses")
        print("- Any required fees like loan fees or insurance")
        
        print("\nPlease note that these are ESTIMATES and actual costs may vary")
        print("based on your specific course load, housing choices, and personal")
        print("spending habits.")
        
        input("\nPress Enter to continue...")

    def exit_program(self):
        """Exit the program."""
        self.print_header("Thank You")
        print("Thank you for using the University Tuition Cost Calculator!")
        print("\nExiting program...")
        sys.exit(0)
        
    def run(self):
        """Run the tuition calculator."""
        try:
            self.main_menu()
        except KeyboardInterrupt:
            self.exit_program()


def load_json_data(json_string):
    """Load JSON data from a string."""
    try:
        return json.loads(json_string)
    except json.JSONDecodeError as e:
        print(f"Error loading JSON data: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # You can either load from a file or use the embedded JSON data
    # Option 1: Load from a file
    with open("./jsonFiles/tuition.json", "r") as f:
        json_data = json.load(f)
    
    calculator = TuitionCalculator(json_data)
    calculator.run()