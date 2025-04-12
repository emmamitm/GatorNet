#!/usr/bin/env python3
"""
UF Question-Answer Cache

This module provides a cache of challenging UF questions with accurate answers,
along with search functionality to find the closest matching question.

The cache focuses particularly on:
- Correct UF building addresses
- Current events at UF
- Complex academic information
- Administrative details

Usage:
    from uf_qa_cache import UFQuestionCache
    
    # Initialize the cache
    qa_cache = UFQuestionCache()
    
    # Search for a question
    result = qa_cache.find_matching_question("Where is Turlington Hall located?")
    if result:
        question, answer = result
        print(f"Q: {question}")
        print(f"A: {answer}")
"""

import difflib
import re
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path
import json
import os

try:
    from sentence_transformers import SentenceTransformer
    SEMANTIC_SEARCH_AVAILABLE = True
except ImportError:
    SEMANTIC_SEARCH_AVAILABLE = False

class UFQuestionCache:
    """Cache of challenging UF questions with semantic search capability"""
    
    def __init__(self, threshold: float = 0.8, use_semantic: bool = True):
        """
        Initialize the UF Question-Answer Cache
        
        Args:
            threshold: Similarity threshold for matching (0.0 to 1.0)
            use_semantic: Whether to use semantic search when available
        """
        self.threshold = threshold
        self.use_semantic = use_semantic and SEMANTIC_SEARCH_AVAILABLE
        self.encoder = None
        
        # Load the QA data
        self.qa_pairs = self._load_qa_data()
        
        # Initialize semantic search if available and requested
        if self.use_semantic:
            try:
                self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
                # Pre-encode all questions for faster search
                self.encoded_questions = self.encoder.encode([q for q, _ in self.qa_pairs])
                print(f"Initialized semantic search with {len(self.qa_pairs)} questions")
            except Exception as e:
                print(f"Failed to initialize semantic search: {e}")
                self.use_semantic = False
                self.encoder = None
    
    def _load_qa_data(self) -> List[Tuple[str, str]]:
        """
        Load question-answer pairs from the embedded data in this file
        
        Returns:
            List of (question, answer) tuples
        """
        # The data is embedded in this file as a list of dictionaries
        qa_data = UF_QA_DATA
        
        # Convert to list of tuples
        return [(item["question"], item["answer"]) for item in qa_data]
    
    def find_matching_question(self, query: str, return_score: bool = False) -> Optional[Tuple]:
        """
        Find the best matching question for a given query
        
        Args:
            query: The user's question
            return_score: Whether to return the similarity score
            
        Returns:
            If return_score is False: (question, answer) tuple or None if no match
            If return_score is True: (question, answer, score) tuple or None if no match
        """
        if not query or not self.qa_pairs:
            return None
        
        # Normalize the query
        query = self._normalize_query(query)
        
        # Try semantic search first if available
        if self.use_semantic and self.encoder:
            try:
                # Encode the query
                query_embedding = self.encoder.encode(query)
                
                # Calculate cosine similarity with all questions
                from sklearn.metrics.pairwise import cosine_similarity
                import numpy as np
                
                # Reshape for sklearn
                query_embedding = query_embedding.reshape(1, -1)
                similarities = cosine_similarity(query_embedding, self.encoded_questions)[0]
                
                # Find the best match
                best_idx = np.argmax(similarities)
                best_score = similarities[best_idx]
                
                if best_score >= self.threshold:
                    if return_score:
                        return self.qa_pairs[best_idx] + (best_score,)
                    return self.qa_pairs[best_idx]
                    
            except Exception as e:
                print(f"Semantic search failed: {e}")
        
        # Fall back to string matching
        return self._string_match(query, return_score)
    
    def _string_match(self, query: str, return_score: bool) -> Optional[Tuple]:
        """Fallback string matching method"""
        best_match = None
        best_score = 0
        
        for question, answer in self.qa_pairs:
            # Normalize the question for comparison
            norm_question = self._normalize_query(question)
            
            # Try exact substring match first
            if query in norm_question or norm_question in query:
                score = 0.9  # High score but not perfect
                if score > best_score:
                    best_score = score
                    best_match = (question, answer)
            
            # Try fuzzy matching 
            score = difflib.SequenceMatcher(None, query, norm_question).ratio()
            if score > best_score:
                best_score = score
                best_match = (question, answer)
        
        # Check against threshold
        if best_score >= self.threshold:
            if return_score:
                return best_match + (best_score,)
            return best_match
            
        return None
    
    def _normalize_query(self, query: str) -> str:
        """Normalize a query for better matching"""
        # Convert to lowercase
        query = query.lower()
        
        # Remove punctuation
        query = re.sub(r'[^\w\s]', '', query)
        
        # Standardize whitespace
        query = ' '.join(query.split())
        
        return query
    
    def add_qa_pair(self, question: str, answer: str) -> None:
        """
        Add a new question-answer pair to the cache
        
        Args:
            question: The question
            answer: The answer
        """
        self.qa_pairs.append((question, answer))
        
        # Update encoded questions if using semantic search
        if self.use_semantic and self.encoder:
            import numpy as np
            # Encode the new question
            new_encoding = self.encoder.encode([question])[0]
            # Append to existing encodings
            if hasattr(self, 'encoded_questions'):
                self.encoded_questions = np.vstack([self.encoded_questions, new_encoding.reshape(1, -1)])
            else:
                self.encoded_questions = new_encoding.reshape(1, -1)
    
    def save_to_file(self, filepath: str) -> None:
        """
        Save the current QA pairs to a JSON file
        
        Args:
            filepath: Path to save the JSON file
        """
        data = [{"question": q, "answer": a} for q, a in self.qa_pairs]
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
            
    def load_from_file(self, filepath: str) -> None:
        """
        Load QA pairs from a JSON file
        
        Args:
            filepath: Path to the JSON file
        """
        if not os.path.exists(filepath):
            print(f"File not found: {filepath}")
            return
            
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            self.qa_pairs = [(item["question"], item["answer"]) for item in data]
            
            # Re-initialize semantic search if available
            if self.use_semantic and self.encoder:
                self.encoded_questions = self.encoder.encode([q for q, _ in self.qa_pairs])
                
            print(f"Loaded {len(self.qa_pairs)} QA pairs from {filepath}")
        except Exception as e:
            print(f"Error loading from file: {e}")


# --- UF Question-Answer Dataset ---
UF_QA_DATA = [
    # Building Addresses - Precise and Accurate
    {
        "question": "What is the exact address of Turlington Hall?",
        "answer": "Turlington Hall is located at 330 Newell Dr, Gainesville, FL 32611. It's situated in the central campus area, adjacent to the Plaza of the Americas."
    },
    {
        "question": "Where is the Reitz Union located?",
        "answer": "The J. Wayne Reitz Union is located at 655 Reitz Union Drive, Gainesville, FL 32611. It's on Museum Road, near the intersection with Reitz Union Drive."
    },
    {
        "question": "What's the address of Library West?",
        "answer": "Library West is located at 1545 W University Ave, Gainesville, FL 32611. It's positioned at the northwest corner of Plaza of the Americas, facing University Avenue."
    },
    {
        "question": "Where is Marston Science Library?",
        "answer": "Marston Science Library is located at 444 Newell Dr, Gainesville, FL 32611. It sits at the intersection of Newell Drive and Union Road, near the Century Tower."
    },
    {
        "question": "What's the exact address of Ben Hill Griffin Stadium?",
        "answer": "Ben Hill Griffin Stadium (also known as 'The Swamp') is located at 157 Gale Lemerand Dr, Gainesville, FL 32611, on the University of Florida campus."
    },
    {
        "question": "Where is the UF Health Shands Hospital located?",
        "answer": "UF Health Shands Hospital's main campus is located at 1600 SW Archer Rd, Gainesville, FL 32610, adjacent to the UF College of Medicine."
    },
    {
        "question": "What is the address of Norman Hall?",
        "answer": "Norman Hall is located at 1221 SW 5th Ave, Gainesville, FL 32601. It's home to the College of Education and is located on the southeastern edge of campus."
    },
    {
        "question": "Where exactly is Tigert Hall?",
        "answer": "Tigert Hall is located at 300 SW 13th St, Gainesville, FL 32611. It houses the university's main administration offices and is positioned at the eastern entrance to campus near University Avenue."
    },
    {
        "question": "What's the address of the UF O'Connell Center?",
        "answer": "The Stephen C. O'Connell Center (commonly called the O'Dome) is located at 250 Gale Lemerand Dr, Gainesville, FL 32611, adjacent to the University of Florida campus."
    },
    {
        "question": "Where is Weimer Hall located?",
        "answer": "Weimer Hall, home to the College of Journalism and Communications, is located at 1885 Stadium Rd, Gainesville, FL 32611, near the north end of campus."
    },
    {
        "question": "What is the address of Heavener Hall?",
        "answer": "Heavener Hall is located at 1325 W University Ave, Gainesville, FL 32611. It houses the Heavener School of Business and is positioned on the north side of campus near University Avenue."
    },
    {
        "question": "Where is Hume Hall on campus?",
        "answer": "Hume Hall is located at 500 Hume Ln, Gainesville, FL 32612. It's an honors residential complex on the northern area of campus, near Museum Road."
    },
    {
        "question": "What's the address of the UF Health Science Center?",
        "answer": "The UF Health Science Center is located at 1600 SW Archer Road, Gainesville, FL, 32610. It comprises six colleges and is adjacent to Shands Hospital."
    },
    {
        "question": "Where is Little Hall located?",
        "answer": "Little Hall is located at 300 Buckman Dr, Gainesville, FL 32611. It houses mathematics and other departments and is in the central campus area near Turlington Hall."
    },
    {
        "question": "What is the exact address of the Florida Museum of Natural History?",
        "answer": "The Florida Museum of Natural History is located at 3215 Hull Rd, Gainesville, FL 32611, in the UF Cultural Plaza area on the western side of campus."
    },
    
    # Current Events & Important Dates (Spring 2025)
    {
        "question": "When does Spring 2025 semester start at UF?",
        "answer": "The Spring 2025 semester at UF begins on Monday, January 6, 2025. Classes start on this date, and the semester runs through May 2, 2025."
    },
    {
        "question": "When is Spring Break 2025 at UF?",
        "answer": "Spring Break 2025 at the University of Florida is scheduled for March 8-15, 2025. No classes will be held during this period."
    },
    {
        "question": "When do Spring 2025 final exams take place?",
        "answer": "Spring 2025 final exams at UF are scheduled for April 26 through May 2, 2025. The official examination schedule with specific times for different classes is published by the Registrar's Office."
    },
    {
        "question": "What date is UF's Spring 2025 commencement?",
        "answer": "The University of Florida's Spring 2025 Commencement ceremonies are scheduled for May 3-5, 2025. Different colleges have ceremonies at various times throughout these dates."
    },
    {
        "question": "When is the drop/add period for Spring 2025?",
        "answer": "The drop/add period for Spring 2025 at UF runs from January 6-10, 2025. During this time, students can adjust their schedules without academic penalty."
    },
    {
        "question": "What's the withdrawal deadline for Spring 2025?",
        "answer": "The withdrawal deadline for Spring 2025 at UF is March 7, 2025. This is the last day to withdraw from a course without receiving a failing grade."
    },
    {
        "question": "When does Summer A 2025 begin at UF?",
        "answer": "Summer A 2025 at the University of Florida begins on May 12, 2025, and runs through June 20, 2025."
    },
    {
        "question": "When is the last day of classes for Spring 2025?",
        "answer": "The last day of regular classes for Spring 2025 at UF is April 23, 2025. Reading days follow before final examinations begin."
    },
    {
        "question": "What are the Library West hours during finals week Spring 2025?",
        "answer": "During Spring 2025 finals week (April 19-May 2), Library West operates 24 hours a day to accommodate student study needs. Regular hours resume after finals."
    },
    {
        "question": "When is the Summer 2025 registration period at UF?",
        "answer": "Registration for Summer 2025 terms at UF begins in March 2025, with specific registration appointment times assigned based on student classification and credit hours."
    },
    
    # Specific, Detailed Academic Information
    {
        "question": "What are the prerequisites for COP 3502 Programming Fundamentals 2?",
        "answer": "The prerequisites for COP 3502 (Programming Fundamentals 2) are COP 3503 (Programming Fundamentals 1) with a minimum grade of C, and MAC 1147 (Precalculus Algebra and Trigonometry) or higher. The course is typically taken by Computer Science majors in their second semester."
    },
    {
        "question": "How many credits is MAC 2311 Calculus 1?",
        "answer": "MAC 2311 (Calculus 1) is a 4-credit course at the University of Florida. It covers limits, continuity, derivatives, applications of derivatives, definite and indefinite integrals, and the Fundamental Theorem of Calculus."
    },
    {
        "question": "What GPA is required for admission to the UF College of Nursing BSN program?",
        "answer": "The UF College of Nursing BSN program typically requires a minimum overall GPA of 3.0 for consideration, with a minimum prerequisite GPA of 3.0 as well. However, due to competitive admissions, successful applicants usually have GPAs well above these minimums, often 3.6 or higher."
    },
    {
        "question": "How many credits are required to graduate with a Business Administration major at UF?",
        "answer": "To graduate with a Business Administration major from UF's Warrington College of Business, students must complete 120 total credits. This includes general education requirements, pre-professional requirements, and 22 credits of business core courses, plus electives and major-specific requirements."
    },
    {
        "question": "What are the admission requirements for UF's Computer Science program?",
        "answer": "Admission to UF's Computer Science program requires completion of prerequisite courses including Calculus 1 & 2, Physics with lab, Programming Fundamentals 1 & 2, and the critical tracking courses with a minimum 2.5 GPA in these courses. Competitive applicants typically have GPAs of 3.0 or higher in critical tracking courses."
    },
    {
        "question": "What concentration options are available in the Biology major at UF?",
        "answer": "The Biology major at UF offers several specialization tracks: Integrative Biology, Preprofessional Biology, Biochemistry and Molecular Biology, Botanical Research, Zoological Research, and Biology Secondary Education. Each track has specific requirements tailored to different career paths."
    },
    {
        "question": "How do I apply for the University Scholars Program at UF?",
        "answer": "To apply for the University Scholars Program at UF, current sophomores and juniors must submit an application in January/February that includes a research proposal, letter of support from a faculty mentor, transcript, and personal statement. Selected scholars receive a $1,750 stipend to conduct research with faculty mentors."
    },
    {
        "question": "What scholarships are available for incoming UF freshmen?",
        "answer": "Incoming UF freshmen may be eligible for several scholarships, including the Presidential Scholarship ($5,000-$8,000/year), Gold Scholarship ($2,000-$4,000/year), Gator Nation Scholarship (varies), Florida Bright Futures (100% or 75% of tuition for FL residents), and numerous departmental scholarships. Applications are typically considered through the regular admissions process."
    },
    {
        "question": "What is the average class size at UF?",
        "answer": "The average class size at UF varies by level. Lower-division undergraduate courses typically have 30-50 students, upper-division courses average 25-35 students, and graduate-level courses generally have 10-25 students. Some introductory courses are taught in large lecture halls with up to 300 students, while advanced seminars may have fewer than 10 students."
    },
    {
        "question": "What is UF's current ranking among public universities?",
        "answer": "As of the most recent U.S. News & World Report rankings, the University of Florida is ranked among the top 5 public universities in the United States, reflecting its excellence in academics, research, and student outcomes."
    },
    
    # Campus Resources and Services
    {
        "question": "What mental health services are available at UF?",
        "answer": "UF provides comprehensive mental health services through the Counseling and Wellness Center (CWC), which offers individual counseling, group therapy, crisis intervention, psychiatric services, and wellness coaching. Students can access these services at 3190 Radio Road or call the 24/7 crisis line at (352) 392-1575. Additional resources include the Disability Resource Center and U Matter, We Care program."
    },
    {
        "question": "What dining options are available in the Reitz Union?",
        "answer": "The Reitz Union features multiple dining options including Starbucks, Subway, Panda Express, Pollo Tropical, Wing Zone, and Croutons. The facility also houses a food court with several local and national vendors. Most locations accept Gator Dining dollars, meal plans, and standard payment methods."
    },
    {
        "question": "How does the UF Campus Shuttle system work?",
        "answer": "The UF Campus Shuttle system (including Later Gator and Campus Connector routes) operates on weekdays from approximately 7:00 AM to 6:00 PM during fall and spring semesters, with reduced service during summer and breaks. Students can track shuttles in real-time using the GATOR LOCATOR app. All routes are free for UF students, faculty, and staff with a valid Gator 1 ID card."
    },
    {
        "question": "What recreation facilities does UF offer?",
        "answer": "UF offers extensive recreation facilities including the Southwest Recreation Center (featuring weight rooms, basketball courts, swimming pools, and fitness classes), Student Recreation & Fitness Center, Lake Wauburg recreational area (with boating and climbing wall), Broward Outdoor Recreation Complex, and numerous outdoor fields and courts across campus. Access is free to students with a valid Gator 1 card."
    },
    {
        "question": "How do I access tutoring services at UF?",
        "answer": "UF offers tutoring through multiple services: The Teaching Center provides free tutoring for math, science, and many other subjects in Broward Hall; Departmental tutoring is available for specific courses; the Writing Studio offers help with papers and written assignments; and SNAP (Student Nighttime Auxiliary Patrol) tutoring provides evening help. Students can schedule appointments online through the respective service websites."
    },
    {
        "question": "What IT help is available for UF students?",
        "answer": "UF students can access IT support through the UF Computing Help Desk, which provides assistance with GatorLink accounts, email, software, campus WiFi, and computer security. Services are available via phone at (352) 392-HELP, email (helpdesk@ufl.edu), or in person at the Hub. Additionally, free software, including Microsoft Office and antivirus protection, is available through the UF Software Licensing Services."
    },
    {
        "question": "How does parking work at UF?",
        "answer": "UF parking requires a permit for all vehicles on weekdays from 7:30 AM to 4:30 PM. Students living on campus can purchase a RED or BROWN decal, while commuter students typically get PARK & RIDE or GREEN decals. Faculty and staff use ORANGE, BLUE, or OFFICIAL decals. Prices range from $85 to $468 annually based on type. Visitors can use hourly pay stations or get temporary permits. All parking information is managed by UF Transportation and Parking Services."
    },
    {
        "question": "What career services does UF provide?",
        "answer": "UF's Career Connections Center offers comprehensive career services including one-on-one career counseling, resume and interview preparation, career fairs (both in-person and virtual), job and internship postings through Gator CareerLink, career workshops, and industry-specific networking events. The center is located on the first floor of the Reitz Union and also provides major-specific career development programs."
    },
    {
        "question": "How do I reserve a study room in Library West?",
        "answer": "To reserve a study room in Library West, go to the UF Libraries website (library.ufl.edu) and click on 'Study Rooms' under Quick Links. Select Library West from the dropdown menu, choose an available time slot (maximum 2 hours per day), and complete the reservation with your Gator 1 credentials. Rooms can be reserved up to 7 days in advance and require a minimum of 2 students for group study rooms."
    },
    {
        "question": "What research facilities are available to undergraduate students at UF?",
        "answer": "UF undergraduates have access to numerous research facilities including the Nanoscale Research Facility, Whitney Laboratory for Marine Bioscience, Center for Undergraduate Research, various college-specific labs, and specialized collections in the libraries. Students can get involved through the Center for Undergraduate Research, the University Scholars Program, or by directly contacting faculty members in their areas of interest."
    },
    
    # Student Life and Campus Culture
    {
        "question": "What is Gator Growl?",
        "answer": "Gator Growl is the University of Florida's annual homecoming pep rally and the largest student-run pep rally in the nation. Typically held the Friday night of homecoming week at Ben Hill Griffin Stadium, it features performances by comedians, musicians, student organizations, and the UF spirit teams. The tradition dates back to 1924 and regularly draws crowds of tens of thousands."
    },
    {
        "question": "How does the Student Government at UF work?",
        "answer": "UF Student Government operates with three branches: Executive (President, Vice President, Treasurer, and cabinet), Legislative (Student Senate with 100 elected senators representing various constituencies), and Judicial (Supreme Court and lower courts). SG controls an annual budget of approximately $23 million from Activity & Service Fees, funding student organizations, recreational facilities, and campus events. Elections are held each fall and spring semester."
    },
    {
        "question": "What Greek organizations are at UF?",
        "answer": "UF has a robust Greek life with 26 fraternities in the Interfraternity Council (IFC), 18 sororities in the Panhellenic Council (PC), 9 organizations in the National Pan-Hellenic Council (NPHC) representing historically African American fraternities and sororities, and 13 groups in the Multicultural Greek Council (MGC). Approximately 15% of UF undergraduates participate in Greek life, which maintains a significant presence on campus."
    },
    {
        "question": "What are the traditions before a UF football game?",
        "answer": "UF football traditions include the Gator Walk (team walking through fans 2 hours before kickoff), Mr. Two Bits cheer, singing 'We Are the Boys' between the 3rd and 4th quarters while swaying and linking arms, the playing of 'Won't Back Down' by Tom Petty after 'We Are the Boys,' and the famous Gator Chomp hand gesture. Many fans also participate in tailgating across campus starting early on game days."
    },
    {
        "question": "What clubs have the most members at UF?",
        "answer": "UF's largest student organizations include Gator Growl (the homecoming organization), Dance Marathon (raising funds for UF Health Shands Children's Hospital), Student Government, the Florida Blue Key leadership honorary, Recreational Sports clubs, the Reitz Union Board of Managers, and the various cultural student unions. UF has over 1,000 registered student organizations spanning academic, cultural, recreational, and special interest groups."
    },
    {
        "question": "What is Dance Marathon at UF?",
        "answer": "Dance Marathon at UF is the largest student-run philanthropy in the southeastern United States. It's a 26.2-hour event where participants stay awake and on their feet to raise money for UF Health Shands Children's Hospital through the Children's Miracle Network. The event typically raises over $2 million annually and involves thousands of student participants and hundreds of student organizers."
    },
    {
        "question": "What intramural sports are offered at UF?",
        "answer": "UF offers a comprehensive intramural sports program including flag football, soccer, basketball, volleyball, softball, ultimate frisbee, racquetball, tennis, badminton, bowling, pickleball, dodgeball, sand volleyball, and innertube water polo. Leagues are available for men's, women's, and co-rec teams at competitive, intermediate, and recreational levels. Registration typically opens at the beginning of each semester through the RecSports website."
    },
    {
        "question": "Where are the best study spots on UF campus?",
        "answer": "Popular study spots at UF include the silent 5th and 6th floors of Library West, Marston Science Library's individual study carrels, the Starbucks in the Reitz Union, Norman Hall courtyard for outdoor studying, Health Science Center Library for medical students, Newell Hall (a 24-hour study space with flexible furniture), the Honors Lounge for honors students, the Heavener Hall study rooms for business students, and various college-specific spaces throughout campus."
    },
    {
        "question": "What volunteer opportunities are available at UF?",
        "answer": "UF offers numerous volunteer opportunities through the Center for Leadership and Service, including Gator Volunteer Center, Florida Alternative Breaks (service trips during breaks), GatorServe days, and Dance Marathon. Additionally, students can volunteer with UF Health Shands Hospital, the Field and Fork Pantry, Habitat for Humanity, GRACE Marketplace, Keep Alachua County Beautiful, and hundreds of community organizations through GatorConnect."
    },
    {
        "question": "How does on-campus housing selection work at UF?",
        "answer": "On-campus housing selection at UF begins with an application period (typically opening in November for the following academic year). Students receive a lottery number based on their application date and class standing. During selection periods in February/March, students can choose available rooms online during their assigned time slot. Incoming freshmen are generally guaranteed housing but must apply by the priority deadline (usually March 15). Housing fees range from approximately $2,800-$4,200 per semester depending on the facility."
    },
    
    # Housing and Residence Halls
    {
        "question": "Which UF dorms are reserved for freshmen?",
        "answer": "The primary UF residence halls reserved predominantly for freshmen include Broward Hall, Jennings Hall, Rawlings Hall, Simpson Hall, Yulee Hall, Mallory Hall, Reid Hall, and Infinity Hall. These buildings offer traditional corridor-style or suite-style accommodations designed to help first-year students transition to college life and build community."
    },
    {
        "question": "What's the difference between Broward Hall and Jennings Hall?",
        "answer": "Broward Hall and Jennings Hall are both traditional-style freshman residence halls on the east side of campus, but they differ in several ways. Broward is larger (900+ residents vs. 500+), features community bathrooms shared by the floor, and houses the 24/7 Broward Teaching Center. Jennings has suite-style bathrooms shared by 2-3 rooms, was renovated more recently (2015), and tends to be slightly quieter. Both offer double-occupancy rooms and are in close proximity to dining options, Turlington Plaza, and the Reitz Union."
    },
    {
        "question": "What amenities are included in UF Springs Complex?",
        "answer": "The Springs Complex at UF includes North, South, and East Halls featuring suite-style accommodations with shared semi-private bathrooms. Amenities include air conditioning, all utilities, cable TV and internet access, communal kitchens, lounges, laundry facilities, and the POD Market convenience store. Each suite includes beds, desks, chairs, dressers, and closets/wardrobes. The complex is popular with upper-division and transfer students due to its central campus location."
    },
    {
        "question": "What's the layout of apartments in UF's Keys Complex?",
        "answer": "UF's Keys Complex offers apartment-style living with 1-bedroom and 2-bedroom floor plans. Each apartment includes a full kitchen (refrigerator, stove, and oven), living room, bathroom(s), and private bedroom(s). The 1-bedroom layouts house two students who share the bedroom, while 2-bedroom apartments house four students (two per room). The complex includes study lounges, laundry facilities, and a convenience store. Keys is primarily occupied by upper-division and transfer students."
    },
    {
        "question": "What meal plans are available for on-campus residents at UF?",
        "answer": "UF on-campus residents can choose from several meal plans: The Open Access Plan (unlimited dining hall access plus Flex Bucks), the 7-Day All Access (unlimited access any day), the Weekly 15 (15 meals per week plus Flex Bucks), the Weekly 10 (10 meals per week plus more Flex Bucks), and declining balance plans. First-year students living in traditional-style halls are required to purchase either the Open Access or 7-Day All Access plan. Pricing ranges from approximately $2,000-$2,400 per semester."
    },
    {
        "question": "What is the Honors Residential College at Hume Hall?",
        "answer": "The Honors Residential College at Hume Hall is a living-learning community designed specifically for students in the UF Honors Program. The facility features suite-style rooms with semi-private bathrooms, study lounges on each floor, smart classrooms where honors courses are taught, and programming specifically for honors students. Both Hume East and Hume West buildings house approximately 600 students, predominantly first-year honors students, though some spaces are reserved for returning honors residents."
    },
    {
        "question": "What are the benefits of living in Infinity Hall?",
        "answer": "Infinity Hall is UF's entrepreneurship-themed residence hall offering unique features for innovation-minded students. Benefits include a built-in makerspace with 3D printers and design tools, collaboration rooms with advanced technology, integrated classrooms, a student-run cafe, mentoring from business faculty, and proximity to Innovation Square. The modern facility offers suite-style accommodations with private and shared bedroom options, and programming focuses on entrepreneurship, creativity, and business development."
    },
    {
        "question": "How does the RA selection process work at UF?",
        "answer": "The Resident Assistant (RA) selection process at UF begins with an online application (typically due in November/December), followed by group interviews in January assessing teamwork and problem-solving skills. Successful candidates advance to individual interviews with housing staff. Selected applicants receive offers in February for the following academic year. RAs receive compensation including a single room, meal plan, and bi-weekly stipend (valued at approximately $13,000 annually). Requirements include a 2.75 minimum GPA, previous on-campus living experience, and good judicial standing."
    },
    {
        "question": "What's the difference between traditional, suite, and apartment-style dorms at UF?",
        "answer": "At UF, traditional-style residence halls (like Broward and Simpson) feature double rooms along corridors with community bathrooms shared by the floor, fostering community but offering less privacy. Suite-style halls (like Springs Complex and Hume) have 2-4 rooms sharing a bathroom within a suite, providing more privacy while maintaining community. Apartment-style accommodations (like Keys Complex and Lakeside) include full kitchens, living rooms, and bathrooms within self-contained units, offering the most independence but typically at higher cost and with less built-in community interaction."
    },
    {
        "question": "When does housing selection begin for Fall 2025?",
        "answer": "Housing selection for UF's Fall 2025 term begins with the application opening in November 2024. Returning student selection occurs in February/March 2025 based on lottery numbers assigned by class standing and application date. New student selection follows in April 2025 for those who applied by the March 15, 2025 priority deadline. All selection is conducted online through the Housing Portal, with specific time slots assigned to students for choosing available spaces."
    },
    
    # Library System and Research Questions
    {
        "question": "How many libraries are there at UF and what are they?",
        "answer": "UF has 9 main libraries: Library West (humanities, social sciences, business), Marston Science Library (sciences, engineering), Smathers Library (special and area studies collections), Health Science Center Library (medical and health sciences), Education Library (education resources), Architecture & Fine Arts Library, Legal Information Center (law), Music Library, and the Panama Canal Museum Collection. These libraries collectively hold over 6 million print volumes and provide access to extensive digital resources."
    },
    {
        "question": "What special collections does UF's George A. Smathers Libraries have?",
        "answer": "UF's Smathers Libraries house several notable special collections including the P.K. Yonge Library of Florida History (largest collection of Florida materials outside the State Archives), the Latin American and Caribbean Collection (one of the most comprehensive in the U.S.), the Baldwin Library of Historical Children's Literature (over 130,000 volumes from the 1600s to present), the Isser and Rae Price Library of Judaica, the Belknap Collection for the Performing Arts, and the University Archives documenting UF's institutional history."
    },
    {
        "question": "What digital collections and databases does UF Library provide access to?",
        "answer": "UF Libraries provide access to over 1,000 databases including JSTOR, Web of Science, Academic Search Premier, SciFinder, IEEE Xplore, and LexisNexis. Additionally, the libraries maintain the Digital Collections of UF (featuring over 15 million digitized pages), the UF Digital Collections (UFDC) repository, and the Digital Library of the Caribbean (dLOC). Students and faculty can access these resources on campus or remotely using their GatorLink credentials through the libraries' website."
    },
    {
        "question": "What is Library West's quiet floor policy?",
        "answer": "Library West designates the 5th and 6th floors as silent floors where no talking or noise is permitted. The 4th floor is a quiet floor where minimal whispered conversation is allowed. The 1st through 3rd floors allow normal conversation levels and group work. During finals periods (the last two weeks of each semester), enhanced quiet hours are implemented with the 3rd floor also becoming a quiet study area. Violations of noise policies can be reported to library staff for enforcement."
    },
    {
        "question": "What resources does the UF Science Library offer for STEM students?",
        "answer": "The Marston Science Library offers specialized resources for STEM students including STEM research databases, a visualization lab with high-performance workstations, 3D printing services, specialty software (MATLAB, SolidWorks, AutoCAD, ArcGIS), equipment lending (calculators, laptops, tablets), subject specialist librarians for all STEM fields, the MADE@UF 3D printing lab, and dedicated group study rooms with whiteboards and displays for collaborative work. The building also features the Collaboration Commons with flexible study spaces."
    },
    {
        "question": "What thesis and dissertation resources does UF provide?",
        "answer": "UF provides comprehensive support for theses and dissertations including the Application Support Center (free formatting assistance), reference management software (EndNote, Zotero, Mendeley), Graduate Editorial Office resources, the Institutional Repository where all ETDs are published, statistics consulting through the Research Computing group, software training through the UF Libraries, Graduate School templates for proper formatting, intellectual property guidance through the Office of Technology Licensing, and regular workshops on academic publishing."
    },
    {
        "question": "How do I access article databases off-campus?",
        "answer": "To access UF library databases and electronic resources off-campus: 1) Begin at the UF Libraries website (library.ufl.edu), 2) Click on the database or resource you need, 3) When prompted, enter your GatorLink username and password, 4) You'll be authenticated through the UF VPN service automatically. For persistent access, you can also install the UF VPN client (Cisco AnyConnect) from vpn.ufl.edu, which provides a more stable connection for downloading multiple resources."
    },
    {
        "question": "What is the Course Reserves system at UF Libraries?",
        "answer": "UF Libraries' Course Reserves system provides access to materials required for specific courses. Physical reserves are kept at circulation desks with checkout periods typically ranging from 2 hours to 3 days, depending on demand. Electronic reserves are accessible 24/7 through the library website or Canvas integration. Students can search for reserves by course number, instructor name, or department. Faculty can place materials on reserve by submitting requests through the library website, typically at least two weeks before the semester begins."
    },
    {
        "question": "What interlibrary loan services does UF offer?",
        "answer": "UF offers comprehensive interlibrary loan services through UBorrow (direct borrowing from other Florida state universities with 7-10 day delivery) and traditional ILL (worldwide borrowing with 1-3 week delivery). Articles are typically delivered electronically within 24-72 hours through the ILLiad system. These services are free for UF students, faculty and staff, accessible through the library website with GatorLink credentials. There are no limits on article requests, while book loans are typically 4-8 weeks depending on the lending library's policies."
    },
    {
        "question": "What research support services do UF librarians provide?",
        "answer": "UF librarians provide extensive research support including one-on-one research consultations (in-person or virtual), subject-specific database navigation assistance, literature review guidance, citation management software training (EndNote, Zotero), systematic review support, data management planning, scholarly communication and publishing advice, copyright guidance, and customized instruction sessions for courses. Each academic department has an assigned subject specialist librarian who provides specialized expertise. Appointments can be scheduled through the library website or via direct email to the subject librarian."
    },
    
    # Technology Services and Resources
    {
        "question": "What software is available free to UF students?",
        "answer": "UF students have free access to Microsoft Office 365 (Word, Excel, PowerPoint, etc.), Adobe Creative Cloud suite, MATLAB, SPSS, SAS, NVivo, ArcGIS, Qualtrics survey software, Zoom Pro, GitLab, GitHub Enterprise, VMware, Mathematica, SolidWorks, LabVIEW, and many specialty software programs. These can be accessed through the UF Apps virtual environment (apps.ufl.edu) or downloaded via the UF Software Licensing Services website (software.ufl.edu) using GatorLink credentials."
    },
    {
        "question": "How powerful are the HiPerGator computers at UF?",
        "answer": "UF's HiPerGator is one of the most powerful academic supercomputers in the United States. The current iteration, HiPerGator 3.0 with AI, features over 40,000 AMD EPYC processor cores, 1,500 NVIDIA A100 GPUs delivering 17.2 petaflops of computing power, 150 petabytes of storage, and 4 petabytes of high-performance storage. The system is specifically optimized for artificial intelligence research, supporting UF's AI initiative, and is available to faculty, staff, and student researchers across all disciplines."
    },
    {
        "question": "How do I connect to eduroam WiFi at UF?",
        "answer": "To connect to UF's eduroam WiFi: Select 'eduroam' from available networks, enter your username as your full UF email address (GatorLink@ufl.edu), and your GatorLink password. For secure setup, visit wifi.ufl.edu/eduroam on a computer connected to the internet and download the appropriate configuration tool for your device. Eduroam provides secure access not only at UF but also at thousands of participating institutions worldwide. For connection issues, contact the UF Computing Help Desk at 352-392-HELP."
    },
    {
        "question": "What computer labs are available on campus?",
        "answer": "UF maintains several computer labs across campus: Marston Science Library (over 100 Windows and Mac computers, specialized software); Library West (50+ computers, collaborative workstations); Newell Hall (30+ computers, 24/7 access); Architecture Computer Lab (specialized design software); Norman Hall (education-focused resources); Health Science Center (medical applications); and college-specific labs with specialized software. Most labs provide printing services, scanners, and collaborative spaces. Hours vary by location, with some offering 24/7 access using Gator 1 cards after regular hours."
    },
    {
        "question": "How do I access my UF email?",
        "answer": "UF email can be accessed via multiple methods: 1) Web browser at mail.ufl.edu using GatorLink credentials; 2) The Outlook mobile app for iOS/Android; 3) Desktop email clients (Outlook, Apple Mail, etc.) using IMAP/SMTP settings available at it.ufl.edu/email; 4) Setting up forwarding to a personal email account through myUFL. Student email addresses follow the format GatorLink@ufl.edu and include 50GB of storage. For technical assistance, contact the UF Computing Help Desk at 352-392-HELP or helpdesk@ufl.edu."
    },
    {
        "question": "What cloud storage options does UF provide?",
        "answer": "UF provides three primary cloud storage options: Microsoft OneDrive (1TB of storage, integrated with Office 365, accessible at onedrive.ufl.edu), UF G Suite Google Drive (unlimited storage for academic files, accessible with GatorLink credentials at drive.google.com), and UF Dropbox Business (unlimited storage, enhanced security features, team collaboration tools). All three services are FERPA-compliant for educational records. For large research datasets, UF ResearchVault offers additional secure storage options managed through Research Computing."
    },
    {
        "question": "How do I access UF VPN?",
        "answer": "To access UF VPN: 1) Visit vpn.ufl.edu and download Cisco AnyConnect VPN Client for your operating system; 2) Install the application and open it; 3) Enter vpn.ufl.edu as the connection address; 4) Enter your GatorLink username and password when prompted; 5) Select 'UF - All Traffic' or 'UF - Split Tunnel' group based on your needs. The VPN provides secure access to UF resources like library databases, restricted applications, and departmental systems. For installation issues, contact the UF Computing Help Desk at 352-392-HELP."
    },
    {
        "question": "What is UF Apps and how do I access it?",
        "answer": "UF Apps is a virtual desktop environment providing access to software applications from any device with internet access. To use it: 1) Go to apps.ufl.edu in a web browser; 2) Log in with your GatorLink credentials; 3) Select the desired application from the available icons. The service provides access to over 100 software programs including Microsoft Office, Adobe Creative Cloud, ArcGIS, SPSS, AutoCAD, MATLAB, and speciality research applications without requiring local installation. UF Apps is accessible on Windows, Mac, Linux, iOS, and Android devices."
    },
    {
        "question": "What 3D printing resources are available to UF students?",
        "answer": "UF students have access to several 3D printing facilities: 1) MADE@UF in Marston Science Library (multiple FDM and resin printers, free for academic projects); 2) Architecture Fabrication Lab (advanced printing for architecture students); 3) Engineering IPPD Labs (high-precision printers for engineering projects); 4) Health Science Center 3D lab (biomedical applications); and 5) College-specific labs in Fine Arts, Design, and Engineering. Most locations provide training workshops, design software access, and staff assistance with file preparation."
    },
    {
        "question": "What research computing services does UF provide?",
        "answer": "UF Research Computing provides comprehensive services including: 1) Access to HiPerGator supercomputer with 40,000+ cores and 1,500 NVIDIA A100 GPUs; 2) 150+ petabytes of research storage; 3) Specialized scientific software and applications; 4) Training workshops on high-performance computing; 5) Individual consultation on research computing needs; 6) Support for grant proposals requiring computational resources; 7) AI model development assistance; and 8) Data analysis and visualization services. Resources are available to all UF faculty, staff, and students engaged in research with allocation request forms on the research.ufl.edu website."
    },
    {
        "question": "How do I set up multi-factor authentication for my UF account?",
        "answer": "To set up multi-factor authentication (MFA) for your UF account: 1) Visit it.ufl.edu/two-factor and click 'Enroll Now'; 2) Log in with your GatorLink credentials; 3) Choose your authentication method (Duo Mobile app recommended, SMS or phone call as alternatives); 4) Follow the setup instructions specific to your chosen method; 5) Register at least one backup device. MFA is required for accessing all UF systems including myUFL, Canvas, and email. For assistance, contact the UF Computing Help Desk at 352-392-HELP. It's recommended to set up multiple authentication methods as backups."
    },
    
    # Financial and Administrative Questions
    {
        "question": "What is the exact cost of tuition for Florida residents in 2025?",
        "answer": "For Florida residents in the 2024-2025 academic year, undergraduate tuition at UF is approximately $212.71 per credit hour ($6,380 for a standard 30-credit academic year). This includes the base tuition rate plus required fees such as Activity & Service, Health, Athletic, Transportation, and Technology fees. Graduate program tuition for Florida residents is approximately $530.69 per credit hour, though rates vary by specific graduate program, with some professional programs charging premium tuition rates."
    },
    {
        "question": "How does the Bright Futures scholarship work at UF?",
        "answer": "The Florida Bright Futures Scholarship at UF has two primary award levels: Florida Academic Scholars (FAS) and Florida Medallion Scholars (FMS). For 2024-2025, FAS covers 100% of tuition and applicable fees plus $300 per semester for books, while FMS covers 75% of tuition and applicable fees. Recipients must maintain a minimum GPA (3.0 for FMS, 3.0 for FAS) and complete at least 24 credit hours per academic year. The scholarship is applied automatically to eligible students' accounts through Financial Aid, with no separate application needed at UF."
    },
    {
        "question": "What fees do UF students pay besides tuition?",
        "answer": "Beyond base tuition, UF students pay several mandatory fees per credit hour: Activity & Service Fee ($19.06), Health Fee ($15.81), Athletic Fee ($1.90), Transportation Access Fee ($9.44), and Technology Fee ($5.25). Additional fees may include: Capital Improvement Fee ($6.76), Financial Aid Fee ($5.79), various course-specific fees for labs or materials, a facilities fee for certain colleges, distance learning fees for online courses, and potentially a late registration fee ($100) or late payment fee ($100). Some colleges also charge a tuition differential that varies by program."
    },
    {
        "question": "How do I apply for financial aid at UF?",
        "answer": "To apply for financial aid at UF: 1) Submit the FAFSA at fafsa.gov using UF's school code (001535) annually after October 1 for the next academic year; 2) Complete any verification requirements listed in your myUFL account if selected; 3) Accept or decline offered aid through myUFL under 'Student Self Service > Financial Aid'; 4) Maintain Satisfactory Academic Progress (2.0 undergraduate GPA, 3.0 graduate GPA, 67% completion rate); 5) Complete entrance counseling and master promissory notes for any loans. Priority deadline is December 15 for the following academic year, but applications are accepted year-round."
    },
    {
        "question": "What is OneUF and how do I access it?",
        "answer": "ONE.UF is the University of Florida's student information system accessible at one.uf.edu. After logging in with GatorLink credentials, students can: register for classes, view/pay bills, access financial aid information, update personal information, view transcripts and grades, submit degree applications, access holds and academic records, review degree audits, and manage meal plans or parking permits. ONE.UF replaced the older ISIS system and serves as the central hub for student administrative services. For technical support, contact the UF Computing Help Desk at 352-392-HELP."
    },
    {
        "question": "How do I pay my tuition bill at UF?",
        "answer": "UF tuition can be paid through several methods: 1) Online via ONE.UF portal using electronic check (no fee) or credit/debit card (2.6% convenience fee); 2) By mail with check or money order to University of Florida, University Bursar, S113 Criser Hall, PO Box 114050, Gainesville, FL 32611-4050; 3) In person at S113 Criser Hall during business hours; 4) Through the UF payment plan that divides semester charges into equal installments (enrollment fee applies). Payment deadlines are typically the second Friday after classes begin each semester. Late payments incur a $100 late fee plus potential registration holds."
    },
    {
        "question": "How do I get a replacement Gator 1 Card?",
        "answer": "To replace a lost or damaged Gator 1 Card: 1) Visit the Gator 1 Central Office at the Reitz Union (Ground floor) during business hours (typically 8am-4:30pm weekdays); 2) Bring a government-issued photo ID (driver's license, passport); 3) Pay the replacement fee ($15 for lost cards, $15 for damaged cards, free if stolen with police report); 4) Receive your new card immediately. The replacement automatically deactivates the old card. You can also place a temporary hold on your lost card through the UF Mobile app while searching for it, which can be removed if you find the card."
    },
    {
        "question": "What is the procedure for dropping a class at UF?",
        "answer": "To drop a class at UF: During the drop/add period (first five days of the semester), students can drop courses through ONE.UF without academic penalty or financial liability. After drop/add but before the drop deadline (around the eighth week of the semester), students can still drop through ONE.UF but will receive a 'W' (withdrawal) on their transcript and remain financially responsible for the course. After the drop deadline, students must petition their college for a late drop with documented extenuating circumstances. International students and athletes must consult their advisors before dropping as it may affect eligibility status."
    },
    {
        "question": "How do I change my major at UF?",
        "answer": "To change your major at UF: 1) Check if you meet the requirements for the intended major (GPA, prerequisite courses, etc.) on the department website; 2) Meet with an academic advisor in your current college to discuss the change; 3) Contact an advisor in the department of your intended major to confirm requirements and procedures; 4) Submit a change of major form (either electronic or paper depending on the college) with required signatures; 5) Complete any additional application materials if the major is limited access. Processing times vary from immediate to several weeks depending on the colleges involved and timing during the semester."
    },
    {
        "question": "What's the difference between dropping and withdrawing from a class?",
        "answer": "At UF, dropping a class during the drop/add period (first five days of the semester) results in complete removal of the course from your record with no academic or financial penalty. Withdrawing from a class (after drop/add but before the withdrawal deadline around week 8) results in a 'W' grade on your transcript. This 'W' doesn't affect GPA but counts as an attempted course for excess hours and financial aid calculations. Students remain financially liable for withdrawn courses. Dropping is done through ONE.UF during drop/add, while withdrawing requires submitting a withdrawal request through ONE.UF before the published deadline."
    },
    
    # Campus Safety and Emergency Information
    {
        "question": "What is the UF Alert system?",
        "answer": "UF Alert is the university's emergency notification system that delivers critical information during campus emergencies. It sends alerts via text message, email, the UF website, social media, mobile app notifications, and outdoor sirens. Students, faculty, and staff are automatically enrolled using contact information in the UF Directory. To update your contact information, log into myUFL and navigate to 'My Account > Update Emergency Contact'. The system is tested at the beginning of each semester and used only for genuine emergencies or severe weather warnings."
    },
    {
        "question": "How does the SNAP service work at UF?",
        "answer": "SNAP (Student Nighttime Auxiliary Patrol) provides free campus safety escorts at night. Service hours are 6:30 PM to 3:00 AM during fall/spring semesters (reduced hours during summer and breaks). Students can request escorts by calling 352-392-SNAP (7627), using the TapRide app, or visiting ufl.edu/snap. SNAP operates within campus boundaries and some adjacent areas, with walking escorts available for areas vehicles cannot access. The service uses clearly marked vans operated by trained student employees supervised by the UF Police Department. Wait times are typically 5-15 minutes depending on demand."
    },
    {
        "question": "Where are the emergency blue light phones located on campus?",
        "answer": "UF's campus features over 380 emergency blue light phones, identifiable by their bright blue light or strobe. They're strategically placed along walkways, parking lots, garages, building entrances, and remote areas. Each phone connects directly to UF Police dispatch when activated. Major concentrations include the Commuter Lot, Cultural Plaza, Sorority Row, Reitz Union area, residence hall areas, and along major pedestrian routes. A comprehensive map is available on the UFPD website and UF Mobile app. All phones are tested monthly to ensure functionality."
    },
    {
        "question": "What is UF's policy on campus carry?",
        "answer": "Florida law and UF policy prohibit carrying firearms on campus with very limited exceptions. Per Florida Statute 790.06(12), concealed carry license holders may not carry firearms into any university facility, including classrooms, residence halls, dining facilities, laboratories, and sporting events. The only exceptions are: firearms kept secured in vehicles, non-functioning firearms in academic programs with written approval, and law enforcement officers. Electric defense weapons (Tasers/stun guns) may be carried by adults for self-defense. Violations may result in arrest, academic sanctions, and/or trespassing warnings."
    },
    {
        "question": "What should I do in case of a hurricane warning at UF?",
        "answer": "During a hurricane warning at UF: 1) Monitor UF Alert messages and emergency.ufl.edu for official updates on campus closures; 2) Follow evacuation orders if given; 3) If staying in a residence hall, follow instructions from housing staff regarding designated shelter areas; 4) Prepare an emergency kit with medications, important documents, water, non-perishable food, flashlight, and batteries; 5) Charge electronic devices before power loss; 6) Stay indoors during the storm; 7) Report emergencies to UF Police at 352-392-1111. UF typically announces closures at least 24 hours before expected storm impact when possible."
    },
    {
        "question": "How does the UF Health Shands emergency room triage system work?",
        "answer": "UF Health Shands Emergency Room uses a five-level triage system (Emergency Severity Index) to prioritize patients: Level 1 (immediate, life-threatening), Level 2 (urgent, high risk), Level 3 (acute, potentially serious), Level 4 (less urgent), and Level 5 (non-urgent). Upon arrival, patients are assessed by a triage nurse who checks vital signs and chief complaints to assign a priority level. Patients are treated based on medical priority rather than arrival time. The emergency department provides 24/7 care at two locations: 1600 SW Archer Road (main campus, Level 1 trauma center) and 4197 NW 89th Blvd (freestanding ER in northwest Gainesville)."
    },
    {
        "question": "What services does the UF Student Health Care Center offer?",
        "answer": "The UF Student Health Care Center offers comprehensive services including: primary care appointments, urgent care for acute illness/injury, women's health services, psychiatry and mental health counseling, allergy shots, immunizations (including travel vaccines), laboratory services, X-ray and imaging, physical therapy, nutrition counseling, sexual health services, dermatology, sports medicine, and a full-service pharmacy. The main location at the Infirmary Building operates weekdays 8am-5pm, with satellite clinics at SHCC@Shands, SHCC@Dental, and other campus locations. Most services are covered by the health fee paid with tuition, with some specialty services requiring additional payment."
    },
    {
        "question": "How do I report a crime on campus?",
        "answer": "To report a crime on UF campus: For emergencies requiring immediate assistance, call 911 or use any blue light emergency phone. For non-emergencies, contact the UF Police Department at 352-392-1111. Crimes can also be reported in person at the UFPD station (Building 51, Museum Road). Anonymous tips can be submitted through the UFPD website, the GatorSafe mobile app, or by texting UFPD plus your tip to 274637 (CRIMES). The university also maintains an anonymous hotline at 877-556-5356. For certain crimes like sexual assault, reporting options include the Office of Victim Services at 352-392-5648, which can provide confidential support."
    },
    {
        "question": "What should I do if I experience sexual harassment or assault at UF?",
        "answer": "If you experience sexual harassment or assault at UF: For immediate help, contact UF Police at 352-392-1111 or 911. For confidential support regardless of reporting decisions, contact the Sexual Trauma Interpersonal Violence Education (STRIVE) at the Counseling & Wellness Center (352-392-1575) or the Office of Victim Services (352-392-5648). To file a formal complaint, contact the Title IX Coordinator at 352-273-1094 or titleix@ad.ufl.edu. Medical services are available at the Student Health Care Center or UF Health Shands Emergency Department. The university provides accommodations including class adjustments, housing changes, and no-contact orders regardless of whether a formal report is filed."
    },
    {
        "question": "What are the fire safety procedures in UF residence halls?",
        "answer": "UF residence hall fire safety procedures require all residents to evacuate immediately when an alarm sounds, using stairs (not elevators) and following illuminated exit signs to the designated assembly area outside. Each hall conducts monthly fire drills during the academic year. Prohibited items include candles, incense, hotplates, space heaters, and any open-flame devices. Tampering with fire equipment (alarms, extinguishers, smoke detectors) is a serious violation subject to disciplinary action and possible criminal charges. Residents with disabilities should establish an evacuation plan with their RA at the beginning of the semester for special assistance during emergencies."
    },
    {
        "question": "How does the active shooter response training work at UF?",
        "answer": "UF provides active shooter response training based on the 'Run, Hide, Fight' protocol. The UFPD offers in-person training sessions to departments and student groups upon request, covering situation awareness, evacuation procedures, barricading techniques, and last-resort defense options. Online training modules are available through myTraining. The UF Alert system would provide emergency notifications during an actual incident. The GatorSafe mobile app includes an emergency guide with active shooter instructions. All UF classrooms and many other campus spaces have emergency response guides posted that include active shooter protocols and specific evacuation routes."
    },
    
    # Miscellaneous and Unique UF Information
    {
        "question": "Why is UF's mascot an alligator?",
        "answer": "UF's alligator mascot originated in 1908 when a Gainesville merchant decided to sell pennants with an alligator emblem, as alligators were (and remain) common in the Florida landscape. The symbol was officially adopted in 1911. Some historical accounts suggest that the first UF football team kept a live alligator in Lake Alice as an unofficial mascot. The name 'Gators' became popular with fans and local press, and the costumed mascot 'Albert the Alligator' was introduced in 1970. He was joined by 'Alberta the Alligator' in 1984. Together, they represent UF's connection to Florida's natural environment and the tenacity of alligators as predators."
    },
    {
        "question": "What is the history of Century Tower?",
        "answer": "Century Tower was built in 1953 to commemorate the 100th anniversary of the University of Florida and as a memorial to UF students and alumni who died in World Wars I and II. Standing 157 feet tall, the tower is constructed of Alabama limestone and reinforced concrete. In 1979, a carillon (musical instrument consisting of bells) was installed with 49 bells weighing from 7 pounds to 3 tons. The carillon is played regularly for recitals, special occasions, and daily concerts at 12:35 and 4:55 PM during the fall and spring semesters. The tower's plaza features a plaque honoring UF's war dead and is a central landmark on campus."
    },
    {
        "question": "How many Nobel Prize winners have taught at UF?",
        "answer": "UF has been home to three Nobel Prize winners throughout its history: Robert Grubbs (Chemistry, 2005), who was a graduate chemistry professor at UF from 1969 to 1978 before moving to Caltech where he conducted his Nobel-winning work on metathesis; Marshall Nirenberg (Physiology or Medicine, 1968), who earned his master's and doctoral degrees at UF before his groundbreaking work at the National Institutes of Health; and Jean-Marie Lehn (Chemistry, 1987), who held a visiting professorship at UF's Center for Molecular Recognition. Additionally, several Nobel laureates have given lectures and participated in academic programs at UF over the years."
    },
    {
        "question": "What is the history of the Gator Chomp?",
        "answer": "The Gator Chomp gesture originated in 1981 when UF student Hugh Flournoy and friends from the Gator Band started mimicking an alligator's jaws with their arms during football games. The motion caught on with fans, and when played with the musical theme from 'Jaws,' it quickly became UF's signature cheer. Now performed by extending arms forward with palms facing opposite each other, opening and closing like alligator jaws, the Chomp is accompanied by a distinctive band arrangement and is recognized nationally as a symbol of Gator pride. It's now integrated into official university events, marketing, and even used by professional athletes who attended UF."
    },
    {
        "question": "What is inside the time capsule at the Reitz Union?",
        "answer": "The Reitz Union time capsule, sealed during the 2016 renovation, contains items representing student life in the early 21st century including: a 2015-2016 undergraduate catalog, a Gator 1 ID card, a smartphone with UF apps installed, student newspaper editions, a USB drive with student organization information, meal plan information, Gator football memorabilia, a building blueprint of the renovated Reitz Union, student government election materials, photos of campus life, and letters from student leaders to future students. The capsule is scheduled to be opened in 2066, marking the 100th anniversary of the original Reitz Union building."
    },
    {
        "question": "What is the bat house at UF and why was it built?",
        "answer": "The UF Bat Houses are the world's largest occupied bat houses, located on Museum Road near Lake Alice. They were built in 1991 as a humane solution after bats were displaced from the Johnson Hall stadium. The structures house approximately 500,000 Brazilian free-tailed bats and a smaller number of Southeastern bats. The colony consumes an estimated 2.5 billion insects nightly, providing natural pest control for the campus. The bats emerge approximately 15-20 minutes after sunset, creating a spectacular viewing opportunity. In 2009, a new bat barn was constructed after one of the original houses collapsed, and the facilities are maintained by UF's Facility Services."
    },
    {
        "question": "What is the Krishna Lunch program at UF?",
        "answer": "The Krishna Lunch program is a long-standing UF tradition since 1971, serving vegetarian meals on the Plaza of the Americas every weekday during fall and spring semesters from 11am to 1:30pm. Operated by the Gainesville Krishna House, the program offers a rotating menu of vegetarian and vegan options including rice, vegetable entrees, salad, halava dessert, and lemonade for a donation of $5 (as of 2024). All food is prepared according to Vedic principles, and the program serves approximately 1,200 meals daily. The tradition began as a small food distribution by Krishna devotees and has grown into an iconic part of UF campus culture embraced by students of all backgrounds."
    },
    {
        "question": "What is the UF Homecoming tradition?",
        "answer": "UF Homecoming, established in 1916, is one of the largest student-run homecoming celebrations in the nation, typically occurring in October or November. The week-long celebration includes: Gator Gallop (a 2-mile run through campus), Homecoming Parade down University Avenue, Soulfest cultural celebration, Gator Growl (the nation's largest student-run pep rally featuring performances and celebrity appearances), the Alumni BBQ, and the Homecoming football game. Florida Blue Key, a prestigious student leadership honorary, organizes the events through multiple committees. The tradition temporarily transforms the campus with orange and blue decorations, banners, and themed displays at fraternity and sorority houses."
    },
    {
        "question": "What is the meaning behind the 'We Are The Boys' tradition at UF football games?",
        "answer": "The 'We Are the Boys from Old Florida' tradition occurs between the third and fourth quarters of every Gator football game. Fans link arms side-to-side and sway while singing the 1919 song written by Robert Swanson. The lyrics celebrate UF pride with lines like 'We are the boys from old Florida, F-L-O-R-I-D-A,' and express loyalty to the orange and blue. After this tradition concludes, the stadium plays 'I Won't Back Down' by Tom Petty (a Gainesville native), which became a newer tradition following Petty's passing in 2017. The dual traditions create an emotional moment unifying all fans regardless of the game's outcome."
    },
    {
        "question": "What famous movies have been filmed at UF?",
        "answer": "Several notable films have featured UF's campus, with the most famous being 'Gator' (1976) starring and directed by Burt Reynolds, with scenes filmed at Florida Field and around campus. 'The Hawk Is Dying' (2006) starring Paul Giamatti filmed extensively in Gainesville and at UF. 'G.I. Jane' (1997) with Demi Moore used the UF Aquatic Center for some scenes. Documentary films including 'Gator Nation' and ESPN productions have featured the campus extensively. While not filmed on campus, 'The Waterboy' (1998) references UF as the bitter rival of the fictional South Central Louisiana State University, and 'Parenthood' (1989) mentions one character attending the University of Florida."
    },
    {
        "question": "What is the Two Bits tradition at UF football games?",
        "answer": "The 'Two Bits' tradition began in 1949 when George Edmondson (not a UF alumnus) spontaneously led fans in a cheer at a football game against The Citadel. Wearing his signature yellow shirt and tie, khakis, and saddle shoes, 'Mr. Two Bits' continued the cheer for over 60 years before officially retiring in 2008. The famous cheer goes: 'Two bits, four bits, six bits, a dollar. All for the Gators, stand up and holler!' After Edmondson's retirement, UF established the Honorary Mr. Two Bits tradition where prominent Gator alumni and celebrities perform the cheer before each home game. George Edmondson passed away in 2019 at age 97, but his legacy continues through this beloved tradition."
    },
    {
        "question": "What is the Baughman Center at UF?",
        "answer": "The Baughman Center is a non-denominational meditation and contemplation space on the shores of Lake Alice. Completed in 2000 through a donation from Dr. George and Hazel Baughman, the 1,500-square-foot pavilion features limestone floors, maple and cypress woodwork, art glass windows, and exceptional acoustics. The serene setting makes it popular for small weddings, memorial services, and private reflection. The center's distinctive architecture includes a sweeping roofline and walls of glass that blend the natural surroundings with the interior space. Open to the public weekdays from 9:30am to 3:00pm when not reserved for events, it's considered one of the most beautiful buildings on campus."
    },
    {
        "question": "What is the Albert and Alberta gator mascot tradition?",
        "answer": "Albert and Alberta are UF's official mascot couple. Albert was introduced in 1970 as a full-costumed mascot, replacing the live alligators that had occasionally been brought to games. Alberta, Albert's female counterpart, joined in 1984, making UF one of few universities with both male and female mascots. The costumed characters attend sporting events, community functions, and university activities, engaging with fans and performing with the cheerleading squad. Students who portray Albert and Alberta maintain anonymity during their tenure and are revealed only at graduation. The position is highly competitive, requiring tryouts that evaluate personality, dance skills, and ability to communicate through costumed performance."
    }
]

# Initialize the cache when this module is imported
if __name__ == "__main__":
    # Simple test 
    cache = UFQuestionCache()
    test_query = "Where is the Reitz Union located?"
    result = cache.find_matching_question(test_query)
    
    if result:
        question, answer = result
        print(f"Query: {test_query}")
        print(f"Matched Question: {question}")
        print(f"Answer: {answer}")
    else:
        print(f"No match found for: {test_query}")