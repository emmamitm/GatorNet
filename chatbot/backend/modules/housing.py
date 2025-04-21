import json
import os


class HousingSystem:
    def __init__(self, json_file=None, housing_data=None):
        """Initialize with either a JSON file or direct data"""
        self.halls = []
        self.rates = {}
        self.links = {}
        self._last_search_results = []
        self._last_recommendation_results = []

        if json_file and os.path.exists(json_file):
            with open(json_file, "r") as f:
                data = json.load(f)
                self.halls = data.get("halls", [])
                self.rates = data.get("rates", {})
                self.links = data.get("links", {})
        elif housing_data:
            self.halls = housing_data.get("halls", [])
            self.rates = housing_data.get("rates", {})
            self.links = housing_data.get("links", {})

        # Process room types and nearby locations correctly
        for hall in self.halls:
            # Process room types - look for actual room types
            room_types_str = hall.get("room_types_str", "")
            actual_room_types = []

            # Common room type prefixes to identify actual room types
            room_type_patterns = [
                "Single",
                "Double",
                "Triple",
                "Quad",
                "Apartment",
                "Suite",
                "One Bedroom",
                "Two Bedroom",
                "Efficiency",
                "Private Bedroom",
            ]

            # Extract the actual room types
            for item in room_types_str.split(", "):
                if any(pattern in item for pattern in room_type_patterns):
                    actual_room_types.append(item)

            # Store the processed room types
            hall["actual_room_types"] = actual_room_types

            # Process nearby locations - exclude room types
            nearby_str = hall.get("nearby_locations_str", "")
            actual_nearby = []

            for item in nearby_str.split(", "):
                if not any(pattern in item for pattern in room_type_patterns):
                    actual_nearby.append(item)

            # Store the processed nearby locations
            hall["actual_nearby"] = actual_nearby

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
            for room_type in hall.get("actual_room_types", []):
                if room_type:
                    self.all_room_types.add(room_type)

        # Extract all nearby locations from the processed data
        self.all_nearby = set()
        for hall in self.halls:
            for location in hall.get("actual_nearby", []):
                if location:
                    self.all_nearby.add(location)

        # Create matcher questions based on hall data
        self.matcher_questions = [
            {
                "id": "hall_type",
                "question": "What type of housing are you looking for?",
                "options": sorted(list(self.hall_types)) + ["No preference"],
            },
            {
                "id": "room_type",
                "question": "What type of room do you prefer?",
                "options": [
                    "Single",
                    "Double",
                    "Triple",
                    "Quad",
                    "Apartment",
                    "Suite",
                    "No preference",
                ],
            },
            {
                "id": "budget",
                "question": "What is your budget per semester (Fall/Spring)?",
                "options": [
                    "Under $3500",
                    "$3500-$4000",
                    "$4000-$4500",
                    "$4500-$5000",
                    "Over $5000",
                    "No preference",
                ],
            },
            {
                "id": "features",
                "question": "What features are most important to you?",
                "options": [
                    "Fully Furnished",
                    "Private Bathroom",
                    "Kitchen/Kitchenette",
                    "Laundry Facilities",
                    "Study Spaces",
                    "Social/Game Rooms",
                    "No preference",
                ],
            },
            {
                "id": "location",
                "question": "What campus location do you prefer to be near?",
                "options": [
                    "College of Business",
                    "College of Engineering",
                    "College of Arts",
                    "Athletics (Stadium/O'Connell Center)",
                    "Reitz Union",
                    "Libraries",
                    "No preference",
                ],
            },
        ]

    def handle_menu_request(self, category, path, selection=None):
        """Process a menu request based on category, path, and selection"""
        if category != "housing":
            return self._default_response()

        # Root menu (no path)
        if not path:
            return self._get_main_menu()

        # If no selection is provided, use the last path element
        if not selection and len(path) > 1:
            selection = path[-1]

        # Process based on first path element
        main_section = path[0]

        if main_section == "view":
            if len(path) == 1:
                return self._get_hall_list()
            elif len(path) >= 2:
                if path[-1].startswith("page_"):
                    page = int(path[-1].split("_")[1])
                    return self._get_hall_list(page)
                else:
                    # View specific hall
                    hall_name = path[-1]
                    return self._get_hall_info(hall_name)

        elif main_section == "search":
            if len(path) == 1:
                return self._get_search_menu()
            elif len(path) == 2:
                if path[1] == "hall_type":
                    return self._get_hall_types()
                elif path[1] == "room_type":
                    return self._get_room_types()
                elif path[1] == "price_range":
                    return self._get_price_ranges()
                elif path[1] == "features":
                    return self._get_features()
                elif path[1] == "location":
                    return self._get_locations()
                elif path[1] == "keyword":
                    return self._get_keyword_search_form()
                elif path[1] == "results":
                    page = 1
                    if selection and selection.startswith("page_"):
                        page = int(selection.split("_")[1])
                    return self._format_search_results(self._last_search_results, page)
            elif len(path) == 3:
                # Process search selections
                if path[1] == "hall_type":
                    results = [
                        hall
                        for hall in self.halls
                        if hall.get("hall_type", "") == path[2]
                    ]
                    self._last_search_results = results
                    return self._format_search_results(results, 1)
                elif path[1] == "room_type":
                    results = []
                    for hall in self.halls:
                        room_types = hall.get("actual_room_types", [])
                        if any(path[2].lower() in rt.lower() for rt in room_types):
                            results.append(hall)
                    self._last_search_results = results
                    return self._format_search_results(results, 1)
                elif path[1] == "price_range":
                    price_range = path[2]
                    results = self._search_by_price_range(price_range)
                    self._last_search_results = results
                    return self._format_search_results(results, 1)
                elif path[1] == "features":
                    feature = path[2]
                    results = [
                        hall
                        for hall in self.halls
                        if feature in hall.get("features_str", "")
                    ]
                    self._last_search_results = results
                    return self._format_search_results(results, 1)
                elif path[1] == "location":
                    search_term = path[2].replace("Near ", "").lower()
                    results = [
                        hall
                        for hall in self.halls
                        if search_term in hall.get("nearby_locations_str", "").lower()
                    ]
                    self._last_search_results = results
                    return self._format_search_results(results, 1)
                elif path[1] == "keyword":
                    keyword = path[2].lower()
                    results = []
                    for hall in self.halls:
                        hall_text = (
                            hall.get("name", "").lower()
                            + " "
                            + hall.get("description", "").lower()
                            + " "
                            + hall.get("features_str", "").lower()
                            + " "
                            + hall.get("room_types_str", "").lower()
                            + " "
                            + hall.get("nearby_locations_str", "").lower()
                        )
                        if keyword in hall_text:
                            results.append(hall)
                    self._last_search_results = results
                    return self._format_search_results(results, 1)
            elif len(path) >= 4:
                # Handle pagination or hall selection from results
                if selection and selection.startswith("page_"):
                    page = int(selection.split("_")[1])
                    return self._format_search_results(self._last_search_results, page)
                else:
                    # View specific hall from search results
                    return self._get_hall_info_by_name(selection)

        elif main_section == "matcher":
            if len(path) == 1:
                return self._get_matcher_question(0, {})
            elif path[1] == "results":
                if len(path) == 2:
                    # Show matcher results
                    hall_scores, reasons = self._calculate_hall_scores(selection)
                    top_matches = sorted(
                        hall_scores.items(), key=lambda x: x[1], reverse=True
                    )[:3]
                    top_halls = []
                    for hall_name, score in top_matches:
                        hall = next(
                            (h for h in self.halls if h["name"] == hall_name), None
                        )
                        if hall:
                            top_halls.append((hall, score, reasons.get(hall_name, [])))

                    self._last_recommendation_results = top_halls
                    return self._format_recommendation_results(top_halls)
                elif len(path) == 3:
                    if path[2] == "compare":
                        # Compare all recommendations
                        return self._format_recommendation_comparison(
                            self._last_recommendation_results
                        )
                    else:
                        # View specific hall from recommendations
                        hall_name = path[2]
                        return self._get_hall_info_by_name(hall_name)
            else:
                # Process matcher questions
                question_id = len(path) - 2
                if question_id < 0:
                    question_id = 0

                # Build previous answers
                previous_answers = {}
                for i in range(min(len(path) - 1, len(self.matcher_questions))):
                    if i + 1 < len(path):
                        q_id = self.matcher_questions[i]["id"]
                        previous_answers[q_id] = path[i + 1]

                # Add current selection
                if selection and question_id < len(self.matcher_questions):
                    q_id = self.matcher_questions[question_id]["id"]
                    previous_answers[q_id] = selection

                    # If last question, show results
                    if question_id == len(self.matcher_questions) - 1:
                        hall_scores, reasons = self._calculate_hall_scores(
                            previous_answers
                        )
                        top_matches = sorted(
                            hall_scores.items(), key=lambda x: x[1], reverse=True
                        )[:3]
                        top_halls = []
                        for hall_name, score in top_matches:
                            hall = next(
                                (h for h in self.halls if h["name"] == hall_name), None
                            )
                            if hall:
                                top_halls.append(
                                    (hall, score, reasons.get(hall_name, []))
                                )

                        self._last_recommendation_results = top_halls
                        return self._format_recommendation_results(top_halls)

                    # Otherwise go to next question
                    return self._get_matcher_question(question_id + 1, previous_answers)

                return self._get_matcher_question(question_id, previous_answers)

        elif main_section == "application":
            return self._get_application_info()

        return self._default_response()

    def _default_response(self):
        """Default response when no route matches"""
        return {
            "question": "Menu not available",
            "options": [],
            "content": "<p>Sorry, this menu option is not available.</p>",
            "breadcrumbs": [],
        }

    def _get_main_menu(self):
        """Return main menu options"""
        return {
            "question": "UF Housing Selection System",
            "options": [
                {"label": "View Residence Hall Information", "value": "view"},
                {"label": "Search Residence Halls", "value": "search"},
                {"label": "Housing Matcher", "value": "matcher"},
                {"label": "Housing Application Information", "value": "application"},
            ],
            "content": "<p>This tool helps you find residence halls that match your preferences.</p>",
            "breadcrumbs": [],
        }

    def _get_hall_list(self, page=1):
        """Return paginated list of residence halls"""
        sorted_halls = sorted(self.halls, key=lambda x: x.get("name", ""))
        page_size = 10
        total_halls = len(sorted_halls)
        total_pages = (total_halls + page_size - 1) // page_size
        page = max(1, min(page, total_pages))
        start_idx = (page - 1) * page_size
        end_idx = min(start_idx + page_size, total_halls)
        page_halls = sorted_halls[start_idx:end_idx]

        content = f"<p class='mb-2 text-sm text-gray-500'>Showing halls {start_idx+1}-{end_idx} of {total_halls} (Page {page}/{total_pages})</p>"
        content += "<div class='space-y-4'>"
        for hall in page_halls:
            hall_type = hall.get("hall_type", "Unknown type")
            content += f"<div class='border-b pb-2'><h3 class='text-lg font-semibold'>{hall.get('name', 'Unnamed Hall')}</h3><p class='text-sm text-gray-600'>{hall_type}</p></div>"
        content += "</div>"

        options = []
        for hall in page_halls:
            options.append(
                {
                    "label": hall.get("name", "Unnamed Hall"),
                    "value": hall.get("name", ""),
                }
            )

        if page > 1:
            options.append({"label": "« Previous Page", "value": f"page_{page-1}"})
        if page < total_pages:
            options.append({"label": "Next Page »", "value": f"page_{page+1}"})

        return {
            "question": "Residence Hall Directory",
            "options": options,
            "content": content,
            "breadcrumbs": ["View Halls"],
            "pagination": {
                "current_page": page,
                "total_pages": total_pages,
                "total_results": total_halls,
            },
        }

    def _get_hall_info(self, hall_name):
        """Get hall details by name"""
        hall = next((h for h in self.halls if h["name"] == hall_name), None)

        if not hall:
            return {
                "question": "Residence Hall Not Found",
                "options": [],
                "content": "<p>Sorry, the requested residence hall was not found.</p>",
                "breadcrumbs": ["View Halls"],
            }

        # Format content with hall details using Tailwind classes
        content = f"""
        <div>
            <h2 class="text-2xl font-bold mb-2">{hall.get('name', 'Unnamed Hall')}</h2>

            <div class='mt-4'>
                <h3 class="text-lg font-semibold mt-4 mb-1">Description</h3>
                <p class='text-base'>{hall.get('description', 'No description available')}</p>
            </div>

            <div class='mt-4'>
                <h3 class="text-lg font-semibold mt-4 mb-1">Location & Type</h3>
                <p><span class="font-semibold">Location:</span> {hall.get('location', 'Not specified')}</p>
                <p><span class="font-semibold">Hall Type:</span> {hall.get('hall_type', 'Not specified')}</p>
            </div>

            <div class='mt-4'>
                <h3 class="text-lg font-semibold mt-4 mb-1">Features</h3>
                <ul class="list-disc list-inside ml-4">
        """

        # Add features
        features = hall.get("features_str", "").split(", ")
        for feature in features:
            if feature:
                content += f"<li>{feature}</li>"

        content += """
                </ul>
            </div>

            <div class="mt-6">
                <h3 class='text-lg font-semibold mb-1'>Room Types</h3>
                <ul class='list-disc list-inside ml-4'>
        """

        # Add room types
        room_types = hall.get("actual_room_types", [])
        if room_types:
            for room_type in room_types:
                content += f"<li>{room_type}</li>"
        else:
            content += "<li>Room type information not available</li>"

        content += """
                </ul>
            </div>

            <div class="mt-6">
                <h3 class='text-lg font-semibold mb-1'>Nearby Locations</h3>
                <ul class='list-disc list-inside ml-4'>
        """

        # Add nearby locations
        nearby = hall.get("actual_nearby", [])
        if nearby:
            for location in nearby:
                content += f"<li>{location}</li>"
        else:
            content += "<li>Nearby location information not available</li>"

        content += """
                </ul>
            </div>

            <div class="mt-6">
                <h3 class='text-lg font-semibold mb-2'>Rental Rates</h3>
        """

        # Add rental rates
        hallName = hall["name"]
        found = False
        content += "<table class='w-full text-left border-collapse border border-gray-300'><thead><tr class='border-b border-gray-300 bg-gray-50'><th class='p-2 font-semibold'>Room Type</th><th class='p-2 font-semibold'>Fall/Spring</th><th class='p-2 font-semibold'>Summer A/B</th><th class='p-2 font-semibold'>Summer C</th></tr></thead><tbody>"
        for rate in self.rates:
            if rate["residence_hall"] == hallName:
                # Basic table styling: full width, borders
                content += f"""
                    <tr class='border-b border-gray-200'>
                        <td class='p-2'>{rate["room_type"]}</td>
                        <td class='p-2'>${rate['fall_spring']}</td>
                        <td class='p-2'>${rate['summer_a_b']}</td>
                        <td class='p-2'>${rate['summer_c']}</td>
                    </tr>
                """
                found = True
        if not found:
            content += "<tr><td colspan='4' class='p-2'>No rental rate information available</td></tr>"
        content += "</tbody></table>"

        content += """
            </div>

            <div class="mt-6">
                <h3 class='text-lg font-semibold mb-1'>Contact Information</h3>
                <p><strong class='font-semibold'>Phone:</strong> {}</p>
                <p><strong class='font-semibold'>Website:</strong> <a href="{}" target="_blank" class="text-blue-600 hover:underline">{}</a></p>
                {}
            </div>
        </div>
        """.format(
            hall.get("phone", "Not available"),
            hall.get("url", "#"),  # Provide a fallback href
            hall.get("url", "Not available"),
            (
                f"<p><strong class='font-semibold'>Email:</strong> {hall.get('email')}</p>"
                if hall.get("email")
                else ""
            ),
        )

        return {
            "question": f"Hall Details: {hall.get('name', 'Unnamed Hall')}",
            "options": [],
            "content": content,
            "breadcrumbs": ["View Halls", "Hall Details"],
        }

    def _get_hall_info_by_name(self, hall_name):
        """Find and return hall by name"""
        hall = next((h for h in self.halls if h["name"] == hall_name), None)
        if hall:
            return self._get_hall_info(hall_name)
        else:
            return {
                "question": "Residence Hall Not Found",
                "options": [],
                "content": f"<p>No residence hall found with name {hall_name}.</p>",
                "breadcrumbs": ["View Halls"],
            }

    def _get_search_menu(self):
        """Return search menu options"""
        return {
            "question": "Search Residence Halls",
            "options": [
                {"label": "Search by hall type", "value": "hall_type"},
                {"label": "Search by room type", "value": "room_type"},
                {"label": "Search by price range", "value": "price_range"},
                {"label": "Search by features", "value": "features"},
                {"label": "Search by location/nearby locations", "value": "location"},
                {"label": "Search by keyword", "value": "keyword"},
            ],
            "content": "<p>Select a search method to find residence halls.</p>",
            "breadcrumbs": ["Search"],
        }

    def _get_hall_types(self):
        """Return hall types for selection"""
        hall_types = sorted(list(self.hall_types))
        options = [{"label": hall_type, "value": hall_type} for hall_type in hall_types]
        return {
            "question": "Select a Hall Type",
            "options": options,
            "content": "<p>Choose a residence hall type to find matching halls.</p>",
            "breadcrumbs": ["Search", "By Hall Type"],
        }

    def _get_room_types(self):
        """Return room types for selection"""
        room_options = ["Single", "Double", "Triple", "Quad", "Apartment", "Suite"]
        options = [
            {"label": room_type, "value": room_type} for room_type in room_options
        ]
        return {
            "question": "Select a Room Type",
            "options": options,
            "content": "<p>Choose a room type to find matching halls.</p>",
            "breadcrumbs": ["Search", "By Room Type"],
        }

    def _get_price_ranges(self):
        """Return price ranges for selection"""
        price_ranges = [
            "Under $3500",
            "$3500-$4000",
            "$4000-$4500",
            "$4500-$5000",
            "Over $5000",
        ]
        options = [{"label": price, "value": price} for price in price_ranges]
        return {
            "question": "Select a Price Range",
            "options": options,
            "content": "<p>Choose a price range per semester (Fall/Spring).</p>",
            "breadcrumbs": ["Search", "By Price Range"],
        }

    def _search_by_price_range(self, price_range):
        """Search halls by price range"""
        results = []
        # Keep track of added hall names to avoid duplicates
        added_halls = set()
        for hall in self.halls:
            hall_name = hall["name"]
            # Iterate through the rates list to find matching halls
            for rate_info in self.rates:
                hall_name = rate_info.get("residence_hall")

                # Skip if hall already added or no name
                if not hall_name or hall_name in added_halls:
                    continue

                try:
                    # Check if 'fall_spring' key exists and is convertible to int
                    if "fall_spring" in rate_info:
                        fall_spring_rate_str = str(rate_info["fall_spring"]).replace(
                            ",", ""
                        )  # Handle potential commas
                        if fall_spring_rate_str.isdigit():
                            fall_spring_rate = int(fall_spring_rate_str)

                            match = False
                            if price_range == "Under $3500" and fall_spring_rate < 3500:
                                match = True
                            elif (
                                price_range == "$3500-$4000"
                                and 3500 <= fall_spring_rate < 4000
                            ):
                                match = True
                            elif (
                                price_range == "$4000-$4500"
                                and 4000 <= fall_spring_rate < 4500
                            ):
                                match = True
                            elif (
                                price_range == "$4500-$5000"
                                and 4500 <= fall_spring_rate < 5000
                            ):
                                match = True
                            elif (
                                price_range == "Over $5000" and fall_spring_rate >= 5000
                            ):
                                match = True

                            if match:
                                # Find the corresponding hall object
                                hall = next(
                                    (h for h in self.halls if h["name"] == hall_name),
                                    None,
                                )
                                if hall:
                                    results.append(hall)
                                    added_halls.add(hall_name)
                                    # No need to break here, as we iterate rates, not halls directly
                                    # We use added_halls to prevent adding the same hall multiple times
                except (ValueError, TypeError):
                    # Ignore if rate data is invalid for this specific rate entry
                    continue
        return results

    def _get_features(self):
        """Return features for selection"""
        common_features = [
            "Fully Furnished",
            "Laundry Facilities",
            "High-Speed Internet",
            "Study Lounge",
            "Game Room",
            "Kitchen/Kitchenette",
            "Private Bathroom",  # Added from matcher questions
        ]
        # Use self.all_features for more comprehensive list, but filter common ones for brevity
        # options = [{"label": feature, "value": feature} for feature in sorted(list(self.all_features))]
        options = [{"label": feature, "value": feature} for feature in common_features]
        return {
            "question": "Select a Feature",
            "options": options,
            "content": "<p>Choose a feature to find halls that offer it.</p>",
            "breadcrumbs": ["Search", "By Feature"],
        }

    def _get_locations(self):
        """Return locations for selection"""
        # Use actual nearby locations extracted during init for better accuracy
        location_options = sorted(list(self.all_nearby))
        # Example common locations (could be replaced or augmented by self.all_nearby)
        # location_options = [
        #     "Near College of Business",
        #     "Near College of Engineering",
        #     "Near Athletics Facilities",
        #     "Near Library West",
        #     "Near Reitz Union",
        # ]
        options = [
            {"label": location, "value": location}
            for location in location_options
            if location
        ]
        return {
            "question": "Select a Location/Nearby Point of Interest",
            "options": options,
            "content": "<p>Choose a location to find nearby residence halls.</p>",
            "breadcrumbs": ["Search", "By Location"],
        }

    def _get_keyword_search_form(self):
        """Return keyword search form"""
        return {
            "question": "Search by Keyword",
            "options": [],
            "content": "<p>Enter a keyword to search in hall names, descriptions, features, and more.</p>",
            "breadcrumbs": ["Search", "By Keyword"],
            "hasCustomInput": True,
            "inputPlaceholder": "Enter keyword",
        }

    def _format_search_results(self, results, page=1):
        """Format paginated search results"""
        if not results:
            return {
                "question": "No Residence Halls Found",
                "options": [],
                "content": "<p>No residence halls found matching your criteria.</p>",
                "breadcrumbs": ["Search", "Results"],
            }

        sorted_results = sorted(results, key=lambda x: x.get("name", ""))
        page_size = 5
        total_results = len(sorted_results)
        total_pages = (total_results + page_size - 1) // page_size
        page = max(1, min(page, total_pages))
        start_idx = (page - 1) * page_size
        end_idx = min(start_idx + page_size, total_results)
        page_results = sorted_results[start_idx:end_idx]

        content = f"<p class='mb-2 text-sm text-gray-500'>Showing results {start_idx+1}-{end_idx} of {total_results} residence halls (Page {page}/{total_pages})</p>"
        content += "<div class='space-y-4'>"
        for hall in page_results:
            hall_type = hall.get("hall_type", "Unknown type")
            desc = hall.get("description", "")
            desc_snippet = (
                (desc[:100] + "...") if len(desc) > 100 else desc
            )  # Truncate description
            # Add border, padding, basic text styling
            content += f"""
            <div class='border-b pb-2'>
                <h3 class='text-lg font-semibold'>{hall.get('name', 'Unnamed Hall')} - <span class='font-normal text-base'>{hall_type}</span></h3>
                <p class='text-sm text-gray-400 mt-1'>{desc_snippet}</p>
            </div>
            """
        content += "</div>"

        options = []
        for hall in page_results:
            options.append(
                {
                    "label": hall.get("name", "Unnamed Hall"),
                    "value": hall.get("name", ""),
                }
            )

        if page > 1:
            options.append({"label": "« Previous Page", "value": f"page_{page-1}"})
        if page < total_pages:
            options.append({"label": "Next Page »", "value": f"page_{page+1}"})

        return {
            "question": "Search Results",
            "options": options,
            "content": content,
            "breadcrumbs": ["Search", "Results"],
            "pagination": {
                "current_page": page,
                "total_pages": total_pages,
                "total_results": total_results,
            },
        }

    def _get_matcher_question(self, question_id, previous_answers=None):
        """Get matcher question data"""
        if previous_answers is None:
            previous_answers = {}

        if question_id >= len(self.matcher_questions):
            # Call calculation and formatting (assuming these methods exist)
            hall_scores, reasons = self._calculate_hall_scores(previous_answers)
            top_matches = sorted(hall_scores.items(), key=lambda x: x[1], reverse=True)[
                :3
            ]
            top_halls = []
            for hall_name, score in top_matches:
                hall = next((h for h in self.halls if h["name"] == hall_name), None)
                if hall:
                    top_halls.append((hall, score, reasons.get(hall_name, [])))

            self._last_recommendation_results = top_halls
            # This method needs to be defined to format the output
            return self._format_recommendation_results(top_halls)

        question_data = self.matcher_questions[question_id]
        q_id = question_data["id"]
        question = question_data["question"]
        options = question_data["options"]

        option_list = [{"label": opt, "value": opt} for opt in options]

        return {
            "question": question,
            "options": option_list,
            "content": "<p>Select an option that best matches your preference.</p>",
            "breadcrumbs": ["Housing Matcher", f"Question {question_id+1}"],
            "metadata": {
                "question_id": question_id,
                "question_key": q_id,
                "total_questions": len(self.matcher_questions),
            },
        }

    def _calculate_hall_scores(self, preferences):
        """Calculate scores for each residence hall based on user preferences"""
        scores = {hall["name"]: 0 for hall in self.halls}
        reasons = {hall["name"]: [] for hall in self.halls}

        # Define points for different matches
        POINTS_EXACT = 3
        POINTS_PARTIAL = 1
        POINTS_FEATURE = 2
        POINTS_LOCATION = 2
        POINTS_BUDGET = 2

        # 1. Hall Type Preference
        hall_type_pref = preferences.get("hall_type")
        if hall_type_pref and hall_type_pref != "No preference":
            for hall in self.halls:
                if hall.get("hall_type") == hall_type_pref:
                    scores[hall["name"]] += POINTS_EXACT
                    reasons[hall["name"]].append(
                        f"+{POINTS_EXACT} for matching hall type '{hall_type_pref}'"
                    )

        # 2. Room Type Preference
        room_type_pref = preferences.get("room_type")
        if room_type_pref and room_type_pref != "No preference":
            pref_lower = room_type_pref.lower()
            for hall in self.halls:
                actual_room_types = hall.get("actual_room_types", [])
                if any(pref_lower in rt.lower() for rt in actual_room_types):
                    scores[hall["name"]] += POINTS_EXACT
                    reasons[hall["name"]].append(
                        f"+{POINTS_EXACT} for offering room type '{room_type_pref}'"
                    )

        # 3. Budget Preference
        budget_pref = preferences.get("budget")
        if budget_pref and budget_pref != "No preference":
            min_rate, max_rate = -1, float("inf")
            if budget_pref == "Under $3500":
                max_rate = 3499
            elif budget_pref == "$3500-$4000":
                min_rate, max_rate = 3500, 3999
            elif budget_pref == "$4000-$4500":
                min_rate, max_rate = 4000, 4499
            elif budget_pref == "$4500-$5000":
                min_rate, max_rate = 4500, 4999
            elif budget_pref == "Over $5000":
                min_rate = 5000

            if min_rate != -1 or max_rate != float("inf"):
                for hall in self.halls:
                    hall_name = hall["name"]
                    if hall_name in self.rates:
                        hall_fits_budget = False
                        for room_type, rates in self.rates[hall_name].items():
                            try:
                                if "fall_spring" in rates:
                                    fall_spring_rate_str = str(
                                        rates["fall_spring"]
                                    ).replace(",", "")
                                    if fall_spring_rate_str.isdigit():
                                        rate = int(fall_spring_rate_str)
                                        if min_rate <= rate <= max_rate:
                                            hall_fits_budget = True
                                            break
                            except (ValueError, TypeError, KeyError):
                                continue
                        if hall_fits_budget:
                            scores[hall_name] += POINTS_BUDGET
                            reasons[hall_name].append(
                                f"+{POINTS_BUDGET} for budget match '{budget_pref}'"
                            )

        # 4. Feature Preferences
        feature_prefs = preferences.get(
            "features"
        )  # Assuming this might be a single selection from the matcher
        if feature_prefs and feature_prefs != "No preference":
            pref_lower = feature_prefs.lower()
            for hall in self.halls:
                features_str = hall.get("features_str", "").lower()
                # Simple check if the preferred feature string exists
                if pref_lower in features_str:
                    scores[hall["name"]] += POINTS_FEATURE
                    reasons[hall["name"]].append(
                        f"+{POINTS_FEATURE} for having feature '{feature_prefs}'"
                    )
                # Handle specific cases like Private Bathroom more robustly if needed
                elif pref_lower == "private bathroom" and (
                    "private bath" in features_str
                    or "suite" in hall.get("hall_type", "").lower()
                ):
                    scores[hall["name"]] += POINTS_FEATURE
                    reasons[hall["name"]].append(
                        f"+{POINTS_FEATURE} for having feature '{feature_prefs}'"
                    )

        # 5. Location Preference
        location_pref = preferences.get("location")
        if location_pref and location_pref != "No preference":
            # Extract keyword from preference (e.g., "Business" from "College of Business")
            location_keyword = location_pref.split(" ")[
                -1
            ].lower()  # Simple keyword extraction
            if "o'connell" in location_pref.lower():
                location_keyword = "o'connell"
            if "athletics" in location_pref.lower():
                location_keyword = "stadium"  # or athletics
            if "reitz" in location_pref.lower():
                location_keyword = "reitz"
            if "libraries" in location_pref.lower():
                location_keyword = "library"  # match Library West etc.

            for hall in self.halls:
                nearby_str = hall.get("nearby_locations_str", "").lower()
                if location_keyword in nearby_str:
                    scores[hall["name"]] += POINTS_LOCATION
                    reasons[hall["name"]].append(
                        f"+{POINTS_LOCATION} for proximity to '{location_pref}'"
                    )

        return scores, reasons

    # --- Placeholder methods for missing functionality ---

    def _format_recommendation_results(self, top_halls):
        """Formats the top recommended halls into HTML"""
        if not top_halls:
            return {
                "question": "No Recommendations Found",
                "options": [],
                "content": "<p>Could not determine recommendations based on your preferences. Try broadening your criteria.</p>",
                "breadcrumbs": ["Housing Matcher", "Results"],
            }

        content = "<h2 class='text-xl font-semibold mb-3'>Top Recommendations</h2>"
        content += "<div class='space-y-5'>"  # Space between recommended halls

        options = []
        for i, (hall, score, reason_list) in enumerate(top_halls):
            hall_name = hall.get("name", "Unnamed Hall")
            hall_type = hall.get("hall_type", "Unknown type")
            desc = hall.get("description", "")
            desc_snippet = (desc[:120] + "...") if len(desc) > 120 else desc

            content += f"<div class='border p-3 rounded-md'>"  # Add border and padding
            content += f"<h3 class='text-lg font-semibold'>{i+1}. {hall_name} <span class='text-base font-normal'>({hall_type})</span></h3>"
            content += f"<p class='text-sm text-secondary mt-1 mb-2'>{desc_snippet}</p>"

            if reason_list:
                content += "<p class='text-xs font-semibold'>Why it's recommended:</p>"
                content += "<ul class='list-disc list-inside ml-2 text-xs'>"
                for reason in reason_list:
                    content += f"<li>{reason.replace('+', '')}</li>"  # Nicer display
                content += "</ul>"
            content += "</div>"

            options.append({"label": f"View Details: {hall_name}", "value": hall_name})

        options.append({"label": "Compare Recommendations", "value": "compare"})

        return {
            "question": "Your Housing Recommendations",
            "options": options,
            "content": content,
            "breadcrumbs": ["Housing Matcher", "Results"],
        }

    def _format_recommendation_comparison(self, recommendations):
        """Formats a comparison table for the recommended halls."""
        if not recommendations or len(recommendations) < 2:
            return {
                "question": "Comparison Not Available",
                "options": [],
                "content": "<p>You need at least two recommendations to compare.</p>",
                "breadcrumbs": ["Housing Matcher", "Results", "Compare"],
            }

        content = (
            "<h2 class='text-xl font-semibold mb-3'>Recommendation Comparison</h2>"
        )
        content += (
            "<div class='overflow-x-auto'>"  # Allow horizontal scroll on small screens
        )
        content += "<table class='w-full text-left border-collapse border border-gray-300 text-sm'>"
        content += "<thead><tr class='border-b border-gray-300 bg-gray-50'>"
        content += "<th class='p-2 font-semibold'>Feature</th>"

        # Headers for each hall
        hall_names = []
        for hall, _, _ in recommendations:
            hall_name = hall.get("name", "N/A")
            hall_names.append(hall_name)
            content += f"<th class='p-2 font-semibold'>{hall_name}</th>"
        content += "</tr></thead><tbody>"

        # --- Rows for comparison ---
        features_to_compare = [
            ("hall_type", "Hall Type"),
            ("location", "Location"),
            ("actual_room_types", "Room Types"),
            ("features_str", "Key Features"),
            ("rates", "Typical Rate (Fall/Spring)"),
        ]

        for key, label in features_to_compare:
            content += f"<tr class='border-b border-gray-200'><td class='p-2 font-semibold align-top'>{label}</td>"
            for hall, _, _ in recommendations:
                value = "N/A"
                if key == "rates":
                    hall_name = hall.get("name")
                    if hall_name in self.rates:
                        # Find a common rate (e.g., Double) or just list a few
                        rates_list = []
                        for rt, r_data in self.rates[hall_name].items():
                            if "fall_spring" in r_data:
                                rates_list.append(f"{rt}: ${r_data['fall_spring']}")
                        value = "<br>".join(rates_list[:2])  # Show first two rates
                        if not value:
                            value = "Rates unavailable"
                elif key == "actual_room_types":
                    value = ", ".join(hall.get(key, []))
                elif key == "features_str":
                    # Show a few key features
                    features = hall.get(key, "").split(", ")
                    value = ", ".join(f for f in features if f)[:80]  # Limit length
                    if len(hall.get(key, "")) > 80:
                        value += "..."
                else:
                    value = hall.get(key, "N/A")

                if not value:
                    value = "N/A"  # Ensure display value
                content += f"<td class='p-2 align-top'>{value}</td>"
            content += "</tr>"

        content += "</tbody></table>"
        content += "</div>"  # End overflow-x-auto

        options = []
        for hall_name in hall_names:
            options.append(
                {"label": f"View Full Details: {hall_name}", "value": hall_name}
            )

        return {
            "question": "Comparing Recommendations",
            "options": options,
            "content": content,
            "breadcrumbs": ["Housing Matcher", "Results", "Compare"],
        }

    def _get_application_info(self):
        """Provides information about the housing application process."""
        # Example content - replace with actual relevant info and links
        content = """
        <h2 class="text-xl font-semibold mb-3">Housing Application Information</h2>
        <p class="mb-2">Information about applying for on-campus housing can be found on the official UF Housing & Residence Life website.</p>
        <h3 class="text-lg font-semibold mt-4 mb-1">Key Dates & Deadlines</h3>
        <p class="mb-2">Application deadlines vary depending on your student status (e.g., freshman, transfer, graduate). Please refer to the official housing calendar.</p>
        <ul class="list-disc list-inside ml-4 mb-3">
            <li>Check the UF Housing website for the most current application opening and closing dates.</li>
            <li>Pay close attention to deposit deadlines and contract signing periods.</li>
        </ul>
        <h3 class="text-lg font-semibold mt-4 mb-1">How to Apply</h3>
        <p class="mb-2">Applications are typically submitted online through the myUFL portal.</p>
        <ol class="list-decimal list-inside ml-4 mb-3">
            <li>Log in to myUFL (my.ufl.edu).</li>
            <li>Navigate to the Housing section.</li>
            <li>Follow the instructions to complete the housing application.</li>
            <li>Submit the required application fee or deposit.</li>
        </ol>
         <h3 class="text-lg font-semibold mt-4 mb-1">Important Links</h3>
         <ul class="list-disc list-inside ml-4">
            <li><a href="https://housing.ufl.edu/" target="_blank" class="text-blue-600 hover:underline">UF Housing & Residence Life Home</a></li>
            <li><a href="https://housing.ufl.edu/apply/" target="_blank" class="text-blue-600 hover:underline">Application Process Details</a></li>
            <li><a href="https://housing.ufl.edu/rates/" target="_blank" class="text-blue-600 hover:underline">Official Rates Information</a></li>
         </ul>
         <p class='mt-4 text-sm text-gray-600'>Please note: This tool provides general information. Always consult the official UF Housing website for the most accurate and up-to-date details.</p>
        """

        return {
            "question": "Housing Application Info",
            "options": [],  # No further options from here typically
            "content": content,
            "breadcrumbs": ["Application Info"],
        }
