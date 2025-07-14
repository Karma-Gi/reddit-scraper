#!/usr/bin/env python3
"""
Test smart entity extraction functionality
"""

import sys
from pathlib import Path

# Add src directory to path
sys.path.append(str(Path(__file__).parent / "src"))

from src.smart_entity_extractor import SmartEntityExtractor
from src.data_processor import DataProcessor
from src.utils import load_config


def test_sample_texts():
    """Test smart extraction on sample texts"""
    print("🧪 TESTING SMART ENTITY EXTRACTION")
    print("=" * 50)
    
    # Sample texts from Reddit study abroad posts
    test_texts = [
        "I'm applying to MIT and Stanford for Computer Science PhD. My GPA is 3.8, any advice?",
        
        "Got accepted to Harvard for MBA program! Also considering Wharton and Kellogg.",
        
        "Looking for MS in Machine Learning. Considering CMU, UC Berkeley, and Georgia Tech.",
        
        "International student applying to US universities for Electrical Engineering PhD. Target schools: Caltech, Princeton, Cornell.",
        
        "Anyone know about the Data Science program at NYU? Also looking at Columbia and UChicago.",
        
        "Rejected from Stanford CS but got into UIUC and UT Austin. Should I take a gap year and reapply?",
        
        "Biomedical Engineering undergrad looking for PhD programs. Interested in Johns Hopkins, Duke, and Rice.",
        
        "MBA vs MS in Finance? Looking at Northwestern Kellogg, UPenn Wharton, and MIT Sloan.",
        
        "Got into Oxford for Economics PhD! Also considering Cambridge and LSE.",
        
        "Chemical Engineering MS programs: which is better - University of Washington or UCSD?"
    ]
    
    try:
        extractor = SmartEntityExtractor()
        
        print("Testing extraction methods...")
        
        for i, text in enumerate(test_texts, 1):
            print(f"\n📝 Test {i}:")
            print(f"Text: {text}")
            
            entities = extractor.extract_entities_smart(text)
            
            print("🏫 Universities:", entities.get('universities', []))
            print("📚 Majors:", entities.get('majors', []))
            print("🎓 Programs:", entities.get('programs', []))
            
            # Calculate extraction score
            total_entities = sum(len(v) for v in entities.values())
            print(f"📊 Total entities found: {total_entities}")
            
            if total_entities == 0:
                print("⚠️  No entities extracted!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in smart extraction test: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_data_processor_integration():
    """Test integration with data processor"""
    print("\n🔗 TESTING DATA PROCESSOR INTEGRATION")
    print("=" * 50)
    
    try:
        processor = DataProcessor()
        
        # Test text
        test_text = "I'm a CS undergrad applying to MIT, Stanford, and CMU for PhD in Machine Learning. My research is in AI and I have publications."
        
        print(f"Test text: {test_text}")
        
        # Test entity extraction
        entities = processor.extract_entities(test_text)
        
        print("\n📊 Extraction Results:")
        print(f"🏫 Universities: {entities.get('universities', [])}")
        print(f"📚 Majors: {entities.get('majors', [])}")
        print(f"🎓 Programs: {entities.get('programs', [])}")
        
        # Check if smart extraction is being used
        if hasattr(processor, 'smart_extractor') and processor.smart_extractor:
            print("✅ Using smart extraction")
        else:
            print("⚠️  Using fallback keyword extraction")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in data processor integration test: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_configuration():
    """Test configuration settings"""
    print("\n⚙️ TESTING CONFIGURATION")
    print("=" * 30)
    
    try:
        config = load_config()
        smart_config = config.get('smart_extraction', {})
        
        print(f"Smart extraction enabled: {smart_config.get('enabled', False)}")
        print(f"Methods: {smart_config.get('methods', [])}")
        print(f"Sentence model: {smart_config.get('sentence_model', 'N/A')}")
        
        if smart_config.get('enabled', False):
            print("✅ Smart extraction is configured")
        else:
            print("⚠️  Smart extraction is disabled")
            print("   Enable it in config.yaml: smart_extraction.enabled: true")
        
        return True
        
    except Exception as e:
        print(f"❌ Error reading configuration: {e}")
        return False


def test_model_availability():
    """Test if required models are available"""
    print("\n🤖 TESTING MODEL AVAILABILITY")
    print("=" * 40)
    
    models_status = {}
    
    # Test spaCy
    try:
        import spacy
        nlp = spacy.load("en_core_web_sm")
        models_status['spaCy'] = True
        print("✅ spaCy en_core_web_sm - Available")
    except Exception as e:
        models_status['spaCy'] = False
        print(f"❌ spaCy - Error: {e}")
    
    # Test sentence transformers
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer('all-MiniLM-L6-v2')
        models_status['SentenceTransformer'] = True
        print("✅ Sentence Transformer - Available")
    except Exception as e:
        models_status['SentenceTransformer'] = False
        print(f"❌ Sentence Transformer - Error: {e}")
    
    # Test transformers
    try:
        from transformers import pipeline
        models_status['Transformers'] = True
        print("✅ Transformers - Available")
    except Exception as e:
        models_status['Transformers'] = False
        print(f"❌ Transformers - Error: {e}")
    
    return models_status


def compare_extraction_methods():
    """Compare different extraction methods"""
    print("\n⚖️ COMPARING EXTRACTION METHODS")
    print("=" * 40)
    
    test_text = "I got into MIT for Computer Science PhD and Stanford for MS in AI. Also considering CMU and UC Berkeley."
    
    try:
        # Test with smart extractor
        extractor = SmartEntityExtractor()
        smart_entities = extractor.extract_entities_smart(test_text)
        
        # Test with basic processor (fallback)
        processor = DataProcessor()
        basic_entities = processor._extract_entities_keyword(test_text)
        
        print(f"Test text: {test_text}")
        
        print("\n🤖 Smart Extraction Results:")
        for key, values in smart_entities.items():
            print(f"  {key}: {values}")
        
        print("\n🔤 Keyword Extraction Results:")
        for key, values in basic_entities.items():
            print(f"  {key}: {values}")
        
        # Compare results
        print("\n📊 Comparison:")
        for key in smart_entities:
            smart_count = len(smart_entities[key])
            basic_count = len(basic_entities[key])
            print(f"  {key}: Smart={smart_count}, Keyword={basic_count}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in comparison: {e}")
        return False


def main():
    """Main test function"""
    print("🧪 SMART ENTITY EXTRACTION TEST SUITE")
    print("=" * 60)
    
    # Test configuration
    config_ok = test_configuration()
    
    # Test model availability
    models_status = test_model_availability()
    
    # Test sample texts
    if any(models_status.values()):
        sample_ok = test_sample_texts()
        integration_ok = test_data_processor_integration()
        comparison_ok = compare_extraction_methods()
    else:
        print("\n⚠️  No models available, skipping extraction tests")
        sample_ok = integration_ok = comparison_ok = False
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 TEST SUMMARY:")
    
    if config_ok:
        print("✅ Configuration - OK")
    else:
        print("❌ Configuration - Failed")
    
    available_models = sum(models_status.values())
    total_models = len(models_status)
    print(f"🤖 Models - {available_models}/{total_models} available")
    
    if available_models > 0:
        if sample_ok:
            print("✅ Sample extraction - OK")
        else:
            print("❌ Sample extraction - Failed")
        
        if integration_ok:
            print("✅ Integration - OK")
        else:
            print("❌ Integration - Failed")
        
        if comparison_ok:
            print("✅ Method comparison - OK")
        else:
            print("❌ Method comparison - Failed")
    
    print("\n🚀 RECOMMENDATIONS:")
    
    if available_models == 0:
        print("❌ No models available!")
        print("   Run: python setup_smart_extraction.py")
    elif available_models < total_models:
        print("⚠️  Some models missing")
        print("   Install missing models for better performance")
    else:
        print("✅ All models available!")
        print("   Smart extraction is ready to use")
    
    if config_ok and available_models > 0:
        print("\n🎯 NEXT STEPS:")
        print("1. Run data processing: python main.py --process")
        print("2. Check results: python main.py --stats")
        print("3. View extracted data: python main.py --view")


if __name__ == "__main__":
    main()
