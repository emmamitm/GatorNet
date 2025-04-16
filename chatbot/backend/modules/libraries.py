import json
import os
from collections import defaultdict


class LibrariesSystem:
    def __init__(self, json_file=None, libraries_data=None):
        """Initialize the library system with data from a file or direct input."""
        self.libraries = []
        self.matcher_questions = []
        self._load_data(json_file, libraries_data)
        self._extract_metadata()

    def _load_data(self, json_file, libraries_data):
        """Load data from either a file or direct input."""
        if json_file and os.path.exists(json_file):
            with open(json_file, "r") as f:
                data = json.load(f)
                self.libraries = data.get("libraries", [])
                self.matcher_questions = data.get("matcher_questions", [])
        elif libraries_data:
            self.libraries = libraries_data.get("libraries", [])
            self.matcher_questions = libraries_data.get("matcher_questions", [])

    def _extract_metadata(self):
        """Extract and organize metadata from libraries."""
        # Use sets for efficient unique item storage
        self.features = set()
        self.specializations = set()
        self.locations = set()

        for library in self.libraries:
            # Extract unique values
            self.features.update(library.get("features", []))
            self.specializations.update(library.get("specializations", []))
            location = library.get("location", "")
            if location:
                self.locations.add(location)

        # Convert sets to sorted lists
        self.features = sorted(self.features)
        self.specializations = sorted(self.specializations)
        self.locations = sorted(self.locations)

    def handle_menu_request(self, category, path, selection):
        """Process a menu request based on category, path, and selection."""
        if category != "libraries":
            return self._create_response("Menu not available")

        # Define route handlers for different paths
        routes = {
            "": self._get_main_menu,
            "info": self._handle_info_route,
            "matcher": self._handle_matcher_route,
        }

        # Get the main section or use empty string for root
        main_section = path[0] if path else ""

        # Call the appropriate route handler if it exists
        if main_section in routes:
            return routes[main_section](path, selection)

        # Default response if no matching route
        return self._create_response("Menu not available")

    def _handle_info_route(self, path, selection):
        """Handle requests to the library info section."""
        path_length = len(path)

        # Library list view
        if path_length == 1:
            return self._create_response(
                "Select a library for more information:",
                options=[
                    {
                        "label": lib.get("name", "Unnamed Library"),
                        "value": lib.get("name", ""),
                    }
                    for lib in self.libraries
                ],
                breadcrumbs=["Get Library Info"],
            )
        # Library details view
        elif path_length == 2:
            return self._get_library_details(path[1], None)
        # Library specific category view
        elif path_length == 3:
            return self._get_library_details(path[1], path[2])

        return self._create_response("Menu not available")

    def _handle_matcher_route(self, path, selection):
        """Handle requests to the library matcher section."""
        path_length = len(path)

        # Matcher intro
        if path_length == 1:
            return self._get_matcher_intro()
        # Start matcher with first question
        elif path_length == 2:
            return self._get_matcher_question(0, [])
        # Handle questions in progress
        elif path_length > 2 and path_length < len(self.matcher_questions) + 2:
            return self._get_matcher_question(path_length - 2, path[2:])
        # Handle results
        elif path_length == len(self.matcher_questions) + 2:
            answers = path[2:]
            return self._process_matcher_results(answers)
        # Handle library selection from results
        elif selection:
            return self._get_library_details(selection, "All Information")

        return self._create_response("Menu not available")

    def _process_matcher_results(self, answers):
        """Process matcher answers and display results."""
        # Map answers to questions
        answer_dict = {}
        for i, answer in enumerate(answers):
            if i < len(self.matcher_questions):
                q_id = self.matcher_questions[i].get("id", f"q{i}")
                answer_dict[q_id] = answer

        # Calculate scores and get best matches
        scores, reasons = self._calculate_scores(answer_dict)
        best_matches = self._get_best_matches(scores, reasons, 2)

        return self._format_matcher_results(best_matches, answers)

    def _create_response(self, question, options=None, content=None, breadcrumbs=None):
        """Create a standardized response structure."""
        response = {"question": question}
        response["options"] = options or []
        if content:
            response["content"] = content
        if breadcrumbs:
            response["breadcrumbs"] = breadcrumbs
        return response

    def _get_main_menu(self, path=None, selection=None):
        """Return the main menu options."""
        return self._create_response(
            "UF Libraries Information System",
            options=[
                {"label": "Get Library Info", "value": "info"},
                {"label": "Library Matcher", "value": "matcher"},
            ],
        )

    def _get_library_details(self, library_name, category=None):
        """Return details for a library, either for a specific category or general info."""
        # Find the library
        library = next(
            (lib for lib in self.libraries if lib.get("name", "") == library_name), None
        )

        if not library:
            return self._create_response(
                "Library Not Found",
                content=f"<p>Sorry, could not find information for '{library_name}'.</p>",
                breadcrumbs=["Get Library Info"],
            )

        # If no category is specified, show category selection
        if not category:
            categories = [
                "Location",
                "Capacity",
                "Hours",
                "Special Notes",
                "URL",
                "Phone",
                "Email",
                "Features",
                "Specializations",
                "All Information",
            ]
            return self._create_response(
                f"What information would you like to see about {library_name}?",
                options=[{"label": cat, "value": cat} for cat in categories],
                breadcrumbs=["Get Library Info", library_name],
            )

        # Generate content based on selected category
        return self._generate_library_content(library, category, library_name)

    def _generate_library_content(self, library, category, library_name):
        """Generate HTML content for library details."""
        content = f"<h3>{library_name}</h3>"

        # Determine which categories to show
        categories_to_show = (
            [
                "Location",
                "Capacity",
                "Hours",
                "Special Notes",
                "URL",
                "Phone",
                "Email",
                "Features",
                "Specializations",
            ]
            if category == "All Information"
            else [category]
        )

        for cat in categories_to_show:
            content += f"<h4>{cat}:</h4>"

            if cat.lower() in ["features", "specializations"]:
                # Handle list-type fields
                items = library.get(cat.lower(), ["No information available"])
                content += (
                    "<ul>" + "".join(f"<li>{item}</li>" for item in items) + "</ul>"
                )
            else:
                # Handle regular fields
                key = cat.lower().replace(" ", "_")
                value = (
                    library.get(key, "No information available")
                    or "Information not available"
                )
                content += f"<p>{value}</p>"

        return self._create_response(
            f"{library_name} - {category}",
            content=content,
            breadcrumbs=["Get Library Info", library_name, category],
        )

    def _get_matcher_intro(self):
        """Return the introduction to the library matcher."""
        content = """
        <div>
            <p>The Library Matcher will help you find the best library for your needs by asking a few questions about your preferences.</p>
            <p>We'll analyze your answers and recommend the most suitable library on campus.</p>
        </div>
        """

        return self._create_response(
            "Library Matcher",
            options=[
                {
                    "label": "Start the Library Matcher",
                    "value": "start",
                    "description": "Find the perfect library for your needs",
                }
            ],
            content=content,
            breadcrumbs=["Library Matcher"],
        )

    def _get_matcher_question(self, question_index, previous_answers):
        """Return a specific matcher question."""
        if question_index < 0 or question_index >= len(self.matcher_questions):
            return self._create_response("Menu not available")

        question_data = self.matcher_questions[question_index]
        question_text = question_data.get("question", "No question available")
        options = question_data.get("options", [])

        return self._create_response(
            question_text,
            options=[{"label": option, "value": option} for option in options],
            content=f"<p class='text-sm text-gray-500'>Question {question_index + 1} of {len(self.matcher_questions)}</p>",
            breadcrumbs=["Library Matcher", f"Question {question_index + 1}"],
        )

    def _calculate_scores(self, preferences):
        """Calculate scores for each library based on user preferences."""
        # Map preference categories to keywords for matching
        keyword_mappings = {
            "purpose": {
                "General study": ["study spaces", "quiet study", "study areas"],
                "Research": ["research assistance", "special collections", "reference"],
                "Group project": ["group study", "collaboration", "group spaces"],
                "Access special collections": [
                    "rare books",
                    "archives",
                    "special collections",
                ],
                "Use specialized equipment": [
                    "makerspace",
                    "equipment",
                    "computers",
                    "technology",
                ],
                "Quiet reading": ["quiet", "reading", "quiet areas"],
            },
            "subject": {
                "General/Humanities": [
                    "general",
                    "humanities",
                    "history",
                    "literature",
                    "philosophy",
                ],
                "Science/Technology/Engineering/Math": [
                    "science",
                    "technology",
                    "engineering",
                    "mathematics",
                    "stem",
                ],
                "Health Sciences/Medicine": [
                    "health",
                    "medical",
                    "medicine",
                    "nursing",
                    "pharmacy",
                ],
                "Law": ["law", "legal", "government"],
                "Architecture/Fine Arts": [
                    "architecture",
                    "fine arts",
                    "design",
                    "art",
                    "visual",
                ],
                "Education": ["education", "teaching", "learning", "educational"],
            },
        }

        # Initialize scores and reasons
        scores = {lib["name"]: 0 for lib in self.libraries}
        reasons = defaultdict(list)

        # Extract user preferences
        purpose = preferences.get("purpose", "")
        subject = preferences.get("subject", "")
        desired_features = preferences.get("features", "")
        visit_time = preferences.get("time", "")

        # Score each library
        for library in self.libraries:
            lib_name = library["name"]
            specializations = " ".join(library.get("specializations", [])).lower()
            features_list = library.get("features", [])
            features_text = " ".join(features_list).lower()
            score = 0

            # Calculate subject match score (0-5 points)
            subject_score, subject_reason = self._score_subject_match(
                subject, specializations, keyword_mappings
            )
            score += subject_score
            if subject_reason:
                reasons[lib_name].append(subject_reason)

            # Calculate purpose match score (0-3 points)
            purpose_score, purpose_reason = self._score_purpose_match(
                purpose, features_text, features_list, keyword_mappings
            )
            score += purpose_score
            if purpose_reason:
                reasons[lib_name].append(purpose_reason)

            # Calculate features match score (0-4 points)
            features_score, features_reason = self._score_features_match(
                desired_features, features_list, library
            )
            score += features_score
            if features_reason:
                reasons[lib_name].append(features_reason)

            # Calculate time availability score (0-2 points)
            time_score, time_reason = self._score_time_match(
                visit_time, library.get("hours", "").lower()
            )
            score += time_score
            if time_reason:
                reasons[lib_name].append(time_reason)

            # Calculate bonus scores for specific combinations (0-2 points)
            bonus_score, bonus_reasons = self._score_special_bonuses(
                specializations, features_text, purpose, subject
            )
            score += bonus_score
            reasons[lib_name].extend(bonus_reasons)

            scores[lib_name] = score

        return scores, dict(reasons)

    def _score_subject_match(self, subject, specializations, keyword_mappings):
        """Score a library based on subject match."""
        if not subject:
            return 0, None

        subject_keywords = keyword_mappings["subject"].get(subject, [])

        if any(keyword in specializations for keyword in subject_keywords):
            return 5, f"Specializes in {subject}"
        elif any(
            subj_term in specializations for subj_term in subject.lower().split("/")
        ):
            return 3, f"Has relevant resources for {subject}"
        return 0, None

    def _score_purpose_match(
        self, purpose, features_text, features_list, keyword_mappings
    ):
        """Score a library based on purpose match."""
        if not purpose:
            return 0, None

        purpose_keywords = keyword_mappings["purpose"].get(purpose, [])

        if any(keyword in features_text for keyword in purpose_keywords):
            return 3, f"Excellent for {purpose.lower()}"

        # Check special cases
        if purpose == "Research" and "research assistance" in features_list:
            return 3, "Provides research assistance"
        elif purpose == "Group project" and "group study rooms" in features_list:
            return 3, "Has group study rooms"
        elif purpose == "Quiet reading" and "quiet study areas" in features_list:
            return 3, "Has quiet study areas"

        return 0, None

    def _score_features_match(self, desired_features, features_list, library):
        """Score a library based on feature match."""
        if not desired_features:
            return 0, None

        # Map of desired features to matching library features and reason text
        feature_mappings = {
            "Group study spaces": (
                ["group study rooms"],
                "Has dedicated group study rooms",
            ),
            "Quiet study areas": (
                ["quiet study areas"],
                "Has designated quiet study areas",
            ),
            "Special collections access": (
                ["special collections"],
                "Provides access to special collections",
            ),
            "Computers and technology": (
                ["computers"],
                "Offers computer and technology resources",
            ),
            "Research assistance": (
                ["research assistance"],
                "Provides dedicated research assistance",
            ),
            "Large capacity": ([], "Has large seating capacity"),
        }

        # Check for direct feature matches
        if desired_features in feature_mappings:
            matching_features, reason = feature_mappings[desired_features]

            # Special case for capacity
            if desired_features == "Large capacity":
                if library.get("capacity") and self._is_large_capacity(
                    library.get("capacity")
                ):
                    return 4, reason
            # Check for matching features in library's feature list
            elif any(feature in features_list for feature in matching_features):
                return 4, reason

        return 0, None

    def _score_time_match(self, visit_time, hours):
        """Score a library based on time availability."""
        if not visit_time:
            return 0, None

        # Map visit times to library hours and reasons
        time_mappings = {
            "Late night (after 10pm)": ((["2am", "24"], 2), "Open late at night"),
            "Weekend": ((["sat", "sun", "weekend"], 2), "Open on weekends"),
            "Weekday daytime": (([], 1), None),  # Most libraries are open weekdays
            "Weekday evening (after 5pm)": (
                (["10pm", "evening", "night"], 2),
                "Open during evening hours",
            ),
        }

        if visit_time in time_mappings:
            (terms, score), reason = time_mappings[visit_time]
            if not terms or any(term in hours for term in terms):
                return score, reason

        return 0, None

    def _score_special_bonuses(self, specializations, features_text, purpose, subject):
        """Calculate bonus scores for specific combinations."""
        score = 0
        reasons = []

        # Special collections bonus
        if (
            "special collections" in specializations
            and purpose == "Access special collections"
        ):
            score += 2
            reasons.append("Specializes in rare and special collections")

        # Makerspace bonus
        if "makerspace" in features_text and purpose == "Use specialized equipment":
            score += 2
            reasons.append("Has a makerspace with specialized equipment")

        # Health sciences bonus
        if "health" in specializations and subject == "Health Sciences/Medicine":
            score += 1
            reasons.append("Dedicated to health sciences resources")

        # Law resources bonus
        if "law" in specializations and subject == "Law":
            score += 1
            reasons.append("Specializes in legal resources")

        return score, reasons

    def _is_large_capacity(self, capacity):
        """Determine if a library has large capacity."""
        if capacity is None:
            return False

        # Handle integer capacity
        if isinstance(capacity, int):
            return capacity > 1000

        # Extract numbers from string
        try:
            if isinstance(capacity, str):
                digits = "".join(filter(str.isdigit, capacity))
                if digits:
                    return int(digits) > 1000
        except:
            pass

        return False

    def _get_best_matches(self, scores, reasons, count=2):
        """Find the best library matches based on scores."""
        if not scores:
            return []

        # Find libraries with the highest score
        max_score = max(scores.values())
        best_matches = [lib for lib, score in scores.items() if score == max_score]

        # Tie-breaker 1: Number of reasons
        if len(best_matches) > 1:
            reason_counts = {lib: len(reasons.get(lib, [])) for lib in best_matches}
            most_reasons = max(reason_counts.values())
            best_matches = [
                lib for lib, count in reason_counts.items() if count == most_reasons
            ]

        # Tie-breaker 2: Library capacity
        if len(best_matches) > 1:
            best_matches = self._break_tie_by_capacity(best_matches)

        # Create result list with the top match and alternates
        result = [
            {
                "name": best_matches[0],
                "score": scores[best_matches[0]],
                "reasons": reasons.get(best_matches[0], []),
            }
        ]

        # Add alternative matches if available
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        for lib, score in sorted_scores:
            if lib not in best_matches and len(result) < count:
                result.append(
                    {"name": lib, "score": score, "reasons": reasons.get(lib, [])}
                )

        return result

    def _break_tie_by_capacity(self, library_names):
        """Break ties between libraries using capacity data."""
        capacities = {}
        for lib_name in library_names:
            library = next(
                (lib for lib in self.libraries if lib["name"] == lib_name), None
            )
            capacity = library.get("capacity") if library else None

            # Extract numeric capacity value
            if isinstance(capacity, int):
                capacities[lib_name] = capacity
            elif isinstance(capacity, str) and capacity.isdigit():
                capacities[lib_name] = int(capacity)
            else:
                capacities[lib_name] = 0

        # Return highest capacity library or first library if no capacity data
        if any(capacities.values()):
            return [max(capacities.items(), key=lambda x: x[1])[0]]
        else:
            return [library_names[0]]

    def _format_matcher_results(self, best_matches, answers):
        """Format the matcher results for display."""
        if not best_matches:
            return self._create_response(
                "No Matches Found",
                content="<p>Sorry, no library matches were found based on your preferences.</p>",
                breadcrumbs=["Library Matcher", "Results"],
            )

        # Get the top library
        top_match = best_matches[0]
        content = self._generate_results_html(top_match, best_matches, answers)

        # Create options for viewing library details
        library_options = [
            {"label": f"View details for {match['name']}", "value": match["name"]}
            for match in best_matches
        ]

        return self._create_response(
            "Library Recommendation",
            options=library_options,
            content=content,
            breadcrumbs=["Library Matcher", "Results"],
        )

    def _generate_results_html(self, top_match, best_matches, answers):
        """Generate HTML content for the matcher results."""
        content = f"""
        <div class="library-matcher-results">
            <h3>Library Recommendation</h3>
            <p>Based on your preferences, I recommend <strong>{top_match['name']}</strong>.</p>
            
            <h4>Analysis of your preferences:</h4>
            <ul>
        """

        # Add user preferences
        for i, question in enumerate(self.matcher_questions):
            if i < len(answers):
                q_text = question.get("question")
                content += f"<li><strong>{q_text}:</strong> {answers[i]}</li>"

        content += f"""
            </ul>
            <p><strong>Match Score:</strong> {top_match['score']}/14</p>
            
            <h4>Why this is a good match:</h4>
            <ul>
        """

        # Add top reasons
        for reason in top_match["reasons"][:3]:
            content += f"<li>{reason}</li>"
        content += "</ul>"

        # Add library details
        top_library = next(
            (lib for lib in self.libraries if lib.get("name", "") == top_match["name"]),
            None,
        )

        if top_library:
            content += self._generate_library_summary(top_library, top_match["name"])

        # Check for late night Library West access
        answer_dict = {
            self.matcher_questions[i].get("id", f"q{i}"): answers[i]
            for i in range(min(len(answers), len(self.matcher_questions)))
        }

        if (
            "time" in answer_dict
            and answer_dict["time"] == "Late night (after 10pm)"
            and "Library West" in top_match["name"]
        ):
            content += "<p><strong>Special Note:</strong> For late night access to Library West, you'll need an active UF ID or Santa Fe College ID.</p>"

        # Add alternative option if available
        if len(best_matches) > 1:
            alt_match = best_matches[1]
            content += f"""
            <h4>Alternative Option:</h4>
            <p>If {top_match['name']} doesn't work for you, consider {alt_match['name']} as an alternative.</p>
            <p>(Match score: {alt_match['score']}/14)</p>
            """

        return content

    def _generate_library_summary(self, library, name):
        """Generate HTML summary of a library's key details."""
        content = f"""
        <h4>About {name}:</h4>
        <ul>
            <li><strong>Location:</strong> {library.get('location', 'Not specified')}</li>
            <li><strong>Hours:</strong> {library.get('hours', 'Not specified')}</li>
        """

        # Add specializations (limited to 3)
        specializations = library.get("specializations", [])
        if specializations:
            content += "<li><strong>Specializes in:</strong> "
            if len(specializations) <= 3:
                content += ", ".join(specializations)
            else:
                content += (
                    ", ".join(specializations[:3])
                    + f" and {len(specializations) - 3} more areas"
                )
            content += "</li>"

        # Add features (limited to 3)
        features = library.get("features", [])
        if features:
            content += "<li><strong>Features:</strong> "
            if len(features) <= 3:
                content += ", ".join(features)
            else:
                content += ", ".join(features[:3]) + f" and {len(features) - 3} more"
            content += "</li>"

        content += "</ul>"
        return content
