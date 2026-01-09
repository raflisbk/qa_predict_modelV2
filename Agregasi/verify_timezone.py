# Verify timezone dari Apify response
# Run: python verify_timezone.py

from datetime import datetime
import pytz

# Data dari output sebelumnya
unix_timestamp = 1767369600
formatted_time = "Jan 2, 2026 at 4:00 PM"

print("🕐 Timezone Verification")
print("=" * 60)

# Convert Unix timestamp (ALWAYS UTC)
utc_dt = datetime.utcfromtimestamp(unix_timestamp)
print(f"\n📅 Unix timestamp: {unix_timestamp}")
print(f"   → UTC:  {utc_dt.strftime('%Y-%m-%d %H:%M:%S')} UTC")

# Convert to WIB (UTC+7)
utc_tz = pytz.UTC
wib_tz = pytz.timezone('Asia/Jakarta')
utc_aware = utc_tz.localize(utc_dt)
wib_dt = utc_aware.astimezone(wib_tz)
print(f"   → WIB:  {wib_dt.strftime('%Y-%m-%d %H:%M:%S')} WIB")

# Parse formattedTime dari Apify
print(f"\n🏷️  Apify formattedTime: '{formatted_time}'")
print(f"   Shows: 4:00 PM")

print("\n🔍 Analysis:")
if wib_dt.hour == 23:  # 11 PM in 24h
    print("   ✅ formattedTime is UTC (16:00 UTC = 4:00 PM UTC)")
    print("   ✅ Our conversion is CORRECT: UTC → WIB")
    print(f"   ✅ Final WIB time: {wib_dt.strftime('%I:%M %p')} (23:00 / 11 PM)")
elif wib_dt.hour == 16:  # 4 PM in 24h
    print("   ⚠️  formattedTime is already WIB (4:00 PM WIB)")
    print("   ❌ Our conversion would be WRONG: will convert again!")
    print("   💡 Need to use formattedTime directly without conversion")

print("\n" + "=" * 60)
print("📌 Recommendation:")
print("   Run actual API call and compare:")
print("   - Unix timestamp converted to WIB")
print("   - formattedTime")
print("   If they match → formattedTime is WIB, use it directly")
print("   If different → formattedTime is UTC, use Unix timestamp")
