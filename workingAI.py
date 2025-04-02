#!/usr/bin/env python3
"""
Enhanced UF Assistant
A powerful assistant for answering questions about University of Florida
using LLaMA 3 with embedded knowledge and advanced retrieval techniques.
"""

import os
import sys
import re
import time
import json
import pickle
import logging
import argparse
import csv
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Union, Any, Set
from pathlib import Path
from functools import lru_cache
import random
from collections import Counter, defaultdict

# Advanced NLP and ML packages
try:
    from llama_cpp import Llama
except ImportError:
    print("llama_cpp not installed, some features will be limited")
    Llama = None

try:
    import torch
    from sentence_transformers import SentenceTransformer
    from sklearn.metrics.pairwise import cosine_similarity
except ImportError:
    print("ML libraries not installed, semantic search will be disabled")
    SentenceTransformer = None
    cosine_similarity = None

try:
    import spacy
    from spacy.language import Language
except ImportError:
    print("spaCy not installed, NLP capabilities will be limited")
    spacy = None
    Language = None

try:
    from fuzzywuzzy import fuzz
except ImportError:
    print("fuzzywuzzy not installed, fuzzy matching will be disabled")
    
    # Simple replacement for fuzz functions if not available
    class FuzzMock:
        @staticmethod
        def ratio(a, b):
            return 50 if a.lower() in b.lower() or b.lower() in a.lower() else 0
            
        @staticmethod
        def partial_ratio(a, b):
            return 50 if a.lower() in b.lower() or b.lower() in a.lower() else 0
            
        @staticmethod
        def token_set_ratio(a, b):
            return 50 if a.lower() in b.lower() or b.lower() in a.lower() else 0
            
    fuzz = FuzzMock()

try:
    import hnswlib
except ImportError:
    print("hnswlib not installed, advanced vector search will be disabled")
    hnswlib = None

try:
    import diskcache as dc
except ImportError:
    print("diskcache not installed, persistent caching will be disabled")
    dc = None

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(), logging.FileHandler('uf_assistant.log')]
)
logger = logging.getLogger('Enhanced_UF_Assistant')

# =============================================================================
# EMBEDDED LIBRARY DATA
# =============================================================================

# Comprehensive library information embedded directly in the code
LIBRARY_DATA = [
    {
        "Library Name": "Library West",
        "Location": "1545 W University Ave, Gainesville, FL 32603",
        "Capacity": "1564",
        "Hours": {
            "Monday": "7:00am - 2:00am",
            "Tuesday": "7:00am - 2:00am",
            "Wednesday": "7:00am - 2:00am",
            "Thursday": "7:00am - 2:00am",
            "Friday": "7:00am - 10:00pm",
            "Saturday": "10:00am - 10:00pm",
            "Sunday": "7:00am - 2:00am"
        },
        "Special Notes": "Building access after 10pm limited to users with active UF ID or Santa Fe College ID",
        "URL": "https://uflib.ufl.edu/library-west/",
        "Phone": "(352) 273-2845",
        "Email": "libwest@uflib.ufl.edu",
        "Tags": "humanities, business, social sciences",
        "Resources": [
            "Research assistance",
            "Computers and laptops for checkout",
            "Printing and scanning",
            "Group study rooms",
            "Quiet study areas",
            "Graduate student study space",
            "Writing assistance services",
            "Course reserves",
            "Citation management tools",
            "Business databases"
        ],
        "Study Spaces": [
            "Silent study areas (4th floor)",
            "Group study rooms (reservation required)",
            "Individual study carrels",
            "Graduate student study space (3rd floor)",
            "Comfortable seating areas",
            "Collaboration spaces with large screens"
        ],
        "Collections": [
            "Humanities literature",
            "Business resources",
            "Social sciences materials",
            "Government documents",
            "Journals and periodicals",
            "Digital collections",
            "Course reserves"
        ],
        "Technology": [
            "Computer workstations",
            "Printing stations",
            "Scanners",
            "Charging stations",
            "Multi-media software",
            "Data analysis tools",
            "Laptops for checkout"
        ],
        "Services": [
            "Research consultations",
            "Course reserves",
            "Interlibrary loan",
            "Writing assistance",
            "Citation help",
            "Subject specialist librarians",
            "Information literacy instruction",
            "Circulation desk"
        ],
        "Aliases": [
            "lib west",
            "west",
            "libwest",
            "library w",
            "west library",
            "lw",
            "library-west"
        ]
    },
    {
        "Library Name": "Marston Science Library",
        "Location": "444 Newell Dr, Gainesville, FL 32611",
        "Capacity": "2208",
        "Hours": {
            "Monday": "7:00am - 2:00am",
            "Tuesday": "7:00am - 2:00am",
            "Wednesday": "7:00am - 2:00am",
            "Thursday": "7:00am - 2:00am",
            "Friday": "7:00am - 10:00pm",
            "Saturday": "10:00am - 10:00pm",
            "Sunday": "7:00am - 2:00am"
        },
        "Special Notes": "Includes Makerspace (capacity: 15); Research assistance; Computers; Printing; Group study rooms; Quiet study areas",
        "URL": "https://uflib.ufl.edu/marston/",
        "Phone": "(352) 273-2845",
        "Email": "marston@uflib.ufl.edu",
        "Tags": "science, engineering, technology, math",
        "Resources": [
            "STEM research materials",
            "Makerspace with 3D printing",
            "Research assistance",
            "Computers and software",
            "Printing and scanning",
            "Group study rooms",
            "Quiet study areas",
            "Technical software",
            "Engineering standards",
            "Data visualization resources",
            "STEM databases",
            "Course reserves",
            "Citation management tools"
        ],
        "Study Spaces": [
            "Quiet study areas (upper floors)",
            "Group study rooms (reservation required)",
            "Individual study carrels",
            "Makerspace",
            "Collaboration pods",
            "Computer labs"
        ],
        "Collections": [
            "Science journals and books",
            "Engineering standards",
            "Technical reports",
            "GIS data",
            "STEM research databases",
            "Course reserves"
        ],
        "Technology": [
            "Computer workstations",
            "Technical software (MATLAB, AutoCAD, SolidWorks)",
            "3D printers",
            "Laser cutters",
            "Printing stations",
            "Scanners",
            "Charging stations",
            "VR equipment",
            "Specialized technology for engineering and sciences"
        ],
        "Services": [
            "STEM research consultations",
            "Course reserves",
            "Interlibrary loan",
            "Data management assistance",
            "Technical software help",
            "3D printing services",
            "Science and engineering librarians",
            "GIS support",
            "Circulation desk"
        ],
        "Aliases": [
            "marston",
            "msl",
            "science library",
            "marston library",
            "science",
            "marston-science",
            "marston's"
        ]
    },
    {
        "Library Name": "Smathers Library",
        "Location": "Plaza of the Americas, Gainesville, FL 32611",
        "Capacity": "Unknown",
        "Hours": {
            "Monday": "7:00am - 2:00am",
            "Tuesday": "7:00am - 2:00am",
            "Wednesday": "7:00am - 2:00am",
            "Thursday": "7:00am - 2:00am",
            "Friday": "7:00am - 10:00pm",
            "Saturday": "10:00am - 10:00pm",
            "Sunday": "7:00am - 2:00am"
        },
        "Special Notes": "Oldest library on campus; Special collections; Research assistance; Computers; Printing; Group study rooms",
        "URL": "https://uflib.ufl.edu/smathers/",
        "Phone": "(352) 273-2845",
        "Email": "smathers@uflib.ufl.edu",
        "Tags": "archives, rare books, historical, manuscripts, special collections",
        "Resources": [
            "Florida history collections",
            "Latin American collections",
            "Rare books",
            "Manuscripts",
            "Archives",
            "Special collections reading rooms",
            "Research assistance",
            "Computers",
            "Printing and scanning",
            "Study areas",
            "Historical collections",
            "Primary sources",
            "P.K. Yonge Library of Florida History"
        ],
        "Study Spaces": [
            "Special collections reading rooms",
            "Grand Reading Room",
            "Individual study carrels",
            "Quiet study areas",
            "Historic study spaces"
        ],
        "Collections": [
            "P.K. Yonge Library of Florida History",
            "Latin American Collection",
            "Judaica Collection",
            "University Archives",
            "Architecture Archives",
            "Rare Books Collection",
            "Historical manuscripts",
            "Political papers",
            "Maps and aerial photographs"
        ],
        "Technology": [
            "Computer workstations",
            "Digital scanners for archival materials",
            "Microfilm readers",
            "Printing stations",
            "Digitization equipment",
            "Digital humanities resources"
        ],
        "Services": [
            "Special collections research help",
            "Archival research consultation",
            "Preservation services",
            "Digitization services",
            "Research consultation for rare materials",
            "Exhibitions of rare materials",
            "Public programming",
            "Circulation desk for general collections"
        ],
        "Aliases": [
            "smathers",
            "east",
            "library east",
            "special collections",
            "smathers-library",
            "smather"
        ]
    },
    {
        "Library Name": "Health Science Center Library",
        "Location": "1600 SW Archer Rd, Gainesville, FL 32610",
        "Capacity": "761",
        "Hours": {
            "Monday": "7:00am - 2:00am",
            "Tuesday": "7:00am - 2:00am",
            "Wednesday": "7:00am - 2:00am",
            "Thursday": "7:00am - 2:00am",
            "Friday": "7:00am - 10:00pm",
            "Saturday": "10:00am - 10:00pm",
            "Sunday": "7:00am - 2:00am"
        },
        "Special Notes": "Medical collections; Study spaces; Computers; Printing; Research assistance; Group study rooms",
        "URL": "https://uflib.ufl.edu/hscl/",
        "Phone": "(352) 273-8408",
        "Email": "hsc-library@uflib.ufl.edu",
        "Tags": "medicine, health, nursing, pharmacy, dental, veterinary",
        "Resources": [
            "Medical and health journals",
            "Clinical resources",
            "Anatomy models",
            "Research databases",
            "Evidence-based medicine tools",
            "Research assistance",
            "Computers with specialized software",
            "Printing and scanning",
            "Group study rooms",
            "Individual study spaces",
            "Course reserves",
            "Citation management tools",
            "Systematic review services"
        ],
        "Study Spaces": [
            "Collaboration rooms",
            "Individual study carrels",
            "Group study rooms (reservation required)",
            "Quiet study areas",
            "Computer labs",
            "Large tables for group study"
        ],
        "Collections": [
            "Medical journals",
            "Health sciences books",
            "Clinical resources",
            "Nursing resources",
            "Pharmacy literature",
            "Dental resources",
            "Veterinary medicine materials",
            "Public health resources",
            "Biomedical research publications",
            "Electronic medical databases",
            "Course reserves"
        ],
        "Technology": [
            "Computer workstations",
            "Clinical software applications",
            "Anatomical visualization tools",
            "Printing stations",
            "Scanners",
            "Charging stations",
            "Medical software",
            "Statistical analysis tools"
        ],
        "Services": [
            "Clinical information services",
            "Evidence-based medicine assistance",
            "Systematic review support",
            "Research consultations",
            "Course reserves",
            "Interlibrary loan",
            "Citation management help",
            "Health sciences librarians",
            "Bibliographic instruction",
            "Circulation desk"
        ],
        "Aliases": [
            "hsc",
            "health science",
            "hscl",
            "medical library",
            "health",
            "medical"
        ]
    },
    {
        "Library Name": "Architecture & Fine Arts Library",
        "Location": "1480 Inner Rd, Gainesville, FL 32611",
        "Capacity": "Unknown",
        "Hours": {
            "Monday": "7:00am - 2:00am",
            "Tuesday": "7:00am - 2:00am",
            "Wednesday": "7:00am - 2:00am",
            "Thursday": "7:00am - 2:00am",
            "Friday": "7:00am - 10:00pm",
            "Saturday": "10:00am - 10:00pm",
            "Sunday": "7:00am - 2:00am"
        },
        "Special Notes": "Arts collections; Study spaces; Computers; Printing; Research assistance; Group study rooms",
        "URL": "https://uflib.ufl.edu/afa/",
        "Phone": "(352) 273-2825",
        "Email": "afa@uflib.ufl.edu",
        "Tags": "art, architecture, design, visual arts, urban planning",
        "Resources": [
            "Architecture books and journals",
            "Fine arts materials",
            "Design resources",
            "Visual reference materials",
            "Research assistance",
            "Design software",
            "Printing and scanning",
            "Material samples library",
            "Course reserves",
            "Visual resources collection",
            "Urban planning resources",
            "Interior design materials"
        ],
        "Study Spaces": [
            "Individual study carrels",
            "Large tables for design work",
            "Group study areas",
            "Computer lab",
            "Quiet study spaces",
            "Material sample review areas"
        ],
        "Collections": [
            "Architecture books",
            "Design periodicals",
            "Arts literature",
            "Urban planning resources",
            "Interior design materials",
            "Landscape architecture resources",
            "Building technology resources",
            "Visual arts books",
            "Art history publications",
            "Design standards and guides",
            "Course reserves"
        ],
        "Technology": [
            "Computer workstations with design software",
            "Large format printers",
            "Scanning stations",
            "Design software (Adobe Creative Suite, AutoCAD, Revit)",
            "Digital media tools",
            "Visual resource databases"
        ],
        "Services": [
            "Design research consultations",
            "Visual resources help",
            "Course reserves",
            "Interlibrary loan",
            "Material sample access",
            "Design software assistance",
            "Architecture & arts librarians",
            "Circulation desk"
        ],
        "Aliases": [
            "afa",
            "architecture library",
            "fine arts",
            "arts library",
            "architecture",
            "arts"
        ]
    },
    {
        "Library Name": "Education Library",
        "Location": "Norman Hall 2nd Floor, Gainesville, FL 32611",
        "Capacity": "Unknown",
        "Hours": {
            "Monday": "7:00am - 2:00am",
            "Tuesday": "7:00am - 2:00am",
            "Wednesday": "7:00am - 2:00am",
            "Thursday": "7:00am - 2:00am",
            "Friday": "7:00am - 10:00pm",
            "Saturday": "10:00am - 10:00pm",
            "Sunday": "7:00am - 2:00am"
        },
        "Special Notes": "Education collections; Study spaces; Computers; Printing; Research assistance; Group study rooms",
        "URL": "https://uflib.ufl.edu/education/",
        "Phone": "(352) 273-2780",
        "Email": "edulib@uflib.ufl.edu",
        "Tags": "education, teaching, learning, curriculum, pedagogy",
        "Resources": [
            "Education books and journals",
            "Curriculum materials",
            "Children's literature collection",
            "Teaching resources",
            "Research assistance",
            "Computers with educational software",
            "Printing and scanning",
            "Group study rooms",
            "Course reserves",
            "Citation management tools",
            "Educational databases"
        ],
        "Study Spaces": [
            "Individual study carrels",
            "Group study rooms (reservation required)",
            "Quiet study areas",
            "Computer lab",
            "Curriculum review spaces",
            "Teaching resource review areas"
        ],
        "Collections": [
            "Education journals",
            "Teaching resources",
            "Curriculum materials",
            "Children's and young adult literature",
            "Educational psychology resources",
            "Special education materials",
            "Educational technology resources",
            "Educational policy publications",
            "Course reserves",
            "Educational assessment resources"
        ],
        "Technology": [
            "Computer workstations",
            "Educational software",
            "Printing stations",
            "Scanners",
            "Curriculum technology tools",
            "Educational media equipment"
        ],
        "Services": [
            "Education research consultations",
            "Curriculum materials access",
            "Course reserves",
            "Interlibrary loan",
            "Instructional material evaluation",
            "Children's literature specialists",
            "Education librarians",
            "Circulation desk"
        ],
        "Aliases": [
            "education",
            "norman hall",
            "education-library",
            "ed library"
        ]
    },
    {
        "Library Name": "Legal Information Center",
        "Location": "Levin College of Law, Gainesville, FL 32611",
        "Capacity": "Unknown",
        "Hours": {
            "Monday": "7:00am - 2:00am",
            "Tuesday": "7:00am - 2:00am",
            "Wednesday": "7:00am - 2:00am",
            "Thursday": "7:00am - 2:00am",
            "Friday": "7:00am - 10:00pm",
            "Saturday": "10:00am - 10:00pm",
            "Sunday": "7:00am - 2:00am"
        },
        "Special Notes": "Legal collections; Study spaces; Computers; Printing; Research assistance; Group study rooms",
        "URL": "https://uflib.ufl.edu/lic/",
        "Phone": "(352) 273-0722",
        "Email": "lic@law.ufl.edu",
        "Tags": "law, legal studies, government, policy",
        "Resources": [
            "Legal books and journals",
            "Law reports",
            "Statutes and regulations",
            "Legal databases (Westlaw, LexisNexis)",
            "Research assistance",
            "Computers with legal software",
            "Printing and scanning",
            "Group study rooms",
            "Individual study spaces",
            "Course reserves",
            "Citation management tools"
        ],
        "Study Spaces": [
            "Individual study carrels",
            "Group study rooms (reservation required)",
            "Quiet study areas",
            "Computer lab",
            "Legal research areas",
            "Mock courtroom"
        ],
        "Collections": [
            "Legal journals",
            "Law reports",
            "State and federal statutes",
            "Case law resources",
            "International law materials",
            "Legal treatises",
            "Government documents",
            "Florida law resources",
            "Course reserves",
            "Legal research guides"
        ],
        "Technology": [
            "Computer workstations",
            "Legal research databases",
            "Printing stations",
            "Scanners",
            "Legal software",
            "Legal citation tools"
        ],
        "Services": [
            "Legal research consultations",
            "Course reserves",
            "Interlibrary loan",
            "Citation management help",
            "Law librarians",
            "Legal database training",
            "Legal research instruction",
            "Circulation desk"
        ],
        "Aliases": [
            "law library",
            "law",
            "legal",
            "levin",
            "law-library",
            "legal-information"
        ]
    },
    {
        "Library Name": "Special & Area Studies Collections",
        "Location": "Smathers Library 2nd Floor, Gainesville, FL 32611",
        "Capacity": "Unknown",
        "Hours": {
            "Monday": "9:00am - 5:00pm",
            "Tuesday": "9:00am - 5:00pm",
            "Wednesday": "9:00am - 5:00pm",
            "Thursday": "9:00am - 5:00pm",
            "Friday": "9:00am - 5:00pm",
            "Saturday": "Closed",
            "Sunday": "Closed"
        },
        "Special Notes": "Located in Grand Reading Room; Rare materials; Archival collections; Historical documents",
        "URL": "https://uflib.ufl.edu/spec/",
        "Phone": "(352) 273-2845",
        "Email": "specialcollections@uflib.ufl.edu",
        "Tags": "special collections, area studies, archives",
        "Resources": [
            "Rare books",
            "Manuscripts",
            "University archives",
            "Florida history collections",
            "Political papers",
            "Archival materials",
            "Research assistance",
            "Specialized reading rooms",
            "Reference services",
            "Digital collections"
        ],
        "Study Spaces": [
            "Special collections reading room",
            "Supervised research areas",
            "Grand Reading Room",
            "Specialized research spaces"
        ],
        "Collections": [
            "Rare books",
            "University Archives",
            "Architecture Archives",
            "P.K. Yonge Library of Florida History",
            "Manuscripts Collection",
            "Political Papers",
            "Judaica Collection",
            "Baldwin Library of Historical Children's Literature",
            "Latin American and Caribbean Collection",
            "Map and Imagery Library"
        ],
        "Technology": [
            "Digital scanners for archival materials",
            "Microfilm readers",
            "Digital cameras for document photography",
            "Digitization equipment",
            "Digital humanities tools"
        ],
        "Services": [
            "Special collections consultations",
            "Archival research assistance",
            "Document delivery services for rare materials",
            "Digitization services",
            "Exhibition preparation",
            "Preservation services",
            "Research guidance for primary sources",
            "Reference services"
        ],
        "Aliases": [
            "special",
            "area studies",
            "area-studies",
            "special-collections"
        ]
    }
]

# =============================================================================
# CAMPUS BUILDINGS DATA
# =============================================================================

CAMPUS_BUILDINGS_DATA = [
    {
        "Building Number": "105",
        "Building Name": "105 Classroom Building",
        "Abbreviation": "CLB",
        "Address": "105 Fletcher Drive, Gainesville, FL 32611",
        "Description": "Classrooms and academic facilities."
    },
    {
        "Building Number": "",
        "Building Name": "Academic Research Building",
        "Abbreviation": "ARB",
        "Address": "1230 Inner Road, Gainesville, FL 32611",
        "Description": "Research labs and interdisciplinary studies."
    },
    {
        "Building Number": "",
        "Building Name": "Alfred A. McKethan Stadium",
        "Abbreviation": "CBP",
        "Address": "2500 SW 2nd Ave, Gainesville, FL 32607",
        "Description": "Former baseball stadium, now Condron Ballpark."
    },
    {
        "Building Number": "",
        "Building Name": "Anderson Hall",
        "Abbreviation": "AND",
        "Address": "100 Fletcher Dr, Gainesville, FL 32611",
        "Description": "Home to the College of Liberal Arts and Sciences."
    },
    {
        "Building Number": "",
        "Building Name": "Animal Sciences Building",
        "Abbreviation": "ANS",
        "Address": "459 Shealy Drive, Gainesville, FL 32611",
        "Description": "Houses the Department of Animal Sciences."
    }
    # Additional buildings would be added here
]

# =============================================================================
# CAMPUS AMENITIES
# =============================================================================

# Information about non-library amenities on campus
CAMPUS_AMENITIES = {
    "coffee_shops": [
        {
            "name": "Starbucks at Library West",
            "location": "First floor of Library West",
            "hours": {
                "Monday": "7:30am - 8:00pm",
                "Tuesday": "7:30am - 8:00pm",
                "Wednesday": "7:30am - 8:00pm",
                "Thursday": "7:30am - 8:00pm",
                "Friday": "7:30am - 5:00pm",
                "Saturday": "Closed",
                "Sunday": "1:00pm - 8:00pm"
            },
            "description": "Full-service Starbucks offering coffee, tea, and light snacks",
            "nearest_library": "Library West"
        },
        {
            "name": "Starbucks at Newell Hall",
            "location": "Newell Hall, ground floor",
            "hours": {
                "Monday": "7:30am - 5:00pm",
                "Tuesday": "7:30am - 5:00pm",
                "Wednesday": "7:30am - 5:00pm",
                "Thursday": "7:30am - 5:00pm",
                "Friday": "7:30am - 3:00pm",
                "Saturday": "Closed",
                "Sunday": "Closed"
            },
            "description": "Starbucks location near Marston Science Library",
            "nearest_library": "Marston Science Library"
        },
        {
            "name": "Starbucks at Reitz Union",
            "location": "Ground floor of the Reitz Union",
            "hours": {
                "Monday": "7:00am - 9:00pm",
                "Tuesday": "7:00am - 9:00pm",
                "Wednesday": "7:00am - 9:00pm",
                "Thursday": "7:00am - 9:00pm",
                "Friday": "7:00am - 8:00pm",
                "Saturday": "9:00am - 6:00pm",
                "Sunday": "10:00am - 6:00pm"
            },
            "description": "Starbucks location in the student union",
            "nearest_library": "Marston Science Library"
        }
    ],
    "dining_locations": [
        {
            "name": "Panda Express",
            "location": "Reitz Union Food Court",
            "hours": {
                "Monday": "10:30am - 8:00pm",
                "Tuesday": "10:30am - 8:00pm",
                "Wednesday": "10:30am - 8:00pm",
                "Thursday": "10:30am - 8:00pm",
                "Friday": "10:30am - 8:00pm",
                "Saturday": "11:00am - 6:00pm",
                "Sunday": "11:00am - 6:00pm"
            },
            "description": "Chinese fast food restaurant",
            "nearest_library": "Marston Science Library"
        },
        {
            "name": "Subway",
            "location": "Reitz Union Food Court",
            "hours": {
                "Monday": "9:00am - 8:00pm",
                "Tuesday": "9:00am - 8:00pm",
                "Wednesday": "9:00am - 8:00pm",
                "Thursday": "9:00am - 8:00pm",
                "Friday": "9:00am - 7:00pm",
                "Saturday": "11:00am - 6:00pm",
                "Sunday": "11:00am - 6:00pm"
            },
            "description": "Sandwich shop",
            "nearest_library": "Marston Science Library"
        },
        {
            "name": "Chick-fil-A",
            "location": "Hub Food Court",
            "hours": {
                "Monday": "7:30am - 8:00pm",
                "Tuesday": "7:30am - 8:00pm",
                "Wednesday": "7:30am - 8:00pm",
                "Thursday": "7:30am - 8:00pm",
                "Friday": "7:30am - 5:00pm",
                "Saturday": "Closed",
                "Sunday": "Closed"
            },
            "description": "Fast food chicken restaurant",
            "nearest_library": "Library West"
        },
        {
            "name": "Krishna Lunch",
            "location": "Plaza of the Americas",
            "hours": {
                "Monday": "11:00am - 1:30pm",
                "Tuesday": "11:00am - 1:30pm",
                "Wednesday": "11:00am - 1:30pm",
                "Thursday": "11:00am - 1:30pm",
                "Friday": "11:00am - 1:30pm",
                "Saturday": "Closed",
                "Sunday": "Closed"
            },
            "description": "Vegetarian lunch service on the Plaza of the Americas",
            "nearest_library": "Smathers Library"
        }
    ],
    "study_spots": [
        {
            "name": "Newell Hall",
            "location": "Newell Hall, near Marston Science Library",
            "hours": {
                "Monday": "24 hours",
                "Tuesday": "24 hours",
                "Wednesday": "24 hours",
                "Thursday": "24 hours",
                "Friday": "24 hours",
                "Saturday": "24 hours",
                "Sunday": "24 hours"
            },
            "description": "24/7 study space with various seating options and a Starbucks",
            "nearest_library": "Marston Science Library"
        }
    ]
}

# =============================================================================
# SUBJECT MAPPINGS
# =============================================================================

# Comprehensive subject to library mappings
SUBJECT_MAPPINGS = {
    # STEM subjects → Marston
    "science": "Marston Science Library",
    "biology": "Marston Science Library",
    "chemistry": "Marston Science Library",
    "physics": "Marston Science Library",
    "engineering": "Marston Science Library",
    "computer": "Marston Science Library",
    "programming": "Marston Science Library",
    "math": "Marston Science Library",
    "mathematics": "Marston Science Library",
    "statistics": "Marston Science Library",
    "data science": "Marston Science Library",
    "technology": "Marston Science Library",
    "astronomy": "Marston Science Library",
    "geology": "Marston Science Library",
    "environmental": "Marston Science Library",
    "computing": "Marston Science Library",
    "stem": "Marston Science Library",
    "robotics": "Marston Science Library",
    "mechanical": "Marston Science Library",
    "electrical": "Marston Science Library",
    "civil": "Marston Science Library",
    "chemical": "Marston Science Library",
    "aerospace": "Marston Science Library",
    "coding": "Marston Science Library",
    "algorithm": "Marston Science Library",
    "machine learning": "Marston Science Library",
    "artificial intelligence": "Marston Science Library",
    "calculus": "Marston Science Library",
    "algebra": "Marston Science Library",
    "geometry": "Marston Science Library",
    
    # Humanities/Business → Library West
    "humanities": "Library West",
    "literature": "Library West",
    "philosophy": "Library West",
    "religion": "Library West",
    "business": "Library West",
    "economics": "Library West",
    "finance": "Library West",
    "management": "Library West",
    "accounting": "Library West",
    "marketing": "Library West",
    "sociology": "Library West",
    "psychology": "Library West",
    "anthropology": "Library West",
    "political": "Library West",
    "international": "Library West",
    "social sciences": "Library West",
    "communication": "Library West",
    "journalism": "Library West",
    "english": "Library West",
    "linguistics": "Library West",
    "writing": "Library West",
    "poetry": "Library West",
    "novel": "Library West",
    "fiction": "Library West",
    "nonfiction": "Library West",
    "history": "Library West",
    "geography": "Library West",
    "ethics": "Library West",
    "languages": "Library West",
    "entrepreneurship": "Library West",
    "human resources": "Library West",
    "operations": "Library West",
    "supply chain": "Library West",
    
    # Florida History/Special Collections → Smathers
    "florida history": "Smathers Library",
    "florida": "Smathers Library",
    "archives": "Smathers Library",
    "rare books": "Smathers Library",
    "manuscripts": "Smathers Library",
    "special collections": "Smathers Library",
    "historical": "Smathers Library",
    "archival": "Smathers Library",
    "preservation": "Smathers Library",
    "primary sources": "Smathers Library",
    "latin american": "Smathers Library",
    "caribbean": "Smathers Library",
    "judaica": "Smathers Library",
    "maps": "Smathers Library",
    "aerial photographs": "Smathers Library",
    "university archives": "Smathers Library",
    "political papers": "Smathers Library",
    "children's literature": "Smathers Library",
    "baldwin": "Smathers Library",
    
    # Medical/Health → Health Science Center Library
    "medicine": "Health Science Center Library",
    "medical": "Health Science Center Library",
    "health": "Health Science Center Library",
    "nursing": "Health Science Center Library",
    "pharmacy": "Health Science Center Library",
    "dental": "Health Science Center Library",
    "dentistry": "Health Science Center Library",
    "veterinary": "Health Science Center Library",
    "clinical": "Health Science Center Library",
    "anatomy": "Health Science Center Library",
    "physiology": "Health Science Center Library",
    "public health": "Health Science Center Library",
    "biomedical": "Health Science Center Library",
    "healthcare": "Health Science Center Library",
    "disease": "Health Science Center Library",
    "patient care": "Health Science Center Library",
    "diagnosis": "Health Science Center Library",
    "treatment": "Health Science Center Library",
    "therapy": "Health Science Center Library",
    "surgery": "Health Science Center Library",
    "epidemiology": "Health Science Center Library",
    "nutrition": "Health Science Center Library",
    "psychiatry": "Health Science Center Library",
    "radiology": "Health Science Center Library",
    "pathology": "Health Science Center Library",
    
    # Art/Architecture → Architecture & Fine Arts Library
    "art": "Architecture & Fine Arts Library",
    "architecture": "Architecture & Fine Arts Library",
    "design": "Architecture & Fine Arts Library",
    "urban planning": "Architecture & Fine Arts Library",
    "music": "Architecture & Fine Arts Library",
    "painting": "Architecture & Fine Arts Library",
    "sculpture": "Architecture & Fine Arts Library",
    "theater": "Architecture & Fine Arts Library",
    "dance": "Architecture & Fine Arts Library",
    "photography": "Architecture & Fine Arts Library",
    "drawing": "Architecture & Fine Arts Library",
    "digital arts": "Architecture & Fine Arts Library",
    "graphic design": "Architecture & Fine Arts Library",
    "interior design": "Architecture & Fine Arts Library",
    "landscape": "Architecture & Fine Arts Library",
    "building": "Architecture & Fine Arts Library",
    "construction": "Architecture & Fine Arts Library",
    "urban design": "Architecture & Fine Arts Library",
    "art history": "Architecture & Fine Arts Library",
    "ceramics": "Architecture & Fine Arts Library",
    "printmaking": "Architecture & Fine Arts Library",
    "film": "Architecture & Fine Arts Library",
    "visual arts": "Architecture & Fine Arts Library",
    "museum": "Architecture & Fine Arts Library",
    "exhibition": "Architecture & Fine Arts Library",
    
    # Education → Education Library
    "education": "Education Library",
    "teaching": "Education Library",
    "learning": "Education Library",
    "curriculum": "Education Library",
    "pedagogy": "Education Library",
    "educational": "Education Library",
    "school": "Education Library",
    "classroom": "Education Library",
    "instruction": "Education Library",
    "k-12": "Education Library",
    "elementary": "Education Library",
    "secondary": "Education Library",
    "child development": "Education Library",
    "literacy": "Education Library",
    "educational psychology": "Education Library",
    "special education": "Education Library",
    "counseling": "Education Library",
    "educational technology": "Education Library",
    "educational leadership": "Education Library",
    "educational policy": "Education Library",
    "teacher": "Education Library",
    "student": "Education Library",
    "lesson plan": "Education Library",
    "assessment": "Education Library",
    "evaluation": "Education Library",
    
    # Legal → Legal Information Center
    "law": "Legal Information Center",
    "legal": "Legal Information Center",
    "legislation": "Legal Information Center",
    "justice": "Legal Information Center",
    "court": "Legal Information Center",
    "criminal": "Legal Information Center",
    "constitutional": "Legal Information Center",
    "judicial": "Legal Information Center",
    "attorney": "Legal Information Center",
    "statutes": "Legal Information Center",
    "regulations": "Legal Information Center",
    "case law": "Legal Information Center",
    "civil law": "Legal Information Center",
    "international law": "Legal Information Center",
    "business law": "Legal Information Center",
    "tort": "Legal Information Center",
    "contract": "Legal Information Center",
    "property law": "Legal Information Center",
    "intellectual property": "Legal Information Center",
    "patent": "Legal Information Center",
    "trademark": "Legal Information Center",
    "copyright": "Legal Information Center",
    "legal research": "Legal Information Center",
    "legal writing": "Legal Information Center",
    "tax law": "Legal Information Center"
}

# =============================================================================
# ACADEMIC CALENDAR DATA
# =============================================================================

ACADEMIC_CALENDAR = {
    'terms': {
        'Spring 2025': {'start': '2025-01-06', 'end': '2025-05-02'},
        'Summer A 2025': {'start': '2025-05-12', 'end': '2025-06-20'},
        'Summer B 2025': {'start': '2025-06-30', 'end': '2025-08-08'},
        'Fall 2025': {'start': '2025-08-25', 'end': '2025-12-12'}
    },
    'events': {
        'Spring 2025 Final Exams': {'start': '2025-04-26', 'end': '2025-05-02'},
        'Spring Break 2025': {'start': '2025-03-08', 'end': '2025-03-15'},
        'Summer Break 2025': {'start': '2025-05-03', 'end': '2025-05-11'},
        'Fall 2025 Final Exams': {'start': '2025-12-06', 'end': '2025-12-12'}
    },
    'library_schedule_exceptions': {
        '2025-01-01': {'all': 'CLOSED - New Year\'s Day'},
        '2025-01-20': {'all': 'CLOSED - Martin Luther King Jr. Day'},
        '2025-03-08': {'all': 'CLOSED - Spring Break Begins'},
        '2025-05-03': {'all': 'CLOSED - Semester Break'},
        '2025-05-26': {'all': 'CLOSED - Memorial Day'},
        '2025-07-04': {'all': 'CLOSED - Independence Day'},
        '2025-09-01': {'all': 'CLOSED - Labor Day'},
        '2025-11-11': {'all': 'CLOSED - Veterans Day'},
        '2025-11-27': {'all': 'CLOSED - Thanksgiving Day'},
        '2025-11-28': {'all': 'CLOSED - Day after Thanksgiving'},
        '2025-12-13': {'all': 'CLOSED - Semester Break'},
        '2025-12-24': {'all': 'CLOSED - Christmas Eve'},
        '2025-12-25': {'all': 'CLOSED - Christmas Day'},
        '2025-12-31': {'all': 'CLOSED - New Year\'s Eve'}
    },
    'extended_hours': {
        'Spring 2025 Finals': {
            'start': '2025-04-19',
            'end': '2025-05-02',
            'libraries': {
                'Library West': '24 hours',
                'Marston Science Library': '24 hours'
            }
        },
        'Fall 2025 Finals': {
            'start': '2025-11-29',
            'end': '2025-12-12',
            'libraries': {
                'Library West': '24 hours',
                'Marston Science Library': '24 hours'
            }
        }
    }
}

# =============================================================================
# UTILITY CLASSES
# =============================================================================

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

class ConversationState:
    """Tracks the state of a conversation for context management"""
    
    def __init__(self, max_history=10):
        self.max_history = max_history
        self.turns = []
        self.current_library = None
        self.current_building = None
        self.current_topic = None
        self.awaiting_followup = False
        self.last_intent = None
        self.mentioned_libraries = set()
        self.mentioned_buildings = set()
        self.discussed_topics = set()
        self.query_type = None
        
    def update(self, content, role):
        """Update conversation state based on new message"""
        # Add to conversation turns
        self.turns.append({"role": role, "content": content})
        
        # Keep only the most recent turns
        if len(self.turns) > self.max_history:
            self.turns = self.turns[-self.max_history:]
        
        # If it's the assistant's message, update followup expectation
        if role == "assistant":
            # Check if the response ends with a question or suggestion
            self.awaiting_followup = content.rstrip().endswith("?") or "would you like" in content.lower()
            
        # If it's the user's message, update context
        elif role == "user":
            # Reset followup flag
            self.awaiting_followup = False
            
    def is_followup_question(self, query, previous_response=None):
        """Determine if this is a followup question"""
        # Short responses are often follow-ups
        if len(query.strip().split()) <= 3:
            return True
            
        # Check for pronouns referring to previous context
        followup_indicators = [
            r'\b(it|its|they|their|there|that|this|those|these)\b',
            r'^(what about|how about|and)\b',
            r'^(what|where|when|how|why|who|which)\b.{1,30}\?$'  # Short questions are often follow-ups
        ]
        
        for pattern in followup_indicators:
            if re.search(pattern, query, re.IGNORECASE):
                return True
        
        return False
        
    def get_active_library(self):
        """Get the currently active library in conversation"""
        return self.current_library
        
    def set_active_library(self, library):
        """Set the active library for the conversation"""
        self.current_library = library
        if library:
            self.mentioned_libraries.add(library.get("Library Name", ""))
            
    def get_active_building(self):
        """Get the currently active building in conversation"""
        return self.current_building
        
    def set_active_building(self, building):
        """Set the active building for the conversation"""
        self.current_building = building
        if building:
            self.mentioned_buildings.add(building.get("Building Name", ""))
    
    def should_maintain_context(self, query, previous_context):
        """Determine if previous context should be maintained"""
        if not previous_context:
            return False
            
        # Check if a different entity is mentioned in the query
        query_lower = query.lower()
        
        if isinstance(previous_context, dict) and "Library Name" in previous_context:
            # We're dealing with a library
            for library in LIBRARY_DATA:
                lib_name = library.get('Library Name', '').lower()
                if lib_name in query_lower and lib_name != previous_context.get('Library Name', '').lower():
                    return False
                    
                # Also check aliases
                if 'Aliases' in library:
                    for alias in library['Aliases']:
                        if alias.lower() in query_lower and lib_name != previous_context.get('Library Name', '').lower():
                            return False
                            
        elif isinstance(previous_context, dict) and "Building Name" in previous_context:
            # We're dealing with a building
            for building in CAMPUS_BUILDINGS_DATA:
                building_name = building.get('Building Name', '').lower()
                if building_name in query_lower and building_name != previous_context.get('Building Name', '').lower():
                    return False
                    
                # Also check abbreviations
                abbr = building.get('Abbreviation', '').lower()
                if abbr and abbr in query_lower and abbr != previous_context.get('Abbreviation', '').lower():
                    return False
                            
        # No new entity mentioned, probably continue with previous context
        return True
            
    def get_conversation_summary(self):
        """Generate a summary of the conversation context"""
        if not self.turns:
            return "No conversation history."
            
        # Extract key information
        summary = {
            "turn_count": len(self.turns),
            "active_library": self.current_library.get("Library Name", "None") if self.current_library else "None",
            "active_building": self.current_building.get("Building Name", "None") if self.current_building else "None",
            "mentioned_libraries": list(self.mentioned_libraries),
            "mentioned_buildings": list(self.mentioned_buildings),
            "discussed_topics": list(self.discussed_topics),
            "awaiting_followup": self.awaiting_followup,
            "last_intent": self.last_intent,
            "query_type": self.query_type
        }
        
        return summary

class MetricsTracker:
    """Track performance metrics for the assistant"""
    
    def __init__(self):
        self.queries_processed = 0
        self.total_response_time = 0
        self.avg_response_time = 0
        self.total_confidence = 0
        self.avg_confidence = 0
        self.library_matches = defaultdict(int)
        self.building_matches = defaultdict(int)
        self.query_categories = defaultdict(int)
        self.intents = defaultdict(int)
        self.hourly_stats = defaultdict(int)
        self.response_quality = []
        
    def record_query(self, query, response, response_time, metrics=None):
        """Record metrics for a processed query"""
        # Increment query count
        self.queries_processed += 1
        
        # Update time metrics
        self.total_response_time += response_time
        self.avg_response_time = self.total_response_time / self.queries_processed
        
        # Update confidence metrics if available
        if metrics and 'confidence' in metrics:
            confidence = metrics.get('confidence', 0)
            self.total_confidence += confidence
            self.avg_confidence = self.total_confidence / self.queries_processed
            
        # Record library matches if available
        if metrics and 'library' in metrics:
            library_name = metrics['library'].get('Library Name', '') if metrics['library'] else 'None'
            self.library_matches[library_name] += 1
            
        # Record building matches if available
        if metrics and 'building' in metrics:
            building_name = metrics['building'].get('Building Name', '') if metrics['building'] else 'None'
            self.building_matches[building_name] += 1
            
        # Record query categories if available
        if metrics and 'categories' in metrics:
            for category in metrics['categories']:
                self.query_categories[category] += 1
                
        # Record intent if available
        if metrics and 'intent' in metrics:
            self.intents[metrics['intent']] += 1
            
        # Record hour of day
        hour = datetime.now().hour
        self.hourly_stats[hour] += 1
        
        # Store query/response pair for quality analysis
        self.response_quality.append({
            'query': query,
            'response': response,
            'response_time': response_time,
            'timestamp': datetime.now().isoformat(),
            'metrics': metrics
        })
        
    def get_summary(self):
        """Get summary of performance metrics"""
        summary = {
            "queries_processed": self.queries_processed,
            "avg_response_time": self.avg_response_time,
            "avg_confidence": self.avg_confidence,
            "top_libraries": dict(sorted(self.library_matches.items(), key=lambda x: x[1], reverse=True)[:5]),
            "top_buildings": dict(sorted(self.building_matches.items(), key=lambda x: x[1], reverse=True)[:5]),
            "top_categories": dict(sorted(self.query_categories.items(), key=lambda x: x[1], reverse=True)[:5]),
            "top_intents": dict(sorted(self.intents.items(), key=lambda x: x[1], reverse=True)[:5]),
            "peak_hours": dict(sorted(self.hourly_stats.items(), key=lambda x: x[1], reverse=True)[:3])
        }
        
        return summary
        
    def export_metrics(self, filename="uf_assistant_metrics.json"):
        """Export metrics to a JSON file"""
        try:
            metrics_data = {
                "summary": self.get_summary(),
                "detailed_metrics": {
                    "queries_processed": self.queries_processed,
                    "avg_response_time": self.avg_response_time,
                    "avg_confidence": self.avg_confidence,
                    "library_matches": dict(self.library_matches),
                    "building_matches": dict(self.building_matches),
                    "query_categories": dict(self.query_categories),
                    "intents": dict(self.intents),
                    "hourly_stats": dict(self.hourly_stats)
                },
                "timestamp": datetime.now().isoformat()
            }
            
            with open(filename, 'w') as f:
                json.dump(metrics_data, f, indent=2)
                
            return True
        except Exception as e:
            logger.error(f"Error exporting metrics: {e}")
            return False

# =============================================================================
# DATA LOADING FUNCTIONS
# =============================================================================

def load_campus_buildings_data(csv_path="scrapedData/campusBuildings/uf_buildings.csv"):
    """Load campus buildings data from CSV file"""
    buildings = []
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                buildings.append({
                    "Building Number": row.get('number', ''),
                    "Building Name": row.get('name', ''),
                    "Abbreviation": row.get('abbreviation', ''),
                    "Address": row.get('address', ''),
                    "Description": row.get('description', '')
                })
        logger.info(f"[OK] Successfully loaded {len(buildings)} campus buildings from CSV")
        return buildings
    except Exception as e:
        logger.error(f"Error loading campus buildings data: {e}")
        # Return the hardcoded data as fallback
        logger.info("[WARNING] Using hardcoded campus buildings data as fallback")
        return CAMPUS_BUILDINGS_DATA

def load_clubs_data(csv_path="scrapedData/campusClubs/uf_organizations.csv"):
    """Load clubs data from CSV file"""
    clubs = []
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                clubs.append({
                    "Club ID": row.get('ID', ''),
                    "Organization Name": row.get('Organization Name', ''),
                    "Description": row.get('Description', '')
                })
        logger.info(f"[OK] Successfully loaded {len(clubs)} clubs from CSV")
        return clubs
    except Exception as e:
        logger.error(f"Error loading clubs data: {e}")
        return []

def load_events_data(csv_path="scrapedData/campusEvents/uf_events_all.csv"):
    """Load events data from CSV file"""
    events = []
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                events.append({
                    "Event Name": row.get('name', ''),
                    "Date": row.get('date', ''),
                    "Time": row.get('time', ''),
                    "Location": row.get('location', ''),
                    "Link": row.get('link', ''),
                    "Description": row.get('description', '')
                })
        logger.info(f"[OK] Successfully loaded {len(events)} events from CSV")
        return events
    except Exception as e:
        logger.error(f"Error loading events data: {e}")
        return []

def load_courses_data(csv_path="scrapedData/classes/courses.csv"):
    """Load courses data from CSV file"""
    courses = []
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                courses.append({
                    "Department": row.get('department', ''),
                    "Course Code": row.get('code', ''),
                    "Course Title": row.get('title', ''),
                    "Credit Count": row.get('credits', ''),
                    "Description": row.get('description', ''),
                    "Prerequisites": row.get('prerequisites', ''),
                    "Grading Scheme": row.get('grading_scheme', '')
                })
        logger.info(f"[OK] Successfully loaded {len(courses)} courses from CSV")
        return courses
    except Exception as e:
        logger.error(f"Error loading courses data: {e}")
        return []

def load_majors_data(csv_path="scrapedData/classes/majors.csv"):
    """Load majors data from CSV file"""
    majors = []
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                majors.append({
                    "Department": row.get('department', ''),
                    "Description": row.get('description', '')
                })
        logger.info(f"[OK] Successfully loaded {len(majors)} majors from CSV")
        return majors
    except Exception as e:
        logger.error(f"Error loading majors data: {e}")
        return []

def load_programs_data(csv_path="scrapedData/classes/programs.csv"):
    """Load programs data from CSV file"""
    programs = []
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                programs.append({
                    "Department": row.get('department', ''),
                    "Program Name": row.get('name', ''),
                    "URL": row.get('url', ''),
                    "Type": row.get('type', '')
                })
        logger.info(f"[OK] Successfully loaded {len(programs)} programs from CSV")
        return programs
    except Exception as e:
        logger.error(f"Error loading programs data: {e}")
        return []

def load_hallinfo_data(csv_path="scrapedData/housing/hallInfo.csv"):
    """Load hall info data from CSV file"""
    hallinfo = []
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                hallinfo.append({
                    "Building Name": row.get('name', ''),
                    "Hall Type": row.get('hall_type', ''),
                    "Description": row.get('description', ''),
                    "Location": row.get('location', ''),
                    "Phone": row.get('phone', ''),
                    "Features": row.get('features_str', '').split(','),
                    "Room Types": row.get('room_types_str', '').split(','),
                    "Nearby Locations": row.get('nearby_locations_str', '').split(','),
                    "URL": row.get('url', ''),
                    "Image URL": row.get('image_url', ''),
                    "Rental Rate URL": row.get('rental_rate_url', '')
                })
        logger.info(f"[OK] Successfully loaded {len(hallinfo)} hall info from CSV")
        return hallinfo
    except Exception as e:
        logger.error(f"Error loading hall info data: {e}")
        return []

def load_housinglinks_data(csv_path="scrapedData/housing/housingLinks.csv"):
    """Load housing links data from CSV file"""
    housinglinks = []
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                housinglinks.append({
                    "Description": row.get('description', ''),
                    "Link": row.get('link', '')
                })
        logger.info(f"[OK] Successfully loaded {len(housinglinks)} housing links from CSV")
        return housinglinks
    except Exception as e:
        logger.error(f"Error loading housing links data: {e}")
        return []

def load_residencehallrates_data(csv_path="scrapedData/housing/residenceHallRates.csv"):
    """Load residence hall rates data from CSV file"""
    residencehallrates = []
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                residencehallrates.append({
                    "Residence Hall": row.get('residence_hall', ''),
                    "Room Type": row.get('room_type', ''),
                    "Fall/Spring Rate": row.get('fall_spring', ''),
                    "Summer A/B Rate": row.get('summer_a_b', ''),
                    "Summer C Rate": row.get('summer_c', '')
                })
        logger.info(f"[OK] Successfully loaded {len(residencehallrates)} residence hall rates from CSV")
        return residencehallrates
    except Exception as e:
        logger.error(f"Error loading residence hall rates data: {e}")
        return []

def load_libraries_data(csv_path="scrapedData/libraries/uf_libraries.csv"):
    """Load libraries data from CSV file"""
    libraries = []
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                libraries.append({
                    "Library Name": row.get('Library Name', ''),
                    "Location": row.get('Location', ''),
                    "Capacity": row.get('Capacity', ''),
                    "Hours": json.loads(row.get('Hours', '{}')) if row.get('Hours') else {},
                    "Special Notes": row.get('Special Notes', ''),
                    "URL": row.get('URL', ''),
                    "Phone": row.get('Phone', ''),
                    "Email": row.get('Email', '')
                })
        logger.info(f"[OK] Successfully loaded {len(libraries)} libraries from CSV")
        return libraries
    except Exception as e:
        logger.error(f"Error loading libraries data: {e}")
        return []

def load_mainufpages_links_data(csv_path="scrapedData/mainUfPages/links.csv"):
    """Load main UF pages data from CSV file"""
    mainufpages = []
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                mainufpages.append({
                    "Source URL": row.get('source_url', ''),
                    "Target URL": row.get('target_url', ''),
                    "Link Text": row.get('link_text', ''),
                    "Timestamp": row.get('timestamp', '')
                })
        logger.info(f"[OK] Successfully loaded {len(mainufpages)} main UF pages from CSV")
        return mainufpages
    except Exception as e:
        logger.error(f"Error loading main UF pages data: {e}")
        return []

def load_mainufpages_mainufdata_data(csv_path="scrapedData/mainUfPages/mainUFData.csv"):
    """Load main UF pages data from CSV file"""
    mainufdata = []
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                mainufdata.append({
                    "Category": row.get('Category', ''),
                    "Name": row.get('Name', ''),
                    "Description": row.get('Description', ''),
                    "Year_Established": row.get('Year_Established', ''),
                    "Location": row.get('Location', ''),
                    "Additional_Notes": row.get('Additional_Notes', '')
                })
        logger.info(f"[OK] Successfully loaded {len(mainufdata)} main UF pages data from CSV")
        return mainufdata
    except Exception as e:
        logger.error(f"Error loading main UF pages data: {e}")
        return []

def load_tuition_data(csv_path="scrapedData/tuition/tuition_costs.csv"):
    """Load tuition data from CSV file"""
    tuition_data = []
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                tuition_data.append({
                    "Category": row.get('Category', ''),
                    "Expense Type": row.get('Expense Type', ''),
                    "Amount": row.get('Amount', ''),
                    "Academic Year": row.get('Academic Year', '')
                })
        logger.info(f"[OK] Successfully loaded {len(tuition_data)} tuition data from CSV")
        return tuition_data
    except Exception as e:
        logger.error(f"Error loading tuition data: {e}")
        return []

# =============================================================================
# ENHANCED KNOWLEDGE RETRIEVAL
# =============================================================================

class EnhancedKnowledgeRetrieval:
    """Advanced knowledge retrieval with hybrid search techniques"""
    
    def __init__(self, libraries_data, embedding_model=None):
        self.libraries_data = libraries_data
        self.embedding_model = embedding_model
        
        # Load and prepare data
        self.library_names = [lib.get('Library Name', '') for lib in libraries_data]
        self.library_by_name = {lib.get('Library Name', ''): lib for lib in libraries_data}
        
        # Build indexes
        self.keyword_index = self._build_keyword_index()
        self.vector_index = self._build_vector_index() if embedding_model else None
        
        # Build data structures for efficient lookup
        self.library_descriptions = self._build_library_descriptions()
        self.library_aliases = self._build_aliases()
        
        # Cache for query results
        self.query_cache = LRUCache(capacity=100)
        
    def _build_keyword_index(self):
        """Build inverted index for keyword search"""
        index = defaultdict(list)
        for i, library in enumerate(self.libraries_data):
            # Extract keywords from all fields
            keywords = []
            
            # Add library name and aliases
            if 'Library Name' in library:
                keywords.append(library['Library Name'].lower())
            if 'Aliases' in library:
                keywords.extend([alias.lower() for alias in library['Aliases']])
            
            # Add tags
            if 'Tags' in library:
                keywords.extend(library['Tags'].lower().split(', '))
                
            # Add key resources
            if 'Resources' in library:
                for resource in library['Resources']:
                    keywords.extend(resource.lower().split())
                    
            # Add all keywords to index
            for keyword in set(keywords):
                index[keyword].append(i)
                
                # Add word parts for better matching
                parts = keyword.split()
                if len(parts) > 1:
                    for part in parts:
                        if len(part) > 3:  # Only add meaningful parts
                            index[part].append(i)
                
        return index
        
    def _build_vector_index(self):
        """Build vector index for semantic search with proper error handling"""
        if not self.embedding_model:
            return None
            
        try:
            # Initialize vector storage
            embeddings = []
            descriptions = []
            
            # First create all descriptions
            for library in self.libraries_data:
                desc = self._create_library_description(library)
                descriptions.append(desc)
            
            # Generate embeddings
            embeddings = self.embedding_model.encode(descriptions)
            
            # Create index if hnswlib is available
            if hnswlib:
                vector_dim = embeddings.shape[1]
                index = hnswlib.Index(space='cosine', dim=vector_dim)
                
                # Initialize with proper parameters
                index.init_index(
                    max_elements=len(self.libraries_data),
                    ef_construction=200,
                    M=16
                )
                
                # Add library embeddings with proper indexing
                index.add_items(embeddings, list(range(len(self.libraries_data))))
                
                # Set search parameters
                index.set_ef(50)
                
                return index
            else:
                # Fallback to dictionary for simpler implementations
                embeddings_dict = {}
                for i in range(len(embeddings)):
                    embeddings_dict[i] = embeddings[i]
                return embeddings_dict
                
        except Exception as e:
            logger.error(f"Error building vector index: {e}")
            # Return empty dict as fallback to avoid errors
            return {}
    
    def _create_library_description(self, library):
        """Create a detailed description of a library for semantic matching"""
        name = library.get('Library Name', '')
        location = library.get('Location', '')
        tags = library.get('Tags', '')
        notes = library.get('Special Notes', '')
        
        # Create a detailed description
        description = f"{name} is a library at the University of Florida. "
        description += f"It is located at {location}. "
        
        if tags:
            description += f"It specializes in {tags}. "
            
        if notes:
            description += f"It offers {notes}. "
        
        # Add resources and collections if available
        if 'Resources' in library and library['Resources']:
            resources = ', '.join(library['Resources'][:5])  # Limit to top 5
            description += f"It provides these resources: {resources}. "
            
        if 'Collections' in library and library['Collections']:
            collections = ', '.join(library['Collections'][:5])  # Limit to top 5
            description += f"Its collections include: {collections}. "
        
        # Add hours information
        if 'Hours' in library and library['Hours']:
            description += f"It is typically open from morning until late evening on weekdays. "
            
        return description
        
    def _build_library_descriptions(self):
        """Build detailed descriptions for all libraries"""
        descriptions = {}
        for library in self.libraries_data:
            name = library.get('Library Name', '')
            if name:
                descriptions[name] = self._create_library_description(library)
        return descriptions
        
    def _build_aliases(self):
        """Build a comprehensive alias dictionary for library names"""
        aliases = {}
        
        # Add aliases from library data
        for library in self.libraries_data:
            name = library.get('Library Name', '')
            if 'Aliases' in library and library['Aliases']:
                for alias in library['Aliases']:
                    aliases[alias.lower()] = name
        
        # Add additional common aliases not covered in the data
        additional_aliases = {
            # Additional Library West variations
            "libw": "Library West",
            "main library": "Library West",
            "humanities library": "Library West",
            "business library": "Library West",
            
            # Additional Marston Science Library variations
            "engineering library": "Marston Science Library",
            "tech library": "Marston Science Library",
            "stem library": "Marston Science Library",
            
            # Additional Smathers Library variations
            "library 1": "Smathers Library",
            "rare books": "Smathers Library",
            "archives library": "Smathers Library",
            
            # Additional Education Library variations
            "norman": "Education Library",
            "teaching library": "Education Library",
            
            # Additional Legal Information Center variations
            "legal library": "Legal Information Center",
            "law college library": "Legal Information Center",
            "levin library": "Legal Information Center",
        }
        
        # Update aliases with additional ones
        aliases.update(additional_aliases)
        
        return aliases
        
    def retrieve_relevant_library(self, query, query_analysis=None):
        """Retrieve the most relevant library for a query using multiple methods"""
        # Preprocess query
        query = self._preprocess_query(query)
        
        # Check cache first
        cache_key = f"retrieve_library:{query}"
        if cache_key in self.query_cache:
            return self.query_cache[cache_key]
            
        # Try multiple methods and combine results
        results = []
        
        # 1. Check for direct library name matches first (most reliable)
        direct_match, direct_confidence = self._find_library_by_name(query)
        if direct_match:
            results.append({"library": direct_match, "confidence": direct_confidence, "method": "direct_match"})
        
        # 2. Try semantic similarity if available
        if self.embedding_model and self.vector_index:
            semantic_match, semantic_confidence = self._find_library_by_semantic_similarity(query)
            if semantic_match:
                results.append({"library": semantic_match, "confidence": semantic_confidence, "method": "semantic"})
        
        # 3. Try subject matching for topic-related queries
        subject_match, subject_confidence = self._find_library_by_subject(query)
        if subject_match:
            results.append({"library": subject_match, "confidence": subject_confidence, "method": "subject"})
            
        # 4. Try keyword-based matching
        keyword_match, keyword_confidence = self._find_library_by_keywords(query)
        if keyword_match:
            results.append({"library": keyword_match, "confidence": keyword_confidence, "method": "keyword"})
        
        # 5. Consider query analysis if provided
        if query_analysis:
            if query_analysis.get('mentioned_libraries'):
                mentioned_lib = query_analysis['mentioned_libraries'][0]
                if mentioned_lib in self.library_by_name:
                    results.append({
                        "library": self.library_by_name[mentioned_lib], 
                        "confidence": 0.9,
                        "method": "query_analysis"
                    })
                    
        # No matches found
        if not results:
            # Try a more aggressive matching as last resort
            last_resort, last_resort_confidence = self._find_library_by_aggressive_matching(query)
            if last_resort:
                results.append({"library": last_resort, "confidence": last_resort_confidence, "method": "aggressive"})
        
        # If still no results, return None
        if not results:
            self.query_cache[cache_key] = (None, 0.0)
            return None, 0.0
        
        # Return the match with highest confidence
        best_result = max(results, key=lambda x: x["confidence"])
        best_match = (best_result["library"], best_result["confidence"])
        
        # Add to cache
        self.query_cache[cache_key] = best_match
        
        return best_match
    
    def _preprocess_query(self, query):
        """Preprocess query for better library matching"""
        # Normalize library names
        query = re.sub(r"\blib\s*west\b", "Library West", query, flags=re.IGNORECASE)
        query = re.sub(r"\bmarston('s)?\b", "Marston Science Library", query, flags=re.IGNORECASE)
        query = re.sub(r"\bsmathers\b", "Smathers Library", query, flags=re.IGNORECASE)
        
        return query
    
    def _find_library_by_name(self, query):
        """Find a library by name using enhanced fuzzy matching"""
        if not query:
            return None, 0.0
        
        # Skip certain phrases that shouldn't match libraries
        skip_phrases = [
            "ai", "artificial intelligence", "bot", "chatbot", "assistant",
            "all libraries", "which libraries", "what libraries", "any libraries",
            "campus", "university", "uf", "florida", "university of florida"
        ]
        
        # Check if query is just one of the skip phrases
        query_lower = query.lower().strip()
        if query_lower in skip_phrases:
            return None, 0.0
            
        # First check for direct match in library names
        for name in self.library_names:
            if query_lower == name.lower():
                return self.library_by_name[name], 0.95
        
        # Then check if the entire query is an alias
        if query_lower in self.library_aliases:
            return self.library_by_name[self.library_aliases[query_lower]], 0.95
        
        # Extract potential library mentions from the query
        words = query_lower.split()
        
        # Check for consecutive word combinations that might refer to a library
        for i in range(len(words)):
            for j in range(i + 1, min(i + 4, len(words) + 1)):  # Look at up to 3-word combinations
                phrase = " ".join(words[i:j])
                
                # Check if this phrase matches an alias
                if phrase in self.library_aliases:
                    return self.library_by_name[self.library_aliases[phrase]], 0.90
                
                # Check for partial matches with library names
                for name in self.library_names:
                    name_lower = name.lower()
                    if phrase in name_lower or name_lower in phrase:
                        if len(phrase) >= 3:  # Only if it's a significant match
                            return self.library_by_name[name], 0.85
        
        # Try fuzzy matching for misspellings
        best_match = None
        best_score = 0
        
        for name in self.library_names:
            # Calculate similarity scores
            token_set_ratio = fuzz.token_set_ratio(query_lower, name.lower())
            partial_ratio = fuzz.partial_ratio(query_lower, name.lower())
            
            # Combined score (weight can be adjusted)
            score = (token_set_ratio * 0.7) + (partial_ratio * 0.3)
            
            if score > best_score and score > 75:  # Threshold can be adjusted
                best_score = score
                best_match = name
        
        if best_match:
            return self.library_by_name[best_match], 0.80
        
        return None, 0.0
    
    def _find_library_by_semantic_similarity(self, query):
        """Find the library that best matches the query semantically"""
        if not self.embedding_model or not self.vector_index or not query:
            return None, 0.0
        
        try:
            # Get query embedding
            query_embedding = self.embedding_model.encode(query)
            
            # Use HNSW approximate nearest neighbor search if available
            if isinstance(self.vector_index, dict):
                # Fallback to manual search with cosine similarity
                best_idx = -1
                best_sim = -1
                
                for idx, embedding in self.vector_index.items():
                    sim = cosine_similarity([query_embedding], [embedding])[0][0]
                    if sim > best_sim:
                        best_sim = sim
                        best_idx = idx
                
                # Only consider it a match if similarity is above threshold
                if best_sim < 0.4 or best_idx < 0:  # This threshold can be tuned
                    return None, 0.0
                    
                library_name = self.library_names[best_idx]
                return self.library_by_name[library_name], min(best_sim, 0.85)
            elif hasattr(self.vector_index, 'knn_query'):
                # Use HNSW index
                labels, distances = self.vector_index.knn_query(query_embedding.reshape(1, -1), k=1)
                best_idx = labels[0][0]
                similarity = 1.0 - distances[0][0]  # Convert distance to similarity
                
                # Only consider it a match if similarity is above threshold
                if similarity < 0.4:  # This threshold can be tuned
                    return None, 0.0
                    
                library_name = self.library_names[best_idx]
                return self.library_by_name[library_name], min(similarity, 0.85)
            else:
                # No suitable vector index
                return None, 0.0
                
        except Exception as e:
            logger.error(f"Error computing semantic similarity: {e}")
            return None, 0.0
        
    def _find_library_by_subject(self, query):
        """Find library based on academic subjects mentioned in query"""
        query_lower = query.lower()
        
        # Count subject matches for each library
        library_scores = Counter()
        
        for subject, library_name in SUBJECT_MAPPINGS.items():
            if subject in query_lower:
                library_scores[library_name] += 1
        
        # Return library with most subject matches
        if library_scores:
            best_library = library_scores.most_common(1)[0][0]
            score_count = library_scores[best_library]
            
            # Scale confidence based on number of matches
            confidence = min(0.8, 0.6 + (score_count * 0.05))
            
            if best_library in self.library_by_name:
                return self.library_by_name[best_library], confidence
        
        return None, 0.0
        
    def _find_library_by_keywords(self, query):
        """Find libraries based on keywords in the index"""
        query_words = query.lower().split()
        
        # Count matches for each library
        library_counts = Counter()
        
        # Check each word in the query
        for word in query_words:
            if word in self.keyword_index:
                for library_idx in self.keyword_index[word]:
                    library_counts[library_idx] += 1
        
        # Find library with most keyword matches
        if library_counts:
            best_idx, count = library_counts.most_common(1)[0]
            
            # Scale confidence based on match count
            confidence = min(0.75, 0.5 + (count * 0.05))
            
            return self.libraries_data[best_idx], confidence
            
        return None, 0.0
        
    def _find_library_by_aggressive_matching(self, query):
        """Last resort matching with aggressive partial matching"""
        query_lower = query.lower()
        
        # General case handling for specific question patterns
        if "reserve" in query_lower and "room" in query_lower:
            # For room reservation questions, default to Library West
            return self.library_by_name.get("Library West"), 0.6
            
        if "coffee" in query_lower or "starbucks" in query_lower:
            # For coffee questions, prioritize libraries with Starbucks
            return self.library_by_name.get("Library West"), 0.65
            
        if "website" in query_lower or "url" in query_lower or "online" in query_lower:
            # For website questions, default to Library West
            return self.library_by_name.get("Library West"), 0.6
        
        # Short forms that might appear in queries
        short_forms = {
            "lib west": "Library West",
            "west": "Library West",
            "marston": "Marston Science Library",
            "science": "Marston Science Library",
            "smathers": "Smathers Library",
            "special": "Smathers Library",
            "health": "Health Science Center Library",
            "hsc": "Health Science Center Library",
            "med": "Health Science Center Library",
            "afa": "Architecture & Fine Arts Library",
            "arts": "Architecture & Fine Arts Library",
            "arch": "Architecture & Fine Arts Library",
            "edu": "Education Library",
            "norman": "Education Library",
            "law": "Legal Information Center",
            "legal": "Legal Information Center",
            "levin": "Legal Information Center"
        }
        
        # Check for any partial matches
        for short_form, library_name in short_forms.items():
            if short_form in query_lower.split():
                return self.library_by_name.get(library_name), 0.6
        
        # Check for common topics or questions
        topic_mappings = {
            "study": "Library West",  # Default to Library West for general study questions
            "quiet": "Marston Science Library",  # Marston has good quiet spaces
            "group": "Library West",  # Library West for group study
            "research": "Smathers Library",  # Research often means special collections
            "book": "Library West",  # General book queries to main library
            "hours": "Library West",  # Hours questions default to main library
            "computer": "Marston Science Library",  # Tech questions to Marston
            "print": "Marston Science Library",  # Printing to Marston
            "where": "Library West"  # Location questions default to main library
        }
        
        for topic, library_name in topic_mappings.items():
            if topic in query_lower:
                return self.library_by_name.get(library_name), 0.5
        
        return None, 0.0
        
    def get_all_libraries_summary(self):
        """Get a summary of all libraries"""
        summaries = []
        for lib in self.libraries_data:
            name = lib.get('Library Name', '')
            location = lib.get('Location', '')
            focus = lib.get('Tags', '')
            
            summary = f"• {name}: Located at {location}."
            if focus:
                summary += f" Focus areas: {focus}."
                
            summaries.append(summary)
        
        return "\n".join(summaries)
    
    def get_library_hours(self, library_name, day=None):
        """Get the hours for a specific library, optionally for a specific day"""
        library = self.library_by_name.get(library_name)
        if not library:
            return "Library not found"
        
        if 'Hours' not in library:
            return "Hours information not available"
        
        hours = library['Hours']
        
        if day:
            # Format day to match keys (capitalize first letter)
            day = day.capitalize()
            if day in hours:
                return f"{hours[day]}"
            else:
                return "Hours not available for this day"
        else:
            # Return all hours
            return "\n".join([f"{d}: {h}" for d, h in hours.items()])
    
    def get_library_resources(self, library_name, resource_type=None):
        """Get resources for a specific library, optionally filtered by type"""
        library = self.library_by_name.get(library_name)
        if not library:
            return []
        
        if resource_type and resource_type in library:
            return library.get(resource_type, [])
        
        # Combine all resource types if no specific type requested
        resource_types = ['Resources', 'Study Spaces', 'Collections', 'Technology', 'Services']
        all_resources = []
        
        for rt in resource_types:
            all_resources.extend(library.get(rt, []))
        
        return all_resources
    
    def get_library_website(self, library_name):
        """Get the website URL for a specific library"""
        library = self.library_by_name.get(library_name)
        if not library or 'URL' not in library:
            return None
        return library.get('URL')
        
    def find_amenities_by_type(self, amenity_type, near_library=None):
        """Find campus amenities by type, optionally near a specific library"""
        if amenity_type not in CAMPUS_AMENITIES:
            return []
            
        amenities = CAMPUS_AMENITIES[amenity_type]
        
        # If a library is specified, prioritize amenities near that library
        if near_library:
            # First, find amenities that are explicitly near this library
            nearby_amenities = [
                amenity for amenity in amenities 
                if amenity.get('nearest_library', '') == near_library
            ]
            
            # If we found any nearby amenities, return those
            if nearby_amenities:
                return nearby_amenities
        
        # Otherwise return all amenities of this type
        return amenities

    def get_academic_calendar_info(self, date=None):
        """Get academic calendar information for a specific date"""
        if date is None:
            date = datetime.now().date()
        else:
            date = date.date() if isinstance(date, datetime) else date
            
        # Convert date to string format for comparison
        date_str = date.strftime('%Y-%m-%d')
        
        # Check if we're in a term
        current_term = None
        for term, dates in ACADEMIC_CALENDAR['terms'].items():
            if dates['start'] <= date_str <= dates['end']:
                current_term = term
                break
                
        # Check if we're in any special event period
        current_event = None
        for event, dates in ACADEMIC_CALENDAR['events'].items():
            if dates['start'] <= date_str <= dates['end']:
                current_event = event
                break
                
        # Check for schedule exceptions
        schedule_exception = None
        if date_str in ACADEMIC_CALENDAR['library_schedule_exceptions']:
            schedule_exception = ACADEMIC_CALENDAR['library_schedule_exceptions'][date_str]
        
        # Check if we're in extended hours period
        extended_hours = None
        for period, info in ACADEMIC_CALENDAR['extended_hours'].items():
            if info['start'] <= date_str <= info['end']:
                extended_hours = {
                    'period': period,
                    'libraries': info['libraries']
                }
                break
                
        return {
            'date': date_str,
            'current_term': current_term,
            'current_event': current_event,
            'schedule_exception': schedule_exception,
            'extended_hours': extended_hours
        }
        
    def get_room_reservation_info(self, library_name):
        """Get room reservation information for a specific library"""
        library = self.library_by_name.get(library_name)
        if not library:
            return None
            
        # Base reservation information
        reservation_info = {
            "library": library_name,
            "website": library.get('URL', ''),
            "process": "To reserve a study room, go to the UF Libraries website, click on 'Study Rooms', sign in with your GatorLink, and select your preferred time and location.",
            "restrictions": []
        }
        
        # Add library-specific restrictions
        if 'Marston' in library_name:
            reservation_info["restrictions"] = [
                "Reservations are limited to 2 hours per day per group",
                "Valid UF ID required",
                "Intended for groups of 2 or more people"
            ]
        elif 'West' in library_name:
            reservation_info["restrictions"] = [
                "Graduate student rooms available on 3rd floor",
                "Undergraduate rooms on multiple floors",
                "Reservations can be made up to 7 days in advance"
            ]
        else:
            reservation_info["restrictions"] = [
                "Most rooms can be reserved for 2 hours",
                "Valid UF ID required",
                "Reservations typically available 7 days in advance"
            ]
            
        return reservation_info

# =============================================================================
# CAMPUS BUILDINGS RETRIEVAL
# =============================================================================

class CampusBuildingsRetrieval:
    """Knowledge retrieval for campus buildings"""
    
    def __init__(self, buildings_data):
        self.buildings_data = buildings_data
        self.building_by_name = {b.get('Building Name', ''): b for b in buildings_data}
        self.building_by_abbr = {}
        
        # Build abbreviation index
        for building in buildings_data:
            abbr = building.get('Abbreviation', '')
            if abbr:
                self.building_by_abbr[abbr] = building
        
        # Build keyword index for building search
        self.keyword_index = self._build_keyword_index()
        
        # Cache for query results
        self.query_cache = LRUCache(capacity=100)
    
    def _build_keyword_index(self):
        """Build keyword index for building search"""
        index = defaultdict(list)
        for i, building in enumerate(self.buildings_data):
            # Extract keywords from name and description
            keywords = []
            
            # Add building name
            name = building.get('Building Name', '')
            if name:
                keywords.append(name.lower())
                parts = name.lower().split()
                for part in parts:
                    if len(part) > 3:
                        keywords.append(part)
            
            # Add abbreviation
            abbr = building.get('Abbreviation', '')
            if abbr:
                keywords.append(abbr.lower())
            
            # Add number
            num = building.get('Building Number', '')
            if num:
                keywords.append(num)
            
            # Add from description
            desc = building.get('Description', '')
            if desc:
                desc_words = desc.lower().split()
                for word in desc_words:
                    if len(word) > 3 and word not in ['with', 'and', 'the', 'for']:
                        keywords.append(word)
            
            # Add all keywords to index
            for keyword in set(keywords):
                index[keyword].append(i)
                
        return index
    
    def retrieve_building(self, query):
        """Retrieve most relevant building for a query"""
        query_lower = query.lower()
        
        # Check cache
        cache_key = f"building:{query_lower}"
        if cache_key in self.query_cache:
            return self.query_cache[cache_key]
            
        # Direct match by name
        for name, building in self.building_by_name.items():
            if query_lower == name.lower() or query_lower in name.lower():
                self.query_cache[cache_key] = (building, 0.95)
                return building, 0.95
        
        # Match by abbreviation
        for abbr, building in self.building_by_abbr.items():
            if query_lower == abbr.lower():
                self.query_cache[cache_key] = (building, 0.95)
                return building, 0.95
                
        # Match by building number
        for building in self.buildings_data:
            if building.get('Building Number') and building['Building Number'] in query:
                self.query_cache[cache_key] = (building, 0.95)
                return building, 0.95
                
        # Keyword search
        building_scores = Counter()
        
        for word in query_lower.split():
            if word in self.keyword_index:
                for building_idx in self.keyword_index[word]:
                    building_scores[building_idx] += 1
        
        # Find building with highest score
        if building_scores:
            best_idx, count = building_scores.most_common(1)[0]
            confidence = min(0.85, 0.6 + (count * 0.05))
            
            self.query_cache[cache_key] = (self.buildings_data[best_idx], confidence)
            return self.buildings_data[best_idx], confidence
        
        # Fuzzy matching for inexact building names
        best_match = None
        best_score = 0
        
        for name, building in self.building_by_name.items():
            # Calculate similarity scores
            token_set_ratio = fuzz.token_set_ratio(query_lower, name.lower())
            partial_ratio = fuzz.partial_ratio(query_lower, name.lower())
            
            # Combined score (weight can be adjusted)
            score = (token_set_ratio * 0.7) + (partial_ratio * 0.3)
            
            if score > best_score and score > 75:  # Threshold can be adjusted
                best_score = score
                best_match = building
        
        if best_match:
            confidence = min(0.8, best_score / 100)
            self.query_cache[cache_key] = (best_match, confidence)
            return best_match, confidence
            
        return None, 0.0
    
    def get_all_buildings_summary(self):
        """Get a summary of all campus buildings"""
        summaries = []
        for building in self.buildings_data:
            name = building.get('Building Name', '')
            abbr = building.get('Abbreviation', '')
            desc = building.get('Description', '')
            
            summary = f"• {name}"
            if abbr:
                summary += f" ({abbr})"
            if desc:
                summary += f": {desc}"
                
            summaries.append(summary)
            
        return "\n".join(summaries)
    
    def get_building_info(self, building_name_or_abbr):
        """Get detailed information about a specific building"""
        # Try to find by name
        building = self.building_by_name.get(building_name_or_abbr)
        
        # If not found, try abbreviation
        if not building:
            building = self.building_by_abbr.get(building_name_or_abbr)
            
        # If still not found, try case-insensitive search
        if not building:
            name_lower = building_name_or_abbr.lower()
            for name, b in self.building_by_name.items():
                if name.lower() == name_lower:
                    building = b
                    break
                    
            if not building:
                for abbr, b in self.building_by_abbr.items():
                    if abbr.lower() == name_lower:
                        building = b
                        break
        
        return building
    
    def find_buildings_by_type(self, building_type):
        """Find buildings of a specific type (based on description)"""
        type_keywords = {
            "classroom": ["classroom", "class", "lecture"],
            "research": ["research", "lab", "laboratory", "studies"],
            "administrative": ["admin", "office", "administration"],
            "athletic": ["athletic", "sport", "stadium", "arena", "gym", "fitness"],
            "residential": ["residential", "dorm", "housing", "hall"],
            "dining": ["dining", "food", "cafeteria", "restaurant"]
        }
        
        if building_type not in type_keywords:
            return []
            
        keywords = type_keywords[building_type]
        matching_buildings = []
        
        for building in self.buildings_data:
            desc = building.get('Description', '').lower()
            name = building.get('Building Name', '').lower()
            
            for keyword in keywords:
                if keyword in desc or keyword in name:
                    matching_buildings.append(building)
                    break
                    
        return matching_buildings
    
    def find_buildings_on_street(self, street_name):
        """Find buildings located on a specific street"""
        street_name_lower = street_name.lower()
        matching_buildings = []
        
        for building in self.buildings_data:
            address = building.get('Address', '').lower()
            
            if street_name_lower in address:
                matching_buildings.append(building)
                
        return matching_buildings

# =============================================================================
# ENHANCED QUERY ANALYZER
# =============================================================================

class EnhancedQueryAnalyzer:
    """Advanced query analyzer with improved intent detection"""
    
    CATEGORIES = {
        'hours': ['hour', 'time', 'open', 'close', 'opening', 'closing', 'schedule', 'when'],
        'location': ['where', 'located', 'find', 'address', 'building', 'map', 'direction', 'get to'],
        'services': ['service', 'offer', 'provide', 'assistance', 'help', 'available', 'computer', 'wifi', 'printing', 'print', 'scanner', 'scan'],
        'collections': ['book', 'collection', 'material', 'resource', 'database', 'journal', 'article', 'research'],
        'features': ['study', 'room', 'space', 'quiet', 'group', 'feature', 'makerspace', 'area'],
        'contact': ['contact', 'phone', 'email', 'call', 'librarian', 'staff', 'support'],
        'offerings': ['offer', 'offering', 'provide', 'have', 'things', 'stuff', 'what', 'available'],
        'resources': ['resource', 'equipment', 'technology', 'computer', 'printer', 'scanner', 'available'],
        'study_spaces': ['study', 'room', 'space', 'quiet', 'silent', 'group', 'collaborative', 'individual'],
        'events': ['event', 'workshop', 'session', 'class', 'training', 'seminar', 'happening'],
        'accessibility': ['accessibility', 'accessible', 'disability', 'handicap', 'wheelchair'],
        'amenities': ['coffee', 'food', 'cafe', 'drink', 'eat', 'restaurant', 'dining', 'starbucks'],
        'website': ['website', 'url', 'link', 'online', 'web', 'site'],
        'reservation': ['reserve', 'book', 'reservation', 'schedule', 'sign up'],
        'general': ['information', 'about', 'tell', 'describe', 'what'],
        'meta': ['ai', 'assistant', 'bot', 'you', 'who are you', 'what are you'],
        'buildings': ['building', 'hall', 'center', 'stadium', 'arena', 'classroom', 'lab', 'location', 'dept', 'department']
    }
    
    INTENTS = {
        'find_location': r'\b(where|location|address|building|find)\b',
        'check_hours': r'\b(hour|time|open|close|when)\b',
        'discover_offerings': r'\b(what|which|tell me about)\b.+\b(offer|available|service|feature|resource)\b',
        'find_study_space': r'\b(study|room|space|quiet)\b',
        'compare_libraries': r'\b(compare|better|best|difference)\b',
        'find_materials': r'\b(book|material|collection|research|database)\b',
        'find_coffee': r'\b(coffee|starbucks|cafe|café)\b',
        'find_food': r'\b(food|eat|restaurant|dining|lunch|dinner)\b',
        'get_information': r'\b(what|tell me|explain|information|about)\b',
        'check_availability': r'\b(available|when|can i|reservation)\b',
        'get_recommendations': r'\b(recommend|suggest|best|good for)\b',
        'get_directions': r'\b(direction|how to get|navigate|find my way)\b',
        'find_website': r'\b(website|url|link|online|web)\b',
        'reserve_room': r'\b(reserve|book|reservation)\b.+\b(room|space|study)\b',
        'find_building': r'\b(where|find|locate|building|hall|center)\b',
        'building_info': r'\b(what|tell me about|info|information|describe)\b.+\b(building|hall|center)\b',
        'general_question': r'\b(what|how|who|when|where)\b'
    }
    
    def __init__(self, nlp_model=None):
        self.nlp = nlp_model
        
        # Precompile patterns for efficiency
        self.category_patterns = {
            category: re.compile(r'\b(' + '|'.join(keywords) + r')\b', re.IGNORECASE)
            for category, keywords in self.CATEGORIES.items()
        }
        
        self.intent_patterns = {
            intent: re.compile(pattern, re.IGNORECASE)
            for intent, pattern in self.INTENTS.items()
        }
        
    def analyze(self, query, conversation_history=None):
        """Perform comprehensive query analysis"""
        # Preprocess query
        query = self._preprocess_query(query)
        
        if not query:
            return {
                'categories': ['general'],
                'intent': 'get_information',
                'question_type': 'unknown',
                'is_meta_question': False,
                'is_all_libraries_query': False,
                'is_building_query': False,
                'is_followup': False,
                'amenity_type': None,
                'mentioned_libraries': [],
                'mentioned_buildings': [],
                'time_reference': None,
                'specific_intents': []
            }
            
        # Process with spaCy if available
        entities = {}
        tokens = []
        pos_tags = []
        noun_chunks = []
        
        if self.nlp:
            try:
                doc = self.nlp(query)
                
                # Extract entities
                for ent in doc.ents:
                    if ent.label_ not in entities:
                        entities[ent.label_] = []
                    entities[ent.label_].append(ent.text)
                
                # Extract tokens and POS tags
                tokens = [token.text for token in doc]
                pos_tags = [token.pos_ for token in doc]
                
                # Extract noun chunks
                noun_chunks = [chunk.text for chunk in doc.noun_chunks]
                
            except Exception as e:
                logger.error(f"Error in spaCy processing: {e}")
        
        # Classify query categories
        categories = self._classify_categories(query)
        
        # Identify question type
        question_type = self._identify_question_type(query)
        
        # Check for meta-questions about the AI itself
        is_meta_question = self._is_meta_question(query)
        
        # Check if asking about all libraries
        is_all_libraries_query = self._is_all_libraries_query(query)
        
        # Check if asking about buildings
        is_building_query = self._is_building_query(query)
        
        # Detect primary intent
        intent = self._detect_intent(query)
        
        # Detect specific intents
        specific_intents = self._detect_specific_intents(query)
        
        # Extract time references
        time_reference = self._detect_time_reference(query)
        
        # Extract library mentions
        mentioned_libraries = self._extract_library_mentions(query)
        
        # Extract building mentions
        mentioned_buildings = self._extract_building_mentions(query)
        
        # Check if this is a follow-up question
        is_followup = self._is_followup_question(query, conversation_history)
        
        # Check for amenity queries
        amenity_type = self._detect_amenity_type(query)
        
        # Return comprehensive analysis
        return {
            'categories': categories,
            'intent': intent,
            'question_type': question_type,
            'is_meta_question': is_meta_question,
            'is_all_libraries_query': is_all_libraries_query,
            'is_building_query': is_building_query,
            'tokens': tokens,
            'pos_tags': pos_tags,
            'noun_chunks': noun_chunks,
            'entities': entities,
            'time_reference': time_reference,
            'mentioned_libraries': mentioned_libraries,
            'mentioned_buildings': mentioned_buildings,
            'is_followup': is_followup,
            'amenity_type': amenity_type,
            'specific_intents': specific_intents
        }
        
    def _preprocess_query(self, query):
        """Preprocess query to better understand user intent"""
        # Normalize library names
        query = re.sub(r"\blib\s*west\b", "Library West", query, flags=re.IGNORECASE)
        query = re.sub(r"\bmarston('s)?\b", "Marston Science Library", query, flags=re.IGNORECASE)
        query = re.sub(r"\bsmathers\b", "Smathers Library", query, flags=re.IGNORECASE)
        
        # Normalize building abbreviations
        query = re.sub(r"\b(?:clb|105 building)\b", "105 Classroom Building", query, flags=re.IGNORECASE)
        query = re.sub(r"\barb\b", "Academic Research Building", query, flags=re.IGNORECASE)
        query = re.sub(r"\band\b", "Anderson Hall", query, flags=re.IGNORECASE)
        
        # Normalize room reservation terms
        if "reserve" in query.lower() and "room" in query.lower():
            if not re.search(r"how|where|can i", query.lower()):
                query = f"how do I reserve a study room {query}"
            
        # Normalize website queries
        if "website" in query.lower() or "url" in query.lower():
            if not re.search(r"what|where is|find|get", query.lower()):
                query = f"find the website for {query}"
        
        return query
        
    def _classify_categories(self, query):
        """Classify a query into one or more categories"""
        categories = []
        query_lower = query.lower()
        
        for category, pattern in self.category_patterns.items():
            if pattern.search(query_lower):
                categories.append(category)
        
        # If no categories matched, consider it a general query
        if not categories:
            categories = ['general']
            
        return categories
        
    def _identify_question_type(self, query):
        """Identify the type of question"""
        # Look for question words
        question_words = {
            'what': r'\b(what|tell me|describe)\b',
            'where': r'\b(where|location|located|find)\b',
            'when': r'\b(when|what time|hours|schedule|open|close)\b',
            'which': r'\b(which|what)\s+(library|place|building)\b',
            'who': r'\b(who|contact|person|librarian)\b',
            'how': r'\b(how|way|method)\b'
        }
        
        for q_type, pattern in question_words.items():
            if re.search(pattern, query, re.IGNORECASE):
                return q_type
        
        # Check for imperatives or statements
        imperative_patterns = [
            r'\b(tell|show|list|give|find)\b',
            r'\b(looking for|need|want)\b',
            r'\b(can you|could you)\b'
        ]
        
        for pattern in imperative_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                return 'imperative'
        
        # Short responses like "yes", "no", "sure"
        if len(query.strip().split()) <= 2:
            return 'short_response'
        
        return 'statement'
        
    def _is_meta_question(self, query):
        """Check if the query is a meta-question about the AI itself"""
        meta_patterns = [
            r'\b(are|is)\s+you\s+an?\s+(ai|bot|robot|assistant|program|computer)',
            r'\b(who|what)\s+are\s+you',
            r'\b(how)\s+do\s+you\s+work',
            r'\byour\s+(creator|maker)',
            r'\bhow\s+were\s+you\s+(made|created|built|designed)'
        ]
        
        for pattern in meta_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                return True
                
        return False
        
    def _is_all_libraries_query(self, query):
        """Check if the query is asking about all libraries"""
        patterns = [
            r'\b(what|which|all|list)\s+libraries',
            r'\blibraries\s+(on|at|in)\s+campus',
            r'\bhow\s+many\s+libraries',
            r'\btell\s+me\s+about\s+(the|all)\s+libraries'
        ]
        
        for pattern in patterns:
            if re.search(pattern, query, re.IGNORECASE):
                return True
                
        return False
    
    def _is_building_query(self, query):
        """Check if the query is related to campus buildings"""
        building_patterns = [
            r'\b(building|hall|center|classroom)\b',
            r'\b(where is|find|locate)\s+[a-z\s]+(building|hall|center|classroom)\b',
            r'\b(what|tell me about|describe)\s+[a-z\s]+(building|hall|center)\b',
            r'\b(clb|arb|and|ans)\b' # Common building abbreviations
        ]
        
        for pattern in building_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                return True
                
        # Check for specific building names that might not have building/hall in them
        building_names = [
            "105 classroom", "academic research", "anderson", "alfred a. mckethan",
            "stadium", "animal sciences"
        ]
        
        for name in building_names:
            if name.lower() in query.lower():
                return True
                
        return False
        
    def _detect_intent(self, query):
        """Detect the primary intent of the query"""
        # Handle short responses
        if len(query.strip().split()) <= 2:
            query_lower = query.lower().strip()
            if query_lower in ['yes', 'yeah', 'sure', 'ok', 'okay', 'please', 'yep']:
                return 'affirmative'
            elif query_lower in ['no', 'nope', 'nah']:
                return 'negative'
            else:
                return 'short_response'
        
        # Check against our defined intent patterns
        matched_intents = []
        for intent, pattern in self.intent_patterns.items():
            if pattern.search(query):
                matched_intents.append(intent)
                
        # If multiple intents match, choose the most specific one
        if len(matched_intents) > 1:
            # Prioritization of intents (more specific ones first)
            priority_order = [
                'reserve_room', 'find_website', 'find_coffee', 'find_food', 
                'find_study_space', 'find_materials', 'check_hours', 'find_location', 
                'find_building', 'building_info', 'get_directions', 'check_availability', 
                'get_recommendations', 'discover_offerings', 'compare_libraries', 
                'get_information'
            ]
            
            # Return the highest priority intent that matched
            for intent in priority_order:
                if intent in matched_intents:
                    return intent
                    
        # If exactly one intent matched, return it
        elif len(matched_intents) == 1:
            return matched_intents[0]
        
        # Default to 'get_information' for general queries
        return 'get_information'
        
    def _detect_specific_intents(self, query):
        """Detect specific question intents with improved accuracy"""
        query_lower = query.lower()
        specific_intents = []
        
        # Reserve-specific intent detection
        if any(word in query_lower for word in ['reserve', 'book', 'reservation']):
            if any(word in query_lower for word in ['room', 'space', 'study']):
                specific_intents.append('reserve_room')
        
        # Website-specific intent detection        
        if any(word in query_lower for word in ['website', 'url', 'link', 'online']):
            specific_intents.append('find_website')
        
        # Coffee-specific matching with library context
        if any(word in query_lower for word in ['coffee', 'starbucks', 'cafe']):
            # Extract library reference if exists
            library_words = ['library', 'west', 'marston', 'smathers', 'hsc', 'afa']
            for word in library_words:
                if word in query_lower:
                    specific_intents.append('find_coffee_near_library')
                    break
        
        # Building-specific intent detection
        if self._is_building_query(query_lower):
            if any(word in query_lower for word in ['where', 'find', 'locate', 'get to']):
                specific_intents.append('find_building_location')
            elif any(word in query_lower for word in ['what', 'tell', 'about', 'describe']):
                specific_intents.append('get_building_info')
                
        return specific_intents
        
    def _detect_time_reference(self, query):
        """Detect time references in the query"""
        time_patterns = {
            'today': r'\b(today|tonight|now)\b',
            'tomorrow': r'\b(tomorrow)\b',
            'weekend': r'\b(weekend|saturday|sunday)\b',
            'weekday': r'\b(weekday|monday|tuesday|wednesday|thursday|friday)\b',
            'morning': r'\b(morning)\b',
            'afternoon': r'\b(afternoon)\b',
            'evening': r'\b(evening|night)\b',
            'finals': r'\b(finals|final exams|exam week)\b',
            'break': r'\b(break|vacation|holiday)\b',
            'semester': r'\b(semester|term|fall|spring|summer)\b'
        }
        
        for time_ref, pattern in time_patterns.items():
            if re.search(pattern, query, re.IGNORECASE):
                return time_ref
        
        return None
        
    def _extract_library_mentions(self, query):
        """Extract explicit mentions of libraries"""
        library_mentions = []
        
        # Common library names and patterns
        library_patterns = [
            (r'\b(library west|lib west|west library)\b', 'Library West'),
            (r'\b(marston|science library|msl)\b', 'Marston Science Library'),
            (r'\b(smathers|east|library east)\b', 'Smathers Library'),
            (r'\b(health science|hsc|medical library)\b', 'Health Science Center Library'),
            (r'\b(architecture|fine arts|afa)\b', 'Architecture & Fine Arts Library'),
            (r'\b(education|norman hall)\b', 'Education Library'),
            (r'\b(law|legal|levin)\b', 'Legal Information Center'),
            (r'\b(special collection|area studies)\b', 'Special & Area Studies Collections')
        ]
        
        for pattern, library_name in library_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                library_mentions.append(library_name)
        
        return library_mentions
    
    def _extract_building_mentions(self, query):
        """Extract explicit mentions of campus buildings"""
        building_mentions = []
        
        # Common building names and patterns
        building_patterns = [
            (r'\b(105 classroom|clb)\b', '105 Classroom Building'),
            (r'\b(academic research|arb)\b', 'Academic Research Building'),
            (r'\b(anderson hall|and)\b', 'Anderson Hall'),
            (r'\b(alfred a. mckethan|mckethan stadium)\b', 'Alfred A. McKethan Stadium'),
            (r'\b(animal sciences|ans)\b', 'Animal Sciences Building')
        ]
        
        for pattern, building_name in building_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                building_mentions.append(building_name)
        
        return building_mentions
    
    def _is_followup_question(self, query, conversation_history):
        """Detect if this is likely a follow-up question"""
        # Check if there's conversation history
        if not conversation_history or len(conversation_history) < 2:
            return False
            
        # Short responses are often follow-ups
        if len(query.strip().split()) <= 3:
            return True
            
        # Check for pronouns referring to previous context
        followup_indicators = [
            r'\b(it|its|they|their|there|that|this|those|these)\b',
            r'^(what about|how about|and)\b',
            r'^(what|where|when|how|why|who|which)\b.{1,30}\?$'  # Short questions are often follow-ups
        ]
        
        for pattern in followup_indicators:
            if re.search(pattern, query, re.IGNORECASE):
                return True
        
        return False
        
    def _detect_amenity_type(self, query):
        """Detect if the query is about a campus amenity"""
        query_lower = query.lower()
        
        # Coffee shops
        coffee_terms = ["coffee", "starbucks", "cafe", "café", "latte", "espresso", "cappuccino", "tea"]
        for term in coffee_terms:
            if term in query_lower:
                return "coffee_shops"
        
        # Food locations
        food_terms = ["food", "eat", "restaurant", "dining", "lunch", "dinner", "breakfast", "meal", "snack"]
        for term in food_terms:
            if term in query_lower:
                return "dining_locations"
                
        # Study spots (non-library)
        study_terms = ["24/7", "all night", "late night", "study spot", "newell"]
        for term in study_terms:
            if term in query_lower:
                return "study_spots"
                
        return None

# =============================================================================
# RESPONSE GENERATOR
# =============================================================================

class AdvancedResponseGenerator:
    """Advanced response generator with verification and enhanced output"""
    
    def __init__(self, llm_model=None):
        self.llm = llm_model
        self.response_cache = LRUCache(capacity=100)
        
        # Create template registry
        self.templates = self._init_templates()
        
        # Create quality enhancer
        self.quality_enhancer = ResponseQualityEnhancer()
        
    def _init_templates(self):
        """Initialize response templates for common query types"""
        return {
            'hours': {
                'template': "{library_name} is open from {hours_today} today ({day_of_week}).\n\nRegular hours:\n{all_hours}\n\n{access_restrictions}",
                'required': ['library_name', 'hours_today', 'day_of_week']
            },
            'location': {
                'template': "{library_name} is located at {location}. {additional_info}",
                'required': ['library_name', 'location']
            },
            'meta': {
                'template': "Yes, I'm an AI assistant specifically designed to provide information about the University of Florida's libraries, buildings, and campus resources. I can help with questions about library hours, locations, services, collections, building information, and other UF-related topics. How can I assist you today?",
                'required': []
            },
            'all_libraries': {
                'template': "The University of Florida has several libraries across campus:\n\n{libraries_list}\n\nEach library offers specialized collections, study spaces, and research assistance for their respective disciplines.",
                'required': ['libraries_list']
            },
            'offerings': {
                'template': "{library_name} offers the following resources and services:\n\n{offerings_list}\n\n{additional_info}",
                'required': ['library_name', 'offerings_list']
            },
            'study_spaces': {
                'template': "{library_name} provides these study spaces:\n\n{spaces_list}\n\nCurrent hours: {today_hours}",
                'required': ['library_name', 'spaces_list']
            },
            'coffee_shops': {
                'template': "Here are the Starbucks locations on UF campus:\n\n{coffee_shops_list}\n\n{additional_info}",
                'required': ['coffee_shops_list']
            },
            'dining_locations': {
                'template': "Here are some dining options near UF libraries:\n\n{dining_list}\n\n{additional_info}",
                'required': ['dining_list']
            },
            'hours_exception': {
                'template': "Please note: {library_name} has special hours {exception_date}. {exception_details}\n\nRegular hours are:\n{regular_hours}",
                'required': ['library_name', 'exception_details']
            },
            'website': {
                'template': "The website for {library_name} is: {website_url}",
                'required': ['library_name', 'website_url']
            },
            'reserve_room': {
                'template': "To reserve a study room at {library_name}:\n\n1. Go to {website_url}\n2. Click on 'Study Rooms' or 'Room Reservations'\n3. Sign in with your GatorLink credentials\n4. Select your preferred time and location\n\nImportant information:\n{reservation_details}",
                'required': ['library_name', 'website_url']
            },
            'building_location': {
                'template': "{building_name} is located at {address}. {additional_info}",
                'required': ['building_name', 'address']
            },
            'building_info': {
                'template': "{building_name}{abbreviation_text} is located at {address}. {description}",
                'required': ['building_name', 'address']
            },
            'error': {
                'template': "I apologize, but I encountered an issue while processing your request. Please try asking your question again, perhaps with different wording.",
                'required': []
            }
        }
    
    def generate(self, query, library=None, building=None, query_analysis=None, conversation_history=None, academic_context=None):
        """Generate a response with advanced verification and enhancement"""
        # Start timing for performance tracking
        start_time = time.time()
        
        # Generate cache key based on query and context
        cache_key = f"{query}"
        if library:
            cache_key += f":{library['Library Name']}"
        if building:
            cache_key += f":{building['Building Name']}"
            
        # Check cache for this exact query
        if cache_key in self.response_cache:
            cached_response, metrics = self.response_cache[cache_key]
            # Update metrics with current timestamp
            metrics['cache_hit'] = True
            metrics['response_time'] = time.time() - start_time
            return cached_response, metrics
            
        try:
            # Check for specific intents that need special handling
            specific_intents = query_analysis.get('specific_intents', [])
            
            # Handle library website requests
            if 'find_website' in specific_intents and library:
                website_response = self._generate_website_response(library)
                if website_response:
                    metrics = {
                        'confidence': 0.95,
                        'method': 'template',
                        'template_used': 'website',
                        'library': library
                    }
                    # Cache and return
                    self.response_cache[cache_key] = (website_response, metrics)
                    return website_response, metrics
                    
            # Handle room reservation requests
            if 'reserve_room' in specific_intents and library:
                reservation_response = self._generate_reservation_response(library)
                if reservation_response:
                    metrics = {
                        'confidence': 0.95,
                        'method': 'template',
                        'template_used': 'reserve_room',
                        'library': library
                    }
                    # Cache and return
                    self.response_cache[cache_key] = (reservation_response, metrics)
                    return reservation_response, metrics
                    
            # Handle building location requests
            if 'find_building_location' in specific_intents and building:
                building_location_response = self._generate_building_location_response(building)
                if building_location_response:
                    metrics = {
                        'confidence': 0.95,
                        'method': 'template',
                        'template_used': 'building_location',
                        'building': building
                    }
                    # Cache and return
                    self.response_cache[cache_key] = (building_location_response, metrics)
                    return building_location_response, metrics
                    
            # Handle building info requests
            if 'get_building_info' in specific_intents and building:
                building_info_response = self._generate_building_info_response(building)
                if building_info_response:
                    metrics = {
                        'confidence': 0.95,
                        'method': 'template',
                        'template_used': 'building_info',
                        'building': building
                    }
                    # Cache and return
                    self.response_cache[cache_key] = (building_info_response, metrics)
                    return building_info_response, metrics
            
            # For other query types, use LLM if available
            if self.llm:
                llm_response, llm_metrics = self._generate_llm_response(
                    query, 
                    query_analysis, 
                    library,
                    building,
                    conversation_history, 
                    academic_context
                )
                
                if llm_response:
                    # Post-process and enhance
                    enhanced_response = self._post_process_response(llm_response)
                    
                    # Update metrics
                    llm_metrics['response_time'] = time.time() - start_time
                    llm_metrics['method'] = 'llm'
                    if library:
                        llm_metrics['library'] = library
                    if building:
                        llm_metrics['building'] = building
                    
                    # Cache response
                    self.response_cache[cache_key] = (enhanced_response, llm_metrics)
                    
                    return enhanced_response, llm_metrics
            
            # Try template-based responses as fallback
            template_response, template_metrics = self._generate_template_response(
                query, query_analysis, library, building, conversation_history, academic_context
            )
            
            # If we got a good template response, use it
            if template_response:
                # Update metrics
                template_metrics['response_time'] = time.time() - start_time
                template_metrics['method'] = 'template'
                if library:
                    template_metrics['library'] = library
                if building:
                    template_metrics['building'] = building
                
                # Cache response
                self.response_cache[cache_key] = (template_response, template_metrics)
                
                return template_response, template_metrics
                
            # Fallback response if both methods failed
            fallback_response = "I'm not able to answer that specific question about UF. Could you try rephrasing your question or ask about something like library hours, building locations, or campus services?"
            fallback_metrics = {
                'confidence': 0.3,
                'method': 'fallback',
                'response_time': time.time() - start_time
            }
            
            return fallback_response, fallback_metrics
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            error_response = "I apologize, but I encountered an unexpected error while processing your request. Please try asking your question again, perhaps with different wording."
            error_metrics = {
                'confidence': 0.0,
                'method': 'error',
                'response_time': time.time() - start_time,
                'error': str(e)
            }
            
            return error_response, error_metrics
    
    def _generate_website_response(self, library):
        """Generate a response for website queries"""
        library_name = library.get('Library Name', '')
        website_url = library.get('URL', '')
        
        if not website_url:
            return None
            
        return self.templates['website']['template'].format(
            library_name=library_name,
            website_url=website_url
        )
        
    def _generate_reservation_response(self, library):
        """Generate a response for room reservation queries"""
        library_name = library.get('Library Name', '')
        website_url = library.get('URL', '')
        
        if not website_url:
            return None
            
        # Generate reservation details based on library
        reservation_details = ""
        
        if 'Marston' in library_name:
            reservation_details = "• Reservations are limited to 2 hours per day per group\n• You must have a valid UF ID to use reserved rooms\n• Rooms must be occupied within 15 minutes of reservation time\n• Most rooms have whiteboards and display screens for collaborative work"
        elif 'West' in library_name:
            reservation_details = "• Graduate student rooms are available on the 3rd floor\n• Undergraduate rooms on multiple floors\n• Reservations can be made up to 7 days in advance\n• You must have a valid UF ID to use reserved rooms"
        else:
            reservation_details = "• Most rooms can be reserved for 2 hours\n• Valid UF ID required\n• Reservations typically available 7 days in advance\n• Some rooms have special technology or equipment"
            
        return self.templates['reserve_room']['template'].format(
            library_name=library_name,
            website_url=website_url,
            reservation_details=reservation_details
        )
    
    def _generate_building_location_response(self, building):
        """Generate a response for building location queries"""
        building_name = building.get('Building Name', '')
        address = building.get('Address', '')
        
        if not address:
            return None
            
        # Add contextual information
        additional_info = building.get('Description', '')
        if not additional_info:
            additional_info = "It is located on the University of Florida campus."
            
        return self.templates['building_location']['template'].format(
            building_name=building_name,
            address=address,
            additional_info=additional_info
        )
        
    def _generate_building_info_response(self, building):
        """Generate a response for building info queries"""
        building_name = building.get('Building Name', '')
        address = building.get('Address', '')
        description = building.get('Description', 'No additional information is available for this building.')
        abbreviation = building.get('Abbreviation', '')
        
        # Format abbreviation text if available
        abbreviation_text = f" ({abbreviation})" if abbreviation else ""
        
        return self.templates['building_info']['template'].format(
            building_name=building_name,
            abbreviation_text=abbreviation_text,
            address=address,
            description=description
        )
    
    def _generate_template_response(self, query, query_analysis, library, building, conversation_history=None, academic_context=None):
        """Generate response using templates for common query types"""
        # Initialize metrics
        metrics = {
            'confidence': 0.0,
            'template_used': None
        }
        
        # Handle meta-questions about the AI
        if query_analysis.get('is_meta_question', False):
            metrics['confidence'] = 0.95
            metrics['template_used'] = 'meta'
            return self.templates['meta']['template'], metrics
            
        # Handle requests for all libraries
        if query_analysis.get('is_all_libraries_query', False):
            libraries_list = self._generate_all_libraries_list()
            metrics['confidence'] = 0.95
            metrics['template_used'] = 'all_libraries'
            return self.templates['all_libraries']['template'].format(
                libraries_list=libraries_list
            ), metrics
            
        # Handle amenity queries
        amenity_type = query_analysis.get('amenity_type')
        if amenity_type and amenity_type in ['coffee_shops', 'dining_locations']:
            template_key = amenity_type
            if template_key in self.templates:
                amenity_content = self._generate_amenity_content(
                    amenity_type, library, query_analysis
                )
                if amenity_content:
                    metrics['confidence'] = 0.9
                    metrics['template_used'] = template_key
                    return self.templates[template_key]['template'].format(
                        **amenity_content
                    ), metrics
                    
        # Building-specific templates
        if building:
            building_name = building.get('Building Name', '')
            
            # Handle building location queries
            if ('location' in query_analysis.get('categories', []) or 
                query_analysis.get('intent') == 'find_building' or 
                query_analysis.get('question_type') == 'where'):
                
                address = building.get('Address', '')
                additional_info = building.get('Description', '')
                
                metrics['confidence'] = 0.9
                metrics['template_used'] = 'building_location'
                return self.templates['building_location']['template'].format(
                    building_name=building_name,
                    address=address,
                    additional_info=additional_info
                ), metrics
                
            # Handle building info queries
            if ('general' in query_analysis.get('categories', []) or 
                query_analysis.get('intent') == 'building_info' or 
                query_analysis.get('question_type') == 'what'):
                
                address = building.get('Address', '')
                description = building.get('Description', 'No additional information is available for this building.')
                abbreviation = building.get('Abbreviation', '')
                
                # Format abbreviation text if available
                abbreviation_text = f" ({abbreviation})" if abbreviation else ""
                
                metrics['confidence'] = 0.9
                metrics['template_used'] = 'building_info'
                return self.templates['building_info']['template'].format(
                    building_name=building_name,
                    abbreviation_text=abbreviation_text,
                    address=address,
                    description=description
                ), metrics
                    
        # Library-specific templates
        if library:
            library_name = library.get('Library Name', '')
            
            # Handle hours query
            if ('hours' in query_analysis.get('categories', []) or 
                query_analysis.get('intent') == 'check_hours'):
                
                # Check for special hours from academic calendar
                has_special_hours = False
                exception_details = None
                
                if academic_context:
                    today_str = datetime.now().strftime('%Y-%m-%d')
                    if academic_context.get('schedule_exception') and today_str in academic_context.get('schedule_exception', {}):
                        has_special_hours = True
                        exception = academic_context['schedule_exception'][today_str]
                        if 'all' in exception:
                            exception_details = exception['all']
                        elif library_name in exception:
                            exception_details = exception[library_name]
                            
                    # Check for extended hours
                    elif academic_context.get('extended_hours') and library_name in academic_context['extended_hours'].get('libraries', {}):
                        has_special_hours = True
                        exception_details = f"Extended hours during {academic_context['extended_hours']['period']}: {academic_context['extended_hours']['libraries'][library_name]}"
                
                # If special hours apply, use that template
                if has_special_hours and exception_details:
                    regular_hours = ""
                    if 'Hours' in library:
                        for day, hours in library['Hours'].items():
                            regular_hours += f"• {day}: {hours}\n"
                    
                    metrics['confidence'] = 0.95
                    metrics['template_used'] = 'hours_exception'
                    return self.templates['hours_exception']['template'].format(
                        library_name=library_name,
                        exception_date="today",
                        exception_details=exception_details,
                        regular_hours=regular_hours.strip()
                    ), metrics
                
                # Otherwise use standard hours template
                # Get today's day of week
                today = datetime.now().strftime('%A')
                
                # Get hours for today
                if 'Hours' in library and today in library['Hours']:
                    hours_today = library['Hours'][today]
                else:
                    hours_today = "hours not available"
                
                # Format all hours
                all_hours = ""
                if 'Hours' in library:
                    for day, hours in library['Hours'].items():
                        all_hours += f"• {day}: {hours}\n"
                
                access_restrictions = ""
                if "Building access after 10pm limited" in library.get('Special Notes', ''):
                    access_restrictions = "Please note that building access after 10pm is limited to users with an active UF ID or Santa Fe College ID."
                
                metrics['confidence'] = 0.95
                metrics['template_used'] = 'hours'
                return self.templates['hours']['template'].format(
                    library_name=library_name,
                    hours_today=hours_today,
                    day_of_week=today,
                    all_hours=all_hours.strip(),
                    access_restrictions=access_restrictions
                ), metrics
                
            # Handle location query
            if ('location' in query_analysis.get('categories', []) or 
                query_analysis.get('intent') == 'find_location' or 
                query_analysis.get('question_type') == 'where'):
                
                location = library.get('Location', '')
                additional_info = ''
                
                # Add contextual information based on library
                if library_name == "Library West":
                    additional_info = "It's situated at the corner of West University Avenue and 15th Street, in the heart of UF's campus."
                elif library_name == "Marston Science Library":
                    additional_info = "It's situated in the central part of UF's campus, making it easily accessible from most classroom buildings."
                elif library_name == "Smathers Library":
                    additional_info = "It's located on the Plaza of the Americas, in the historic part of campus."
                
                metrics['confidence'] = 0.9
                metrics['template_used'] = 'location'
                return self.templates['location']['template'].format(
                    library_name=library_name,
                    location=location,
                    additional_info=additional_info
                ), metrics
            
            # Handle offerings query
            if ('offerings' in query_analysis.get('categories', []) or 
                'services' in query_analysis.get('categories', []) or 
                query_analysis.get('intent') == 'discover_offerings'):
                
                # Get all resources
                resources = []
                for resource_type in ['Resources', 'Services', 'Technology']:
                    if resource_type in library:
                        resources.extend(library[resource_type])
                
                # If no resources found, return None to use LLM
                if not resources:
                    return None, metrics
                
                # Format resources list
                offerings_list = ""
                for resource in resources[:10]:  # Limit to top 10
                    offerings_list += f"• {resource}\n"
                    
                additional_info = f"For more information, contact {library.get('Email', '')} or visit their website at {library.get('URL', '')}."
                
                metrics['confidence'] = 0.85
                metrics['template_used'] = 'offerings'
                return self.templates['offerings']['template'].format(
                    library_name=library_name,
                    offerings_list=offerings_list.strip(),
                    additional_info=additional_info
                ), metrics
            
            # Handle study spaces query
            if ('study_spaces' in query_analysis.get('categories', []) or 
                query_analysis.get('intent') == 'find_study_space'):
                
                # Get study spaces
                study_spaces = []
                if 'Study Spaces' in library:
                    study_spaces = library['Study Spaces']
                
                # If no study spaces found, return None to use LLM
                if not study_spaces:
                    return None, metrics
                    
                # Format study spaces list
                spaces_list = ""
                for space in study_spaces:
                    spaces_list += f"• {space}\n"
                
                # Get today's hours
                today = datetime.now().strftime('%A')
                today_hours = "unavailable"
                if 'Hours' in library and today in library['Hours']:
                    today_hours = library['Hours'][today]
                
                metrics['confidence'] = 0.85
                metrics['template_used'] = 'study_spaces'
                return self.templates['study_spaces']['template'].format(
                    library_name=library_name,
                    spaces_list=spaces_list.strip(),
                    today_hours=today_hours
                ), metrics
        
        # For other query types, use LLM
        return None, metrics
        
    def _generate_amenity_content(self, amenity_type, library, query_analysis):
        """Generate content for amenity templates"""
        if amenity_type == "coffee_shops":
            # Prepare coffee shops content
            coffee_shops_list = ""
            
            # Get coffee shops data from CAMPUS_AMENITIES
            coffee_shops = CAMPUS_AMENITIES.get('coffee_shops', [])
            
            # Filter by nearest library if specified
            nearest_library = library.get('Library Name', '') if library else None
            if nearest_library and any(shop for shop in coffee_shops if shop.get('nearest_library') == nearest_library):
                filtered_shops = [shop for shop in coffee_shops if shop.get('nearest_library') == nearest_library]
            else:
                filtered_shops = coffee_shops
                
            # Generate list content
            for shop in filtered_shops:
                name = shop.get('name', '')
                location = shop.get('location', '')
                
                # Get today's hours
                today = datetime.now().strftime('%A')
                hours_today = "hours unavailable"
                if 'hours' in shop and today in shop['hours']:
                    hours_today = shop['hours'][today]
                
                coffee_shops_list += f"• {name}: Located at {location}. Hours today: {hours_today}\n\n"
            
            # Add additional info
            additional_info = ""
            if nearest_library:
                additional_info = f"These coffee options are convenient to {nearest_library}."
            else:
                additional_info = "All Starbucks locations accept Gator Dining Dollars and major credit cards."
                
            return {
                'coffee_shops_list': coffee_shops_list.strip(),
                'additional_info': additional_info
            }
            
        elif amenity_type == "dining_locations":
            # Prepare dining locations content
            dining_list = ""
            
            # Get dining locations data
            dining_locations = CAMPUS_AMENITIES.get('dining_locations', [])
            
            # Filter by nearest library if specified
            nearest_library = library.get('Library Name', '') if library else None
            if nearest_library and any(loc for loc in dining_locations if loc.get('nearest_library') == nearest_library):
                filtered_locations = [loc for loc in dining_locations if loc.get('nearest_library') == nearest_library]
            else:
                filtered_locations = dining_locations
                
            # Generate list content
            for location in filtered_locations:
                name = location.get('name', '')
                loc = location.get('location', '')
                
                # Get today's hours
                today = datetime.now().strftime('%A')
                hours_today = "hours unavailable"
                if 'hours' in location and today in location['hours']:
                    hours_today = location['hours'][today]
                
                dining_list += f"• {name}: Located at {loc}. Hours today: {hours_today}\n\n"
                
            # Add additional info
            additional_info = ""
            if nearest_library:
                additional_info = f"These dining options are all within walking distance of {nearest_library}."
            else:
                additional_info = "Most dining locations accept Gator Dining Dollars and major credit cards."
                
            return {
                'dining_list': dining_list.strip(),
                'additional_info': additional_info
            }
            
        # Return None for unsupported amenity types
        return None
        
    def _generate_all_libraries_list(self):
        """Generate a formatted list of all libraries"""
        libraries_list = "• Library West: Focuses on humanities, business, and social sciences\n"
        libraries_list += "• Marston Science Library: Specializes in science, engineering, technology, and math\n"
        libraries_list += "• Smathers Library: Houses special collections, archives, and rare materials\n"
        libraries_list += "• Health Science Center Library: Serves medical and health science disciplines\n"
        libraries_list += "• Architecture & Fine Arts Library: Supports art, design, and architecture programs\n"
        libraries_list += "• Education Library: Resources for education and teaching\n"
        libraries_list += "• Legal Information Center: Law and legal resources"
        return libraries_list
        
    def _generate_llm_response(self, query, query_analysis, library=None, building=None, conversation_history=None, academic_context=None):
        """Generate a response using the LLM model"""
        if not self.llm:
            # If no LLM is available, return None to use fallback
            return None, {'confidence': 0.0}
        
        # Create optimized prompt for LLaMA 3
        prompt = self._generate_optimized_prompt(
            query, query_analysis, library, building, conversation_history, academic_context
        )
        
        # Determine appropriate generation parameters based on query
        params = self._get_generation_params(query_analysis)
        
        try:
            # Generate response with LLM
            result = self.llm(
                prompt, 
                max_tokens=params['max_tokens'],
                temperature=params['temperature'],
                top_p=params['top_p'],
                top_k=params['top_k'],
                repeat_penalty=params['repeat_penalty'],
                stop=["<|user|>", "<|system|>"]
            )
            
            # Extract response text
            response = result["choices"][0]["text"].strip()
            
            # Calculate confidence based on response properties
            confidence = self._calculate_response_confidence(
                response, query, query_analysis, library, building
            )
            
            return response, {'confidence': confidence}
            
        except Exception as e:
            logger.error(f"Error generating LLM response: {e}")
            return None, {'confidence': 0.0, 'error': str(e)}
            
    def _generate_optimized_prompt(self, query, query_analysis, library=None, building=None, conversation_history=None, academic_context=None):
        """Generate an optimized prompt for LLaMA 3"""
        # Create system message
        system_message = """<|system|>
You are the UF Assistant, an expert on University of Florida. 
Provide accurate, helpful information about campus buildings, libraries, resources, and services.
Your responses should be: (1) factual and based only on the provided UF data, 
(2) concise and directly answering the user's question, (3) helpful for students 
and faculty navigating UF campus, and (4) conversational but professional in tone.
</|system|>
"""
        
        # Build context section
        context = "<|system|>\nRELEVANT UF INFORMATION:\n"
        
        # Add library context if relevant
        if library:
            # Add specific library information
            library_name = library.get('Library Name', '')
            context += f"Library: {library_name}\n"
            context += f"Location: {library.get('Location', '')}\n"
            
            # Hours
            if 'Hours' in library:
                context += "Hours:\n"
                for day, hours in library['Hours'].items():
                    context += f"- {day}: {hours}\n"
            
            # Tags/focus
            if 'Tags' in library:
                context += f"Focus areas: {library.get('Tags', '')}\n"
                
            # Special notes
            if 'Special Notes' in library and library['Special Notes']:
                context += f"Special Notes: {library['Special Notes']}\n"
                
            # Add key resources (limit to reduce token usage)
            resource_types = ['Resources', 'Study Spaces', 'Collections', 'Technology', 'Services']
            for rt in resource_types:
                if rt in library and library[rt]:
                    # Limit to 5 items per category
                    items = library[rt][:5]
                    context += f"\n{rt}:\n"
                    for item in items:
                        context += f"- {item}\n"
                        
            # Contact info
            contact_info = []
            if library.get('Phone', ''):
                contact_info.append(f"Phone: {library.get('Phone', '')}")
            if library.get('Email', ''):
                contact_info.append(f"Email: {library.get('Email', '')}")
            if library.get('URL', ''):
                contact_info.append(f"Website: {library.get('URL', '')}")
                
            if contact_info:
                context += "\nContact Information:\n"
                for info in contact_info:
                    context += f"- {info}\n"
        
        # Add building context if relevant
        if building:
            building_name = building.get('Building Name', '')
            abbr = building.get('Abbreviation', '')
            
            context += f"Building: {building_name}\n"
            if abbr:
                context += f"Abbreviation: {abbr}\n"
            if building.get('Building Number', ''):
                context += f"Building Number: {building.get('Building Number', '')}\n"
            if building.get('Address', ''):
                context += f"Address: {building.get('Address', '')}\n"
            if building.get('Description', ''):
                context += f"Description: {building.get('Description', '')}\n"
                
        # Add general UF information if no specific entity
        if not library and not building:
            # Determine what kind of information to include based on query
            if query_analysis.get('is_building_query'):
                # Add general buildings information
                context += "UF has numerous buildings across campus. Some notable ones include:\n"
                for i, building_data in enumerate(CAMPUS_BUILDINGS_DATA[:5]):  # Limit to 5 for brevity
                    name = building_data.get('Building Name', '')
                    abbr = building_data.get('Abbreviation', '')
                    desc = building_data.get('Description', '')
                    
                    context += f"- {name}"
                    if abbr:
                        context += f" ({abbr})"
                    if desc:
                        context += f": {desc}"
                    context += "\n"
                
            elif query_analysis.get('is_all_libraries_query'):
                # Add brief library information
                context += "UF has several libraries across campus, including:\n"
                for lib_data in LIBRARY_DATA[:5]:  # Limit to 5 main libraries
                    name = lib_data.get('Library Name', '')
                    tags = lib_data.get('Tags', '')
                    
                    context += f"- {name}"
                    if tags:
                        context += f": Focuses on {tags}"
                    context += "\n"
                    
            else:
                # Add general UF information
                context += "The University of Florida (UF) is a major public research university in Gainesville, Florida. "
                context += "The campus includes various libraries, academic buildings, research facilities, and student resources. "
                context += "UF offers numerous academic programs and is known for its research activities.\n"
                
        # Add academic calendar context if available
        if academic_context:
            context += "\nACADEMIC CONTEXT:\n"
            
            # Current term
            if academic_context.get('current_term'):
                context += f"Current term: {academic_context['current_term']}\n"
                
            # Special events
            if academic_context.get('current_event'):
                context += f"Current event: {academic_context['current_event']}\n"
                
            # Schedule exceptions
            if academic_context.get('schedule_exception'):
                for date, exception in academic_context['schedule_exception'].items():
                    # Check if it's today or upcoming
                    today = datetime.now().strftime('%Y-%m-%d')
                    if date >= today:
                        if isinstance(exception, dict):
                            for loc, hours in exception.items():
                                context += f"- {date}, {loc}: {hours}\n"
                        else:
                            context += f"- {date}: {exception}\n"
                        
            # Extended hours
            if academic_context.get('extended_hours'):
                extended = academic_context['extended_hours']
                context += f"\nExtended hours for {extended['period']}:\n"
                for lib, hours in extended.get('libraries', {}).items():
                    context += f"- {lib}: {hours}\n"
                    
        context += "</|system|>\n"
        
        # Add conversational context if available
        if conversation_history and len(conversation_history) > 0:
            # Get the last 3 exchanges (up to 6 messages)
            recent_history = conversation_history[-min(6, len(conversation_history)):]
            
            for msg in recent_history:
                role = msg.get('role', '')
                content = msg.get('content', '')
                
                if role == 'user':
                    context += f"<|user|>\n{content}\n"
                elif role == 'assistant':
                    context += f"<|assistant|>\n{content}\n"
        
        # Add any special handling guidance based on query analysis
        intent = query_analysis.get('intent', '')
        specific_intents = query_analysis.get('specific_intents', [])
        
        if intent or specific_intents:
            system_guidance = ""
            
            if 'reserve_room' in specific_intents:
                system_guidance = "Explain the room reservation process in detail, including how to access the system, time limits, and requirements."
            elif 'find_website' in specific_intents:
                system_guidance = "Provide the website URL along with any helpful information about navigating the site."
            elif intent in ['find_location', 'find_building']:
                system_guidance = "Give the exact address and helpful navigation tips."
            elif intent == 'check_hours':
                system_guidance = "Provide today's hours first, then full weekly schedule if relevant."
            elif intent == 'find_study_space':
                system_guidance = "Describe available study areas, features, noise levels, and reservation requirements."
            elif intent in ['find_coffee', 'find_food']:
                system_guidance = "Provide detailed information about nearby options with hours."
            elif intent == 'building_info':
                system_guidance = "Provide detailed information about the building's purpose, departments housed there, and relevant features."
                
            if system_guidance:
                context += f"<|system|>\nGUIDANCE: {system_guidance}</|system|>\n"
        
        # Add the current query
        prompt = f"{system_message}\n{context}<|user|>\n{query}\n<|assistant|>"
        
        return prompt
        
    def _get_generation_params(self, query_analysis):
        """Get appropriate generation parameters based on query type"""
        # Base parameters
        params = {
            'max_tokens': 800,
            'temperature': 0.7,
            'top_p': 0.9,
            'top_k': 40,
            'repeat_penalty': 1.1
        }
        
        # Adjust based on query intent
        intent = query_analysis.get('intent', '')
        specific_intents = query_analysis.get('specific_intents', [])
        
        # Special handling for specific intents
        if 'reserve_room' in specific_intents or 'find_website' in specific_intents:
            # More precise for factual information
            params['temperature'] = 0.3
            params['top_p'] = 0.95
            params['repeat_penalty'] = 1.2
            
        elif intent in ['check_hours', 'find_location', 'find_building']:
            # More deterministic for factual queries
            params['temperature'] = 0.3
            params['top_p'] = 0.95
            params['repeat_penalty'] = 1.2
            
        elif intent in ['get_information', 'discover_offerings', 'building_info']:
            # Balanced for informational content
            params['temperature'] = 0.6
            params['max_tokens'] = 1000  # Allow longer responses for information
            
        elif intent in ['get_recommendations', 'compare_libraries']:
            # More creative for suggestions
            params['temperature'] = 0.75
            params['top_p'] = 0.85
            
        # Adjust for short queries (likely follow-ups)
        if query_analysis.get('is_followup', False):
            params['max_tokens'] = 500  # Shorter responses for follow-ups
            
        return params
        
    def _calculate_response_confidence(self, response, query, query_analysis, library=None, building=None):
        """Calculate confidence score for a generated response"""
        # Start with base confidence
        confidence = 0.7
        
        # Check for question-answer alignment
        if query_analysis.get('question_type') == 'where' and ('located at' in response or 'address is' in response):
            confidence += 0.1
        elif query_analysis.get('question_type') == 'when' and re.search(r'\d+(?:am|pm|AM|PM)', response):
            confidence += 0.1
        elif query_analysis.get('question_type') == 'what' and ('is a' in response or 'houses' in response or 'contains' in response):
            confidence += 0.1
            
        # Check for entity name inclusion
        if library and library.get('Library Name', '') in response:
            confidence += 0.05
        if building and building.get('Building Name', '') in response:
            confidence += 0.05
            
        # Check for specific query terms in response
        query_words = set(query.lower().split())
        important_words = [w for w in query_words if len(w) > 3 and w not in ['what', 'where', 'when', 'how', 'the', 'and', 'for', 'are', 'does', 'about']]
        
        matched_words = sum(1 for word in important_words if word in response.lower())
        if important_words:
            word_match_score = matched_words / len(important_words)
            confidence += word_match_score * 0.1
            
        # Check for formatting quality
        if '•' in response or re.search(r'\n\d+\.', response):
            confidence += 0.05  # Well-formatted lists
            
        # Penalize very short or very long responses
        response_length = len(response.split())
        if response_length < 20:
            confidence -= 0.1  # Too short
        elif response_length > 500:
            confidence -= 0.1  # Too long
            
        # Cap confidence
        return min(max(confidence, 0.3), 0.95)
        
    def _post_process_response(self, response):
        """Clean up and format the response"""
        # Remove repetitive signoffs
        common_endings = [
            "Let me know if you have any other questions or need further assistance.",
            "Let me know if you have any other questions.",
            "Feel free to ask if you have any other questions.",
            "I hope this helps!",
            "I hope this information helps.",
            "Is there anything else I can help you with?",
            "Have a great day and happy learning!",
            "Have a great day!",
            "Good luck with your studies!",
            "Go Gators!"
        ]
        
        for ending in common_endings:
            if response.endswith(ending):
                response = response[:-len(ending)].strip()
        
        # Remove anything after assistant marker which appears in some outputs
        if "<|assistant|>" in response:
            response = response.split("<|assistant|>")[0].strip()
            
        # Format lists consistently
        lines = response.split('\n')
        formatted_lines = []
        
        for line in lines:
            # Standardize bullet points
            if re.match(r'\s*[-*]\s+', line):
                formatted_line = re.sub(r'\s*[-*]\s+', '• ', line)
                formatted_lines.append(formatted_line)
            else:
                formatted_lines.append(line)
                
        response = '\n'.join(formatted_lines)
        
        # Standardize hours format
        hours_pattern = r'(\d{1,2}(?::\d{2})?(?:am|pm|AM|PM))\s*-\s*(\d{1,2}(?::\d{2})?(?:am|pm|AM|PM))'
        
        def format_hours(match):
            start, end = match.groups()
            return f"{start} - {end}"
            
        response = re.sub(hours_pattern, format_hours, response)
        
        # Replace any placeholder date references with actual values
        today = datetime.now()
        response = response.replace("{day_of_week}", today.strftime('%A'))
        response = response.replace("{date}", today.strftime('%B %d, %Y'))
        
        return response

class ResponseQualityEnhancer:
    """Enhances response quality with better formatting and contextual additions"""
    
    def __init__(self):
        self.formatting_patterns = {
            'hours': r'(\d{1,2}(?::\d{2})?(?:am|pm|AM|PM))\s*-\s*(\d{1,2}(?::\d{2})?(?:am|pm|AM|PM))',
            'lists': r'(?:\n\s*[-•*]\s+.+){2,}',
            'locations': r'\b\d+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:\s+(?:Rd|Dr|St|Ave))?\b',
            'urls': r'(https?://[^\s]+)'
        }
        
    def enhance(self, response, query_analysis=None, with_citations=False):
        """Enhance response quality with improved formatting"""
        # Improve text formatting
        enhanced = self._improve_formatting(response)
        
        # Add day-awareness
        enhanced = self._add_day_awareness(enhanced)
        
        # Add helpful contextual information
        if query_analysis:
            enhanced = self._add_contextual_info(enhanced, query_analysis)
        
        return enhanced
        
    def _improve_formatting(self, response):
        """Improve text formatting for readability"""
        # Format library hours consistently
        def format_hours(match):
            # Standardize hours format
            start, end = match.groups()
            return f"{start} - {end}"
            
        response = re.sub(self.formatting_patterns['hours'], format_hours, response)
        
        # Ensure lists are properly formatted with consistent bullets
        if re.search(self.formatting_patterns['lists'], response):
            lines = response.split('\n')
            formatted_lines = []
            
            for line in lines:
                if re.match(r'\s*[-•*]\s+', line):
                    # Standardize bullet points
                    formatted_line = re.sub(r'\s*[-•*]\s+', '• ', line)
                    formatted_lines.append(formatted_line)
                else:
                    formatted_lines.append(line)
                    
            response = '\n'.join(formatted_lines)
            
        # Format URLs as proper links
        def format_url(match):
            url = match.group(1)
            # Remove trailing periods that might be part of URLs
            if url.endswith('.'):
                url = url[:-1]
                return f"{url}."
            return url
            
        response = re.sub(self.formatting_patterns['urls'], format_url, response)
        
        return response
        
    def _add_day_awareness(self, response):
        """Add day-specific awareness to responses"""
        today = datetime.now()
        current_day = today.strftime('%A')
        tomorrow = (today + timedelta(days=1)).strftime('%A')
        
        # Replace generic references with specific days
        response = response.replace("today", f"today ({current_day})")
        response = response.replace("tomorrow", f"tomorrow ({tomorrow})")
        
        # Add current time context for hours
        if "Hours" in response and "today" in response.lower():
            current_time = today.strftime('%-I:%M%p').lower()
            
            # Only add if not already present
            if "current time" not in response.lower():
                time_context = f"\n\nThe current time is {current_time}."
                
                # Check if we need to append or insert
                if response.endswith((".", "!", "?")):
                    response += time_context
                else:
                    response += "." + time_context
        
        return response
        
    def _add_contextual_info(self, response, query_analysis):
        """Add helpful contextual information based on query type"""
        intent = query_analysis.get('intent', '')
        specific_intents = query_analysis.get('specific_intents', [])
        
        # Add extra information based on intent
        if intent == 'check_hours' and 'after 10pm' not in response and 'Library West' in response:
            # Add access restriction reminder for late hours
            if not response.endswith((".", "!", "?")):
                response += "."
            response += "\n\nRemember that building access after 10pm requires an active UF ID or Santa Fe College ID."
            
        elif intent == 'find_study_space' and 'reserve' in response and 'how to reserve' not in response.lower():
            # Add reservation tip
            reservation_tip = "\n\nTip: Group study rooms can be reserved up to 7 days in advance through the library website."
            
            # Only add if not already similar information included
            if 'reserve' in response.lower() and 'reservation' in response.lower() and 'website' not in response.lower():
                if not response.endswith((".", "!", "?")):
                    response += "."
                response += reservation_tip
                
        elif intent == 'find_location' and any(lib in response for lib in ['Marston Science Library', 'Library West']) and 'parking' not in response.lower():
            # Add parking tip for main libraries
            if 'Marston Science Library' in response:
                parking_tip = "\n\nParking tip: The Reitz Union parking garage and the Newell Drive garage are closest to Marston Science Library."
            else:  # Library West
                parking_tip = "\n\nParking tip: The Newell Drive garage is the closest parking to Library West."
                
            if not response.endswith((".", "!", "?")):
                response += "."
            response += parking_tip
            
        elif intent == 'find_building' and 'classroom' in response.lower() and 'classes' not in response.lower():
            # Add classroom usage tip
            classroom_tip = "\n\nTip: Classroom schedules are usually posted outside each room, or you can check the UF Schedule of Courses for class locations."
            
            if not response.endswith((".", "!", "?")):
                response += "."
            response += classroom_tip
            
        # Add website information for website queries
        if 'find_website' in specific_intents and 'http' not in response:
            # Try to find library website
            for library in LIBRARY_DATA:
                if library['Library Name'] in response and 'URL' in library:
                    website_info = f"\n\nWebsite: {library['URL']}"
                    if not response.endswith((".", "!", "?")):
                        response += "."
                    response += website_info
                    break
            
        return response

class LLaMA3OptimizedConfig:
    """Custom configuration for LLaMA 3 8B model with memory optimization"""
    
    def __init__(self, model_path):
        """Initialize with model path and optimal settings"""
        self.model_path = model_path
        
        # Optimized settings for LLaMA 3 8B
        self.settings = {
            # General settings
            'n_ctx': 4096,            # Context window size
            'n_batch': 512,           # Batch size for prompt processing
            'n_threads': 8,           # CPU thread count
            
            # Model efficiency settings
            'n_gpu_layers': 35,       # Number of layers to offload to GPU
            'main_gpu': 0,            # Main GPU device
            'tensor_split': None,     # No tensor splitting needed for 8B model
            'rope_freq_base': 10000,  # Base frequency for RoPE embeddings
            'rope_freq_scale': 1.0    # Scale for RoPE frequency base
        }
        
    def get_inference_params(self, query_type='general'):
        """Get inference parameters optimized for specific query type"""
        # Base parameters
        params = {
            'temp': 0.7,              # Temperature
            'top_p': 0.9,             # Top-p sampling
            'top_k': 40,              # Top-k sampling 
            'repeat_penalty': 1.1,    # Repetition penalty
            'max_tokens': 800         # Maximum tokens to generate
        }
        
        # Adjust based on query type
        if query_type == 'factual':
            params['temp'] = 0.3      # Low temperature for factual answers
            params['top_p'] = 0.95    # Higher precision
            params['repeat_penalty'] = 1.2  # Stronger repetition penalty
            
        elif query_type == 'creative':
            params['temp'] = 0.8      # Higher temperature for creative responses
            params['top_p'] = 0.85    # More variety
            params['repeat_penalty'] = 1.05  # Lower repetition penalty
            
        elif query_type == 'technical':
            params['temp'] = 0.3      # Low temperature for technical precision
            params['top_p'] = 0.97    # Higher precision
            params['repeat_penalty'] = 1.15  # Moderate repetition penalty
            
        return params
        
    def initialize_model(self):
        """Initialize the LLaMA model with optimal settings"""
        if not Llama:
            logger.error("LLaMA library not available")
            return None
            
        try:
            # Determine if GPU is available
            gpu_available = torch and torch.cuda.is_available()
            n_gpu_layers = self.settings['n_gpu_layers'] if gpu_available else 0
            
            if gpu_available:
                logger.info("GPU detected - enabling GPU acceleration")
            else:
                logger.info("No GPU detected - using CPU only")
                
            # Initialize model with settings
            model = Llama(
                model_path=self.model_path,
                n_ctx=self.settings['n_ctx'],
                n_batch=self.settings['n_batch'],
                n_threads=self.settings['n_threads'],
                n_gpu_layers=n_gpu_layers,
                verbose=False
            )
            
            return model
            
        except Exception as e:
            logger.error(f"Failed to initialize LLaMA model: {e}")
            return None

class AcademicCalendarContext:
    """Provides awareness of UF academic calendar for contextually relevant responses"""
    
    def __init__(self):
        """Initialize with academic calendar data"""
        self.calendar_data = ACADEMIC_CALENDAR
        self.current_term = self._determine_current_term()
        self.upcoming_events = self._get_upcoming_events()
        
    def _determine_current_term(self):
        """Determine the current academic term"""
        today_str = datetime.now().strftime('%Y-%m-%d')
        
        for term, dates in self.calendar_data['terms'].items():
            if dates['start'] <= today_str <= dates['end']:
                return term
                
        return None
        
    def _get_upcoming_events(self):
        """Get upcoming academic calendar events"""
        today = datetime.now().date()
        upcoming = []
        
        for event, dates in self.calendar_data['events'].items():
            event_start = datetime.strptime(dates['start'], '%Y-%m-%d').date()
            
            # If this event is in the future and within 14 days
            if event_start > today and (event_start - today).days <= 14:
                upcoming.append({
                    'event': event,
                    'start_date': dates['start'],
                    'days_until': (event_start - today).days
                })
                
        # Sort by days until
        upcoming.sort(key=lambda x: x['days_until'])
        
        return upcoming
        
    def get_current_context(self):
        """Get current academic calendar context"""
        today_str = datetime.now().strftime('%Y-%m-%d')
        
        # Check if we're in any special event period
        current_event = None
        for event, dates in self.calendar_data['events'].items():
            if dates['start'] <= today_str <= dates['end']:
                current_event = event
                break
                
        # Check for schedule exceptions
        schedule_exception = None
        if today_str in self.calendar_data['library_schedule_exceptions']:
            schedule_exception = self.calendar_data['library_schedule_exceptions'][today_str]
        
        # Check if we're in extended hours period
        extended_hours = None
        for period, info in self.calendar_data['extended_hours'].items():
            if info['start'] <= today_str <= info['end']:
                extended_hours = {
                    'period': period,
                    'libraries': info['libraries']
                }
                break
                
        return {
            'date': today_str,
            'current_term': self.current_term,
            'current_event': current_event,
            'schedule_exception': schedule_exception,
            'extended_hours': extended_hours,
            'upcoming_events': self.upcoming_events
        }

# =============================================================================
# ENHANCED UF ASSISTANT
# =============================================================================

class EnhancedUFAssistant:
    """Enhanced UF Assistant with comprehensive university knowledge"""
    
    def __init__(self, model_path, use_gpu=False):
        """Initialize the assistant with all enhanced components"""
        # Start timing for initialization
        init_start_time = time.time()
        
        # Configure logger for initialization tracking
        logger.info(f"Initializing Enhanced UF Assistant with model: {model_path}")
        
        # Initialize LLaMA 3 model with optimized configuration
        llama_config = LLaMA3OptimizedConfig(model_path)
        self.llm = llama_config.initialize_model()
        if self.llm:
            logger.info("[OK] Successfully initialized LLaMA 3 model")
        else:
            logger.warning("[WARNING] Failed to load LLaMA model - some features will be limited")
        
        # Initialize embedding model
        self.embedding_model = self._init_embedding_model()
        if self.embedding_model:
            logger.info("[OK] Successfully initialized embedding model")
        else:
            logger.warning("[WARNING] No embedding model available - semantic search will be disabled")
        
        # Initialize NLP model
        self.nlp_model = self._init_nlp_model()
        if self.nlp_model:
            logger.info("[OK] Successfully initialized NLP model")
        else:
            logger.warning("[WARNING] No NLP model available - some linguistic features will be limited")
        
        # Load campus buildings data
        self.campus_buildings_data = load_campus_buildings_data()
        self.club_data = load_clubs_data()
        self.event_data = load_events_data()
        self.courses_data = load_courses_data()
        self.majors_data = load_majors_data()
        self.programs_data = load_programs_data()
        self.hallinfo_data = load_hallinfo_data()
        self.housinglinks_data = load_housinglinks_data()
        self.libraries_data = load_libraries_data()
        self.mainufpages_links_data = load_mainufpages_links_data()
        self.mainufpages_mainufdata_data = load_mainufpages_mainufdata_data()
        self.tuition_data = load_tuition_data()
        
        # Initialize enhanced components
        self.library_knowledge = EnhancedKnowledgeRetrieval(LIBRARY_DATA, self.embedding_model)
        logger.info("[OK] Initialized library knowledge retrieval system")
        
        self.buildings_knowledge = CampusBuildingsRetrieval(self.campus_buildings_data)
        logger.info("[OK] Initialized campus buildings knowledge retrieval system")
        
        self.query_analyzer = EnhancedQueryAnalyzer(self.nlp_model)
        logger.info("[OK] Initialized enhanced query analyzer")
        
        self.response_generator = AdvancedResponseGenerator(self.llm)
        logger.info("[OK] Initialized advanced response generator")
        
        self.academic_calendar = AcademicCalendarContext()
        logger.info("[OK] Initialized academic calendar context")
        
        # Initialize conversation management
        self.conversation_history = []
        self.conversation_state = ConversationState()
        logger.info("[OK] Initialized conversation state manager")
        
        # Initialize performance metrics tracking
        self.metrics_tracker = MetricsTracker()
        logger.info("[OK] Initialized metrics tracker")
        
        # Measure initialization time
        init_time = time.time() - init_start_time
        logger.info(f"[OK] Initialization complete in {init_time:.2f} seconds")
        
    def _init_embedding_model(self):
        """Initialize the embedding model for semantic search"""
        try:
            if SentenceTransformer:
                # Use a smaller and faster model for embedded deployment
                model = SentenceTransformer('all-MiniLM-L6-v2')
                return model
            else:
                return None
        except Exception as e:
            logger.error(f"Failed to initialize embedding model: {e}")
            return None
            
    def _init_nlp_model(self):
        """Initialize the NLP model for linguistic analysis"""
        try:
            if spacy:
                try:
                    # Load the small English model for speed
                    model = spacy.load("en_core_web_sm")
                    return model
                except OSError:
                    # Download if not available
                    logger.warning("spaCy model not found, attempting to download...")
                    import subprocess
                    try:
                        subprocess.check_call([sys.executable, "-m", "spacy", "download", "en_core_web_sm"])
                        model = spacy.load("en_core_web_sm")
                        return model
                    except Exception as e:
                        logger.error(f"Failed to download spaCy model: {e}")
                        return None
            else:
                return None
        except Exception as e:
            logger.error(f"Error initializing NLP model: {e}")
            return None
            
    def process_query(self, query):
        """Process a user query with enhanced accuracy and context awareness"""
        # Start timer for performance monitoring
        start_time = time.time()
        
        try:
            # Preprocess query for better understanding
            query = self._preprocess_query(query)
            
            # Add query to conversation history
            self.conversation_history.append({"role": "user", "content": query})
            
            # Update conversation state
            self.conversation_state.update(query, "user")
            
            # Get current academic context
            academic_context = self.academic_calendar.get_current_context()
            
            # Analyze query
            query_analysis = self.query_analyzer.analyze(query, self.conversation_history)
            logger.info(f"Query analysis: intent={query_analysis.get('intent')}, categories={query_analysis.get('categories')}")
            
            # Determine if this is a building-related query
            is_building_query = 'buildings' in query_analysis.get('categories', []) or \
                               query_analysis.get('intent') in ['find_building', 'building_info'] or \
                               query_analysis.get('is_building_query', False)
            
            # Determine if this is a library-related query
            is_library_query = any(category in query_analysis.get('categories', []) for category in 
                                ['hours', 'collections', 'study_spaces', 'services', 'offerings']) or \
                              query_analysis.get('intent') in ['check_hours', 'find_materials', 'find_study_space'] or \
                              query_analysis.get('is_all_libraries_query', False)
            
            # Initialize relevant entities
            library = None
            library_confidence = 0.0
            building = None
            building_confidence = 0.0
            
            # If this is a follow-up, try to use the previously active context
            if query_analysis.get('is_followup', False):
                if is_building_query or not is_library_query:
                    # Check for building context first
                    prev_building = self.conversation_state.get_active_building()
                    if prev_building and self.conversation_state.should_maintain_context(query, prev_building):
                        building = prev_building
                        building_confidence = 0.8
                        logger.info(f"Using previous building context: {building.get('Building Name', '')}")
                
                if is_library_query or (not building and not is_building_query):
                    # Check for library context
                    prev_library = self.conversation_state.get_active_library()
                    if prev_library and self.conversation_state.should_maintain_context(query, prev_library):
                        library = prev_library
                        library_confidence = 0.8
                        logger.info(f"Using previous library context: {library.get('Library Name', '')}")
            
            # If no context from history, try to identify from query
            if is_building_query and not building:
                building, building_confidence = self.buildings_knowledge.retrieve_building(query)
                
                if building:
                    logger.info(f"Identified building: {building.get('Building Name', '')} (confidence: {building_confidence:.2f})")
                else:
                    logger.info("No specific building identified")
                    
            if (is_library_query or not building) and not library:
                library, library_confidence = self.library_knowledge.retrieve_relevant_library(
                    query, query_analysis
                )
                
                if library:
                    logger.info(f"Identified library: {library.get('Library Name', '')} (confidence: {library_confidence:.2f})")
                else:
                    logger.info("No specific library identified")
            
            # Update active entities in conversation state
            if building and building_confidence >= 0.7:
                self.conversation_state.set_active_building(building)
            
            if library and library_confidence >= 0.7:
                self.conversation_state.set_active_library(library)
            
            # Generate response
            response, generation_metrics = self.response_generator.generate(
                query, 
                library,
                building,
                query_analysis,
                self.conversation_history,
                academic_context
            )
            
            # Final response time
            response_time = time.time() - start_time
            
            # Add to conversation history
            self.conversation_history.append({"role": "assistant", "content": response})
            self.conversation_state.update(response, "assistant")
            
            # Update metrics
            metrics = {**generation_metrics, 'response_time': response_time}
            if library and library_confidence >= 0.5:
                metrics['library'] = library
            if building and building_confidence >= 0.5:
                metrics['building'] = building
                
            self.metrics_tracker.record_query(
                query, 
                response, 
                response_time,
                metrics
            )
            
            logger.info(f"Response generated in {response_time:.2f}s (method: {generation_metrics.get('method', 'unknown')})")
            
            return response
            
        except Exception as e:
            # Handle unexpected errors gracefully
            logger.error(f"Error processing query: {e}")
            error_response = "I apologize for the technical issue. As the UF Assistant, I'm experiencing a momentary glitch. Please try asking your question again or rephrase your question."
            
            # Still add to conversation history
            self.conversation_history.append({"role": "assistant", "content": error_response})
            
            # Track error metrics
            error_time = time.time() - start_time
            self.metrics_tracker.record_query(
                query, 
                error_response, 
                error_time,
                {'method': 'error', 'error': str(e)}
            )
            
            return error_response
    
    def _preprocess_query(self, query):
        """Preprocess query for better understanding"""
        # Normalize library names
        query = re.sub(r"\blib\s*west\b", "Library West", query, flags=re.IGNORECASE)
        query = re.sub(r"\bmarston('s)?\b", "Marston Science Library", query, flags=re.IGNORECASE)
        query = re.sub(r"\bsmather('s)?\b", "Smathers Library", query, flags=re.IGNORECASE)
        
        # Normalize building references
        query = re.sub(r"\bclb\b", "105 Classroom Building", query, flags=re.IGNORECASE)
        query = re.sub(r"\barb\b", "Academic Research Building", query, flags=re.IGNORECASE)
        query = re.sub(r"\band\b", "Anderson Hall", query, flags=re.IGNORECASE)
        
        # Handle special queries
        query_lower = query.lower()
        
        # Room reservation queries
        if "room" in query_lower and any(word in query_lower for word in ["reserve", "book", "reservation"]):
            if not any(word in query_lower for word in ["how", "can i", "where"]):
                query = f"how do I reserve a study room {query}"
        
        # Website queries
        if any(word in query_lower for word in ["website", "url", "site", "web"]):
            if not any(word in query_lower for word in ["what", "where"]):
                query = f"what is the website for {query}"
                
        # Coffee queries
        if "coffee" in query_lower:
            if not any(word in query_lower for word in ["where", "what", "is there"]):
                query = f"where can I get coffee {query}"
        
        return query
            
    def reset_conversation(self):
        """Reset the conversation history and state"""
        self.conversation_history = []
        self.conversation_state = ConversationState()
        return "Conversation has been reset."
        
    def get_metrics_summary(self):
        """Get a summary of assistant performance metrics"""
        return self.metrics_tracker.get_summary()
        
    def export_metrics(self, filename="uf_assistant_metrics.json"):
        """Export performance metrics to JSON file"""
        return self.metrics_tracker.export_metrics(filename)

# =============================================================================
# TRAINING EXAMPLES
# =============================================================================

# Training examples for response consistency and faster common questions
TRAINING_EXAMPLES = [
    {
        "query": "What are the hours for Library West?",
        "response": "Library West is open from 7:00am to 2:00am today (Thursday).\n\nRegular hours:\n• Monday: 7:00am - 2:00am\n• Tuesday: 7:00am - 2:00am\n• Wednesday: 7:00am - 2:00am\n• Thursday: 7:00am - 2:00am\n• Friday: 7:00am - 10:00pm\n• Saturday: 10:00am - 10:00pm\n• Sunday: 7:00am - 2:00am\n\nPlease note that building access after 10pm is limited to users with an active UF ID or Santa Fe College ID."
    },
    {
        "query": "Where is Marston Science Library located?",
        "response": "Marston Science Library is located at 444 Newell Dr, Gainesville, FL 32611. It's situated in the central part of UF's campus, making it easily accessible from most classroom buildings."
    },
    {
        "query": "Tell me about Smathers Library",
        "response": "Smathers Library is UF's oldest library, located at the Plaza of the Americas in Gainesville, FL 32611. It houses special collections, archives, rare books, and historical manuscripts.\n\nThe library offers several resources:\n• Florida history collections\n• Latin American collections\n• Rare books and manuscripts\n• Archives and special collections reading rooms\n• Research assistance for historical materials\n\nSmathers Library is open from 7:00am to 2:00am Monday through Thursday, 7:00am to 10:00pm on Friday, 10:00am to 10:00pm on Saturday, and 7:00am to 2:00am on Sunday.\n\nThe library is known for its historical collections, including the P.K. Yonge Library of Florida History and various special collections."
    },
    {
        "query": "What are things Marston offers?",
        "response": "Marston Science Library offers the following resources and services:\n\n• STEM research materials and databases\n• Makerspace with 3D printing capabilities\n• Technical software (MATLAB, AutoCAD, SolidWorks, etc.)\n• Group study rooms (reservations required)\n• Quiet study areas on upper floors\n• Computer workstations with specialized software\n• Research assistance for science and engineering\n• Printing and scanning services\n• GIS support and data visualization resources\n• Course reserves for STEM classes\n\nThe library specializes in science, engineering, technology, and mathematics resources. For more information, you can contact them at marston@uflib.ufl.edu or visit their website at https://uflib.ufl.edu/marston/."
    },
    {
        "query": "Where can I study quietly?",
        "response": "For quiet studying at UF, you have several good options:\n\n• Library West: The 4th floor is a designated silent study area with individual study carrels.\n\n• Marston Science Library: The upper floors (especially the 3rd and 4th floors) offer quiet study areas with individual seating.\n\n• Smathers Library: The Grand Reading Room provides a quiet, historic study environment.\n\n• Health Science Center Library: Offers designated quiet study spaces throughout the building.\n\nAll these libraries have extended hours during weekdays (generally 7am-2am). Library West and Marston Science Library tend to be the most popular for quiet studying. Just remember that building access after 10pm requires an active UF ID."
    },
    {
        "query": "I need to print something, where should I go?",
        "response": "You can print at any of the UF libraries. Here are your options:\n\n• Marston Science Library: Printing stations are available on the 1st floor. They offer both black & white and color printing options.\n\n• Library West: Printing services are located on the 1st floor near the entrance.\n\n• Smathers Library: Printing is available on the 2nd floor.\n\n• Health Science Center Library: Printing stations are located throughout the building.\n\nTo print, you'll need to send your document to the print queue and use your Gator 1 card to release the print job. Black and white printing typically costs $0.08 per page, while color printing is $0.25 per page. All libraries have scanning services available at no cost."
    },
    {
        "query": "Where can I find legal resources on campus?",
        "response": "The Legal Information Center at the Levin College of Law is your best resource for legal materials on campus. Located at the UF Levin College of Law (Gainesville, FL 32611), this specialized library offers:\n\n• Comprehensive legal collections including case law, statutes, and regulations\n• Legal research databases (Westlaw, LexisNexis, HeinOnline)\n• Study spaces designed for law students\n• Legal research assistance from specialized librarians\n• Computer workstations with legal software\n• Group study rooms for collaborative work\n\nThe Legal Information Center is open from 7:00am to 2:00am Monday through Thursday, 7:00am to 10:00pm on Friday, 10:00am to 10:00pm on Saturday, and 7:00am to 2:00am on Sunday. For specific questions about legal resources, you can contact them at lic@law.ufl.edu or (352) 273-0722."
    },
    {
        "query": "I'm looking for architecture books",
        "response": "The Architecture & Fine Arts Library is your best resource for architecture books at UF. Located at 1480 Inner Rd, Gainesville, FL 32611, this specialized library offers:\n\n• Comprehensive architecture book collections\n• Design and building technology resources\n• Urban planning materials\n• Interior design references\n• Visual resources for architecture studies\n• Design standards and guides\n• Architectural journals and periodicals\n\nThe library provides spaces specifically designed for architecture students, including large tables for design work and computer stations with specialized design software like AutoCAD and Revit.\n\nIt's open from 7:00am to 2:00am Monday through Thursday, 7:00am to 10:00pm on Friday, 10:00am to 10:00pm on Saturday, and 7:00am to 2:00am on Sunday. For specific questions about architecture resources, you can contact them at afa@uflib.ufl.edu."
    },
    {
        "query": "Are you an AI?",
        "response": "Yes, I'm an AI assistant specifically designed to provide information about the University of Florida's libraries, buildings, campus resources, and other UF-related topics. I can help with questions about library hours, locations, services, collections, building information, and more. How can I assist you with UF-related questions today?"
    },
    {
        "query": "What libraries are on campus?",
        "response": "The University of Florida has several libraries across campus:\n\n• Library West: Focuses on humanities, business, and social sciences\n• Marston Science Library: Specializes in science, engineering, technology, and math\n• Smathers Library: Houses special collections, archives, and rare materials\n• Health Science Center Library: Serves medical and health science disciplines\n• Architecture & Fine Arts Library: Supports art, design, and architecture programs\n• Education Library: Resources for education and teaching\n• Legal Information Center: Law and legal resources\n\nEach library offers specialized collections, study spaces, and research assistance for their respective disciplines."
    },
    {
        "query": "I'm looking for books on Florida history",
        "response": "For books on Florida history, your best resource is the P.K. Yonge Library of Florida History, located in Smathers Library (on the Plaza of the Americas). This is one of the most comprehensive collections of Florida historical materials anywhere.\n\nThe collection includes:\n• Rare books on Florida's colonial and territorial periods\n• Extensive manuscript collections from Florida's notable historical figures\n• Historical newspapers and periodicals\n• Maps and geographical materials related to Florida\n• Archival photographs documenting Florida's history\n• Local and regional historical records\n• Materials on indigenous peoples of Florida\n\nThese materials are part of the Special & Area Studies Collections and are typically used in the reading room on the 2nd floor of Smathers Library. Some items may require advance notice to access.\n\nSmathers Library is open from 7:00am to 2:00am Monday through Thursday, 7:00am to 10:00pm on Friday, 10:00am to 10:00pm on Saturday, and 7:00am to 2:00am on Sunday. However, the Special Collections reading room has more limited hours, typically 9:00am to 5:00pm Monday through Friday.\n\nFor specific research assistance with Florida history materials, you can contact specialcollections@uflib.ufl.edu."
    },
    {
        "query": "Is there a cafe in any of the libraries?",
        "response": "Yes, there is a café in Library West called the Starbucks Library West. It's located on the first floor of Library West and offers a selection of coffee drinks, teas, pastries, and light snacks.\n\nThis Starbucks location is popular among students for study breaks and quick refreshments. The hours may be slightly different from the library's hours, typically opening a bit later and closing earlier than the library itself.\n\nOther UF libraries don't have cafés inside them, but there are numerous dining options near the libraries:\n\n• Near Marston Science Library: You'll find the Reitz Union food court and Starbucks at Newell Hall within walking distance\n• Near Health Science Center Library: Several cafés and food options are available in the health complex buildings\n• Near Smathers Library: The Plaza of the Americas often has food vendors during weekdays\n\nWhile beverages with secure lids are generally permitted in library spaces, food policies may vary by location and specific areas within each library."
    },
    {
        "query": "Where are the Starbucks on campus?",
        "response": "There are three Starbucks locations on the UF campus:\n\n• Starbucks at Library West: Located on the first floor of Library West. Open from 7:30am to 8:00pm Monday through Thursday, 7:30am to 5:00pm on Friday, closed Saturday, and 1:00pm to 8:00pm on Sunday.\n\n• Starbucks at Newell Hall: Located on the ground floor of Newell Hall, near Marston Science Library. Open from 7:30am to 5:00pm Monday through Friday, closed on weekends.\n\n• Starbucks at the Reitz Union: Located on the ground floor of the Reitz Union. Open from 7:00am to 9:00pm Monday through Thursday, 7:00am to 8:00pm on Friday, 9:00am to 6:00pm on Saturday, and 10:00am to 6:00pm on Sunday.\n\nThe Starbucks at Library West is particularly convenient if you're studying there."
    },
    {
        "query": "Does Marston have coffee?",
        "response": "Marston Science Library itself does not have a coffee shop inside the building. However, there is a Starbucks located nearby at Newell Hall, which is just a short walk from Marston. This Starbucks is typically open from 7:30am to 5:00pm on weekdays. Additionally, there are vending machines within Marston where you can purchase cold beverages and snacks."
    },
    {
        "query": "What's the website for Library West?",
        "response": "The website for Library West is: https://uflib.ufl.edu/library-west/"
    },
    {
        "query": "How do I reserve a study room at Marston?",
        "response": "To reserve a study room at Marston Science Library:\n\n1. Go to https://uflib.ufl.edu/marston/\n2. Click on 'Study Rooms' or 'Room Reservations'\n3. Sign in with your GatorLink credentials\n4. Select your preferred time and location\n\nImportant information:\n• Reservations are limited to 2 hours per day per group\n• You must have a valid UF ID to use reserved rooms\n• Rooms must be occupied within 15 minutes of reservation time\n• Most rooms have whiteboards and display screens for collaborative work"
    },
    {
        "query": "Where is Anderson Hall?",
        "response": "Anderson Hall is located at 100 Fletcher Dr, Gainesville, FL 32611. It's home to the College of Liberal Arts and Sciences at the University of Florida. The building is centrally located on campus, making it easily accessible from most other facilities."
    },
    {
        "query": "What is the Academic Research Building?",
        "response": "The Academic Research Building (ARB) is located at 1230 Inner Road, Gainesville, FL 32611. It houses research laboratories and facilities for interdisciplinary studies at the University of Florida. The building provides space for various research initiatives across multiple academic disciplines."
    },
    {
        "query": "Tell me about CLB",
        "response": "The 105 Classroom Building (CLB) is located at 105 Fletcher Drive, Gainesville, FL 32611. It's primarily used for classrooms and academic facilities at the University of Florida. Many undergraduate courses are held in this building, which is equipped with standard classroom technology and learning spaces."
    },
    {
        "query": "Is there a stadium on campus?",
        "response": "Yes, UF has several athletic facilities on campus. The Alfred A. McKethan Stadium, formerly used for baseball, has been replaced by Condron Ballpark located at 2500 SW 2nd Ave, Gainesville, FL 32607. The main football stadium is Ben Hill Griffin Stadium, also known as 'The Swamp,' which is one of the most recognized stadiums in college football."
    }
]

# =============================================================================
# INTERACTIVE CLI
# =============================================================================

def interactive_cli(assistant):
    """Run an interactive CLI for the UF Assistant"""
    print("\n=== Enhanced UF Assistant ===")
    print("Type your questions about UF libraries and campus buildings (or '/help' for commands)")
    
    while True:
        try:
            # Get query from user
            query = input("\n> ").strip()
            
            # Check for exit command
            if query.lower() in ['quit', 'exit', 'bye', 'q']:
                break
                
            # Process special commands
            if query.startswith('/'):
                # Reset conversation
                if query == '/reset':
                    assistant.reset_conversation()
                    print("Conversation history has been reset.")
                    continue
                    
                # Show metrics
                elif query == '/metrics':
                    metrics = assistant.get_metrics_summary()
                    print("\n=== Performance Metrics ===")
                    print(f"Queries Processed: {metrics['queries_processed']}")
                    print(f"Average Response Time: {metrics['avg_response_time']:.2f} seconds")
                    print(f"Average Confidence: {metrics['avg_confidence']:.2f}")
                    print("\nTop Library Matches:")
                    for lib, count in metrics['top_libraries'].items():
                        print(f"  - {lib}: {count}")
                    print("\nTop Building Matches:")
                    for building, count in metrics['top_buildings'].items():
                        print(f"  - {building}: {count}")
                    print("\nTop Intents:")
                    for intent, count in metrics['top_intents'].items():
                        print(f"  - {intent}: {count}")
                    continue
                    
                # Export metrics
                elif query == '/export':
                    filename = input("Enter filename (default: uf_assistant_metrics.json): ").strip()
                    if not filename:
                        filename = "uf_assistant_metrics.json"
                    success = assistant.export_metrics(filename)
                    if success:
                        print(f"Metrics exported to {filename}")
                    else:
                        print("Error exporting metrics")
                    continue
                    
                # Print commands help
                elif query == '/help':
                    print("\n=== Commands ===")
                    print("/reset - Reset conversation history")
                    print("/metrics - Show performance metrics")
                    print("/export - Export metrics to file")
                    print("/help - Show this help message")
                    print("/quit or quit - Exit the program")
                    continue
                    
                # Exit command
                elif query == '/quit':
                    break
            
            # Generate response
            start_time = time.time()
            response = assistant.process_query(query)
            end_time = time.time()
            
            # Print response with timing information
            print(f"\n{response}")
            print(f"\n[Response time: {end_time - start_time:.2f} seconds]")
            
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"\nError: {str(e)}")

# =============================================================================
# BATCH TESTING
# =============================================================================

def run_batch_tests(assistant, test_set='basic'):
    """Run a batch of tests on the assistant"""
    # Define test sets
    test_sets = {
        'basic': [
            "What are the hours for Library West?",
            "Where is Marston Science Library located?",
            "Tell me about Smathers Library",
            "Are you an AI?",
            "What libraries are on campus?"
        ],
        'detailed': [
            "What are things Marston offers?",
            "Where can I study quietly?",
            "I need to print something, where should I go?",
            "Which libraries have the best wifi?",
            "Where can I find legal resources?",
            "Does the Education Library have study rooms?",
            "What special collections does Smathers have?",
            "I'm looking for architecture books, which library should I go to?",
            "Are there any cafes in the libraries?",
            "Do UF libraries have textbooks on reserve?"
        ],
        'edge_cases': [
            "When was Library West built?",  # Might not have this specific info
            "Can I eat in the library?",  # Policy question
            "Where is the nearest bathroom to Marston?",  # Very specific location
            "Which library is best for studying?",  # Subjective question
            "Why is the library named Marston?",  # Historical question
            "lib wet hours",  # Typos/misspellings
            "I need help with my research paper",  # General assistance
            "Can I check out a laptop?",  # Specific service
            "How many books does Library West have?",  # Specific count
            "What's the quietest spot in the library?"  # Subjective assessment
        ],
        'amenities': [
            "Where can I get coffee near Marston?",
            "Does Library West have a cafe?",
            "Where are the Starbucks on campus?",
            "Where can I eat near the libraries?",
            "What food options are near Smathers?",
            "Is there a coffee shop in Marston?"
        ],
        'followups': [
            "Where is Marston?",
            "Does it have coffee?",
            "yes",
            "where's the closest one?",
            "thanks",
            "where can I eat nearby?"
        ],
        'buildings': [
            "Where is Anderson Hall?",
            "What is the CLB building?",
            "Tell me about the Academic Research Building",
            "How do I get to Anderson Hall from Marston?",
            "What departments are in Anderson Hall?",
            "Is there a stadium on campus?",
            "Where are the classrooms on campus?",
            "What building is at 105 Fletcher Drive?"
        ]
    }
    
    # Get the appropriate test set
    if test_set in test_sets:
        tests = test_sets[test_set]
    elif test_set == 'all':
        tests = []
        for test_group in test_sets.values():
            tests.extend(test_group)
    else:
        print(f"Test set '{test_set}' not found. Using basic test set.")
        tests = test_sets['basic']
    
    print(f"\n===== RUNNING {len(tests)} TESTS =====\n")
    
    results = []
    
    # Reset conversation history for testing
    assistant.reset_conversation()
    
    # Run each test
    for i, query in enumerate(tests):
        print(f"Test #{i+1}: {query}")
        
        # Process the query and time it
        start_time = time.time()
        response = assistant.process_query(query)
        end_time = time.time()
        response_time = end_time - start_time
        
        # Print the result
        print("\nResponse:")
        print(response)
        print(f"\nResponse time: {response_time:.2f} seconds")
        print("\n" + "-" * 80 + "\n")
        
        # Store result
        results.append({
            "query": query,
            "response": response,
            "response_time": response_time
        })
    
    # Print summary
    total_time = sum(result["response_time"] for result in results)
    avg_time = total_time / len(results)
    
    print("\n===== TEST SUMMARY =====")
    print(f"Tests run: {len(results)}")
    print(f"Total time: {total_time:.2f} seconds")
    print(f"Average response time: {avg_time:.2f} seconds")
    
    return results

# =============================================================================
# BUILDING TEST SPECIFIC FUNCTION
# =============================================================================

def test_building_queries(assistant):
    """Test building-related queries on the UF Assistant"""
    building_tests = [
        "Where is Anderson Hall?",
        "What is the Academic Research Building?",
        "Tell me about CLB",
        "Where are the classrooms on campus?",
        "How do I find the Animal Sciences Building?",
        "Which building houses the College of Liberal Arts and Sciences?",
        "What's the abbreviation for 105 Classroom Building?",
        "Where is the former baseball stadium?",
        "What buildings are on Fletcher Drive?"
    ]
    
    print(f"\n===== TESTING BUILDING QUERIES =====\n")
    
    for i, query in enumerate(building_tests):
        print(f"Test #{i+1}: {query}")
        
        # Process the query and time it
        start_time = time.time()
        response = assistant.process_query(query)
        end_time = time.time()
        response_time = end_time - start_time
        
        # Print the result
        print("\nResponse:")
        print(response)
        print(f"\nResponse time: {response_time:.2f} seconds")
        print("\n" + "-" * 80 + "\n")

# =============================================================================
# MAIN FUNCTION
# =============================================================================

def main():
    """Main function to run the Enhanced UF Assistant"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Enhanced UF Assistant')
    parser.add_argument('--model_path', type=str, default='./AI/models/Meta-Llama-3-8B-Instruct-Q8_0.gguf',
                      help='Path to the LLaMA model')
    parser.add_argument('--use_gpu', action='store_true',
                      help='Use GPU for inference if available')
    parser.add_argument('--test', choices=['basic', 'detailed', 'edge_cases', 'amenities', 'followups', 'buildings', 'all'],
                      help='Run tests instead of interactive mode')
    parser.add_argument('--interactive', action='store_true',
                      help='Run in interactive mode after tests')
    args = parser.parse_args()
    
    print("Initializing Enhanced UF Assistant...")
    
    # Initialize the assistant
    assistant = EnhancedUFAssistant(
        model_path=args.model_path,
        use_gpu=args.use_gpu
    )
    
    # Run tests if requested
    if args.test:
        if args.test == 'buildings':
            test_building_queries(assistant)
        elif args.test == 'all':
            run_batch_tests(assistant, 'basic')
            test_building_queries(assistant)
        else:
            run_batch_tests(assistant, args.test)
    
    # Run interactive mode if requested or if no tests were run
    if args.interactive or not args.test:
        interactive_cli(assistant)
    
    print("\nThank you for using the Enhanced UF Assistant!")

if __name__ == "__main__":
    main()