#!/usr/bin/env python3
"""
Setup script for smart entity extraction models
"""

import subprocess
import sys
import os
from pathlib import Path


def install_package(package):
    """Install a Python package"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        return True
    except subprocess.CalledProcessError:
        return False


def download_spacy_model():
    """Download spaCy English model"""
    try:
        subprocess.check_call([sys.executable, "-m", "spacy", "download", "en_core_web_sm"])
        return True
    except subprocess.CalledProcessError:
        return False


def test_imports():
    """Test if all required packages can be imported"""
    packages = {
        'spacy': 'spaCy',
        'transformers': 'Transformers',
        'sentence_transformers': 'Sentence Transformers',
        'torch': 'PyTorch',
    }
    
    results = {}
    for package, name in packages.items():
        try:
            __import__(package)
            results[name] = True
            print(f"✅ {name} - OK")
        except ImportError:
            results[name] = False
            print(f"❌ {name} - Not installed")
    
    return results


def test_spacy_model():
    """Test if spaCy model is available"""
    try:
        import spacy
        nlp = spacy.load("en_core_web_sm")
        print("✅ spaCy en_core_web_sm model - OK")
        return True
    except OSError:
        print("❌ spaCy en_core_web_sm model - Not found")
        return False
    except ImportError:
        print("❌ spaCy - Not installed")
        return False


def test_sentence_transformer():
    """Test sentence transformer model"""
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer('all-MiniLM-L6-v2')
        print("✅ Sentence Transformer model - OK")
        return True
    except Exception as e:
        print(f"❌ Sentence Transformer model - Error: {e}")
        return False


def main():
    """Main setup function"""
    print("🤖 SMART ENTITY EXTRACTION SETUP")
    print("=" * 50)
    
    print("\n📦 STEP 1: Installing required packages...")
    
    # Core NLP packages
    packages = [
        "spacy>=3.7.0",
        "transformers>=4.35.0",
        "torch>=2.0.0",
        "sentence-transformers>=2.2.0",
    ]
    
    for package in packages:
        print(f"Installing {package}...")
        if install_package(package):
            print(f"✅ {package} installed successfully")
        else:
            print(f"❌ Failed to install {package}")
    
    print("\n📥 STEP 2: Downloading spaCy model...")
    if download_spacy_model():
        print("✅ spaCy model downloaded successfully")
    else:
        print("❌ Failed to download spaCy model")
        print("   Try manually: python -m spacy download en_core_web_sm")
    
    print("\n🧪 STEP 3: Testing installations...")
    import_results = test_imports()
    spacy_model_ok = test_spacy_model()
    sentence_transformer_ok = test_sentence_transformer()
    
    print("\n📊 SETUP SUMMARY:")
    print("=" * 30)
    
    all_good = True
    
    if all(import_results.values()):
        print("✅ All packages installed successfully")
    else:
        print("❌ Some packages failed to install")
        all_good = False
    
    if spacy_model_ok:
        print("✅ spaCy model ready")
    else:
        print("❌ spaCy model not available")
        all_good = False
    
    if sentence_transformer_ok:
        print("✅ Sentence transformer ready")
    else:
        print("❌ Sentence transformer not available")
        all_good = False
    
    print("\n🔧 CONFIGURATION:")
    if all_good:
        print("✅ Smart extraction is ready to use!")
        print("   Set 'smart_extraction.enabled: true' in config.yaml")
        print("\n   Available methods:")
        print("   - spacy: Named Entity Recognition")
        print("   - keyword: Enhanced keyword matching")
        print("   - pattern: Regex pattern matching")
        print("   - semantic: Semantic similarity matching")
    else:
        print("⚠️  Some components are missing")
        print("   Smart extraction will fall back to keyword matching")
        print("   You can still use basic functionality")
    
    print("\n🧪 NEXT STEPS:")
    print("1. Test smart extraction:")
    print("   python test_smart_extraction.py")
    print("\n2. Run data processing:")
    print("   python main.py --process")
    print("\n3. Check extraction results:")
    print("   python main.py --stats")
    
    if not all_good:
        print("\n🔧 TROUBLESHOOTING:")
        print("If installation failed, try:")
        print("1. Update pip: python -m pip install --upgrade pip")
        print("2. Install PyTorch separately: pip install torch")
        print("3. Install packages one by one")
        print("4. Use conda instead of pip for some packages")


if __name__ == "__main__":
    main()
