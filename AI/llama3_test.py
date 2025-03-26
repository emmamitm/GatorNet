import os
import json
import pickle
import numpy as np
import requests
import re
import time
from collections import deque
from bs4 import BeautifulSoup
from llama_cpp import Llama
from sentence_transformers import SentenceTransformer


class LLaMA3Assistant:
    def __init__(self):
        self.MODEL_PATH = r"C:\Users\smhue\OneDrive\Documents\GitHub\GatorNet\AI\models\AI\Meta-Llama-3-8B-Instruct-Q4_K_M.gguf"

        if not os.path.exists(self.MODEL_PATH):
            raise FileNotFoundError(f"Model file not found at {self.MODEL_PATH}. Please download it from Hugging Face and place it in the 'models' folder.")

        self.llm = Llama(
            model_path=self.MODEL_PATH,
            n_ctx=4096,
            n_threads=8,
            n_gpu_layers=32,
            temperature=0.3,
            verbose=False
        )

        self.encoder = SentenceTransformer("all-MiniLM-L6-v2")

        self.BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        self.CACHE_FILE = os.path.join(self.BASE_DIR, "uf_knowledge.cache")
        self.UF_BASE_URLS = [
            'https://campusmap.ufl.edu/',
            'https://housing.ufl.edu/living-options/apply/residence-halls/',
            'https://rec.ufl.edu/facilities/',
            'https://studentlife.ufl.edu/',
            'https://registrar.ufl.edu/',
            'https://www.advising.ufl.edu/',
            'https://welcome.ufl.edu/',
            'https://career.ufl.edu/',
            'https://floridagators.com/',
            'https://news.ufl.edu/'
        ]

        self.SCRAPE_DEPTH = 1
        self.MAX_PAGES = 20

        self.knowledge_base = self.load_or_build_knowledge()

        with open(os.path.join(self.BASE_DIR, "static_knowledge.json"), "r") as f:
            self.STATIC_KNOWLEDGE = json.load(f)

        self.embedding_cache = {}
        self.cache_static_embeddings()

    def cache_static_embeddings(self):
        for category, data in self.STATIC_KNOWLEDGE.items():
            text = json.dumps(data)
            self.embedding_cache[f"static_{category}"] = self.encoder.encode([text])[0]

    def safe_scrape(self, url):
        try:
            time.sleep(0.5)
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')

            for element in soup(['script', 'style', 'nav', 'footer', 'header']):
                element.decompose()

            main_content = soup.find('main') or soup.find('article') or soup.find('div', class_=re.compile(r'content|main'))
            text = main_content.get_text(separator=' ', strip=True) if main_content else soup.get_text(separator=' ', strip=True)
            text = re.sub(r'\s+', ' ', text)
            return f"[Source: {url}]\n{text[:3000]}"
        except Exception:
            return None

    def load_or_build_knowledge(self):
        if os.path.exists(self.CACHE_FILE):
            with open(self.CACHE_FILE, "rb") as f:
                return pickle.load(f)

        knowledge = []
        visited = set()
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
        with open(self.CACHE_FILE, "wb") as f:
            pickle.dump(knowledge, f)
        return knowledge

    def get_relevant_context(self, query, k=4):
        if query not in self.embedding_cache:
            self.embedding_cache[query] = self.encoder.encode([query])[0]
        query_embedding = self.embedding_cache[query]

        contexts = []
        for category, data in self.STATIC_KNOWLEDGE.items():
            key = f"static_{category}"
            similarity = np.dot(query_embedding, self.embedding_cache[key])
            contexts.append((similarity, json.dumps(data)))

        for text in self.knowledge_base:
            if text not in self.embedding_cache:
                self.embedding_cache[text] = self.encoder.encode([text])[0]
            similarity = np.dot(query_embedding, self.embedding_cache[text])
            contexts.append((similarity, text))

        contexts.sort(reverse=True)
        return "\n".join(text for _, text in contexts[:k])

    def generate_response(self, query):
        context = self.get_relevant_context(query)

        prompt = f"""
You are a knowledgeable and helpful assistant for the University of Florida. Answer the following question clearly, accurately, and directly. If the context doesn't help, suggest where the user might look (like the campus map, registrar, or student affairs).

Context:
{context[:1500]}

Question: {query}

Answer:
"""

        result = self.llm(prompt, max_tokens=350, stop=["Question:", "\n\n"], echo=False)
        return result["choices"][0]["text"].strip()


if __name__ == "__main__":
    assistant = LLaMA3Assistant()
    print("\n=== LLaMA 3 UF Assistant ===")
    print("Type a question (or 'quit' to exit):")

    while True:
        try:
            query = input("\n> ").strip()
            if query.lower() == "quit":
                break
            response = assistant.generate_response(query)
            print("\n" + response + "\n")
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"\n[Error] {str(e)}\n")

    print("Goodbye!")
