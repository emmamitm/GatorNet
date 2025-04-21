import json
import os


class CoursesSystem:  # Renamed from CourseSystem to CoursesSystem for consistency
    def __init__(
        self, json_file=None, course_data=None
    ):  # Changed parameter name from courses_data to course_data for consistency
        """Initialize with either a JSON file or direct data"""
        if json_file and os.path.exists(json_file):
            with open(json_file, "r") as f:
                self.data = json.load(f)
        elif course_data:
            # Load data directly from provided dictionary
            self.data = course_data
        else:
            self.data = {"matcher_questions": [], "courses": [], "college_groups": []}

        self.matcher_questions = self.data.get("matcher_questions", [])
        self.courses = self.data.get("courses", [])
        self.college_groups = self.data.get("college_groups", [])

        self._last_search_results = []
        self._last_recommendation_results = []

        # Build comprehensive mappings from JSON data
        self.build_mappings()

    def build_mappings(self):
        """Build comprehensive mappings from JSON data"""
        # Build college mapping from college_groups
        self.category_mapping = {}
        for group in self.college_groups:
            group_name = group.get("group_name", "")
            self.category_mapping[group_name] = [group_name]

        # Map each department to its college group
        self.department_to_college = {}
        for group in self.college_groups:
            group_name = group.get("group_name", "")
            departments = group.get("departments", [])
            for dept in departments:
                self.department_to_college[dept] = group_name

        # Build department mapping
        self.department_mapping = {}
        for group in self.college_groups:
            departments = group.get("departments", [])
            for dept in departments:
                simplified_dept = dept.split(" | ")[
                    0
                ]  # Handle cases like "Biology | Botany | Zoology"
                self.department_mapping[simplified_dept] = []
                for d in dept.split(" | "):
                    self.department_mapping[simplified_dept].append(d)

        # Level mapping
        self.level_mapping = {
            "Introductory (1000-2000 levels)": ["1000-level", "2000-level"],
            "Intermediate (3000-4000 levels)": ["3000-level", "4000-level"],
            "Advanced/Graduate (5000+ levels)": [
                "5000-level",
                "6000-level",
                "7000-level",
            ],
        }

        # Theme mapping - build from course_themes
        self.theme_mapping = {
            "Practical Skills": ["Applications & Practice", "Professional Development"],
            "Theoretical Knowledge": ["Theory & Concepts", "History & Heritage"],
            "Research & Analysis": ["Research & Analysis"],
            "Professional Development": ["Professional Development"],
            "Creative & Design": ["Design & Creativity"],
            "Technology & Computing": ["Technology & Computing"],
        }

        self.credit_mapping = {
            "1-2 Credits": ["1", "2"],
            "3-4 Credits": ["3", "4"],
            "5+ Credits": ["5", "6", "7", "8", "9", "10", "11", "12"],
        }

    def handle_menu_request(self, category, path, selection=None):
        """Process a menu request based on category, path, and selection"""
        if category != "courses":
            return self._default_response()

        # Root menu (no path)
        if not path:
            return self._get_main_menu()

        if not selection:
            selection = (
                path[-1] if path else None
            )  # Default to last path element if no selection provided

        # Process based on first path element
        main_section = path[0]

        if main_section == "find_course":
            if len(path) == 1:
                return self._get_course_search_form()
            elif len(path) == 2:
                return self._get_course_info(path[1])
            elif selection:
                # Handle the case where the course code comes from selection
                return self._get_course_info(selection)

        elif main_section == "search":
            if len(path) == 1:
                return self._get_search_menu()
            elif len(path) == 2:
                if path[1] == "code":
                    return self._get_code_search_form()
                elif path[1] == "title":
                    return self._get_title_search_form()
                elif path[1] == "department":
                    return self._get_department_selection()
                elif path[1] == "level":
                    return self._get_level_selection()
            elif len(path) == 3:
                if path[1] == "code":
                    # Handle code search
                    return self._search_courses(
                        {
                            "search_type": "code",
                            "search_term": selection,
                        }
                    )
                elif path[1] == "title":
                    # Handle title search
                    return self._search_courses(
                        {
                            "search_type": "title",
                            "search_term": selection,
                        }
                    )
                elif path[1] == "department":
                    # Handle department search
                    return self._search_courses(
                        {
                            "search_type": "department",
                            "dept_idx": selection,
                        }
                    )
                elif path[1] == "level":
                    # Handle level search
                    return self._search_courses(
                        {
                            "search_type": "level",
                            "level_idx": selection,
                        }
                    )
            elif len(path) == 4:
                # Handle search results pagination
                if path[-1].startswith("prev_"):
                    page = int(path[-1].split("_")[1])
                    return self._format_search_results(self._last_search_results, page)
                elif path[-1].startswith("next_"):
                    page = int(path[-1].split("_")[1])
                    return self._format_search_results(self._last_search_results, page)
                # Handle case where selection is a course code
                if path[1] == "code":
                    return self._get_course_info(selection)
                elif path[1] == "title":
                    return self._get_course_info(selection)
                elif path[1] == "department":
                    return self._get_course_info(selection)
                elif path[1] == "level":
                    return self._get_course_info(selection)
            else:
                # Has to be search results pagination >2 pages
                if path[-1].startswith("prev_"):
                    page = int(path[-1].split("_")[1])
                    return self._format_search_results(self._last_search_results, page)
                elif path[-1].startswith("next_"):
                    page = int(path[-1].split("_")[1])
                    return self._format_search_results(self._last_search_results, page)
                # Handle case where selection is a course code
                return self._get_course_info(selection)

        elif main_section == "recommendation":
            if len(path) == 1:
                # Start recommendation process
                return self._get_recommendation_question(0, {})
            elif len(path) == 2:
                question_id = 1
                previous_answers = {"college_group": selection}
                return self._get_recommendation_question(question_id, previous_answers)
            elif len(path) == 3:
                question_id = 2
                previous_answers = {"college_group": path[1], "department": selection}
                return self._get_recommendation_question(question_id, previous_answers)
            elif len(path) == 4:
                question_id = 3
                previous_answers = {
                    "college_group": path[1],
                    "department": path[2],
                    "course_level": selection,
                }
                return self._get_recommendation_question(question_id, previous_answers)
            elif len(path) == 5:
                question_id = 4
                previous_answers = {
                    "college_group": path[1],
                    "department": path[2],
                    "course_level": path[3],
                    "course_theme": selection,
                }
                return self._get_recommendation_question(question_id, previous_answers)
            elif len(path) == 6:
                question_id = 5
                previous_answers = {
                    "college_group": path[1],
                    "department": path[2],
                    "course_level": path[3],
                    "course_theme": path[4],
                    "credit_hours": selection,
                }
                return self._get_recommendation_question(question_id, previous_answers)
            elif len(path) == 7:
                question_id = 6
                previous_answers = {
                    "college_group": path[1],
                    "department": path[2],
                    "course_level": path[3],
                    "course_theme": path[4],
                    "credit_hours": path[5],
                    "time_commitment": selection,
                }
                return self._get_course_recommendations(previous_answers)
            else:
                # Handle pagination
                if path[-1].startswith("prev_"):
                    page = int(path[-1].split("_")[1])
                    return self._format_search_results(
                        self._last_recommendation_results, page
                    )
                elif path[-1].startswith("next_"):
                    page = int(path[-1].split("_")[1])
                    return self._format_search_results(
                        self._last_recommendation_results, page
                    )
                # Handle case where selection is a course code
                return self._get_course_info(selection)

        # Default response if no matching route is found
        return self._default_response()

    def _default_response(self):
        """Default response when no matching route is found"""
        return {
            "question": "Menu not available",
            "options": [],
            "content": "<p>Sorry, this menu option is not available.</p>",
            "breadcrumbs": [],
        }

    def _get_main_menu(self):
        """Return the main menu options in web-compatible format"""
        content = """
        <div>
            <p>Welcome to the UF Course Recommendation System</p>
            <p>This tool helps you find courses that match your interests and academic needs.</p>
        </div>
        """

        return {
            "question": "UF Course Recommendation System",
            "options": [
                {"label": "Find Course Information", "value": "find_course"},
                {"label": "Search Courses", "value": "search"},
                {"label": "Get Course Recommendations", "value": "recommendation"},
            ],
            "content": content,
            "breadcrumbs": [],
        }

    def _get_course_search_form(self):
        """Return form for finding a specific course by code"""
        return {
            "question": "Find Course by Code",
            "options": [],
            "content": "<p>Enter the course code (e.g., ENC1101) to find detailed information.</p>",
            "breadcrumbs": ["Find Course"],
            "hasCustomInput": True,
            "inputPlaceholder": "Enter course code (e.g., ENC1101)",
        }

    def _get_search_menu(self):
        """Return search options menu in web-compatible format"""
        return {
            "question": "Course Search",
            "options": [
                {"label": "Search by code", "value": "code"},
                {"label": "Search by title keyword", "value": "title"},
                {"label": "Search by department", "value": "department"},
                {"label": "Search by level", "value": "level"},
            ],
            "content": "<p>Select a search method to find courses.</p>",
            "breadcrumbs": ["Search"],
        }

    def _get_code_search_form(self):
        """Return form for searching by course code"""
        return {
            "question": "Search by Course Code",
            "options": [],
            "content": "<p>Enter a full or partial course code to search (e.g., 'ENC' will find all English Composition courses).</p>",
            "breadcrumbs": ["Search", "By Code"],
            "hasCustomInput": True,
            "inputPlaceholder": "Enter course code or prefix",
        }

    def _get_title_search_form(self):
        """Return form for searching by course title"""
        return {
            "question": "Search by Course Title",
            "options": [],
            "content": "<p>Enter a keyword to search in course titles.</p>",
            "breadcrumbs": ["Search", "By Title"],
            "hasCustomInput": True,
            "inputPlaceholder": "Enter keyword to search in titles",
        }

    def _get_department_selection(self):
        """Return list of departments to choose from"""
        # Get all unique departments
        dept_list = sorted(
            set(c.get("department", "") for c in self.courses if "department" in c)
        )
        options = [{"label": dept, "value": str(i)} for i, dept in enumerate(dept_list)]

        return {
            "question": "Select Department",
            "options": options,
            "content": "<p>Please select a department to view its courses.</p>",
            "breadcrumbs": ["Search", "By Department"],
        }

    def _get_level_selection(self):
        """Return list of course levels to choose from"""
        levels = [
            "1000-level",
            "2000-level",
            "3000-level",
            "4000-level",
            "5000-level",
            "6000-level",
            "7000-level",
        ]
        options = [{"label": level, "value": str(i)} for i, level in enumerate(levels)]

        return {
            "question": "Select Course Level",
            "options": options,
            "content": "<p>Please select a course level.</p>",
            "breadcrumbs": ["Search", "By Level"],
        }

    def _get_course_info(self, course_code):
        """
        Get detailed information for a specific course

        Args:
            course_code: Course code to look up

        Returns:
            Dict with course details formatted for frontend
        """
        course = next(
            (c for c in self.courses if c["code"].lower() == course_code.lower()), None
        )

        if course:
            # Format themes properly
            themes = course.get("themes", ["N/A"])
            if not isinstance(themes, list):
                themes = [themes]
            themes_str = ", ".join(themes)

            # Create HTML content for course details
            content = f"""
                <div>
                    <h3 class="text-xl font-semibold mb-3">{course['code']} - {course['title']}</h3>
                    <p class="mb-1"><strong class="font-medium">Department:</strong> {course.get('department', 'N/A')}</p>
                    <p class="mb-1"><strong class="font-medium">College:</strong> {course.get('college', 'N/A')}</p>
                    <p class="mb-1"><strong class="font-medium">Credits:</strong> {course.get('credits', 'N/A')}</p>
                    <p class="mb-1"><strong class="font-medium">Level:</strong> {course.get('level', 'N/A')}</p>
                    <p class="mt-2 mb-1"><strong class="font-medium">Description:</strong></p>
                    <p class="text-sm text-gray-700 mb-1">{course.get('description', 'No description available')}</p>
                    <p class="mt-2 mb-1"><strong class="font-medium">Prerequisites:</strong></p>
                    <p class="text-sm text-gray-700 mb-1">{course.get('prerequisites', 'None')}</p>
                    <p class="mt-2 mb-1"><strong class="font-medium">Themes:</strong> {themes_str}</p>
                </div>
            """

            return {
                "question": f"Course Details: {course['code']}",
                "options": [],
                "content": content,
                "breadcrumbs": ["Course Details"],
            }
        else:
            return {
                "question": "Course Not Found - " + course_code,
                "options": [],
                "content": "<p>Course not found. Please check the course code.</p>",
                "breadcrumbs": ["Course Details"],
            }

    def _search_courses(self, selection):
        """
        Search for courses with various criteria

        Args:
            selection: Dict or string with search parameters

        Returns:
            Dict with search results formatted for frontend
        """
        results = []

        # Handle different selection formats
        if isinstance(selection, dict):
            search_type = selection.get("search_type", "")
            search_term = selection.get("search_term", "")
            dept_idx = selection.get("dept_idx")
            level_idx = selection.get("level_idx")
        elif isinstance(selection, str):
            # For custom input from forms
            search_type = "code"  # Default to code search
            search_term = selection
            dept_idx = None
            level_idx = None
        else:
            return self._default_response()

        # Execute search based on type
        if search_type == "code":
            results = [
                c for c in self.courses if search_term.upper() in c["code"].upper()
            ]
        elif search_type == "title":
            results = [
                c for c in self.courses if search_term.lower() in c["title"].lower()
            ]
        elif search_type == "department":
            if dept_idx is not None:
                # Get all unique departments
                dept_list = sorted(
                    set(
                        c.get("department", "")
                        for c in self.courses
                        if "department" in c
                    )
                )
                try:
                    dept_idx = int(dept_idx)
                    if 0 <= dept_idx < len(dept_list):
                        selected_dept = dept_list[dept_idx]
                        results = [
                            c
                            for c in self.courses
                            if c.get("department") == selected_dept
                        ]
                    else:
                        return {
                            "question": "Invalid Selection",
                            "options": [],
                            "content": "<p>Invalid department selection.</p>",
                            "breadcrumbs": ["Search", "Results"],
                        }
                except (ValueError, TypeError):
                    return self._get_department_selection()
            else:
                return self._get_department_selection()
        elif search_type == "level":
            if level_idx is not None:
                levels = [
                    "1000-level",
                    "2000-level",
                    "3000-level",
                    "4000-level",
                    "5000-level",
                    "6000-level",
                    "7000-level",
                ]
                try:
                    level_idx = int(level_idx)
                    if 0 <= level_idx < len(levels):
                        selected_level = levels[level_idx]
                        results = [
                            c for c in self.courses if c.get("level") == selected_level
                        ]
                    else:
                        return {
                            "question": "Invalid Selection",
                            "options": [],
                            "content": "<p>Invalid level selection.</p>",
                            "breadcrumbs": ["Search", "Results"],
                        }
                except (ValueError, TypeError):
                    return self._get_level_selection()
            else:
                return self._get_level_selection()

        # Store results for pagination
        self._last_search_results = results

        # Format and return the search results
        return self._format_search_results(results, 1)

    def _format_search_results(self, results, page=1):
        """
        Format search results with pagination for the frontend

        Args:
            results: List of course results
            page: Current page number

        Returns:
            Dict with paginated results for frontend
        """
        if not results:
            return {
                "question": "No Courses Found",
                "options": [],
                "content": "<p>No courses found matching your search criteria.</p>",
                "breadcrumbs": ["Search", "Results"],
            }

        page_size = 10
        total_pages = (len(results) + page_size - 1) // page_size

        # Make sure page is within bounds
        page = max(1, min(page, total_pages))

        start_idx = (page - 1) * page_size
        end_idx = min(start_idx + page_size, len(results))

        page_results = results[start_idx:end_idx]

        # Create HTML content for search results
        content = f"""
        <div class="p-4 rounded-lg shadow-sm">
            <p class="text-sm mb-4">Showing results {start_idx+1}-{end_idx} of {len(results)} courses (Page {page}/{total_pages})</p>
            <table class="w-full text-left border-collapse">
            <thead>
            <tr>
            <th class="p-2 text-xs font-semibold uppercase border-b">Code</th>
            <th class="p-2 text-xs font-semibold uppercase border-b">Title</th>
            <th class="p-2 text-xs font-semibold uppercase border-b">Level</th>
            </tr>
            </thead>
            <tbody>
        """

        for course in page_results:
            content += f"""
                <tr>
                    <td>{course["code"]}</td>
                    <td>{course["title"]}</td>
                    <td>{course.get("level", "N/A")}</td>
                </tr>
            """

        content += """
                </tbody>
            </table>
        </div>
        """

        # Create options for pagination and course selection
        options = []

        # Course selection options
        for course in page_results:
            options.append(
                {"label": f"View {course['code']}", "value": f"{course['code']}"}
            )

        # Pagination options
        if page > 1:
            options.append({"label": "« Previous Page", "value": f"prev_{page-1}"})

        if page < total_pages:
            options.append({"label": "Next Page »", "value": f"next_{page+1}"})

        return {
            "question": "Search Results",
            "options": options,
            "content": content,
            "breadcrumbs": ["Search", "Results"],
            "pagination": {
                "current_page": page,
                "total_pages": total_pages,
                "total_results": len(results),
            },
        }

    def _get_recommendation_question(self, question_id, previous_answers=None):
        """
        Get recommendation question for the questionnaire

        Args:
            question_id: Index of the current question
            previous_answers: Dict with answers to previous questions

        Returns:
            Dict with question and options for frontend
        """
        if previous_answers is None:
            previous_answers = {}

        # If we've answered all questions, show results
        if question_id >= len(self.matcher_questions):
            return self._get_course_recommendations(previous_answers)

        # Get current question
        question_data = self.matcher_questions[question_id]
        q_id = question_data["id"]
        question = question_data["question"]
        options = question_data["options"]

        # Create options for frontend
        option_list = [{"label": opt, "value": opt} for opt in options]

        return {
            "question": question,
            "options": option_list,
            "content": "<p>Please select one option to help us find courses that match your preferences.</p>",
            "breadcrumbs": ["Recommendations", f"Question {question_id+1}"],
            "metadata": {
                "question_id": question_id,
                "question_key": q_id,
                "total_questions": len(self.matcher_questions),
            },
        }

    def _get_course_recommendations(self, answers):
        """
        Get course recommendations based on user preferences

        Args:
            answers: Dict with user answers to recommendation questions

        Returns:
            Dict with recommended courses for frontend
        """
        # Filter out navigation responses (e.g., 'prev_1')
        filtered_answers = {}
        if isinstance(answers, dict):
            for q_id, answer in answers.items():
                if not (
                    isinstance(answer, str)
                    and (answer.startswith("prev_") or answer.startswith("next_"))
                ):
                    filtered_answers[q_id] = answer
        else:
            # Handle case where answers is not a dict
            return self._get_recommendation_question(0, {})

        # Recommendation logic - improved matching
        matched_courses = []
        matched_courses_secondary = []  # less strict matching
        matched_courses_tertiary = []  # even less strict matching

        for course in self.courses:
            # Check college group match
            college_match = filtered_answers.get(
                "college_group"
            ) == "Any College" or course.get(
                "college", ""
            ) in self.category_mapping.get(
                filtered_answers.get("college_group", ""), []
            )

            # Check department match
            department_match = filtered_answers.get(
                "department"
            ) == "Any Department" or course.get(
                "department", ""
            ) in self.department_mapping.get(
                filtered_answers.get("department", ""), []
            )

            # Check course level match
            level_match = course.get("level", "") in self.level_mapping.get(
                filtered_answers.get("course_level", ""), []
            )

            # Check course theme match
            theme_match = False
            course_themes = course.get("themes", [])
            # Ensure course_themes is a list
            if not isinstance(course_themes, list):
                course_themes = [course_themes] if course_themes else []

            # Flatten mapped themes for the selected theme
            mapped_themes = self.theme_mapping.get(
                filtered_answers.get("course_theme", ""), []
            )

            # More flexible theme matching
            for course_theme in course_themes:
                for mapped_theme in mapped_themes:
                    if mapped_theme.lower() in course_theme.lower():
                        theme_match = True
                        break
                if theme_match:
                    break

            # Check credit hours match
            credit_match = filtered_answers.get(
                "credit_hours"
            ) == "Any Credit Hours" or str(course.get("credits", "")).split("-")[
                0
            ] in self.credit_mapping.get(
                filtered_answers.get("credit_hours", ""), []
            )

            # Time commitment logic
            time_match = True
            if filtered_answers.get("time_commitment") != "Any Commitment":
                credits = course.get("credits", "3")
                try:
                    # Convert to integer, using first number if it's a range
                    credit_val = int(str(credits).split("-")[0])

                    if (
                        filtered_answers.get("time_commitment")
                        == "Light (Less intensive)"
                        and credit_val > 2
                    ):
                        time_match = False
                    elif (
                        filtered_answers.get("time_commitment")
                        == "Intensive (More challenging)"
                        and credit_val < 3
                    ):
                        time_match = False
                except ValueError:
                    # If we can't convert to int, assume it matches
                    pass

            # If all matches are true, add to recommended courses
            if (
                college_match
                and department_match
                and level_match
                and theme_match
                and credit_match
                and time_match
            ):
                matched_courses.append(course)
            elif (
                department_match
                and level_match
                and theme_match
                and credit_match
                and time_match
            ):
                matched_courses_secondary.append(course)  # less strict matching
            elif college_match and department_match and credit_match:
                matched_courses_tertiary.append(course)  # even less strict matching

        # Combine all matched courses
        if not matched_courses:
            print("No strict matches found. Trying secondary and tertiary matches.")
            matched_courses = matched_courses_secondary + matched_courses_tertiary

        # Store results for pagination
        self._last_recommendation_results = matched_courses

        # Format and return the recommendation results
        if not matched_courses:
            return {
                "question": "No Matching Courses",
                "options": [
                    {"label": "Try Different Preferences", "value": "recommendation"}
                ],
                "content": "<p>No matching courses found. Try adjusting your preferences.</p>",
                "breadcrumbs": ["Recommendations", "Results"],
            }

        # Create summary of user selections
        content = "<div class='recommendation-summary'><h3>Your Preferences</h3><ul>"
        for q in self.matcher_questions:
            q_id = q["id"]
            if q_id in filtered_answers:
                content += f"<li><strong>{q['question']}</strong>: {filtered_answers[q_id]}</li>"
        content += "</ul></div>"

        # Add the matched courses summary
        content += f"""
        <div>
            <h3>Recommended Courses ({len(matched_courses)})</h3>
            <p>Based on your preferences, we recommend the following courses:</p>
        </div>
        """

        # Format the results like the search results
        result = self._format_search_results(matched_courses)
        result["content"] = content + result["content"]
        return result
