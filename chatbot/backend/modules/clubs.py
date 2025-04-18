import json
import os


class ClubsSystem:
    def __init__(self, json_file=None, club_data=None):
        """Initialize with either a JSON file or direct data"""
        self.clubs = []
        self.category_groups = []
        self.categories = []
        self.matcher_questions = []
        self._last_search_results = []
        self._last_recommendation_results = []

        if json_file and os.path.exists(json_file):
            with open(json_file, "r") as f:
                data = json.load(f)
                self.clubs = data.get("clubs", [])
                self.category_groups = data.get("category_groups", [])
                self.categories = data.get("categories", [])
                self.matcher_questions = data.get("matcher_questions", [])
        elif club_data:
            self.clubs = club_data.get("clubs", [])
            self.category_groups = club_data.get("category_groups", [])
            self.categories = club_data.get("categories", [])
            self.matcher_questions = club_data.get("matcher_questions", [])

        self.build_mappings()

    def build_mappings(self):
        """Build helper mappings for searching"""
        # Map categories to subcategories
        self.category_subcategories = {}
        for category in self.categories:
            self.category_subcategories[category["name"]] = category["subcategories"]

        # Map groups to categories
        self.group_categories = {}
        for group in self.category_groups:
            self.group_categories[group["group_name"]] = group["categories"]

        # Flat lists for easier access
        self.all_categories = []
        for group in self.category_groups:
            self.all_categories.extend(group["categories"])

        self.all_subcategories = []
        for category in self.categories:
            self.all_subcategories.extend(category["subcategories"])

    def handle_menu_request(self, category, path, selection=None):
        """Process a menu request based on category, path, and selection"""
        if category != "clubs":
            return self._default_response()

        # Root menu (no path)
        if not path:
            return self._get_main_menu()

        # Process based on first path element
        main_section = path[0]

        # If no selection is provided, use the last path element
        if not selection and len(path) > 1:
            selection = path[-1]

        if main_section == "browse":
            if len(path) >= 1:
                if path[-1].startswith("page_"):
                    page = int(path[-1].split("_")[1])
                    return self._get_club_list(page)
                elif path[-1].isdigit():
                    # View specific club
                    return self._get_club_info(path[-1])
                else:
                    # View all clubs
                    return self._get_club_list()

        elif main_section == "search":
            if len(path) == 1:
                return self._get_search_menu()
            elif path[1] == "category_group":
                if len(path) == 2:
                    return self._get_category_groups()
                elif len(path) == 3:
                    return self._get_categories_in_group(path[2])
                elif len(path) == 4:
                    results = self._find_clubs_by_interest(path[3])
                    self._last_search_results = results
                    return self._format_search_results(results, 1)
                else:
                    if selection and selection.isdigit():
                        return self._get_club_info(selection)
                    elif selection and selection.startswith("page_"):
                        page = int(selection.split("_")[1])
                        return self._format_search_results(
                            self._last_search_results, page
                        )
            elif path[1] == "category":
                if len(path) == 2:
                    return self._get_categories()
                elif len(path) == 3:
                    return self._get_subcategories(path[2])
                elif len(path) == 4:
                    results = self._find_clubs_by_interest(path[3])
                    self._last_search_results = results
                    return self._format_search_results(results, 1)
                else:
                    if selection and selection.isdigit():
                        return self._get_club_info(selection)
                    elif selection and selection.startswith("page_"):
                        page = int(selection.split("_")[1])
                        return self._format_search_results(
                            self._last_search_results, page
                        )
            elif path[1] == "keyword":
                if len(path) == 2:
                    return self._get_keyword_search_form()
                elif len(path) == 3:
                    results = self._find_clubs_by_keyword(path[2])
                    self._last_search_results = results
                    return self._format_search_results(results, 1)
                else:
                    if selection and selection.isdigit():
                        return self._get_club_info(selection)
                    elif selection and selection.startswith("page_"):
                        page = int(selection.split("_")[1])
                        return self._format_search_results(
                            self._last_search_results, page
                        )
            elif path[1] == "id":
                if len(path) == 2:
                    return self._get_id_search_form()
                elif len(path) == 3:
                    return self._get_club_info_by_id(path[2])
            elif path[1] == "results":
                page = int(selection) if selection and str(selection).isdigit() else 1
                return self._format_search_results(self._last_search_results, page)

        elif main_section == "matcher":
            if len(path) == 1:
                return self._get_matcher_question(0, {})
            elif path[1] == "results":
                if len(path) == 2:
                    # Show matcher results
                    matches = self._calculate_club_matches(selection)
                    self._last_recommendation_results = [m["club"] for m in matches]
                    return self._format_recommendation_results(matches, selection)
                else:
                    # View specific club from results
                    return self._get_club_info(path[2])
            else:
                # Process matcher questions
                question_id = len(path) - 2
                if question_id < 0:
                    question_id = 0

                # Build previous answers
                previous_answers = {}
                for i in range(min(len(path) - 1, len(self.matcher_questions))):
                    if i + 1 < len(path):
                        q_id = (
                            self.matcher_questions[i]["id"]
                            if i < len(self.matcher_questions)
                            else f"q{i}"
                        )
                        previous_answers[q_id] = path[i + 1]

                # Add current selection
                if selection and question_id < len(self.matcher_questions):
                    q_id = self.matcher_questions[question_id]["id"]
                    previous_answers[q_id] = selection

                    # If last question, show results
                    if question_id == len(self.matcher_questions) - 1:
                        matches = self._calculate_club_matches(previous_answers)
                        self._last_recommendation_results = [m["club"] for m in matches]
                        return self._format_recommendation_results(
                            matches, previous_answers
                        )

                    # Otherwise go to next question
                    return self._get_matcher_question(question_id + 1, previous_answers)

                return self._get_matcher_question(question_id, previous_answers)

        elif main_section == "getting_involved":
            return self._get_getting_involved_info()

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
            "question": "UF Club Selection System",
            "options": [
                {"label": "Browse All Clubs", "value": "browse"},
                {"label": "Search Clubs", "value": "search"},
                {"label": "Club Matcher", "value": "matcher"},
                {"label": "Getting Involved", "value": "getting_involved"},
            ],
            "content": "<p>This tool helps you find student organizations that match your interests.</p>",
            "breadcrumbs": [],
        }

    def _get_club_list(self, page=1):
        """Return paginated list of clubs"""
        sorted_clubs = sorted(self.clubs, key=lambda x: x.get("Organization Name", ""))
        page_size = 20
        total_clubs = len(sorted_clubs)
        total_pages = (total_clubs + page_size - 1) // page_size
        page = max(1, min(page, total_pages))
        start_idx = (page - 1) * page_size
        end_idx = min(start_idx + page_size, total_clubs)
        page_clubs = sorted_clubs[start_idx:end_idx]

        content = f"<p>Showing clubs {start_idx+1}-{end_idx} of {total_clubs} (Page {page}/{total_pages})</p>"
        content += "<div class='club-list'>"
        for club in page_clubs:
            content += f"<div class='club-item'><h3>{club.get('Organization Name', 'Unnamed Club')}</h3></div>"
        content += "</div>"

        options = []
        for club in page_clubs:
            club_id = club.get("ID", "")
            options.append(
                {
                    "label": club.get("Organization Name", "Unnamed Club"),
                    "value": f"{club_id}",
                }
            )

        if page > 1:
            options.append({"label": "« Previous Page", "value": f"page_{page-1}"})
        if page < total_pages:
            options.append({"label": "Next Page »", "value": f"page_{page+1}"})

        return {
            "question": "Browse All Clubs",
            "options": options,
            "content": content,
            "breadcrumbs": ["Browse"],
            "pagination": {
                "current_page": page,
                "total_pages": total_pages,
                "total_results": total_clubs,
            },
        }

    def _get_club_info(self, club_id):
        """Get club details by ID"""
        club = next(
            (c for c in self.clubs if str(c.get("ID", "")) == str(club_id)), None
        )

        if not club:
            return {
                "question": "Club Not Found",
                "options": [],
                "content": "<p>Sorry, the requested club was not found.</p>",
                "breadcrumbs": ["Club Details"],
            }

        content = f"""
        <div class="club-details">
            <h2>{club.get('Organization Name', 'Unnamed Club')}</h2>
            <div class="club-section">
                <h3>Description</h3>
                <p>{club.get('Description', 'No description available')}</p>
            </div>
            <div class="club-section">
                <h3>Contact Information</h3>
                <p><strong>ID:</strong> {club.get('ID', 'Not available')}</p>
            </div>
        </div>
        """

        return {
            "question": f"Club Details: {club.get('Organization Name', 'Unnamed Club')}",
            "options": [],
            "content": content,
            "breadcrumbs": ["Club Details"],
        }

    def _get_search_menu(self):
        """Return search menu options"""
        return {
            "question": "Search Clubs",
            "options": [
                {"label": "Search by category group", "value": "category_group"},
                {"label": "Search by specific category", "value": "category"},
                {"label": "Search by keyword", "value": "keyword"},
                {"label": "Search by ID", "value": "id"},
            ],
            "content": "<p>Select a search method to find clubs.</p>",
            "breadcrumbs": ["Search"],
        }

    def _get_category_groups(self):
        """Return category groups for selection"""
        options = [
            {"label": g["group_name"], "value": g["group_name"]}
            for g in self.category_groups
        ]
        return {
            "question": "Select a Category Group",
            "options": options,
            "content": "<p>Choose a category group to see its categories.</p>",
            "breadcrumbs": ["Search", "By Category Group"],
        }

    def _get_categories_in_group(self, group_name):
        """Return categories in the selected group"""
        categories = self.group_categories.get(group_name, [])
        options = [{"label": category, "value": category} for category in categories]
        return {
            "question": f"Categories in {group_name}",
            "options": options,
            "content": "<p>Select a category to see subcategories.</p>",
            "breadcrumbs": ["Search", "By Category Group", group_name],
        }

    def _get_categories(self):
        """Return all categories for selection"""
        options = [
            {"label": category, "value": category}
            for category in sorted(self.all_categories)
        ]
        return {
            "question": "Select a Category",
            "options": options,
            "content": "<p>Choose a category to see subcategories.</p>",
            "breadcrumbs": ["Search", "By Category"],
        }

    def _get_subcategories(self, category_name):
        """Return subcategories for the selected category"""
        subcategories = self.category_subcategories.get(category_name, [])
        options = [{"label": sub, "value": sub} for sub in subcategories]
        return {
            "question": f"Subcategories of {category_name}",
            "options": options,
            "content": "<p>Select a subcategory to find clubs.</p>",
            "breadcrumbs": ["Search", "By Category", category_name],
        }

    def _get_keyword_search_form(self):
        """Return keyword search form"""
        return {
            "question": "Search by Keyword",
            "options": [],
            "content": "<p>Enter a keyword to search in club names and descriptions.</p>",
            "breadcrumbs": ["Search", "By Keyword"],
            "hasCustomInput": True,
            "inputPlaceholder": "Enter keyword",
        }

    def _get_id_search_form(self):
        """Return ID search form"""
        return {
            "question": "Search by ID",
            "options": [],
            "content": "<p>Enter the club ID number.</p>",
            "breadcrumbs": ["Search", "By ID"],
            "hasCustomInput": True,
            "inputPlaceholder": "Enter club ID",
        }

    def _get_club_info_by_id(self, club_id):
        """Find and return club by ID"""
        try:
            numeric_id = int(club_id)
            club = next(
                (c for c in self.clubs if int(c.get("ID", 0)) == numeric_id), None
            )
            if club:
                return self._get_club_info(club_id)
            else:
                return {
                    "question": "Club Not Found",
                    "options": [],
                    "content": f"<p>No club found with ID {club_id}.</p>",
                    "breadcrumbs": ["Search", "By ID"],
                }
        except ValueError:
            return {
                "question": "Invalid ID",
                "options": [],
                "content": "<p>Please enter a valid numeric ID.</p>",
                "breadcrumbs": ["Search", "By ID"],
            }

    def _find_clubs_by_interest(self, interest):
        """Find clubs matching an interest"""
        interest_lower = interest.lower()
        return [
            c
            for c in self.clubs
            if interest_lower in str(c.get("Description", "")).lower()
            or interest_lower in str(c.get("Organization Name", "")).lower()
        ]

    def _find_clubs_by_keyword(self, keyword):
        """Find clubs matching a keyword"""
        keyword_lower = keyword.lower()
        return [
            c
            for c in self.clubs
            if keyword_lower in str(c.get("Description", "")).lower()
            or keyword_lower in str(c.get("Organization Name", "")).lower()
        ]

    def _format_search_results(self, results, page=1):
        """Format paginated search results"""
        if not results:
            return {
                "question": "No Clubs Found",
                "options": [],
                "content": "<p>No clubs found matching your criteria.</p>",
                "breadcrumbs": ["Search", "Results"],
            }

        sorted_results = sorted(results, key=lambda x: x.get("Organization Name", ""))
        page_size = 10
        total_results = len(sorted_results)
        total_pages = (total_results + page_size - 1) // page_size
        page = max(1, min(page, total_pages))
        start_idx = (page - 1) * page_size
        end_idx = min(start_idx + page_size, total_results)
        page_results = sorted_results[start_idx:end_idx]

        content = f"<p>Showing results {start_idx+1}-{end_idx} of {total_results} clubs (Page {page}/{total_pages})</p>"
        content += "<div class='club-results'>"
        for club in page_results:
            content += f"<div class='club-result-item'><h3>{club.get('Organization Name', 'Unnamed Club')}</h3></div>"
        content += "</div>"

        options = []
        for club in page_results:
            club_id = club.get("ID", "")
            options.append(
                {
                    "label": club.get("Organization Name", "Unnamed Club"),
                    "value": f"{club_id}",
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
            matches = self._calculate_club_matches(previous_answers)
            self._last_recommendation_results = [m["club"] for m in matches]
            return self._format_recommendation_results(matches, previous_answers)

        question_data = self.matcher_questions[question_id]
        q_id = question_data["id"]
        question = question_data["question"]

        # Handle dynamic options
        if q_id == "primary_interest" and previous_answers.get("category_group"):
            options = self.group_categories.get(previous_answers["category_group"], [])
            option_list = [{"label": opt, "value": opt} for opt in options]
        elif q_id == "subcategory_interests" and previous_answers.get(
            "primary_interest"
        ):
            options = self.category_subcategories.get(
                previous_answers["primary_interest"], []
            )
            multiple = question_data.get("multiple", False)
            select_count = question_data.get("select_count", 3)
            option_list = [
                {
                    "label": opt,
                    "value": opt,
                    "type": "checkbox" if multiple else "radio",
                }
                for opt in options
            ]

            if multiple:
                return {
                    "question": question,
                    "options": option_list,
                    "content": f"<p>Select up to {select_count} options.</p>",
                    "breadcrumbs": ["Club Matcher", f"Question {question_id+1}"],
                    "metadata": {
                        "question_id": question_id,
                        "question_key": q_id,
                        "multiple_selection": True,
                        "select_count": select_count,
                    },
                }
        else:
            options = question_data.get("options", [])
            if isinstance(options, str):
                if "dynamically_populated" in options:
                    return self._get_matcher_question(question_id + 1, previous_answers)

            multiple = question_data.get("multiple", False)
            select_count = question_data.get("select_count", 3)
            option_list = [
                {
                    "label": opt,
                    "value": opt,
                    "type": "checkbox" if multiple else "radio",
                }
                for opt in options
            ]

            if multiple:
                return {
                    "question": question,
                    "options": option_list,
                    "content": f"<p>Select up to {select_count} options.</p>",
                    "breadcrumbs": ["Club Matcher", f"Question {question_id+1}"],
                    "metadata": {
                        "question_id": question_id,
                        "question_key": q_id,
                        "multiple_selection": True,
                        "select_count": select_count,
                    },
                }

        return {
            "question": question,
            "options": option_list,
            "content": "<p>Select an option that best matches your preference.</p>",
            "breadcrumbs": ["Club Matcher", f"Question {question_id+1}"],
            "metadata": {"question_id": question_id, "question_key": q_id},
        }

    def _calculate_club_matches(self, preferences):
        """Calculate club match scores"""
        matches = []

        selected_subcategories = preferences.get("subcategory_interests", [])
        if not isinstance(selected_subcategories, list):
            selected_subcategories = [selected_subcategories]

        commitment_level = preferences.get("commitment_level", "")

        for club in self.clubs:
            score = 0
            match_reasons = []
            description = str(club.get("Description", "")).lower()
            org_name = str(club.get("Organization Name", "")).lower()

            # Score subcategory matches
            for subcategory in selected_subcategories:
                subcategory_lower = subcategory.lower()
                if subcategory_lower in description or subcategory_lower in org_name:
                    score += 2
                    match_reasons.append(f"Matches your interest in {subcategory}")
                elif any(word in description for word in subcategory_lower.split()):
                    score += 1
                    match_reasons.append(
                        f"Partially matches your interest in {subcategory}"
                    )

            # Score commitment level
            if commitment_level:
                keywords = {
                    "Casual interest (1-2 hours/week)": [
                        "casual",
                        "informal",
                        "social",
                        "occasional",
                    ],
                    "Regular involvement (3-5 hours/week)": [
                        "regular",
                        "weekly",
                        "meetings",
                        "participate",
                    ],
                    "Dedicated participation (6-10 hours/week)": [
                        "dedicated",
                        "commitment",
                        "competitive",
                        "events",
                    ],
                    "Leadership role (10+ hours/week)": [
                        "leadership",
                        "executive",
                        "organize",
                        "manage",
                    ],
                }

                for keyword in keywords.get(commitment_level, []):
                    if keyword in description:
                        score += 1
                        match_reasons.append(
                            f"Matches your {commitment_level} preference"
                        )
                        break

            if score > 0:
                matches.append(
                    {"club": club, "score": score, "reasons": match_reasons[:3]}
                )

        return sorted(matches, key=lambda x: x["score"], reverse=True)

    def _format_recommendation_results(self, matches, preferences):
        """Format club recommendation results"""
        if not matches:
            return {
                "question": "No Matching Clubs",
                "options": [],
                "content": "<p>Sorry, we couldn't find any clubs matching your preferences.</p>",
                "breadcrumbs": ["Club Matcher", "Results"],
            }

        content = "<div class='recommendation-results'><h3>Top Club Matches</h3>"
        top_matches = matches[: min(10, len(matches))]

        for i, match in enumerate(top_matches, 1):
            club = match["club"]
            score = match["score"]
            reasons = match["reasons"]

            content += f"<div class='recommendation-item'><h4>{i}. {club.get('Organization Name', 'Unnamed Club')}</h4>"
            content += f"<p><strong>Match Score:</strong> {score}</p>"

            if reasons:
                content += "<div class='match-reasons'><p><strong>Why this is a good match:</strong></p><ul>"
                for reason in reasons:
                    content += f"<li>{reason}</li>"
                content += "</ul></div>"

            content += "</div>"

        content += "</div>"

        options = []
        for match in top_matches:
            club = match["club"]
            club_id = club.get("ID", "")
            options.append(
                {
                    "label": club.get("Organization Name", "Unnamed Club"),
                    "value": f"{club_id}",
                }
            )

        return {
            "question": "Club Recommendations",
            "options": options,
            "content": content,
            "breadcrumbs": ["Club Matcher", "Results"],
        }

    def _get_getting_involved_info(self):
        """Return getting involved information"""
        content = """
        <div class="getting-involved">
            <h2>How to Get Involved in UF Organizations</h2>
            <div class="section">
                <h3>1. Explore and Research</h3>
                <p>Browse organizations, attend the Student Organization Fair, and visit organization websites.</p>
            </div>
            <div class="section">
                <h3>2. Attend Meetings and Events</h3>
                <p>Most organizations welcome new members to general meetings. Check GatorConnect for meeting times.</p>
            </div>
            <div class="section">
                <h3>3. Resources</h3>
                <p>GatorConnect: <a href="https://orgs.studentinvolvement.ufl.edu/">https://orgs.studentinvolvement.ufl.edu/</a></p>
            </div>
        </div>
        """

        return {
            "question": "Getting Involved",
            "options": [],
            "content": content,
            "breadcrumbs": ["Getting Involved"],
        }
