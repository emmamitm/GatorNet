# AI_model.py
import requests
from bs4 import BeautifulSoup
from llama_cpp import Llama
import re
import numpy as np
import time
from collections import deque
from sentence_transformers import SentenceTransformer
import logging
import os
import pickle
import json
import gdown
from pySmartDL import SmartDL
import sys
import argparse

class UFAssistant:
    def __init__(self, check_only=False):
        # Expanded source URLs for better coverage
        self.UF_BASE_URLS = [
            'https://catalog.ufl.edu/UGRD/programs/',
            'https://catalog.ufl.edu/UGRD/colleges-schools/',
            'https://www.uflib.ufl.edu/about-us/',
            'https://housing.ufl.edu/living-options/apply/residence-halls/',
            'https://campusmap.ufl.edu/',
            'https://www.bsd.ufl.edu/g1c/campus_map/Buildings.aspx',
            'https://rec.ufl.edu/facilities/',
            'https://www.dso.ufl.edu/departments',
            'https://news.ufl.edu/',
            'https://calendar.ufl.edu/',
            'https://www.uflib.ufl.edu/using/hours.html',
            'https://businessservices.ufl.edu/services/gator-dining/locations/',
            'https://parking.ufl.edu/parking-at-uf/',
            'https://ufl.edu',
            'https://news.ufl.edu',
            'https://calendar.ufl.edu/all',
            'https://calendar.ufl.edu/studentlife/all',
            'https://studentlife.ufl.edu/',
            'https://studentlife.ufl.edu/all-news/',
            'https://catalog.ufl.edu/UGRD/dates-deadlines/',
            'https://catalog.ufl.edu/UGRD/academic-programs/departments/',
            'https://orgs.studentinvolvement.ufl.edu/organizations',
            'https://orgs.studentinvolvement.ufl.edu/Events',
            'https://major.biology.ufl.edu/advising/biology-related-student-clubs/',
            'https://news.clas.ufl.edu/',
            'https://clas.ufl.edu/calendar/',
            'https://www.eng.ufl.edu/newengineer/',
            'https://www.eng.ufl.edu/news-events/events-calendar/',
            'https://warrington.ufl.edu/about/fisher/news/',
            'https://warrington.ufl.edu/accounting-current-students/fsoa-calendars/',
            'https://blogs.ifas.ufl.edu/news/',
            'https://ifas.ufl.edu/newsroom/',
            'https://arts.ufl.edu/in-the-loop/news/',
            'https://news.warrington.ufl.edu/tag/heavener-school-of-business/',
            'https://warrington.ufl.edu/about/events/',
            'https://dcp.ufl.edu/rinker/category/news/',
            'https://dcp.ufl.edu/rinker/events-calendar/',
            'https://dcp.ufl.edu/dcp-news/',
            'https://dcp.ufl.edu/dcp-events/',
            'https://hhp.ufl.edu/about/news/',
            'https://hhp.ufl.edu/about/events/',
            'https://www.jou.ufl.edu/category/college-news/',
            'https://www.jou.ufl.edu/calendar/',
            'https://blogs.ifas.ufl.edu/snre/',
            'https://recsports.ufl.edu/',
            'https://recsports.ufl.edu/events/',
            'https://career.ufl.edu/',
            'https://careerhub.ufl.edu/events/',
            'https://careerhub.ufl.edu/jobs/',
            'https://www.advising.ufl.edu/beyond120/events/',
            'https://floridagators.com/calendar'
        ]
        
        
        self.STATIC_KNOWLEDGE = {
            "libraries": {
                "Marston Science Library": {
                    "location": "Central campus, near Century Tower",
                    "description": "Science and engineering focused library with study spaces and collaboration rooms",
                    "features": ["24/5 study space", "3D printing", "VR/AR lab", "Computer labs", "Group study rooms", "Silent study floors", "Research assistance"],
                    "floors": {
                        "Ground": "Computers and collaboration space",
                        "First": "MADE@UF lab and group study",
                        "Second": "Quiet study and stacks",
                        "Third": "Silent study and research materials",
                        "Fourth": "Silent study"
                    }
                },
                "Library West": {
                    "location": "Next to Plaza of the Americas",
                    "description": "Humanities and social sciences library with extensive study areas",
                    "features": ["24/5 study space", "Graduate study rooms", "Starbucks", "Group study pods", "Research assistance", "Writing center satellite"],
                    "floors": {
                        "Ground": "Starbucks and casual study",
                        "First": "Research help and circulation",
                        "Second": "Group study and computers",
                        "Third": "Quiet study and stacks",
                        "Fourth": "Graduate study and silence",
                        "Fifth & Sixth": "Silent study"
                    }
                },
                "Education Library": {
                    "location": "Norman Hall",
                    "description": "Education and teaching resources",
                    "features": ["Children's literature collection", "Curriculum resources", "Study rooms"]
                },
                "Health Science Library": {
                    "location": "Health Science Center",
                    "description": "Medical and health sciences resources",
                    "features": ["Medical databases", "Study rooms", "Clinical information resources"]
                },
                "Architecture and Fine Arts Library": {
                    "location": "Fine Arts Building A",
                    "description": "Art, architecture, and design resources",
                    "features": ["Visual arts collections", "Digital media lab", "Special collections"]
                }
            },
            "buildings": {
                "Reitz Union": {
                    "location": "Museum Road",
                    "description": "Student union with dining, study spaces, and meeting rooms",
                    "features": ["Food court", "Game room", "Career center", "Hotel", "Computer lab", "UF Bookstore", "ATMs", "Printing services"],
                    "dining_options": ["Starbucks", "Panda Express", "Subway", "Pollo Tropical", "Wing Zone"],
                    "services": ["GatorWell", "Multicultural Affairs", "Student Government", "Student Activities"]
                },
                "Ben Hill Griffin Stadium": {
                    "location": "Central campus",
                    "description": "Home of Gator football, known as 'The Swamp'",
                    "features": ["90,000+ capacity", "Gator sportshop", "Hall of Fame"],
                    "history": "Opened in 1930, named after Ben Hill Griffin Jr. in 1989",
                    "traditions": ["Mr. Two Bits", "Gator chomp", "We Are the Boys"]
                },
                "Century Tower": {
                    "location": "Historic part of campus",
                    "description": "157-foot carillon tower",
                    "features": ["61-bell carillon", "Musical performances", "Campus landmark"],
                    "history": "Built in 1953 to commemorate the university's centennial"
                },
                "Norman Hall": {
                    "location": "East campus",
                    "description": "College of Education building",
                    "features": ["Recently renovated", "Education library", "Classrooms", "Norman Cafe"]
                },
                "Heavener Hall": {
                    "location": "Near Century Tower",
                    "description": "Business administration building",
                    "features": ["Study rooms", "Career center", "Trading lab", "Cafe"]
                }
            },
            "dining": {
                "locations": [
                    "Reitz Union",
                    "Marston Library",
                    "Newell Hall",
                    "Broward Dining",
                    "Gator Corner Dining",
                    "Graham Oasis",
                    "Little Hall Express",
                    "Rawlings POD Market",
                    "Norman Cafe"
                ],
                "popular_spots": [
                    "Krishna Lunch on Plaza",
                    "Starbucks at Lib West",
                    "Panda Express",
                    "Au Bon Pain at HSC",
                    "Subway at Reitz",
                    "Chick-fil-A at Broward"
                ],
                "meal_plans": {
                    "types": ["Open Access", "Weekly Access", "Declining Balance"],
                    "features": ["Flex Bucks", "Dining Dollars", "Food points"]
                }
            },
            "transportation": {
                "bus_services": {
                    "campus": ["Later Gator", "Campus Connector", "East-West Circulator"],
                    "city": ["RTS regular routes", "RTS Later Gator"]
                },
                "parking": {
                    "decal_types": ["Red", "Orange", "Blue", "Green", "Park & Ride", "Motorcycle"],
                    "garages": ["Reitz Union", "O'Connell Center", "Medical Plaza", "Shands"]
                },
                "bike_services": ["Bike repair stations", "Covered bike racks", "Gator Gears bike share"]
            },
            "recreation": {
                "southwest_rec": {
                    "location": "Hull Road",
                    "features": ["Weight room", "Indoor track", "Basketball courts", "Climbing wall", "Pool"]
                },
                "student_rec": {
                    "location": "Near Reitz Union",
                    "features": ["Fitness classes", "Racquetball courts", "Indoor courts"]
                },
                "lake_wauburg": {
                    "location": "South of campus",
                    "features": ["Climbing wall", "Boating", "Picnic areas", "Team building course"]
                }
            },
            "academic_info": {
                "colleges": [
                    "Liberal Arts and Sciences",
                    "Engineering",
                    "Business",
                    "Education",
                    "Medicine",
                    "Law",
                    "Agricultural and Life Sciences",
                    "Design, Construction and Planning",
                    "Health and Human Performance",
                    "Journalism and Communications",
                    "Nursing",
                    "Pharmacy",
                    "Public Health and Health Professions",
                    "Veterinary Medicine"
                ],
                "important_offices": {
                    "registrar": "222 Criser Hall",
                    "financial_aid": "S-107 Criser Hall",
                    "bursar": "S-113 Criser Hall",
                    "advising": "Academic Advising Center, The Hub"
                }
            },
            "student_services": {
                "healthcare": {
                    "shands": "Main hospital and emergency care",
                    "student_health": "Infirmary building, primary care",
                    "counseling": "3190 Radio Road, mental health services"
                },
                "technology": {
                    "computer_labs": ["Marston", "Library West", "CSE", "Architecture"],
                    "wifi": ["UF_WiFi", "eduroam"],
                    "printing": ["PrintSmart locations", "WebPrint service"]
                },
                "safety": {
                    "uf_police": "Building 51, Museum Road",
                    "blue_light_phones": "Emergency phones across campus",
                    "gator_safe": "Safety escort service",
                    "snap": "Student Nighttime Auxiliary Patrol"
                }
            },
            "traditions": {
                "events": [
                    "Gator Growl",
                    "Orange and Blue Game",
                    "Homecoming Parade",
                    "Soulfest",
                    "GatorNights"
                ],
                "locations": {
                    "plaza_americas": "Historic gathering space and Krishna lunch",
                    "century_tower": "Carillon concerts",
                    "lake_alice": "Bat watching and nature walks"
                }
            }
        }

        self.SCRAPE_DEPTH = 2
        self.MAX_PAGES = 30
        
        # Model files are in models
        self.MODELS_DIR = "models"
        self.MISTRAL_MODEL = os.path.join(self.MODELS_DIR, "mistral-7b-instruct.Q4_0.gguf")
        self.LLAMA_MODEL = os.path.join(self.MODELS_DIR, "llama-2-7b.Q4_0.gguf")
        
        self.CACHE_FILE = "uf_knowledge.cache"
        
        # Configure logging to be silent by default
        logging.basicConfig(level=logging.ERROR,
                        format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger("UF Assistant")
        self.embedding_cache = {}
        
        # Check for models without downloading
        if check_only:
            models_exist = self.ensure_model_files_present(check_only=True)
            if not models_exist:
                print("Model files not found in AI/models/ directory.")
                return
            else:
                print("All model files are present.")
                return
        else:
            # Just check if models exist without trying to download
            models_exist = self.ensure_model_files_present(check_only=True)
            if not models_exist:
                print("Model files not found in AI/models/ directory. Please ensure they are present.")
                sys.exit(1)
        
        # Add organization data to static knowledge
        self.STATIC_KNOWLEDGE["organizations"] = self.load_organization_data()
        self.initialize_components()
    
    def download_with_smartdl(self, url, dest):
        """Download a file using pySmartDL with optimized settings."""
        try:
            # Removed logging statement
            dl = SmartDL(
                url, 
                dest,
                threads=16,                  
                timeout=20,                  
                connect_timeout=20,          
                fix_urls=True,              
                progress_bar=False,          # Keep this false to avoid printing batches
                multipart_threshold=8 * 1024,
                request_args={               
                    'headers': {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                        'Accept': '*/*',
                        'Accept-Encoding': 'gzip, deflate',
                        'Connection': 'keep-alive'
                    },
                    'verify': False,
                    'allow_redirects': True
                }
            )
            
            dl.start(blocking=True)  # Use blocking mode to avoid progress updates
            
            return dl.isSuccessful()
                
        except Exception as e:
            self.logger.error(f"Download error: {str(e)}")
            return False
    
    def ensure_model_files_present(self, check_only=False):
        """
        Ensure model files are present. 
        
        Args:
            check_only (bool): If True, only check if files exist without downloading.
                           Returns True if files exist, False otherwise.
        
        Returns:
            bool: True if files exist, False if check_only=True and files are missing
        """
        os.makedirs(self.MODELS_DIR, exist_ok=True)
        
        # Check if model files exist
        models_exist = (
            os.path.exists(self.MISTRAL_MODEL) and 
            os.path.exists(self.LLAMA_MODEL)
        )
        
        # If just checking, return the result without downloading
        if check_only:
            return models_exist
        
        # If models don't exist and we're not in check-only mode, we would download them
        # But per your request, we're just checking if they're in the models/ folder
        if not models_exist:
            print(f"Model files not found in {self.MODELS_DIR}. Please ensure they are present.")
            return False
        
        return True
    
    def load_organization_data(self):
        """Load scraped organization data from the results folder"""
        print("Loading organization data...")
        
        org_data = {
            "organizations": [],
            "categories": {},
            "sources": ["https://orgs.studentinvolvement.ufl.edu/organizations"]
        }
        
        # Try to load JSON data first (most complete)
        json_path = os.path.join("results", "uf_organizations.json")
        
        if os.path.exists(json_path):
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    orgs = json.load(f)
                    if isinstance(orgs, list) and len(orgs) > 0:
                        org_data["organizations"] = orgs
                        print(f"Loaded {len(orgs)} organizations from JSON")
                        return org_data
            except Exception as e:
                print(f"Error loading JSON: {str(e)}")
        
        # Try CSV next
        csv_path = os.path.join("results", "uf_organizations.csv")
        if os.path.exists(csv_path):
            try:
                import csv
                orgs = []
                with open(csv_path, 'r', encoding='utf-8', newline='') as f:
                    reader = csv.reader(f)
                    next(reader)  # Skip header
                    for row in reader:
                        if len(row) > 1:
                            orgs.append(row[1])  # Assuming second column is name
                
                if orgs:
                    org_data["organizations"] = orgs
                    print(f"Loaded {len(orgs)} organizations from CSV")
                    return org_data
            except Exception as e:
                print(f"Error loading CSV: {str(e)}")
        
        # Try text file as last resort
        txt_path = os.path.join("results", "uf_organizations.txt")
        if os.path.exists(txt_path):
            try:
                orgs = []
                with open(txt_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        # Extract org name from format like "1. Organization Name"
                        match = re.match(r'^\d+\.\s+(.+)$', line.strip())
                        if match:
                            orgs.append(match.group(1))
                
                if orgs:
                    org_data["organizations"] = orgs
                    print(f"Loaded {len(orgs)} organizations from text file")
                    return org_data
            except Exception as e:
                print(f"Error loading text file: {str(e)}")
        
        # Try loading from HTML as absolute last resort
        html_path = os.path.join("results", "page_source.html")
        if os.path.exists(html_path):
            try:
                from bs4 import BeautifulSoup
                with open(html_path, 'r', encoding='utf-8') as f:
                    html = f.read()
                
                soup = BeautifulSoup(html, 'html.parser')
                orgs = []
                
                # Try to find organization titles
                for selector in ['.box-title a', 'h2.box-title', '.box-body h2', 'h2']:
                    elements = soup.select(selector)
                    if elements:
                        for element in elements:
                            name = element.text.strip()
                            if name:
                                orgs.append(name)
                        break
                
                if orgs:
                    org_data["organizations"] = orgs
                    print(f"Extracted {len(orgs)} organizations from cached HTML")
                    return org_data
            except Exception as e:
                print(f"Error processing HTML: {str(e)}")
        
        print("No organization data found")
        return org_data
    
    def initialize_components(self):
        """Initialize LLM and encoder components with optimized settings."""
        try:
            # Loading message instead of logging
            print("Loading AI models...", end="", flush=True)
            
            # Use a faster, smaller encoder model
            self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
            
            # Load LLM with optimized settings
            self.llm = Llama(
                model_path=self.MISTRAL_MODEL,
                n_ctx=2048,         
                n_threads=8,         # Increased for better performance
                n_gpu_layers=32,     # Maximize GPU usage if available
                temperature=0.1,
                verbose=False
            )
            
            # Cache static knowledge embeddings
            for category, data in self.STATIC_KNOWLEDGE.items():
                text = json.dumps(data)
                self.embedding_cache[f"static_{category}"] = self.encoder.encode([text])[0]
                
            self.knowledge_base = self.load_or_build_knowledge()
            
            print(" Ready!")
                
        except Exception as e:
            print(f"\nError initializing AI components: {str(e)}")
            raise
    
    def load_or_build_knowledge(self):
        """Load cached knowledge or build new knowledge base."""
        if os.path.exists(self.CACHE_FILE):
            try:
                with open(self.CACHE_FILE, 'rb') as f:
                    return pickle.load(f)
            except Exception as e:
                self.logger.error(f"Cache loading failed: {str(e)}")
                os.remove(self.CACHE_FILE)
        
        print("Building knowledge base (this may take a few minutes)...")
        knowledge = []
        visited = set()
        
        # Add static knowledge first.
        for category, data in self.STATIC_KNOWLEDGE.items():
            knowledge.append(json.dumps(data))
        
        # Scrape dynamic content.
        for base_url in self.UF_BASE_URLS:
            queue = deque([(base_url, 0)])
            
            while queue and len(knowledge) < self.MAX_PAGES:
                url, depth = queue.popleft()
                
                if url in visited or depth > self.SCRAPE_DEPTH:
                    continue
                    
                visited.add(url)
                content = self.safe_scrape(url)
                
                if content:
                    knowledge.append(content)
                    
                    if depth < self.SCRAPE_DEPTH:
                        try:
                            response = requests.get(url, timeout=5)
                            soup = BeautifulSoup(response.text, 'html.parser')
                            links = soup.find_all('a', href=True)
                            
                            for link in links:
                                href = link['href']
                                if href.startswith('http') and 'ufl.edu' in href:
                                    queue.append((href, depth + 1))
                        except Exception as e:
                            continue

        try:
            with open(self.CACHE_FILE, 'wb') as f:
                pickle.dump(knowledge, f)
        except Exception as e:
            self.logger.error(f"Cache saving failed: {str(e)}")

        return knowledge
    
    def get_relevant_context(self, query, k=5):
        """Find most relevant context with caching."""
        try:
            # Cache query embedding
            if query not in self.embedding_cache:
                self.embedding_cache[query] = self.encoder.encode([query])[0]
            query_embedding = self.embedding_cache[query]
            
            contexts = []
            
            # First check static knowledge
            for category, data in self.STATIC_KNOWLEDGE.items():
                cache_key = f"static_{category}"
                if cache_key in self.embedding_cache:
                    similarity = np.dot(query_embedding, self.embedding_cache[cache_key])
                    contexts.append((similarity, json.dumps(data)))
            
            # Then check dynamic knowledge
            for text in self.knowledge_base:
                if text not in self.embedding_cache:
                    self.embedding_cache[text] = self.encoder.encode([text])[0]
                similarity = np.dot(query_embedding, self.embedding_cache[text])
                contexts.append((similarity, text))
            
            contexts.sort(reverse=True)
            return "\n".join(text for _, text in contexts[:k])
            
        except Exception as e:
            self.logger.error(f"Context retrieval error: {str(e)}")
            return ""
    
    def safe_scrape(self, url):
        """Enhanced scraping with better content extraction."""
        try:
            time.sleep(0.5)  # Reduced sleep time for faster scraping
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove unwanted elements.
            for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
                element.decompose()
                
            main_content = soup.find('main') or soup.find('article') or soup.find('div', class_=re.compile(r'content|main'))
            
            if main_content:
                text = main_content.get_text(separator=' ', strip=True)
            else:
                text = soup.get_text(separator=' ', strip=True)
            
            # Clean up text.
            text = re.sub(r'\s+', ' ', text)
            text = re.sub(r'[^\w\s.,!?-]', '', text)
            
            # Add metadata but keep it minimal
            text = f"[Source: {url}]\n{text[:3000]}"
            
            return text
            
        except Exception as e:
            return None
    
    def enrich_with_static_knowledge(self, query, context):
        """Add relevant static knowledge to the context based on query keywords."""
        query_lower = query.lower()
        additional_context = []

        # Organization related queries
        if any(word in query_lower for word in ['organization', 'club', 'society', 'group', 'join', 'member', 'student org']):
            orgs = self.STATIC_KNOWLEDGE.get('organizations', {})
            if orgs and orgs.get('organizations'):
                # If the query contains a specific term, try to filter relevant organizations
                specific_terms = [word for word in query_lower.split() if len(word) > 3]
                
                if specific_terms:
                    relevant_orgs = []
                    for org in orgs['organizations']:
                        if any(term in org.lower() for term in specific_terms):
                            relevant_orgs.append(org)
                    
                    if relevant_orgs:
                        org_sample = relevant_orgs[:20]  # Limit to avoid context overflow
                        additional_context.append(f"Relevant Organizations: {org_sample}")
                    else:
                        # If no specific matches, provide a sample
                        org_sample = orgs['organizations'][:20]  # First 20 orgs as a sample
                        additional_context.append(f"Example Organizations: {org_sample}")
                        additional_context.append(f"Total Organizations: {len(orgs['organizations'])}")
                else:
                    # No specific terms, just provide a sample
                    org_sample = orgs['organizations'][:20]  # First 20 orgs as a sample
                    additional_context.append(f"Example Organizations: {org_sample}")
                    additional_context.append(f"Total Organizations: {len(orgs['organizations'])}")

        # Library related queries
        if any(word in query_lower for word in ['library', 'marston', 'lib west', 'study', 'book', 'research']):
            additional_context.append(f"Library Information: {json.dumps(self.STATIC_KNOWLEDGE['libraries'], indent=2)}")

        # Building related queries
        if any(word in query_lower for word in ['building', 'reitz', 'stadium', 'swamp', 'century', 'tower', 'newell', 'norman']):
            additional_context.append(f"Building Information: {json.dumps(self.STATIC_KNOWLEDGE['buildings'], indent=2)}")

        # Food related queries
        if any(word in query_lower for word in ['food', 'eat', 'dining', 'restaurant', 'meal', 'krishna', 'cafe']):
            additional_context.append(f"Dining Information: {json.dumps(self.STATIC_KNOWLEDGE['dining'], indent=2)}")

        # Transportation related queries
        if any(word in query_lower for word in ['bus', 'parking', 'transportation', 'bike', 'decal', 'rts']):
            additional_context.append(f"Transportation Information: {json.dumps(self.STATIC_KNOWLEDGE['transportation'], indent=2)}")

        # Recreation related queries
        if any(word in query_lower for word in ['gym', 'recreation', 'fitness', 'swimming', 'southwest', 'lake wauburg']):
            additional_context.append(f"Recreation Information: {json.dumps(self.STATIC_KNOWLEDGE['recreation'], indent=2)}")

        # Academic related queries
        if any(word in query_lower for word in ['college', 'class', 'major', 'academic', 'registrar', 'advising']):
            additional_context.append(f"Academic Information: {json.dumps(self.STATIC_KNOWLEDGE['academic_info'], indent=2)}")

        # Student services related queries
        if any(word in query_lower for word in ['health', 'counseling', 'computer', 'wifi', 'police', 'safety']):
            additional_context.append(f"Student Services Information: {json.dumps(self.STATIC_KNOWLEDGE['student_services'], indent=2)}")

        # Tradition related queries
        if any(word in query_lower for word in ['tradition', 'gator growl', 'homecoming', 'plaza', 'century tower']):
            additional_context.append(f"Campus Traditions Information: {json.dumps(self.STATIC_KNOWLEDGE['traditions'], indent=2)}")

        if additional_context:
            context = "\n".join(additional_context) + "\n" + context

        return context

    def generate_response(self, query):
        """Generate faster responses with optimized prompt."""
        try:
            context = self.get_relevant_context(query, k=3)  # Reduce from k=5 to k=3
            context = self.enrich_with_static_knowledge(query, context)
            
            # Use a shorter prompt
            prompt = f"""You are a UF assistant. Be concise.

Context: {context[:1500]}  # Limit context length

Question: {query}

Answer:"""
            
            response = self.llm(
                prompt,
                max_tokens=200,    # Reduced from 300
                stop=["Question:", "\n\n"],
                echo=False
            )
            
            return response['choices'][0]['text'].strip()
            
        except Exception as e:
            self.logger.error(f"Response generation error: {str(e)}")
            return "I apologize, but I encountered an error. Please try asking your question again."

    def suggest_related_topics(self, query):
        """Suggest related topics based on the user's query."""
        query_lower = query.lower()
        suggestions = []
        
        # Define topic relationships
        if any(word in query_lower for word in ['library', 'study']):
            suggestions.extend(['computer labs', 'printing services', '24/7 study spaces'])
        elif any(word in query_lower for word in ['food', 'dining']):
            suggestions.extend(['meal plans', 'Krishna lunch', 'campus cafes'])
        elif any(word in query_lower for word in ['bus', 'parking']):
            suggestions.extend(['bike services', 'SNAP service', 'parking decals'])
        elif any(word in query_lower for word in ['recreation', 'gym']):
            suggestions.extend(['Lake Wauburg activities', 'fitness classes', 'intramural sports'])
        elif any(word in query_lower for word in ['class', 'academic']):
            suggestions.extend(['advising services', 'tutoring centers', 'academic support'])
        elif any(word in query_lower for word in ['health', 'medical']):
            suggestions.extend(['counseling services', 'wellness programs', 'student insurance'])
        
        if suggestions:
            print("\nRelated topics you might be interested in:")
            for suggestion in suggestions:
                print(f"- {suggestion}")

    def run(self):
        """Streamlined interactive assistant with no batches printing."""
        print("\n=== UF Campus Assistant ===")
        print("Ask me anything about UF! Type 'quit' to exit.\n")
        
        while True:
            try:
                query = input("> ").strip()
                if not query:
                    continue
                if query.lower() == 'quit':
                    break
                
                # Simple thinking indicator
                print("Thinking...", end="\r", flush=True)
                
                # Generate response and clear the thinking indicator
                response = self.generate_response(query)
                print(" " * 10, end="\r")  # Clear the "Thinking..." text
                print("\n" + response + "\n")
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print("\nAn error occurred. Please try again.\n")
        
        print("Goodbye!")
        self.llm.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='UF Assistant with organization data')
    parser.add_argument('--check-only', action='store_true', 
                        help='Only check if model files exist without downloading')
    parser.add_argument('--preload-only', action='store_true',
                        help='Initialize models but exit without starting interactive mode')
    
    args = parser.parse_args()
    
    try:
        assistant = UFAssistant(check_only=args.check_only)
        
        # If check_only is True, the assistant already reported the status
        if args.check_only:
            sys.exit(0)
            
        # Exit after preloading if requested
        if args.preload_only:
            print("AI models loaded successfully")
            sys.exit(0)
            
        # Otherwise run the assistant
        assistant.run()
    except Exception as e:
        print(f"Failed to start assistant: {str(e)}")
        sys.exit(1)