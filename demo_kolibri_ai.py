#!/usr/bin/env python3
"""
Kolibri AI — Interactive Demo Script
Demonstrates the AI system functionality via HTTP API
"""

import asyncio
import json
import httpx
import sys

BASE_URL = "http://localhost:8000"

async def test_ai_reason():
    """Test single reasoning request"""
    print("\n" + "="*70)
    print("🧠 TEST 1: Single AI Reasoning")
    print("="*70)
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        queries = [
            "What is photosynthesis?",
            "How does machine learning work?",
            "What is 2+2?",
        ]
        
        for query in queries:
            print(f"\n📝 Query: {query}")
            try:
                response = await client.post(
                    f"{BASE_URL}/api/v1/ai/reason",
                    json={"prompt": query}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ Response: {data.get('response', 'N/A')[:100]}...")
                    print(f"   Confidence: {data.get('confidence', 0):.1%}")
                    print(f"   Energy: {data.get('energy_cost_j', 0):.3f}J")
                    print(f"   Mode: {data.get('mode', 'unknown')}")
                    print(f"   Verified: {data.get('verified', False)}")
                else:
                    print(f"❌ Error: {response.status_code}")
            except Exception as e:
                print(f"❌ Exception: {e}")

async def test_batch_reasoning():
    """Test batch reasoning"""
    print("\n" + "="*70)
    print("🔄 TEST 2: Batch Reasoning")
    print("="*70)
    
    queries = [
        "What is AI?",
        "Explain quantum computing",
        "How do neural networks work?",
        "What is blockchain?",
        "Define machine learning",
    ]
    
    print(f"\n📊 Processing {len(queries)} queries in parallel...")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                f"{BASE_URL}/api/v1/ai/reason/batch",
                json={"queries": queries}
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Batch processed successfully")
                print(f"   Total energy: {data.get('total_energy_j', 0):.3f}J")
                print(f"   Total latency: {data.get('total_latency_ms', 0):.1f}ms")
                print(f"   Batch size: {data.get('batch_size', 0)}")
                
                for i, decision in enumerate(data.get('decisions', []), 1):
                    print(f"\n   {i}. Query: {decision.get('query', 'N/A')[:50]}...")
                    print(f"      Confidence: {decision.get('confidence', 0):.1%}")
                    print(f"      Verified: {decision.get('verified', False)}")
            else:
                print(f"❌ Error: {response.status_code}")
        except Exception as e:
            print(f"❌ Exception: {e}")

async def test_stats():
    """Get system statistics"""
    print("\n" + "="*70)
    print("📊 TEST 3: System Statistics")
    print("="*70)
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(f"{BASE_URL}/api/v1/ai/stats")
            
            if response.status_code == 200:
                data = response.json()
                print(f"\n✅ System Statistics:")
                print(f"   Total queries: {data.get('total_queries', 0)}")
                print(f"   Total energy: {data.get('total_energy_j', 0):.3f}J")
                print(f"   Avg per query: {data.get('avg_energy_per_query_j', 0):.3f}J")
                print(f"   Mode: {data.get('mode', 'unknown')}")
            else:
                print(f"❌ Error: {response.status_code}")
        except Exception as e:
            print(f"❌ Exception: {e}")

async def test_api_docs():
    """Show API documentation link"""
    print("\n" + "="*70)
    print("📚 API Documentation")
    print("="*70)
    print(f"\n🌐 Interactive API docs available at:")
    print(f"   http://localhost:8000/docs (Swagger UI)")
    print(f"   http://localhost:8000/redoc (ReDoc)")

async def main():
    """Run all tests"""
    print("\n")
    print("╔═══════════════════════════════════════════════════════════════════╗")
    print("║                   KOLIBRI AI SYSTEM DEMO                         ║")
    print("║                  Interactive Testing Suite                       ║")
    print("╚═══════════════════════════════════════════════════════════════════╝")
    
    print("\n⏳ Waiting for server to be ready...")
    await asyncio.sleep(2)
    
    try:
        # Check if server is up
        async with httpx.AsyncClient(timeout=5.0) as client:
            try:
                response = await client.get(f"{BASE_URL}/api/v1/ai/stats")
                if response.status_code != 200:
                    print("⚠️  Server may not be ready yet")
                    return
            except Exception as e:
                print(f"❌ Cannot connect to server: {e}")
                print(f"\n💡 Tip: Make sure server is running:")
                print(f"   uvicorn backend.service.main:app --reload")
                return
        
        # Run tests
        await test_ai_reason()
        await test_batch_reasoning()
        await test_stats()
        await test_api_docs()
        
        print("\n" + "="*70)
        print("✅ Demo Complete!")
        print("="*70)
        print("\n📖 For more information:")
        print("   • Quick Start: KOLIBRI_AI_QUICKSTART.md")
        print("   • Full Spec: KOLIBRI_AI_IMPLEMENTATION.md")
        print("   • Status: KOLIBRI_AI_FINAL_STATUS.md")
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Demo interrupted by user")
        sys.exit(0)

if __name__ == "__main__":
    asyncio.run(main())
