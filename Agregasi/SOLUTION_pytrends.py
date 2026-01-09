# Alternative: Using PyTrends (free, faster than Apify scraping)
# Trade-off: Unofficial API, might break, less reliable

from pytrends.request import TrendReq
import pandas as pd

def fetch_from_pytrends(keyword: str) -> List[Dict[str, Any]]:
    """
    Fetch Google Trends data using PyTrends (unofficial API).
    
    Pros:
    - ✅ FREE (no Apify cost)
    - ✅ FAST (10-30s vs 60-180s)
    - ✅ Direct API calls (no browser scraping)
    
    Cons:
    - ❌ Unofficial (Google might block/change)
    - ❌ Rate limits (might get blocked)
    - ❌ Less reliable than Apify
    """
    pytrends = TrendReq(hl='id-ID', tz=420)  # Indonesia, UTC+7
    
    # Build payload
    pytrends.build_payload(
        [keyword],
        cat=0,
        timeframe='now 7-d',
        geo='ID',
        gprop=''
    )
    
    # Get hourly interest over time
    df = pytrends.get_historical_interest(
        [keyword],
        year_start=2026,
        month_start=1,
        day_start=2,
        hour_start=0,
        year_end=2026,
        month_end=1,
        day_end=9,
        hour_end=23,
        cat=0,
        geo='ID',
        gprop='',
        sleep=0
    )
    
    # Transform to our format
    timeline_data = []
    for idx, row in df.iterrows():
        timeline_data.append({
            "date": idx.isoformat(),
            "value": int(row[keyword]) if pd.notna(row[keyword]) else 0
        })
    
    return timeline_data

# Hybrid approach: Try PyTrends first, fallback to Apify
def fetch_trends_hybrid(keyword: str):
    """Try PyTrends first (fast), fallback to Apify (reliable)."""
    try:
        # Try PyTrends (10-30s)
        logger.info(f"Trying PyTrends for: {keyword}")
        data = fetch_from_pytrends(keyword)
        if data:
            return data, "pytrends"
    except Exception as e:
        logger.warning(f"PyTrends failed: {e}, falling back to Apify")
    
    # Fallback to Apify (60-180s but reliable)
    logger.info(f"Using Apify for: {keyword}")
    data, stats = fetch_from_apify(keyword)
    return data, "apify"
