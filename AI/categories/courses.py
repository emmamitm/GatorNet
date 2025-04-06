import json
import os
import sys


class CourseSystem:
    def __init__(self, json_file):
        with open(json_file, "r") as f:
            self.data = json.load(f)
        self.matcher_questions = self.data["matcher_questions"]
        self.courses = self.data.get("courses", [])
        self.college_groups = self.data.get("college_groups", [])

        # Updated mapping dictionaries to help with recommendations
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
                simplified_dept = dept.split(" | ")[0]  # Handle cases like "Biology | Botany | Zoology"
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

    def search_courses(self):
        """Search for courses with flexible search options"""
        print("\n===== Course Search =====")
        print("1. Search by code")
        print("2. Search by title keyword")
        print("3. Search by department")
        print("4. Search by level")
        print("0. Back to main menu")
        
        choice = input("\nEnter your choice: ").strip()
        
        if choice == "0":
            return
        elif choice == "1":
            search_term = input("Enter course code (e.g., MAR2290): ").strip().upper()
            results = [c for c in self.courses if search_term in c["code"].upper()]
        elif choice == "2":
            search_term = input("Enter title keyword: ").strip().lower()
            results = [c for c in self.courses if search_term.lower() in c["title"].lower()]
        elif choice == "3":
            # Show list of departments for selection
            dept_list = set()
            for course in self.courses:
                if "department" in course:
                    dept_list.add(course["department"])
            
            departments = sorted(list(dept_list))
            for i, dept in enumerate(departments, 1):
                print(f"{i}. {dept}")
            
            try:
                dept_idx = int(input("Enter department number: ").strip()) - 1
                if 0 <= dept_idx < len(departments):
                    search_term = departments[dept_idx]
                    results = [c for c in self.courses if c.get("department") == search_term]
                else:
                    print("Invalid selection.")
                    return
            except ValueError:
                print("Invalid input.")
                return
        elif choice == "4":
            levels = ["1000-level", "2000-level", "3000-level", "4000-level", "5000-level", "6000-level", "7000-level"]
            for i, level in enumerate(levels, 1):
                print(f"{i}. {level}")
            
            try:
                level_idx = int(input("Enter level number: ").strip()) - 1
                if 0 <= level_idx < len(levels):
                    search_term = levels[level_idx]
                    results = [c for c in self.courses if c.get("level") == search_term]
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

    def display_search_results(self, results):
        """Display search results with pagination"""
        if not results:
            print("No courses found matching your search criteria.")
            return
            
        page_size = 10
        total_pages = (len(results) + page_size - 1) // page_size
        current_page = 1
        
        while True:
            start_idx = (current_page - 1) * page_size
            end_idx = min(start_idx + page_size, len(results))
            
            print(f"\nShowing results {start_idx+1}-{end_idx} of {len(results)} courses (Page {current_page}/{total_pages})")
            
            for i, course in enumerate(results[start_idx:end_idx], start_idx+1):
                print(f"{i}. {course['code']} - {course['title']} ({course.get('level', 'N/A')})")
            
            print("\nOptions:")
            print("N: Next page")
            print("P: Previous page")
            print("V #: View details for course number #")
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
                    course_num = int(choice[2:]) - 1
                    if 0 <= course_num < len(results):
                        self.display_course_info(results[course_num]["code"])
                    else:
                        print("Invalid course number.")
                except ValueError:
                    print("Invalid input. Please enter a valid course number.")
            else:
                print("Invalid choice. Please try again.")

    def display_course_info(self, course_code):
        """Display detailed information for a specific course."""
        course = next(
            (c for c in self.courses if c["code"].lower() == course_code.lower()), None
        )
        if course:
            print(f"\nCourse: {course['code']} - {course['title']}")
            print(f"Department: {course.get('department', 'N/A')}")
            print(f"College: {course.get('college', 'N/A')}")
            print(f"Credits: {course.get('credits', 'N/A')}")
            print(f"Level: {course.get('level', 'N/A')}")
            print(
                f"Description: {course.get('description', 'No description available')}"
            )
            print(f"Prerequisites: {course.get('prerequisites', 'None')}")
            
            # Handle themes that might be a string or a list
            themes = course.get('themes', ['N/A'])
            if not isinstance(themes, list):
                themes = [themes]
            print(f"Themes: {', '.join(themes)}")
            
            input("\nPress Enter to continue...")
        else:
            print("Course not found. Please check the course code.")

    def course_recommendation(self):
        """Provide course recommendations based on user preferences."""
        answers = {}
        for question_data in self.matcher_questions:
            q_id = question_data["id"]
            question = question_data["question"]
            options = question_data["options"]

            selected = self.get_selection(options, question)
            if not selected:
                return
            answers[q_id] = selected

        # Recommendation logic - improved matching
        matched_courses = []
        for course in self.courses:
            # Check college group match
            college_match = answers.get("college_group") == "Any College" or course.get("college", "") in self.category_mapping.get(answers["college_group"], [])

            # Check department match
            department_match = answers.get("department") == "Any Department" or course.get("department", "") in self.department_mapping.get(answers["department"], [])

            # Check course level match
            level_match = course.get("level", "") in self.level_mapping.get(answers["course_level"], [])

            # Check course theme match
            theme_match = False
            course_themes = course.get("themes", [])
            # Ensure course_themes is a list
            if not isinstance(course_themes, list):
                course_themes = [course_themes] if course_themes else []
            
            # Flatten mapped themes for the selected theme
            mapped_themes = self.theme_mapping.get(answers["course_theme"], [])
            
            # More flexible theme matching
            for course_theme in course_themes:
                for mapped_theme in mapped_themes:
                    if mapped_theme.lower() in course_theme.lower():
                        theme_match = True
                        break
                if theme_match:
                    break

            # Check credit hours match
            credit_match = answers.get("credit_hours") == "Any Credit Hours" or str(course.get("credits", "")).split("-")[0] in self.credit_mapping.get(answers["credit_hours"], [])

            # Time commitment logic (could be improved with actual data)
            time_match = True
            if answers.get("time_commitment") != "Any Commitment":
                credits = course.get("credits", "3")
                try:
                    # Convert to integer, using first number if it's a range
                    credit_val = int(str(credits).split("-")[0])
                    
                    if answers["time_commitment"] == "Light (Less intensive)" and credit_val > 2:
                        time_match = False
                    elif answers["time_commitment"] == "Intensive (More challenging)" and credit_val < 3:
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

        if matched_courses:
            self.display_search_results(matched_courses)
        else:
            print("\nNo matching courses found. Try adjusting your preferences.")

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
            print("\n===== UF Course Recommendation System =====")
            options = ["Find Course Information", "Search Courses", "Get Course Recommendations"]
            selected = self.get_selection(options, "Main Menu", allow_exit=True)

            if selected == "Find Course Information":
                course_code = input("\nEnter course code (e.g., MAR2290): ")
                self.display_course_info(course_code)
            elif selected == "Search Courses":
                self.search_courses()
            elif selected == "Get Course Recommendations":
                self.course_recommendation()

    def exit_program(self):
        """Exit the program."""
        print("\nThank you for using the UF Course Recommendation System!")
        sys.exit(0)


if __name__ == "__main__":
    json_file = "./jsonFiles/courses.json"
    system = CourseSystem(json_file)
    system.main_menu()