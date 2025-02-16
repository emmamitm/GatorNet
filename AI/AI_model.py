import requests
from bs4 import BeautifulSoup
from llama_cpp import Llama
import re
import numpy as np
import textwrap
import time
from collections import deque
from sentence_transformers import SentenceTransformer
import logging
import os
import pickle
import json
import zipfile

class UFAssistant:
    def __init__(self):
        # Expanded source URLs for better coverage
        self.UF_BASE_URLS = [
            # Academic Information
            'https://catalog.ufl.edu/UGRD/programs/',
            'https://catalog.ufl.edu/UGRD/colleges-schools/',
            
            # Campus Life & Facilities
            'https://www.uflib.ufl.edu/about-us/',  # Library info
            'https://housing.ufl.edu/living-options/apply/residence-halls/',  # Dorm info
            'https://campusmap.ufl.edu/',  # Campus map
            
            # Student Services
            'https://www.bsd.ufl.edu/g1c/campus_map/Buildings.aspx',  # Building directory
            'https://rec.ufl.edu/facilities/',  # Recreation facilities
            'https://www.dso.ufl.edu/departments',  # Student services
            
            # Current Information
            'https://news.ufl.edu/',
            'https://calendar.ufl.edu/',
            
            # Additional Resources
            'https://www.uflib.ufl.edu/using/hours.html',  # Library hours
            'https://businessservices.ufl.edu/services/gator-dining/locations/',  # Dining locations
            'https://parking.ufl.edu/parking-at-uf/'  # Parking info
        ]
        
        self.STATIC_KNOWLEDGE = {
            "libraries": {
                "Marston Science Library": {
                    "location": "Central campus, near Century Tower",
                    "description": "Science and engineering focused library with study spaces and collaboration rooms",
                    "features": ["24/5 study space", "3D printing", "VR/AR lab", "Computer labs"]
                },
                "Library West": {
                    "location": "Next to Plaza of the Americas",
                    "description": "Humanities and social sciences library with extensive study areas",
                    "features": ["24/5 study space", "Graduate study rooms", "Starbucks"]
                }
            },
            "buildings": {
                "Reitz Union": {
                    "location": "Museum Road",
                    "description": "Student union with dining, study spaces, and meeting rooms",
                    "features": ["Food court", "Game room", "Career center", "Hotel"]
                },
                "Ben Hill Griffin Stadium": {
                    "location": "Central campus",
                    "description": "Home of Gator football, known as 'The Swamp'",
                    "features": ["90,000+ capacity", "Gator sportshop", "Hall of Fame"]
                }
            },
            "dining": {
                "locations": ["Reitz Union", "Marston Library", "Newell Hall", "Broward Dining"],
                "popular_spots": ["Krishna Lunch on Plaza", "Starbucks at Lib West", "Panda Express"]
            }
        }

        self.SCRAPE_DEPTH = 2
        self.MAX_PAGES = 30  # Increased from 20
        
        # Set the expected unzipped model file path.
        # Update these lines in __init__
        self.MODEL_PATH = "AI/models/mistral-7b-instruct.Q4_0.gguf"
        self.ZIPPED_MODEL_PATH = "AI/models/modelfiles.zip" 
        # Set the zipped model file path.
        self.CACHE_FILE = "uf_knowledge.cache"
        
        logging.basicConfig(level=logging.INFO,
                            format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger("UF Assistant")
        
        # Ensure the model is unzipped before initializing components.
        self.ensure_model_unzipped()
        self.initialize_components()

    def ensure_model_unzipped(self):
        """Check if the unzipped model file exists; if not, unzip it from the provided zip file."""
        if not os.path.exists(self.MODEL_PATH):
            self.logger.info("Unzipped model file not found. Unzipping from {}...".format(self.ZIPPED_MODEL_PATH))
            try:
                # Create models directory if it doesn't exist
                os.makedirs(os.path.dirname(self.MODEL_PATH), exist_ok=True)
                
                with zipfile.ZipFile(self.ZIPPED_MODEL_PATH, 'r') as zip_ref:
                    # Extract only the specific model file we need
                    for file in zip_ref.namelist():
                        if file.endswith('mistral-7b-instruct.Q4_0.gguf'):
                            # Read the file from zip
                            data = zip_ref.read(file)
                            # Write to correct location, removing any nested 'models' directory
                            with open(self.MODEL_PATH, 'wb') as f:
                                f.write(data)
                            break
                self.logger.info("Model unzipped successfully.")
            except Exception as e:
                self.logger.error(f"Failed to unzip model: {str(e)}")
                raise
        else:
            self.logger.info("Model file already unzipped.")

    def initialize_components(self):
        """Initialize LLM and encoder components with error handling."""
        try:
            self.logger.info("Initializing encoder...")
            self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
            
            self.logger.info("Initializing LLM...")
            self.llm = Llama(
                model_path=self.MODEL_PATH,
                n_ctx=4096,  # Increased context window
                n_threads=8,  # Increased threads
                n_gpu_layers=32,  # Increased GPU layers
                temperature=0.1,  # Reduced temperature for more focused responses
                verbose=False
            )
            
            self.knowledge_base = self.load_or_build_knowledge()
            
        except Exception as e:
            self.logger.error(f"Initialization error: {str(e)}")
            raise

    def load_or_build_knowledge(self):
        """Load cached knowledge or build new knowledge base."""
        if os.path.exists(self.CACHE_FILE):
            self.logger.info("Loading cached knowledge...")
            try:
                with open(self.CACHE_FILE, 'rb') as f:
                    return pickle.load(f)
            except Exception as e:
                self.logger.error(f"Cache loading failed: {str(e)}")
                os.remove(self.CACHE_FILE)
        
        self.logger.info("Building new knowledge base from sources...")
        knowledge = []
        visited = set()
        
        # Add static knowledge first.
        knowledge.extend([
            json.dumps(self.STATIC_KNOWLEDGE['libraries']),
            json.dumps(self.STATIC_KNOWLEDGE['buildings']),
            json.dumps(self.STATIC_KNOWLEDGE['dining'])
        ])
        
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
                    self.logger.info(f"Added content from: {url[:50]}...")
                    
                    # Extract new links if within depth limit.
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
                            self.logger.warning(f"Link extraction failed for {url}: {str(e)}")
                            continue

        # Cache the knowledge.
        try:
            with open(self.CACHE_FILE, 'wb') as f:
                pickle.dump(knowledge, f)
        except Exception as e:
            self.logger.error(f"Cache saving failed: {str(e)}")

        return knowledge

    def get_relevant_context(self, query, k=5):
        """Find most relevant context for a query."""
        try:
            query_embedding = self.encoder.encode([query])[0]
            contexts = []
            
            for text in self.knowledge_base:
                text_embedding = self.encoder.encode([text])[0]
                similarity = np.dot(query_embedding, text_embedding)
                contexts.append((similarity, text))
            
            contexts.sort(reverse=True)
            relevant_texts = [text for _, text in contexts[:k]]
            
            return "\n".join(relevant_texts)
            
        except Exception as e:
            self.logger.error(f"Context retrieval error: {str(e)}")
            return ""

    def safe_scrape(self, url):
        """Enhanced scraping with better content extraction."""
        try:
            time.sleep(1)
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive'
            }
            
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove unwanted elements.
            for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
                element.decompose()
                
            # Prioritize main content areas.
            main_content = soup.find('main') or soup.find('article') or soup.find('div', class_=re.compile(r'content|main'))
            
            if main_content:
                text = main_content.get_text(separator=' ', strip=True)
            else:
                text = soup.get_text(separator=' ', strip=True)
            
            # Clean up text.
            text = re.sub(r'\s+', ' ', text)
            text = re.sub(r'[^\w\s.,!?-]', '', text)
            
            # Add metadata.
            text = f"[Source: {url}]\n[Last Updated: {time.strftime('%Y-%m-%d')}]\n\n{text[:3000]}"
            
            return text
            
        except Exception as e:
            self.logger.warning(f"Scraping failed for {url}: {str(e)}")
            return None

    def enrich_with_static_knowledge(self, query, context):
        """Add relevant static knowledge to the context."""
        query_lower = query.lower()
        additional_context = []

        # Add library information if relevant.
        if any(word in query_lower for word in ['library', 'marston', 'lib west', 'study']):
            additional_context.append(str(self.STATIC_KNOWLEDGE['libraries']))

        # Add building information if relevant.
        if any(word in query_lower for word in ['building', 'reitz', 'stadium', 'swamp']):
            additional_context.append(str(self.STATIC_KNOWLEDGE['buildings']))

        # Add dining information if relevant.
        if any(word in query_lower for word in ['food', 'eat', 'dining', 'restaurant']):
            additional_context.append(str(self.STATIC_KNOWLEDGE['dining']))

        if additional_context:
            context = "\n".join(additional_context) + "\n" + context

        return context

    def generate_response(self, query):
        """Generate improved responses with static knowledge integration."""
        try:
            context = self.get_relevant_context(query, k=5)  # Increased context retrieval.
            context = self.enrich_with_static_knowledge(query, context)
            
            prompt = f"""You are a knowledgeable assistant for the University of Florida (UF).
Answer the following question using the provided context. Be specific and detailed.
If you're not certain about something, say so, but provide any relevant information you do have.

Context: {context}

Question: {query}

Detailed answer:"""
            
            response = self.llm(
                prompt,
                max_tokens=750,  # Increased token limit.
                stop=["Question:", "\n\n\n"],
                echo=False
            )
            
            return response['choices'][0]['text'].strip()
            
        except Exception as e:
            self.logger.error(f"Response generation error: {str(e)}")
            return "I apologize, but I encountered an error. Please try asking your question again."

    def run(self):
        """Interactive assistant with improved UI."""
        print("\n=== UF Campus Assistant ===")
        print("Ready to answer questions about UF! Try asking about:")
        print("- Campus locations and buildings")
        print("- Libraries and study spaces")
        print("- Dining options and facilities")
        print("- Student services and resources")
        print("\nType 'quit' to exit")
        
        while True:
            try:
                query = input("\nQuestion: ").strip()
                
                if not query:
                    continue
                    
                if query.lower() in ('exit', 'quit'):
                    break
                    
                response = self.generate_response(query)
                print(f"\nAnswer: {textwrap.fill(response, width=80)}")
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                self.logger.error(f"Runtime error: {str(e)}")
                print("\nAn error occurred. Please try again.")
        
        self.llm.close()

if __name__ == "__main__":
    try:
        assistant = UFAssistant()
        assistant.run()
    except Exception as e:
        print(f"Failed to start assistant: {str(e)}")
