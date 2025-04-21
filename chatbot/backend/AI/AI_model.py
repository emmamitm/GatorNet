#!/usr/bin/env python3
# NEW
"""
Enhanced UF Assistant
A powerful assistant for answering questions about University of Florida
using LLaMA 3 with embedded knowledge and advanced retrieval techniques.
"""
import csv
import functools
import torch
import difflib
from loguru import logger
import hydra
from omegaconf import DictConfig
from sentence_transformers import SentenceTransformer
import os
import re
import json
import time
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path
from collections import defaultdict

# ------------------------------
# Setup Logging (using loguru)
# ------------------------------
logger.remove()  # Remove the default logger
logger.add("enhanced_uf_assistant.log", level="INFO")
logger.info("Enhanced UF Assistant starting up...")

# Define the path to the home directory - using the correct structure
HOME_DIR = os.path.abspath(os.path.dirname(__file__))

# ------------------------------
# Academic Calendar Data
# ------------------------------

# Add this at the beginning of AI_model.py in chatbot/backend/AI/
import os
import sys

# Handle the HOME_DIR properly to find data files
current_dir = os.path.abspath(os.path.dirname(__file__))

# Check for environment variable first
if "AI_DATA_DIR" in os.environ:
    HOME_DIR = os.environ["AI_DATA_DIR"]
    print(f"Using HOME_DIR from environment variable: {HOME_DIR}")
else:
    # Try to determine the HOME_DIR by finding scrapedData
    # Check parent directories
    test_dir = current_dir
    for _ in range(5):  # Try up to 5 levels up
        if os.path.exists(os.path.join(test_dir, "scrapedData")):
            HOME_DIR = test_dir
            print(f"Found scrapedData in {test_dir}, setting HOME_DIR")
            break
        parent = os.path.dirname(test_dir)
        if parent == test_dir:  # Reached root
            break
        test_dir = parent
    else:
        # Default to the current directory
        HOME_DIR = current_dir
        print(
            f"WARNING: Could not find scrapedData directory. Using {HOME_DIR} as HOME_DIR"
        )
        print(f"Current directory contains: {os.listdir(current_dir)}")


# Function to verify data directories
def verify_data_directories():
    required_dirs = [
        os.path.join(HOME_DIR, "scrapedData"),
        os.path.join(HOME_DIR, "scrapedData", "campusBuildings"),
        os.path.join(HOME_DIR, "scrapedData", "campusClubs"),
        os.path.join(HOME_DIR, "scrapedData", "libraries"),
        os.path.join(HOME_DIR, "scrapedData", "housing"),
        os.path.join(HOME_DIR, "scrapedData", "classes"),
    ]

    for directory in required_dirs:
        if os.path.exists(directory):
            print(f"✓ Found {directory}")
            # Check for some files
            try:
                files = os.listdir(directory)
                if files:
                    print(f"  ✓ Contains {len(files)} files/directories")
                else:
                    print(f"  ✗ Directory is empty")
            except Exception as e:
                print(f"  ✗ Error listing directory: {e}")
        else:
            print(f"✗ Missing {directory}")


# Call this on module load
verify_data_directories()

ACADEMIC_CALENDAR = {
    "terms": {
        "Spring 2025": {"start": "2025-01-06", "end": "2025-05-02"},
        "Summer A 2025": {"start": "2025-05-12", "end": "2025-06-20"},
        "Summer B 2025": {"start": "2025-06-30", "end": "2025-08-08"},
        "Fall 2025": {"start": "2025-08-25", "end": "2025-12-12"},
    },
    "events": {
        "Spring 2025 Final Exams": {"start": "2025-04-26", "end": "2025-05-02"},
        "Spring Break 2025": {"start": "2025-03-08", "end": "2025-03-15"},
        "Summer Break 2025": {"start": "2025-05-03", "end": "2025-05-11"},
        "Fall 2025 Final Exams": {"start": "2025-12-06", "end": "2025-12-12"},
    },
    "library_schedule_exceptions": {
        "2025-01-01": {"all": "CLOSED - New Year's Day"},
        "2025-01-20": {"all": "CLOSED - Martin Luther King Jr. Day"},
        "2025-03-08": {"all": "CLOSED - Spring Break Begins"},
        "2025-05-03": {"all": "CLOSED - Semester Break"},
        "2025-05-26": {"all": "CLOSED - Memorial Day"},
        "2025-07-04": {"all": "CLOSED - Independence Day"},
    },
    "extended_hours": {
        "Spring 2025 Finals": {
            "start": "2025-04-19",
            "end": "2025-05-02",
            "libraries": {
                "Library West": "24 hours",
                "Marston Science Library": "24 hours",
            },
        },
        "Fall 2025 Finals": {
            "start": "2025-11-29",
            "end": "2025-12-12",
            "libraries": {
                "Library West": "24 hours",
                "Marston Science Library": "24 hours",
            },
        },
    },
}

# ------------------------------
# Entity Aliases
# ------------------------------
LIBRARY_ALIASES = {
    "library west": ["lib west", "west library", "west", "libwest"],
    "marston science library": ["marston", "msl", "marston library", "science library"],
    "smathers library": ["smathers", "east", "library east", "east library"],
    "health science center library": [
        "health library",
        "hscl",
        "health science library",
    ],
    "architecture & fine arts library": [
        "afa",
        "architecture library",
        "fine arts library",
    ],
    "education library": ["norman hall library", "education", "norman library"],
    "legal information center": ["law library", "legal library", "law", "legal"],
}

BUILDING_ALIASES = {
    "reitz union": ["reitz", "student union", "j. wayne reitz", "the union"],
    "century tower": ["the tower", "bell tower", "carillon"],
    "ben hill griffin stadium": [
        "the swamp",
        "stadium",
        "football stadium",
        "ben hill",
    ],
    "turlington hall": ["turlington", "plaza of the americas"],
    "norman hall": ["norman", "college of education", "education building"],
    "dickinson hall": ["dickinson", "florida museum of natural history"],
    "matherly hall": ["matherly"],
    "tigert hall": ["tigert", "administration", "admin building"],
    "newell hall": ["newell"],
    "weil hall": ["weil", "engineering building"],
    "marston science library": ["marston", "msl"],
    "library west": ["lib west", "west library"],
}

DORM_ALIASES = {
    "broward hall": ["broward"],
    "jennings hall": ["jennings"],
    "rawlings hall": ["rawlings"],
    "simpson hall": ["simpson"],
    "cypress hall": ["cypress"],
    "hume hall": ["hume", "honors dorm", "honors residence"],
    "springs complex": ["springs", "springs residence"],
    "beaty towers": ["beaty", "towers"],
    "keys complex": ["keys", "keys residence"],
    "yulee hall": ["yulee"],
    "reid hall": ["reid"],
    "murphree hall": ["murphree"],
    "thomas hall": ["thomas"],
}


# ------------------------------
# Enhanced Major Search Functionality
# ------------------------------
def search_major_info(query, home_dir):
    """
    Search for information about an academic major/program
    with improved detection and formatting
    """
    # Normalize query
    query_lower = query.lower().strip()

    # Extract major name with improved patterns
    major_patterns = [
        r"major in\s+([a-zA-Z\s&]+)(?:\s|$|\.|\?)",
        r"studying\s+([a-zA-Z\s&]+)(?:\s|$|\.|\?)",
        r"about\s+([a-zA-Z\s&]+)\s+(?:major|program|degree)",
        r"([a-zA-Z\s&]+)\s+(?:major|program|degree)",
        r"information about\s+([a-zA-Z\s&]+)",
    ]

    extracted_major = None
    for pattern in major_patterns:
        match = re.search(pattern, query_lower)
        if match:
            extracted_major = match.group(1).strip()
            break

    # If no pattern matched, use the whole query
    if not extracted_major:
        # Remove common words that aren't part of a major name
        filter_words = [
            "what",
            "is",
            "the",
            "about",
            "tell",
            "me",
            "information",
            "program",
        ]
        query_words = query_lower.split()
        filtered_query = " ".join(
            [word for word in query_words if word not in filter_words]
        )
        extracted_major = filtered_query.strip()

    logger.info(f"Extracted major: {extracted_major}")

    # Define paths for both programs and majors CSVs
    programs_path = os.path.join(home_dir, "scrapedData", "classes", "programs.csv")
    majors_path = os.path.join(home_dir, "scrapedData", "classes", "majors.csv")

    # Load programs data with error handling
    programs = []
    departments = set()
    try:
        with open(programs_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Clean up field names if needed
                cleaned_row = {k.strip(): v.strip() for k, v in row.items() if k and v}
                programs.append(cleaned_row)
                if "Department" in cleaned_row:
                    departments.add(cleaned_row["Department"].lower())
    except Exception as e:
        logger.error(f"Error loading programs: {e}")
        programs = []

    # Load majors data for descriptions
    majors_descriptions = {}
    try:
        with open(majors_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if "Department" in row and "Description" in row:
                    dept = row["Department"].strip().lower()
                    desc = row["Description"].strip()
                    if dept and desc:
                        majors_descriptions[dept] = desc
    except Exception as e:
        logger.error(f"Error loading majors descriptions: {e}")

    # Search for matching programs - trying different matching approaches

    # 1. First try exact match on name
    matched_programs = []
    matched_department = None

    for program in programs:
        if "Name" in program and program["Name"].lower() == extracted_major:
            matched_programs.append(program)
            if "Department" in program:
                matched_department = program["Department"]

    # 2. Try partial match on name if no exact matches
    if not matched_programs:
        for program in programs:
            if "Name" in program and extracted_major in program["Name"].lower():
                matched_programs.append(program)
                if "Department" in program and not matched_department:
                    matched_department = program["Department"]

    # 3. Try match on department
    if not matched_programs:
        for program in programs:
            if (
                "Department" in program
                and program["Department"].lower() == extracted_major
            ):
                matched_programs.append(program)
                if not matched_department:
                    matched_department = program["Department"]

    # 4. Try fuzzy matching for department if still no matches
    if not matched_programs and departments:
        # Try to find close matches to departments
        close_matches = difflib.get_close_matches(
            extracted_major, list(departments), n=1, cutoff=0.7
        )
        if close_matches:
            matched_department = close_matches[0]
            # Get all programs in that department
            for program in programs:
                if (
                    "Department" in program
                    and program["Department"].lower() == matched_department
                ):
                    matched_programs.append(program)

    # Get major description
    description = "No detailed information available."
    if matched_department and matched_department.lower() in majors_descriptions:
        description = majors_descriptions[matched_department.lower()]

    # Format the response
    if matched_programs:
        # Get all types of programs (major, minor, certificate)
        program_types = []
        program_details = []

        for program in matched_programs:
            prog_type = program.get("Type", "")
            name = program.get("Name", "")
            url = program.get("URL", "")
            dept = program.get("Department", matched_department or "")

            if prog_type and prog_type not in program_types:
                program_types.append(prog_type)

            if name and prog_type:
                detail = f"• {name} ({prog_type})"
                if url:
                    detail += f" - [Catalog Link](https://catalog.ufl.edu{url})"
                program_details.append(detail)

        # Format the title - use department name or the first program name
        title = matched_department or matched_programs[0].get(
            "Name", extracted_major.title()
        )

        # Build a properly formatted response
        response = f"""
🎓 **{title}**

{description}

**Available as:** {', '.join(program_types)}

**Available Programs:**
{"".join(program_details)}

For more details, visit the [UF Catalog](https://catalog.ufl.edu).
"""
        return response, True

    # If no matches found, return a generic response
    else:
        response = f"""
🎓 **{extracted_major.title()}**

I don't have specific information about this program in my database. 

The University of Florida offers over 100 undergraduate majors across multiple colleges. Your program might be offered under a different name or as a specialization within another major.

For the most accurate and complete information, please visit the [UF Undergraduate Catalog](https://catalog.ufl.edu/UGRD/) or contact the UF Admissions Office.
"""
        return response, False


# ------------------------------
# Data Loading Functions
# ------------------------------
def load_campus_buildings_data():
    """Load campus buildings data from CSV file"""
    csv_path = os.path.join(HOME_DIR, "scrapedData/campusBuildings/uf_buildings.csv")
    buildings = []

    try:
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                buildings.append(
                    {
                        "Building Number": row.get("number", ""),
                        "Building Name": row.get("name", ""),
                        "Abbreviation": row.get("abbreviation", ""),
                        "Address": row.get("address", ""),
                        "Description": row.get("description", ""),
                    }
                )
        logger.info(
            f"[OK] Successfully loaded {len(buildings)} campus buildings from CSV"
        )
        return buildings
    except Exception as e:
        logger.error(f"Error loading campus buildings data: {e}")
        return []


def load_clubs_data():
    """Load clubs data from CSV file"""
    csv_path = os.path.join(HOME_DIR, "scrapedData/campusClubs/uf_organizations.csv")
    clubs = []

    try:
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                clubs.append(
                    {
                        "Club ID": row.get("ID", ""),
                        "Organization Name": row.get("Organization Name", ""),
                        "Description": row.get("Description", ""),
                    }
                )
        logger.info(f"[OK] Successfully loaded {len(clubs)} clubs from CSV")
        return clubs
    except Exception as e:
        logger.error(f"Error loading clubs data: {e}")
        return []


def load_events_data():
    """Load events data from CSV file"""
    csv_path = os.path.join(HOME_DIR, "scrapedData/campusEvents/uf_events_all.csv")
    events = []

    try:
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                events.append(
                    {
                        "Event Name": row.get("name", ""),
                        "Date": row.get("date", ""),
                        "Time": row.get("time", ""),
                        "Location": row.get("location", ""),
                        "Link": row.get("link", ""),
                        "Description": row.get("description", ""),
                    }
                )
        logger.info(f"[OK] Successfully loaded {len(events)} events from CSV")
        return events
    except Exception as e:
        logger.error(f"Error loading events data: {e}")
        return []


def load_courses_data():
    """Load courses data from CSV file"""
    csv_path = os.path.join(HOME_DIR, "scrapedData/classes/courses.csv")
    courses = []

    try:
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                courses.append(
                    {
                        "Department": row.get("department", ""),
                        "Course Code": row.get("code", ""),
                        "Course Title": row.get("title", ""),
                        "Credit Count": row.get("credits", ""),
                        "Description": row.get("description", ""),
                        "Prerequisites": row.get("prerequisites", ""),
                        "Grading Scheme": row.get("grading_scheme", ""),
                    }
                )
        logger.info(f"[OK] Successfully loaded {len(courses)} courses from CSV")
        return courses
    except Exception as e:
        logger.error(f"Error loading courses data: {e}")
        return []


def load_majors_data():
    """Load majors data from CSV file"""
    csv_path = os.path.join(HOME_DIR, "scrapedData/classes/majors.csv")
    majors = []

    try:
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                majors.append(
                    {
                        "Department": row.get("department", ""),
                        "Description": row.get("description", ""),
                    }
                )
        logger.info(f"[OK] Successfully loaded {len(majors)} majors from CSV")
        return majors
    except Exception as e:
        logger.error(f"Error loading majors data: {e}")
        return []


def load_programs_data():
    """Load programs data from CSV file"""
    csv_path = os.path.join(HOME_DIR, "scrapedData/classes/programs.csv")
    programs = []

    try:
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                programs.append(
                    {
                        "Department": row.get("Department", ""),
                        "Name": row.get("Name", ""),
                        "URL": row.get("URL", ""),
                        "Type": row.get("Type", ""),
                    }
                )
        logger.info(f"[OK] Successfully loaded {len(programs)} programs from CSV")
        return programs
    except Exception as e:
        logger.error(f"Error loading programs data: {e}")
        return []


def load_hallinfo_data():
    """Load hall info data from CSV file"""
    csv_path = os.path.join(HOME_DIR, "scrapedData/housing/hallInfo.csv")
    hallinfo = []

    try:
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Safely handle the splitting of string fields
                features = (
                    row.get("features_str", "").split(",")
                    if row.get("features_str")
                    else []
                )
                room_types = (
                    row.get("room_types_str", "").split(",")
                    if row.get("room_types_str")
                    else []
                )
                nearby_locations = (
                    row.get("nearby_locations_str", "").split(",")
                    if row.get("nearby_locations_str")
                    else []
                )

                hallinfo.append(
                    {
                        "Building Name": row.get("name", ""),
                        "Hall Type": row.get("hall_type", ""),
                        "Description": row.get("description", ""),
                        "Location": row.get("location", ""),
                        "Phone": row.get("phone", ""),
                        "Features": features,
                        "Room Types": room_types,
                        "Nearby Locations": nearby_locations,
                        "URL": row.get("url", ""),
                        "Image URL": row.get("image_url", ""),
                        "Rental Rate URL": row.get("rental_rate_url", ""),
                    }
                )
        logger.info(f"[OK] Successfully loaded {len(hallinfo)} hall info from CSV")
        return hallinfo
    except Exception as e:
        logger.error(f"Error loading hall info data: {e}")
        return []


def load_libraries_data():
    """Load libraries data from CSV file with enhanced parsing"""
    csv_path = os.path.join(HOME_DIR, "scrapedData/libraries/uf_libraries.csv")
    libraries = []

    try:
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # More robust hours parsing
                hours = {}
                if "Hours" in row and row["Hours"]:
                    try:
                        # Try to parse hours from format like "7am - 2am (Sun-Thu) 7am - 10pm (Fri) 10am - 10pm (Sat)"
                        hours_text = row["Hours"]

                        # Parse specific day patterns
                        day_patterns = [
                            (
                                r"([\d:]+\s*[ap]m\s*-\s*[\d:]+\s*[ap]m)\s*\((Sun-Thu|Mon-Thu|Mon-Fri)\)",
                                ["Monday", "Tuesday", "Wednesday", "Thursday"],
                            ),
                            (
                                r"([\d:]+\s*[ap]m\s*-\s*[\d:]+\s*[ap]m)\s*\((Fri)\)",
                                ["Friday"],
                            ),
                            (
                                r"([\d:]+\s*[ap]m\s*-\s*[\d:]+\s*[ap]m)\s*\((Sat)\)",
                                ["Saturday"],
                            ),
                            (
                                r"([\d:]+\s*[ap]m\s*-\s*[\d:]+\s*[ap]m)\s*\((Sun)\)",
                                ["Sunday"],
                            ),
                        ]

                        for pattern, days in day_patterns:
                            matches = re.findall(pattern, hours_text)
                            if matches:
                                for match in matches:
                                    hour_str = (
                                        match[0] if isinstance(match, tuple) else match
                                    )
                                    for day in days:
                                        hours[day] = hour_str.strip()

                        # Handle special cases
                        if "Sun-Thu" in hours_text and not hours.get("Sunday"):
                            if "Monday" in hours:
                                hours["Sunday"] = hours["Monday"]

                        # Fallback if specific patterns didn't work
                        if not hours:
                            days_of_week = [
                                "Monday",
                                "Tuesday",
                                "Wednesday",
                                "Thursday",
                                "Friday",
                                "Saturday",
                                "Sunday",
                            ]
                            default_hours = "8:00am - 5:00pm"
                            for day in days_of_week:
                                if day not in hours:
                                    hours[day] = default_hours
                    except Exception as e:
                        logger.warning(f"Error parsing library hours: {e}")
                        # Create default hours if parsing fails
                        days_of_week = [
                            "Monday",
                            "Tuesday",
                            "Wednesday",
                            "Thursday",
                            "Friday",
                            "Saturday",
                            "Sunday",
                        ]
                        default_hours = "8:00am - 5:00pm"
                        for day in days_of_week:
                            hours[day] = default_hours

                libraries.append(
                    {
                        "Library Name": row.get("Library Name", ""),
                        "Location": row.get("Location", ""),
                        "Capacity": row.get("Capacity", ""),
                        "Hours": hours,
                        "Special Notes": row.get("Special Notes", ""),
                        "URL": row.get("URL", ""),
                        "Phone": row.get("Phone", ""),
                        "Email": row.get("Email", ""),
                    }
                )
        logger.info(f"[OK] Successfully loaded {len(libraries)} libraries from CSV")
        return libraries
    except Exception as e:
        logger.error(f"Error loading libraries data: {e}")
        return []


# ------------------------------
# Caching for Embeddings
# ------------------------------
@functools.lru_cache(maxsize=128)
def get_embedding(text: str, model_name: str = "all-MiniLM-L6-v2"):
    """Return a cached embedding for a given text."""
    embedder = SentenceTransformer(model_name)
    return embedder.encode(text)


# ------------------------------
# LRU Cache for Query Results
# ------------------------------
class LRUCache:
    """LRU Cache implementation for query results"""

    def __init__(self, capacity=100):
        self.capacity = capacity
        self.cache = {}
        self.order = []

    def __contains__(self, key):
        return key in self.cache

    def __getitem__(self, key):
        if key not in self.cache:
            return None

        # Update access order
        self.order.remove(key)
        self.order.append(key)

        return self.cache[key]

    def __setitem__(self, key, value):
        # If key exists, update order
        if key in self.cache:
            self.order.remove(key)
        # If cache is full, remove least recently used item
        elif len(self.cache) >= self.capacity:
            lru_key = self.order.pop(0)
            del self.cache[lru_key]

        # Add new item
        self.cache[key] = value
        self.order.append(key)

    def clear(self):
        """Clear the cache"""
        self.cache = {}
        self.order = []


# ------------------------------
# Conversation State Management
# ------------------------------
class ConversationState:
    """Tracks the state of a conversation for context management with enhanced capabilities"""

    def __init__(self, max_history=10):
        self.max_history = max_history
        self.history = []
        self.current_library = None
        self.current_building = None
        self.current_dorm = None
        self.current_course = None
        self.current_major = None
        self.current_club = None
        self.awaiting_followup = False
        self.last_intent = None
        self.mentioned_entities = {
            "libraries": set(),
            "buildings": set(),
            "dorms": set(),
            "courses": set(),
            "majors": set(),
            "clubs": set(),
        }
        self.intent_counts = defaultdict(int)  # Track common intents for user
        self.is_personal_query = False
        self.last_query_time = None
        self.session_start_time = datetime.now()
        logger.info("Initialized enhanced conversation state.")

    def add_message(self, speaker: str, message: str):
        # Add timestamp to track conversation pacing
        current_time = datetime.now()
        if self.last_query_time:
            time_diff = (current_time - self.last_query_time).total_seconds()
            # Add time context for long pauses (over 2 minutes)
            if speaker == "User" and time_diff > 120:
                logger.info(f"User returned after {time_diff:.1f} seconds")

        self.last_query_time = current_time

        # Add message to history with timestamp
        timestamp = current_time.strftime("%H:%M:%S")
        self.history.append(f"[{timestamp}] {speaker}: {message}")

        # Keep only the most recent messages
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history :]

        # If it's the assistant's message, update followup expectation
        if speaker == "Assistant":
            # Check if the response ends with a question or suggestion
            self.awaiting_followup = (
                message.rstrip().endswith("?") or "would you like" in message.lower()
            )

        # If it's the user's message, update context
        elif speaker == "User":
            # Reset followup flag
            self.awaiting_followup = False

            # Check for personal queries
            self.is_personal_query = self._check_personal_query(message)

            # Track session duration for context
            session_duration = (
                current_time - self.session_start_time
            ).total_seconds() / 60
            if session_duration > 20:
                # Long conversation - user might need a reminder about capabilities
                logger.info(
                    f"Long conversation detected: {session_duration:.1f} minutes"
                )

    def _check_personal_query(self, query):
        """Enhanced check for personal queries"""
        personal_indicators = [
            r"\bmy\s+([a-z]+\b)",  # Captures the noun after "my"
            r"\bi\s+am\s+([a-z]+\b)",
            r"\bam\s+i\s+([a-z]+\b)",
            r"\bdo\s+i\s+([a-z]+\b)",
            r"\bcan\s+i\s+([a-z]+\b)",
            r"\bwhat\s+is\s+my\b",
            r"\bwhere\s+is\s+my\b",
            r"\bhow\s+do\s+i\s+([a-z]+\b)",
            r"\bi\s+like\b",
            r"\bi\s+enjoy\b",
            r"\bi\s+prefer\b",
            r"\bi\s+want\b",
            r"\bif\s+i\s+am\b",
            r"\bcould\s+i\b",
            r"\bshould\s+i\b",
        ]

        for pattern in personal_indicators:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                # Log what kind of personal info was requested
                if match.groups():
                    logger.info(f"Personal query detected about: {match.group(1)}")
                return True

        return False

    def is_followup_question(self, query):
        """Enhanced followup detection"""
        # Short responses are often follow-ups
        if len(query.strip().split()) <= 3:
            return True

        # Check for pronouns referring to previous context
        followup_indicators = [
            r"\b(it|its|they|their|there|that|this|those|these)\b",
            r"^(what about|how about|and)\b",
            r"^(what|where|when|how|why|who|which)\b.{1,30}\?$",  # Short questions
            r"\btoo\b$",  # Ending with "too" suggests reference to previous
            r"\balso\b",  # "also" suggests building on previous
            r"^(yes|no|sure|okay|yeah|nope)",  # Affirmative/negative responses
            r"\banother\b",  # Asking for another similar thing
        ]

        for pattern in followup_indicators:
            if re.search(pattern, query, re.IGNORECASE):
                return True

        # Check if query refers to the most recent entity mentioned
        for entity_type in [
            "libraries",
            "buildings",
            "dorms",
            "courses",
            "majors",
            "clubs",
        ]:
            if self.mentioned_entities[entity_type]:
                most_recent = list(self.mentioned_entities[entity_type])[-1]
                if most_recent.lower() in query.lower():
                    return True

        return False

    def update_intent_tracking(self, intent):
        """Track user intent patterns"""
        self.intent_counts[intent] += 1
        self.last_intent = intent

    def get_dominant_interests(self):
        """Return the user's most common interests based on intent frequency"""
        if not self.intent_counts:
            return None

        # Find the most common intent
        max_count = max(self.intent_counts.values())
        if max_count < 2:  # Need at least 2 of same type to establish pattern
            return None

        dominant_intents = [
            intent for intent, count in self.intent_counts.items() if count == max_count
        ]

        if dominant_intents:
            return dominant_intents[0]
        return None

    def get_history(self) -> str:
        return "\n".join(self.history)

    def set_active_entity(self, entity_type, entity_data, name_key):
        """Generalized method to set active entities"""
        if entity_type == "library":
            self.current_library = entity_data
            if entity_data and name_key in entity_data:
                self.mentioned_entities["libraries"].add(entity_data[name_key])
        elif entity_type == "building":
            self.current_building = entity_data
            if entity_data and name_key in entity_data:
                self.mentioned_entities["buildings"].add(entity_data[name_key])
        elif entity_type == "dorm":
            self.current_dorm = entity_data
            if entity_data and name_key in entity_data:
                self.mentioned_entities["dorms"].add(entity_data[name_key])
        elif entity_type == "course":
            self.current_course = entity_data
            if entity_data and name_key in entity_data:
                self.mentioned_entities["courses"].add(entity_data[name_key])
        elif entity_type == "major":
            self.current_major = entity_data
            if entity_data and name_key in entity_data:
                self.mentioned_entities["majors"].add(entity_data[name_key])
        elif entity_type == "club":
            self.current_club = entity_data
            if entity_data and name_key in entity_data:
                self.mentioned_entities["clubs"].add(entity_data[name_key])

    def set_active_library(self, library):
        """Set the active library for the conversation"""
        self.set_active_entity("library", library, "Library Name")

    def get_active_library(self):
        """Get the currently active library in conversation"""
        return self.current_library

    def set_active_building(self, building):
        """Set the active building for the conversation"""
        self.set_active_entity("building", building, "Building Name")

    def get_active_building(self):
        """Get the currently active building in conversation"""
        return self.current_building

    def set_active_dorm(self, dorm):
        """Set the active dorm for the conversation"""
        self.set_active_entity("dorm", dorm, "Building Name")

    def get_active_dorm(self):
        """Get the currently active dorm in conversation"""
        return self.current_dorm

    def set_active_course(self, course):
        """Set the active course for the conversation"""
        self.set_active_entity("course", course, "Course Code")

    def get_active_course(self):
        """Get the currently active course in conversation"""
        return self.current_course

    def set_active_major(self, major):
        """Set the active major for the conversation"""
        if isinstance(major, dict) and "department" in major:
            # For structured academic info
            self.current_major = major
            self.mentioned_entities["majors"].add(major["department"])
        elif isinstance(major, dict) and "response" in major:
            # For new response-based format
            self.current_major = major
            self.mentioned_entities["majors"].add(major["query"])
        else:
            # For legacy format
            self.set_active_entity("major", major, "Department")

    def get_active_major(self):
        """Get the currently active major in conversation"""
        return self.current_major

    def set_active_club(self, club):
        """Set the active club for the conversation"""
        self.set_active_entity("club", club, "Organization Name")

    def get_active_club(self):
        """Get the currently active club in conversation"""
        return self.current_club

    def should_maintain_context(self, query, previous_context):
        """Enhanced context maintenance decision with better entity tracking"""
        if not previous_context:
            return False

        # Short queries usually maintain context
        if len(query.strip().split()) <= 3:
            return True

        query_lower = query.lower()

        # Check if a different entity is explicitly mentioned
        entity_mentioned = False
        context_maintained = True

        if isinstance(previous_context, dict):
            # Determine what type of entity we're dealing with
            entity_type = None
            entity_name = None

            if "Library Name" in previous_context:
                entity_type = "libraries"
                entity_name = previous_context.get("Library Name", "")
            elif "Building Name" in previous_context:
                entity_type = "buildings"
                entity_name = previous_context.get("Building Name", "")
            elif "Course Code" in previous_context:
                entity_type = "courses"
                entity_name = previous_context.get("Course Code", "")
            elif "Department" in previous_context:
                entity_type = "majors"
                entity_name = previous_context.get("Department", "")
            elif "department" in previous_context:  # For new structured format
                entity_type = "majors"
                entity_name = previous_context.get("department", "")
            elif "Organization Name" in previous_context:
                entity_type = "clubs"
                entity_name = previous_context.get("Organization Name", "")

            if entity_type and entity_name:
                # Check if any other entity of this type is mentioned
                for mentioned in self.mentioned_entities[entity_type]:
                    if (
                        mentioned.lower() in query_lower
                        and mentioned.lower() != entity_name.lower()
                        and len(mentioned) > 3
                    ):  # Avoid short name false positives

                        entity_mentioned = True
                        context_maintained = False
                        break

                # Check explicit context switchers
                context_switchers = [
                    "instead",
                    "different",
                    "another",
                    "not that",
                    "other than",
                ]
                if any(switcher in query_lower for switcher in context_switchers):
                    context_maintained = False

        # If no other entity mentioned and no context switchers, maintain context
        return not entity_mentioned and context_maintained

    def reset_active_contexts(self):
        """Reset all active contexts"""
        self.current_library = None
        self.current_building = None
        self.current_dorm = None
        self.current_course = None
        self.current_major = None
        self.current_club = None


# ------------------------------
# Academic Knowledge Retrieval
# ------------------------------
class AcademicInfoRetrieval:
    def __init__(self, embedding_model: SentenceTransformer):
        self.embedding_model = embedding_model
        self.programs_data = load_programs_data()
        self.majors_data = load_majors_data()
        self.courses_data = load_courses_data()

        # Create department indexes and mappings
        self._create_indexes()

        self.query_cache = LRUCache(capacity=100)
        logger.info(
            f"Initialized academic info retrieval with {len(self.programs_data)} programs, {len(self.majors_data)} majors, and {len(self.courses_data)} courses."
        )

    def _create_indexes(self):
        """Create useful indexes for quick lookups"""
        # Create a department-to-programs mapping
        self.department_programs = defaultdict(list)
        for program in self.programs_data:
            dept = program.get("Department", "").strip()
            if dept:
                self.department_programs[dept.lower()].append(program)

        # Create a program name-to-program mapping
        self.program_by_name = {}
        for program in self.programs_data:
            name = program.get("Name", "").strip()
            if name:
                self.program_by_name[name.lower()] = program

        # Create mappings of common search terms to departments
        self.search_terms = {}
        for dept in self.department_programs.keys():
            # Add the department name itself
            self.search_terms[dept] = dept

            # Add simplified versions
            simple_name = dept.replace("&", "and").lower()
            self.search_terms[simple_name] = dept

            # Add common abbreviations - for example "CS" for Computer Science
            if "computer science" in dept.lower():
                self.search_terms["cs"] = dept
                self.search_terms["computer science"] = dept
            elif "engineering" in dept.lower():
                # Extract abbreviation for engineering departments
                parts = dept.split()
                if len(parts) > 1:
                    abbr = "".join(p[0] for p in parts if p[0].isalpha()).upper()
                    if len(abbr) > 1:
                        self.search_terms[abbr.lower()] = dept

    def get_info(self, query: str) -> dict:
        """Get comprehensive information about an academic program or department"""
        # Check cache first
        cache_key = f"academic:{query.lower()}"
        if cache_key in self.query_cache:
            return self.query_cache[cache_key]

        query_lower = query.lower()

        # Prepare result structure
        result = {
            "department": "",
            "programs": [],
            "description": "No detailed information available.",
            "colleges": set(),
            "query": query,  # Store original query
            "type": "unknown",  # Department or specific program
        }

        # Try direct match to a department using our search terms index
        matched_dept = None
        if query_lower in self.search_terms:
            matched_dept = self.search_terms[query_lower]
        else:
            # Try common variations
            query_simple = (
                query_lower.replace("major", "").replace("program", "").strip()
            )
            if query_simple in self.search_terms:
                matched_dept = self.search_terms[query_simple]

        # If we matched a department, get all programs in that department
        if matched_dept:
            result["department"] = matched_dept
            result["programs"] = self.department_programs[matched_dept]
            result["type"] = "department"

            # Extract colleges from program names
            for program in result["programs"]:
                name = program.get("Name", "")
                if "|" in name:
                    college = name.split("|")[1].strip()
                    result["colleges"].add(college)

            # Look for a description
            for entry in self.majors_data:
                if entry.get("Department", "").lower() == matched_dept:
                    result["description"] = entry.get(
                        "Description", result["description"]
                    )
                    break

        # Try direct match to program name
        if not result["programs"]:
            # Try direct match on program name
            for program in self.programs_data:
                name = program.get("Name", "").lower()
                if query_lower in name:
                    result["programs"].append(program)
                    result["department"] = program.get("Department", "")
                    result["type"] = "program"

                    # Look for a description
                    for entry in self.majors_data:
                        if (
                            entry.get("Department", "").lower()
                            == result["department"].lower()
                        ):
                            result["description"] = entry.get(
                                "Description", result["description"]
                            )
                            break

        # If still no match, try fuzzy matching
        if not result["programs"]:
            # Try fuzzy matching on department
            department_names = list(self.department_programs.keys())
            matches = difflib.get_close_matches(
                query_lower, department_names, n=1, cutoff=0.7
            )

            if matches:
                matched_dept = matches[0]
                result["department"] = matched_dept
                result["programs"] = self.department_programs[matched_dept]
                result["type"] = "department"

                # Extract colleges from program names
                for program in result["programs"]:
                    name = program.get("Name", "")
                    if "|" in name:
                        college = name.split("|")[1].strip()
                        result["colleges"].add(college)

                # Look for a description
                for entry in self.majors_data:
                    if entry.get("Department", "").lower() == matched_dept:
                        result["description"] = entry.get(
                            "Description", result["description"]
                        )
                        break

        # If still no programs found, try semantic search
        if not result["programs"]:
            try:
                # Encode query
                query_embedding = self.embedding_model.encode(query_lower)
                best_match = None
                best_score = 0

                # Search for department match first
                for dept in self.department_programs.keys():
                    dept_embedding = self.embedding_model.encode(dept)

                    # Calculate cosine similarity
                    similarity = torch.nn.functional.cosine_similarity(
                        torch.tensor(query_embedding).unsqueeze(0),
                        torch.tensor(dept_embedding).unsqueeze(0),
                    ).item()

                    if similarity > best_score:
                        best_score = similarity
                        best_match = dept

                if best_match and best_score > 0.7:
                    result["department"] = best_match
                    result["programs"] = self.department_programs[best_match]
                    result["type"] = "department"

                    # Look for a description
                    for entry in self.majors_data:
                        if entry.get("Department", "").lower() == best_match:
                            result["description"] = entry.get(
                                "Description", result["description"]
                            )
                            break
            except Exception as e:
                logger.error(f"Error in semantic search: {e}")

        # Convert colleges set to list before caching
        result["colleges"] = list(result["colleges"])

        # Cache result
        self.query_cache[cache_key] = result
        return result

    def get_all_majors(self) -> list:
        """Get a list of all majors offered"""
        majors = []
        for program in self.programs_data:
            if program.get("Type") == "Major":
                majors.append(program)
        return majors

    def get_all_minors(self) -> list:
        """Get a list of all minors offered"""
        minors = []
        for program in self.programs_data:
            if program.get("Type") == "Minor":
                minors.append(program)
        return minors

    def get_programs_by_college(self, college: str) -> list:
        """Get all programs offered by a specific college"""
        college_lower = college.lower()
        programs = []
        for program in self.programs_data:
            name = program.get("Name", "")
            if "|" in name and college_lower in name.split("|")[1].lower():
                programs.append(program)
        return programs


# ------------------------------
# Campus Clubs Retrieval
# ------------------------------
class CampusClubsRetrieval:
    def __init__(self, embedding_model: SentenceTransformer):
        self.embedding_model = embedding_model
        self.club_data = load_clubs_data()
        self.query_cache = LRUCache(capacity=100)
        logger.info(
            f"Initialized campus clubs retrieval with {len(self.club_data)} entries."
        )

    def get_club_info(self, query: str) -> str:
        # Check cache first
        cache_key = f"club:{query.lower()}"
        if cache_key in self.query_cache:
            return self.query_cache[cache_key]

        # Enhanced matching with multiple approaches
        query_lower = query.lower()

        # Try direct match first with improved matching
        for entry in self.club_data:
            name = entry.get("Organization Name", "").lower()
            # Direct match, substring match, or match without "club" suffix
            if (
                query_lower == name
                or query_lower in name
                or query_lower.replace(" club", "") == name
                or query_lower.replace(" organization", "") == name
            ):

                result = entry.get(
                    "Description", "No additional information available."
                )
                self.query_cache[cache_key] = result
                return result

        # Try fuzzy matching with improved threshold
        names = [entry.get("Organization Name", "") for entry in self.club_data]
        best_matches = difflib.get_close_matches(
            query_lower, [name.lower() for name in names], n=1, cutoff=0.7
        )  # Higher threshold
        if best_matches:
            for entry in self.club_data:
                if best_matches[0] == entry.get("Organization Name", "").lower():
                    result = entry.get(
                        "Description", "No additional information available."
                    )
                    self.query_cache[cache_key] = result
                    return result

        # Try semantic search with enhanced similarity scoring
        try:
            query_embedding = self.embedding_model.encode(query_lower)
            best_match = None
            best_score = 0

            for entry in self.club_data:
                name = entry.get("Organization Name", "")
                desc = entry.get("Description", "")

                if not name:
                    continue

                # Use all information for better matching
                entry_text = f"{name} {desc}"
                entry_embedding = self.embedding_model.encode(entry_text)

                # Calculate cosine similarity
                similarity = torch.nn.functional.cosine_similarity(
                    torch.tensor(query_embedding).unsqueeze(0),
                    torch.tensor(entry_embedding).unsqueeze(0),
                ).item()

                if similarity > best_score:
                    best_score = similarity
                    best_match = entry

            if best_match and best_score > 0.7:  # Higher threshold for better quality
                result = best_match.get(
                    "Description", "No additional information available."
                )
                self.query_cache[cache_key] = result
                return result

        except Exception as e:
            logger.error(f"Error in semantic search: {e}")

        return f"No club info found for '{query}'."

    def get_clubs_by_category(self, category: str) -> List[Dict]:
        """Get clubs in a specific category with enhanced matching"""
        category_keywords = {
            "cultural": [
                "cultural",
                "international",
                "multicultural",
                "diversity",
                "heritage",
                "ethnic",
            ],
            "academic": [
                "academic",
                "honor",
                "research",
                "study",
                "education",
                "scholar",
            ],
            "professional": [
                "professional",
                "career",
                "industry",
                "business",
                "pre-professional",
                "job",
            ],
            "service": [
                "service",
                "volunteer",
                "community",
                "philanthropy",
                "charity",
                "outreach",
            ],
            "religious": [
                "religious",
                "christian",
                "catholic",
                "jewish",
                "muslim",
                "hindu",
                "faith",
                "spiritual",
            ],
            "sports": [
                "sport",
                "athletic",
                "recreation",
                "fitness",
                "outdoor",
                "team",
                "physical",
                "game",
            ],
            "greek": [
                "fraternity",
                "sorority",
                "greek",
                "panhellenic",
                "ifc",
                "chapter",
            ],
        }

        matching_clubs = []
        category_lower = category.lower()

        # First try direct category match
        if category_lower in category_keywords:
            keywords = category_keywords[category_lower]
        else:
            # Otherwise try partial matches
            for cat, words in category_keywords.items():
                if category_lower in cat or cat in category_lower:
                    keywords = words
                    break
            else:
                # If still no match, try fuzzy matching
                best_match = difflib.get_close_matches(
                    category_lower, category_keywords.keys(), n=1, cutoff=0.6
                )
                if best_match:
                    keywords = category_keywords[best_match[0]]
                else:
                    # No matches found, use the query itself as a keyword
                    keywords = [category_lower]

        # Search names, descriptions and actual category field
        for club in self.club_data:
            name = club.get("Organization Name", "").lower()
            desc = club.get("Description", "").lower()

            # Direct category match
            if any(keyword in name or keyword in desc for keyword in keywords):
                matching_clubs.append(club)

        return matching_clubs


# ------------------------------
# Query Analyzer
# ------------------------------
class QueryAnalyzer:
    def __init__(self):
        # Define comprehensive patterns for intent detection with prioritization
        self.intent_patterns = {
            "library_hours": [
                r"(?:library|lib).*hours",
                r"hours.*(?:library|lib)",
                r"when.*(?:library|lib).*open",
                r"(?:library|lib).*open.*?when",
                r"(?:library|lib).*close",
                r"is (?:library|lib) open",
                r"(?:library|lib).*schedule",
            ],
            "building_location": [
                r"where is",
                r"location of",
                r"located",
                r"address",
                r"find",
                r"get to",
                r"directions to",
                r"how.*get to",
                r"where.*find",
                r"map",
            ],
            "dorm_info": [
                r"dorm",
                r"housing",
                r"residence hall",
                r"live",
                r"on-campus housing",
                r"rooms",
                r"housing options",
                r"where to live",
                r"accommodation",
                r"freshman.*housing",
            ],
            "course_info": [
                r"course",
                r"class",
                r"(?:course|class).*description",
                r"about.*(?:course|class)",
                r"syllabus",
                r"prereq",
                r"credit",
                r"professor",
                r"instructor",
                r"teach",
                r"[A-Z]{3}\s*\d{4}",
            ],
            "major_info": [
                r"major",
                r"program",
                r"degree",
                r"concentration",
                r"department",
                r"field of study",
                r"academic program",
                r"specialization",
                r"track",
            ],
            "club_info": [
                r"club",
                r"organization",
                r"group",
                r"society",
                r"association",
                r"student org",
                r"student group",
                r"extracurricular",
                r"activities",
            ],
        }

        # Intent priority order (for resolving multiple matches)
        self.intent_priority = [
            "library_hours",
            "building_location",
            "dorm_info",
            "course_info",
            "major_info",
            "club_info",
        ]

        logger.info("Initialized enhanced query analyzer.")

    def analyze(self, query: str) -> dict:
        query_lower = query.lower()

        # Initialize result
        analysis = {
            "intent": "generic",
            "query": query,
            "is_location_query": any(
                kw in query_lower for kw in ["where", "located", "location", "address"]
            ),
            "is_hours_query": any(
                kw in query_lower
                for kw in ["hours", "open", "close", "schedule", "when"]
            ),
            "is_major_query": "major" in query_lower
            or "program" in query_lower
            or "degree" in query_lower,
            "is_club_query": "club" in query_lower or "organization" in query_lower,
            "is_dorm_query": any(
                kw in query_lower for kw in ["dorm", "housing", "residence", "live"]
            ),
            "is_course_query": "course" in query_lower
            or "class" in query_lower
            or re.search(r"[A-Z]{3}\s*\d{4}", query),
            "is_all_query": any(
                kw in query_lower
                for kw in ["all ", "list of", "what are the", "types of"]
            ),
            "is_personal_query": any(
                kw in query_lower for kw in ["my ", "i am", "for me", "my academic"]
            ),
        }

        # Match priorities
        matched_intents = []

        # Check for specific intents
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    matched_intents.append(intent)
                    break

        # Determine the highest priority match
        for priority_intent in self.intent_priority:
            if priority_intent in matched_intents:
                analysis["intent"] = priority_intent
                break

        # Extract potential entities with improved regex
        if analysis["is_major_query"]:
            # Look for major names after "major in", "studying", etc.
            major_patterns = [
                r"major in\s+([a-zA-Z\s&]+)(?:\s|$|\.|\?)",
                r"studying\s+([a-zA-Z\s&]+)(?:\s|$|\.|\?)",
                r"about\s+([a-zA-Z\s&]+)\s+major",
                r"about\s+([a-zA-Z\s&]+)\s+program",
            ]
            for pattern in major_patterns:
                match = re.search(pattern, query_lower)
                if match:
                    analysis["potential_major"] = match.group(1).strip()
                    break

        if analysis["is_course_query"]:
            # Look for course codes (e.g., "COP 3502" or "COP3502")
            course_code_pattern = r"([A-Z]{3})\s*(\d{4}[A-Za-z]*)"
            matches = re.findall(course_code_pattern, query)
            if matches:
                analysis["potential_course_code"] = f"{matches[0][0]} {matches[0][1]}"

        # Look for library names
        if "library" in query_lower or "lib" in query_lower:
            library_patterns = [
                r"(library\s+west)",
                r"(marston\s+(?:science\s+)?library)",
                r"(smathers\s+library)",
                r"(west\s+library)",
                r"(lib\s+west)",
                r"(health\s+science\s+(?:center\s+)?library)",
                r"(architecture\s+(?:&|and)\s+fine\s+arts\s+library)",
                r"(education\s+library)",
                r"(legal\s+information\s+center)",
                r"(law\s+library)",
            ]

            for pattern in library_patterns:
                match = re.search(pattern, query_lower)
                if match:
                    analysis["potential_library"] = match.group(1).strip()
                    break

        # Look for building names
        building_patterns = [
            r"(reitz\s+union)",
            r"(century\s+tower)",
            r"(ben\s+hill\s+griffin\s+stadium)",
            r"(the\s+swamp)",
            r"(turlington\s+hall)",
            r"(norman\s+hall)",
            r"(dickinson\s+hall)",
            r"(matherly\s+hall)",
            r"(tigert\s+hall)",
            r"(newell\s+hall)",
            r"(weil\s+hall)",
        ]

        for pattern in building_patterns:
            match = re.search(pattern, query_lower)
            if match:
                analysis["potential_building"] = match.group(1).strip()
                break

        # Look for dorm names
        dorm_patterns = [
            r"(broward\s+hall)",
            r"(jennings\s+hall)",
            r"(rawlings\s+hall)",
            r"(simpson\s+hall)",
            r"(cypress\s+hall)",
            r"(hume\s+hall)",
            r"(springs\s+complex)",
            r"(beaty\s+towers)",
            r"(keys\s+complex)",
            r"(yulee\s+hall)",
            r"(reid\s+hall)",
            r"(murphree\s+hall)",
            r"(thomas\s+hall)",
        ]

        for pattern in dorm_patterns:
            match = re.search(pattern, query_lower)
            if match:
                analysis["potential_dorm"] = match.group(1).strip()
                break

        logger.info(f"Enhanced query analysis result: {analysis}")
        return analysis

    def is_major_query(self, query):
        """Enhanced detection for academic major queries"""
        query_lower = query.lower()

        # Check for explicit major keywords
        major_keywords = [
            "major",
            "program",
            "degree",
            "study",
            "department",
            "concentration",
            "specialization",
        ]

        if any(keyword in query_lower for keyword in major_keywords):
            return True

        # Check for academic field names (common majors)
        common_majors = [
            "computer science",
            "engineering",
            "business",
            "psychology",
            "biology",
            "chemistry",
            "economics",
            "english",
            "history",
            "mathematics",
            "physics",
            "political science",
            "sociology",
        ]

        if any(major in query_lower for major in common_majors):
            return True

        return False


# ------------------------------
# Response Generator
# ------------------------------
class ResponseGenerator:
    """Enhanced response generator with better templating, data validation and academic program support"""

    def __init__(self, llm=None):
        self.llm = llm

        # Template responses for common queries with consistent formatting
        self.templates = {
            "hours": """
📚 {library_name} Hours

Today ({day_of_week}): {hours_today}

Weekly Schedule:
{all_hours}
{special_hours_note}
""",
            "location": """
🏢 {entity_name}

📍 Located at: {location}
""",
            "building_info": """
🏢 {building_name}{abbr_text}

📍 Location: {address}

{description}
""",
            "dorm_info": """
🏠 {dorm_name}

📍 Location: {location}
🏠 Type: {hall_type} residence hall

{description}

Features include:
{features_list}
""",
            "course_info": """
📚 {course_code}: {course_title}

Credits: {credits}

{description}

Prerequisites: {prerequisites}
""",
            "major_info": """
🎓 {major_name}

Department: {department}
{college_info}
{type_info}

{description}

{programs_list}
""",
            "program_detail": """
Program: {program_name}
Type: {program_type}
Department: {department}
{college}

{catalog_url}
""",
            "club_info": """
🎭 {club_name}

{description}
""",
            "personal_query": """
I don't have access to your personal information such as {personal_type}. As an AI assistant, I can only provide general information about UF.

For personalized information, please visit ONE.UF or contact the relevant department directly.
""",
            "meta_question": """
I'm the UF Assistant, an AI designed to provide helpful information about the University of Florida. I can answer questions about campus buildings, libraries, housing, academic programs, and other UF-related topics.

How can I help you today?
""",
            "error": """
I apologize, but I couldn't find specific information about {query_subject}. Could you try rephrasing your question or asking about something else?
""",
        }

    def generate(
        self,
        analysis,
        library_info=None,
        building_info=None,
        dorm_info=None,
        major_info=None,
        club_info=None,
        academic_calendar=None,
    ):
        """Generate a response with improved data validation"""
        query = analysis["query"]
        intent = analysis["intent"]

        # Check for personal query first
        if analysis.get("is_personal_query"):
            return self._handle_personal_query(query)

        # Handle different intents with data validation
        if intent == "library_hours" and library_info:
            try:
                return self._generate_library_hours_response(
                    library_info, academic_calendar
                )
            except Exception as e:
                logger.error(f"Error generating library hours response: {e}")
                return self.templates["error"].format(query_subject="library hours")

        elif intent == "building_location" and building_info:
            try:
                return self._generate_building_location_response(building_info)
            except Exception as e:
                logger.error(f"Error generating building location response: {e}")
                return self.templates["error"].format(query_subject="building location")

        elif intent == "dorm_info" and dorm_info:
            try:
                return self._generate_dorm_info_response(dorm_info)
            except Exception as e:
                logger.error(f"Error generating dorm info response: {e}")
                return self.templates["error"].format(
                    query_subject="dormitory information"
                )

        elif intent == "major_info" and major_info:
            try:
                # Handle the new format from search_major_info
                if isinstance(major_info, dict) and "response" in major_info:
                    return major_info["response"]
                else:
                    return self._generate_major_info_response(major_info)
            except Exception as e:
                logger.error(f"Error generating major info response: {e}")
                return self.templates["error"].format(query_subject="major information")

        elif intent == "club_info" and club_info:
            try:
                return self._generate_club_info_response(club_info)
            except Exception as e:
                logger.error(f"Error generating club info response: {e}")
                return self.templates["error"].format(query_subject="club information")

        # Check for valid entity information that might not match the intent
        if library_info and not intent == "library_hours":
            try:
                if analysis.get("is_location_query"):
                    return self._generate_library_location_response(library_info)
                else:
                    return self._generate_library_info_response(library_info)
            except Exception:
                pass

        if building_info and not intent == "building_location":
            try:
                return self._generate_building_location_response(building_info)
            except Exception:
                pass

        if dorm_info and not intent == "dorm_info":
            try:
                return self._generate_dorm_info_response(dorm_info)
            except Exception:
                pass

        # If all else fails, use LLM if available
        if self.llm:
            try:
                return self._generate_llm_response(
                    query,
                    analysis,
                    library_info,
                    building_info,
                    dorm_info,
                    major_info,
                    club_info,
                    academic_calendar,
                )
            except Exception as e:
                logger.error(f"Error generating LLM response: {e}")

        # Fallback response when no specific information found
        return f"I don't have specific information to answer your question about {query}. Could you try asking about a specific library, building, major, or club at UF?"

    def _handle_personal_query(self, query):
        """Handle personal queries with improved UF-relevant detection"""
        # First check if this is a UF-relevant personal query that we SHOULD answer
        if self._is_uf_relevant_personal_query(query):
            # For UF-relevant personal queries, forward to LLM if available
            if self.llm:
                try:
                    prompt = f"""You are the UF Assistant, an AI designed to provide helpful information about the University of Florida.

    User Question: {query}

    This is a personal question about University of Florida academics or campus life.
    Respond as if you are a helpful academic advisor. Provide tailored recommendations
    based on the person's stated interests or preferences. Include specific UF majors,
    programs, or departments that would be appropriate for them. Do not refuse to answer
    or say you lack access to personal information - instead, provide helpful guidance.
    """

                    # Generate response with LLaMA
                    result = self.llm(
                        prompt=prompt,
                        max_tokens=500,
                        temperature=0.7,
                        stop=["User:", "Assistant:"],
                    )

                    # Extract response text
                    return result["choices"][0]["text"].strip()
                except Exception as e:
                    logger.error(
                        f"Error generating LLM response for personal query: {e}"
                    )
                    # Fall back to standard personal query handling

        # For non-UF-relevant personal queries, use the template
        query_lower = query.lower()
        personal_type = ""

        if "my major" in query_lower or "my degree" in query_lower:
            personal_type = "your major, courses, or academic program"
        elif "my schedule" in query_lower or "my class" in query_lower:
            personal_type = "your schedule or classes"
        elif "my dorm" in query_lower or "my room" in query_lower:
            personal_type = "your housing assignment or room"
        elif "my grade" in query_lower or "my gpa" in query_lower:
            personal_type = "your grades or academic standing"
        elif "my account" in query_lower or "my password" in query_lower:
            personal_type = "your account information or credentials"
        else:
            personal_type = "personal information"

        return self.templates["personal_query"].format(personal_type=personal_type)

    def _generate_library_hours_response(self, library, academic_calendar=None):
        """Generate response for library hours query with robust data validation"""
        library_name = library.get("Library Name", "Unknown Library")

        # Debug logging
        logger.info(f"Library hours data structure: {type(library.get('Hours'))}")
        if isinstance(library.get("Hours"), dict):
            logger.info(f"Library hours keys: {library.get('Hours').keys()}")

        # Get today's day of week
        today = datetime.now().strftime("%A")

        # Get hours for today with validation
        hours_today = "Information not available"
        hours_data = library.get("Hours", {})

        if isinstance(hours_data, dict):
            # Try direct match
            if today in hours_data:
                hours_today = hours_data[today]
            else:
                # Try case-insensitive match
                for day, hours in hours_data.items():
                    if isinstance(day, str) and day.lower() == today.lower():
                        hours_today = hours
                        break

        # Format all hours with validation
        all_hours = ""
        if isinstance(hours_data, dict) and hours_data:
            for day, hours in hours_data.items():
                if isinstance(day, str) and isinstance(hours, str):
                    all_hours += f"• {day}: {hours}\n"

        # If no hours found, use default hours
        if not all_hours:
            all_hours = "• Monday: 8:00am - 6:00pm\n• Tuesday: 8:00am - 6:00pm\n• Wednesday: 8:00am - 6:00pm\n• Thursday: 8:00am - 6:00pm\n• Friday: 8:00am - 5:00pm\n• Saturday: 10:00am - 5:00pm\n• Sunday: 12:00pm - 5:00pm"

        # Check for special hours from academic calendar
        special_hours_note = ""
        if academic_calendar and isinstance(academic_calendar, dict):
            today_str = datetime.now().strftime("%Y-%m-%d")
            exceptions = academic_calendar.get("library_schedule_exceptions", {})

            if isinstance(exceptions, dict) and today_str in exceptions:
                exception = exceptions[today_str]
                if isinstance(exception, dict):
                    if "all" in exception:
                        special_hours_note = f"\nSpecial Note: {exception['all']}"
                    elif library_name in exception:
                        special_hours_note = (
                            f"\nSpecial Note: {exception[library_name]}"
                        )

        # Format and return the response
        response = self.templates["hours"].format(
            library_name=library_name,
            day_of_week=today,
            hours_today=hours_today,
            all_hours=all_hours.strip(),
            special_hours_note=special_hours_note,
        )

        return response.strip()

    def _is_uf_relevant_personal_query(self, query):
        """Determine if a personal query is about UF programs and should be answered"""
        query_lower = query.lower()

        # UF-relevant keywords in context of personal questions
        uf_relevant_keywords = [
            "major",
            "program",
            "degree",
            "study",
            "class",
            "course",
            "career",
            "job",
            "college",
            "department",
            "admission",
            "application",
            "academic",
            "subject",
            "field",
            "interest",
            "graduate",
            "art",
            "science",
            "engineering",
            "business",
            "medicine",
            "law",
            "education",
            "minor",
        ]

        # UF-specific keywords
        uf_specific = ["uf", "university of florida", "gator", "gators"]

        # Check if the query contains UF-relevant academic keywords
        has_uf_relevant = any(
            keyword in query_lower for keyword in uf_relevant_keywords
        )

        # Check if there's a specific reference to UF
        has_uf_reference = any(term in query_lower for term in uf_specific)

        # Consider it UF-relevant if it has both relevant keywords and UF reference,
        # or if it's a query about majors/programs/courses (high confidence academic)
        high_confidence_academic = any(
            term in query_lower for term in ["major", "program", "course", "degree"]
        )

        return (has_uf_relevant and has_uf_reference) or high_confidence_academic

    def _generate_library_location_response(self, library):
        """Generate response for library location query"""
        library_name = library.get("Library Name", "Unknown Library")
        location = library.get("Location", "University of Florida campus")

        response = self.templates["location"].format(
            entity_name=library_name, location=location
        )

        return response.strip()

    def _generate_library_info_response(self, library):
        """Generate general info about a library"""
        library_name = library.get("Library Name", "Unknown Library")
        location = library.get("Location", "University of Florida campus")
        description = library.get("Description", "")
        special_notes = library.get("Special Notes", "")

        if not description:
            description = "A campus library at the University of Florida."

        if special_notes:
            description += f"\n\n{special_notes}"

        response = f"""
📚 {library_name}

📍 Located at: {location}

{description}
"""

        return response.strip()

    def _generate_building_location_response(self, building):
        """Generate response for building location query"""
        building_name = building.get("Building Name", "Unknown Building")
        address = building.get("Address", "University of Florida campus")
        description = building.get(
            "Description", "No additional information is available for this building."
        )
        abbr = building.get("Abbreviation", "")

        if not address:
            address = "the University of Florida campus in Gainesville"

        abbr_text = f" ({abbr})" if abbr else ""

        response = self.templates["building_info"].format(
            building_name=building_name,
            abbr_text=abbr_text,
            address=address,
            description=description,
        )

        return response.strip()

    def _generate_dorm_info_response(self, dorm):
        """Generate response for dorm info query with enhanced formatting"""
        dorm_name = dorm.get("Building Name", "Unknown Residence Hall")
        hall_type = dorm.get("Hall Type", "residential")
        description = dorm.get("Description", "Information not available.")
        location = dorm.get("Location", "the University of Florida campus")

        # Format features list with validation
        features_list = ""
        if dorm.get("Features") and isinstance(dorm["Features"], list):
            for feature in dorm["Features"]:
                if feature and isinstance(feature, str) and feature.strip():
                    features_list += f"• {feature.strip()}\n"

        if not features_list:
            features_list = "• Standard residence hall amenities\n• Study spaces\n• Laundry facilities\n• High-speed internet"

        response = self.templates["dorm_info"].format(
            dorm_name=dorm_name,
            hall_type=hall_type,
            location=location,
            description=description,
            features_list=features_list,
        )

        return response.strip()

    def _generate_major_info_response(self, major_info):
        """Generate response for major info query with enhanced academic program support"""
        # Check if this is a new format structured major info
        if isinstance(major_info, dict) and "programs" in major_info:
            return self._generate_structured_major_info(major_info)

        # Handle legacy format
        major_name = major_info.get("Department", "Unknown Major")
        department = major_info.get("Department", "Unknown Department")
        description = major_info.get(
            "Description", "No detailed description available."
        )

        # Create a properly capitalized name
        display_name = " ".join(word.capitalize() for word in major_name.split())

        response = self.templates["major_info"].format(
            major_name=display_name,
            department=department,
            college_info="",
            type_info="",
            description=description,
            programs_list="",
        )

        return response.strip()

    def _generate_structured_major_info(self, major_info):
        """Generate response for structured academic program information"""
        # Extract basic information
        department = major_info.get("department", "Unknown Department")
        description = major_info.get(
            "description", "No detailed information available."
        )
        programs = major_info.get("programs", [])
        colleges = major_info.get("colleges", [])
        original_query = major_info.get("query", "")

        # Create a capitalized display name for the major
        if original_query:
            display_name = " ".join(
                word.capitalize() for word in original_query.split()
            )
        else:
            display_name = " ".join(word.capitalize() for word in department.split())

        # Format colleges information
        college_info = ""
        if colleges:
            if len(colleges) == 1:
                college_info = f"College: {colleges[0]}"
            else:
                college_info = f"Colleges: {', '.join(colleges)}"

        # Format type information
        program_types = set()
        for program in programs:
            if program.get("Type"):
                program_types.add(program.get("Type"))

        type_info = ""
        if program_types:
            type_info = f"Available as: {', '.join(program_types)}"

        # Format programs list
        programs_list = ""
        if programs:
            programs_list = "Available Programs:\n"
            for program in programs:
                name = program.get("Name", "")
                url = program.get("URL", "")
                prog_type = program.get("Type", "")

                if name:
                    program_entry = f"• {name} ({prog_type})"
                    if url:
                        program_entry += f" - Catalog: https://catalog.ufl.edu{url}"
                    programs_list += program_entry + "\n"

        # Format the response
        response = self.templates["major_info"].format(
            major_name=display_name,
            department=department,
            college_info=college_info,
            type_info=type_info,
            description=description,
            programs_list=programs_list,
        )

        return response.strip()

    def _generate_club_info_response(self, club):
        """Generate response for club info query"""
        club_name = club.get("Organization Name", "Unknown Club")
        description = club.get("Description", "No detailed description available.")

        response = self.templates["club_info"].format(
            club_name=club_name, description=description
        )

        return response.strip()

    def _generate_llm_response(
        self,
        query,
        analysis,
        library_info=None,
        building_info=None,
        dorm_info=None,
        major_info=None,
        club_info=None,
        academic_calendar=None,
    ):
        """Generate a response using the LLM with contextual information"""
        if not self.llm:
            return "I'm not sure how to answer that question about UF."

        # Build prompt with relevant context
        prompt = self._build_llm_prompt(
            query,
            analysis,
            library_info,
            building_info,
            dorm_info,
            major_info,
            club_info,
            academic_calendar,
        )

        try:
            # Generate response
            result = self.llm(
                prompt=prompt,
                max_tokens=500,
                temperature=0.7,
                stop=["User:", "Assistant:"],
            )

            # Extract response text
            response = result["choices"][0]["text"].strip()
            return response

        except Exception as e:
            logger.error(f"Error generating LLM response: {e}")
            return "I encountered an error while processing your request. Could you try rephrasing your question?"

    def _build_llm_prompt(
        self,
        query,
        analysis,
        library_info=None,
        building_info=None,
        dorm_info=None,
        major_info=None,
        club_info=None,
        academic_calendar=None,
    ):
        """Build a prompt for the LLM with relevant context"""
        # Start with system instructions
        prompt = "You are the UF Assistant, an AI designed to provide helpful information about the University of Florida.\n\n"

        # Add markdown formatting instruction - explicitly say NO LINKS
        prompt += "IMPORTANT: Format your response using clean, simple markdown syntax with proper headers, lists, and bold text. DO NOT INCLUDE ANY LINKS OR URLS IN YOUR RESPONSE - no matter what. Never use markdown link syntax [text](url).\n\n"

        # Add relevant context
        prompt += "Context Information:\n"

        if library_info:
            prompt += f"Library: {library_info.get('Library Name', '')}\n"
            if "Hours" in library_info and isinstance(library_info["Hours"], dict):
                prompt += "Hours:\n"
                for day, hours in library_info["Hours"].items():
                    prompt += f"- {day}: {hours}\n"
            if "Location" in library_info:
                prompt += f"Location: {library_info['Location']}\n"

        if building_info:
            prompt += f"Building: {building_info.get('Building Name', '')}\n"
            if "Address" in building_info:
                prompt += f"Address: {building_info['Address']}\n"
            if "Description" in building_info:
                prompt += f"Description: {building_info['Description']}\n"

        if dorm_info:
            prompt += f"Residence Hall: {dorm_info.get('Building Name', '')}\n"
            if "Hall Type" in dorm_info:
                prompt += f"Type: {dorm_info['Hall Type']}\n"
            if "Location" in dorm_info:
                prompt += f"Location: {dorm_info['Location']}\n"
            if "Description" in dorm_info:
                prompt += f"Description: {dorm_info['Description']}\n"

        if major_info:
            # Handle both structured and legacy formats
            if isinstance(major_info, dict) and "programs" in major_info:
                prompt += f"Major/Department: {major_info.get('department', '')}\n"
                if "description" in major_info:
                    prompt += f"Description: {major_info['description']}\n"
                if "programs" in major_info:
                    prompt += "Programs:\n"
                    for program in major_info["programs"]:
                        prompt += (
                            f"- {program.get('Name', '')} ({program.get('Type', '')})\n"
                        )
            elif isinstance(major_info, dict) and "response" in major_info:
                # New response-based format
                prompt += f"Major Info: Available as formatted text\n"
            else:
                prompt += f"Major: {major_info.get('Department', '')}\n"
                if "Description" in major_info:
                    prompt += f"Description: {major_info['Description']}\n"

        if club_info:
            prompt += f"Club: {club_info.get('Organization Name', '')}\n"
            if "Description" in club_info:
                prompt += f"Description: {club_info['Description']}\n"

        if academic_calendar:
            prompt += "Academic Calendar Information:\n"
            for term, dates in academic_calendar.get("terms", {}).items():
                prompt += f"- {term}: {dates['start']} to {dates['end']}\n"

        # Add important facts and corrections
        prompt += "\nFactual Corrections:\n"
        prompt += "- Century Tower is a bell tower/carillon, NOT a residence hall.\n"
        prompt += "- Residence halls for freshmen include Broward, Jennings, Rawlings, Simpson, and others, but NOT Century Tower.\n"

        # Add the query
        prompt += f"\nUser Question: {query}\n\n"

        # Add markdown formatting guidelines - improved for cleaner output and NO LINKS
        prompt += "FORMATTING GUIDELINES:\n"
        prompt += (
            "1. Use clean, proper markdown: '## Heading' with a space after the #\n"
        )
        prompt += "2. Use **bold** for emphasis, not ***triple asterisks***\n"
        prompt += "3. Format lists using * with a space: '* Item'\n"
        prompt += "4. DO NOT INCLUDE ANY LINKS OR URLS - not even to UF websites\n"
        prompt += "5. Instead of links, mention resources by name only (e.g., 'Check the UF Catalog' instead of providing a URL)\n"
        prompt += "6. Do not sign your response or add 'Best,' or 'The UF Assistant' at the end\n"
        prompt += "7. Keep your response focused and concise\n\n"

        # Add instructions based on intent
        intent = analysis.get("intent", "generic")
        if intent == "library_hours":
            prompt += "Please provide information about the library's hours, focusing on when it's open and any special schedule information.\n"
        elif intent == "building_location":
            prompt += "Please provide the location of the building and any relevant information about how to find it.\n"
        elif intent == "dorm_info":
            prompt += "Please provide information about the residence hall, including its features and location.\n"
        elif intent == "major_info":
            prompt += "Please provide information about the academic major/program, including what students learn and career opportunities.\n"
        elif intent == "club_info":
            prompt += "Please provide information about the student organization, including its purpose and activities.\n"
        else:
            prompt += (
                "Please provide a helpful response to the user's question about UF.\n"
            )

        prompt += "Assistant:"

        return prompt


# ------------------------------
# Academic Calendar Context
# ------------------------------
class AcademicCalendarContext:
    """Provides awareness of UF academic calendar for relevant responses"""

    def __init__(self):
        self.calendar_data = ACADEMIC_CALENDAR
        logger.info("Initialized academic calendar context.")

    def get_current_context(self):
        """Get current academic calendar context with enhanced validation"""
        today = datetime.now()
        today_str = today.strftime("%Y-%m-%d")

        result = {
            "current_term": None,
            "current_event": None,
            "library_schedule_exceptions": None,
            "extended_hours": None,
        }

        try:
            # Determine current term
            for term, dates in self.calendar_data.get("terms", {}).items():
                if dates.get("start") <= today_str <= dates.get("end"):
                    result["current_term"] = term
                    break

            # Check if we're in any special event period
            for event, dates in self.calendar_data.get("events", {}).items():
                if dates.get("start") <= today_str <= dates.get("end"):
                    result["current_event"] = event
                    break

            # Check for schedule exceptions
            if today_str in self.calendar_data.get("library_schedule_exceptions", {}):
                result["library_schedule_exceptions"] = {
                    today_str: self.calendar_data["library_schedule_exceptions"][
                        today_str
                    ]
                }

            # Check if we're in extended hours period
            for period, info in self.calendar_data.get("extended_hours", {}).items():
                if info.get("start") <= today_str <= info.get("end"):
                    result["extended_hours"] = {
                        "period": period,
                        "libraries": info.get("libraries", {}),
                    }
                    break
        except Exception as e:
            logger.error(f"Error getting academic calendar context: {e}")

        return result


# ------------------------------
# LLaMA Model Configuration
# ------------------------------
class LlamaModelConfig:
    """Configuration for LLaMA model with optimized settings"""

    def __init__(self, model_path):
        self.model_path = model_path

        # Default settings for optimal performance
        self.settings = {
            "n_ctx": 4096,  # Context window size
            "n_batch": 512,  # Batch size for prompt processing
            "n_threads": 8,  # CPU thread count
            "n_gpu_layers": 35,  # Number of layers to offload to GPU if available
            "use_mlock": True,  # Use mlock to keep model in memory
        }

    def initialize_model(self):
        """Initialize the LLaMA model with optimal settings"""
        try:
            from llama_cpp import Llama

            # Check if GPU is available
            gpu_available = torch.cuda.is_available() if torch is not None else False
            # Check if MPS is available for Apple Silicon
            mps_available = (
                torch.backends.mps.is_available() if torch is not None else False
            )

            # Optimize for different hardware
            if gpu_available or mps_available:
                logger.info("GPU detected - enabling GPU acceleration")
                n_gpu_layers = self.settings["n_gpu_layers"]
            else:
                logger.info("No GPU detected - using CPU only")
                n_gpu_layers = 0

            # Initialize model with optimal settings
            model = Llama(
                model_path=self.model_path,
                n_ctx=self.settings["n_ctx"],
                n_batch=self.settings["n_batch"],
                n_threads=self.settings["n_threads"],
                n_gpu_layers=n_gpu_layers,
                use_mlock=self.settings["use_mlock"],
            )

            logger.info(f"Successfully loaded LLaMA model from {self.model_path}")
            return model

        except Exception as e:
            logger.error(f"Failed to initialize LLaMA model: {e}")
            return None


# ------------------------------
# Main Application
# ------------------------------
class EnhancedUFAssistant:
    """Enhanced UF Assistant integrating academic information, calendar awareness, and interconnected data"""

    def __init__(self, config_path="conf/config.yaml"):
        # Start timing for initialization
        init_start_time = time.time()

        # Define the path to the home directory
        global HOME_DIR
        self.HOME_DIR = HOME_DIR

        # Load configuration if available
        self.config = self._load_config(config_path)

        # Initialize embedding model
        self.embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
        logger.info("Initialized embedding model")

        # Initialize LLaMA model if path is provided
        llama_model_path = self.config.get("llama_model") if self.config else None
        self.llm = None

        if llama_model_path:
            llama_config = LlamaModelConfig(llama_model_path)
            self.llm = llama_config.initialize_model()

        # Load data using the provided loading functions
        logger.info("Loading data from CSV files...")
        self.campus_buildings = load_campus_buildings_data()
        self.libraries = load_libraries_data()
        self.dorms = load_hallinfo_data()

        # Initialize knowledge components
        self.academic_info = AcademicInfoRetrieval(self.embedding_model)
        self.clubs_info = CampusClubsRetrieval(self.embedding_model)
        self.query_analyzer = QueryAnalyzer()
        self.response_generator = ResponseGenerator(self.llm)
        self.academic_calendar = AcademicCalendarContext()
        self.conversation_state = ConversationState()

        # Cache for query results
        self.query_cache = LRUCache(capacity=100)

        # Validate data integrity
        self._validate_data()

        # Log initialization time
        init_time = time.time() - init_start_time
        logger.info(f"Initialization complete in {init_time:.2f} seconds")

    def _load_config(self, config_path):
        """Load configuration from YAML file"""
        try:
            return hydra.compose(config_name="config")
        except Exception as e:
            logger.warning(f"Could not load config from {config_path}: {e}")
            return None

    def _validate_data(self):
        """Validate loaded data and report any issues"""
        validation_issues = []

        # Check libraries
        if not self.libraries or len(self.libraries) == 0:
            validation_issues.append("No library data loaded")
        else:
            for idx, library in enumerate(self.libraries):
                if not library.get("Library Name"):
                    validation_issues.append(f"Library at index {idx} missing name")
                if not library.get("Hours") or not isinstance(
                    library.get("Hours"), dict
                ):
                    validation_issues.append(
                        f"Library '{library.get('Library Name', f'at index {idx}')}' has invalid hours format"
                    )

        # Check buildings
        if not self.campus_buildings or len(self.campus_buildings) == 0:
            validation_issues.append("No building data loaded")
        else:
            for idx, building in enumerate(self.campus_buildings):
                if not building.get("Building Name"):
                    validation_issues.append(f"Building at index {idx} missing name")

        # Check dorms
        if not self.dorms or len(self.dorms) == 0:
            validation_issues.append("No dormitory data loaded")
        else:
            for idx, dorm in enumerate(self.dorms):
                if not dorm.get("Building Name"):
                    validation_issues.append(f"Dormitory at index {idx} missing name")

        # Log validation issues
        if validation_issues:
            for issue in validation_issues:
                logger.warning(f"Data validation issue: {issue}")

        return len(validation_issues) == 0

    def _find_entity(self, query, entities, name_key, aliases_dict=None):
        """Generalized entity finder for libraries, buildings, dorms etc."""
        query_lower = query.lower()

        # Check direct match first
        for entity in entities:
            entity_name = entity.get(name_key, "").lower()
            if entity_name in query_lower:
                return entity

        # Check aliases if provided
        if aliases_dict:
            for entity in entities:
                entity_name = entity.get(name_key, "").lower()
                for alias_key, aliases in aliases_dict.items():
                    if alias_key == entity_name:
                        for alias in aliases:
                            if alias.lower() in query_lower:
                                return entity

        # Try course code pattern for courses
        if name_key == "Course Code":
            course_pattern = r"([A-Z]{3})\s*(\d{4}[A-Za-z]*)"
            matches = re.findall(course_pattern, query)
            if matches:
                course_code = f"{matches[0][0]} {matches[0][1]}"
                for entity in entities:
                    if course_code.lower() == entity.get(name_key, "").lower():
                        return entity

        # Try fuzzy matching
        best_match = None
        best_score = 0

        for entity in entities:
            entity_name = entity.get(name_key, "").lower()
            score = difflib.SequenceMatcher(None, query_lower, entity_name).ratio()

            if score > best_score and score > 0.6:
                best_score = score
                best_match = entity

        return best_match

    def _find_library(self, query):
        """Find the most relevant library for the query using the generalized finder"""
        return self._find_entity(query, self.libraries, "Library Name", LIBRARY_ALIASES)

    def _find_building(self, query):
        """Find the most relevant building for the query using the generalized finder"""
        return self._find_entity(
            query, self.campus_buildings, "Building Name", BUILDING_ALIASES
        )

    def _find_dorm(self, query):
        """Find the most relevant dorm for the query using the generalized finder"""
        return self._find_entity(query, self.dorms, "Building Name", DORM_ALIASES)

    def _is_uf_relevant_personal_query(self, query):
        """Determine if a personal query is relevant to UF and should be answered"""
        query_lower = query.lower()

        # UF-relevant keywords in context of personal questions
        uf_relevant_keywords = [
            "major",
            "program",
            "degree",
            "study",
            "class",
            "course",
            "career",
            "job",
            "college",
            "department",
            "admission",
            "application",
            "academic",
            "subject",
            "field",
            "interest",
            "graduate",
            "art",
            "science",
            "engineering",
            "business",
            "medicine",
            "law",
            "education",
            "minor",
        ]

        # UF-specific keywords
        uf_specific = ["uf", "university of florida", "gator", "gators"]

        # Check if the query contains UF-relevant academic keywords
        has_uf_relevant = any(
            keyword in query_lower for keyword in uf_relevant_keywords
        )

        # Check if there's a specific reference to UF
        has_uf_reference = any(term in query_lower for term in uf_specific)

        # Consider it UF-relevant if it has both relevant keywords and UF reference,
        # or if it's a query about majors/programs/courses (high confidence academic)
        high_confidence_academic = any(
            term in query_lower for term in ["major", "program", "course", "degree"]
        )

        return (has_uf_relevant and has_uf_reference) or high_confidence_academic

    def process_query(self, query):
        """Process a user query with enhanced entity detection and data interconnection"""
        # Start timer for performance monitoring
        start_time = time.time()

        try:
            # Check cache first
            cache_key = f"query:{query.lower()}"
            if cache_key in self.query_cache:
                return self.query_cache[cache_key]

            # Add to conversation state
            self.conversation_state.add_message("User", query)

            # Analyze query
            analysis = self.query_analyzer.analyze(query)

            # Update conversation intent tracking
            self.conversation_state.update_intent_tracking(
                analysis.get("intent", "generic")
            )

            # Get current academic calendar context
            academic_context = self.academic_calendar.get_current_context()

            # Initialize entity information variables
            library_info = None
            building_info = None
            dorm_info = None
            major_info = None
            club_info = None

            # New approach for handling personal queries
            if analysis.get("is_personal_query"):
                if self._is_uf_relevant_personal_query(query) and self.llm:
                    try:
                        # Create a prompt for LLaMA specifically for UF-relevant personal queries
                        prompt = f"""You are the UF Assistant, an AI designed to provide helpful information about the University of Florida.

    User Question: {query}

    This appears to be a personal question related to University of Florida academics or campus life. 
    Respond as if you are a helpful academic advisor at UF. Provide tailored recommendations based 
    on the user's stated interests, preferences, or needs. Include specific majors, programs, resources, 
    or departments at UF that would be appropriate. DO NOT say you don't have access to personal 
    information - instead, offer thoughtful advice based on the user's question."""

                        # Generate response with LLaMA
                        result = self.llm(
                            prompt=prompt,
                            max_tokens=500,
                            temperature=0.7,
                            stop=["User:", "Assistant:"],
                        )

                        # Extract response text
                        response = result["choices"][0]["text"].strip()

                        # Add to conversation state
                        self.conversation_state.add_message("Assistant", response)

                        # Cache the result
                        self.query_cache[cache_key] = response

                        # Log processing time
                        processing_time = time.time() - start_time
                        logger.info(
                            f"Processed personal query in {processing_time:.2f} seconds"
                        )

                        return response
                    except Exception as e:
                        logger.error(
                            f"Error generating LLaMA response for personal query: {e}"
                        )
                        # Fall through to standard processing if LLaMA fails

            # Rest of the existing process_query method continues as before...
            # If no specific intent detected, always use LLaMA for response
            if analysis.get("intent") == "generic":
                # Reset active contexts for generic queries
                self.conversation_state.reset_active_contexts()

                # Generate response with LLaMA if available
                if self.llm:
                    try:
                        # Create a prompt for LLaMA
                        prompt = "You are the UF Assistant, an AI designed to provide helpful information about the University of Florida.\n\n"
                        prompt += f"User Question: {query}\n\n"
                        prompt += "Please provide a helpful response to the user's question about UF.\n"
                        prompt += "Assistant:"

                        # Generate response with LLaMA
                        result = self.llm(
                            prompt=prompt,
                            max_tokens=500,
                            temperature=0.7,
                            stop=["User:", "Assistant:"],
                        )

                        # Extract response text
                        response = result["choices"][0]["text"].strip()

                        # Add to conversation state
                        self.conversation_state.add_message("Assistant", response)

                        # Cache the result
                        self.query_cache[cache_key] = response

                        # Log processing time
                        processing_time = time.time() - start_time
                        logger.info(f"Processed query in {processing_time:.2f} seconds")

                        return response
                    except Exception as e:
                        logger.error(f"Error generating LLaMA response: {e}")
                        # Fall through to standard processing if LLaMA fails

            # Try to identify entities in the query
            # If it's a followup question, try to use previous context
            if self.conversation_state.is_followup_question(query):
                if self.conversation_state.get_active_library():
                    library_info = self.conversation_state.get_active_library()
                if self.conversation_state.get_active_building():
                    building_info = self.conversation_state.get_active_building()
                if self.conversation_state.get_active_dorm():
                    dorm_info = self.conversation_state.get_active_dorm()
                if self.conversation_state.get_active_major():
                    major_info = self.conversation_state.get_active_major()
                if self.conversation_state.get_active_club():
                    club_info = self.conversation_state.get_active_club()
            else:
                # Not a followup question, reset active contexts
                self.conversation_state.reset_active_contexts()

            # Try to identify entities in the query with error handling
            try:
                # Library information
                if analysis.get("is_hours_query") or "library" in query.lower():
                    library_info = self._find_library(query)
                    if library_info:
                        # Make sure Hours is properly structured
                        if not library_info.get("Hours") or not isinstance(
                            library_info["Hours"], dict
                        ):
                            # Try to parse from the original Hours field
                            library_info["Hours"] = {}
                            days_of_week = [
                                "Monday",
                                "Tuesday",
                                "Wednesday",
                                "Thursday",
                                "Friday",
                                "Saturday",
                                "Sunday",
                            ]
                            for day in days_of_week:
                                library_info["Hours"][day] = "8:00am - 6:00pm"

                        self.conversation_state.set_active_library(library_info)
            except Exception as e:
                logger.error(f"Error finding library: {e}")

            try:
                # Building information
                if (
                    analysis.get("is_location_query")
                    or "building" in query.lower()
                    or "where is" in query.lower()
                ):
                    building_info = self._find_building(query)
                    if building_info:
                        self.conversation_state.set_active_building(building_info)
            except Exception as e:
                logger.error(f"Error finding building: {e}")

            try:
                # Dorm information
                if analysis.get("is_dorm_query"):
                    dorm_info = self._find_dorm(query)
                    if dorm_info:
                        self.conversation_state.set_active_dorm(dorm_info)
            except Exception as e:
                logger.error(f"Error finding dorm: {e}")

            try:
                # Major/Program information using enhanced search_major_info function
                if analysis.get("is_major_query") or self.query_analyzer.is_major_query(
                    query
                ):
                    major_response, found = search_major_info(query, self.HOME_DIR)
                    if found:
                        major_info = {"response": major_response, "query": query}
                        self.conversation_state.set_active_major(major_info)
                        self.query_cache[cache_key] = major_response
                        return major_response
            except Exception as e:
                logger.error(f"Error finding major with enhanced search: {e}")
                # Fall back to legacy method if enhanced search fails
                try:
                    if analysis.get("is_major_query"):
                        major_name = analysis.get("potential_major", query)
                        major_info = self.academic_info.get_info(major_name)
                        if major_info:
                            self.conversation_state.set_active_major(major_info)
                except Exception as e2:
                    logger.error(f"Error with fallback major search: {e2}")

            try:
                # Club information
                if analysis.get("is_club_query"):
                    club_info_text = self.clubs_info.get_club_info(query)
                    if club_info_text and "No club info found" not in club_info_text:
                        club_info = {
                            "Organization Name": query,
                            "Description": club_info_text,
                        }
                        self.conversation_state.set_active_club(club_info)
            except Exception as e:
                logger.error(f"Error finding club: {e}")

            # Generate response with fallback to default if needed
            try:
                response = self.response_generator.generate(
                    analysis,
                    library_info=library_info,
                    building_info=building_info,
                    dorm_info=dorm_info,
                    major_info=major_info,
                    club_info=club_info,
                    academic_calendar=academic_context,
                )
            except Exception as e:
                logger.error(f"Error generating response: {e}")
                response = f"I'm sorry, I couldn't find specific information about {query}. Can you try asking in a different way?"

            # Add to conversation state
            self.conversation_state.add_message("Assistant", response)

            # Cache the result
            self.query_cache[cache_key] = response

            # Log processing time
            processing_time = time.time() - start_time
            logger.info(f"Processed query in {processing_time:.2f} seconds")

            return response

        except Exception as e:
            logger.error(f"Critical error processing query: {e}")
            return "I apologize, but I encountered an error processing your request. Please try asking about a different topic."

    def reset_conversation(self):
        """Reset the conversation state"""
        self.conversation_state = ConversationState()
        return "Conversation has been reset."


# ------------------------------
# Main Application
# ------------------------------
if __name__ == "__main__":
    import argparse
    import sys

    # Create argument parser
    parser = argparse.ArgumentParser(description="UF Assistant")
    parser.add_argument("--query", type=str, help="Query to process")

    # Parse arguments
    args = parser.parse_args()

    # Initialize hydra
    hydra.initialize(config_path="conf")

    # Initialize the assistant
    assistant = EnhancedUFAssistant()

    if args.query:
        # Process the query provided via command line
        print(f"> {args.query}")
        response = assistant.process_query(args.query)
        # CRITICAL FIX: Make sure to print in a single line without buffering
        print(response, flush=True)
    else:
        # Interactive mode
        print(
            "UF Assistant is ready! Type your questions about UF (or 'exit' to quit).\n"
        )

        while True:
            # Get user input
            user_input = input("> ")

            # Check if user wants to exit
            if user_input.lower() in ["exit", "quit", "bye"]:
                print("Goodbye!")
                break

            # Process the query and get response
            response = assistant.process_query(user_input)

            # Print the response
            print(f"{response}\n")

if __name__ == "__main__":
    main()
