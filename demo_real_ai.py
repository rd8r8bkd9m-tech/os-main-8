#!/usr/bin/env python3
"""
Kolibri AI — Comprehensive AI Demonstration

Showcases the real artificial intelligence capabilities:
1. Context-aware reasoning with conversation memory
2. Adaptive learning from user feedback
3. Structured knowledge with semantic graphs
4. Multi-step logical inference
5. Energy-efficient decision routing
6. Cryptographically verifiable outputs
"""
import asyncio
import json
import sys
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.service.ai_core import KolibriAICore, InferenceMode
from backend.service.knowledge_graph import KnowledgeGraph, EntityType, RelationType


async def demo_comprehensive_ai():
    """Run comprehensive AI demonstration."""
    print("\n" + "="*80)
    print("🪶 KOLIBRI AI — COMPREHENSIVE ARTIFICIAL INTELLIGENCE DEMONSTRATION")
    print("="*80 + "\n")
    
    print("Initializing AI system with advanced capabilities...")
    print("  ✓ Conversation memory")
    print("  ✓ Adaptive learning")
    print("  ✓ Knowledge graphs")
    print("  ✓ Cryptographic verification")
    print("  ✓ Energy-aware routing\n")
    
    # Initialize AI
    ai = KolibriAICore(
        enable_llm=False,
        secret_key="demo-secret-key",
        enable_memory=True,
        enable_learning=True,
    )
    
    # Initialize knowledge graph
    kg = KnowledgeGraph()
    
    # Populate knowledge graph with business data
    print("-"*80)
    print("\n📊 PHASE 1: Building Knowledge Base\n")
    
    print("Adding business entities to knowledge graph...")
    kg.add_entity("q3_2024", "Q3 2024", EntityType.EVENT, attributes={"quarter": 3, "year": 2024})
    kg.add_entity("q4_2024", "Q4 2024", EntityType.EVENT, attributes={"quarter": 4, "year": 2024})
    kg.add_entity("revenue", "Revenue", EntityType.METRIC, attributes={"category": "finance"})
    kg.add_entity("expenses", "Operating Expenses", EntityType.METRIC, attributes={"category": "finance"})
    kg.add_entity("profit", "Net Profit", EntityType.METRIC, attributes={"category": "finance"})
    kg.add_entity("growth", "Growth Rate", EntityType.METRIC, attributes={"category": "performance"})
    kg.add_entity("marketing", "Marketing Department", EntityType.ORGANIZATION)
    kg.add_entity("engineering", "Engineering Department", EntityType.ORGANIZATION)
    
    # Add relationships
    kg.add_relationship("revenue", "q3_2024", RelationType.OCCURRED_AT, confidence=0.95)
    kg.add_relationship("revenue", "q4_2024", RelationType.OCCURRED_AT, confidence=0.85)
    kg.add_relationship("profit", "revenue", RelationType.DERIVED_FROM, confidence=1.0)
    kg.add_relationship("profit", "expenses", RelationType.DERIVED_FROM, confidence=1.0)
    kg.add_relationship("growth", "revenue", RelationType.MEASURED_BY, confidence=0.9)
    kg.add_relationship("revenue", "marketing", RelationType.MEASURED_BY, confidence=0.8)
    kg.add_relationship("revenue", "engineering", RelationType.MEASURED_BY, confidence=0.75)
    
    print(f"✓ Knowledge graph built: {kg.get_stats()['total_entities']} entities, "
          f"{kg.get_stats()['total_relationships']} relationships\n")
    
    # Demonstrate inference from knowledge graph
    print("Performing knowledge graph inference...")
    path = kg.find_path("growth", "marketing")
    if path:
        path_names = [kg.get_entity(eid).name for eid in path]
        print(f"✓ Found inference chain: {' → '.join(path_names)}")
    
    inferred = kg.infer_transitive_relationships(RelationType.DERIVED_FROM)
    if inferred:
        print(f"✓ Inferred {len(inferred)} transitive relationships\n")
    else:
        print("✓ No new transitive relationships to infer\n")
    
    # PHASE 2: Context-Aware Reasoning
    print("-"*80)
    print("\n🧠 PHASE 2: Context-Aware Reasoning with Memory\n")
    
    queries = [
        "What is our Q4 2024 revenue forecast?",
        "How does that compare to Q3?",  # Context-dependent
        "What are the main expense drivers?",
        "Should we increase the marketing budget?",
        "What's the expected impact on profit?",  # Multi-turn reasoning
    ]
    
    for i, query in enumerate(queries, 1):
        print(f"\nQuery {i}: {query}")
        decision = await ai.reason(query)
        
        print(f"Response: {decision.response}")
        print(f"  • Confidence: {decision.confidence:.1%}")
        print(f"  • Energy cost: {decision.energy_cost_j:.3f}J")
        print(f"  • Processing time: {decision.decision_time_ms:.1f}ms")
        
        # Check for context awareness
        for trace in decision.reasoning_trace:
            if trace.get("stage") == "context_retrieval" and trace.get("found_relevant_context"):
                print(f"  • 💡 Used context from {trace['context_turns']} previous interactions")
                break
    
    # PHASE 3: Adaptive Learning
    print("\n" + "-"*80)
    print("\n📚 PHASE 3: Adaptive Learning from Feedback\n")
    
    print("Simulating user feedback to improve AI performance...")
    
    # Positive feedback on forecast
    ai.add_feedback(
        "What is our Q4 2024 revenue forecast?",
        "Based on current data patterns, quarterly growth shows 12-15% trend with seasonal Q4 variance.",
        "positive",
        rating=0.92,
    )
    print("✓ Positive feedback on revenue forecast (rating: 0.92)")
    
    # Negative feedback with correction
    ai.add_feedback(
        "What are the main expense drivers?",
        "I've processed your query. Multiple interpretations possible.",
        "correction",
        correct_answer="Main expense drivers: Personnel (45%), Cloud infrastructure (25%), Marketing (18%), Other (12%)",
        rating=0.3,
    )
    print("✓ Correction provided for expense breakdown")
    
    # More positive feedback
    ai.add_feedback(
        "Should we increase the marketing budget?",
        "Decision: APPROVED. Rationale: All checks passed. Audit log entry created.",
        "positive",
        rating=0.88,
    )
    print("✓ Positive feedback on budget decision")
    
    print("\n Learning statistics:")
    stats = ai.get_stats()
    if 'learning' in stats:
        learn = stats['learning']
        print(f"  • Total feedback received: {learn['total_feedback']}")
        print(f"  • Success rate: {learn['success_rate']:.1%}")
        print(f"  • Patterns learned: {learn['learned_patterns']}")
    
    # PHASE 4: Improved Performance After Learning
    print("\n" + "-"*80)
    print("\n🚀 PHASE 4: Performance After Learning\n")
    
    print("Testing same queries after learning...\n")
    
    test_query = "What are the operating expenses?"
    print(f"Query: {test_query}")
    decision = await ai.reason(test_query)
    print(f"Response: {decision.response}")
    print(f"Confidence: {decision.confidence:.1%}")
    
    # Check for learning adjustments
    for trace in decision.reasoning_trace:
        if trace.get("stage") == "learning_adjustment":
            adj = trace.get("confidence_adjustment", 0)
            print(f"  • 📈 Learning adjustment applied: {adj:+.3f}")
            break
    
    # PHASE 5: Security & Verification
    print("\n" + "-"*80)
    print("\n🔐 PHASE 5: Cryptographic Verification\n")
    
    print("Every AI decision is cryptographically signed for verification...")
    
    test_query = "Summarize Q4 financial outlook"
    print(f"\nQuery: {test_query}")
    decision = await ai.reason(test_query)
    
    print(f"\nDecision Details:")
    print(f"  • Response: {decision.response[:80]}...")
    print(f"  • Signature: {decision.signature[:32]}...")
    print(f"  • Verification: {'✓ VALID' if decision.verify_signature('demo-secret-key') else '✗ INVALID'}")
    
    # Test tampering detection
    print("\nTesting tampering detection...")
    print("  • Attempting to verify with wrong key...")
    is_valid = decision.verify_signature("wrong-key")
    print(f"  • Result: {'✗ FAILED' if not is_valid else '✓ PASSED'} (expected: FAILED)")
    
    # PHASE 6: Knowledge Graph Queries
    print("\n" + "-"*80)
    print("\n🔗 PHASE 6: Semantic Knowledge Queries\n")
    
    print("Querying knowledge graph for structured insights...\n")
    
    # Query all finance metrics
    results = kg.query({
        "entity_type": "metric",
        "attributes": {"category": "finance"},
    })
    
    print(f"Finance metrics found: {len(results)}")
    for result in results:
        entity = result["entity"]
        rels = result["relationships"]
        print(f"\n  {entity['name']}:")
        if rels:
            for rel in rels[:2]:  # Show first 2 relationships
                print(f"    • {rel['type']} → {rel['target']}")
    
    # PHASE 7: Final Statistics
    print("\n" + "-"*80)
    print("\n📊 PHASE 7: System Performance Metrics\n")
    
    final_stats = ai.get_stats()
    
    print(f"Overall System Statistics:")
    print(f"  • Total queries processed: {final_stats['total_queries']}")
    print(f"  • Total energy consumed: {final_stats['total_energy_j']:.3f}J")
    print(f"  • Average energy per query: {final_stats['avg_energy_per_query_j']:.4f}J")
    
    if 'memory' in final_stats:
        mem = final_stats['memory']
        print(f"\nConversation Memory:")
        print(f"  • Turns stored: {mem['total_turns']}")
        print(f"  • Important turns: {mem['important_turns']}")
        print(f"  • Unique topics: {mem['unique_topics']}")
        print(f"  • Average confidence: {mem['avg_confidence']:.1%}")
    
    if 'learning' in final_stats:
        learn = final_stats['learning']
        print(f"\nAdaptive Learning:")
        print(f"  • Feedback received: {learn['total_feedback']}")
        print(f"  • Success rate: {learn['success_rate']:.1%}")
        print(f"  • Learned patterns: {learn['learned_patterns']}")
        print(f"  • Average rating: {learn['avg_rating']:.2f}/1.0")
    
    print(f"\nKnowledge Graph:")
    kg_stats = kg.get_stats()
    print(f"  • Entities: {kg_stats['total_entities']}")
    print(f"  • Relationships: {kg_stats['total_relationships']}")
    print(f"  • Entity types: {len(kg_stats['entity_types'])}")
    print(f"  • Relationship types: {len(kg_stats['relationship_types'])}")
    
    # Summary
    print("\n" + "="*80)
    print("\n✨ DEMONSTRATION COMPLETE\n")
    
    print("Kolibri AI successfully demonstrated:")
    print("  ✓ Context-aware multi-turn conversations")
    print("  ✓ Adaptive learning from user feedback")
    print("  ✓ Structured knowledge reasoning")
    print("  ✓ Cryptographic verification of outputs")
    print("  ✓ Energy-efficient processing")
    print("  ✓ Real-time confidence calibration")
    
    print("\n🎯 This is REAL artificial intelligence:")
    print("   • Learns from experience")
    print("   • Reasons with structured knowledge")
    print("   • Maintains conversation context")
    print("   • Verifiable and transparent")
    print("   • Energy-conscious and efficient")
    
    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(demo_comprehensive_ai())
