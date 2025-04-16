import json
import os


class TuitionSystem:
    def __init__(self, json_file=None, tuition_data=None):
        """Initialize with either a JSON file or direct data"""
        if json_file and os.path.exists(json_file):
            with open(json_file, "r") as f:
                self.data = json.load(f)
        elif tuition_data:
            # Load data directly from provided dictionary
            self.data = tuition_data
        else:
            self.data = {"name": "Tuition Calculator", "description": "", "root": {}}

    def handle_menu_request(self, category, path, selection):
        """Process a menu request based on category, path, and selection"""
        if category != "tuition":
            return self._default_response()

        # Root menu (no path)
        if not path:
            return self._get_main_menu()

        # Get the first path element to determine which submenu to show
        main_section = path[0]

        if main_section == "calculate":
            # Handle the calculation path
            if len(path) == 1:
                # Start the calculation from the root
                return self._get_question_node(self.data["root"])
            elif len(path) > 1:
                # Navigate through the decision tree
                return self._handle_navigation(path[1:], selection)
        elif main_section == "about":
            # Display the about information
            return self._get_about_info()
        elif main_section == "results":
            # Display results if we have them
            if len(path) > 1:
                return self._get_results(path[1])

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
        """Return the main menu options"""
        content = f"""
        <div>
            <p>{self.data["description"]}</p>
            <p>This tool helps you estimate university costs based on your status and academic year.</p>
        </div>
        """

        return {
            "question": self.data["name"],
            "options": [
                {"label": "Calculate Tuition Costs", "value": "calculate"},
                {"label": "About This Calculator", "value": "about"},
            ],
            "content": content,
            "breadcrumbs": [],
        }

    def _get_about_info(self):
        """Return information about the calculator"""
        content = """
        <div>
            <p>The University Tuition Cost Calculator provides estimated costs
            for attending the university based on your residency status and
            the academic year you plan to attend.</p>
            
            <p>These estimates include:</p>
            <ul>
                <li>Tuition and mandatory fees</li>
                <li>Books and supplies</li>
                <li>Transportation expenses</li>
                <li>Living expenses (housing and food)</li>
                <li>Miscellaneous personal expenses</li>
                <li>Any required fees like loan fees or insurance</li>
            </ul>
            
            <p>Please note that these are ESTIMATES and actual costs may vary
            based on your specific course load, housing choices, and personal
            spending habits.</p>
        </div>
        """

        return {
            "question": "About This Calculator",
            "options": [],
            "content": content,
            "breadcrumbs": ["About"],
        }

    def _get_question_node(self, node, path_so_far=None):
        """Return a question node from the decision tree"""
        if path_so_far is None:
            path_so_far = []

        if "result" in node:
            # This is a result node, return the results
            return self._format_results(node["result"], path_so_far)

        # This is a question node
        question = node.get("question", "Make a selection")
        options = []

        for i, option in enumerate(node["options"]):
            options.append(
                {"label": option["label"], "value": str(i)}  # Use index as the value
            )

        return {
            "question": question,
            "options": options,
            "breadcrumbs": ["Calculate Tuition"] + path_so_far,
        }

    def _handle_navigation(self, path, selection):
        """Handle navigation through the decision tree"""
        # Start at the root node
        current_node = self.data["root"]

        # Track the navigation path and build breadcrumbs
        navigation_path = []

        # Follow the path to the current node
        for idx, choice in enumerate(path):
            try:
                choice_idx = int(choice)
                option = current_node["options"][choice_idx]
                navigation_path.append(option["label"])

                if "next" in option:
                    current_node = option["next"]
                elif "result" in option:
                    # Return the results
                    return self._format_results(option["result"], navigation_path)
                else:
                    # End of path without a result
                    return self._default_response()
            except (ValueError, IndexError):
                return self._default_response()

        # If selection is provided, add it to the path
        if selection is not None:
            try:
                selection_idx = int(selection)
                option = current_node["options"][selection_idx]

                if "next" in option:
                    return self._get_question_node(
                        option["next"], navigation_path + [option["label"]]
                    )
                elif "result" in option:
                    return self._format_results(
                        option["result"], navigation_path + [option["label"]]
                    )
            except (ValueError, IndexError):
                pass

        # Return the current node
        return self._get_question_node(current_node, navigation_path)

    def _format_results(self, result, path_so_far):
        """Format the tuition calculation results"""
        # Create a table of costs
        content = """
        <div class="tuition-results">
            <h3>Tuition Cost Breakdown</h3>
            
            <table class="cost-table">
                <thead>
                    <tr>
                        <th style="text-align:left">Item</th>
                        <th style="text-align:right">Amount</th>
                    </tr>
                </thead>
                <tbody>
        """

        # Add each cost item
        for item in result["breakdown"]:
            item_type = item["type"]
            amount = item["amount"]
            content += f'<tr><td>{item_type}</td><td style="text-align:right">${amount:,.2f}</td></tr>'

        # Add the total
        content += f"""
                </tbody>
                <tfoot>
                    <tr>
                        <th style="text-align:left">Total Cost</th>
                        <th style="text-align:right">${result['total']:,.2f}</th>
                    </tr>
                </tfoot>
            </table>
            
            <div class="notes">
                <h4>Notes:</h4>
                <ul>
                    <li>Tuition amounts are for the full academic year (Fall and Spring semesters)</li>
                    <li>Living expenses are based on on-campus housing and meal plan estimates</li>
                    <li>All amounts are subject to change without notice</li>
                </ul>
            </div>
        </div>
        """

        return {
            "question": "Tuition Cost Breakdown",
            "options": [],
            "content": content,
            "breadcrumbs": ["Calculate Tuition"] + path_so_far,
        }
