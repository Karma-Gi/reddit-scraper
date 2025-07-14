"""
Smart labeling analyzer using AI models for accurate scoring
Analyzes application difficulty, course evaluation, and sentiment
"""

import re
import json
from typing import Dict, List, Optional, Tuple, Any
import logging

try:
    from .utils import load_config, log_message
except ImportError:
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent))
    from utils import load_config, log_message


class SmartLabelingAnalyzer:
    """AI-powered labeling analyzer for study abroad content"""
    
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize the smart labeling analyzer"""
        self.config = load_config(config_path)
        self.labeling_config = self.config.get('smart_labeling', {})
        
        # Initialize models
        self.sentiment_analyzer = None
        self.text_classifier = None
        self.llm_client = None
        
        self._initialize_models()
        self._load_analysis_patterns()
    
    def _initialize_models(self):
        """Initialize AI models based on configuration"""
        methods = self.labeling_config.get('methods', ['textblob'])
        
        # Initialize TextBlob for basic sentiment
        if 'textblob' in methods:
            try:
                from textblob import TextBlob
                self.textblob_available = True
                log_message("✅ TextBlob sentiment analyzer loaded")
            except ImportError:
                self.textblob_available = False
                log_message("⚠️  TextBlob not available")

        # Initialize VADER sentiment analyzer
        if 'vader' in methods:
            try:
                from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
                self.vader_analyzer = SentimentIntensityAnalyzer()
                log_message("✅ VADER sentiment analyzer loaded")
            except ImportError:
                self.vader_analyzer = None
                log_message("⚠️  VADER sentiment not available")
        
        # Initialize Transformers for advanced analysis
        if 'transformers' in methods:
            try:
                from transformers import pipeline
                import torch

                # Check PyTorch version
                torch_version = torch.__version__
                log_message(f"PyTorch version: {torch_version}")

                # Try multiple models in order of preference
                models_to_try = [
                    "distilbert-base-uncased-finetuned-sst-2-english",  # Most compatible
                    "cardiffnlp/twitter-roberta-base-sentiment-latest",
                    "nlptown/bert-base-multilingual-uncased-sentiment"
                ]

                for model_name in models_to_try:
                    try:
                        log_message(f"Attempting to load model: {model_name}")
                        self.sentiment_analyzer = pipeline(
                            "sentiment-analysis",
                            model=model_name,
                            return_all_scores=False
                        )
                        log_message(f"✅ Successfully loaded sentiment model: {model_name}")
                        break
                    except Exception as e:
                        error_msg = str(e)
                        if "torch.load" in error_msg and "v2.6" in error_msg:
                            log_message(f"⚠️  PyTorch version too old for {model_name}")
                        else:
                            log_message(f"⚠️  Failed to load {model_name}: {error_msg[:100]}...")
                        continue
                else:
                    self.sentiment_analyzer = None
                    log_message("❌ All transformer models failed to load")
                    log_message("💡 Consider upgrading PyTorch: pip install torch>=2.6.0")

            except ImportError:
                log_message("⚠️  Transformers not available")
        
        # Initialize LLM client if configured
        if 'llm' in methods:
            self._initialize_llm()
    
    def _initialize_llm(self):
        """Initialize LLM client for advanced analysis"""
        llm_config = self.labeling_config.get('llm', {})
        if not llm_config.get('enabled', False):
            return
        
        provider = llm_config.get('provider', 'openai')
        
        try:
            if provider == 'openai':
                import openai
                api_key = llm_config.get('api_key')
                if api_key:
                    self.llm_client = openai.OpenAI(api_key=api_key)
                    self.llm_provider = 'openai'
                    log_message("✅ OpenAI client initialized")
            elif provider == 'anthropic':
                import anthropic
                api_key = llm_config.get('api_key')
                if api_key:
                    self.llm_client = anthropic.Anthropic(api_key=api_key)
                    self.llm_provider = 'anthropic'
                    log_message("✅ Anthropic client initialized")
        except ImportError as e:
            log_message(f"⚠️  LLM client not available: {e}")
    
    def _load_analysis_patterns(self):
        """Load patterns for rule-based analysis"""
        # Enhanced difficulty indicators with more academic terms
        self.difficulty_patterns = {
            '极难': [
                r'impossible', r'extremely hard', r'nearly impossible', r'extremely competitive',
                r'rejection rate.*9[0-9]%', r'acceptance rate.*[0-5]%',
                r'top 1%', r'elite', r'most competitive', r'ivy league',
                r'harvard', r'mit', r'stanford', r'princeton', r'yale',
                r'dream school', r'reach school', r'super competitive',
                r'got rejected.*high gpa', r'perfect.*still rejected'
            ],
            '难': [
                r'very hard', r'difficult', r'competitive', r'challenging', r'tough',
                r'rejection rate.*[7-8][0-9]%', r'acceptance rate.*[1-2][0-9]%',
                r'top 10%', r'highly selective', r'selective',
                r'berkeley', r'ucla', r'michigan', r'carnegie mellon',
                r'hard to get in', r'very competitive', r'need high gpa',
                r'requires.*research', r'need.*experience'
            ],
            '中等': [
                r'moderate', r'average', r'reasonable', r'manageable', r'decent chance',
                r'acceptance rate.*[3-6][0-9]%', r'middle tier', r'target school',
                r'good chance', r'reasonable expectations', r'match school',
                r'state school', r'public university'
            ],
            '易': [
                r'easy', r'simple', r'not hard', r'accessible', r'easy to get in',
                r'acceptance rate.*[7-9][0-9]%', r'safety school', r'backup',
                r'guaranteed admission', r'open admission', r'community college',
                r'sure thing', r'easy acceptance'
            ]
        }
        
        # Course evaluation indicators
        self.course_patterns = {
            '优秀': [
                r'excellent', r'outstanding', r'amazing', r'fantastic',
                r'best.*program', r'top.*course', r'highly recommend'
            ],
            '良好': [
                r'good', r'solid', r'decent', r'satisfactory',
                r'recommend', r'worth it'
            ],
            '一般': [
                r'okay', r'average', r'mediocre', r'so-so',
                r'not bad', r'could be better'
            ],
            '差': [
                r'bad', r'terrible', r'awful', r'disappointing',
                r'waste of time', r'not recommend', r'avoid'
            ]
        }
        
        # Sentiment indicators
        self.sentiment_patterns = {
            '积极': [
                r'excited', r'happy', r'thrilled', r'grateful',
                r'love', r'amazing', r'wonderful', r'perfect'
            ],
            '消极': [
                r'disappointed', r'frustrated', r'worried', r'stressed',
                r'hate', r'terrible', r'awful', r'regret'
            ],
            '中性': [
                r'neutral', r'objective', r'factual', r'information'
            ]
        }
    
    def analyze_comprehensive(self, text: str, post_id: Optional[str] = None) -> Dict[str, Any]:
        """Comprehensive analysis using multiple methods"""
        results = {
            'difficulty_label': None,
            'difficulty_score': 0.0,
            'course_label': None,
            'course_score': 0.0,
            'sentiment_label': None,
            'sentiment_score': 0.0,
            'confidence': 0.0,
            'method_used': []
        }
        
        methods = self.labeling_config.get('methods', ['pattern'])
        
        # Method 1: Pattern-based analysis
        if 'pattern' in methods:
            pattern_results = self._analyze_with_patterns(text)
            self._merge_results(results, pattern_results, 'pattern')
        
        # Method 2: TextBlob sentiment
        if 'textblob' in methods and self.textblob_available:
            textblob_results = self._analyze_with_textblob(text)
            self._merge_results(results, textblob_results, 'textblob')

        # Method 3: VADER sentiment
        if 'vader' in methods and hasattr(self, 'vader_analyzer') and self.vader_analyzer:
            vader_results = self._analyze_with_vader(text)
            self._merge_results(results, vader_results, 'vader')

        # Method 4: Transformers models
        if 'transformers' in methods and self.sentiment_analyzer:
            transformer_results = self._analyze_with_transformers(text)
            self._merge_results(results, transformer_results, 'transformers')
        
        # Method 4: LLM analysis (most accurate)
        if 'llm' in methods and self.llm_client:
            llm_results = self._analyze_with_llm(text)
            self._merge_results(results, llm_results, 'llm')
        
        # Apply academic domain adjustments
        results = self._apply_academic_adjustments(results, text)

        # Calculate final confidence
        results['confidence'] = self._calculate_confidence(results)

        return results

    def _apply_academic_adjustments(self, results: Dict[str, Any], text: str) -> Dict[str, Any]:
        """Apply domain-specific adjustments for academic content"""
        text_lower = text.lower()

        # Boost difficulty scores for top universities
        top_universities = ['harvard', 'mit', 'stanford', 'princeton', 'yale', 'caltech']
        if any(uni in text_lower for uni in top_universities):
            if results['difficulty_score'] < 8.0:
                results['difficulty_score'] = min(results['difficulty_score'] + 1.5, 10.0)
                results['difficulty_label'] = '极难' if results['difficulty_score'] >= 8.5 else '难'

        # Boost course scores for positive academic terms
        positive_academic = ['excellent program', 'outstanding', 'top-tier', 'world-class', 'prestigious']
        if any(term in text_lower for term in positive_academic):
            if results['course_score'] < 8.0:
                results['course_score'] = min(results['course_score'] + 1.0, 10.0)
                results['course_label'] = '优秀' if results['course_score'] >= 8.0 else '良好'

        # Adjust sentiment for academic stress indicators
        stress_indicators = ['stressful', 'overwhelming', 'burned out', 'exhausted', 'pressure']
        if any(indicator in text_lower for indicator in stress_indicators):
            if results['sentiment_score'] > 4.0:
                results['sentiment_score'] = max(results['sentiment_score'] - 1.5, 0.0)
                if results['sentiment_score'] <= 3.0:
                    results['sentiment_label'] = '消极'

        # Boost positive sentiment for success stories
        success_indicators = ['got accepted', 'admitted', 'got in', 'accepted to', 'dream school']
        if any(indicator in text_lower for indicator in success_indicators):
            if results['sentiment_score'] < 7.0:
                results['sentiment_score'] = min(results['sentiment_score'] + 2.0, 10.0)
                results['sentiment_label'] = '积极'

        return results
    
    def _analyze_with_patterns(self, text: str) -> Dict[str, Any]:
        """Pattern-based analysis using regex"""
        text_lower = text.lower()
        results = {
            'difficulty_label': None,
            'difficulty_score': 0.5,
            'course_label': None,
            'course_score': 0.5,
            'sentiment_label': None,
            'sentiment_score': 0.5
        }
        
        # Analyze difficulty
        difficulty_scores = {}
        for label, patterns in self.difficulty_patterns.items():
            score = 0
            for pattern in patterns:
                matches = len(re.findall(pattern, text_lower))
                score += matches
            if score > 0:
                difficulty_scores[label] = score
        
        if difficulty_scores:
            best_difficulty = max(difficulty_scores, key=difficulty_scores.get)
            results['difficulty_label'] = best_difficulty
            results['difficulty_score'] = self._label_to_score(best_difficulty, 'difficulty')
        
        # Analyze course quality
        course_scores = {}
        for label, patterns in self.course_patterns.items():
            score = 0
            for pattern in patterns:
                matches = len(re.findall(pattern, text_lower))
                score += matches
            if score > 0:
                course_scores[label] = score
        
        if course_scores:
            best_course = max(course_scores, key=course_scores.get)
            results['course_label'] = best_course
            results['course_score'] = self._label_to_score(best_course, 'course')
        
        # Analyze sentiment
        sentiment_scores = {}
        for label, patterns in self.sentiment_patterns.items():
            score = 0
            for pattern in patterns:
                matches = len(re.findall(pattern, text_lower))
                score += matches
            if score > 0:
                sentiment_scores[label] = score
        
        if sentiment_scores:
            best_sentiment = max(sentiment_scores, key=sentiment_scores.get)
            results['sentiment_label'] = best_sentiment
            results['sentiment_score'] = self._label_to_score(best_sentiment, 'sentiment')
        
        return results
    
    def _analyze_with_textblob(self, text: str) -> Dict[str, Any]:
        """TextBlob-based sentiment analysis"""
        try:
            from textblob import TextBlob
            
            blob = TextBlob(text)
            polarity = blob.sentiment.polarity  # -1 to 1
            
            # Convert polarity to our scale
            sentiment_score = (polarity + 1) / 2 * 10  # 0-10 scale
            
            # Determine sentiment label
            if polarity > 0.1:
                sentiment_label = '积极'
            elif polarity < -0.1:
                sentiment_label = '消极'
            else:
                sentiment_label = '中性'
            
            return {
                'sentiment_label': sentiment_label,
                'sentiment_score': sentiment_score,
                'difficulty_label': None,
                'difficulty_score': 5.0,
                'course_label': None,
                'course_score': 5.0
            }
            
        except Exception as e:
            log_message(f"TextBlob analysis error: {e}", "ERROR")
            return {}

    def _analyze_with_vader(self, text: str) -> Dict[str, Any]:
        """VADER-based sentiment analysis"""
        try:
            if not self.vader_analyzer:
                return {}

            scores = self.vader_analyzer.polarity_scores(text)
            compound_score = scores['compound']  # -1 to 1

            # Convert compound score to our scale
            sentiment_score = (compound_score + 1) / 2 * 10  # 0-10 scale

            # Determine sentiment label based on VADER thresholds
            if compound_score >= 0.05:
                sentiment_label = '积极'
            elif compound_score <= -0.05:
                sentiment_label = '消极'
            else:
                sentiment_label = '中性'

            return {
                'sentiment_label': sentiment_label,
                'sentiment_score': sentiment_score,
                'difficulty_label': None,
                'difficulty_score': 5.0,
                'course_label': None,
                'course_score': 5.0
            }

        except Exception as e:
            log_message(f"VADER analysis error: {e}", "ERROR")
            return {}
    
    def _analyze_with_transformers(self, text: str) -> Dict[str, Any]:
        """Transformers-based sentiment analysis"""
        try:
            if not self.sentiment_analyzer:
                return {}
            
            # Truncate text if too long
            if len(text) > 512:
                text = text[:512]
            
            result = self.sentiment_analyzer(text)[0]
            label = result['label'].upper()
            confidence = result['score']
            
            # Enhanced mapping with more aggressive scoring
            if label in ['POSITIVE', 'POS']:
                sentiment_label = '积极'
                # More aggressive positive scoring
                sentiment_score = 6 + (confidence * 4)  # 6-10 scale
            elif label in ['NEGATIVE', 'NEG']:
                sentiment_label = '消极'
                # More aggressive negative scoring
                sentiment_score = 4 - (confidence * 4)  # 0-4 scale
            else:
                sentiment_label = '中性'
                sentiment_score = 5.0
            
            return {
                'sentiment_label': sentiment_label,
                'sentiment_score': sentiment_score,
                'difficulty_label': None,
                'difficulty_score': 5.0,
                'course_label': None,
                'course_score': 5.0
            }
            
        except Exception as e:
            log_message(f"Transformers analysis error: {e}", "ERROR")
            return {}
    
    def _analyze_with_llm(self, text: str) -> Dict[str, Any]:
        """LLM-based comprehensive analysis"""
        try:
            if not self.llm_client:
                return {}
            
            prompt = f"""
            分析以下留学相关文本的三个维度，并给出评分：

            文本: {text}

            请分析：
            1. 申请难度 (极难/难/中等/易) 和评分 (0-10，10最难)
            2. 课程评价 (优秀/良好/一般/差) 和评分 (0-10，10最好)  
            3. 情感倾向 (积极/消极/中性) 和评分 (0-10，10最积极)

            返回JSON格式:
            {{
                "difficulty_label": "难度标签",
                "difficulty_score": 数字评分,
                "course_label": "课程标签", 
                "course_score": 数字评分,
                "sentiment_label": "情感标签",
                "sentiment_score": 数字评分,
                "reasoning": "分析理由"
            }}
            """
            
            if self.llm_provider == 'openai':
                response = self.llm_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=500,
                    temperature=0.1
                )
                result_text = response.choices[0].message.content
                
            elif self.llm_provider == 'anthropic':
                response = self.llm_client.messages.create(
                    model="claude-3-sonnet-20240229",
                    max_tokens=500,
                    messages=[{"role": "user", "content": prompt}]
                )
                result_text = response.content[0].text
            
            # Parse JSON response
            try:
                result = json.loads(result_text)
                return {
                    'difficulty_label': result.get('difficulty_label'),
                    'difficulty_score': float(result.get('difficulty_score', 5.0)),
                    'course_label': result.get('course_label'),
                    'course_score': float(result.get('course_score', 5.0)),
                    'sentiment_label': result.get('sentiment_label'),
                    'sentiment_score': float(result.get('sentiment_score', 5.0)),
                    'reasoning': result.get('reasoning', '')
                }
            except json.JSONDecodeError:
                log_message("Failed to parse LLM response as JSON")
                return {}
                
        except Exception as e:
            log_message(f"LLM analysis error: {e}", "ERROR")
            return {}
    
    def _label_to_score(self, label: str, category: str) -> float:
        """Convert label to numerical score with enhanced ranges"""
        if category == 'difficulty':
            # More spread out difficulty scoring
            mapping = {'极难': 9.5, '难': 7.5, '中等': 5.0, '易': 2.5}
        elif category == 'course':
            # More spread out course quality scoring
            mapping = {'优秀': 9.0, '良好': 7.5, '一般': 5.0, '差': 2.5}
        elif category == 'sentiment':
            # More extreme sentiment scoring
            mapping = {'积极': 8.5, '中性': 5.0, '消极': 1.5}
        else:
            return 5.0

        return mapping.get(label, 5.0)
    
    def _merge_results(self, target: Dict, source: Dict, method: str):
        """Merge analysis results with weighted averaging"""
        if not source:
            return

        target['method_used'].append(method)

        # Adjusted weights - pattern matching is crucial for academic content
        weights = {
            'pattern': 0.7,      # Higher weight for domain-specific patterns
            'textblob': 0.4,
            'vader': 0.5,
            'transformers': 0.6,  # Reduced weight due to conservative bias
            'llm': 1.0
        }

        weight = weights.get(method, 0.5)
        
        # Merge scores with weighted average
        for key in ['difficulty_score', 'course_score', 'sentiment_score']:
            if key in source and source[key] is not None:
                if target[key] == 0.0:
                    target[key] = source[key] * weight
                else:
                    target[key] = (target[key] + source[key] * weight) / 2
        
        # Update labels (prefer higher-weight methods)
        for key in ['difficulty_label', 'course_label', 'sentiment_label']:
            if key in source and source[key] is not None:
                if not target[key] or weight > 0.5:
                    target[key] = source[key]
    
    def _calculate_confidence(self, results: Dict) -> float:
        """Calculate confidence score based on methods used and consistency"""
        methods_used = len(results['method_used'])
        
        # Base confidence from number of methods
        base_confidence = min(methods_used * 0.25, 1.0)
        
        # Bonus for high-quality methods
        if 'llm' in results['method_used']:
            base_confidence += 0.3
        if 'transformers' in results['method_used']:
            base_confidence += 0.2
        
        return min(base_confidence, 1.0)
