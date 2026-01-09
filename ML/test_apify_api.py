"""
Quick test script untuk API dengan Apify real-time fetch
"""

import requests
import json
from datetime import datetime

# API base URL
BASE_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint"""
    print("\n" + "="*70)
    print("TEST 1: Health Check")
    print("="*70)
    
    response = requests.get(f"{BASE_URL}/api/v1/best-time/health")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    return response.status_code == 200

def test_categories():
    """Test list categories"""
    print("\n" + "="*70)
    print("TEST 2: List Categories")
    print("="*70)
    
    response = requests.get(f"{BASE_URL}/api/v1/best-time/categories")
    print(f"Status Code: {response.status_code}")
    print(f"Categories: {json.dumps(response.json(), indent=2)}")
    
    return response.status_code == 200

def test_predict(category="Food & Culinary"):
    """Test prediction endpoint with real-time Apify fetch"""
    print("\n" + "="*70)
    print(f"TEST 3: Predict Best Time (Real-time Apify)")
    print("="*70)
    
    payload = {
        "category": category,
        "window_hours": 3,
        "top_k": 3,
        "days_ahead": 7
    }
    
    print(f"\nRequest Payload:")
    print(json.dumps(payload, indent=2))
    
    print(f"\n⏳ Fetching real-time data from Google Trends via Apify...")
    print(f"   This may take 30-60 seconds...")
    
    start_time = datetime.now()
    response = requests.post(
        f"{BASE_URL}/api/v1/best-time/predict",
        json=payload,
        timeout=120  # 2 minutes timeout for Apify fetch
    )
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    print(f"\n✓ Request completed in {duration:.2f} seconds")
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"\nPrediction Results:")
        print(f"Category: {result['category']}")
        print(f"Model: {result['model_info']['model_type']} (R² = {result['model_info'].get('r2', 'N/A')})")
        print(f"\nTop 3 Best Posting Times:")
        print("-" * 70)
        
        for rec in result['recommendations']:
            print(f"#{rec['rank']} - {rec['day_name']}, {rec['date']}")
            print(f"     Time: {rec['time_window']}")
            print(f"     Confidence: {rec['confidence_score']:.1%}")
            print()
    else:
        print(f"Error: {response.text}")
    
    return response.status_code == 200

def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("APIFY REAL-TIME API TEST SUITE")
    print("="*70)
    print(f"Testing API at: {BASE_URL}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = []
    
    # Test 1: Health
    try:
        results.append(("Health Check", test_health()))
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        results.append(("Health Check", False))
    
    # Test 2: Categories
    try:
        results.append(("List Categories", test_categories()))
    except Exception as e:
        print(f"❌ Categories test failed: {e}")
        results.append(("List Categories", False))
    
    # Test 3: Prediction with Apify
    try:
        results.append(("Predict (Apify)", test_predict()))
    except Exception as e:
        print(f"❌ Prediction test failed: {e}")
        results.append(("Predict (Apify)", False))
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    total = len(results)
    passed = sum(1 for _, p in results if p)
    print(f"\nTotal: {passed}/{total} tests passed")
    print("="*70)

if __name__ == "__main__":
    main()
