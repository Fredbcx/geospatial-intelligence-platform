#!/bin/bash
# test-api-format.sh - Diagnose API response format

echo "🔍 Testing API Response Format..."
echo ""

# Test 1: Raw response
echo "1️⃣ RAW API RESPONSE (first 500 chars):"
curl -s http://localhost:8000/api/alerts | head -c 500
echo ""
echo ""

# Test 2: Check if it's an array or object
echo "2️⃣ CHECKING FORMAT:"
RESPONSE=$(curl -s http://localhost:8000/api/alerts)
echo "$RESPONSE" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(f'Type: {type(data).__name__}')
    
    if isinstance(data, list):
        print(f'✅ Direct array with {len(data)} items')
        if len(data) > 0:
            print(f'Sample item keys: {list(data[0].keys())[:10]}')
    elif isinstance(data, dict):
        print(f'📦 Object with keys: {list(data.keys())}')
        for key in data.keys():
            if isinstance(data[key], list):
                print(f'   ✅ Found array in key \"{key}\" with {len(data[key])} items')
                if len(data[key]) > 0:
                    print(f'   Sample item keys: {list(data[key][0].keys())[:10]}')
    else:
        print(f'❌ Unknown type: {type(data)}')
except Exception as e:
    print(f'❌ Error: {e}')
"
echo ""

# Test 3: Pretty print first alert
echo "3️⃣ FIRST ALERT (pretty print):"
echo "$RESPONSE" | python -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if isinstance(data, list) and len(data) > 0:
        print(json.dumps(data[0], indent=2))
    elif isinstance(data, dict):
        for key in data.keys():
            if isinstance(data[key], list) and len(data[key]) > 0:
                print(json.dumps(data[key][0], indent=2))
                break
except Exception as e:
    print(f'Error: {e}')
"
echo ""

echo "✅ Test complete!"