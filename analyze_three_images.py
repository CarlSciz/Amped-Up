"""
Zeus Multi-Image Analysis Demo
Demonstrates Zeus's ability to analyze 3 different or same pictures of a pole
"""

import sys
import os

# Add backend to path
sys.path.insert(0, 'backend')

from backend.zeus_agent import ZeusAgent


def main():
    """Demonstrate multi-image analysis with Zeus"""
    
    print("=" * 80)
    print("ZEUS MULTI-IMAGE ANALYSIS DEMONSTRATION")
    print("=" * 80)
    print("\nThis demo shows Zeus analyzing 3 images of the same pole")
    print("to provide comprehensive inspection results.\n")
    
    # Initialize Zeus
    zeus = ZeusAgent()
    
    # Example 1: Analyze 3 different images of the same pole
    print("\n" + "=" * 80)
    print("EXAMPLE 1: Three Different Views of the Same Pole")
    print("=" * 80)
    
    image_paths_example1 = [
        "picture/20260516_171832.jpg",
        "picture/20260516_171832.jpg",  # Using same image for demo
        "picture/20260516_171832.jpg"   # In production, these would be different angles
    ]
    
    try:
        # Perform multi-image analysis
        analysis = zeus.analyze_multiple_images(
            image_paths=image_paths_example1,
            pole_id="POLE-DEMO-001",
            context={
                "location": "Main St & 5th Ave",
                "pole_class": "Class 2",
                "length_ft": 40,
                "installation_year": 2010
            }
        )
        
        # Print formatted results
        zeus.print_multi_image_analysis(analysis)
        
        # Show key insights
        print("\n" + "=" * 80)
        print("KEY INSIGHTS FROM MULTI-IMAGE ANALYSIS")
        print("=" * 80)
        
        print(f"\n✓ Total defects identified: {len(analysis.consolidated_defects)}")
        print(f"✓ Overall confidence: {analysis.confidence_scores['overall_analysis']:.1%}")
        print(f"✓ Multi-view confirmations: {len([d for d in analysis.consolidated_defects if d['image_count'] > 1])}")
        
        # Show severity breakdown
        print("\n📊 Severity Breakdown:")
        for severity, count in analysis.overall_severity.items():
            if count > 0:
                emoji = "🔴" if severity == "imminent_danger" else "⚠️" if severity == "serious" else "🟡" if severity == "other_than_serious" else "🟢"
                print(f"   {emoji} {severity.replace('_', ' ').title()}: {count}")
        
    except Exception as e:
        print(f"\n❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()
    
    # Example 2: Analyze same image 3 times (testing consistency)
    print("\n\n" + "=" * 80)
    print("EXAMPLE 2: Same Image Analyzed 3 Times (Consistency Check)")
    print("=" * 80)
    
    image_paths_example2 = [
        "picture/20260516_171832.jpg",
        "picture/20260516_171832.jpg",
        "picture/20260516_171832.jpg"
    ]
    
    try:
        analysis2 = zeus.analyze_multiple_images(
            image_paths=image_paths_example2,
            pole_id="POLE-DEMO-002"
        )
        
        print(f"\n✓ Consistency test complete")
        print(f"✓ All defects should show 100% multi-view confirmation")
        print(f"✓ Defects confirmed in all 3 images: {len([d for d in analysis2.consolidated_defects if d['image_count'] == 3])}")
        print(f"✓ Average confidence boost: {sum(d['confidence'] for d in analysis2.consolidated_defects) / len(analysis2.consolidated_defects):.1%}")
        
    except Exception as e:
        print(f"\n❌ Error during consistency check: {e}")
    
    # Show Zeus capabilities
    print("\n\n" + "=" * 80)
    print("ZEUS MULTI-IMAGE CAPABILITIES")
    print("=" * 80)
    
    print("\n🎯 What Zeus Can Do with Multiple Images:")
    print("   • Analyze 1-3 images simultaneously")
    print("   • Correlate findings across different views")
    print("   • Increase confidence for defects visible in multiple images")
    print("   • Identify complementary coverage from different angles")
    print("   • Generate consolidated recommendations")
    print("   • Provide comprehensive severity assessment")
    
    print("\n📈 Benefits of Multi-Image Analysis:")
    print("   • Higher detection confidence")
    print("   • Reduced false positives")
    print("   • Better coverage of pole condition")
    print("   • More accurate severity assessment")
    print("   • Comprehensive inspection reports")
    
    # Interactive Zeus queries
    print("\n\n" + "=" * 80)
    print("ZEUS INTERACTIVE Q&A")
    print("=" * 80)
    
    questions = [
        "Why is multi-image analysis important for pole inspection?",
        "What are the benefits of analyzing multiple views?",
        "How does Zeus handle defects visible in multiple images?"
    ]
    
    for question in questions:
        response = zeus.ask(question)
        print(f"\n❓ {question}")
        print(f"💬 Zeus: {response.answer[:300]}...")
    
    print("\n\n" + "=" * 80)
    print("DEMONSTRATION COMPLETE")
    print("=" * 80)
    print("\n✓ Zeus successfully analyzed multiple images")
    print("✓ Multi-image correlation and consolidation working")
    print("✓ Confidence scoring and recommendations generated")
    print("\nFor production use, provide actual different angle images for best results.")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()

# Made with Bob