"""
Smart entity extractor using multiple NLP models
Supports spaCy NER, BERT-based models, and LLM APIs
"""

import re
import json
from typing import Dict, List, Set, Optional, Tuple
from collections import defaultdict
import logging

try:
    from .utils import load_config, log_message
except ImportError:
    # Fallback for direct execution
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent))
    from utils import load_config, log_message


class SmartEntityExtractor:
    """Advanced entity extractor using multiple NLP approaches"""
    
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize the smart entity extractor"""
        self.config = load_config(config_path)
        self.extraction_config = self.config.get('smart_extraction', {})
        
        # Initialize models based on configuration
        self.spacy_nlp = None
        self.sentence_transformer = None
        self.university_embeddings = None
        
        self._initialize_models()
        self._load_knowledge_base()
    
    def _initialize_models(self):
        """Initialize NLP models based on configuration"""
        methods = self.extraction_config.get('methods', ['spacy'])
        
        # Initialize spaCy
        if 'spacy' in methods:
            try:
                import spacy
                # Try to load English model
                try:
                    self.spacy_nlp = spacy.load("en_core_web_sm")
                    log_message("✅ Loaded spaCy en_core_web_sm model")
                except OSError:
                    log_message("⚠️  spaCy en_core_web_sm not found. Install with: python -m spacy download en_core_web_sm")
                    self.spacy_nlp = None
            except ImportError:
                log_message("⚠️  spaCy not installed")
        
        # Initialize sentence transformer for semantic similarity
        if 'semantic' in methods:
            try:
                from sentence_transformers import SentenceTransformer
                model_name = self.extraction_config.get('sentence_model', 'all-MiniLM-L6-v2')
                self.sentence_transformer = SentenceTransformer(model_name)
                log_message(f"✅ Loaded sentence transformer: {model_name}")
            except ImportError:
                log_message("⚠️  sentence-transformers not installed")
    
    def _load_knowledge_base(self):
        """Load and expand knowledge base with semantic embeddings"""
        # Extended university database
        self.universities_db = {
            # US Universities
            'MIT': ['Massachusetts Institute of Technology', 'MIT', 'mit'],
            'Stanford': ['Stanford University', 'Stanford', 'stanford'],
            'Harvard': ['Harvard University', 'Harvard', 'harvard'],
            'CMU': ['Carnegie Mellon University', 'CMU', 'Carnegie Mellon', 'carnegie mellon'],
            'UC Berkeley': ['University of California Berkeley', 'UC Berkeley', 'Berkeley', 'UCB'],
            'Caltech': ['California Institute of Technology', 'Caltech', 'caltech'],
            'Princeton': ['Princeton University', 'Princeton', 'princeton'],
            'Yale': ['Yale University', 'Yale', 'yale'],
            'Columbia': ['Columbia University', 'Columbia', 'columbia'],
            'UChicago': ['University of Chicago', 'UChicago', 'Chicago', 'uchicago'],
            'Cornell': ['Cornell University', 'Cornell', 'cornell'],
            'UPenn': ['University of Pennsylvania', 'UPenn', 'Penn', 'upenn'],
            'Northwestern': ['Northwestern University', 'Northwestern', 'northwestern'],
            'Duke': ['Duke University', 'Duke', 'duke'],
            'Johns Hopkins': ['Johns Hopkins University', 'Johns Hopkins', 'JHU', 'johns hopkins'],
            'UCLA': ['University of California Los Angeles', 'UCLA', 'ucla'],
            'UCSD': ['University of California San Diego', 'UCSD', 'ucsd'],
            'NYU': ['New York University', 'NYU', 'nyu'],
            'Georgia Tech': ['Georgia Institute of Technology', 'Georgia Tech', 'GT', 'gatech'],
            'UIUC': ['University of Illinois Urbana-Champaign', 'UIUC', 'Illinois', 'uiuc'],
            'UT Austin': ['University of Texas at Austin', 'UT Austin', 'Texas', 'ut austin'],
            'University of Washington': ['University of Washington', 'UW', 'Washington', 'uw'],
            'Rice': ['Rice University', 'Rice', 'rice'],
            'Vanderbilt': ['Vanderbilt University', 'Vanderbilt', 'vanderbilt'],
            'Brown': ['Brown University', 'Brown', 'brown'],
            'Dartmouth': ['Dartmouth College', 'Dartmouth', 'dartmouth'],
            
            # International Universities
            'Oxford': ['University of Oxford', 'Oxford', 'oxford'],
            'Cambridge': ['University of Cambridge', 'Cambridge', 'cambridge'],
            'Imperial College': ['Imperial College London', 'Imperial', 'imperial'],
            'ETH Zurich': ['ETH Zurich', 'ETH', 'eth zurich'],
            'University of Toronto': ['University of Toronto', 'UofT', 'Toronto', 'uoft'],
            'McGill': ['McGill University', 'McGill', 'mcgill'],
            'NUS': ['National University of Singapore', 'NUS', 'nus'],
            'NTU': ['Nanyang Technological University', 'NTU', 'ntu'],
            'University of Melbourne': ['University of Melbourne', 'Melbourne', 'unimelb'],
            'ANU': ['Australian National University', 'ANU', 'anu'],
        }
        
        # Extended majors database
        self.majors_db = {
            'Computer Science': ['Computer Science', 'CS', 'computer science', 'computing'],
            'Electrical Engineering': ['Electrical Engineering', 'EE', 'electrical engineering', 'ECE'],
            'Mechanical Engineering': ['Mechanical Engineering', 'ME', 'mechanical engineering'],
            'Civil Engineering': ['Civil Engineering', 'CE', 'civil engineering'],
            'Chemical Engineering': ['Chemical Engineering', 'ChemE', 'chemical engineering'],
            'Biomedical Engineering': ['Biomedical Engineering', 'BME', 'biomedical engineering'],
            'Mathematics': ['Mathematics', 'Math', 'mathematics', 'Applied Mathematics'],
            'Physics': ['Physics', 'physics', 'Applied Physics'],
            'Chemistry': ['Chemistry', 'chemistry', 'Biochemistry'],
            'Biology': ['Biology', 'biology', 'Molecular Biology', 'Cell Biology'],
            'Medicine': ['Medicine', 'medicine', 'Medical', 'MD'],
            'Business': ['Business', 'business', 'Business Administration'],
            'MBA': ['MBA', 'Master of Business Administration', 'mba'],
            'Economics': ['Economics', 'economics', 'Econ'],
            'Finance': ['Finance', 'finance', 'Financial Engineering'],
            'Psychology': ['Psychology', 'psychology', 'Psych'],
            'Political Science': ['Political Science', 'politics', 'government'],
            'International Relations': ['International Relations', 'IR', 'international relations'],
            'Data Science': ['Data Science', 'data science', 'Data Analytics'],
            'Machine Learning': ['Machine Learning', 'ML', 'machine learning', 'AI'],
            'Artificial Intelligence': ['Artificial Intelligence', 'AI', 'artificial intelligence'],
            'Cybersecurity': ['Cybersecurity', 'cybersecurity', 'Information Security'],
            'Software Engineering': ['Software Engineering', 'software engineering', 'SWE'],
        }
        
        # Extended programs database
        self.programs_db = {
            'PhD': ['PhD', 'Ph.D.', 'Doctor of Philosophy', 'Doctorate', 'doctoral'],
            'Master': ['Master', 'Masters', 'MS', 'MA', 'MEng', 'MSc'],
            'Bachelor': ['Bachelor', 'Bachelors', 'BS', 'BA', 'BSc', 'undergraduate'],
            'MBA': ['MBA', 'Master of Business Administration'],
            'JD': ['JD', 'Juris Doctor', 'Law School'],
            'MD': ['MD', 'Doctor of Medicine', 'Medical School'],
            'Postdoc': ['Postdoc', 'Post-doctoral', 'Postdoctoral'],
            'Certificate': ['Certificate', 'certification', 'cert'],
        }
        
        # Create reverse lookup dictionaries
        self._create_reverse_lookups()
    
    def _create_reverse_lookups(self):
        """Create reverse lookup dictionaries for fast matching"""
        self.university_lookup = {}
        for canonical, variants in self.universities_db.items():
            for variant in variants:
                self.university_lookup[variant.lower()] = canonical
        
        self.major_lookup = {}
        for canonical, variants in self.majors_db.items():
            for variant in variants:
                self.major_lookup[variant.lower()] = canonical
        
        self.program_lookup = {}
        for canonical, variants in self.programs_db.items():
            for variant in variants:
                self.program_lookup[variant.lower()] = canonical
    
    def extract_entities_smart(self, text: str) -> Dict[str, List[str]]:
        """Extract entities using multiple smart methods"""
        entities = {
            'universities': [],
            'majors': [],
            'programs': []
        }
        
        methods = self.extraction_config.get('methods', ['spacy', 'keyword', 'pattern'])
        
        # Method 1: spaCy NER
        if 'spacy' in methods and self.spacy_nlp:
            spacy_entities = self._extract_with_spacy(text)
            self._merge_entities(entities, spacy_entities)
        
        # Method 2: Enhanced keyword matching
        if 'keyword' in methods:
            keyword_entities = self._extract_with_keywords(text)
            self._merge_entities(entities, keyword_entities)
        
        # Method 3: Pattern matching
        if 'pattern' in methods:
            pattern_entities = self._extract_with_patterns(text)
            self._merge_entities(entities, pattern_entities)
        
        # Method 4: Semantic similarity (if available)
        if 'semantic' in methods and self.sentence_transformer:
            semantic_entities = self._extract_with_semantics(text)
            self._merge_entities(entities, semantic_entities)
        
        # Method 5: LLM API (if configured)
        if 'llm' in methods:
            llm_entities = self._extract_with_llm(text)
            self._merge_entities(entities, llm_entities)
        
        # Clean and deduplicate
        entities = self._clean_entities(entities)
        
        return entities
    
    def _extract_with_spacy(self, text: str) -> Dict[str, List[str]]:
        """Extract entities using spaCy NER"""
        entities = {'universities': [], 'majors': [], 'programs': []}
        
        try:
            doc = self.spacy_nlp(text)
            
            for ent in doc.ents:
                if ent.label_ in ['ORG', 'GPE']:  # Organizations and places
                    # Check if it's a university
                    if self._is_university(ent.text):
                        canonical = self._get_canonical_university(ent.text)
                        if canonical:
                            entities['universities'].append(canonical)
                
                # Look for degree mentions in context
                if ent.label_ in ['PERSON', 'ORG']:
                    context = text[max(0, ent.start_char-50):ent.end_char+50]
                    program = self._extract_program_from_context(context)
                    if program:
                        entities['programs'].append(program)
        
        except Exception as e:
            log_message(f"Error in spaCy extraction: {e}", "ERROR")
        
        return entities
    
    def _extract_with_keywords(self, text: str) -> Dict[str, List[str]]:
        """Enhanced keyword-based extraction"""
        entities = {'universities': [], 'majors': [], 'programs': []}
        text_lower = text.lower()
        
        # Extract universities
        for variant, canonical in self.university_lookup.items():
            if variant in text_lower:
                entities['universities'].append(canonical)
        
        # Extract majors
        for variant, canonical in self.major_lookup.items():
            if variant in text_lower:
                entities['majors'].append(canonical)
        
        # Extract programs
        for variant, canonical in self.program_lookup.items():
            if variant in text_lower:
                entities['programs'].append(canonical)
        
        return entities
    
    def _extract_with_patterns(self, text: str) -> Dict[str, List[str]]:
        """Extract entities using regex patterns"""
        entities = {'universities': [], 'majors': [], 'programs': []}
        
        # University patterns
        university_patterns = [
            r'University of ([A-Z][a-zA-Z\s]+)',
            r'([A-Z][a-zA-Z\s]+) University',
            r'([A-Z]{2,5})\s+(?:university|college)',
            r'(?:studying at|admitted to|applying to)\s+([A-Z][a-zA-Z\s]+)',
        ]
        
        for pattern in university_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                university_name = match.group(1).strip()
                canonical = self._get_canonical_university(university_name)
                if canonical:
                    entities['universities'].append(canonical)
        
        # Program patterns
        program_patterns = [
            r'(PhD|Ph\.D\.|doctorate|doctoral)\s+(?:in|program)',
            r'(Master|MS|MA|MEng)\s+(?:in|of|program)',
            r'(Bachelor|BS|BA|undergraduate)\s+(?:in|of|program)',
            r'applying for\s+(PhD|Master|Bachelor)',
        ]
        
        for pattern in program_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                program = match.group(1)
                canonical = self._get_canonical_program(program)
                if canonical:
                    entities['programs'].append(canonical)
        
        return entities
    
    def _extract_with_semantics(self, text: str) -> Dict[str, List[str]]:
        """Extract entities using semantic similarity"""
        entities = {'universities': [], 'majors': [], 'programs': []}
        
        try:
            # This is a placeholder for semantic extraction
            # Would require pre-computed embeddings and similarity matching
            pass
        except Exception as e:
            log_message(f"Error in semantic extraction: {e}", "ERROR")
        
        return entities
    
    def _extract_with_llm(self, text: str) -> Dict[str, List[str]]:
        """Extract entities using LLM API"""
        entities = {'universities': [], 'majors': [], 'programs': []}
        
        try:
            llm_config = self.extraction_config.get('llm', {})
            if not llm_config.get('enabled', False):
                return entities
            
            provider = llm_config.get('provider', 'openai')
            
            if provider == 'openai':
                entities = self._extract_with_openai(text)
            elif provider == 'anthropic':
                entities = self._extract_with_anthropic(text)
        
        except Exception as e:
            log_message(f"Error in LLM extraction: {e}", "ERROR")
        
        return entities
    
    def _extract_with_openai(self, text: str) -> Dict[str, List[str]]:
        """Extract entities using OpenAI GPT"""
        try:
            import openai
            
            prompt = f"""
            Extract universities, academic majors, and degree programs from the following text.
            Return the result as JSON with keys: universities, majors, programs.
            Only include entities that are explicitly mentioned.
            
            Text: {text}
            
            JSON:
            """
            
            # This would require OpenAI API key configuration
            # Implementation depends on API setup
            
        except ImportError:
            log_message("OpenAI library not installed")
        except Exception as e:
            log_message(f"OpenAI extraction error: {e}", "ERROR")
        
        return {'universities': [], 'majors': [], 'programs': []}
    
    def _is_university(self, text: str) -> bool:
        """Check if text likely refers to a university"""
        university_indicators = [
            'university', 'college', 'institute', 'school',
            'tech', 'polytechnic', 'academy'
        ]
        text_lower = text.lower()
        return any(indicator in text_lower for indicator in university_indicators)
    
    def _get_canonical_university(self, text: str) -> Optional[str]:
        """Get canonical university name"""
        text_lower = text.lower().strip()
        return self.university_lookup.get(text_lower)
    
    def _get_canonical_program(self, text: str) -> Optional[str]:
        """Get canonical program name"""
        text_lower = text.lower().strip()
        return self.program_lookup.get(text_lower)
    
    def _merge_entities(self, target: Dict, source: Dict):
        """Merge entities from source into target"""
        for key in target:
            if key in source:
                target[key].extend(source[key])
    
    def _clean_entities(self, entities: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """Clean and deduplicate entities"""
        cleaned = {}
        for key, values in entities.items():
            # Remove duplicates while preserving order
            seen = set()
            cleaned_values = []
            for value in values:
                if value and value not in seen:
                    seen.add(value)
                    cleaned_values.append(value)
            cleaned[key] = cleaned_values

        return cleaned

    def _extract_program_from_context(self, context: str) -> Optional[str]:
        """Extract program type from context text"""
        context_lower = context.lower()

        # Look for program indicators
        program_indicators = [
            ('phd', 'PhD'),
            ('ph.d.', 'PhD'),
            ('doctorate', 'PhD'),
            ('doctoral', 'PhD'),
            ('master', 'Master'),
            ('masters', 'Master'),
            ('ms ', 'Master'),
            ('ma ', 'Master'),
            ('meng', 'Master'),
            ('msc', 'Master'),
            ('bachelor', 'Bachelor'),
            ('bachelors', 'Bachelor'),
            ('bs ', 'Bachelor'),
            ('ba ', 'Bachelor'),
            ('bsc', 'Bachelor'),
            ('undergraduate', 'Bachelor'),
            ('mba', 'MBA'),
            ('jd', 'JD'),
            ('md', 'MD'),
            ('postdoc', 'Postdoc'),
        ]

        for indicator, canonical in program_indicators:
            if indicator in context_lower:
                return canonical

        return None

    def _extract_with_openai(self, text: str) -> Dict[str, List[str]]:
        """Extract entities using OpenAI GPT"""
        entities = {'universities': [], 'majors': [], 'programs': []}

        try:
            import openai

            llm_config = self.extraction_config.get('llm', {})
            api_key = llm_config.get('api_key')

            if not api_key:
                log_message("OpenAI API key not configured")
                return entities

            client = openai.OpenAI(api_key=api_key)

            prompt = f"""
            Extract universities, academic majors, and degree programs from the following text.
            Return the result as JSON with keys: universities, majors, programs.
            Only include entities that are explicitly mentioned.

            Text: {text}

            JSON:
            """

            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0
            )

            result_text = response.choices[0].message.content

            # Parse JSON response
            import json
            try:
                result = json.loads(result_text)
                if isinstance(result, dict):
                    entities.update(result)
            except json.JSONDecodeError:
                log_message("Failed to parse OpenAI response as JSON")

        except ImportError:
            log_message("OpenAI library not installed")
        except Exception as e:
            log_message(f"OpenAI extraction error: {e}", "ERROR")

        return entities

    def _extract_with_anthropic(self, text: str) -> Dict[str, List[str]]:
        """Extract entities using Anthropic Claude"""
        entities = {'universities': [], 'majors': [], 'programs': []}

        try:
            import anthropic

            llm_config = self.extraction_config.get('llm', {})
            api_key = llm_config.get('api_key')

            if not api_key:
                log_message("Anthropic API key not configured")
                return entities

            client = anthropic.Anthropic(api_key=api_key)

            prompt = f"""
            Extract universities, academic majors, and degree programs from the following text.
            Return the result as JSON with keys: universities, majors, programs.
            Only include entities that are explicitly mentioned.

            Text: {text}

            JSON:
            """

            response = client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}]
            )

            result_text = response.content[0].text

            # Parse JSON response
            import json
            try:
                result = json.loads(result_text)
                if isinstance(result, dict):
                    entities.update(result)
            except json.JSONDecodeError:
                log_message("Failed to parse Anthropic response as JSON")

        except ImportError:
            log_message("Anthropic library not installed")
        except Exception as e:
            log_message(f"Anthropic extraction error: {e}", "ERROR")

        return entities
