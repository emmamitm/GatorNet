#!/usr/bin/env python3
"""
Enhanced UF Assistant
A powerful assistant for answering questions about University of Florida
using LLaMA 3 with embedded knowledge and advanced retrieval techniques.
Now with residence hall and housing information.
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
        "Special Notes": "Includes Makerspace (capacity: 15)",
        "URL": "https://uflib.ufl.edu/marston/",
        "Phone": "(352) 273-2845",
        "Email": "marston@uflib.ufl.edu",
        "Tags": "science, engineering, technology, agriculture",
        "Resources": [
            "Research assistance",
            "Computers and laptops for checkout",
            "Printing and scanning",
            "Group study rooms",
            "Quiet study areas",
            "Makerspace with 3D printers",
            "Course reserves",
            "Citation management tools",
            "STEM databases"
        ],
        "Study Spaces": [
            "Silent study areas",
            "Group study rooms (reservation required)",
            "Individual study carrels",
            "Collaborative spaces",
            "Comfortable seating areas"
        ],
        "Collections": [
            "Science literature",
            "Engineering resources",
            "Technology materials",
            "Agricultural literature",
            "Journals and periodicals",
            "Digital collections",
            "Course reserves"
        ],
        "Technology": [
            "Computer workstations",
            "Printing stations",
            "Scanners",
            "Charging stations",
            "3D printers",
            "VR equipment",
            "Data analysis tools",
            "Laptops for checkout"
        ],
        "Services": [
            "Research consultations",
            "Course reserves",
            "Interlibrary loan",
            "Citation help",
            "Subject specialist librarians",
            "Information literacy instruction",
            "Circulation desk",
            "Makerspace training"
        ],
        "Aliases": [
            "marston",
            "msl",
            "science library",
            "marston library"
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
        "Special Notes": "Oldest library on campus",
        "URL": "https://uflib.ufl.edu/smathers/",
        "Phone": "(352) 273-2845",
        "Email": "smathers@uflib.ufl.edu",
        "Tags": "special collections, archives, history",
        "Resources": [
            "Special collections",
            "Research assistance",
            "Computers",
            "Printing",
            "Group study rooms",
            "Rare books and manuscripts",
            "University archives"
        ],
        "Study Spaces": [
            "Group study rooms (reservation required)",
            "Individual study carrels",
            "Reading rooms",
            "Grand Reading Room"
        ],
        "Collections": [
            "Special collections",
            "Rare books",
            "University archives",
            "Latin American collection",
            "Florida history",
            "Judaica collection",
            "P.K. Yonge Library of Florida History"
        ],
        "Technology": [
            "Computer workstations",
            "Printing stations",
            "Scanners",
            "Microfilm readers",
            "Digitization equipment"
        ],
        "Services": [
            "Research consultations",
            "Archival assistance",
            "Rare materials access",
            "Subject specialist librarians",
            "Information literacy instruction",
            "Circulation desk"
        ],
        "Aliases": [
            "smathers",
            "library east",
            "east library",
            "lib east",
            "special collections"
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
        "Special Notes": "Medical collections",
        "URL": "https://uflib.ufl.edu/hscl/",
        "Phone": "(352) 273-8408",
        "Email": "hsc-library@uflib.ufl.edu",
        "Tags": "medicine, dentistry, nursing, pharmacy, public health",
        "Resources": [
            "Medical research assistance",
            "Computers",
            "Printing",
            "Group study rooms",
            "Quiet study areas",
            "Medical journals and databases",
            "Course reserves",
            "Citation management tools"
        ],
        "Study Spaces": [
            "Silent study areas",
            "Group study rooms (reservation required)",
            "Individual study carrels",
            "Collaboration spaces"
        ],
        "Collections": [
            "Medical literature",
            "Dental resources",
            "Nursing materials",
            "Pharmacy resources",
            "Public health literature",
            "Journals and periodicals",
            "Digital collections",
            "Course reserves"
        ],
        "Technology": [
            "Computer workstations",
            "Printing stations",
            "Scanners",
            "Charging stations",
            "Medical software",
            "Data analysis tools"
        ],
        "Services": [
            "Research consultations",
            "Course reserves",
            "Interlibrary loan",
            "Citation help",
            "Subject specialist librarians",
            "Information literacy instruction",
            "Circulation desk",
            "Systematic review support"
        ],
        "Aliases": [
            "hscl",
            "health science library",
            "medical library",
            "hsc library"
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
        "Special Notes": "Arts collections",
        "URL": "https://uflib.ufl.edu/afa/",
        "Phone": "(352) 273-2825",
        "Email": "afa@uflib.ufl.edu",
        "Tags": "architecture, art, design, urban planning",
        "Resources": [
            "Arts research assistance",
            "Computers",
            "Printing",
            "Group study rooms",
            "Quiet study areas",
            "Art and design databases",
            "Course reserves",
            "Citation management tools"
        ],
        "Study Spaces": [
            "Study areas",
            "Group study rooms (reservation required)",
            "Individual study carrels"
        ],
        "Collections": [
            "Architecture literature",
            "Art resources",
            "Design materials",
            "Urban planning resources",
            "Journals and periodicals",
            "Digital collections",
            "Course reserves"
        ],
        "Technology": [
            "Computer workstations",
            "Printing stations",
            "Scanners",
            "Design software",
            "Large format printers"
        ],
        "Services": [
            "Research consultations",
            "Course reserves",
            "Interlibrary loan",
            "Citation help",
            "Subject specialist librarians",
            "Information literacy instruction",
            "Circulation desk"
        ],
        "Aliases": [
            "afa",
            "architecture library",
            "fine arts library",
            "art library"
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
        "Special Notes": "Education collections",
        "URL": "https://uflib.ufl.edu/education/",
        "Phone": "(352) 273-2780",
        "Email": "edulib@uflib.ufl.edu",
        "Tags": "education, teaching, learning, curriculum",
        "Resources": [
            "Education research assistance",
            "Computers",
            "Printing",
            "Study areas",
            "Education databases",
            "Course reserves",
            "Citation management tools",
            "Curriculum materials"
        ],
        "Study Spaces": [
            "Study areas",
            "Individual study carrels",
            "Collaboration spaces"
        ],
        "Collections": [
            "Education literature",
            "Teaching resources",
            "Curriculum materials",
            "Children's literature",
            "Journals and periodicals",
            "Digital collections",
            "Course reserves"
        ],
        "Technology": [
            "Computer workstations",
            "Printing stations",
            "Scanners",
            "Educational software"
        ],
        "Services": [
            "Research consultations",
            "Course reserves",
            "Interlibrary loan",
            "Citation help",
            "Subject specialist librarians",
            "Information literacy instruction",
            "Circulation desk"
        ],
        "Aliases": [
            "edulib",
            "education library",
            "norman library",
            "teaching library"
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
        "Special Notes": "Legal collections",
        "URL": "https://uflib.ufl.edu/lic/",
        "Phone": "(352) 273-0722",
        "Email": "lic@law.ufl.edu",
        "Tags": "law, legal studies, government documents",
        "Resources": [
            "Legal research assistance",
            "Computers",
            "Printing",
            "Group study rooms",
            "Quiet study areas",
            "Legal databases",
            "Course reserves",
            "Citation management tools"
        ],
        "Study Spaces": [
            "Silent study areas",
            "Group study rooms (reservation required)",
            "Individual study carrels",
            "Reading rooms"
        ],
        "Collections": [
            "Legal literature",
            "Law resources",
            "Government documents",
            "Case law",
            "Journals and periodicals",
            "Digital collections",
            "Course reserves"
        ],
        "Technology": [
            "Computer workstations",
            "Printing stations",
            "Scanners",
            "Legal research software"
        ],
        "Services": [
            "Research consultations",
            "Course reserves",
            "Interlibrary loan",
            "Citation help",
            "Subject specialist librarians",
            "Information literacy instruction",
            "Circulation desk",
            "Legal research training"
        ],
        "Aliases": [
            "lic",
            "law library",
            "legal library",
            "levin library"
        ]
    },
    {
        "Library Name": "Special & Area Studies Collections",
        "Location": "Smathers Library 2nd Floor",
        "Capacity": "Unknown",
        "Hours": {
            "By appointment": "Closed"
        },
        "Special Notes": "Located in Grand Reading Room",
        "URL": "https://uflib.ufl.edu/spec/",
        "Phone": "(352) 273-2778",
        "Email": "spec@uflib.ufl.edu",
        "Tags": "rare books, archives, manuscripts, special collections",
        "Resources": [
            "Special collections research assistance",
            "Rare books",
            "Manuscripts",
            "University archives",
            "Florida history collections",
            "Archival materials"
        ],
        "Study Spaces": [
            "Grand Reading Room",
            "Research tables"
        ],
        "Collections": [
            "University Archives",
            "P.K. Yonge Library of Florida History",
            "Latin American Collection",
            "Rare Book Collection",
            "Baldwin Library of Historical Children's Literature",
            "Judaica Collection",
            "African Studies Collection"
        ],
        "Technology": [
            "Specialized scanning equipment",
            "Microfilm readers",
            "Digital preservation tools"
        ],
        "Services": [
            "Research consultations",
            "Archival assistance",
            "Digitization services",
            "Preservation services",
            "Exhibition support",
            "Subject specialist archivists"
        ],
        "Aliases": [
            "special collections",
            "archives",
            "rare books",
            "manuscripts"
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
        "Address": "1275 Center Drive, Gainesville, FL 32610",
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
        "Address": "1405 W University Ave, Gainesville, FL 32611",
        "Description": "Home to the College of Liberal Arts and Sciences."
    },
    {
        "Building Number": "",
        "Building Name": "Animal Sciences Building",
        "Abbreviation": "ANSC",
        "Address": "2250 Shealy Dr, Gainesville, FL 32608",
        "Description": "Animal science research and education."
    },
    {
        "Building Number": "",
        "Building Name": "Aquatic Food Production Pilot Plant",
        "Abbreviation": "AFPP",
        "Address": "7922 NW 71st St, Gainesville, FL 32653",
        "Description": "Aquaculture and food production research."
    },
    {
        "Building Number": "",
        "Building Name": "Aquatic Products Lab",
        "Abbreviation": "APL",
        "Address": "7922 NW 71st St, Gainesville, FL 32653",
        "Description": "Supports aquatic food research."
    },
    {
        "Building Number": "",
        "Building Name": "Architecture Building",
        "Abbreviation": "ARCH",
        "Address": "331 Architecture Building, P.O. Box 115701, Gainesville, FL 32611-5701",
        "Description": "College of Design, Construction & Planning."
    },
    {
        "Building Number": "",
        "Building Name": "Bartram Hall",
        "Abbreviation": "BRM",
        "Address": "Bartram Hall, Gainesville, FL 32611",
        "Description": "Classrooms and offices for multiple departments."
    },
    {
        "Building Number": "",
        "Building Name": "Basic Science Building",
        "Abbreviation": "BSB",
        "Address": "1600 SW Archer Rd, Gainesville, FL 32610",
        "Description": "UF Health Science Center research hub."
    },
    {
        "Building Number": "",
        "Building Name": "Basketball Practice Facility",
        "Abbreviation": "BPF",
        "Address": "250 Gale Lemerand Dr, Gainesville, FL 32611",
        "Description": "Training facility for basketball teams."
    },
    {
        "Building Number": "",
        "Building Name": "Baughman Center",
        "Abbreviation": "BAUG",
        "Address": "1700 Museum Rd, Gainesville, FL 32611",
        "Description": "Meditation and ceremonial space."
    },
    {
        "Building Number": "",
        "Building Name": "Beaty Towers",
        "Abbreviation": "BEAT",
        "Address": "13 Inner Rd, Gainesville, FL 32603",
        "Description": "Undergraduate residence hall."
    },
    {
        "Building Number": "",
        "Building Name": "Benton Hall",
        "Abbreviation": "BENT",
        "Address": "1460 Union Rd, Gainesville, FL 32611",
        "Description": "Engineering and computer science departments."
    },
    {
        "Building Number": "",
        "Building Name": "Biomedical Sciences Building",
        "Abbreviation": "BMS",
        "Address": "1275 Center Dr, Gainesville, FL 32610",
        "Description": "Biomedical research and labs."
    },
    {
        "Building Number": "",
        "Building Name": "Black Hall",
        "Abbreviation": "BLA",
        "Address": "1800 Weimer Hall, Gainesville, FL 32611",
        "Description": "College of Journalism and Communications."
    },
    {
        "Building Number": "",
        "Building Name": "Bookstore and Welcome Center",
        "Abbreviation": "UFBK",
        "Address": "Museum Road and Reitz Union Drive, P.O. Box 118450, Gainesville, FL 32611-8450",
        "Description": "Campus bookstore and visitor center."
    },
    {
        "Building Number": "",
        "Building Name": "Broward Dining Facility",
        "Abbreviation": "BRD",
        "Address": "650 Broward Dr, Gainesville, FL 32611",
        "Description": "Dining hall in Broward Hall."
    },
    {
        "Building Number": "",
        "Building Name": "Broward Hall",
        "Abbreviation": "BRO",
        "Address": "650 Broward Dr, Gainesville, FL 32611",
        "Description": "Residential hall with dining facilities."
    },
    {
        "Building Number": "",
        "Building Name": "Bruton-Geer Hall",
        "Abbreviation": "BRG",
        "Address": "Mowry Rd, Gainesville, FL 32611",
        "Description": "Agricultural and Life Sciences programs."
    },
    {
        "Building Number": "",
        "Building Name": "Bryan Hall",
        "Abbreviation": "BRY",
        "Address": "1384 Union Rd, Gainesville, FL 32611",
        "Description": "Classrooms and administrative offices."
    },
    {
        "Building Number": "",
        "Building Name": "Bryant Space Science Center",
        "Abbreviation": "BSSC",
        "Address": "223 Bryant Space Science Center, Gainesville, FL 32611",
        "Description": "Astronomy and space science research."
    },
    {
        "Building Number": "",
        "Building Name": "Buckman Hall",
        "Abbreviation": "BUCK",
        "Address": "100 Museum Rd, Gainesville, FL 32611",
        "Description": "Residential hall for freshmen."
    },
    {
        "Building Number": "",
        "Building Name": "Cancer Center",
        "Abbreviation": "CNC",
        "Address": "1515 SW Archer Rd, Gainesville, FL 32608",
        "Description": "UF Health Cancer Center facility."
    },
    {
        "Building Number": "",
        "Building Name": "Cancer and Genetics Research Complex",
        "Abbreviation": "CGRC",
        "Address": "2033 Mowry Rd, Gainesville, FL 32610",
        "Description": "Cancer and genetics research hub."
    },
    {
        "Building Number": "",
        "Building Name": "Carleton Auditorium",
        "Abbreviation": "CARL",
        "Address": "1475 Union Rd, Gainesville, FL 32611",
        "Description": "Lecture and event venue."
    },
    {
        "Building Number": "",
        "Building Name": "Carr Hall",
        "Abbreviation": "CARR",
        "Address": "1465 Union Rd, Gainesville, FL 32611",
        "Description": "Academic offices and classrooms."
    },
    {
        "Building Number": "",
        "Building Name": "Carse Swimming Complex",
        "Abbreviation": "CARSE",
        "Address": "1425 Stadium Rd, Gainesville, FL 32611",
        "Description": "Athletic swimming facilities."
    },
    {
        "Building Number": "",
        "Building Name": "Century Tower",
        "Abbreviation": "CENT",
        "Address": "100 Newell Dr, Gainesville, FL 32611",
        "Description": "Iconic bell tower and campus landmark."
    },
    {
        "Building Number": "",
        "Building Name": "Chemical Engineering Student Center",
        "Abbreviation": "CHESC",
        "Address": "1006 Center Dr, Gainesville, FL 32603",
        "Description": "Student center for chemical engineering."
    },
    {
        "Building Number": "",
        "Building Name": "Chemistry Laboratory",
        "Abbreviation": "CHEM",
        "Address": "125 Chemistry Lab Building, Gainesville, FL 32611",
        "Description": "Undergraduate chemistry labs."
    },
    {
        "Building Number": "",
        "Building Name": "Clinical and Translational Research Building",
        "Abbreviation": "CTRB",
        "Address": "2004 Mowry Rd, Gainesville, FL 32610",
        "Description": "Medical research and clinical trials."
    },
    {
        "Building Number": "",
        "Building Name": "Communicore Building",
        "Abbreviation": "COMM",
        "Address": "1275 Center Dr, Gainesville, FL 32610",
        "Description": "Health Science Center classrooms and labs."
    },
    {
        "Building Number": "",
        "Building Name": "Computer Science Building",
        "Abbreviation": "CSE",
        "Address": "432 Newell Dr, Gainesville, FL 32611",
        "Description": "Computer & Information Science & Engineering."
    },
    {
        "Building Number": "",
        "Building Name": "Condron Ballpark",
        "Abbreviation": "CBP",
        "Address": "2500 SW 2nd Ave, Gainesville, FL 32607",
        "Description": "Baseball stadium (formerly McKethan Stadium)."
    },
    {
        "Building Number": "",
        "Building Name": "Constans Theatre",
        "Abbreviation": "CONST",
        "Address": "687 McCarty Dr, Gainesville, FL 32611",
        "Description": "Performing arts theater."
    },
    {
        "Building Number": "",
        "Building Name": "Cooperative Living Organization",
        "Abbreviation": "CLO",
        "Address": "117 NW 15th St, Gainesville, FL 32603",
        "Description": "Student cooperative housing."
    },
    {
        "Building Number": "",
        "Building Name": "Corry Memorial Village",
        "Abbreviation": "CORRY",
        "Address": "1225 SW 9th Rd, Gainesville, FL 32601",
        "Description": "Graduate and family housing."
    },
    {
        "Building Number": "",
        "Building Name": "Counseling and Wellness Center",
        "Abbreviation": "CWC",
        "Address": "3190 Radio Rd, Gainesville, FL 32611",
        "Description": "Mental health and wellness services."
    },
    {
        "Building Number": "",
        "Building Name": "Courtelis Equine Teaching Hospital",
        "Abbreviation": "CETH",
        "Address": "2015 SW 16th Ave, Gainesville, FL 32610",
        "Description": "Equine veterinary hospital."
    },
    {
        "Building Number": "",
        "Building Name": "Criser Hall",
        "Abbreviation": "CRIS",
        "Address": "222 Criser Hall, P.O. Box 114000, Gainesville, FL 32611-4000",
        "Description": "Administrative offices, including Registrar."
    },
    {
        "Building Number": "",
        "Building Name": "Dauer Hall",
        "Abbreviation": "DAU",
        "Address": "220 Dauer Dr, Gainesville, FL 32611",
        "Description": "Political science and public health."
    },
    {
        "Building Number": "",
        "Building Name": "Davis Cancer Pavilion",
        "Abbreviation": "DAVIS",
        "Address": "1505 SW Archer Rd, Gainesville, FL 32608",
        "Description": "Cancer treatment and outpatient care."
    },
    {
        "Building Number": "",
        "Building Name": "Dental Science Building",
        "Abbreviation": "DENT",
        "Address": "1395 Center Dr, Gainesville, FL 32610",
        "Description": "College of Dentistry."
    },
    {
        "Building Number": "",
        "Building Name": "Deriso Hall",
        "Abbreviation": "DERI",
        "Address": "1376 Stadium Rd, Gainesville, FL 32611",
        "Description": "Engineering labs and classrooms."
    },
    {
        "Building Number": "",
        "Building Name": "Development and Alumni Affairs Building",
        "Abbreviation": "DAAB",
        "Address": "1938 W University Ave, Gainesville, FL 32603",
        "Description": "Alumni relations and fundraising."
    },
    {
        "Building Number": "",
        "Building Name": "Diamond Village",
        "Abbreviation": "DIAM",
        "Address": "1329 Diamond Rd, Gainesville, FL 32611",
        "Description": "Apartment-style student housing."
    },
    {
        "Building Number": "",
        "Building Name": "Dickinson Hall",
        "Abbreviation": "DICK",
        "Address": "1659 Museum Rd, Gainesville, FL 32611",
        "Description": "Art and art history departments."
    },
    {
        "Building Number": "",
        "Building Name": "Donald R. Dizney Stadium",
        "Abbreviation": "DIZ",
        "Address": "2800 SW 13th St, Gainesville, FL 32608",
        "Description": "Lacrosse and soccer stadium."
    },
    {
        "Building Number": "",
        "Building Name": "Doyle Conner Building",
        "Abbreviation": "DCB",
        "Address": "1911 SW 34th St, Gainesville, FL 32608",
        "Description": "Agricultural extension services."
    },
    {
        "Building Number": "",
        "Building Name": "East Campus Office Building",
        "Abbreviation": "ECOB",
        "Address": "1790 E University Ave, Gainesville, FL 32601",
        "Description": "Administrative offices."
    },
    {
        "Building Number": "",
        "Building Name": "East Hall",
        "Abbreviation": "EAST",
        "Address": "100 Stadium Rd, Gainesville, FL 32611",
        "Description": "Residential hall."
    },
    {
        "Building Number": "",
        "Building Name": "Elmore Hall",
        "Abbreviation": "ELM",
        "Address": "425 25th St, Gainesville, FL 32611",
        "Description": "Levin College of Law offices."
    },
    {
        "Building Number": "",
        "Building Name": "Emerging Pathogens Institute",
        "Abbreviation": "EPI",
        "Address": "2055 Mowry Rd, Gainesville, FL 32610",
        "Description": "Infectious disease research."
    },
    {
        "Building Number": "",
        "Building Name": "Emerson Alumni Hall",
        "Abbreviation": "EAH",
        "Address": "1938 W University Ave, Gainesville, FL 32603",
        "Description": "UF Alumni Association headquarters."
    },
    {
        "Building Number": "",
        "Building Name": "Entomology-Nematology Building",
        "Abbreviation": "ENTM",
        "Address": "1881 Natural Area Dr, Gainesville, FL 32611",
        "Description": "Insect and nematode studies."
    },
    {
        "Building Number": "",
        "Building Name": "Environmental Health and Safety Administrative Offices",
        "Abbreviation": "EHS",
        "Address": "916 Newell Dr, Gainesville, FL 32611",
        "Description": "Campus safety and compliance."
    },
    {
        "Building Number": "",
        "Building Name": "Farrior Hall",
        "Abbreviation": "FAR",
        "Address": "100 Farrior Hall, 100 Fletcher Drive, Gainesville, FL 32611",
        "Description": "Psychology department offices."
    },
    {
        "Building Number": "",
        "Building Name": "Fifield Hall",
        "Abbreviation": "FIF",
        "Address": "2550 Hull Rd, Gainesville, FL 32611",
        "Description": "Horticultural sciences department."
    },
    {
        "Building Number": "",
        "Building Name": "Fine Arts Building A",
        "Abbreviation": "FAA",
        "Address": "101 Fine Arts Building A, Gainesville, FL 32611",
        "Description": "Art studios and classrooms."
    },
    {
        "Building Number": "",
        "Building Name": "Fine Arts Building B",
        "Abbreviation": "FAB",
        "Address": "105 Fine Arts Building B, Gainesville, FL 32611",
        "Description": "Fine arts facilities."
    },
    {
        "Building Number": "",
        "Building Name": "Fine Arts Building C",
        "Abbreviation": "FAC",
        "Address": "107 Fine Arts Building C, Gainesville, FL 32611",
        "Description": "Additional art studios and labs."
    },
    {
        "Building Number": "",
        "Building Name": "Fletcher Hall",
        "Abbreviation": "FLET",
        "Address": "1365 Stadium Rd, Gainesville, FL 32611",
        "Description": "Residential hall."
    },
    {
        "Building Number": "",
        "Building Name": "Flint Hall",
        "Abbreviation": "FLINT",
        "Address": "1881 Stadium Rd, Gainesville, FL 32611",
        "Description": "School of Music facilities."
    },
    {
        "Building Number": "",
        "Building Name": "Florida Gymnasium",
        "Abbreviation": "FLGYM",
        "Address": "1864 Stadium Rd, Gainesville, FL 32611",
        "Description": "Historic sports and event venue."
    },
    {
        "Building Number": "",
        "Building Name": "Florida Pool",
        "Abbreviation": "FLPOOL",
        "Address": "1425 Stadium Rd, Gainesville, FL 32611",
        "Description": "Olympic-sized swimming pool."
    },
    {
        "Building Number": "",
        "Building Name": "Food Science and Human Nutrition Building",
        "Abbreviation": "FSHN",
        "Address": "572 Newell Dr, Gainesville, FL 32611",
        "Description": "Food and nutrition research."
    },
    {
        "Building Number": "",
        "Building Name": "Frazier Rogers Hall",
        "Abbreviation": "FRAZ",
        "Address": "Frazier Rogers Hall, Gainesville, FL 32611",
        "Description": "Agricultural and Biological Engineering."
    },
    {
        "Building Number": "",
        "Building Name": "Gator Band Shell",
        "Abbreviation": "GBAND",
        "Address": "Bandshell Drive, Gainesville, FL 32611",
        "Description": "Outdoor concert stage."
    },
    {
        "Building Number": "",
        "Building Name": "Gator Corner Dining Facility",
        "Abbreviation": "GCD",
        "Address": "698 Gale Lemerand Dr, Gainesville, FL 32611",
        "Description": "Dining hall near campus core."
    },
    {
        "Building Number": "",
        "Building Name": "General Services Building",
        "Abbreviation": "GSB",
        "Address": "P.O. Box 117700, Gainesville, FL 32611",
        "Description": "Facilities and maintenance offices."
    },
    {
        "Building Number": "",
        "Building Name": "Gerson Hall",
        "Abbreviation": "GERS",
        "Address": "1368 Union Rd, Gainesville, FL 32611",
        "Description": "Engineering classrooms and labs."
    },
    {
        "Building Number": "",
        "Building Name": "Graham Hall",
        "Abbreviation": "GRAH",
        "Address": "78 Stadium Rd, Gainesville, FL 32611",
        "Description": "Residential hall."
    },
    {
        "Building Number": "",
        "Building Name": "Gran Telescopio Canarias",
        "Abbreviation": "GTC",
        "Address": "La Palma, Spain",
        "Description": "UF-partnered astronomical observatory (not on campus)."
    },
    {
        "Building Number": "",
        "Building Name": "Griffin-Floyd Hall",
        "Abbreviation": "GRIF",
        "Address": "230 Newell Dr, Gainesville, FL 32611",
        "Description": "Residential hall."
    },
    {
        "Building Number": "",
        "Building Name": "Grinter Hall",
        "Abbreviation": "GRIN",
        "Address": "319 Grinter Hall, P.O. Box 115530, Gainesville, FL 32611-5530",
        "Description": "Graduate School and International Center."
    },
    {
        "Building Number": "",
        "Building Name": "Harn Museum of Art",
        "Abbreviation": "HARN",
        "Address": "3259 Hull Rd, Gainesville, FL 32608",
        "Description": "Campus art museum."
    },
    {
        "Building Number": "",
        "Building Name": "Harrell Medical Education Building",
        "Abbreviation": "HMEB",
        "Address": "1104 Newell Dr, Gainesville, FL 32610",
        "Description": "Medical education and simulation."
    },
    {
        "Building Number": "",
        "Building Name": "Health Center Annex #1",
        "Abbreviation": "HCA1",
        "Address": "1329 SW 16th St, Gainesville, FL 32608",
        "Description": "UF Health administrative offices."
    },
    {
        "Building Number": "",
        "Building Name": "Health Profession, Nursing, Pharmacy Building",
        "Abbreviation": "HPNP",
        "Address": "G205 HPNP Complex, P.O. Box 100185, Gainesville, FL 32610-0185",
        "Description": "Interprofessional healthcare education."
    },
    {
        "Building Number": "",
        "Building Name": "Heavener Hall",
        "Abbreviation": "HEAV",
        "Address": "340 Newell Dr, Gainesville, FL 32611",
        "Description": "Warrington College of Business."
    },
    {
        "Building Number": "",
        "Building Name": "Herbert Wertheim Laboratory for Engineering Excellence",
        "Abbreviation": "HWB",
        "Address": "1064 Center Dr, Gainesville, FL 32611",
        "Description": "Engineering innovation hub."
    },
    {
        "Building Number": "",
        "Building Name": "Hitchcock Field & Fork Pantry",
        "Abbreviation": "HFFP",
        "Address": "564 Newell Dr, Gainesville, FL 32611",
        "Description": "Student food pantry."
    },
    {
        "Building Number": "",
        "Building Name": "Holland Law Center",
        "Abbreviation": "HLC",
        "Address": "164 Holland Hall, P.O. Box 117621, Gainesville, FL 32611-7621",
        "Description": "Law school facilities."
    },
    {
        "Building Number": "",
        "Building Name": "Honors Village",
        "Abbreviation": "HONV",
        "Address": "1331 Stadium Rd, Gainesville, FL 32611",
        "Description": "Residential community for honors students."
    },
    {
        "Building Number": "",
        "Building Name": "Hough Hall",
        "Abbreviation": "HOUG",
        "Address": "340 Newell Dr, Gainesville, FL 32611",
        "Description": "Business school classrooms."
    },
    {
        "Building Number": "",
        "Building Name": "Housing Office",
        "Abbreviation": "HOUS",
        "Address": "1304 Diamond Rd, Gainesville, FL 32611",
        "Description": "Housing administration."
    },
    {
        "Building Number": "",
        "Building Name": "Human Development Center",
        "Abbreviation": "HDC",
        "Address": "1604 McCarty Dr, Gainesville, FL 32611",
        "Description": "Special education and psychology services."
    },
    {
        "Building Number": "",
        "Building Name": "Human Resources Building",
        "Abbreviation": "HRB",
        "Address": "903 W University Ave, Gainesville, FL 32601-5117",
        "Description": "HR services and offices."
    },
    {
        "Building Number": "",
        "Building Name": "Hume Hall",
        "Abbreviation": "HUME",
        "Address": "1223 Museum Rd, Gainesville, FL 32611",
        "Description": "Honors residential hall."
    },
    {
        "Building Number": "",
        "Building Name": "Indoor Practice Facility",
        "Abbreviation": "IPF",
        "Address": "2510 Lemerand Drive, Gainesville, FL 32611",
        "Description": "Athletic training facility."
    },
    {
        "Building Number": "",
        "Building Name": "Infinity Hall",
        "Abbreviation": "INF",
        "Address": "978 SW 8th Ave, Gainesville, FL 32601",
        "Description": "Residential hall."
    },
    {
        "Building Number": "",
        "Building Name": "Infirmary Hall",
        "Abbreviation": "INFIRM",
        "Address": "280 Fletcher Dr, Gainesville, FL 32611",
        "Description": "Former infirmary, now offices."
    },
    {
        "Building Number": "",
        "Building Name": "Institute of Black Culture",
        "Abbreviation": "IBC",
        "Address": "1510 W University Ave, Gainesville, FL 32603",
        "Description": "Cultural and educational center."
    },
    {
        "Building Number": "",
        "Building Name": "Institute of Hispanic/Latino Culture",
        "Abbreviation": "IHLC",
        "Address": "1504 W University Ave, Gainesville, FL 32603",
        "Description": "Hispanic/Latino cultural center."
    },
    {
        "Building Number": "",
        "Building Name": "James G. Pressly Stadium",
        "Abbreviation": "PRESS",
        "Address": "2800 SW 13th St, Gainesville, FL 32608",
        "Description": "Track and field stadium."
    },
    {
        "Building Number": "",
        "Building Name": "Jennings Hall",
        "Abbreviation": "JENN",
        "Address": "1330 Stadium Rd, Gainesville, FL 32611",
        "Description": "Residential hall."
    },
    {
        "Building Number": "",
        "Building Name": "Johnson Hall",
        "Abbreviation": "JOH",
        "Address": "1100 Stadium Rd, Gainesville, FL 32611",
        "Description": "Academic advising and classrooms."
    },
    {
        "Building Number": "",
        "Building Name": "Keys Residential Complex",
        "Abbreviation": "KEYS",
        "Address": "1231 SW 9th Rd, Gainesville, FL 32601",
        "Description": "Apartment-style housing."
    },
    {
        "Building Number": "",
        "Building Name": "Lakeside Residential Complex",
        "Abbreviation": "LAKE",
        "Address": "1275 Stadium Rd, Gainesville, FL 32611",
        "Description": "On-campus apartments."
    },
    {
        "Building Number": "",
        "Building Name": "Larsen Hall",
        "Abbreviation": "LARS",
        "Address": "207 Stadium Rd, Gainesville, FL 32611",
        "Description": "Residential hall."
    },
    {
        "Building Number": "",
        "Building Name": "Law Advocacy Center",
        "Abbreviation": "LAC",
        "Address": "2500 SW 2nd Ave, Gainesville, FL 32607",
        "Description": "Moot court and law competitions."
    },
    {
        "Building Number": "",
        "Building Name": "Leigh Hall",
        "Abbreviation": "LEIGH",
        "Address": "1365 Union Rd, Gainesville, FL 32611",
        "Description": "Engineering and tech labs."
    },
    {
        "Building Number": "",
        "Building Name": "Lemerand Center",
        "Abbreviation": "LEM",
        "Address": "1329 SW 16th St, Gainesville, FL 32610",
        "Description": "Clinical research and patient care."
    },
    {
        "Building Number": "",
        "Building Name": "Library West",
        "Abbreviation": "LIBW",
        "Address": "1545 W University Ave, Gainesville, FL 32603",
        "Description": "Main university library."
    },
    {
        "Building Number": "",
        "Building Name": "Linder Tennis Stadium",
        "Abbreviation": "LIND",
        "Address": "2800 SW 13th St, Gainesville, FL 32608",
        "Description": "Tennis competition venue."
    },
    {
        "Building Number": "",
        "Building Name": "Lipoff Hall",
        "Abbreviation": "LIPO",
        "Address": "1600 SW Archer Rd, Gainesville, FL 32610",
        "Description": "Health Science Center offices."
    },
    {
        "Building Number": "",
        "Building Name": "Little Hall",
        "Abbreviation": "LIT",
        "Address": "2 Stadium Rd, Gainesville, FL 32611",
        "Description": "Mathematics department."
    },
    {
        "Building Number": "",
        "Building Name": "Little Hall Express",
        "Abbreviation": "LHE",
        "Address": "4 Stadium Rd, Gainesville, FL 32611",
        "Description": "Math tutoring center."
    },
    {
        "Building Number": "",
        "Building Name": "Maguire Village",
        "Abbreviation": "MAG",
        "Address": "34 Maguire Village, Gainesville, FL 32603",
        "Description": "Graduate and family housing."
    },
    {
        "Building Number": "",
        "Building Name": "Malachowsky Hall for Data Science & Information Technology",
        "Abbreviation": "MHD",
        "Address": "1064 Center Dr, Gainesville, FL 32611",
        "Description": "Data science and IT research (opened 2023)."
    },
    {
        "Building Number": "",
        "Building Name": "Mallory Hall",
        "Abbreviation": "MALL",
        "Address": "1474 Union Rd, Gainesville, FL 32611",
        "Description": "Residential hall."
    },
    {
        "Building Number": "",
        "Building Name": "Mark Bostick Golf Clubhouse",
        "Abbreviation": "BOST",
        "Address": "2800 SW 2nd Ave, Gainesville, FL 32607",
        "Description": "Golf course and clubhouse."
    },
    {
        "Building Number": "",
        "Building Name": "Marston Science Library",
        "Abbreviation": "MAR",
        "Address": "444 Newell Dr, Gainesville, FL 32611",
        "Description": "Science and engineering library."
    },
    {
        "Building Number": "",
        "Building Name": "Material Engineering Building",
        "Abbreviation": "MAT",
        "Address": "549 Gale Lemerand Dr, Gainesville, FL 32611",
        "Description": "Materials science research."
    },
    {
        "Building Number": "",
        "Building Name": "Matherly Hall",
        "Abbreviation": "MATH",
        "Address": "1405 W University Ave, Gainesville, FL 32611",
        "Description": "Economics and business departments."
    },
    {
        "Building Number": "",
        "Building Name": "McCarty Hall A",
        "Abbreviation": "MC A",
        "Address": "1680 Union Rd, Gainesville, FL 32611",
        "Description": "Residential hall."
    },
    {
        "Building Number": "",
        "Building Name": "McCarty Hall B",
        "Abbreviation": "MC B",
        "Address": "1690 Union Rd, Gainesville, FL 32611",
        "Description": "Residential hall."
    },
    {
        "Building Number": "",
        "Building Name": "McCarty Hall C",
        "Abbreviation": "MC C",
        "Address": "1700 Union Rd, Gainesville, FL 32611",
        "Description": "Residential hall."
    },
    {
        "Building Number": "",
        "Building Name": "McCarty Hall D",
        "Abbreviation": "MC D",
        "Address": "2002 McCarty Hall D, P.O. Box 110270, Gainesville, FL 32611-0270",
        "Description": "Residential hall."
    },
    {
        "Building Number": "",
        "Building Name": "McGuire Center",
        "Abbreviation": "MCG",
        "Address": "1765 Stadium Rd, Gainesville, FL 32611",
        "Description": "Entrepreneurship and innovation center."
    },
    {
        "Building Number": "",
        "Building Name": "McKnight Brain Institute",
        "Abbreviation": "MBI",
        "Address": "1149 Newell Dr, Gainesville, FL 32611",
        "Description": "Neuroscience research institute."
    },
    {
        "Building Number": "",
        "Building Name": "Mechanical Engineering Building A",
        "Abbreviation": "MEB A",
        "Address": "939 Center Dr, Gainesville, FL 32611",
        "Description": "Mechanical engineering labs."
    },
    {
        "Building Number": "",
        "Building Name": "Mechanical Engineering Building B",
        "Abbreviation": "MEB B",
        "Address": "945 Center Dr, Gainesville, FL 32611",
        "Description": "Mechanical engineering facilities."
    },
    {
        "Building Number": "",
        "Building Name": "Mechanical Engineering Building C",
        "Abbreviation": "MEB C",
        "Address": "951 Center Dr, Gainesville, FL 32611",
        "Description": "Additional engineering labs."
    },
    {
        "Building Number": "",
        "Building Name": "Microbiology/Cell Science Building",
        "Abbreviation": "MIC",
        "Address": "1355 Museum Dr, Gainesville, FL 32611",
        "Description": "Microbiology research."
    },
    {
        "Building Number": "",
        "Building Name": "Multi Purpose Lab",
        "Abbreviation": "MPL",
        "Address": "2510 Lemerand Drive, Gainesville, FL 32611",
        "Description": "Athletic training and practice facility."
    },
    {
        "Building Number": "",
        "Building Name": "Murphree Hall",
        "Abbreviation": "MURP",
        "Address": "20 Fletcher Dr, Gainesville, FL 32611",
        "Description": "Residential hall."
    },
    {
        "Building Number": "",
        "Building Name": "Music Building",
        "Abbreviation": "MUS",
        "Address": "435 Newell Dr, Gainesville, FL 32611",
        "Description": "School of Music facilities."
    },
    {
        "Building Number": "",
        "Building Name": "Nanoscale Research Facility",
        "Abbreviation": "NRF",
        "Address": "218 MAE-A, Gainesville, FL 32611",
        "Description": "Nanotechnology research labs."
    },
    {
        "Building Number": "",
        "Building Name": "New Engineering Building",
        "Abbreviation": "NEB",
        "Address": "1064 Center Dr, Gainesville, FL 32611",
        "Description": "Engineering classrooms and labs."
    },
    {
        "Building Number": "",
        "Building Name": "Newell Hall",
        "Abbreviation": "NEWL",
        "Address": "985 Museum Rd, Gainesville, FL 32611",
        "Description": "Study spaces and classrooms."
    },
    {
        "Building Number": "",
        "Building Name": "Newins-Ziegler Hall",
        "Abbreviation": "NZH",
        "Address": "Newins-Ziegler Hall, Gainesville, FL 32611",
        "Description": "Agricultural and Life Sciences."
    },
    {
        "Building Number": "",
        "Building Name": "Norman Gym",
        "Abbreviation": "NORM",
        "Address": "1390 Stadium Rd, Gainesville, FL 32611",
        "Description": "Recreational sports facility."
    },
    {
        "Building Number": "",
        "Building Name": "Norman Hall",
        "Abbreviation": "NORM",
        "Address": "140 Norman Hall, P.O. Box 117040, Gainesville, FL 32611-7040",
        "Description": "College of Education."
    },
    {
        "Building Number": "",
        "Building Name": "North Hall",
        "Abbreviation": "NORTH",
        "Address": "175 Stadium Rd, Gainesville, FL 32611",
        "Description": "Residential hall."
    },
    {
        "Building Number": "",
        "Building Name": "Nuclear Sciences Building",
        "Abbreviation": "NSB",
        "Address": "202 Nuclear Sciences Ctr, Gainesville, FL 32611",
        "Description": "Nuclear engineering research."
    },
    {
        "Building Number": "",
        "Building Name": "O'Connell Center",
        "Abbreviation": "O'DOME",
        "Address": "250 Gale Lemerand Dr, Gainesville, FL 32611",
        "Description": "Arena for sports and events."
    },
    {
        "Building Number": "",
        "Building Name": "Observatory",
        "Abbreviation": "OBS",
        "Address": "209 Bryant Space Science Center, Gainesville, FL 32611",
        "Description": "Astronomical observatory."
    },
    {
        "Building Number": "",
        "Building Name": "Orthopaedics and Sports Medicine Institute",
        "Abbreviation": "OSMI",
        "Address": "3450 Hull Rd, Gainesville, FL 32608",
        "Description": "Orthopedic care and research."
    },
    {
        "Building Number": "",
        "Building Name": "P.K. Yonge Developmental Research School",
        "Abbreviation": "PKY",
        "Address": "1080 SW 11th St, Gainesville, FL 32601",
        "Description": "K-12 laboratory school."
    },
    {
        "Building Number": "",
        "Building Name": "Particle Science Technology Building",
        "Abbreviation": "PSTB",
        "Address": "2300 NE 8th Ave, Gainesville, FL 32641",
        "Description": "Particle science research."
    },
    {
        "Building Number": "",
        "Building Name": "Patient Services Building",
        "Abbreviation": "PSB",
        "Address": "1600 SW Archer Rd, Gainesville, FL 32610",
        "Description": "UF Health outpatient services."
    },
    {
        "Building Number": "",
        "Building Name": "Peabody Hall",
        "Abbreviation": "PEA",
        "Address": "301 Peabody Hall, Gainesville, FL 32611",
        "Description": "College of Education."
    },
    {
        "Building Number": "",
        "Building Name": "Phelps Lab",
        "Abbreviation": "PHELP",
        "Address": "1268 Center Dr, Gainesville, FL 32611",
        "Description": "Psychology research labs."
    },
    {
        "Building Number": "",
        "Building Name": "Phillips Center",
        "Abbreviation": "PHIL",
        "Address": "3201 Hull Rd, Gainesville, FL 32611",
        "Description": "Performing arts venue."
    },
    {
        "Building Number": "",
        "Building Name": "Physics Building",
        "Abbreviation": "PHYS",
        "Address": "2001 Museum Rd, Gainesville, FL 32611",
        "Description": "Physics department and classrooms."
    },
    {
        "Building Number": "",
        "Building Name": "Reitz Union",
        "Abbreviation": "REITZ",
        "Address": "Museum Road, P.O. Box 118505, Gainesville, FL 32611-8505",
        "Description": "Student union building."
    },
    {
        "Building Number": "",
        "Building Name": "Rinker Hall",
        "Abbreviation": "RH",
        "Address": "304 Rinker Hall, P.O. Box 115703, Gainesville, FL 32611-5703",
        "Description": "School of Building Construction."
    },
    {
        "Building Number": "",
        "Building Name": "Shands Hospital",
        "Abbreviation": "SHANDS",
        "Address": "1600 SW Archer Rd, Gainesville, FL 32610",
        "Description": "UF Health's main hospital."
    },
    {
        "Building Number": "",
        "Building Name": "Smathers Library",
        "Abbreviation": "LIB E",
        "Address": "1508 Union Rd, Gainesville, FL 32611",
        "Description": "University library (Library East)."
    },
    {
        "Building Number": "",
        "Building Name": "Thomas Hall",
        "Abbreviation": "THO",
        "Address": "1401 Stadium Rd, Gainesville, FL 32611",
        "Description": "Residential housing for upper-division students."
    },
    {
        "Building Number": "",
        "Building Name": "Tigert Hall",
        "Abbreviation": "TIG",
        "Address": "226 Tigert Hall, P.O. Box 113150, Gainesville, FL 32611-3150",
        "Description": "Main administration building."
    },
    {
        "Building Number": "",
        "Building Name": "University Auditorium",
        "Abbreviation": "AUD",
        "Address": "333 Newell Dr, Gainesville, FL 32611",
        "Description": "Performance venue."
    },
    {
        "Building Number": "",
        "Building Name": "Weil Hall",
        "Abbreviation": "WEIL",
        "Address": "312 Weil Hall, P.O. Box 116550, Gainesville, FL 32611-6550",
        "Description": "College of Engineering."
    },
    {
        "Building Number": "",
        "Building Name": "Weimer Hall",
        "Abbreviation": "WEIM",
        "Address": "1000 Weimer Hall, P.O. Box 118400, Gainesville, FL 32611-8400",
        "Description": "College of Journalism and Communications."
    },
    {
        "Building Number": "",
        "Building Name": "Yulee Hall",
        "Abbreviation": "YUL",
        "Address": "12 Fletcher Dr, Gainesville, FL 32611",
        "Description": "Residential hall."
    }
]

# =============================================================================
# HOUSING DATA
# =============================================================================

# Housing information embedded directly in the code
HOUSING_DATA = [
    {
        "name": "Beaty Towers",
        "hall_type": "Apartment Style",
        "description": "Beaty Towers is a centrally located apartment style building. Located on the corner of Museum Road and 13th Street, Beaty Towers is close to the College of Music, Design Construction and Planning, and a short walk to the Warrington College of Business. Each apartment features double room suites with a semi-private bathroom, built in desks, and a kitchenette complete with a refrigerator, oven, and garbage disposal.",
        "location": "11 Beaty Towers, Gainesville, FL 32612-1101",
        "phone": "352-392-6111",
        "features": [
            "Fully Furnished", 
            "Twin XL Beds", 
            "Passenger Elevators", 
            "High-Speed Internet", 
            "Laundry Facilities", 
            "The Market in Beaty Towers", 
            "Game Room"
        ],
        "room_types": [
            "Apartments", 
            "Steinbrenner Band Hall", 
            "College of Design Construction and Planning", 
            "College of Architecture", 
            "Sorority Row"
        ],
        "nearby_locations": [
            "Apartments", 
            "Steinbrenner Band Hall", 
            "College of Design Construction and Planning", 
            "College of Architecture", 
            "Sorority Row"
        ],
        "url": "https://housing.ufl.edu/beaty-towers/",
        "image_url": "https://housing.ufl.edu/wp-content/uploads/2022/02/2012_BEATY_sky_blue_exterior_05_22_0134_POST-scaled.jpg",
        "rental_rate_url": "https://housing.ufl.edu/rates-payments-agreements/residence-hall-rental-rates/"
    },
    {
        "name": "Broward Hall",
        "hall_type": "Traditional Style",
        "description": "Broward Hall is a fully furnished traditional style hall located near various colleges and libraries. Students living in Broward Hall will be steps away from the Broward Dining Hall, Century Tower, and the Plaza of the Americas. Broward Hall offers a range of room styles including single, double, and triple options. Each floor has a shared restroom and community kitchen, that offers a microwave, oven, and stove. It is recommended for students to supply their own in-room refrigerator.",
        "location": "680 Broward Dr., Gainesville, FL 32612",
        "phone": "352-392-6051",
        "features": [
            "Fully Furnished", 
            "Twin XL Beds", 
            "Passenger Elevator", 
            "High-Speed WiFi", 
            "Laundry Room", 
            "Study Lounge", 
            "Game Room"
        ],
        "room_types": [
            "Single Room", 
            "Double Room", 
            "Triple Room", 
            "College of Education", 
            "College of the Arts", 
            "College of Design, Construction and Planning", 
            "Century Tower", 
            "The Eatery at Broward Hall", 
            "Turlington Plaza", 
            "Library West"
        ],
        "nearby_locations": [
            "Single Room", 
            "Double Room", 
            "Triple Room", 
            "College of Education", 
            "College of the Arts", 
            "College of Design, Construction and Planning", 
            "Century Tower", 
            "The Eatery at Broward Hall", 
            "Turlington Plaza", 
            "Library West"
        ],
        "url": "https://housing.ufl.edu/broward-hall/",
        "image_url": "https://housing.ufl.edu/wp-content/uploads/2022/02/2011_BrowardArea_TOPBuildingExterior-3_noLogo-scaled.jpg",
        "rental_rate_url": "https://housing.ufl.edu/rates-payments-agreements/residence-hall-rental-rates/"
    },
    {
        "name": "Buckman Hall",
        "hall_type": "Traditional Style",
        "description": "Buckman Hall is located in the University's historic district. Buckman Hall is unique in that no two rooms have the same layout, so you can guarantee you will have a unique picturesque room. This hall is located near on-campus and off-campus dining locations, the Student Recreation Center, the Hub, Newell Hall, and Library West. Each floor has a shared restroom and a community kitchen, that offers a stove, oven, and microwave. It is recommended for students to supply their own in-room refrigerator.",
        "location": "132 Buckman Dr., Gainesville, FL 32612",
        "phone": "352-392-6091",
        "features": [
            "Fully Furnished", 
            "Twin XL Beds", 
            "High-Speed WiFi", 
            "Laundry Room", 
            "Study Lounge", 
            "Game Room"
        ],
        "room_types": [
            "Single Room", 
            "Double Room", 
            "Triple Room", 
            "Newell Hall", 
            "Library West", 
            "College of Liberal Arts and Sciences", 
            "College of Journalism and Communications", 
            "College of Health and Human Performance", 
            "The Hub"
        ],
        "nearby_locations": [
            "Single Room", 
            "Double Room", 
            "Triple Room", 
            "Newell Hall", 
            "Library West", 
            "College of Liberal Arts and Sciences", 
            "College of Journalism and Communications", 
            "College of Health and Human Performance", 
            "The Hub"
        ],
        "url": "https://housing.ufl.edu/buckman-hall/",
        "image_url": "https://housing.ufl.edu/wp-content/uploads/2022/02/2011_MurphreeArea_ThomasBuildingExterior-1-2.jpg",
        "rental_rate_url": "https://housing.ufl.edu/rates-payments-agreements/residence-hall-rental-rates/"
    },
    {
        "name": "Corry Village",
        "hall_type": "Apartment Style",
        "description": "Corry Village is centrally located on the University of Florida Campus. The village features a new community center at the front of the complex, playgrounds for children, and residential parking. Apartments are outfitted with a full kitchen including a full-size range, oven, and refrigerator. Rent includes internet access, water, and a community center with access to movies, games, and equipment you can check out at no additional charge.",
        "location": "278 Corry Village, Gainesville, FL 32603",
        "phone": "352-392-6081",
        "features": [
            "Laundry Room", 
            "Cable TV", 
            "Play Room for Children", 
            "Playground", 
            "Study Room", 
            "Basketball Court", 
            "Volleyball Court", 
            "Barbeque Areas"
        ],
        "room_types": [
            "One Bedroom Apartment", 
            "Two Bedroom Apartment", 
            "College of Law", 
            "Baby Gator Child Development Center", 
            "Lake Alice", 
            "Field and Fork Farm and Gardens", 
            "UF Bat Houses"
        ],
        "nearby_locations": [
            "One Bedroom Apartment", 
            "Two Bedroom Apartment", 
            "College of Law", 
            "Baby Gator Child Development Center", 
            "Lake Alice", 
            "Field and Fork Farm and Gardens", 
            "UF Bat Houses"
        ],
        "url": "https://housing.ufl.edu/corry-village/",
        "image_url": "https://housing.ufl.edu/wp-content/uploads/2022/02/DSC1782-scaled.jpg",
        "rental_rate_url": "https://housing.ufl.edu/rates-payments-agreements/graduate-and-family-housing-rental-rates/"
    },
    {
        "name": "Cypress Hall",
        "hall_type": "Suite Style",
        "description": "One of the newest residence halls on campus, Cypress Hall and offers universally designed single, double and super suite style rooms. Cypress hosts a limited number of rooms with SureHands Lift system for students with physical impairments and approved housing accommodations. Located on the east side of campus, Cypress Hall is near the Broward Dining Hall, the College of Education, and the College of the Arts. Each floor has a community kitchen, that offers an oven and stove. It is recommended for students to supply their own in-room microwave and refrigerator.",
        "location": "1310 Museum Rd. Gainesville, FL 32612",
        "phone": "352-392-6101",
        "features": [
            "Fully Furnished", 
            "Full XL Beds", 
            "Passenger Elevators", 
            "High-Speed WiFi", 
            "Laundry Room", 
            "Study Lounge"
        ],
        "room_types": [
            "Single Suite", 
            "Double Suite", 
            "Super Suite", 
            "College of Education", 
            "College of the Arts", 
            "College of Design Construction and Planning", 
            "Beaty P.O.D. Market"
        ],
        "nearby_locations": [
            "Single Suite", 
            "Double Suite", 
            "Super Suite", 
            "College of Education", 
            "College of the Arts", 
            "College of Design Construction and Planning", 
            "Beaty P.O.D. Market"
        ],
        "url": "https://housing.ufl.edu/cypress-hall/",
        "image_url": "https://housing.ufl.edu/wp-content/uploads/2022/02/170503_Buildings_UFCypressHall_0008_MattPendleton-scaled.jpg",
        "rental_rate_url": "https://housing.ufl.edu/rates-payments-agreements/residence-hall-rental-rates/"
    },
    {
        "name": "Diamond Village",
        "hall_type": "Apartment Style",
        "description": "Diamond Village is located on the southeast side of campus and is near UF Shands, the College of Medicine, and the College of Dentistry. Diamond Village is ideal for individuals and families that are environmentally conscious; the community features solar panels, a community herb and butterfly garden, rain barrels, and a cistern garden. With an on site playroom, basketball court, and Baby Gator Child Development Center, Diamond Village is perfect for families with young children.",
        "location": "University of Florida, Gainesville, FL 32603",
        "phone": "352-392-6081",
        "features": [
            "High Speed Internet", 
            "Laundry Facilities", 
            "The Market in Beaty Towers", 
            "Game Room"
        ],
        "room_types": [
            "One Bedroom Apartment", 
            "Two Bedroom Apartment", 
            "College of Medicine", 
            "UF Health Shands", 
            "College of Dentistry", 
            "Baby Gator Child Development Center"
        ],
        "nearby_locations": [
            "One Bedroom Apartment", 
            "Two Bedroom Apartment", 
            "College of Medicine", 
            "UF Health Shands", 
            "College of Dentistry", 
            "Baby Gator Child Development Center"
        ],
        "url": "https://housing.ufl.edu/diamond-village/",
        "image_url": "https://housing.ufl.edu/wp-content/uploads/2022/02/2011_Diamond_BuildingExterior-24-scaled.jpg",
        "rental_rate_url": "https://housing.ufl.edu/rates-payments-agreements/graduate-and-family-housing-rental-rates/"
    },
    {
        "name": "East Hall",
        "hall_type": "Traditional Style",
        "description": "East Hall is located directly across the street from the Herbert Wertheim College of Engineering, making it the ideal location for the Engineering Living Learning Community. Students living in East hall will have easy access to athletic events, a swimming pool, Flavet Field, and the Reitz Union.  East Hall offers double and triple style rooms options. Each floor has a shared restroom and a community kitchen, that offers a microwave, oven, and stove. It is recommended for students to supply their own in-room refrigerator.",
        "location": "1310 Museum Rd., Gainesville, FL 32612",
        "phone": "352-392-6101",
        "features": [
            "Fully Furnished", 
            "Twin XL Bed", 
            "Passenger Elevator", 
            "High-Speed WiFi", 
            "Laundry Room", 
            "Study Lounge"
        ],
        "room_types": [
            "Double Room", 
            "Triple Room", 
            "Reitz Union", 
            "College of Engineering", 
            "Flavet Field", 
            "Graham Pool", 
            "Stephen C. O'Connell Center", 
            "Ben Hill Griffin Stadium", 
            "James G. Pressley Field"
        ],
        "nearby_locations": [
            "Double Room", 
            "Triple Room", 
            "Reitz Union", 
            "College of Engineering", 
            "Flavet Field", 
            "Graham Pool", 
            "Stephen C. O'Connell Center", 
            "Ben Hill Griffin Stadium", 
            "James G. Pressley Field"
        ],
        "url": "https://housing.ufl.edu/east-hall/",
        "image_url": "https://housing.ufl.edu/wp-content/uploads/2022/02/2012_TolbertArea_Exterior_IMG_7485_POST-scaled.jpg",
        "rental_rate_url": "https://housing.ufl.edu/rates-payments-agreements/residence-hall-rental-rates/"
    },
    {
        "name": "Fletcher Hall",
        "hall_type": "Traditional Style",
        "description": "Fletcher Hall is is located in the University's historic district. Being in the historic district means that no two rooms are alike so you're guaranteed to have a unique picturesque room. This hall is located near on and off campus dining locations, the Student Recreation Center, the Hub, Newell Hall, and Library West. Each floor has a shared restroom and community kitchen that offers a stove and microwave. It is recommended for students to supply their own in-room refrigerator.",
        "location": "72 Buckman Dr., Gainesville, FL 32612",
        "phone": "352-392-6091",
        "features": [
            "Fully Furnished", 
            "Twin XL Bed", 
            "High-Speed WiFi", 
            "Laundry Room", 
            "Study Lounge", 
            "Game Room"
        ],
        "room_types": [
            "Single Room", 
            "Double Room", 
            "Two Room Double", 
            "Triple Room", 
            "Two Room Triple", 
            "Newell Hall", 
            "Library West", 
            "College of Liberal Arts and Sciences", 
            "College of Journalism and Communications", 
            "College of Health and Human Performance", 
            "The Hub"
        ],
        "nearby_locations": [
            "Single Room", 
            "Double Room", 
            "Two Room Double", 
            "Triple Room", 
            "Two Room Triple", 
            "Newell Hall", 
            "Library West", 
            "College of Liberal Arts and Sciences", 
            "College of Journalism and Communications", 
            "College of Health and Human Performance", 
            "The Hub"
        ],
        "url": "https://housing.ufl.edu/fletcher-hall/",
        "image_url": "https://housing.ufl.edu/wp-content/uploads/2022/02/EZ_20120203_UF_campus_beauty_0040-scaled.jpg",
        "rental_rate_url": "https://housing.ufl.edu/rates-payments-agreements/residence-hall-rental-rates/"
    },
    {
        "name": "Graham Hall",
        "hall_type": "Traditional Style",
        "description": "Graham Hall is a traditional residence hall located in the Graham Area, offering double rooms for students. With its location on the corner of Museum Road and Gale Lemerand Drive, residents have easy access to the Reitz Union, athletic venues, and recreational fields. The hall features The Market in Graham Hall for convenient dining options, as well as a swimming pool and recreation room. Each floor has a shared restroom and community kitchen. It is recommended for students to supply their own in-room refrigerator.",
        "location": "21 Graham Area, Gainesville, FL 32612",
        "phone": "352-392-6021",
        "features": [
            "Fully Furnished", 
            "Twin XL Bed", 
            "Swimming Pool", 
            "The Market in Graham Hall", 
            "Laundry Room", 
            "Study Space", 
            "Game Room", 
            "Recreation Room", 
            "Freight Elevator"
        ],
        "room_types": [
            "Double Room", 
            "Herbert Wertheim College of Engineering", 
            "College of Journalism and Communications", 
            "Newell Hall", 
            "Flavet Field", 
            "Gator Corner Dining", 
            "Ben Hill Griffin Stadium", 
            "Stephen C. O'Connell Center"
        ],
        "nearby_locations": [
            "Double Room", 
            "Herbert Wertheim College of Engineering", 
            "College of Journalism and Communications", 
            "Newell Hall", 
            "Flavet Field", 
            "Gator Corner Dining", 
            "Ben Hill Griffin Stadium", 
            "Stephen C. O'Connell Center"
        ],
        "url": "https://housing.ufl.edu/graham-hall/",
        "image_url": "https://housing.ufl.edu/wp-content/uploads/2022/02/GRAHAM_P4118067_FB.jpg",
        "rental_rate_url": "https://housing.ufl.edu/rates-payments-agreements/residence-hall-rental-rates/"
    },
    {
        "name": "Honors Village",
        "hall_type": "Traditional & Suite Style",
        "description": "Currently under construction, the brand-new Honors Village will serve honors residents. Located on the east side of campus and spanning five buildings, four Residence Halls and a Learning Commons, the village will feature four room types. Each floor includes a kitchen, lounge, social space, study space, a centrally located laundry room with washers/dryers, folding tables and various seating locations. Additionally, the first floor of each building will feature a unique programming space based on the building theme such as a meditation space, library, ensemble and private music practice rooms, makers space, and classroom/study spaces. The Main Desk located in the Learning Commons will feature package lockers and a printer station accessible to residents. Nearby residents will find food locations such as The Eatery at Broward Hall, The Market at Beaty Towers or the Hub.",
        "location": "1512 Museum Rd. Gainesville, FL 32612",
        "phone": "352-846-4987",
        "features": [
            "Fully Furnished", 
            "Dual Passenger Elevators in Each Building", 
            "High-Speed WiFi", 
            "Laundry Rooms on Every Residential Floor", 
            "Classroom/Study Spaces", 
            "Makers Space", 
            "Meditation Space", 
            "Ensemble and Private Music Practice Rooms", 
            "Centrally located Private Bathrooms", 
            "Package Lockers", 
            "Printer Stations"
        ],
        "room_types": [
            "Traditional Single", 
            "Traditional Double", 
            "Suite Single with Semi-Private Bathroom", 
            "Suite Double with Semi-Private Bathroom", 
            "College of Education", 
            "College of the Arts", 
            "College of Design Construction and Planning", 
            "The Eatery at Broward Hall", 
            "The Market in Beaty Towers", 
            "Century Tower"
        ],
        "nearby_locations": [
            "Traditional Single", 
            "Traditional Double", 
            "Suite Single with Semi-Private Bathroom", 
            "Suite Double with Semi-Private Bathroom", 
            "College of Education", 
            "College of the Arts", 
            "College of Design Construction and Planning", 
            "The Eatery at Broward Hall", 
            "The Market in Beaty Towers", 
            "Century Tower"
        ],
        "url": "https://housing.ufl.edu/honors-village/",
        "image_url": "https://housing.ufl.edu/wp-content/uploads/2023/11/20231120_HRL_Honors-Village-Exterior_DW2_4898-scaled.jpg",
        "rental_rate_url": "https://housing.ufl.edu/rates-payments-agreements/residence-hall-rental-rates/"
    },
    {
        "name": "Hume Hall",
        "hall_type": "Suite Style Hall",
        "description": "Students living in Hume Hall can expect short travel times to the Reitz Union, Flavet Field, fraternity row, athletic venues and outdoor recreation fields. Each floor has options for single or double suites, a community kitchen that offers a microwave, oven and stove. It is recommended for students to supply their own in-room refrigerator.",
        "location": "19 Hume Honors Residential College  Gainesville, FL 32612",
        "phone": "352-392-6011",
        "features": [
            "Fully Furnished", 
            "Twin XL Beds", 
            "Semi-Private Bathrooms", 
            "Passenger Elevator", 
            "High-Speed Internet", 
            "Hume Classroom", 
            "Study Room", 
            "Laundry Room", 
            "Game Room"
        ],
        "room_types": [
            "Single Room Suite", 
            "Double Room Suite", 
            "Reitz Union", 
            "Marston's Science Library", 
            "Newell Hall", 
            "Outdoor Fields", 
            "Gator Corner Dining", 
            "Graham Pool", 
            "Ben Hill Griffin Stadium", 
            "Stephen C. O'Connell Center"
        ],
        "nearby_locations": [
            "Single Room Suite", 
            "Double Room Suite", 
            "Reitz Union", 
            "Marston's Science Library", 
            "Newell Hall", 
            "Outdoor Fields", 
            "Gator Corner Dining", 
            "Graham Pool", 
            "Ben Hill Griffin Stadium", 
            "Stephen C. O'Connell Center"
        ],
        "url": "https://housing.ufl.edu/hume-hall/",
        "image_url": "https://housing.ufl.edu/wp-content/uploads/2022/02/170614_Buildings_UFHumeHall_Exterior_4534_MattPendleton-scaled.jpg",
        "rental_rate_url": "https://housing.ufl.edu/rates-payments-agreements/residence-hall-rental-rates/"
    },
    {
        "name": "Infinity Hall",
        "hall_type": "Suite Style",
        "description": "Infinity Hall is a modern suite-style residence hall located in Innovation Square, just a short walk from campus. Designed for entrepreneurial and innovation-minded students, it features a Maker Space and collaborative areas. Each suite includes semi-private bathrooms and is fully furnished. With its unique off-campus location, Infinity Hall provides easy access to downtown Gainesville while maintaining proximity to the university.",
        "location": "978 SW 2nd Ave., Gainesville, FL 32601",
        "phone": "352-392-9675",
        "features": [
            "Fully Furnished", 
            "Twin XL Beds", 
            "Semi-Private Bathroom", 
            "Passenger Elevator", 
            "High-Speed Internet", 
            "Maker Space", 
            "Laundry Room", 
            "Social Lounges", 
            "Private Study Room", 
            "Game Room"
        ],
        "room_types": [
            "Single Suite", 
            "Double Suite", 
            "Super Suite", 
            "Warrington College of Business", 
            "College of the Arts", 
            "College of Education", 
            "Library West", 
            "Marston's Science Library", 
            "Downtown Gainesville"
        ],
        "nearby_locations": [
            "Single Suite", 
            "Double Suite", 
            "Super Suite", 
            "Warrington College of Business", 
            "College of the Arts", 
            "College of Education", 
            "Library West", 
            "Marston's Science Library", 
            "Downtown Gainesville"
        ],
        "url": "https://housing.ufl.edu/infinity-hall/",
        "image_url": "https://housing.ufl.edu/wp-content/uploads/2022/02/2015-09-02_Infinity_Hall01675-scaled.jpg",
        "rental_rate_url": "https://housing.ufl.edu/rates-payments-agreements/residence-hall-rental-rates/"
    },
    {
        "name": "Jennings Hall",
        "hall_type": "Traditional Style",
        "description": "Jennings Hall is a traditional-style residence hall that offers double and triple rooms. Located near on-campus dining options, sorority row, the College of Music, College of Design Construction and Planning, and a short walk to the Warrington College of Business. Each floor has a shared restroom and community kitchen equipped with a microwave, range, oven, and stove. It is recommended for students to supply their own in-room refrigerator.",
        "location": "1509 Museum Rd., Gainesville, FL 32612",
        "phone": "352-392-6061",
        "features": [
            "Fully Furnished", 
            "Twin XL Beds", 
            "High-Speed Internet", 
            "Passenger Elevator", 
            "Laundry Facilities", 
            "Game Room"
        ],
        "room_types": [
            "Double Room", 
            "Triple Room", 
            "The Market in Beaty Towers", 
            "Broward Dining Hall", 
            "Steinbrenner Band Hall", 
            "College of Design Construction and Planning", 
            "College of Architecture", 
            "Sorority Row"
        ],
        "nearby_locations": [
            "Double Room", 
            "Triple Room", 
            "The Market in Beaty Towers", 
            "Broward Dining Hall", 
            "Steinbrenner Band Hall", 
            "College of Design Construction and Planning", 
            "College of Architecture", 
            "Sorority Row"
        ],
        "url": "https://housing.ufl.edu/jennings-hall/",
        "image_url": "https://housing.ufl.edu/wp-content/uploads/2022/01/220511_HRL_JenningsHall_046.jpg",
        "rental_rate_url": "https://housing.ufl.edu/rates-payments-agreements/residence-hall-rental-rates/"
    },
    {
        "name": "Keys Residential Complex",
        "hall_type": "Apartment Style",
        "description": "Keys Residential Complex is an ideal living option for students who love apartment style living. Located near athletic venues, Flavet Field, Gator Corner Dining, and fraternity row means you will always have somewhere to go or something to do. Each apartment is fully furnished with full-size beds, a couch in the living room, a kitchen with a stove, oven, refrigerator, and microwave.",
        "location": "44 Keys Residential College, Gainesville, FL 32612",
        "phone": "352-392-8107",
        "features": [
            "Fully Furnished", 
            "Full XL Beds", 
            "Laundry Room", 
            "Social Lounges", 
            "Study Space", 
            "Game Room"
        ],
        "room_types": [
            "Four Bedroom Apartments", 
            "James G. Pressley Stadium", 
            "Stephen C. O'Connell Center", 
            "Ben Hill Griffin Stadium", 
            "Flavet Field", 
            "College of Engineering", 
            "Reitz Union"
        ],
        "nearby_locations": [
            "Four Bedroom Apartments", 
            "James G. Pressley Stadium", 
            "Stephen C. O'Connell Center", 
            "Ben Hill Griffin Stadium", 
            "Flavet Field", 
            "College of Engineering", 
            "Reitz Union"
        ],
        "url": "https://housing.ufl.edu/keys-residential-complex/",
        "image_url": "https://housing.ufl.edu/wp-content/uploads/2023/09/230607_HRL_KeysResidenceComplex_0055-HDR.jpg",
        "rental_rate_url": "https://housing.ufl.edu/rates-payments-agreements/residence-hall-rental-rates/"
    },
    {
        "name": "Lakeside Residential Complex",
        "hall_type": "Apartment Style",
        "description": "Lakeside Residential Complex is perfect for active students. Located near Florida Field, Katie Seashole Pressley Stadium, Lake Alice, and the UF Bat Houses. With plenty of outdoor recreational spaces there is plenty to do. Lakeside offers private fully furnished bedrooms, shared common spaces, and no need for a mini fridge, you will have a full kitchen with full size appliances exclusively for you and your roommates.",
        "location": "51 Lakeside Complex, Gainesville, FL 32612",
        "phone": "352-392-1453",
        "features": [
            "Fully Furnished", 
            "Twin XL Bed", 
            "Private Bedroom", 
            "Passenger Elevator", 
            "High-Speed Internet", 
            "Outdoor Volleyball Court", 
            "Laundry Room", 
            "Study Spaces", 
            "Game Room"
        ],
        "room_types": [
            "Private Bedroom Apartments", 
            "Shared Bedroom Apartments", 
            "Southwest Rec", 
            "Florida Ballpark", 
            "James G. Pressly Stadium", 
            "Katie Seashole Pressly Stadium", 
            "Florida Museum", 
            "Performing Arts"
        ],
        "nearby_locations": [
            "Private Bedroom Apartments", 
            "Shared Bedroom Apartments", 
            "Southwest Rec", 
            "Florida Ballpark", 
            "James G. Pressly Stadium", 
            "Katie Seashole Pressly Stadium", 
            "Florida Museum", 
            "Performing Arts"
        ],
        "url": "https://housing.ufl.edu/lakeside-residential-complex/",
        "image_url": "https://housing.ufl.edu/wp-content/uploads/2022/02/2012_Lakeside_Exterior_5_22_POST_001-scaled.jpg",
        "rental_rate_url": "https://housing.ufl.edu/rates-payments-agreements/residence-hall-rental-rates/"
    },
    {
        "name": "Mallory Hall",
        "hall_type": "Traditional Style",
        "description": "Mallory Hall is a fully furnished, traditional style hall located near various colleges and libraries. Mallory Hall offers a range of room styles including single, double, and triple options. Each floor has a shared restroom and community kitchen, that offers a microwave, oven, and stove. It is recommended for students to supply their own in-room refrigerator.",
        "location": "1367 Inner Rd., Gainesville, FL 32612",
        "phone": "352-392-6101",
        "features": [
            "Fully Furnished", 
            "Twin XL Beds", 
            "High-Speed Internet", 
            "Freight Elevator", 
            "Laundry Facilities", 
            "Study Lounge"
        ],
        "room_types": [
            "Single Room", 
            "Double Room", 
            "Triple Room", 
            "College of Education", 
            "College of the Arts", 
            "College of Design Construction and Planning", 
            "The Market in Beaty Towers"
        ],
        "nearby_locations": [
            "Single Room", 
            "Double Room", 
            "Triple Room", 
            "College of Education", 
            "College of the Arts", 
            "College of Design Construction and Planning", 
            "The Market in Beaty Towers"
        ],
        "url": "https://housing.ufl.edu/mallory-hall/",
        "image_url": "https://housing.ufl.edu/wp-content/uploads/2022/02/2015-10-12_Mallory_Hall-4683-scaled.jpg",
        "rental_rate_url": "https://housing.ufl.edu/rates-payments-agreements/residence-hall-rental-rates/"
    },
    {
        "name": "Murphree Hall",
        "hall_type": "Traditional Style",
        "description": "Murphree Hall is is located in the University's historic district. Being in the historic district means that no two rooms are alike so you're guaranteed to have a unique picturesque room. Murphree Hall is located near on and off campus dining locations, the Student Recreation Center, the Hub, Newell Hall, and Library West. Each floor has a shared restroom and community kitchen that offers a stove and microwave. It is recommended for students to supply their own in-room refrigerator.",
        "location": "110 Fletcher Dr., Gainesville, FL 32612",
        "phone": "352-392-6091",
        "features": [
            "Fully Furnished", 
            "Twin XL Beds", 
            "High-Speed WiFi", 
            "Laundry Room", 
            "Study Lounge", 
            "Game Room"
        ],
        "room_types": [
            "Double Room", 
            "Two Room Double", 
            "Triple Room", 
            "Two Room Triple", 
            "Newell Hall", 
            "Library West", 
            "College of Liberal Arts and Sciences", 
            "College of Journalism and Communications", 
            "College of Health and Human Performance", 
            "The Hub"
        ],
        "nearby_locations": [
            "Double Room", 
            "Two Room Double", 
            "Triple Room", 
            "Two Room Triple", 
            "Newell Hall", 
            "Library West", 
            "College of Liberal Arts and Sciences", 
            "College of Journalism and Communications", 
            "College of Health and Human Performance", 
            "The Hub"
        ],
        "url": "https://housing.ufl.edu/murphree-hall/",
        "image_url": "https://housing.ufl.edu/wp-content/uploads/2022/02/Murphree_Exterior_2012_IMG_7165_POST-scaled.jpg",
        "rental_rate_url": "https://housing.ufl.edu/rates-payments-agreements/residence-hall-rental-rates/"
    },
    {
        "name": "North Hall",
        "hall_type": "Traditional Style",
        "description": "North Hall is home to the Pre-Health Living Learning Community and is a great space for like minded students to learn and study together. Located directly across the street from the Stephen C. O'Connell Center, James G. Pressley Stadium, and Ben Hill Griffin Stadium makes this hall perfect for students who are interested in attending athletic events. North Hall offers single, double and triple style rooms options. Each floor has a shared restroom and a community kitchen, that offers a microwave, oven, and stove. It is recommended for students to supply their own in-room refrigerator.",
        "location": "2063 Stadium Rd., Gainesville, FL 32612",
        "phone": "352-392-6031",
        "features": [
            "Laundry Room", 
            "Twin XL Beds", 
            "Freight Elevator", 
            "High-Speed Internet", 
            "Social Lounges", 
            "Private Study Room"
        ],
        "room_types": [
            "Single Room", 
            "Double Room", 
            "Stephen C. O'Connell Center", 
            "Ben Hill Griffin Stadium", 
            "James G. Pressley Field", 
            "Graham Pool", 
            "Flavet Field", 
            "Reitz Union"
        ],
        "nearby_locations": [
            "Single Room", 
            "Double Room", 
            "Stephen C. O'Connell Center", 
            "Ben Hill Griffin Stadium", 
            "James G. Pressley Field", 
            "Graham Pool", 
            "Flavet Field", 
            "Reitz Union"
        ],
        "url": "https://housing.ufl.edu/north-hall/",
        "image_url": "https://housing.ufl.edu/wp-content/uploads/2022/02/2012_TolbertArea_Exterior_IMG_7369_POST-scaled.jpg",
        "rental_rate_url": "https://housing.ufl.edu/residence-halls/residence-hall-rental-rates/"
    },
    {
        "name": "Rawlings Hall",
        "hall_type": "Traditional Style",
        "description": "Rawlings Hall is a fully furnished, traditional style hall located near various colleges and libraries. Rawlings Hall is steps away from the Broward Dining Hall, Century Tower, and the Plaza of the Americas.  This hall offers a range of room styles including single, double, and triple options. Each floor has a shared restroom and community kitchen, that offers a microwave, oven, and stove. It is recommended for students to supply their own in-room refrigerator.",
        "location": "651 Newell Dr., Gainesville, FL 32612",
        "phone": "352-392-6051",
        "features": [
            "Fully Furnished", 
            "Twin XL Beds", 
            "Freight Elevator", 
            "High-Speed Internet", 
            "Laundry Room", 
            "Study Lounge"
        ],
        "room_types": [
            "Double Room", 
            "College of Agricultural and Life Sciences", 
            "Martson's Science Library", 
            "Library West", 
            "Turlington Plaza", 
            "College of Education", 
            "College of the Arts", 
            "College of Design, Construction and Planning", 
            "Broward Dining Hall"
        ],
        "nearby_locations": [
            "Double Room", 
            "College of Agricultural and Life Sciences", 
            "Martson's Science Library", 
            "Library West", 
            "Turlington Plaza", 
            "College of Education", 
            "College of the Arts", 
            "College of Design, Construction and Planning", 
            "Broward Dining Hall"
        ],
        "url": "https://housing.ufl.edu/rawlings-hall/",
        "image_url": "https://housing.ufl.edu/wp-content/uploads/2022/02/2015-10-12_Rawlings_Hall-4911.jpg",
        "rental_rate_url": "https://housing.ufl.edu/rates-payments-agreements/residence-hall-rental-rates/"
    },
    {
        "name": "Reid Hall",
        "hall_type": "Traditional Style",
        "description": "Reid Hall is a fully furnished, traditional style hall located near various colleges and libraries. Reid Hall offers a range of room styles including single, double, and triple options. Each floor has a shared restroom and community kitchen, that offers a microwave, oven, and stove. It is recommended for students to supply their own in-room refrigerator.",
        "location": "1316 Museum Rd., Gainesville, FL 32612",
        "phone": "352-392-6101",
        "features": [
            "Fully Furnished", 
            "Twin XL Beds", 
            "Freight Elevator", 
            "High-Speed Internet", 
            "Laundry Room", 
            "Study Lounge"
        ],
        "room_types": [
            "Single Room", 
            "Double Room", 
            "Triple Room", 
            "College of Education", 
            "College of the Arts", 
            "College of Design Construction and Planning", 
            "The Market in Beaty Towers", 
            "Broward Dining Hall", 
            "Century Tower", 
            "Marston Science Library"
        ],
        "nearby_locations": [
            "Single Room", 
            "Double Room", 
            "Triple Room", 
            "College of Education", 
            "College of the Arts", 
            "College of Design Construction and Planning", 
            "The Market in Beaty Towers", 
            "Broward Dining Hall", 
            "Century Tower", 
            "Marston Science Library"
        ],
        "url": "https://housing.ufl.edu/reid-hall/",
        "image_url": "https://housing.ufl.edu/wp-content/uploads/2022/02/171214_HRE_Buildings_Reid_Ext_5680_KyleAllport.jpg",
        "rental_rate_url": "https://housing.ufl.edu/rates-payments-agreements/residence-hall-rental-rates/"
    },
    {
        "name": "Riker Hall",
        "hall_type": "Traditional Style",
        "description": "Riker Hall is located directly across the street from the Stephen C. O'Connell Center, James G. Pressley Stadium, and Ben Hill Griffin Stadium making it perfect for students who are interested in attending athletic events. Riker Hall offers single, double and triple style rooms options. Each floor has a shared restroom and a community kitchen, that offers a microwave, oven, and stove. It is recommended for students to supply their own in-room refrigerator.",
        "location": "2069 Stadium Rd., Gainesville, FL 32612",
        "phone": "352-392-6031",
        "features": [
            "Laundry Room", 
            "Twin XL Bed", 
            "Passenger Elevator", 
            "High-Speed Internet", 
            "Social Lounges", 
            "Private Study Room"
        ],
        "room_types": [
            "Single Rooms", 
            "Double Rooms", 
            "Triple Rooms", 
            "Stephen C. O'Connell Center", 
            "Ben Hill Griffin Stadium", 
            "James G. Pressley Field", 
            "Graham Pool", 
            "Flavet Field", 
            "Reitz Union"
        ],
        "nearby_locations": [
            "Single Rooms", 
            "Double Rooms", 
            "Triple Rooms", 
            "Stephen C. O'Connell Center", 
            "Ben Hill Griffin Stadium", 
            "James G. Pressley Field", 
            "Graham Pool", 
            "Flavet Field", 
            "Reitz Union"
        ],
        "url": "https://housing.ufl.edu/riker-hall/",
        "image_url": "https://housing.ufl.edu/wp-content/uploads/2022/02/2012_TolbertArea_Exterior_IMG_7420_POST-scaled.jpg",
        "rental_rate_url": "https://housing.ufl.edu/rates-payments-agreements/residence-hall-rental-rates/"
    },
    {
        "name": "Simpson Hall",
        "hall_type": "Traditional Style",
        "description": "Simpson Hall is a traditional residence hall located on the corner of Museum Road and Gale Lemerand Drive making it a short distance from the Reitz Union, athletic venues, fraternity row, and recreational fields. Each floor has a shared restroom and a community kitchen that offers a stove, oven and microwave. It is recommended for students to supply their own in-room refrigerator.",
        "location": "21 Graham Area, Gainesville, FL 32612",
        "phone": "352-392-6021",
        "features": [
            "Fully Furnished", 
            "Freight Elevator", 
            "High-Speed Internet", 
            "Swimming Pool", 
            "The Market in Graham Hall", 
            "Laundry Room", 
            "Study Space", 
            "Game Room"
        ],
        "room_types": [
            "Double Room", 
            "Herbert Wertheim College of Engineering", 
            "College of Journalism and Communications", 
            "Newell Hall", 
            "Flavet Field", 
            "Gator Corner Dining", 
            "Ben Hill Griffin Stadium", 
            "Stephen C. O'Connell Center", 
            "Reitz Union"
        ],
        "nearby_locations": [
            "Double Room", 
            "Herbert Wertheim College of Engineering", 
            "College of Journalism and Communications", 
            "Newell Hall", 
            "Flavet Field", 
            "Gator Corner Dining", 
            "Ben Hill Griffin Stadium", 
            "Stephen C. O'Connell Center", 
            "Reitz Union"
        ],
        "url": "https://housing.ufl.edu/simpson-hall/",
        "image_url": "https://housing.ufl.edu/wp-content/uploads/2022/02/2015-10-12_Simpson_Hall-04451-scaled.jpg",
        "rental_rate_url": "https://housing.ufl.edu/rates-payments-agreements/residence-hall-rental-rates/"
    },
    {
        "name": "Sledd Hall",
        "hall_type": "Traditional Style",
        "description": "Sledd Hall is located in the University's historic district, offering a unique living experience with character and charm. The hall features a variety of room configurations including singles, doubles, and triples. Located near Newell Hall, Library West, and several colleges, Sledd Hall offers convenience to academic resources. Each floor has a shared restroom and community kitchen. It is recommended for students to supply their own in-room refrigerator.",
        "location": "191 Fletcher Dr., Gainesville, FL 32612",
        "phone": "352-392-6091",
        "features": [
            "Fully Furnished", 
            "Twin XL Beds", 
            "High-Speed WiFi", 
            "Laundry Room", 
            "Study Lounge", 
            "Game Room"
        ],
        "room_types": [
            "Single Room", 
            "Double Room", 
            "Two Room Double", 
            "Triple Room", 
            "Two Room Triple", 
            "Three Room Triple", 
            "Three Room Quad", 
            "Newell Hall", 
            "Library West", 
            "College of Liberal Arts and Sciences", 
            "College of Journalism and Communications", 
            "College of Health and Human Performance", 
            "The Hub"
        ],
        "nearby_locations": [
            "Single Room", 
            "Double Room", 
            "Two Room Double", 
            "Triple Room", 
            "Two Room Triple", 
            "Three Room Triple", 
            "Three Room Quad", 
            "Newell Hall", 
            "Library West", 
            "College of Liberal Arts and Sciences", 
            "College of Journalism and Communications", 
            "College of Health and Human Performance", 
            "The Hub"
        ],
        "url": "https://housing.ufl.edu/sledd-hall/",
        "image_url": "https://housing.ufl.edu/wp-content/uploads/2022/02/200310_HRE_Well-a-Palooza_009.jpg",
        "rental_rate_url": "https://housing.ufl.edu/rates-payments-agreements/residence-hall-rental-rates/"
    },
    {
        "name": "Springs Residential Complex",
        "hall_type": "Suite Style",
        "description": "Springs Residential Complex is located near athletic venues, Flavet Field, Gator Corner Dining, and fraternity row so you will always have somewhere to go or something to do. Each suite has a semi-private restroom shared with their suitemates and a kitchen on each floor that offers a microwave, oven, and stove. It is recommended for students to supply their own in-room refrigerator.",
        "location": "45 Springs Residential ComplexGainesville, FL 32612",
        "phone": "352-392-0459",
        "features": [
            "Fully Furnished", 
            "Twin XL Beds", 
            "Passenger Elevator", 
            "High-Speed Internet", 
            "Laundry Room", 
            "Social Lounges", 
            "Study Space", 
            "Outdoor Volleyball Space", 
            "Game Room"
        ],
        "room_types": [
            "Single Suite", 
            "Double Suite", 
            "James G. Pressley Stadium", 
            "Stephen C. O'Connell Center", 
            "Ben Hill Griffin Stadium", 
            "Flavet Field", 
            "College of Engineering", 
            "Reitz Union"
        ],
        "nearby_locations": [
            "Single Suite", 
            "Double Suite", 
            "James G. Pressley Stadium", 
            "Stephen C. O'Connell Center", 
            "Ben Hill Griffin Stadium", 
            "Flavet Field", 
            "College of Engineering", 
            "Reitz Union"
        ],
        "url": "https://housing.ufl.edu/springs-residential-complex/",
        "image_url": "https://housing.ufl.edu/wp-content/uploads/2022/02/2010_Springs-8-scaled.jpg",
        "rental_rate_url": "https://housing.ufl.edu/rates-payments-agreements/residence-hall-rental-rates/"
    },
    {
        "name": "Tanglewood Village",
        "hall_type": "Apartments",
        "description": "Tanglewood Village is a retreat from main campus and gives you the peace of mind of living in a dedicated student and family focused community. Tanglewood Village features apartments and townhome style units. The community provides playgrounds, a pool, free resident parking, a community garden, barbeque areas, and more.",
        "location": "2901 SW 13th St., Gainesville, FL 32608",
        "phone": "352-392-6081",
        "features": [
            "Free Parking", 
            "24/7 Area Office", 
            "Fitness Room", 
            "Community Garden", 
            "Laundry Room", 
            "Cable TV", 
            "Wired Ethernet Services"
        ],
        "room_types": [
            "One Bedroom Apartment", 
            "Two Bedroom Apartment", 
            "Two Bedroom Townhome", 
            "Efficiency Apartment", 
            "Lake Wauburg", 
            "UF Health Shands", 
            "College of Veterinary Medicine"
        ],
        "nearby_locations": [
            "One Bedroom Apartment", 
            "Two Bedroom Apartment", 
            "Two Bedroom Townhome", 
            "Efficiency Apartment", 
            "Lake Wauburg", 
            "UF Health Shands", 
            "College of Veterinary Medicine"
        ],
        "url": "https://housing.ufl.edu/tanglewood-village/",
        "image_url": "https://housing.ufl.edu/wp-content/uploads/2022/02/200312_HRE_HonorsBakingClass_2440-scaled.jpg",
        "rental_rate_url": "https://housing.ufl.edu/rates-payments-agreements/graduate-and-family-housing-rental-rates/"
    },
    {
        "name": "The Continuum",
        "hall_type": "Apartments",
        "description": "Enjoy a hassle-free living experience with our fully furnished apartments and a dedicated team committed to providing exceptional service. Your rent includes all major appliances, such as a washer, dryer, refrigerator, microwave, dishwasher, and stove/oven, as well as high-speed internet and HDTV cable packages. Furniture is provided and thoughtfully selected to include everything you need, from living room seating, mattress, desk, and more. Select studio layouts may vary slightly in furnishings but maintain the same focus on quality and comfort.",
        "location": "491 W University Ave. Suite 130,Gainesville, FL, 32601",
        "phone": "352-415-2278",
        "features": [
            "Business Center", 
            "Recreation Room", 
            "Fitness Center", 
            "Swimming Pool", 
            "Pet Friendly"
        ],
        "room_types": [
            "Studio", 
            "One Bedroom Apartment", 
            "Two Bedroom Apartment", 
            "Four Bedroom Apartment", 
            "College of Business", 
            "College of Education", 
            "Downtown Gainesville"
        ],
        "nearby_locations": [
            "Studio", 
            "One Bedroom Apartment", 
            "Two Bedroom Apartment", 
            "Four Bedroom Apartment", 
            "College of Business", 
            "College of Education", 
            "Downtown Gainesville"
        ],
        "url": "https://housing.ufl.edu/the-continuum/",
        "image_url": "https://housing.ufl.edu/wp-content/uploads/2025/01/Continuum-4.png",
        "rental_rate_url": "https://housing.ufl.edu/rates-payments-agreements/graduate-and-family-housing-rental-rates/"
    },
    {
        "name": "Thomas Hall",
        "hall_type": "Traditional Style",
        "description": "Thomas Hall is situated in the University's historic district, offering students a blend of traditional architecture and modern amenities. This residence hall provides a variety of room options including singles, doubles, triples, and quads. Located near Newell Hall, Library West, and several academic colleges, Thomas Hall offers convenient access to campus resources. Each floor features shared restrooms and community kitchens, along with study spaces and social areas.",
        "location": "133 Fletcher Dr., Gainesville, FL 32612",
        "phone": "352-392-6091",
        "features": [
            "Fully Furnished", 
            "Twin XL Beds", 
            "High-Speed WiFi", 
            "Laundry Room", 
            "Study Lounge", 
            "Game Room"
        ],
        "room_types": [
            "Single Room", 
            "Double Room", 
            "Triple Room", 
            "Quad Room", 
            "Newell Hall", 
            "Library West", 
            "College of Liberal Arts and Sciences", 
            "College of Journalism and Communications", 
            "College of Health and Human Performance", 
            "The Hub"
        ],
        "nearby_locations": [
            "Single Room", 
            "Double Room", 
            "Triple Room", 
            "Quad Room", 
            "Newell Hall", 
            "Library West", 
            "College of Liberal Arts and Sciences", 
            "College of Journalism and Communications", 
            "College of Health and Human Performance", 
            "The Hub"
        ],
        "url": "https://housing.ufl.edu/thomas-hall/",
        "image_url": "https://housing.ufl.edu/wp-content/uploads/2022/02/2015-11-04_Thomas_Hall-5409-scaled.jpg",
        "rental_rate_url": "https://housing.ufl.edu/rates-payments-agreements/residence-hall-rental-rates/"
    },
    {
        "name": "Tolbert Hall",
        "hall_type": "Traditional Style",
        "description": "Tolbert Hall is located directly across the street from Van Fleet Hall. Making it the ideal location for the ROTC Living Learning Community. Students living in Tolbert Hall will have easy access to athletic events, a swimming pool, Flavet Field, and the Reitz Union.  Tolbert Hall offers single, double and triple style rooms options. Each floor has a shared restroom and a community kitchen, that offers a microwave, oven, and stove. It is recommended for students to supply their own in-room refrigerator.",
        "location": "2087 Stadium Rd., Gainesville, FL 32612",
        "phone": "352-392-6031",
        "features": [
            "Fully Furnished", 
            "Twin XL Beds", 
            "Passenger Elevator", 
            "High-Speed Internet", 
            "Maritime Skills Simulator", 
            "Laundry Room", 
            "Social Lounges", 
            "Private Study Room", 
            "Game Room"
        ],
        "room_types": [
            "Single Room", 
            "Double Room", 
            "Triple Room", 
            "Van Fleet Hall", 
            "Stephen C. O'Connell Center", 
            "Ben Hill Griffin Stadium", 
            "James G. Pressley Field", 
            "Graham Pool", 
            "Flavet Field", 
            "Reitz Union"
        ],
        "nearby_locations": [
            "Single Room", 
            "Double Room", 
            "Triple Room", 
            "Van Fleet Hall", 
            "Stephen C. O'Connell Center", 
            "Ben Hill Griffin Stadium", 
            "James G. Pressley Field", 
            "Graham Pool", 
            "Flavet Field", 
            "Reitz Union"
        ],
        "url": "https://housing.ufl.edu/tolbert-hall/",
        "image_url": "https://housing.ufl.edu/wp-content/uploads/2022/02/210820_UFSL_UF25ClassPhoto_227.jpg",
        "rental_rate_url": "https://housing.ufl.edu/rates-payments-agreements/residence-hall-rental-rates/"
    },
    {
        "name": "Trusler Hall",
        "hall_type": "Traditional Style",
        "description": "Trusler Hall is a traditional residence hall located on the corner of Museum Road and Gale Lemerand Drive making it a short distance from the Reitz Union, athletic venues, fraternity row, and recreational fields. Each floor has a shared restroom and a community kitchen that offers a stove, oven and microwave. It is recommended for students to supply their own in-room refrigerator.",
        "location": "21 Graham Area, Gainesville, FL 32612",
        "phone": "352-392-6021",
        "features": [
            "Fully Furnished", 
            "Twin XL Beds", 
            "Freight Elevator", 
            "High-Speed Internet", 
            "Graham Pool", 
            "The Market in Graham Hall", 
            "Laundry Room", 
            "Study Space", 
            "Game Room"
        ],
        "room_types": [
            "Double Room", 
            "Ben Hill Griffin Stadium", 
            "Stephen C. O'Connell Center", 
            "Reitz Union", 
            "Gator Corner Dining", 
            "Flavet Field", 
            "Newell Hall"
        ],
        "nearby_locations": [
            "Double Room", 
            "Ben Hill Griffin Stadium", 
            "Stephen C. O'Connell Center", 
            "Reitz Union", 
            "Gator Corner Dining", 
            "Flavet Field", 
            "Newell Hall"
        ],
        "url": "https://housing.ufl.edu/trusler-hall/",
        "image_url": "https://housing.ufl.edu/wp-content/uploads/2022/02/130604_UFhousingGraham_3166_TimCasey-scaled.jpg",
        "rental_rate_url": "https://housing.ufl.edu/rates-payments-agreements/residence-hall-rental-rates/"
    },
    {
        "name": "Weaver Hall",
        "hall_type": "Traditional Style",
        "description": "Weaver Hall is a traditional-style residence hall located in the Tolbert Area, offering single, double, and triple room options. Its convenient location provides easy access to the Reitz Union, College of Engineering, and athletic venues including the Stephen C. O'Connell Center and Ben Hill Griffin Stadium. Each floor has a shared restroom and community kitchen. The hall features study lounges and laundry facilities to support student life and academic success.",
        "location": "562 Gale Lemerand Dr., Gainesville, FL 32612",
        "phone": "352-392-6031",
        "features": [
            "Fully Furnished", 
            "Twin XL Beds", 
            "Freight Elevator", 
            "High-Speed Internet", 
            "Laundry Room", 
            "Study Lounge"
        ],
        "room_types": [
            "Single Room", 
            "Double Room", 
            "Triple Room", 
            "Reitz Union", 
            "College of Engineering", 
            "Flavet Field", 
            "Graham Pool", 
            "Stephen C. O'Connell Center", 
            "Ben Hill Griffin Stadium", 
            "James G. Pressley Field"
        ],
        "nearby_locations": [
            "Single Room", 
            "Double Room", 
            "Triple Room", 
            "Reitz Union", 
            "College of Engineering", 
            "Flavet Field", 
            "Graham Pool", 
            "Stephen C. O'Connell Center", 
            "Ben Hill Griffin Stadium", 
            "James G. Pressley Field"
        ],
        "url": "https://housing.ufl.edu/weaver-hall/",
        "image_url": "https://housing.ufl.edu/wp-content/uploads/2025/02/HRL-LLC-Website-Headers-1280-x-854.jpg",
        "rental_rate_url": "https://housing.ufl.edu/rates-payments-agreements/residence-hall-rental-rates/"
    },
    {
        "name": "Yulee Hall",
        "hall_type": "Traditional Style",
        "description": "Yulee Hall is a fully furnished, traditional style hall located near various colleges and libraries. Yulee Hall offers a range of room styles including single, double, and triple options. Each floor has a shared restroom and community kitchen that boasts a microwave, oven, and stove. It is recommended for students to supply their own in-room refrigerator.",
        "location": "1367 Inner Rd., Gainesville, FL 32612",
        "phone": "352-392-6101",
        "features": [
            "Fully Furnished", 
            "Twin XL Beds", 
            "Freight Elevator", 
            "High-Speed Internet", 
            "Laundry Room", 
            "Study Lounge"
        ],
        "room_types": [
            "Single Room", 
            "Double Room", 
            "Triple Room", 
            "College of Education", 
            "College of the Arts", 
            "College of Design Construction and Planning", 
            "The Market in Beaty Towers"
        ],
        "nearby_locations": [
            "Single Room", 
            "Double Room", 
            "Triple Room", 
            "College of Education", 
            "College of the Arts", 
            "College of Design Construction and Planning", 
            "The Market in Beaty Towers"
        ],
        "url": "https://housing.ufl.edu/yulee-hall/",
        "image_url": "https://housing.ufl.edu/wp-content/uploads/2022/02/2015-10-12_Yulee_Hall-4726-scaled.jpg",
        "rental_rate_url": "https://housing.ufl.edu/rates-payments-agreements/residence-hall-rental-rates/"
    }
]

# Residence Hall Rates Data
RESIDENCE_HALL_RATES = [
    {
        "residence_hall": "Beaty Towers",
        "room_type": "Apartment Double",
        "fall_spring": 3821,
        "summer_a_b": 1433,
        "summer_c": 2866
    },
    {
        "residence_hall": "Broward Hall",
        "room_type": "Traditional Single",
        "fall_spring": 3766,
        "summer_a_b": 1412,
        "summer_c": 2824
    },
    {
        "residence_hall": "Broward Hall",
        "room_type": "Traditional Double",
        "fall_spring": 3556,
        "summer_a_b": 1334,
        "summer_c": 2668
    },
    {
        "residence_hall": "Broward Hall",
        "room_type": "Traditional Triple",
        "fall_spring": 3136,
        "summer_a_b": 1176,
        "summer_c": 2352
    },
    {
        "residence_hall": "Buckman Hall",
        "room_type": "Traditional Single",
        "fall_spring": 3766,
        "summer_a_b": 1412,
        "summer_c": 2824
    },
    {
        "residence_hall": "Buckman Hall",
        "room_type": "Traditional Double",
        "fall_spring": 3556,
        "summer_a_b": 1334,
        "summer_c": 2668
    },
    {
        "residence_hall": "Buckman Hall",
        "room_type": "Traditional Triple",
        "fall_spring": 3136,
        "summer_a_b": 1176,
        "summer_c": 2352
    },
    {
        "residence_hall": "Cypress Hall",
        "room_type": "Suite Single",
        "fall_spring": 5081,
        "summer_a_b": 1905,
        "summer_c": 3810
    },
    {
        "residence_hall": "Cypress Hall",
        "room_type": "Suite Double",
        "fall_spring": 4800,
        "summer_a_b": 1800,
        "summer_c": 3600
    },
    {
        "residence_hall": "East Hall",
        "room_type": "Traditional Double",
        "fall_spring": 3556,
        "summer_a_b": 1334,
        "summer_c": 2668
    },
    {
        "residence_hall": "East Hall",
        "room_type": "Traditional Triple",
        "fall_spring": 3136,
        "summer_a_b": 1176,
        "summer_c": 2352
    },
    {
        "residence_hall": "Fletcher Hall",
        "room_type": "Traditional Single",
        "fall_spring": 3766,
        "summer_a_b": 1412,
        "summer_c": 2824
    },
    {
        "residence_hall": "Fletcher Hall",
        "room_type": "Traditional Large Single",
        "fall_spring": 4082,
        "summer_a_b": 1531,
        "summer_c": 3062
    },
    {
        "residence_hall": "Fletcher Hall",
        "room_type": "Traditional Double",
        "fall_spring": 3556,
        "summer_a_b": 1334,
        "summer_c": 2668
    },
    {
        "residence_hall": "Fletcher Hall",
        "room_type": "Traditional Large Double",
        "fall_spring": 4082,
        "summer_a_b": 1531,
        "summer_c": 3062
    },
    {
        "residence_hall": "Honors Village",
        "room_type": "Suite Single",
        "fall_spring": 5589,
        "summer_a_b": 2096,
        "summer_c": 4192
    },
    {
        "residence_hall": "Honors Village",
        "room_type": "Suite Double",
        "fall_spring": 5281,
        "summer_a_b": 1980,
        "summer_c": 3960
    },
    {
        "residence_hall": "Honors Village",
        "room_type": "Traditional Single",
        "fall_spring": 5081,
        "summer_a_b": 1905,
        "summer_c": 3810
    },
    {
        "residence_hall": "Honors Village",
        "room_type": "Traditional Double",
        "fall_spring": 4800,
        "summer_a_b": 1800,
        "summer_c": 3600
    },
    {
        "residence_hall": "Hume Hall",
        "room_type": "Suite Single",
        "fall_spring": 5081,
        "summer_a_b": 1905,
        "summer_c": 3810
    },
    {
        "residence_hall": "Hume Hall",
        "room_type": "Suite Double",
        "fall_spring": 4800,
        "summer_a_b": 1800,
        "summer_c": 3600
    },
    {
        "residence_hall": "Infinity Hall",
        "room_type": "Suite Single",
        "fall_spring": 5302,
        "summer_a_b": 2253,
        "summer_c": 4506
    },
    {
        "residence_hall": "Infinity Hall",
        "room_type": "Suite Double",
        "fall_spring": 5008,
        "summer_a_b": 2128,
        "summer_c": 4256
    },
    {
        "residence_hall": "Infinity Hall",
        "room_type": "Suite Large Double",
        "fall_spring": 5157,
        "summer_a_b": 2192,
        "summer_c": 4384
    },
    # Additional hall rates would be included here
]

# Links to Housing Resources
HOUSING_LINKS = [
    {
        "description": "First Year Student Housing Application",
        "link": "https://housing.ufl.edu/apply/first-year-student-application/"
    },
    {
        "description": "Graduate and Family Housing Application",
        "link": "https://housing.ufl.edu/apply/graduate-and-family-housing-application/"
    },
    {
        "description": "Housing Application Guide",
        "link": "https://housing.ufl.edu/apply/how-to-apply/"
    },
    {
        "description": "Current Student Housing Application",
        "link": "https://housing.ufl.edu/apply/current-student-application/"
    },
    {
        "description": "Housing Frequently Asked Questions",
        "link": "https://housing.ufl.edu/apply/frequently-asked-questions/"
    },
    {
        "description": "Graduate and Family Housing Options",
        "link": "https://housing.ufl.edu/living-options/?housing-type=family-housing"
    },
    {
        "description": "Residence Hall Options for Individuals",
        "link": "https://housing.ufl.edu/living-options/?housing-type=individual-housing"
    },
    {
        "description": "Living Learning Communities Information",
        "link": "https://housing.ufl.edu/living-learning-communities/"
    },
    {
        "description": "Graduate and Family Housing Rental Rates",
        "link": "https://housing.ufl.edu/rates-payments-agreements/graduate-and-family-housing-rental-rates/"
    },
    {
        "description": "Residence Hall Rental Rates",
        "link": "https://housing.ufl.edu/rates-payments-agreements/residence-hall-rental-rates/"
    },
    # Additional housing links would be included here
]

# =============================================================================
# CAMPUS AMENITIES
# =============================================================================

# Information about non-library amenities on campus
CAMPUS_AMENITIES = {
    "coffee_shops": [
        # Coffee shop entries...
    ],
    "dining_locations": [
        # Dining location entries...
    ],
    "study_spots": [
        # Study spot entries...
    ]
}

# =============================================================================
# SUBJECT MAPPINGS
# =============================================================================

# Comprehensive subject to library mappings
SUBJECT_MAPPINGS = {
    # STEM subjects → Marston
    "science": "Marston Science Library",
    # Other subject mappings...
}

# =============================================================================
# ACADEMIC CALENDAR DATA
# =============================================================================

ACADEMIC_CALENDAR = {
    'terms': {
        'Spring 2025': {'start': '2025-01-06', 'end': '2025-05-02'},
        # Other terms...
    },
    'events': {
        'Spring 2025 Final Exams': {'start': '2025-04-26', 'end': '2025-05-02'},
        # Other events...
    },
    'library_schedule_exceptions': {
        '2025-01-01': {'all': 'CLOSED - New Year\'s Day'},
        # Other exceptions...
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
        # Other extended hours periods...
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
        self.current_residence_hall = None  # Added for housing
        self.current_topic = None
        self.awaiting_followup = False
        self.last_intent = None
        self.mentioned_libraries = set()
        self.mentioned_buildings = set()
        self.mentioned_residence_halls = set()  # Added for housing
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
            
    def get_active_residence_hall(self):
        """Get the currently active residence hall in conversation"""
        return self.current_residence_hall
        
    def set_active_residence_hall(self, residence_hall):
        """Set the active residence hall for the conversation"""
        self.current_residence_hall = residence_hall
        if residence_hall:
            self.mentioned_residence_halls.add(residence_hall.get("name", ""))
    
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
                            
        elif isinstance(previous_context, dict) and "name" in previous_context:
            # We're dealing with a residence hall
            for hall in HOUSING_DATA:
                hall_name = hall.get('name', '').lower()
                if hall_name in query_lower and hall_name != previous_context.get('name', '').lower():
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
            "active_residence_hall": self.current_residence_hall.get("name", "None") if self.current_residence_hall else "None",
            "mentioned_libraries": list(self.mentioned_libraries),
            "mentioned_buildings": list(self.mentioned_buildings),
            "mentioned_residence_halls": list(self.mentioned_residence_halls),
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
        self.residence_hall_matches = defaultdict(int)  # Added for housing
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
            
        # Record residence hall matches if available
        if metrics and 'residence_hall' in metrics:
            hall_name = metrics['residence_hall'].get('name', '') if metrics['residence_hall'] else 'None'
            self.residence_hall_matches[hall_name] += 1
            
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
            "top_residence_halls": dict(sorted(self.residence_hall_matches.items(), key=lambda x: x[1], reverse=True)[:5]),
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
                    "residence_hall_matches": dict(self.residence_hall_matches),
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
        logger.info(f"✅ Successfully loaded {len(buildings)} campus buildings from CSV")
        return buildings
    except Exception as e:
        logger.error(f"Error loading campus buildings data: {e}")
        # Return the hardcoded data as fallback
        logger.info("⚠️ Using hardcoded campus buildings data as fallback")
        return CAMPUS_BUILDINGS_DATA

def load_housing_data(hall_info_path="scrapedData/housing/hallInfo.csv", 
                    rates_path="scrapedData/housing/residenceHallRates.csv",
                    links_path="scrapedData/housing/housingLinks.csv"):
    """Load housing data from CSV files"""
    # Initialize data structures
    housing_data = []
    rates_data = []
    links_data = []
    
    # Try to load hall info
    try:
        with open(hall_info_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Convert string lists to actual lists
                features = row.get('features_str', '').split(', ') if row.get('features_str') else []
                room_types = row.get('room_types_str', '').split(', ') if row.get('room_types_str') else []
                nearby = row.get('nearby_locations_str', '').split(', ') if row.get('nearby_locations_str') else []
                
                hall = {
                    "name": row.get('name', ''),
                    "hall_type": row.get('hall_type', ''),
                    "description": row.get('description', ''),
                    "location": row.get('location', ''),
                    "phone": row.get('phone', ''),
                    "features": features,
                    "room_types": room_types,
                    "nearby_locations": nearby,
                    "url": row.get('url', ''),
                    "image_url": row.get('image_url', ''),
                    "rental_rate_url": row.get('rental_rate_url', '')
                }
                housing_data.append(hall)
        logger.info(f"✅ Successfully loaded {len(housing_data)} residence halls from CSV")
    except Exception as e:
        logger.error(f"Error loading hall info data: {e}")
        # Use embedded data as fallback
        housing_data = HOUSING_DATA
        logger.info("⚠️ Using hardcoded housing data as fallback")
    
    # Try to load rental rates
    try:
        with open(rates_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                rate = {
                    "residence_hall": row.get('residence_hall', ''),
                    "room_type": row.get('room_type', ''),
                    "fall_spring": int(row.get('fall_spring', 0)),
                    "summer_a_b": int(row.get('summer_a_b', 0)),
                    "summer_c": int(row.get('summer_c', 0))
                }
                rates_data.append(rate)
        logger.info(f"✅ Successfully loaded {len(rates_data)} residence hall rates from CSV")
    except Exception as e:
        logger.error(f"Error loading rates data: {e}")
        # Use embedded data as fallback
        rates_data = RESIDENCE_HALL_RATES
        logger.info("⚠️ Using hardcoded rates data as fallback")
    
    # Try to load housing links
    try:
        with open(links_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                link = {
                    "description": row.get('description', ''),
                    "link": row.get('link', '')
                }
                links_data.append(link)
        logger.info(f"✅ Successfully loaded {len(links_data)} housing links from CSV")
    except Exception as e:
        logger.error(f"Error loading housing links data: {e}")
        # Use embedded data as fallback
        links_data = HOUSING_LINKS
        logger.info("⚠️ Using hardcoded housing links data as fallback")
    
    return housing_data, rates_data, links_data

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
        
    # Various methods for knowledge retrieval...

# =============================================================================
# HOUSING KNOWLEDGE RETRIEVAL
# =============================================================================

class HousingKnowledgeRetrieval:
    """Knowledge retrieval for residence halls and housing information"""
    
    def __init__(self, housing_data, rates_data, links_data, embedding_model=None):
        self.housing_data = housing_data
        self.rates_data = rates_data
        self.links_data = links_data
        self.embedding_model = embedding_model
        
        # Create lookup dictionaries
        self.halls_by_name = {hall.get('name', ''): hall for hall in housing_data}
        self.rates_by_hall = self._index_rates_by_hall()
        self.links_by_desc = {link.get('description', ''): link.get('link', '') for link in links_data}
        
        # Build searchable indexes
        self.keyword_index = self._build_keyword_index()
        self.hall_types_index = self._build_hall_types_index()
        self.features_index = self._build_features_index()
        self.room_types_index = self._build_room_types_index()
        
        # Vector index for semantic search
        self.vector_index = self._build_vector_index() if embedding_model else None
        
        # Cache for query results
        self.query_cache = LRUCache(capacity=100)
        
    def _index_rates_by_hall(self):
        """Create an index of rates by residence hall"""
        rates_index = defaultdict(list)
        for rate in self.rates_data:
            hall_name = rate.get('residence_hall', '')
            rates_index[hall_name].append(rate)
        return rates_index
    
    def _build_keyword_index(self):
        """Build keyword index for residence hall search"""
        index = defaultdict(list)
        for i, hall in enumerate(self.housing_data):
            # Extract keywords from all fields
            keywords = []
            
            # Add hall name
            name = hall.get('name', '')
            if name:
                keywords.append(name.lower())
                keywords.extend(name.lower().split())
            
            # Add hall type
            hall_type = hall.get('hall_type', '')
            if hall_type:
                keywords.append(hall_type.lower())
                keywords.extend(hall_type.lower().split())
            
            # Add from description
            desc = hall.get('description', '')
            if desc:
                # Extract meaningful keywords
                desc_words = desc.lower().split()
                for word in desc_words:
                    if len(word) > 3 and word not in ['with', 'and', 'the', 'for', 'that', 'this', 'from', 'each']:
                        keywords.append(word)
            
            # Add features
            features = hall.get('features', [])
            for feature in features:
                keywords.extend(feature.lower().split())
            
            # Add room types
            room_types = hall.get('room_types', [])
            for room_type in room_types:
                keywords.extend(room_type.lower().split())
            
            # Add all keywords to index
            for keyword in set(keywords):
                if len(keyword) > 2:  # Only index words of reasonable length
                    index[keyword].append(i)
                
        return index
    
    def _build_hall_types_index(self):
        """Build index for hall types"""
        index = defaultdict(list)
        for i, hall in enumerate(self.housing_data):
            hall_type = hall.get('hall_type', '').lower()
            if hall_type:
                index[hall_type].append(i)
                # Also add common variations
                if 'apartment' in hall_type:
                    index['apartment'].append(i)
                    index['apt'].append(i)
                if 'traditional' in hall_type:
                    index['traditional'].append(i)
                    index['trad'].append(i)
                if 'suite' in hall_type:
                    index['suite'].append(i)
        return index
    
    def _build_features_index(self):
        """Build index for residence hall features"""
        index = defaultdict(list)
        for i, hall in enumerate(self.housing_data):
            features = hall.get('features', [])
            for feature in features:
                feature_lower = feature.lower()
                index[feature_lower].append(i)
                
                # Add common variations for features
                if 'wifi' in feature_lower or 'internet' in feature_lower:
                    index['wifi'].append(i)
                    index['internet'].append(i)
                    index['connection'].append(i)
                if 'laundry' in feature_lower:
                    index['laundry'].append(i)
                    index['washing'].append(i)
                if 'elevator' in feature_lower:
                    index['elevator'].append(i)
                    index['lift'].append(i)
                if 'game' in feature_lower:
                    index['game'].append(i)
                    index['recreation'].append(i)
                if 'study' in feature_lower:
                    index['study'].append(i)
                    index['quiet'].append(i)
                    
        return index
    
    def _build_room_types_index(self):
        """Build index for room types"""
        index = defaultdict(list)
        for i, hall in enumerate(self.housing_data):
            room_types = hall.get('room_types', [])
            for room_type in room_types:
                room_type_lower = room_type.lower()
                index[room_type_lower].append(i)
                
                # Add common variations
                if 'single' in room_type_lower:
                    index['single'].append(i)
                    index['individual'].append(i)
                if 'double' in room_type_lower:
                    index['double'].append(i)
                    index['shared'].append(i)
                    index['roommate'].append(i)
                if 'triple' in room_type_lower:
                    index['triple'].append(i)
                    index['three'].append(i)
                if 'apartment' in room_type_lower:
                    index['apartment'].append(i)
                    index['apt'].append(i)
                    
        return index
    
    def _build_vector_index(self):
        """Build vector index for semantic search"""
        if not self.embedding_model:
            return None
            
        try:
            # Initialize vector storage
            descriptions = []
            
            # Create descriptions for each hall
            for hall in self.housing_data:
                desc = self._create_hall_description(hall)
                descriptions.append(desc)
            
            # Generate embeddings
            embeddings = self.embedding_model.encode(descriptions)
            
            # Create index if hnswlib is available
            if hnswlib:
                vector_dim = embeddings.shape[1]
                index = hnswlib.Index(space='cosine', dim=vector_dim)
                
                # Initialize with proper parameters
                index.init_index(
                    max_elements=len(self.housing_data),
                    ef_construction=200,
                    M=16
                )
                
                # Add residence hall embeddings
                index.add_items(embeddings, list(range(len(self.housing_data))))
                
                # Set search parameters
                index.set_ef(50)
                
                return index
            else:
                # Fallback to dictionary
                embeddings_dict = {}
                for i in range(len(embeddings)):
                    embeddings_dict[i] = embeddings[i]
                return embeddings_dict
                
        except Exception as e:
            logger.error(f"Error building housing vector index: {e}")
            return {}
    
    def _create_hall_description(self, hall):
        """Create a detailed description of a residence hall for semantic matching"""
        name = hall.get('name', '')
        hall_type = hall.get('hall_type', '')
        desc = hall.get('description', '')
        location = hall.get('location', '')
        
        # Create a detailed description
        description = f"{name} is a {hall_type} residence hall at the University of Florida. "
        
        if desc:
            # Truncate if too long
            if len(desc) > 200:
                description += f"{desc[:200]}... "
            else:
                description += f"{desc} "
        
        description += f"It is located at {location}. "
        
        # Add features
        features = hall.get('features', [])
        if features:
            feature_text = ', '.join(features[:5])  # Limit to top 5
            description += f"Features include: {feature_text}. "
        
        # Add room types
        room_types = hall.get('room_types', [])
        if room_types:
            room_type_text = ', '.join(room_types[:5])  # Limit to top 5
            description += f"Room types available: {room_type_text}. "
            
        return description
    
    def retrieve_residence_hall(self, query):
        """Retrieve most relevant residence hall for a query"""
        # Preprocess query
        query = query.lower().strip()
        
        # Check cache first
        cache_key = f"hall_query:{query}"
        if cache_key in self.query_cache:
            return self.query_cache[cache_key]
        
        # Try direct name match first (highest confidence)
        for name, hall in self.halls_by_name.items():
            if query == name.lower() or query in name.lower():
                self.query_cache[cache_key] = (hall, 0.95)
                return hall, 0.95
        
        results = []
        
        # Try semantic search if available
        if self.embedding_model and self.vector_index:
            semantic_match, semantic_confidence = self._find_hall_by_semantic_similarity(query)
            if semantic_match:
                results.append({"hall": semantic_match, "confidence": semantic_confidence, "method": "semantic"})
        
        # Try keyword search
        keyword_match, keyword_confidence = self._find_hall_by_keywords(query)
        if keyword_match:
            results.append({"hall": keyword_match, "confidence": keyword_confidence, "method": "keyword"})
        
        # Try hall type search
        type_match, type_confidence = self._find_hall_by_type(query)
        if type_match:
            results.append({"hall": type_match, "confidence": type_confidence, "method": "hall_type"})
        
        # Try features search
        feature_match, feature_confidence = self._find_hall_by_features(query)
        if feature_match:
            results.append({"hall": feature_match, "confidence": feature_confidence, "method": "features"})
        
        # Try room type search
        room_match, room_confidence = self._find_hall_by_room_type(query)
        if room_match:
            results.append({"hall": room_match, "confidence": room_confidence, "method": "room_type"})
        
        # No matches found
        if not results:
            self.query_cache[cache_key] = (None, 0.0)
            return None, 0.0
        
        # Return best match
        best_result = max(results, key=lambda x: x["confidence"])
        best_match = (best_result["hall"], best_result["confidence"])
        
        # Add to cache
        self.query_cache[cache_key] = best_match
        
        return best_match
    
    def _find_hall_by_semantic_similarity(self, query):
        """Find residence hall by semantic similarity"""
        if not self.embedding_model or not self.vector_index or not query:
            return None, 0.0
        
        try:
            # Get query embedding
            query_embedding = self.embedding_model.encode(query)
            
            if isinstance(self.vector_index, dict):
                # Fallback to manual search
                best_idx = -1
                best_sim = -1
                
                for idx, embedding in self.vector_index.items():
                    sim = cosine_similarity([query_embedding], [embedding])[0][0]
                    if sim > best_sim:
                        best_sim = sim
                        best_idx = idx
                
                if best_sim < 0.4 or best_idx < 0:
                    return None, 0.0
                    
                return self.housing_data[best_idx], min(best_sim, 0.85)
            elif hasattr(self.vector_index, 'knn_query'):
                # Use HNSW index
                labels, distances = self.vector_index.knn_query(query_embedding.reshape(1, -1), k=1)
                best_idx = labels[0][0]
                similarity = 1.0 - distances[0][0]
                
                if similarity < 0.4:
                    return None, 0.0
                    
                return self.housing_data[best_idx], min(similarity, 0.85)
            else:
                return None, 0.0
                
        except Exception as e:
            logger.error(f"Error computing housing semantic similarity: {e}")
            return None, 0.0
    
    def _find_hall_by_keywords(self, query):
        """Find residence hall based on keywords"""
        if not query:
            return None, 0.0
            
        query_words = query.lower().split()
        
        # Count matches for each hall
        hall_counts = Counter()
        
        for word in query_words:
            if word in self.keyword_index:
                for hall_idx in self.keyword_index[word]:
                    hall_counts[hall_idx] += 1
        
        # Find hall with most keyword matches
        if hall_counts:
            best_idx, count = hall_counts.most_common(1)[0]
            
            # Scale confidence based on match count
            confidence = min(0.85, 0.5 + (count * 0.05))
            
            return self.housing_data[best_idx], confidence
            
        return None, 0.0
    
    def _find_hall_by_type(self, query):
        """Find residence halls based on hall type"""
        hall_type_keywords = {
            "apartment": ["apartment", "apt", "kitchen", "kitchenette"],
            "traditional": ["traditional", "trad", "classic", "dorm", "dormitory"],
            "suite": ["suite", "semi-private", "bathroom"]
        }
        
        # Determine which hall type is being asked for
        target_type = None
        for hall_type, keywords in hall_type_keywords.items():
            for keyword in keywords:
                if keyword in query:
                    target_type = hall_type
                    break
            if target_type:
                break
        
        if not target_type:
            return None, 0.0
        
        # Find halls matching the target type
        matching_halls = []
        for hall in self.housing_data:
            hall_type = hall.get('hall_type', '').lower()
            if target_type in hall_type:
                matching_halls.append(hall)
        
        if matching_halls:
            # Return the first match with decent confidence
            # (In a real system, we might want to rank these more carefully)
            return matching_halls[0], 0.8
            
        return None, 0.0
    
    def _find_hall_by_features(self, query):
        """Find residence halls based on features mentioned"""
        feature_keywords = {
            "wifi": ["wifi", "internet", "wireless", "connection"],
            "laundry": ["laundry", "washing", "dryer", "washer"],
            "furnished": ["furnished", "furniture", "bed", "desk"],
            "elevator": ["elevator", "lift"],
            "kitchen": ["kitchen", "kitchenette", "cooking", "stove", "oven", "refrigerator", "fridge"],
            "study": ["study", "quiet", "lounge", "studying"],
            "game": ["game", "recreation", "social", "play"]
        }
        
        # Determine which features are being asked for
        target_features = set()
        for feature, keywords in feature_keywords.items():
            for keyword in keywords:
                if keyword in query:
                    target_features.add(feature)
        
        if not target_features:
            return None, 0.0
        
        # Find halls matching the target features
        hall_matches = Counter()
        for hall in self.housing_data:
            hall_features = [f.lower() for f in hall.get('features', [])]
            for target in target_features:
                if any(target in feature for feature in hall_features):
                    hall_matches[hall] += 1
        
        if hall_matches:
            # Get hall with most feature matches
            best_hall, match_count = hall_matches.most_common(1)[0]
            confidence = min(0.85, 0.6 + (match_count / len(target_features) * 0.25))
            return best_hall, confidence
            
        return None, 0.0
    
    def _find_hall_by_room_type(self, query):
        """Find residence halls based on room types mentioned"""
        room_keywords = {
            "single": ["single", "individual", "one person", "private", "by myself"],
            "double": ["double", "shared", "roommate", "two person", "with someone"],
            "triple": ["triple", "three person", "three roommates"],
            "apartment": ["apartment", "apt", "kitchen"]
        }
        
        # Determine which room type is being asked for
        target_room_type = None
        for room_type, keywords in room_keywords.items():
            for keyword in keywords:
                if keyword in query:
                    target_room_type = room_type
                    break
            if target_room_type:
                break
        
        if not target_room_type:
            return None, 0.0
        
        # Find halls with that room type
        matching_halls = []
        for hall in self.housing_data:
            room_types = [r.lower() for r in hall.get('room_types', [])]
            if any(target_room_type in room_type for room_type in room_types):
                matching_halls.append(hall)
        
        if matching_halls:
            # Return the first match with decent confidence
            return matching_halls[0], 0.8
            
        return None, 0.0
    
    def get_hall_rates(self, hall_name, room_type=None):
        """Get rental rates for a specific residence hall"""
        if hall_name not in self.rates_by_hall:
            return []
        
        rates = self.rates_by_hall[hall_name]
        
        # Filter by room type if specified
        if room_type:
            rates = [rate for rate in rates if room_type.lower() in rate.get('room_type', '').lower()]
            
        return rates
    
    def get_all_halls_by_type(self, hall_type):
        """Get all residence halls of a specific type"""
        if not hall_type:
            return []
        
        hall_type_lower = hall_type.lower()
        return [hall for hall in self.housing_data if hall_type_lower in hall.get('hall_type', '').lower()]
    
    def find_halls_by_feature(self, feature):
        """Find residence halls that have a specific feature"""
        if not feature:
            return []
        
        feature_lower = feature.lower()
        return [hall for hall in self.housing_data 
                if any(feature_lower in f.lower() for f in hall.get('features', []))]
    
    def find_halls_by_room_type(self, room_type):
        """Find residence halls offering a specific room type"""
        if not room_type:
            return []
        
        room_type_lower = room_type.lower()
        return [hall for hall in self.housing_data 
                if any(room_type_lower in r.lower() for r in hall.get('room_types', []))]
    
    def find_halls_in_price_range(self, min_price, max_price, term="fall_spring"):
        """Find residence halls within a specific price range"""
        matching_halls = set()
        
        for rate in self.rates_data:
            price = rate.get(term, 0)
            if min_price <= price <= max_price:
                hall_name = rate.get('residence_hall', '')
                if hall_name in self.halls_by_name:
                    matching_halls.add(self.halls_by_name[hall_name])
        
        return list(matching_halls)
    
    def get_cheapest_halls(self, top_n=5, term="fall_spring"):
        """Get the cheapest residence halls"""
        # Group rates by hall and get minimum rate for each hall
        hall_min_rates = {}
        for rate in self.rates_data:
            hall_name = rate.get('residence_hall', '')
            price = rate.get(term, 0)
            
            if hall_name not in hall_min_rates or price < hall_min_rates[hall_name]:
                hall_min_rates[hall_name] = price
        
        # Sort by price
        sorted_halls = sorted(hall_min_rates.items(), key=lambda x: x[1])
        
        # Get hall objects for the top N
        cheapest_halls = []
        for hall_name, price in sorted_halls[:top_n]:
            if hall_name in self.halls_by_name:
                hall = self.halls_by_name[hall_name]
                hall['min_price'] = price  # Add price to hall object
                cheapest_halls.append(hall)
        
        return cheapest_halls
    
    def get_related_links(self, topic=None):
        """Get links related to housing, optionally filtered by topic"""
        if not topic:
            return self.links_data
        
        topic_lower = topic.lower()
        return [link for link in self.links_data 
                if topic_lower in link.get('description', '').lower()]
    
    def get_all_halls_summary(self):
        """Get a brief summary of all residence halls"""
        summaries = []
        for hall in self.housing_data:
            name = hall.get('name', '')
            hall_type = hall.get('hall_type', '')
            
            # Get minimum price for fall/spring
            min_price = float('inf')
            for rate in self.rates_by_hall.get(name, []):
                price = rate.get('fall_spring', 0)
                if price > 0 and price < min_price:
                    min_price = price
            
            price_text = f"starting at ${min_price}/semester" if min_price < float('inf') else ""
            
            summary = f"• {name}: {hall_type} {price_text}"
            summaries.append(summary)
            
        return "\n".join(summaries)
    
    def compare_halls(self, hall_names, include_rates=True):
        """Compare multiple residence halls"""
        if not hall_names:
            return {}
        
        comparison = {}
        for name in hall_names:
            if name in self.halls_by_name:
                hall = self.halls_by_name[name]
                hall_data = {
                    "name": name,
                    "hall_type": hall.get('hall_type', ''),
                    "location": hall.get('location', ''),
                    "features": hall.get('features', []),
                    "room_types": hall.get('room_types', [])
                }
                
                # Add rates if requested
                if include_rates:
                    rates = self.get_hall_rates(name)
                    hall_data["rates"] = rates
                    
                comparison[name] = hall_data
                
        return comparison

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
    
    # Rest of the class implementation...

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
        'buildings': ['building', 'hall', 'center', 'stadium', 'arena', 'classroom', 'lab', 'location', 'dept', 'department'],
        'housing': ['residence', 'hall', 'dorm', 'housing', 'live', 'room', 'apartment', 'flat', 'roommate', 'suite'],
        'housing_types': ['traditional', 'apartment', 'suite', 'single', 'double', 'triple', 'quad'],
        'housing_rates': ['rate', 'cost', 'price', 'expensive', 'cheap', 'affordable', 'semester', 'fall', 'spring', 'summer'],
        'housing_features': ['kitchen', 'bathroom', 'laundry', 'wifi', 'furnished', 'elevator', 'air conditioning', 'ac', 'private', 'shared'],
        'housing_application': ['apply', 'application', 'deadline', 'deposit', 'request', 'submit']
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
        'find_housing': r'\b(where|which|find|locate|recommend)\b.+\b(live|dorm|residence|housing|hall)\b',
        'check_housing_rates': r'\b(cost|price|rate|how much|expensive|cheap)\b.+\b(dorm|residence|housing|hall|room|apartment)\b',
        'get_housing_info': r'\b(what|tell me|explain|information|about)\b.+\b(dorm|residence|housing|hall)\b',
        'compare_housing': r'\b(compare|differ|best|difference|better)\b.+\b(dorm|residence|housing|hall)\b',
        'apply_housing': r'\b(how|where|when)\b.+\b(apply|application|sign up|get|request)\b.+\b(dorm|residence|housing|hall)\b',
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
                'is_housing_query': False,  # Added for housing
                'is_followup': False,
                'amenity_type': None,
                'mentioned_libraries': [],
                'mentioned_buildings': [],
                'mentioned_residence_halls': [],  # Added for housing
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
        
        # Check if asking about housing
        is_housing_query = self._is_housing_query(query)
        
        # Check if asking about all residence halls
        is_all_residence_halls_query = self._is_all_residence_halls_query(query)
        
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
        
        # Extract residence hall mentions
        mentioned_residence_halls = self._extract_residence_hall_mentions(query)
        
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
            'is_housing_query': is_housing_query,
            'is_all_residence_halls_query': is_all_residence_halls_query,
            'tokens': tokens,
            'pos_tags': pos_tags,
            'noun_chunks': noun_chunks,
            'entities': entities,
            'time_reference': time_reference,
            'mentioned_libraries': mentioned_libraries,
            'mentioned_buildings': mentioned_buildings,
            'mentioned_residence_halls': mentioned_residence_halls,
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
        
        # Normalize residence hall terms
        query = re.sub(r"\bdorm(s|itory|itories)?\b", "residence hall", query, flags=re.IGNORECASE)
        
        # Normalize room reservation terms
        if "reserve" in query.lower() and "room" in query.lower():
            if not re.search(r"how|where|can i", query.lower()):
                query = f"how do I reserve a study room {query}"
            
        # Normalize website queries
        if "website" in query.lower() or "url" in query.lower():
            if not re.search(r"what|where is|find|get", query.lower()):
                query = f"find the website for {query}"
        
        # Normalize housing cost queries
        if re.search(r"cost|price|rate|how much", query.lower()) and re.search(r"dorm|residence|housing|hall", query.lower()):
            if not re.search(r"what|how much|tell me", query.lower()):
                query = f"how much does it cost to live in {query}"
        
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
            'which': r'\b(which|what)\s+(library|place|building|residence hall|dorm)\b',
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
    
    def _is_housing_query(self, query):
        """Check if the query is related to residence halls/housing"""
        housing_patterns = [
            r'\b(dorm|dormitory|residence hall|residence|housing)\b',
            r'\b(where|how)\s+(to|can I|do I)\s+(live|stay|reside)\s+(on|in)\s+campus',
            r'\b(on-campus|on campus)\s+(living|housing|residence)',
            r'\b(traditional|apartment|suite)\s+(style|hall|room)',
            r'\b(single|double|triple|quad)\s+(room|occupancy)',
            r'\b(beaty|broward|buckman|cypress|east|fletcher|graham|hume|infinity|jennings|keys|lakeside)\b',
            r'\b(mallory|murphree|north|rawlings|reid|riker|simpson|sledd|springs|tanglewood|thomas|tolbert|weaver|yulee)\b',
            r'\b(how much|cost|price|rate|rates)\s+(for|of|to live in)\s+(dorm|housing|residence hall)',
            r'\b(apply|application)\s+for\s+(housing|dorm|residence hall)'
        ]
        
        for pattern in housing_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                return True
                
        # Check for housing-related categories
        housing_categories = ['housing', 'housing_types', 'housing_rates', 'housing_features', 'housing_application']
        categories = self._classify_categories(query)
        
        if any(category in housing_categories for category in categories):
            return True
                
        return False
    
    def _is_all_residence_halls_query(self, query):
        """Check if the query is asking about all residence halls"""
        patterns = [
            r'\b(what|which|all|list)\s+(residence halls|dorms|dormitories)',
            r'\b(residence halls|dorms|dormitories)\s+(on|at|in)\s+campus',
            r'\bhow\s+many\s+(residence halls|dorms|dormitories)',
            r'\btell\s+me\s+about\s+(the|all)\s+(residence halls|dorms|dormitories)',
            r'\bwhere\s+can\s+I\s+live\s+on\s+campus'
        ]
        
        for pattern in patterns:
            if re.search(pattern, query, re.IGNORECASE):
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
                'check_housing_rates', 'find_housing', 'get_housing_info', 'compare_housing', 'apply_housing',
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
        
        # Housing-specific intent detection
        if self._is_housing_query(query_lower):
            # Check for rates questions
            if any(word in query_lower for word in ['cost', 'price', 'rate', 'how much', 'expensive', 'cheap']):
                specific_intents.append('check_housing_rates')
            
            # Check for comparison questions
            if any(word in query_lower for word in ['compare', 'difference', 'better', 'best']):
                specific_intents.append('compare_housing')
            
            # Check for application questions
            if any(word in query_lower for word in ['apply', 'application', 'sign up', 'request']):
                specific_intents.append('apply_housing')
            
            # Check for housing type questions
            if any(word in query_lower for word in ['traditional', 'apartment', 'suite']):
                specific_intents.append('housing_type_info')
            
            # Check for housing feature questions
            if any(word in query_lower for word in ['feature', 'amenity', 'offer', 'provide', 'include']):
                specific_intents.append('housing_features_info')
                
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
    
    def _extract_residence_hall_mentions(self, query):
        """Extract explicit mentions of residence halls"""
        hall_mentions = []
        
        # Common residence hall names and patterns
        hall_patterns = [
            (r'\b(beaty towers|beaty)\b', 'Beaty Towers'),
            (r'\b(broward hall|broward)\b', 'Broward Hall'),
            (r'\b(buckman hall|buckman)\b', 'Buckman Hall'),
            (r'\b(cypress hall|cypress)\b', 'Cypress Hall'),
            (r'\b(east hall|east)\b', 'East Hall'),
            (r'\b(fletcher hall|fletcher)\b', 'Fletcher Hall'),
            (r'\b(graham hall|graham)\b', 'Graham Hall'),
            (r'\b(honors village|honors)\b', 'Honors Village'),
            (r'\b(hume hall|hume)\b', 'Hume Hall'),
            (r'\b(infinity hall|infinity)\b', 'Infinity Hall'),
            (r'\b(jennings hall|jennings)\b', 'Jennings Hall'),
            (r'\b(keys complex|keys)\b', 'Keys Residential Complex'),
            (r'\b(lakeside complex|lakeside)\b', 'Lakeside Residential Complex'),
            (r'\b(mallory hall|mallory)\b', 'Mallory Hall'),
            (r'\b(murphree hall|murphree)\b', 'Murphree Hall'),
            (r'\b(north hall|north)\b', 'North Hall'),
            (r'\b(rawlings hall|rawlings)\b', 'Rawlings Hall'),
            (r'\b(reid hall|reid)\b', 'Reid Hall'),
            (r'\b(riker hall|riker)\b', 'Riker Hall'),
            (r'\b(simpson hall|simpson)\b', 'Simpson Hall'),
            (r'\b(sledd hall|sledd)\b', 'Sledd Hall'),
            (r'\b(springs complex|springs)\b', 'Springs Residential Complex'),
            (r'\b(thomas hall|thomas)\b', 'Thomas Hall'),
            (r'\b(tolbert hall|tolbert)\b', 'Tolbert Hall'),
            (r'\b(trusler hall|trusler)\b', 'Trusler Hall'),
            (r'\b(weaver hall|weaver)\b', 'Weaver Hall'),
            (r'\b(yulee hall|yulee)\b', 'Yulee Hall')
        ]
        
        for pattern, hall_name in hall_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                hall_mentions.append(hall_name)
        
        return hall_mentions
    
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
            r'^(what|where|when|how|why|who|which)\b.{1,30}\?  # Short questions are often follow-ups
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
        """Initialize the response generator with model"""
        self.llm = llm_model
        self.response_cache = LRUCache(capacity=100)
        
        # Create template registry
        self.templates = self._init_templates()
        
        # Create quality enhancer
        self.quality_enhancer = ResponseQualityEnhancer()
        
    def _init_templates(self):
        """Initialize response templates for common query types"""
        templates = {
            'hours': {
                'template': "{library_name} is open from {hours_today} today ({day_of_week}).\n\nRegular hours:\n{all_hours}\n\n{access_restrictions}",
                'required': ['library_name', 'hours_today', 'day_of_week']
            },
            'location': {
                'template': "{library_name} is located at {location}. {additional_info}",
                'required': ['library_name', 'location']
            },
            'meta': {
                'template': "Yes, I'm an AI assistant specifically designed to provide information about the University of Florida's libraries, buildings, campus resources, and housing options. I can help with questions about library hours, locations, services, collections, building information, residence halls, and other UF-related topics. How can I assist you today?",
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
            # Housing-specific templates
            'residence_hall_info': {
                'template': "{hall_name} is a {hall_type} residence hall located at {location}.\n\n{description}\n\nFeatures:\n{features_list}\n\nRoom types available:\n{room_types_list}\n\nFor more information, visit: {url}",
                'required': ['hall_name', 'hall_type', 'location']
            },
            'hall_rates': {
                'template': "Rates for {hall_name} (2025):\n\n{rates_list}\n\nPlease note that these rates are per semester. For official and up-to-date rates, please visit the UF Housing website at {rental_rate_url}",
                'required': ['hall_name', 'rates_list']
            },
            'all_halls': {
                'template': "UF offers the following residence halls on campus:\n\n{halls_list}\n\nThese residence halls offer various room types and amenities. Visit the UF Housing website for more details: https://housing.ufl.edu/",
                'required': ['halls_list']
            },
            'hall_comparison': {
                'template': "Comparison of {halls_names}:\n\n{comparison_table}\n\nVisit the UF Housing website for more details: https://housing.ufl.edu/",
                'required': ['halls_names', 'comparison_table']
            },
            'housing_application': {
                'template': "To apply for on-campus housing at UF:\n\n1. Visit {application_url}\n2. Log in with your GatorLink credentials\n3. Complete the housing application\n4. Pay the application fee of $25\n\nImportant dates:\n{dates_info}\n\nFor more information, refer to the Housing Application Guide: https://housing.ufl.edu/apply/how-to-apply/",
                'required': ['application_url']
            },
            'error': {
                'template': "I apologize, but I encountered an issue while processing your request. Please try asking your question again, perhaps with different wording.",
                'required': []
            }
        }
        
        return templates
    
    def generate(self, query, library=None, building=None, residence_hall=None, query_analysis=None, conversation_history=None, academic_context=None):
        """Generate a response with advanced verification and enhancement"""
        # Start timing for performance tracking
        start_time = time.time()
        
        # Generate cache key based on query and context
        cache_key = f"{query}"
        if library:
            cache_key += f":{library['Library Name']}"
        if building:
            cache_key += f":{building['Building Name']}"
        if residence_hall:
            cache_key += f":{residence_hall['name']}"
            
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
            
            # Check if this is a housing query first
            is_housing_query = query_analysis.get('is_housing_query', False)
            
            if is_housing_query and residence_hall:
                # Handle residence hall information requests
                if 'check_housing_rates' in specific_intents:
                    rates_response = self._generate_hall_rates_response(residence_hall)
                    if rates_response:
                        metrics = {
                            'confidence': 0.95,
                            'method': 'template',
                            'template_used': 'hall_rates',
                            'residence_hall': residence_hall
                        }
                        # Cache and return
                        self.response_cache[cache_key] = (rates_response, metrics)
                        return rates_response, metrics
                
                # Handle general hall info requests
                hall_info_response = self._generate_hall_info_response(residence_hall)
                if hall_info_response:
                    metrics = {
                        'confidence': 0.95,
                        'method': 'template',
                        'template_used': 'residence_hall_info',
                        'residence_hall': residence_hall
                    }
                    # Cache and return
                    self.response_cache[cache_key] = (hall_info_response, metrics)
                    return hall_info_response, metrics
            
            # Handle "all residence halls" queries
            if query_analysis.get('is_all_residence_halls_query', False):
                halls_list_response = self._generate_all_halls_response()
                if halls_list_response:
                    metrics = {
                        'confidence': 0.95,
                        'method': 'template',
                        'template_used': 'all_halls'
                    }
                    # Cache and return
                    self.response_cache[cache_key] = (halls_list_response, metrics)
                    return halls_list_response, metrics
            
            # Handle housing application queries
            if 'apply_housing' in specific_intents:
                application_response = self._generate_housing_application_response()
                if application_response:
                    metrics = {
                        'confidence': 0.95,
                        'method': 'template',
                        'template_used': 'housing_application'
                    }
                    # Cache and return
                    self.response_cache[cache_key] = (application_response, metrics)
                    return application_response, metrics
            
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
                    residence_hall,
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
                    if residence_hall:
                        llm_metrics['residence_hall'] = residence_hall
                    
                    # Cache response
                    self.response_cache[cache_key] = (enhanced_response, llm_metrics)
                    
                    return enhanced_response, llm_metrics
            
            # Try template-based responses as fallback
            template_response, template_metrics = self._generate_template_response(
                query, query_analysis, library, building, residence_hall, conversation_history, academic_context
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
                if residence_hall:
                    template_metrics['residence_hall'] = residence_hall
                
                # Cache response
                self.response_cache[cache_key] = (template_response, template_metrics)
                
                return template_response, template_metrics
                
            # Fallback response if both methods failed
            fallback_response = "I'm not able to answer that specific question about UF. Could you try rephrasing your question or ask about something like library hours, building locations, residence halls, or campus services?"
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
    
    def _generate_hall_info_response(self, residence_hall):
        """Generate a response for residence hall information"""
        hall_name = residence_hall.get('name', '')
        hall_type = residence_hall.get('hall_type', '')
        location = residence_hall.get('location', '')
        description = residence_hall.get('description', '')
        url = residence_hall.get('url', '')
        
        # Format features list
        features_list = ""
        for feature in residence_hall.get('features', []):
            features_list += f"• {feature}\n"
            
        # Format room types list
        room_types_list = ""
        for room_type in residence_hall.get('room_types', []):
            if "College of" not in room_type and "Hall" not in room_type:  # Filter out non-room-type entries
                room_types_list += f"• {room_type}\n"
        
        return self.templates['residence_hall_info']['template'].format(
            hall_name=hall_name,
            hall_type=hall_type,
            location=location,
            description=description,
            features_list=features_list.strip(),
            room_types_list=room_types_list.strip(),
            url=url
        )
    
    def _generate_hall_rates_response(self, residence_hall, rates_data=None):
        """Generate a response with residence hall rates"""
        hall_name = residence_hall.get('name', '')
        rental_rate_url = residence_hall.get('rental_rate_url', 'https://housing.ufl.edu/rates-payments-agreements/residence-hall-rental-rates/')
        
        # Format rates list
        rates_list = ""
        
        if rates_data:
            hall_rates = [rate for rate in rates_data if rate.get('residence_hall', '') == hall_name]
            
            if hall_rates:
                for rate in hall_rates:
                    room_type = rate.get('room_type', '')
                    fall_spring = rate.get('fall_spring', 0)
                    summer_a_b = rate.get('summer_a_b', 0)
                    summer_c = rate.get('summer_c', 0)
                    
                    rates_list += f"• {room_type}:\n"
                    rates_list += f"  - Fall/Spring: ${fall_spring}\n"
                    rates_list += f"  - Summer A/B: ${summer_a_b}\n"
                    rates_list += f"  - Summer C: ${summer_c}\n\n"
            else:
                rates_list = "Rate information for this hall is not available. Please check the UF Housing website for current rates."
        else:
            rates_list = "Rate information for this hall is not available. Please check the UF Housing website for current rates."
            
        return self.templates['hall_rates']['template'].format(
            hall_name=hall_name,
            rates_list=rates_list.strip(),
            rental_rate_url=rental_rate_url
        )
    
    def _generate_all_halls_response(self):
        """Generate a response listing all residence halls"""
        halls_list = "• Traditional Style Halls: Broward Hall, Buckman Hall, East Hall, Fletcher Hall, Graham Hall, Jennings Hall, Mallory Hall, Murphree Hall, North Hall, Rawlings Hall, Reid Hall, Riker Hall, Simpson Hall, Sledd Hall, Thomas Hall, Tolbert Hall, Trusler Hall, Weaver Hall, Yulee Hall\n\n"
        halls_list += "• Suite Style Halls: Cypress Hall, Honors Village, Hume Hall, Infinity Hall, Springs Residential Complex\n\n"
        halls_list += "• Apartment Style Halls: Beaty Towers, Corry Village, Diamond Village, Keys Residential Complex, Lakeside Residential Complex, Tanglewood Village, The Continuum"
        
        return self.templates['all_halls']['template'].format(
            halls_list=halls_list
        )
    
    def _generate_housing_application_response(self):
        """Generate a response about housing applications"""
        application_url = "https://housing.ufl.edu/apply/"
        
        # Application dates info
        dates_info = "• First-Year Students: Applications typically open in November for the following academic year\n"
        dates_info += "• Current Students: Applications typically open in February for the following academic year\n"
        dates_info += "• Graduate and Family Housing: Applications accepted on a rolling basis\n\n"
        dates_info += "Note: Housing assignments are made on a first-come, first-served basis, so it's recommended to apply as early as possible."
        
        return self.templates['housing_application']['template'].format(
            application_url=application_url,
            dates_info=dates_info
        )
    
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
    
    def _generate_template_response(self, query, query_analysis, library, building, residence_hall, conversation_history=None, academic_context=None):
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
            
        # Handle requests for all residence halls
        if query_analysis.get('is_all_residence_halls_query', False):
            halls_list = self._generate_all_halls_list()
            metrics['confidence'] = 0.95
            metrics['template_used'] = 'all_halls'
            return self.templates['all_halls']['template'].format(
                halls_list=halls_list
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
        
        # Residence hall specific templates
        if residence_hall:
            hall_name = residence_hall.get('name', '')
            
            # Handle rates query
            if ('housing_rates' in query_analysis.get('categories', []) or
                query_analysis.get('intent') == 'check_housing_rates' or
                any(word in query.lower() for word in ['cost', 'price', 'rate', 'how much'])):
                
                rates_response = self._generate_hall_rates_response(residence_hall)
                metrics['confidence'] = 0.95
                metrics['template_used'] = 'hall_rates'
                return rates_response, metrics
            
            # Handle general info query
            if ('housing' in query_analysis.get('categories', []) or
                query_analysis.get('intent') == 'get_housing_info' or
                query_analysis.get('question_type') == 'what'):
                
                info_response = self._generate_hall_info_response(residence_hall)
                metrics['confidence'] = 0.95
                metrics['template_used'] = 'residence_hall_info'
                return info_response, metrics
                    
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
            
            # Other library-specific templates...
        
        # For other query types, use LLM
        return None, metrics
    
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
    
    def _generate_all_halls_list(self):
        """Generate a formatted list of all residence halls"""
        halls_list = "• Traditional Style Halls: Broward Hall, Buckman Hall, East Hall, Fletcher Hall, Graham Hall, Jennings Hall, Mallory Hall, Murphree Hall, North Hall, Rawlings Hall, Reid Hall, Riker Hall, Simpson Hall, Sledd Hall, Thomas Hall, Tolbert Hall, Trusler Hall, Weaver Hall, Yulee Hall\n\n"
        halls_list += "• Suite Style Halls: Cypress Hall, Honors Village, Hume Hall, Infinity Hall, Springs Residential Complex\n\n"
        halls_list += "• Apartment Style Halls: Beaty Towers, Corry Village, Diamond Village, Keys Residential Complex, Lakeside Residential Complex, Tanglewood Village, The Continuum"
        
        return halls_list
        
    def _generate_amenity_content(self, amenity_type, library, query_analysis):
        """Generate content for amenity templates"""
        # Existing implementation...
        return None
        
    def _generate_llm_response(self, query, query_analysis, library=None, building=None, residence_hall=None, conversation_history=None, academic_context=None):
        """Generate a response using the LLM model"""
        if not self.llm:
            # If no LLM is available, return None to use fallback
            return None, {'confidence': 0.0}
        
        # Create optimized prompt for LLaMA 3
        prompt = self._generate_optimized_prompt(
            query, query_analysis, library, building, residence_hall, conversation_history, academic_context
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
                response, query, query_analysis, library, building, residence_hall
            )
            
            return response, {'confidence': confidence}
            
        except Exception as e:
            logger.error(f"Error generating LLM response: {e}")
            return None, {'confidence': 0.0, 'error': str(e)}
            
    def _generate_optimized_prompt(self, query, query_analysis, library=None, building=None, residence_hall=None, conversation_history=None, academic_context=None):
        """Generate an optimized prompt for LLaMA 3"""
        # Create system message
        system_message = """<|system|>
You are the UF Assistant, an expert on University of Florida. 
Provide accurate, helpful information about campus buildings, libraries, resources, residence halls, and housing options.
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
        
        # Add residence hall context if relevant
        if residence_hall:
            hall_name = residence_hall.get('name', '')
            
            context += f"Residence Hall: {hall_name}\n"
            context += f"Hall Type: {residence_hall.get('hall_type', '')}\n"
            context += f"Location: {residence_hall.get('location', '')}\n"
            context += f"Description: {residence_hall.get('description', '')}\n"
            
            # Features
            features = residence_hall.get('features', [])
            if features:
                context += "Features:\n"
                for feature in features:
                    context += f"- {feature}\n"
            
            # Room types
            room_types = residence_hall.get('room_types', [])
            if room_types:
                context += "Room Types:\n"
                for room_type in room_types:
                    if "College of" not in room_type and "Hall" not in room_type:  # Filter out non-room-type entries
                        context += f"- {room_type}\n"
            
            # Contact and website
            if residence_hall.get('phone', ''):
                context += f"Phone: {residence_hall.get('phone', '')}\n"
            if residence_hall.get('url', ''):
                context += f"Website: {residence_hall.get('url', '')}\n"
            
            # Rates information (if available)
            context += "\nPlease note that residence hall rates vary by room type and term (Fall/Spring vs. Summer).\n"
                
        # Add general UF information if no specific entity
        if not library and not building and not residence_hall:
            # Determine what kind of information to include based on query
            if query_analysis.get('is_housing_query', False):
                context += "UF offers a variety of on-campus housing options:\n\n"
                context += "1. Traditional Style Halls: Shared community bathrooms, community kitchens, typically double or triple occupancy rooms\n"
                context += "2. Suite Style Halls: Semi-private bathrooms shared with suitemates, typically double or single rooms\n"
                context += "3. Apartment Style Halls: Full kitchens, private or shared bedrooms, private bathrooms\n\n"
                context += "Housing costs vary by hall type, room type, and term (Fall/Spring vs. Summer).\n"
                context += "Applications typically open in November for first-year students and February for current students.\n"
                context += "For more information, students can visit: https://housing.ufl.edu/\n"
                
            elif query_analysis.get('is_building_query'):
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
                context += "The campus includes various libraries, academic buildings, research facilities, residence halls, and student resources. "
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
            elif intent == 'check_housing_rates':
                system_guidance = "Provide specific rates for the requested residence hall, noting differences by room type and term."
            elif intent == 'get_housing_info':
                system_guidance = "Describe the residence hall, its features, room types, and location on campus."
            elif intent == 'compare_housing':
                system_guidance = "Compare the requested residence halls focusing on type, features, location, and rates."
            elif intent == 'apply_housing':
                system_guidance = "Explain the housing application process, including timelines, fees, and steps."
                
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
            
        elif intent in ['get_information', 'discover_offerings', 'building_info', 'get_housing_info']:
            # Balanced for informational content
            params['temperature'] = 0.6
            params['max_tokens'] = 1000  # Allow longer responses for information
            
        elif intent in ['get_recommendations', 'compare_libraries', 'compare_housing']:
            # More creative for suggestions
            params['temperature'] = 0.75
            params['top_p'] = 0.85
            
        # Adjust for short queries (likely follow-ups)
        if query_analysis.get('is_followup', False):
            params['max_tokens'] = 500  # Shorter responses for follow-ups
            
        return params
        
    def _calculate_response_confidence(self, response, query, query_analysis, library=None, building=None, residence_hall=None):
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
        elif query_analysis.get('question_type') == 'how' and ('cost' in query.lower()) and re.search(r'\$\d+', response):
            confidence += 0.1
            
        # Check for entity name inclusion
        if library and library.get('Library Name', '') in response:
            confidence += 0.05
        if building and building.get('Building Name', '') in response:
            confidence += 0.05
        if residence_hall and residence_hall.get('name', '') in response:
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
        
        # Standardize dollar amounts
        money_pattern = r'(\d+)(\s+)dollars'
        response = re.sub(money_pattern, r'$\1', response)
        
        return response

class ResponseQualityEnhancer:
    """Enhances response quality with better formatting and contextual additions"""
    
    def __init__(self):
        self.formatting_patterns = {
            'hours': r'(\d{1,2}(?::\d{2})?(?:am|pm|AM|PM))\s*-\s*(\d{1,2}(?::\d{2})?(?:am|pm|AM|PM))',
            'lists': r'(?:\n\s*[-•*]\s+.+){2,}',
            'locations': r'\b\d+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:\s+(?:Rd|Dr|St|Ave))?\b',
            'urls': r'(https?://[^\s]+)',
            'money': r'\$(\d+(?:\.\d{2})?)'
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
        
        # Standardize money formatting
        def format_money(match):
            amount = match.group(1)
            # Format with commas for thousands
            try:
                value = float(amount)
                if value.is_integer():
                    return f"${int(value):,}"
                else:
                    return f"${value:,.2f}"
            except:
                return f"${amount}"
                
        response = re.sub(self.formatting_patterns['money'], format_money, response)
        
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
                    
        # Add housing application info
        if intent == 'apply_housing' and 'housing.ufl.edu/apply' not in response:
            application_info = "\n\nTo apply for housing, visit https://housing.ufl.edu/apply/"
            if not response.endswith((".", "!", "?")):
                response += "."
            response += application_info
            
        # Add housing rates info
        if intent == 'check_housing_rates' and not re.search(r'\$\d+', response):
            rates_info = "\n\nFor the most up-to-date housing rates, visit https://housing.ufl.edu/rates-payments-agreements/"
            if not response.endswith((".", "!", "?")):
                response += "."
            response += rates_info
            
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
            logger.info("✅ Successfully initialized LLaMA 3 model")
        else:
            logger.warning("⚠️ Failed to load LLaMA model - some features will be limited")
        
        # Initialize embedding model
        self.embedding_model = self._init_embedding_model()
        if self.embedding_model:
            logger.info("✅ Successfully initialized embedding model")
        else:
            logger.warning("⚠️ No embedding model available - semantic search will be disabled")
        
        # Initialize NLP model
        self.nlp_model = self._init_nlp_model()
        if self.nlp_model:
            logger.info("✅ Successfully initialized NLP model")
        else:
            logger.warning("⚠️ No NLP model available - some linguistic features will be limited")
        
        # Load campus buildings data
        self.campus_buildings_data = load_campus_buildings_data()
        
        # Load housing data
        self.housing_data, self.rates_data, self.links_data = load_housing_data()
        
        # Initialize enhanced components
        self.library_knowledge = EnhancedKnowledgeRetrieval(LIBRARY_DATA, self.embedding_model)
        logger.info("✅ Initialized library knowledge retrieval system")
        
        self.buildings_knowledge = CampusBuildingsRetrieval(self.campus_buildings_data)
        logger.info("✅ Initialized campus buildings knowledge retrieval system")
        
        self.housing_knowledge = HousingKnowledgeRetrieval(self.housing_data, self.rates_data, self.links_data, self.embedding_model)
        logger.info("✅ Initialized housing knowledge retrieval system")
        
        self.query_analyzer = EnhancedQueryAnalyzer(self.nlp_model)
        logger.info("✅ Initialized enhanced query analyzer")
        
        self.response_generator = AdvancedResponseGenerator(self.llm)
        logger.info("✅ Initialized advanced response generator")
        
        self.academic_calendar = AcademicCalendarContext()
        logger.info("✅ Initialized academic calendar context")
        
        # Initialize conversation management
        self.conversation_history = []
        self.conversation_state = ConversationState()
        logger.info("✅ Initialized conversation state manager")
        
        # Initialize performance metrics tracking
        self.metrics_tracker = MetricsTracker()
        logger.info("✅ Initialized metrics tracker")
        
        # Measure initialization time
        init_time = time.time() - init_start_time
        logger.info(f"✅ Initialization complete in {init_time:.2f} seconds")
        
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
                              
            # Determine if this is a housing-related query
            is_housing_query = 'housing' in query_analysis.get('categories', []) or \
                              any(category in query_analysis.get('categories', []) for category in 
                                 ['housing_types', 'housing_rates', 'housing_features', 'housing_application']) or \
                              query_analysis.get('intent') in ['find_housing', 'check_housing_rates', 'get_housing_info'] or \
                              query_analysis.get('is_housing_query', False) or \
                              query_analysis.get('is_all_residence_halls_query', False)
            
            # Initialize relevant entities
            library = None
            library_confidence = 0.0
            building = None
            building_confidence = 0.0
            residence_hall = None
            residence_hall_confidence = 0.0
            
            # If this is a follow-up, try to use the previously active context
            if query_analysis.get('is_followup', False):
                if is_housing_query or not (is_building_query or is_library_query):
                    # Check for residence hall context first
                    prev_hall = self.conversation_state.get_active_residence_hall()
                    if prev_hall and self.conversation_state.should_maintain_context(query, prev_hall):
                        residence_hall = prev_hall
                        residence_hall_confidence = 0.8
                        logger.info(f"Using previous residence hall context: {residence_hall.get('name', '')}")
                
                if (is_building_query or not is_library_query) and not residence_hall:
                    # Check for building context
                    prev_building = self.conversation_state.get_active_building()
                    if prev_building and self.conversation_state.should_maintain_context(query, prev_building):
                        building = prev_building
                        building_confidence = 0.8
                        logger.info(f"Using previous building context: {building.get('Building Name', '')}")
                
                if (is_library_query or (not building and not is_building_query)) and not residence_hall:
                    # Check for library context
                    prev_library = self.conversation_state.get_active_library()
                    if prev_library and self.conversation_state.should_maintain_context(query, prev_library):
                        library = prev_library
                        library_confidence = 0.8
                        logger.info(f"Using previous library context: {library.get('Library Name', '')}")
            
            # If no context from history, try to identify from query
            if is_housing_query and not residence_hall:
                residence_hall, residence_hall_confidence = self.housing_knowledge.retrieve_residence_hall(query)
                
                if residence_hall:
                    logger.info(f"Identified residence hall: {residence_hall.get('name', '')} (confidence: {residence_hall_confidence:.2f})")
                else:
                    logger.info("No specific residence hall identified")
                
            if is_building_query and not building and not residence_hall:
                building, building_confidence = self.buildings_knowledge.retrieve_building(query)
                
                if building:
                    logger.info(f"Identified building: {building.get('Building Name', '')} (confidence: {building_confidence:.2f})")
                else:
                    logger.info("No specific building identified")
                    
            if (is_library_query or not (building or residence_hall)) and not library:
                library, library_confidence = self.library_knowledge.retrieve_relevant_library(
                    query, query_analysis
                )
                
                if library:
                    logger.info(f"Identified library: {library.get('Library Name', '')} (confidence: {library_confidence:.2f})")
                else:
                    logger.info("No specific library identified")
            
            # Update active entities in conversation state
            if residence_hall and residence_hall_confidence >= 0.7:
                self.conversation_state.set_active_residence_hall(residence_hall)
            
            if building and building_confidence >= 0.7:
                self.conversation_state.set_active_building(building)
            
            if library and library_confidence >= 0.7:
                self.conversation_state.set_active_library(library)
            
            # Generate response
            response, generation_metrics = self.response_generator.generate(
                query, 
                library,
                building,
                residence_hall,
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
            if residence_hall and residence_hall_confidence >= 0.5:
                metrics['residence_hall'] = residence_hall
                
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
        
        # Normalize residence hall terms
        query = re.sub(r"\bdorm(s|itory|itories)?\b", "residence hall", query, flags=re.IGNORECASE)
        
        # Normalize common residence hall abbreviations
        query = re.sub(r"\bbeaty\b", "Beaty Towers", query, flags=re.IGNORECASE)
        query = re.sub(r"\bhume\b", "Hume Hall", query, flags=re.IGNORECASE)
        query = re.sub(r"\bbroward\b", "Broward Hall", query, flags=re.IGNORECASE)
        
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
                
        # Housing cost queries
        if re.search(r"cost|price|rate|how much", query_lower) and re.search(r"dorm|residence|housing|hall", query_lower):
            if not re.search(r"what are|how much", query_lower):
                query = f"how much does it cost to live in {query}"
        
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
    # Other examples...
    {
        "query": "Tell me about Beaty Towers",
        "response": "Beaty Towers is an Apartment Style residence hall located at 11 Beaty Towers, Gainesville, FL 32612-1101. It's centrally located on the corner of Museum Road and 13th Street, close to the College of Music, Design Construction and Planning, and a short walk to the Warrington College of Business.\n\nEach apartment features double room suites with a semi-private bathroom, built-in desks, and a kitchenette complete with a refrigerator, oven, and garbage disposal.\n\nFeatures:\n• Fully Furnished\n• Twin XL Beds\n• Passenger Elevators\n• High-Speed Internet\n• Laundry Facilities\n• The Market in Beaty Towers\n• Game Room\n\nBeaty Towers offers Apartment Double rooms at a rate of $3,821 per semester for Fall/Spring and $1,433 for Summer A or B ($2,866 for Summer C).\n\nFor more information, visit: https://housing.ufl.edu/beaty-towers/"
    },
    {
        "query": "How much does on-campus housing cost?",
        "response": "UF on-campus housing costs vary by residence hall type, room configuration, and semester. Here's a general overview of the pricing (2025 rates):\n\n• Traditional Style Halls (like Broward, Buckman, East):\n  - Single rooms: $3,766 per Fall/Spring semester\n  - Double rooms: $3,556 per Fall/Spring semester\n  - Triple rooms: $3,136 per Fall/Spring semester\n\n• Suite Style Halls (like Cypress, Hume, Springs):\n  - Single suites: $4,408-$5,081 per Fall/Spring semester\n  - Double suites: $4,109-$4,800 per Fall/Spring semester\n\n• Apartment Style Halls (like Beaty, Keys, Lakeside):\n  - Single rooms in apartments: $4,262-$4,603 per Fall/Spring semester\n  - Double rooms in apartments: $3,821 per Fall/Spring semester\n\nSummer rates are approximately 35-40% of the Fall/Spring rates for a single term (A or B), or about 75% for the full Summer C term.\n\nThe Honors Village and Infinity Hall tend to be among the most expensive options, while traditional triple rooms are typically the most affordable.\n\nFor exact rates and up-to-date information, visit: https://housing.ufl.edu/rates-payments-agreements/residence-hall-rental-rates/"
    },
    {
        "query": "How do I apply for housing at UF?",
        "response": "To apply for on-campus housing at UF:\n\n1. Visit https://housing.ufl.edu/apply/\n2. Log in with your GatorLink credentials\n3. Complete the housing application\n4. Pay the application fee of $25\n\nImportant dates to know:\n• First-Year Students: Applications typically open in November for the following academic year\n• Current Students: Applications typically open in February for the following academic year\n• Graduate and Family Housing: Applications accepted on a rolling basis\n\nHousing assignments are made on a first-come, first-served basis, so it's recommended to apply as early as possible. For more information, refer to the Housing Application Guide: https://housing.ufl.edu/apply/how-to-apply/"
    },
    {
        "query": "What residence halls are available at UF?",
        "response": "UF offers the following residence halls on campus:\n\n• Traditional Style Halls: Broward Hall, Buckman Hall, East Hall, Fletcher Hall, Graham Hall, Jennings Hall, Mallory Hall, Murphree Hall, North Hall, Rawlings Hall, Reid Hall, Riker Hall, Simpson Hall, Sledd Hall, Thomas Hall, Tolbert Hall, Trusler Hall, Weaver Hall, Yulee Hall\n\n• Suite Style Halls: Cypress Hall, Honors Village, Hume Hall, Infinity Hall, Springs Residential Complex\n\n• Apartment Style Halls: Beaty Towers, Corry Village, Diamond Village, Keys Residential Complex, Lakeside Residential Complex, Tanglewood Village, The Continuum\n\nThese residence halls offer various room types and amenities. Visit the UF Housing website for more details: https://housing.ufl.edu/"
    }
]

# =============================================================================
# INTERACTIVE CLI
# =============================================================================

def interactive_cli(assistant):
    """Run an interactive CLI for the UF Assistant"""
    print("\n=== Enhanced UF Assistant ===")
    print("Type your questions about UF libraries, campus buildings, and housing (or '/help' for commands)")
    
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
                    print("\nTop Residence Hall Matches:")
                    for hall, count in metrics['top_residence_halls'].items():
                        print(f"  - {hall}: {count}")
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
# HOUSING TEST SPECIFIC FUNCTION
# =============================================================================

def test_housing_queries(assistant):
    """Test housing-related queries on the UF Assistant"""
    housing_tests = [
        "Tell me about Beaty Towers",
        "What are the different types of housing options at UF?",
        "How much does it cost to live in Hume Hall?",
        "What features does Infinity Hall have?",
        "Which residence halls are closest to the engineering buildings?",
        "Compare Broward Hall and Jennings Hall",
        "What's the cheapest housing option at UF?",
        "How do I apply for housing at UF?",
        "Are there apartment-style residence halls?",
        "What's the difference between traditional style and suite style halls?"
    ]
    
    print(f"\n===== TESTING HOUSING QUERIES =====\n")
    
    for i, query in enumerate(housing_tests):
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
        'housing': [
            "Tell me about Beaty Towers",
            "What are the different types of housing options at UF?",
            "How much does it cost to live in Hume Hall?",
            "What features does Infinity Hall have?",
            "Which residence halls are closest to the engineering buildings?",
            "Compare Broward Hall and Jennings Hall",
            "What's the cheapest housing option at UF?",
            "How do I apply for housing at UF?",
            "Are there apartment-style residence halls?",
            "What's the difference between traditional style and suite style halls?"
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
# MAIN FUNCTION
# =============================================================================

def main():
    """Main function to run the Enhanced UF Assistant"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Enhanced UF Assistant')
    parser.add_argument('--model_path', type=str, default='/Users/emmamitchell/Desktop/GatorNet/AI/models/Meta-Llama-3-8B-Instruct-Q8_0.gguf',
                      help='Path to the LLaMA model')
    parser.add_argument('--use_gpu', action='store_true',
                      help='Use GPU for inference if available')
    parser.add_argument('--test', choices=['basic', 'detailed', 'edge_cases', 'housing', 'buildings', 'all'],
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
        if args.test == 'housing':
            test_housing_queries(assistant)
        elif args.test == 'buildings':
            test_building_queries(assistant)
        elif args.test == 'all':
            run_batch_tests(assistant, 'basic')
            test_housing_queries(assistant)
            test_building_queries(assistant)
        else:
            run_batch_tests(assistant, args.test)
    
    # Run interactive mode if requested or if no tests were run
    if args.interactive or not args.test:
        interactive_cli(assistant)
    
    print("\nThank you for using the Enhanced UF Assistant!")

if __name__ == "__main__":
    main()