import json
import os
import sys


class CourseSystem:
    def __init__(self, json_file):
        with open(json_file, "r") as f:
            self.data = json.load(f)
        self.matcher_questions = self.data["matcher_questions"]
        self.courses = self.data.get("courses", [])

        # Updated mapping dictionaries to help with recommendations
        self.category_mapping = {
            "Arts & Sciences": ["Arts & Sciences", "Languages & International Studies"],
            "Engineering": ["Engineering"],
            "Business": ["Business"],
            "Health & Medicine": ["Health & Medicine", "Agriculture & Life Sciences"],
            "Fine Arts": ["Fine Arts", "Journalism & Communications"],
            "Technology & Computing": [
                "Engineering",
                "Computer and Information Science & Engineering",
                "Information Systems",
            ],
        }

        self.department_mapping = {
            "Computer Science": ["Computer and Information Science & Engineering"],
            "Management": ["Management"],
            "Marketing": ["Marketing"],
            "Biology": ["Biology", "Microbiology & Cell Science"],
            "Chemistry": ["Chemistry"],
            "Psychology": ["Psychology", "Clinical and Health Psychology"],
            "Physics": ["Physics"],
            "Mathematics": ["Mathematics", "Statistics"],
            "Engineering Disciplines": [
                "Agricultural and Biological Engineering",
                "Biomedical Engineering",
                "Chemical Engineering",
                "Civil and Coastal Engineering",
                "Electrical and Computer Engineering",
            ],
        }

        self.level_mapping = {
            "Introductory (1000-2000 levels)": ["1000-level", "2000-level"],
            "Intermediate (3000-4000 levels)": ["3000-level", "4000-level"],
            "Advanced/Graduate (5000+ levels)": [
                "5000-level",
                "6000-level",
                "7000-level",
            ],
        }

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
            "5+ Credits": ["5"],
        }

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
            print(f"Themes: {', '.join(course.get('themes', ['N/A']))}")
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

        # Recommendation logic
        matched_courses = []
        for course in self.courses:
            # Check college group match
            college_match = answers.get("college_group") == "Any College" or any(
                coll in self.category_mapping.get(answers["college_group"], [])
                for coll in [course.get("college", "")]
            )

            # Check department match
            department_match = answers.get("department") == "Any Department" or any(
                dept in self.department_mapping.get(answers["department"], [])
                for dept in [course.get("department", "")]
            )

            # Check course level match
            level_match = any(
                lvl in self.level_mapping.get(answers["course_level"], [])
                for lvl in [course.get("level", "")]
            )

            # Check course theme match
            theme_match = False
            course_themes = course.get("themes", [])
            # Ensure course_themes is a list
            if not isinstance(course_themes, list):
                course_themes = [course_themes] if course_themes else []

            # Flatten mapped themes for the selected theme
            mapped_themes = self.theme_mapping.get(answers["course_theme"], [])

            # Check if any of the course's themes match the mapped themes
            theme_match = any(
                any(
                    mapped_theme.lower() in str(course_theme).lower()
                    for mapped_theme in mapped_themes
                )
                for course_theme in course_themes
            )

            # Check credit hours match
            credit_match = answers.get("credit_hours") == "Any Credit Hours" or any(
                credits in self.credit_mapping.get(answers["credit_hours"], [])
                for credits in [str(course.get("credits", ""))]
            )

            # Time commitment is harder to match precisely
            # We'll use it as a very loose filter for now
            time_match = answers.get("time_commitment") == "Any Commitment"

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
            print("\nRecommended Courses:")
            # Limit to first 10 courses
            for course in matched_courses[:10]:
                print(f"{course['code']} - {course['title']} ({course['level']})")
                print(f"  Department: {course['department']}")
                print(f"  Credits: {course.get('credits', 'N/A')}")
                print(f"  Themes: {', '.join(course.get('themes', ['N/A']))}\n")

            # Indicate if more courses exist
            if len(matched_courses) > 10:
                print(f"... and {len(matched_courses) - 10} more courses")
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
            options = ["Find Course Information", "Get Course Recommendations"]
            selected = self.get_selection(options, "Main Menu", allow_exit=True)

            if selected == "Find Course Information":
                course_code = input("\nEnter course code (e.g., MAR2290): ")
                self.display_course_info(course_code)
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
