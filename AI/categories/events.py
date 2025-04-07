import json
import os
import sys
import datetime
from datetime import datetime as dt


class EventsSystem:
    def __init__(self, json_file=None, events_data=None):
        """Initialize with either a JSON file or direct events data"""
        if json_file and os.path.exists(json_file):
            with open(json_file, "r") as f:
                self.data = json.load(f)
                self.events = self.data.get("events", [])
        elif events_data:
            # Load data directly from provided dictionary
            self.events = events_data.get("events", [])
        else:
            self.events = []
            
        # Sort events by date and time
        self.sort_events()
        
        # Create category mappings
        self.build_mappings()
    
    def sort_events(self):
        """Sort events by date and time"""
        def event_sort_key(event):
            event_date = event.get("date", "9999-12-31")
            event_time = event.get("time", "23:59")
            if event_time == "":
                event_time = "00:00"
            return (event_date, event_time)
            
        self.events = sorted(self.events, key=event_sort_key)
    
    def build_mappings(self):
        """Build mappings for categories and filters"""
        # Extract unique event types based on naming patterns
        self.event_types = set()
        self.locations = set()
        self.dates = set()
        
        for event in self.events:
            # Extract event types based on common naming patterns
            name = event.get("name", "").lower()
            
            if "vs" in name or "at" in name or "sport" in name:
                self.event_types.add("Sports")
            elif "seminar" in name or "colloquium" in name or "lecture" in name:
                self.event_types.add("Academic")
            elif "concert" in name or "music" in name or "performance" in name or "theatre" in name or "dance" in name:
                self.event_types.add("Arts & Culture")
            elif "workshop" in name or "training" in name:
                self.event_types.add("Workshops & Training")
            elif "conference" in name or "symposium" in name:
                self.event_types.add("Conferences")
            
            # Extract locations
            location = event.get("location", "")
            if location:
                self.locations.add(location)
            
            # Extract dates (by month)
            date = event.get("date", "")
            if date:
                try:
                    date_obj = dt.strptime(date, "%Y-%m-%d")
                    month_name = date_obj.strftime("%B %Y")
                    self.event_types.add(month_name)
                    self.dates.add(date)
                except ValueError:
                    pass
        
        # Convert sets to sorted lists
        self.event_types = sorted(list(self.event_types))
        self.locations = sorted(list(self.locations))
        self.dates = sorted(list(self.dates))
        
        # Create time of day mapping
        self.time_mapping = {
            "Morning (before 12pm)": lambda time: time and (time.endswith("am") or time.startswith("1") and not time.startswith("1:") and not time.startswith("10") and not time.startswith("11")),
            "Afternoon (12pm-5pm)": lambda time: time and (time.endswith("pm") and (time.startswith("12") or time.startswith("1") or time.startswith("2") or time.startswith("3") or time.startswith("4") or time.startswith("5"))),
            "Evening (after 5pm)": lambda time: time and (time.endswith("pm") and (time.startswith("6") or time.startswith("7") or time.startswith("8") or time.startswith("9") or time.startswith("10") or time.startswith("11")))
        }

    def display_event_info(self, event_index):
        """Display detailed information for a specific event."""
        if 0 <= event_index < len(self.events):
            event = self.events[event_index]
            print(f"\nEvent: {event.get('name', 'Unnamed Event')}")
            print(f"Date: {event.get('date', 'No date specified')}")
            
            time = event.get('time', '')
            if time:
                print(f"Time: {time}")
            
            location = event.get('location', '')
            if location:
                print(f"Location: {location}")
            
            description = event.get('description', '')
            if description:
                print(f"\nDescription: {description}")
            
            link = event.get('link', '')
            if link:
                print(f"\nEvent Link: {link}")
            
            input("\nPress Enter to continue...")
        else:
            print("Event not found. Please check the event number.")

    def search_events(self):
        """Search for events with flexible search options"""
        print("\n===== Event Search =====")
        print("1. Search by keyword")
        print("2. Search by date")
        print("3. Search by location")
        print("4. Search by time of day")
        print("0. Back to main menu")
        
        choice = input("\nEnter your choice: ").strip()
        
        if choice == "0":
            return
        elif choice == "1":
            search_term = input("Enter keyword to search: ").strip().lower()
            results = [e for e in self.events if search_term in e.get("name", "").lower() or 
                      search_term in e.get("description", "").lower()]
        elif choice == "2":
            print("\nEnter date in format YYYY-MM-DD (e.g., 2025-04-15)")
            search_date = input("Date: ").strip()
            results = [e for e in self.events if e.get("date", "") == search_date]
        elif choice == "3":
            # Show list of available locations
            if not self.locations:
                print("No location information available.")
                return
                
            print("\nAvailable locations:")
            for i, location in enumerate(self.locations, 1):
                print(f"{i}. {location}")
            
            try:
                loc_idx = int(input("\nSelect location number: ").strip()) - 1
                if 0 <= loc_idx < len(self.locations):
                    search_location = self.locations[loc_idx]
                    results = [e for e in self.events if e.get("location", "") == search_location]
                else:
                    print("Invalid selection.")
                    return
            except ValueError:
                print("Invalid input.")
                return
        elif choice == "4":
            time_options = list(self.time_mapping.keys())
            
            print("\nSelect time of day:")
            for i, time_option in enumerate(time_options, 1):
                print(f"{i}. {time_option}")
            
            try:
                time_idx = int(input("\nEnter your choice: ").strip()) - 1
                if 0 <= time_idx < len(time_options):
                    selected_time = time_options[time_idx]
                    time_filter = self.time_mapping[selected_time]
                    results = [e for e in self.events if time_filter(e.get("time", ""))]
                else:
                    print("Invalid selection.")
                    return
            except ValueError:
                print("Invalid input.")
                return
        else:
            print("Invalid choice.")
            return
        
        self.display_search_results(results)

    def display_events_by_date(self):
        """Display events organized by date"""
        # Group events by date
        events_by_date = {}
        for event in self.events:
            date = event.get("date", "No date")
            if date not in events_by_date:
                events_by_date[date] = []
            events_by_date[date].append(event)
        
        # Sort dates
        sorted_dates = sorted(events_by_date.keys())
        
        if not sorted_dates:
            print("No events with dates found.")
            return
            
        # Filter dates for pagination
        today = datetime.date.today().strftime("%Y-%m-%d")
        future_dates = [d for d in sorted_dates if d >= today]
        
        if not future_dates:
            print("No upcoming events found.")
            return
        
        page_size = 5  # Number of dates to show per page
        total_pages = (len(future_dates) + page_size - 1) // page_size
        current_page = 1
        
        while True:
            start_idx = (current_page - 1) * page_size
            end_idx = min(start_idx + page_size, len(future_dates))
            
            print(f"\nShowing dates {start_idx+1}-{end_idx} of {len(future_dates)} (Page {current_page}/{total_pages})")
            
            # Display events for each date in the current page
            for i, date in enumerate(future_dates[start_idx:end_idx], start_idx+1):
                try:
                    date_obj = dt.strptime(date, "%Y-%m-%d")
                    formatted_date = date_obj.strftime("%A, %B %d, %Y")
                    print(f"\n{i}. {formatted_date}")
                except ValueError:
                    print(f"\n{i}. {date}")
                
                # List events for this date
                for j, event in enumerate(events_by_date[date], 1):
                    time = event.get("time", "")
                    time_str = f" at {time}" if time else ""
                    print(f"   {j}. {event.get('name', 'Unnamed Event')}{time_str}")
            
            print("\nOptions:")
            print("N: Next page")
            print("P: Previous page")
            print("V #: View events for date number #")
            print("B: Back to main menu")
            
            choice = input("\nEnter your choice: ").strip().lower()
            
            if choice == 'n' and current_page < total_pages:
                current_page += 1
            elif choice == 'p' and current_page > 1:
                current_page -= 1
            elif choice == 'b':
                return
            elif choice.startswith('v '):
                try:
                    date_num = int(choice[2:]) - 1
                    if 0 <= date_num < len(future_dates):
                        self.display_events_for_date(future_dates[date_num], events_by_date[future_dates[date_num]])
                    else:
                        print("Invalid date number.")
                except ValueError:
                    print("Invalid input. Please enter a valid date number.")
            else:
                print("Invalid choice. Please try again.")

    def display_events_for_date(self, date, events):
        """Display all events for a specific date with options to view details"""
        try:
            date_obj = dt.strptime(date, "%Y-%m-%d")
            formatted_date = date_obj.strftime("%A, %B %d, %Y")
            print(f"\nEvents for {formatted_date}:")
        except ValueError:
            print(f"\nEvents for {date}:")
        
        # Sort events by time
        events = sorted(events, key=lambda e: e.get("time", ""))
        
        while True:
            # Display events
            for i, event in enumerate(events, 1):
                time = event.get("time", "")
                time_str = f" at {time}" if time else ""
                location = event.get("location", "")
                location_str = f" - {location}" if location else ""
                print(f"{i}. {event.get('name', 'Unnamed Event')}{time_str}{location_str}")
            
            print("\nOptions:")
            print("V #: View details for event number #")
            print("B: Back to date list")
            
            choice = input("\nEnter your choice: ").strip().lower()
            
            if choice == 'b':
                return
            elif choice.startswith('v '):
                try:
                    event_num = int(choice[2:]) - 1
                    if 0 <= event_num < len(events):
                        event = events[event_num]
                        self.display_single_event(event)
                    else:
                        print("Invalid event number.")
                except ValueError:
                    print("Invalid input. Please enter a valid event number.")
            else:
                print("Invalid choice. Please try again.")

    def display_single_event(self, event):
        """Display detailed information for a single event"""
        print(f"\nEvent: {event.get('name', 'Unnamed Event')}")
        print(f"Date: {event.get('date', 'No date specified')}")
        
        time = event.get('time', '')
        if time:
            print(f"Time: {time}")
        
        location = event.get('location', '')
        if location:
            print(f"Location: {location}")
        
        description = event.get('description', '')
        if description:
            print(f"\nDescription: {description}")
        
        link = event.get('link', '')
        if link:
            print(f"\nEvent Link: {link}")
        
        input("\nPress Enter to continue...")

    def display_search_results(self, results):
        """Display search results with pagination"""
        if not results:
            print("No events found matching your search criteria.")
            return
            
        page_size = 10
        total_pages = (len(results) + page_size - 1) // page_size
        current_page = 1
        
        while True:
            start_idx = (current_page - 1) * page_size
            end_idx = min(start_idx + page_size, len(results))
            
            print(f"\nShowing results {start_idx+1}-{end_idx} of {len(results)} events (Page {current_page}/{total_pages})")
            
            for i, event in enumerate(results[start_idx:end_idx], start_idx+1):
                date = event.get("date", "No date")
                time = event.get("time", "")
                time_str = f" at {time}" if time else ""
                print(f"{i}. [{date}] {event.get('name', 'Unnamed Event')}{time_str}")
            
            print("\nOptions:")
            print("N: Next page")
            print("P: Previous page")
            print("V #: View details for event number #")
            print("B: Back to search menu")
            
            choice = input("\nEnter your choice: ").strip().lower()
            
            if choice == 'n' and current_page < total_pages:
                current_page += 1
            elif choice == 'p' and current_page > 1:
                current_page -= 1
            elif choice == 'b':
                return
            elif choice.startswith('v '):
                try:
                    event_num = int(choice[2:]) - 1
                    if 0 <= event_num < len(results):
                        self.display_single_event(results[event_num])
                    else:
                        print("Invalid event number.")
                except ValueError:
                    print("Invalid input. Please enter a valid event number.")
            else:
                print("Invalid choice. Please try again.")

    def event_recommendation(self):
        """Match events based on user preferences"""
        import random
        from datetime import datetime, timedelta
        
        print("\n===== Event Matchmaker =====")
        print("This feature will help match you with events based on your preferences.")
        
        # Collect user preferences
        answers = {}
        
        # 1. Event type preference
        event_type_options = ["Sports", "Academic", "Arts & Culture", "Workshops & Training", 
                             "Conferences", "Any Type"]
        selected = self.get_selection(event_type_options, "What type of event are you interested in?")
        if not selected:
            return
        answers["event_type"] = selected
        
        # 2. Time of day preference
        time_options = list(self.time_mapping.keys())
        time_options.append("Any time")
        selected = self.get_selection(time_options, "What time of day do you prefer?")
        if not selected:
            return
        answers["time_preference"] = selected
        
        # 3. Location preference
        if self.locations:
            location_options = list(self.locations)
            location_options.append("Any location")
            selected = self.get_selection(location_options, "Do you prefer a specific location?")
            if not selected:
                return
            answers["location"] = selected
        else:
            answers["location"] = "Any location"
        
        # 4. Date range
        date_range_options = ["Next 7 days", "Next 14 days", "Next 30 days", "Any time"]
        selected = self.get_selection(date_range_options, "When would you like to attend?")
        if not selected:
            return
        answers["date_range"] = selected
        
        # 5. Keywords of interest
        print("\nEnter keywords that interest you (optional, press Enter to skip):")
        keywords = input("Keywords (comma separated): ").strip().lower()
        if keywords:
            answers["keywords"] = [k.strip() for k in keywords.split(",")]
        else:
            answers["keywords"] = []
        
        # Find matching events
        matched_events = self.find_matching_events(answers)
        
        # Display results
        if matched_events:
            self.display_search_results(matched_events)
        else:
            print("\nNo events found matching your preferences.")
            # Provide 5 random events happening in the next week as fallback
            random_events = self.get_random_upcoming_events(5, 7)
            if random_events:
                print("\nHere are some upcoming events you might be interested in:")
                self.display_search_results(random_events)
            else:
                print("No upcoming events found in the next week.")
                
    def find_matching_events(self, preferences):
        """Find events matching the given preferences"""
        from datetime import datetime, timedelta
        
        matches = []
        today = datetime.now()
        
        # Parse date range preference
        if preferences["date_range"] == "Next 7 days":
            max_date = (today + timedelta(days=7)).strftime("%Y-%m-%d")
        elif preferences["date_range"] == "Next 14 days":
            max_date = (today + timedelta(days=14)).strftime("%Y-%m-%d")
        elif preferences["date_range"] == "Next 30 days":
            max_date = (today + timedelta(days=30)).strftime("%Y-%m-%d")
        else:
            max_date = "9999-12-31"  # Any time
        
        today_str = today.strftime("%Y-%m-%d")
        
        for event in self.events:
            event_date = event.get("date", "")
            
            # Skip past events
            if event_date < today_str:
                continue
                
            # Skip events beyond the selected date range
            if event_date > max_date:
                continue
            
            # Check event type match (if specified)
            event_type_match = True
            if preferences["event_type"] != "Any Type":
                event_name = event.get("name", "").lower()
                event_type_match = False
                
                if preferences["event_type"] == "Sports":
                    if "vs" in event_name or "at" in event_name or "sport" in event_name or "athletics" in event_name or "gators" in event_name:
                        event_type_match = True
                
                elif preferences["event_type"] == "Academic":
                    if "seminar" in event_name or "colloquium" in event_name or "lecture" in event_name or "symposium" in event_name or "conference" in event_name:
                        event_type_match = True
                
                elif preferences["event_type"] == "Arts & Culture":
                    if "concert" in event_name or "music" in event_name or "performance" in event_name or "theatre" in event_name or "dance" in event_name or "art" in event_name:
                        event_type_match = True
                
                elif preferences["event_type"] == "Workshops & Training":
                    if "workshop" in event_name or "training" in event_name or "learn" in event_name or "course" in event_name:
                        event_type_match = True
                
                elif preferences["event_type"] == "Conferences":
                    if "conference" in event_name or "symposium" in event_name or "forum" in event_name:
                        event_type_match = True
            
            if not event_type_match:
                continue
            
            # Check time of day match (if specified)
            time_match = True
            if preferences["time_preference"] != "Any time":
                event_time = event.get("time", "")
                if event_time:
                    time_filter = self.time_mapping.get(preferences["time_preference"])
                    time_match = time_filter(event_time) if time_filter else True
            
            if not time_match:
                continue
            
            # Check location match (if specified)
            location_match = True
            if preferences["location"] != "Any location":
                event_location = event.get("location", "")
                location_match = preferences["location"] == event_location
            
            if not location_match:
                continue
            
            # Check keyword matches
            keyword_match = True
            if preferences["keywords"]:
                event_text = (event.get("name", "") + " " + event.get("description", "")).lower()
                keyword_match = any(keyword in event_text for keyword in preferences["keywords"])
            
            if not keyword_match:
                continue
            
            # If we got here, all criteria match
            matches.append(event)
        
        return matches
    
    def get_random_upcoming_events(self, count=5, days=7):
        """Get random events happening in the next specified number of days"""
        import random
        from datetime import datetime, timedelta
        
        today = datetime.now()
        max_date = (today + timedelta(days=days)).strftime("%Y-%m-%d")
        today_str = today.strftime("%Y-%m-%d")
        
        # Find all events in the next week
        upcoming_events = [
            event for event in self.events 
            if event.get("date", "") >= today_str and event.get("date", "") <= max_date
        ]
        
        # Return random selection or all if fewer than requested
        if len(upcoming_events) <= count:
            return upcoming_events
        else:
            return random.sample(upcoming_events, count)

    def get_selection(self, options, prompt="Select an option", allow_exit=True):
        """Get a single selection from a list of options."""
        while True:
            print(f"\n{prompt}:")
            for i, option in enumerate(options, 1):
                print(f"{i}. {option}")
            if allow_exit:
                print("\n0. Back to previous menu")
                print("E. Exit program")

            choice = input("\nEnter your choice: ").strip().lower()
            if choice == "e":
                self.exit_program()
            if allow_exit and choice == "0":
                return None

            try:
                choice_index = int(choice) - 1
                if 0 <= choice_index < len(options):
                    return options[choice_index]
            except ValueError:
                pass

            print("\nInvalid selection. Please try again.")

    def main_menu(self):
        """Display the main menu and handle user interactions."""
        while True:
            print("\n===== UF Events System =====")
            options = ["Browse Events by Date", "Search Events", "Event Matchmaker"]
            selected = self.get_selection(options, "Main Menu", allow_exit=True)

            if selected == "Browse Events by Date":
                self.display_events_by_date()
            elif selected == "Search Events":
                self.search_events()
            elif selected == "Event Matchmaker":
                self.event_recommendation()

    def exit_program(self):
        """Exit the program."""
        print("\nThank you for using the UF Events System!")
        sys.exit(0)


if __name__ == "__main__":
    # Load from the specified JSON file path
    json_file = "./jsonFiles/events.json"
    
    try:
        system = EventsSystem(json_file=json_file)
    except Exception as e:
        print(f"Error loading events data from file: {e}")
        print(f"Please make sure {json_file} exists and contains valid JSON.")
        sys.exit(1)
    
    # Start the system
    system.main_menu()