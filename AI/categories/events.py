import json
import os
import sys

class CampusEventSystem:
    def __init__(self, json_file):
        with open(json_file, 'r') as f:
            self.data = json.load(f)
        self.events = self.data["events"]
        self.matcher_questions = self.data["matcher_questions"]
        self.faqs = self.data["faqs"]

    def display_event_info(self, event_name):
        event = next((e for e in self.events if e["name"].lower() == event_name.lower()), None)
        if event:
            print(f"\nEvent: {event['name']}")
            print(f"Type: {event['type']}")
            print(f"Location: {event['location']}")
            print(f"Time: {event['time']}")
            print(f"Description: {event['description']}")
        else:
            print("Event not found. Please check the name or spelling.")

    def event_recommendation(self):
        answers = {}
        for question_data in self.matcher_questions:
            q_id = question_data["id"]
            question = question_data["question"]
            options = question_data["options"]

            selected = self.get_selection(options, question)
            if not selected:
                return
            answers[q_id] = selected

        # Simple recommendation logic
        matched_events = []
        for event in self.events:
            if answers["interest"] == event["type"] or answers["location_preference"] in [event["location"], "No preference"]:
                matched_events.append(event)

        if matched_events:
            print("\nRecommended Events:")
            for event in matched_events:
                self.display_event_info(event["name"])
        else:
            print("\nNo matching events found. Try adjusting your preferences.")

    def get_selection(self, options, prompt="Select an option", allow_exit=True):
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

    def display_faqs(self):
        print("\nFrequently Asked Questions:")
        for faq in self.faqs:
            print(f"\nQ: {faq['question']}")
            print(f"A: {faq['answer']}")

    def main_menu(self):
        while True:
            print("\n===== UF Campus Events System =====")
            options = [
                "Find Event Info",
                "Get Event Recommendations",
                "View Event FAQs"
            ]
            selected = self.get_selection(options, "Main Menu", allow_exit=True)

            if selected == "Find Event Info":
                event_name = input("\nEnter event name: ")
                self.display_event_info(event_name)
            elif selected == "Get Event Recommendations":
                self.event_recommendation()
            elif selected == "View Event FAQs":
                self.display_faqs()

    def exit_program(self):
        print("\nThank you for using the UF Campus Events System!")
        sys.exit(0)

if __name__ == "__main__":
    json_file = "campus_events.json"
    system = CampusEventSystem(json_file)
    system.main_menu()
