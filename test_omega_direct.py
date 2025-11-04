#!/usr/bin/env python3
"""Direct test of cognition_test binary"""
import subprocess
import os

os.chdir("/Users/kolibri/Downloads/os-main 8")

print("🧠 Testing Kolibri-Omega cognition_test directly...\n")

try:
    print("📝 Running: ./build-fuzz/cognition_test")
    result = subprocess.run(
        ["./build-fuzz/cognition_test"],
        capture_output=True,
        text=True,
        timeout=10
    )
    
    print(f"Return code: {result.returncode}")
    print(f"Stderr length: {len(result.stderr)}")
    print(f"Stdout length: {len(result.stdout)}\n")
    
    # Show output
    if result.stdout:
        print("📊 STDOUT Output (first 2000 chars):")
        print("=" * 60)
        print(result.stdout[:2000])
        print("=" * 60)
        
        # Count phases
        phases = ["Canvas", "Observer", "Dreamer", "Solver", "InferenceEngine", 
                  "ExtendedPatternDetector", "AbstractionEngine", "CounterfactualReasoner",
                  "PolicyLearner", "BayesianCausal"]
        
        print("\n🎯 Detected Phases:")
        for phase in phases:
            if phase in result.stdout:
                count = result.stdout.count(f"[{phase}]")
                print(f"  ✅ {phase}: {count} occurrences")
        
    if result.stderr:
        print("\n⚠️ STDERR Output:")
        print(result.stderr[:500])
        
except subprocess.TimeoutExpired:
    print("❌ Timeout after 10 seconds")
except FileNotFoundError:
    print("❌ Binary not found: ./build-fuzz/cognition_test")
except Exception as e:
    print(f"❌ Error: {e}")
