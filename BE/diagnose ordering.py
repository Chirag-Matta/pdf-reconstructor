#!/usr/bin/env python3
"""
Diagnostic tool to analyze PDF ordering results
Usage: python diagnose_ordering.py metadata.json
"""

import json
import sys
from pathlib import Path

def analyze_ordering(metadata_path: str):
    """Analyze the ordering results and provide insights"""
    
    with open(metadata_path, 'r') as f:
        data = json.load(f)
    
    print("=" * 80)
    print("PDF RECONSTRUCTION DIAGNOSTIC REPORT")
    print("=" * 80)
    
    print(f"\n📄 Document: {data['original_filename']}")
    print(f"📊 Total Pages: {data['page_count']}")
    
    # Analyze if LLM refinement was used
    initial = data['initial_order']
    final = data['final_order']
    
    print(f"\n🤖 LLM Refinement: {'❌ NOT USED (orders are identical)' if initial == final else '✅ USED'}")
    
    if initial == final:
        print("   💡 Tip: Set OPENAI_API_KEY in .env to enable LLM refinement")
    
    # Analyze confidence scores
    confidences = data['confidences']
    avg_conf = sum(confidences) / len(confidences) if confidences else 0
    low_conf_count = sum(1 for c in confidences if c < 0.6)
    
    print(f"\n📈 Confidence Analysis:")
    print(f"   Average confidence: {avg_conf:.2%}")
    print(f"   Minimum confidence: {min(confidences):.2%}")
    print(f"   Maximum confidence: {max(confidences):.2%}")
    print(f"   Low confidence transitions (<60%): {low_conf_count}/{len(confidences)}")
    
    if avg_conf < 0.65:
        print("   ⚠️  Low average confidence suggests document has similar-looking pages")
        print("   💡 This is common with legal documents - LLM refinement recommended")
    
    # Show ordering
    print(f"\n📑 Page Order:")
    print(f"   Original shuffle: {initial[:15]}{'...' if len(initial) > 15 else ''}")
    print(f"   Final order:      {final[:15]}{'...' if len(final) > 15 else ''}")
    
    # Analyze first few pages
    print(f"\n📖 First 5 Pages Content Preview:")
    summaries = data['summaries']
    for i in range(min(5, len(final))):
        idx = final[i]
        preview = summaries[idx][:150].replace('\n', ' ').strip()
        conf = confidences[i]
        print(f"\n   Position {i} (from original page {idx}) - Confidence: {conf:.1%}")
        print(f"   {preview}...")
    
    # Look for potential issues
    print(f"\n🔍 Potential Issues:")
    issues_found = False
    
    # Check if title page is first
    first_page = summaries[final[0]]
    if not any(keyword in first_page.upper()[:200] for keyword in ['LOAN AGREEMENT', 'TITLE', 'COVER', 'DATED', 'BETWEEN']):
        print("   ⚠️  First page doesn't appear to be a title/cover page")
        issues_found = True
    
    # Check for large confidence drops
    for i in range(1, len(confidences)):
        if confidences[i-1] > 0.8 and confidences[i] < 0.5:
            print(f"   ⚠️  Large confidence drop at position {i}: {confidences[i-1]:.1%} → {confidences[i]:.1%}")
            issues_found = True
    
    # Check if we have many very similar pages
    if low_conf_count > len(confidences) * 0.5:
        print(f"   ⚠️  More than 50% of transitions have low confidence")
        print(f"   💡 Document likely has many pages with similar content")
        issues_found = True
    
    if not issues_found:
        print("   ✅ No obvious issues detected")
    
    # Recommendations
    print(f"\n💡 Recommendations:")
    if initial == final:
        print("   1. Enable OpenAI API for better ordering of complex documents")
        print("      Add OPENAI_API_KEY to your .env file")
    
    if avg_conf < 0.65:
        print("   2. This document has low semantic similarity between pages")
        print("      - Consider using a domain-specific embedding model")
        print("      - Legal documents benefit greatly from LLM refinement")
    
    if low_conf_count > 5:
        print("   3. Consider manual review of the ordering")
        print("      - Check if pages with low confidence are in logical sequence")
    
    print("\n" + "=" * 80)

def main():
    if len(sys.argv) < 2:
        print("Usage: python diagnose_ordering.py metadata.json")
        print("\nExample: python diagnose_ordering.py reordered_output_metadata.json")
        sys.exit(0)
    
    metadata_path = sys.argv[1]
    
    if not Path(metadata_path).exists():
        print(f"Error: File not found: {metadata_path}")
        sys.exit(1)
    
    try:
        analyze_ordering(metadata_path)
    except Exception as e:
        print(f"Error analyzing metadata: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()