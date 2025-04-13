import json
import os
import datetime
from datetime import datetime as dt, timedelta
import random


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
            elif (
                "concert" in name
                or "music" in name
                or "performance" in name
                or "theatre" in name
                or "dance" in name
            ):
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
            "Morning (before 12pm)": lambda time: time
            and (
                time.endswith("am")
                or time.startswith("1")
                and not time.startswith("1:")
                and not time.startswith("10")
                and not time.startswith("11")
            ),
            "Afternoon (12pm-5pm)": lambda time: time
            and (
                time.endswith("pm")
                and (
                    time.startswith("12")
                    or time.startswith("1")
                    or time.startswith("2")
                    or time.startswith("3")
                    or time.startswith("4")
                    or time.startswith("5")
                )
            ),
            "Evening (after 5pm)": lambda time: time
            and (
                time.endswith("pm")
                and (
                    time.startswith("6")
                    or time.startswith("7")
                    or time.startswith("8")
                    or time.startswith("9")
                    or time.startswith("10")
                    or time.startswith("11")
                )
            ),
        }

    def handle_menu_request(self, category, path, selection):
        """Process a menu request based on category, path, and selection"""
        if category != "events":
            return self._default_response()

        # Root menu (no path)
        if not path:
            return self._get_main_menu()

        # Get the first path element to determine which submenu to show
        main_section = path[0]

        # Browse section
        if main_section == "browse":
            if len(path) == 1:
                return self._get_browse_menu()
            elif len(path) == 2:
                return self._get_events_for_date(path[1])

        # Search section
        elif main_section == "search":
            if len(path) == 1:
                return self._get_search_menu()
            elif len(path) == 2:
                if path[1] == "keyword":
                    return self._get_keyword_search_prompt()
                elif path[1] == "date":
                    return self._get_date_search_prompt()
                elif path[1] == "location":
                    return self._get_location_search_menu()
                elif path[1] == "timeofday":
                    return self._get_time_of_day_menu()
            elif len(path) == 3:
                if path[1] == "keyword":
                    return self._get_keyword_search_results(path[2])
                elif path[1] == "date":
                    return self._get_date_search_results(path[2])
                elif path[1] == "location":
                    return self._get_location_search_results(path[2])
                elif path[1] == "timeofday":
                    return self._get_time_search_results(path[2])

        # Event Matchmaker section
        elif main_section == "matchmaker":
            if len(path) == 1:
                return self._get_event_matchmaker_type_menu()
            elif len(path) == 2:
                return self._get_event_matchmaker_time_menu()
            elif len(path) == 3:
                return self._get_event_matchmaker_location_menu()
            elif len(path) == 4:
                return self._get_event_matchmaker_date_menu()
            elif len(path) == 5:
                return self._get_event_matchmaker_keywords_prompt()
            elif len(path) == 6:
                return self._get_event_matchmaker_results(
                    path[1], path[2], path[3], path[4], path[5]
                )

        # Check if an event was selected for details
        if selection:
            return self._get_event_details(selection)

        # Default response if no matching route is found
        return self._default_response()

    def find_matching_events(self, preferences):
        """Find events matching the given preferences"""
        matches = []
        today = datetime.datetime.now()

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
                    if (
                        "vs" in event_name
                        or "at" in event_name
                        or "sport" in event_name
                        or "athletics" in event_name
                        or "gators" in event_name
                    ):
                        event_type_match = True

                elif preferences["event_type"] == "Academic":
                    if (
                        "seminar" in event_name
                        or "colloquium" in event_name
                        or "lecture" in event_name
                        or "symposium" in event_name
                        or "conference" in event_name
                    ):
                        event_type_match = True

                elif preferences["event_type"] == "Arts & Culture":
                    if (
                        "concert" in event_name
                        or "music" in event_name
                        or "performance" in event_name
                        or "theatre" in event_name
                        or "dance" in event_name
                        or "art" in event_name
                    ):
                        event_type_match = True

                elif preferences["event_type"] == "Workshops & Training":
                    if (
                        "workshop" in event_name
                        or "training" in event_name
                        or "learn" in event_name
                        or "course" in event_name
                    ):
                        event_type_match = True

                elif preferences["event_type"] == "Conferences":
                    if (
                        "conference" in event_name
                        or "symposium" in event_name
                        or "forum" in event_name
                    ):
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
                event_text = (
                    event.get("name", "") + " " + event.get("description", "")
                ).lower()
                keyword_match = any(
                    keyword in event_text for keyword in preferences["keywords"]
                )

            if not keyword_match:
                continue

            # If we got here, all criteria match
            matches.append(event)

        return matches

    def get_random_upcoming_events(self, count=5, days=7):
        """Get random events happening in the next specified number of days"""
        today = datetime.datetime.now()
        max_date = (today + timedelta(days=days)).strftime("%Y-%m-%d")
        today_str = today.strftime("%Y-%m-%d")

        # Find all events in the next week
        upcoming_events = [
            event
            for event in self.events
            if event.get("date", "") >= today_str and event.get("date", "") <= max_date
        ]

        # Return random selection or all if fewer than requested
        if len(upcoming_events) <= count:
            return upcoming_events
        else:
            return random.sample(upcoming_events, count)

    # Private helper methods for web interface

    def _default_response(self):
        return {
            "question": "Menu not available",
            "options": [],
            "content": "<p>Sorry, this menu option is not available.</p>",
            "breadcrumbs": [],
        }

    def _get_main_menu(self):
        return {
            "question": "What would you like to do?",
            "options": [
                {"label": "Browse Events by Date", "value": "browse"},
                {"label": "Search Events", "value": "search"},
                {"label": "Event Matchmaker", "value": "matchmaker"},
            ],
            "breadcrumbs": [],
        }

    def _get_browse_menu(self):
        # Get upcoming dates with events
        today = datetime.date.today().strftime("%Y-%m-%d")
        future_dates = [date for date in sorted(self.dates) if date >= today]

        # Format dates for display (limited to 10)
        date_options = []
        for date in future_dates[:10]:
            try:
                date_obj = dt.strptime(date, "%Y-%m-%d")
                formatted_date = date_obj.strftime("%A, %B %d, %Y")
                date_options.append(
                    {
                        "label": formatted_date,
                        "value": date,
                        "description": f"See events on this date",
                    }
                )
            except ValueError:
                date_options.append(
                    {
                        "label": date,
                        "value": date,
                        "description": f"See events on this date",
                    }
                )

        return {
            "question": "Select a date to view events:",
            "options": date_options,
            "breadcrumbs": ["Browse Events"],
        }

    def _get_events_for_date(self, date):
        # Find events for this date
        events_for_date = [e for e in self.events if e.get("date") == date]
        events_for_date = sorted(events_for_date, key=lambda e: e.get("time", ""))

        # Format for display
        event_options = []
        for event in events_for_date:
            time = event.get("time", "")
            time_str = f" at {time}" if time else ""
            location = event.get("location", "")

            event_options.append(
                {
                    "label": f"{event.get('name', 'Unnamed Event')}{time_str}",
                    "value": event.get("name", ""),
                    "description": location if location else "No location specified",
                }
            )

        # Format date for breadcrumb
        try:
            date_obj = dt.strptime(date, "%Y-%m-%d")
            formatted_date = date_obj.strftime("%B %d, %Y")
            full_formatted_date = date_obj.strftime("%A, %B %d, %Y")
        except ValueError:
            formatted_date = date
            full_formatted_date = date

        return {
            "question": f"Events on {full_formatted_date}:",
            "options": event_options,
            "breadcrumbs": ["Browse Events", formatted_date],
        }

    def _get_search_menu(self):
        return {
            "question": "Search for events by:",
            "options": [
                {"label": "Keyword Search", "value": "keyword"},
                {"label": "Date", "value": "date"},
                {"label": "Location", "value": "location"},
                {"label": "Time of Day", "value": "timeofday"},
            ],
            "breadcrumbs": ["Search Events"],
        }

    def _get_keyword_search_prompt(self):
        return {
            "question": "Enter keyword to search:",
            "options": [],
            "hasCustomInput": True,
            "inputPlaceholder": "Enter keyword...",
            "breadcrumbs": ["Search Events", "By Keyword"],
        }

    def _get_date_search_prompt(self):
        return {
            "question": "Enter date in format YYYY-MM-DD:",
            "options": [],
            "hasCustomInput": True,
            "inputPlaceholder": "YYYY-MM-DD",
            "breadcrumbs": ["Search Events", "By Date"],
        }

    def _get_location_search_menu(self):
        location_options = []
        for location in self.locations:
            location_options.append({"label": location, "value": location})

        return {
            "question": "Select a location:",
            "options": location_options,
            "breadcrumbs": ["Search Events", "By Location"],
        }

    def _get_time_of_day_menu(self):
        time_options = list(self.time_mapping.keys())

        return {
            "question": "Select time of day:",
            "options": [{"label": option, "value": option} for option in time_options],
            "breadcrumbs": ["Search Events", "By Time of Day"],
        }

    def _get_event_matchmaker_type_menu(self):
        event_type_options = [
            "Any Type",
            "Sports",
            "Academic",
            "Arts & Culture",
            "Workshops & Training",
            "Conferences",
        ]
        return {
            "question": "What type of event are you interested in?",
            "options": [
                {"label": option, "value": option.lower().replace(" ", "_")}
                for option in event_type_options
            ],
            "breadcrumbs": ["Event Matchmaker"],
        }

    def _get_event_matchmaker_time_menu(self):
        time_options = list(self.time_mapping.keys())
        time_options.insert(0, "Any time")

        return {
            "question": "What time of day do you prefer?",
            "options": [{"label": option, "value": option} for option in time_options],
            "breadcrumbs": ["Event Matchmaker", "Event Type"],
        }

    def _get_event_matchmaker_location_menu(self):
        location_options = list(self.locations)
        location_options.insert(0, "Any location")

        return {
            "question": "Do you prefer a specific location?",
            "options": [
                {"label": option, "value": option} for option in location_options
            ],
            "breadcrumbs": ["Event Matchmaker", "Event Type", "Time Preference"],
        }

    def _get_event_matchmaker_date_menu(self):
        date_range_options = ["Any time", "Next 7 days", "Next 14 days", "Next 30 days"]

        return {
            "question": "When would you like to attend?",
            "options": [
                {"label": option, "value": option} for option in date_range_options
            ],
            "breadcrumbs": [
                "Event Matchmaker",
                "Event Type",
                "Time Preference",
                "Location",
            ],
        }

    def _get_event_matchmaker_keywords_prompt(self):
        return {
            "question": "Enter keywords that interest you (optional):",
            "options": [],
            "hasCustomInput": True,
            "inputPlaceholder": "Keywords (comma separated)",
            "breadcrumbs": [
                "Event Matchmaker",
                "Event Type",
                "Time Preference",
                "Location",
                "Date Range",
            ],
        }

    def _get_event_matchmaker_results(
        self, event_type, time_preference, location, date_range, keywords_input
    ):
        # Parse keywords
        keywords = keywords_input.split(",") if keywords_input else []

        # Format event type
        formatted_event_type = (
            event_type.replace("_", " ").title()
            if event_type != "any_type"
            else "Any Type"
        )

        # Prepare preferences object
        preferences = {
            "event_type": formatted_event_type,
            "time_preference": time_preference,
            "location": location,
            "date_range": date_range,
            "keywords": keywords,
        }

        # Find matching events
        matched_events = self.find_matching_events(preferences)

        # Prepare results
        event_options = []
        for event in matched_events[:10]:  # Limit to 10 results
            date = event.get("date", "No date")
            try:
                date_obj = dt.strptime(date, "%Y-%m-%d")
                formatted_date = date_obj.strftime("%a, %b %d")
            except ValueError:
                formatted_date = date

            time = event.get("time", "")
            time_str = f" at {time}" if time else ""
            location_str = (
                f" - {event.get('location', 'No location')}"
                if event.get("location", "")
                else ""
            )

            event_options.append(
                {
                    "label": f"{event.get('name', 'Unnamed Event')}",
                    "value": event.get("name", ""),
                    "description": f"{formatted_date}{time_str}{location_str}",
                }
            )

        # If no results, get random suggestions
        if not event_options:
            random_events = self.get_random_upcoming_events(5, 7)
            for event in random_events:
                date = event.get("date", "No date")
                try:
                    date_obj = dt.strptime(date, "%Y-%m-%d")
                    formatted_date = date_obj.strftime("%a, %b %d")
                except ValueError:
                    formatted_date = date

                time = event.get("time", "")
                time_str = f" at {time}" if time else ""
                location_str = (
                    f" - {event.get('location', 'No location')}"
                    if event.get("location", "")
                    else ""
                )

                event_options.append(
                    {
                        "label": f"{event.get('name', 'Unnamed Event')}",
                        "value": event.get("name", ""),
                        "description": f"{formatted_date}{time_str}{location_str}",
                    }
                )

            content = "<p>No events found matching your preferences. Here are some random upcoming events:</p>"
        else:
            content = (
                f"<p>Found {len(matched_events)} events matching your preferences:</p>"
            )

        return {
            "question": "Matching Events:",
            "options": event_options,
            "content": content,
            "breadcrumbs": ["Event Matchmaker", "Results"],
        }

    def _get_keyword_search_results(self, keyword):
        keyword = keyword.lower()
        keyword_events = [
            e
            for e in self.events
            if keyword in e.get("name", "").lower()
            or keyword in e.get("description", "").lower()
        ]

        # Sort by date
        keyword_events = sorted(keyword_events, key=lambda e: e.get("date", ""))

        event_options = []
        for event in keyword_events[:10]:  # Limit to 10 results
            date = event.get("date", "No date")
            try:
                date_obj = dt.strptime(date, "%Y-%m-%d")
                formatted_date = date_obj.strftime("%a, %b %d")
            except ValueError:
                formatted_date = date

            time = event.get("time", "")
            time_str = f" at {time}" if time else ""
            location = event.get("location", "")
            location_str = f" - {location}" if location else ""

            event_options.append(
                {
                    "label": f"{event.get('name', 'Unnamed Event')}",
                    "value": event.get("name", ""),
                    "description": f"{formatted_date}{time_str}{location_str}",
                }
            )

        return {
            "question": f'Events matching "{keyword}":',
            "options": event_options,
            "content": f"<p>Found {len(keyword_events)} events matching '{keyword}'.</p>",
            "breadcrumbs": ["Search Events", "By Keyword", f'"{keyword}"'],
        }

    def _get_date_search_results(self, search_date):
        date_events = [e for e in self.events if e.get("date", "") == search_date]

        # Sort by time
        date_events = sorted(date_events, key=lambda e: e.get("time", ""))

        # Format date for display
        try:
            date_obj = dt.strptime(search_date, "%Y-%m-%d")
            formatted_date = date_obj.strftime("%A, %B %d, %Y")
        except ValueError:
            formatted_date = search_date

        event_options = []
        for event in date_events:
            time = event.get("time", "")
            time_str = f" at {time}" if time else ""

            event_options.append(
                {
                    "label": f"{event.get('name', 'Unnamed Event')}{time_str}",
                    "value": event.get("name", ""),
                    "description": event.get("location", "No location specified"),
                }
            )

        return {
            "question": f"Events on {formatted_date}:",
            "options": event_options,
            "content": f"<p>Found {len(date_events)} events on this date.</p>",
            "breadcrumbs": ["Search Events", "By Date", formatted_date],
        }

    def _get_location_search_results(self, selected_location):
        events_at_location = [
            e for e in self.events if e.get("location") == selected_location
        ]

        # Sort by date and time
        events_at_location = sorted(
            events_at_location, key=lambda e: (e.get("date", ""), e.get("time", ""))
        )

        event_options = []
        for event in events_at_location[:10]:  # Limit to 10 results
            date = event.get("date", "No date")
            try:
                date_obj = dt.strptime(date, "%Y-%m-%d")
                formatted_date = date_obj.strftime("%a, %b %d")
            except ValueError:
                formatted_date = date

            time = event.get("time", "")
            time_str = f" at {time}" if time else ""

            event_options.append(
                {
                    "label": f"{event.get('name', 'Unnamed Event')}",
                    "value": event.get("name", ""),
                    "description": f"{formatted_date}{time_str}",
                }
            )

        return {
            "question": f"Events at {selected_location}:",
            "options": event_options,
            "content": f"<p>Found {len(events_at_location)} events at this location.</p>",
            "breadcrumbs": ["Search Events", "By Location", selected_location],
        }

    def _get_time_search_results(self, selected_time):
        time_filter = self.time_mapping.get(selected_time)

        if time_filter:
            time_events = [e for e in self.events if time_filter(e.get("time", ""))]

            # Sort by date
            time_events = sorted(time_events, key=lambda e: e.get("date", ""))

            event_options = []
            for event in time_events[:10]:  # Limit to 10 results
                date = event.get("date", "No date")
                try:
                    date_obj = dt.strptime(date, "%Y-%m-%d")
                    formatted_date = date_obj.strftime("%a, %b %d")
                except ValueError:
                    formatted_date = date

                time = event.get("time", "")
                location = event.get("location", "No location")

                event_options.append(
                    {
                        "label": f"{event.get('name', 'Unnamed Event')}",
                        "value": event.get("name", ""),
                        "description": f"{formatted_date} at {time} - {location}",
                    }
                )

            return {
                "question": f"Events during {selected_time}:",
                "options": event_options,
                "content": f"<p>Found {len(time_events)} events during this time of day.</p>",
                "breadcrumbs": ["Search Events", "By Time of Day", selected_time],
            }

        return {
            "question": "No Results",
            "options": [],
            "content": "<p>No events found for this time of day.</p>",
            "breadcrumbs": ["Search Events", "By Time of Day", selected_time],
        }

    def _get_event_details(self, event_name):
        # Find the specific event
        selected_events = [e for e in self.events if e.get("name", "") == event_name]

        if selected_events:
            event = selected_events[0]

            date = event.get("date", "No date specified")
            try:
                date_obj = dt.strptime(date, "%Y-%m-%d")
                formatted_date = date_obj.strftime("%A, %B %d, %Y")
            except ValueError:
                formatted_date = date

            time = event.get("time", "")
            location = event.get("location", "")
            description = event.get("description", "No description available.")
            link = event.get("link", "")

            content = f"""
            <div class="event-details">
                <h3>{event.get('name', 'Unnamed Event')}</h3>
                <p><strong>Date:</strong> {formatted_date}</p>
                {'<p><strong>Time:</strong> ' + time + '</p>' if time else ''}
                {'<p><strong>Location:</strong> ' + location + '</p>' if location else ''}
                <p><strong>Description:</strong><br>{description}</p>
                {'<p><strong>Event Link:</strong> <a href="' + link + '" target="_blank">' + link + '</a></p>' if link else ''}
            </div>
            """

            return {
                "question": "Event Details:",
                "options": [],
                "content": content,
                "breadcrumbs": ["Event Details"],
            }

        return {
            "question": "Event Not Found",
            "options": [],
            "content": "<p>The requested event could not be found.</p>",
            "breadcrumbs": ["Event Details"],
        }
