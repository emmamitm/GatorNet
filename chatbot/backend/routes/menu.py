from flask import Blueprint, request, jsonify
import os
import importlib

# Create blueprint
menu_routes = Blueprint("menu", __name__)

# Map of category names to module and class names
module_mapping = {
    "events": {
        "module": "modules.events",
        "class": "EventsSystem",
        "file": "events.json",
    },
    "libraries": {
        "module": "modules.libraries",
        "class": "LibrariesSystem",
        "file": "libraries.json",
    },
    "courses": {
        "module": "modules.courses",
        "class": "CoursesSystem",
        "file": "courses.json",
    },
    "clubs": {"module": "modules.clubs", "class": "ClubsSystem", "file": "clubs.json"},
    "housing": {
        "module": "modules.housing",
        "class": "HousingSystem",
        "file": "housing.json",
    },
    "tuition": {
        "module": "modules.tuition",
        "class": "TuitionSystem",
        "file": "tuition.json",
    },
}

# Initialize systems dictionary
systems = {}


def initialize_systems():
    """Initialize all module systems"""
    for category, info in module_mapping.items():
        try:
            # Import the module
            module_name = info["module"]
            class_name = info["class"]
            json_file = f"./jsonFiles/{info['file']}"

            # Dynamic import
            module = importlib.import_module(module_name)

            # Get the class from the module
            system_class = getattr(module, class_name)

            # Initialize the system
            if os.path.exists(json_file):
                systems[category] = system_class(json_file=json_file)
            else:
                # Initialize with empty data if file doesn't exist
                print(
                    f"Warning: {json_file} not found. Initializing {category} with empty data."
                )
                systems[category] = system_class(events_data={"events": []})

            print(f"Successfully loaded {category} system")

        except Exception as e:
            print(f"Error loading {category} system: {e}")
            systems[category] = None


@menu_routes.route("/api/menu", methods=["POST"])
def get_menu():
    """Handle menu navigation requests"""
    data = request.get_json()

    # Extract data from request
    category = data.get("category", "")
    path = data.get("path", [])
    selection = data.get("selection", None)

    # Lazy initialization of systems if needed
    if not systems:
        initialize_systems()

    # Check if system exists for this category
    if category not in systems or systems[category] is None:
        return jsonify(
            {
                "question": "System Unavailable",
                "options": [],
                "content": f"<p>The {category} system is currently unavailable.</p>",
                "breadcrumbs": [],
            }
        )

    # Use the appropriate system to handle the menu request
    system = systems[category]
    menu_data = system.handle_menu_request(category, path, selection)

    return jsonify(menu_data)
