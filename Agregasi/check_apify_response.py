# Test script untuk check Apify response structure
# Run: python check_apify_response.py

import os
from apify_client import ApifyClient
from dotenv import load_dotenv
import json

load_dotenv()

client = ApifyClient(os.getenv("APIFY_TOKEN"))

print("🔍 Testing Apify Google Trends Scraper response...")
print("=" * 60)

# Use real-world keyword for testing
test_keyword = "skincare"  # Real viral keyword to test actual performance
print(f"📝 Test keyword: '{test_keyword}' (viral keyword - real-world test)")

run = client.actor("apify/google-trends-scraper").call(
    run_input={
        "searchTerms": [test_keyword],
        "timeRange": "now 7-d",
        "geo": "ID",
        "isPublic": False,  # Private dataset
    },
    memory_mbytes=4096,  # High memory for viral keywords
    timeout_secs=600,  # 10 min timeout for slow fetches
)

print(f"\n✅ Run completed: {run['id']}")
print(f"📊 Dataset ID: {run['defaultDatasetId']}")
print(f"⏱️  Duration: {run.get('stats', {}).get('durationMillis', 0)}ms")

# Get all dataset items
dataset_items = list(client.dataset(run["defaultDatasetId"]).iterate_items())

print(f"\n📦 Total items in dataset: {len(dataset_items)}")

if dataset_items:
    print("\n🔑 Keys in first item:")
    first_item = dataset_items[0]
    for key in first_item.keys():
        print(f"  - {key}")
    
    print("\n� TIMEZONE VERIFICATION:")
    if "interestOverTime_timelineData" in first_item:
        sample = first_item["interestOverTime_timelineData"][0]
        unix_ts = int(sample.get("time", 0))
        formatted = sample.get("formattedTime", "")
        
        from datetime import datetime
        import pytz
        
        # Convert Unix timestamp to UTC then WIB
        utc_dt = datetime.utcfromtimestamp(unix_ts)
        utc_tz = pytz.UTC
        wib_tz = pytz.timezone('Asia/Jakarta')
        utc_aware = utc_tz.localize(utc_dt)
        wib_dt = utc_aware.astimezone(wib_tz)
        
        print(f"  Unix timestamp: {unix_ts}")
        print(f"  → UTC:  {utc_dt.strftime('%Y-%m-%d %H:%M:%S')} ({utc_dt.strftime('%I:%M %p')} UTC)")
        print(f"  → WIB:  {wib_dt.strftime('%Y-%m-%d %H:%M:%S')} ({wib_dt.strftime('%I:%M %p')} WIB)")
        print(f"  Apify formattedTime: '{formatted}'")
        
        # Check if formattedTime matches UTC or WIB
        if formatted:
            if f"{utc_dt.hour % 12 or 12}" in formatted or f"{utc_dt.hour}:00" in formatted:
                print(f"  ✅ formattedTime matches UTC time")
            elif f"{wib_dt.hour % 12 or 12}" in formatted or f"{wib_dt.hour}:00" in formatted:
                print(f"  ⚠️  formattedTime matches WIB time (already converted!)")
                print(f"  💡 Use formattedTime directly, don't convert again!")
    
    print("\n�📄 Full first item structure:")
    print(json.dumps(first_item, indent=2, default=str)[:2000])  # First 2000 chars
    
    # Check for different possible keys
    print("\n🔍 Looking for timeline data in:")
    possible_keys = [
        "timelineData",
        "timeline",
        "data",
        "interestOverTime",
        "hourlyInterestOverTime",
        "averagesByHours"
    ]
    
    for key in possible_keys:
        if key in first_item:
            print(f"  ✅ Found: {key}")
            if isinstance(first_item[key], list):
                print(f"     Length: {len(first_item[key])} items")
                if first_item[key]:
                    print(f"     Sample: {first_item[key][0]}")
        else:
            print(f"  ❌ Not found: {key}")
else:
    print("⚠️  No items in dataset!")

print("\n" + "=" * 60)
print("💡 Recommendation: Update services.py based on actual keys found above")
