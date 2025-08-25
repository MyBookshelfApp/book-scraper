#!/usr/bin/env python3
"""
Test script to verify imports work correctly
"""
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all imports work correctly"""
    print("🧪 Testing imports...")
    
    try:
        # Test basic imports
        from app.config import settings
        print("✅ Config imported successfully")
        
        from app.models.book import Book, BookSource
        print("✅ Book models imported successfully")
        
        from app.core.scraper_engine import ScraperEngine
        print("✅ Scraper engine imported successfully")
        
        from app.api.routes import router
        print("✅ API routes imported successfully")
        
        from app.dependencies import get_scraper_engine, set_scraper_engine
        print("✅ Dependencies imported successfully")
        
        from app.main import app
        print("✅ Main app imported successfully")
        
        print("\n🎉 All imports successful! No circular import issues.")
        return True
        
    except Exception as e:
        print(f"\n❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1) 