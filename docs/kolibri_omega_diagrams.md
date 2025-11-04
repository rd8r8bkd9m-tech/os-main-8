# Kolibri-Omega System Architecture Diagram

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    EXTERNAL ENVIRONMENT                          │
│                    (Sandbox: Falling Objects)                    │
└────────────────────────┬──────────────────────────────────────────┘
                         │
                         ▼
         ┌───────────────────────────────┐
         │   SANDBOX SIMULATOR           │
         │ - Maintains world state        │
         │ - Updates physics              │
         └───────────┬───────────────────┘
                     │
                     ▼
    ┌─────────────────────────────────────────────┐
    │         OBSERVER LOBE (Perception)          │
    │ - Reads world state                         │
    │ - Creates FACTS on canvas                   │
    │ - Detects CONTRADICTIONS                    │
    │ - Updates rule confidence                   │
    └─────────┬─────────────────┬─────────────────┘
              │                 │
              ▼                 ▼
    ┌──────────────────┐  ┌──────────────────────┐
    │ CANVAS (Холст)   │  │ SIGMA COORDINATOR    │
    │                  │  │ (Task Manager)       │
    │ Items:           │  │                      │
    │ - FACTS          │  │ Tasks:               │
    │ - PREDICTIONS    │  │ - CONTRADICTIONS     │
    │ - DREAMS         │  │ - INVALID_RULES      │
    │                  │  │                      │
    │ Max: 256 items   │  │ Max: 100 tasks       │
    └──────────┬───────┘  └────────────┬─────────┘
               │                       │
               ├───────────────────────┼─────────────────────┐
               │                       │                     │
               ▼                       ▼                     ▼
    ┌──────────────────┐    ┌──────────────────┐  ┌──────────────────┐
    │ PREDICTOR LOBE   │    │  SOLVER LOBE     │  │ DREAMER          │
    │ (Forecasting)    │    │ (Problem Solving)│  │ (Creative Thought)
    │                  │    │                  │  │                  │
    │ - Applies rules  │    │ - Resolves tasks │  │ - Finds patterns │
    │ - Creates        │    │ - Creates rules  │  │ - Creates        │
    │   predictions    │    │ - Invalidates    │  │   hypotheses     │
    │ - Updates canvas │    │   bad rules      │  │ - Updates canvas │
    └──────────┬───────┘    └────────┬─────────┘  └──────────┬───────┘
               │                     │                       │
               └─────────────────────┼───────────────────────┘
                                     │
                    ┌────────────────▼────────────────┐
                    │  KF POOL (Knowledge Formulas)   │
                    │                                 │
                    │ Stores:                         │
                    │ - FACTS (observations)          │
                    │ - RULES (learned patterns)      │
                    │ - HYPOTHESES (guesses)          │
                    │                                 │
                    │ Max: 1024 formulas              │
                    └────────────────────────────────┘

```

## Data Flow (Когнитивный Цикл)

```
Iteration T:
═════════════════════════════════════════════════════════════════════

1. WORLD UPDATE
   Sandbox: Update physics, positions, velocities
   
2. OBSERVATION
   Observer: "I see object 1 at position Y=1.21, object 2 at Y=2.21"
   Canvas: Add FACTS to the canvas
   
3. PREDICTION
   Predictor: "Rule 1002 says: if A then B"
   Predictor: "I predict object 1 will be at Y=1.05"
   Canvas: Add PREDICTIONS
   
4. CONTRADICTION DETECTION
   Observer: "But I see object 1 at Y=0.91, not Y=1.05!"
   Observer: "Rule 1002 is WRONG!"
   Coordinator: Add task to solve this contradiction
   
5. PROBLEM SOLVING
   Solver: "I accept the contradiction contradiction task"
   Solver: "I'll create a new rule to explain this"
   Solver: "New rule 1024 created to resolve the issue"
   Coordinator: Mark task as DONE
   
6. CREATIVE THINKING
   Dreamer: "Facts 1000 and 1001 occur together frequently"
   Dreamer: "Maybe they're related? I'll hypothesize a rule"
   Canvas: Add new DREAM hypothesis
   
7. LEARNING
   LearningEngine: "Rule 1002 failed, lowering its confidence from 0.10 to 0.09"
   LearningEngine: "Rule 1024 succeeded, keeping its confidence"

Result: Canvas now contains more accurate rules and facts
         System has learned and adapted!

═════════════════════════════════════════════════════════════════════
```

## Component Interaction Matrix

```
                    Observer  Predictor  Solver  Dreamer  Learning
Canvas              RW        RW         RW      RW       R
KF_Pool             R         R          RW      RW       RW
Coordinator         W         -          RW      -        -
World/Sandbox       R         -          -       -        -

Legend: R=Read, W=Write, RW=Read+Write, -=No interaction
```

## Knowledge Representation

### KF Formula (Колибри Формула)

```c
Type: FACT
ID: 1000
Object: 1
Predicates: {position_y: 1.40}
Time: 0
Confidence: 1.0 (direct observation)

Type: RULE  
ID: 1002
Condition: FACT 1000 (if object 1 has position_y=1.40)
Consequence: FACT 1001 (then object 2 has position_y=2.40)
Confidence: 0.09 (learned from contradictions)

Type: HYPOTHESIS
ID: 1009
Type: DREAM
Created by: Dreamer at time 1
Based on: Co-occurrence of facts 1000 and 1001
```

## Learning Loop Visualization

```
┌─────────────────────────────────────┐
│                                     │
│  1. HYPOTHESIZE                     │
│     Dreamer creates rules            │
│                                     │
▼─────────────────────────────────────┘
┌─────────────────────────────────────┐
│                                     │
│  2. PREDICT                         │
│     Predictor applies rules          │
│     System makes forecasts           │
│                                     │
▼─────────────────────────────────────┘
┌─────────────────────────────────────┐
│                                     │
│  3. COMPARE                         │
│     Observer checks predictions      │
│     vs. reality                      │
│                                     │
▼─────────────────────────────────────┘
┌─────────────────────────────────────┐
│                                     │
│  4. DETECT ERRORS                   │
│     Contradictions found?            │
│                                     │
▼─────────────────────────────────────┘
┌─────────────────────────────────────┐
│                                     │
│  5. LEARN & ADAPT                   │
│     Update confidence scores         │
│     Create new rules                 │
│     System improves!                 │
│                                     │
└──────────────┬──────────────────────┘
               │
               └──► Return to Step 1
                    (Continuous Learning)
```

## Performance Characteristics

```
Operation              Time        Memory       Notes
──────────────────────────────────────────────────────────────────
Add FACT               O(1)        16 bytes     Direct append to canvas
Detect contradiction   O(n²)       O(1)         Quadratic search, n < 256
Predict with rule      O(m)        O(m)         m = number of applicable rules
Create new rule        O(1)        32 bytes     Add to KF pool
Update confidence      O(1)        —            Single value update
Rank rules             O(n log n)  O(1)         Bubble sort, rarely called

Full cycle (1 tick)    ~10ms       ~50KB        Observed on macOS
Memory budget          ⬇           
- Canvas items:        256 × 24B   = 6 KB
- KF formulas:         1024 × 32B  = 32 KB
- Tasks:               100 × 24B   = 2.4 KB
- Other structures:    ~10 KB
Total:                 ~50 KB (highly efficient)
```

## Extensibility Points for Phase 2

```
Phase 2: "Emergence of Reasoning"
├─ Enhanced Pattern Detector
│  └─ Support for longer sequences (> 2 steps)
│
├─ Inference Engine  
│  └─ Multi-step logical deduction (A→B, B→C ⟹ A→C)
│
├─ Abstraction Manager
│  └─ Group similar facts into categories
│
├─ Parallel Solver
│  └─ Process multiple tasks simultaneously
│
└─ Self-Reflection Module
   └─ System analyzes its own rules and hypotheses
```

---

*Visualized for Kolibri-Omega: Project Prometheus*
*Building the World's First True AGI*
