"""
Test script untuk cek apakah evaluation routes terdaftar
"""
import sys
sys.path.insert(0, '.')

from app import create_app
from app.extensions import db

app = create_app()

print("=" * 80)
print("EVALUATION ROUTES CHECK")
print("=" * 80)

with app.app_context():
    # Get all registered routes
    rules = []
    for rule in app.url_map.iter_rules():
        if 'evaluation' in str(rule.endpoint).lower():
            rules.append({
                'endpoint': str(rule.endpoint),
                'rule': str(rule),
                'methods': ', '.join(sorted(rule.methods - {'HEAD', 'OPTIONS'}))
            })
    
    if rules:
        print(f"\n✅ Found {len(rules)} evaluation routes:\n")
        for r in sorted(rules, key=lambda x: x['rule']):
            print(f"  {r['methods']:10}  {r['rule']:50}  →  {r['endpoint']}")
    else:
        print("\n❌ No evaluation routes found!")
    
    print("\n" + "=" * 80)
    
    # Test if summary endpoint exists
    print("\nTesting summary endpoint availability:")
    test_endpoint = '/evaluasi-tes/api/1/summary'
    print(f"  Endpoint: {test_endpoint}")
    
    # Check if route matches
    matched = False
    for rule in app.url_map.iter_rules():
        if rule.rule == '/evaluasi-tes/api/<int:course_id>/summary':
            matched = True
            print(f"  ✅ Route found: {rule.rule}")
            print(f"  ✅ Endpoint: {rule.endpoint}")
            print(f"  ✅ Methods: {', '.join(sorted(rule.methods - {'HEAD', 'OPTIONS'}))}")
            break
    
    if not matched:
        print(f"  ❌ Route NOT found!")

print("\n" + "=" * 80)
