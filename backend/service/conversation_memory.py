"""Conversation memory system for context-aware reasoning.

Enables the AI to remember past interactions and use them for better decision-making.
Implements sliding window memory with importance scoring and retrieval.
"""
from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple

__all__ = [
    "ConversationTurn",
    "ConversationMemory",
]


@dataclass
class ConversationTurn:
    """Single conversation turn with metadata."""
    
    timestamp: float
    query: str
    response: str
    confidence: float
    importance: float = 0.5  # 0.0 to 1.0
    entities: List[str] = field(default_factory=list)
    topics: List[str] = field(default_factory=list)
    
    def is_relevant_to(self, query: str) -> float:
        """Calculate relevance score to a new query (0.0 to 1.0)."""
        query_lower = query.lower()
        score = 0.0
        
        # Check entity overlap
        for entity in self.entities:
            if entity.lower() in query_lower:
                score += 0.3
        
        # Check topic overlap
        for topic in self.topics:
            if topic.lower() in query_lower:
                score += 0.2
        
        # Check keyword overlap
        query_words = set(query_lower.split())
        turn_words = set(self.query.lower().split())
        overlap = len(query_words & turn_words)
        if overlap > 0:
            score += 0.1 * min(overlap / len(query_words), 1.0)
        
        return min(score, 1.0)


class ConversationMemory:
    """
    Conversation memory system with importance-based retention.
    
    Features:
    - Sliding window memory (configurable size)
    - Importance scoring for selective retention
    - Context retrieval by relevance
    - Automatic entity and topic extraction
    """
    
    def __init__(
        self,
        *,
        max_turns: int = 50,
        importance_threshold: float = 0.3,
    ):
        """Initialize conversation memory.
        
        Args:
            max_turns: Maximum number of turns to retain
            importance_threshold: Minimum importance for long-term retention
        """
        self.max_turns = max_turns
        self.importance_threshold = importance_threshold
        self.turns: deque[ConversationTurn] = deque(maxlen=max_turns)
        self.important_turns: List[ConversationTurn] = []
        self.entity_index: Dict[str, List[int]] = {}  # entity -> turn indices
        self.topic_index: Dict[str, List[int]] = {}  # topic -> turn indices
    
    def _extract_entities(self, text: str) -> List[str]:
        """Extract named entities from text (simple keyword-based)."""
        entities = []
        text_lower = text.lower()
        
        # Common business entities
        if any(word in text_lower for word in ["revenue", "sales", "profit", "growth"]):
            entities.append("financial_metrics")
        
        if any(word in text_lower for word in ["q1", "q2", "q3", "q4", "quarter"]):
            entities.append("quarterly_period")
        
        if any(word in text_lower for word in ["approve", "decision", "budget", "expense"]):
            entities.append("approval_process")
        
        # Technical entities
        if any(word in text_lower for word in ["code", "function", "class", "algorithm"]):
            entities.append("technical_code")
        
        if any(word in text_lower for word in ["model", "training", "inference", "neural"]):
            entities.append("ml_system")
        
        return entities
    
    def _extract_topics(self, text: str) -> List[str]:
        """Extract topics from text."""
        topics = []
        text_lower = text.lower()
        
        topic_keywords = {
            "finance": ["revenue", "sales", "profit", "budget", "cost"],
            "operations": ["process", "workflow", "approval", "decision"],
            "technology": ["code", "system", "algorithm", "model"],
            "planning": ["forecast", "predict", "project", "plan"],
            "analysis": ["analyze", "calculate", "compute", "evaluate"],
        }
        
        for topic, keywords in topic_keywords.items():
            if any(kw in text_lower for kw in keywords):
                topics.append(topic)
        
        return topics
    
    def _calculate_importance(self, turn: ConversationTurn) -> float:
        """Calculate importance score for a conversation turn."""
        importance = 0.0
        
        # High confidence responses are more important
        importance += turn.confidence * 0.3
        
        # Turns with many entities/topics are more important
        importance += min(len(turn.entities) * 0.1, 0.3)
        importance += min(len(turn.topics) * 0.1, 0.2)
        
        # Long, detailed responses are more important
        response_length_score = min(len(turn.response) / 500.0, 0.2)
        importance += response_length_score
        
        return min(importance, 1.0)
    
    def add_turn(
        self,
        query: str,
        response: str,
        confidence: float,
    ) -> ConversationTurn:
        """Add a new conversation turn to memory."""
        entities = self._extract_entities(query + " " + response)
        topics = self._extract_topics(query + " " + response)
        
        turn = ConversationTurn(
            timestamp=time.time(),
            query=query,
            response=response,
            confidence=confidence,
            entities=entities,
            topics=topics,
        )
        
        # Calculate importance
        turn.importance = self._calculate_importance(turn)
        
        # Add to recent memory
        self.turns.append(turn)
        turn_idx = len(self.turns) - 1
        
        # Index entities and topics
        for entity in entities:
            if entity not in self.entity_index:
                self.entity_index[entity] = []
            self.entity_index[entity].append(turn_idx)
        
        for topic in topics:
            if topic not in self.topic_index:
                self.topic_index[topic] = []
            self.topic_index[topic].append(turn_idx)
        
        # Add to important memory if threshold met
        if turn.importance >= self.importance_threshold:
            self.important_turns.append(turn)
        
        return turn
    
    def get_relevant_context(
        self,
        query: str,
        *,
        max_turns: int = 5,
        min_relevance: float = 0.3,
    ) -> List[ConversationTurn]:
        """Retrieve relevant conversation turns for context.
        
        Args:
            query: Current query to find context for
            max_turns: Maximum number of turns to return
            min_relevance: Minimum relevance score
            
        Returns:
            List of relevant conversation turns, sorted by relevance
        """
        # Score all turns by relevance
        scored_turns: List[Tuple[float, ConversationTurn]] = []
        
        for turn in self.turns:
            relevance = turn.is_relevant_to(query)
            if relevance >= min_relevance:
                # Boost recent turns slightly
                recency_boost = 0.1 * (1.0 - (time.time() - turn.timestamp) / 3600.0)
                recency_boost = max(0.0, recency_boost)
                final_score = relevance + recency_boost
                scored_turns.append((final_score, turn))
        
        # Also check important turns
        for turn in self.important_turns:
            relevance = turn.is_relevant_to(query)
            if relevance >= min_relevance:
                # Important turns get extra boost
                final_score = relevance + 0.15
                scored_turns.append((final_score, turn))
        
        # Sort by score and return top N
        scored_turns.sort(key=lambda x: x[0], reverse=True)
        return [turn for _, turn in scored_turns[:max_turns]]
    
    def get_recent_turns(self, n: int = 5) -> List[ConversationTurn]:
        """Get N most recent conversation turns."""
        return list(self.turns)[-n:]
    
    def get_turns_by_entity(self, entity: str) -> List[ConversationTurn]:
        """Get all turns mentioning a specific entity."""
        if entity not in self.entity_index:
            return []
        
        indices = self.entity_index[entity]
        return [self.turns[i] for i in indices if i < len(self.turns)]
    
    def get_turns_by_topic(self, topic: str) -> List[ConversationTurn]:
        """Get all turns about a specific topic."""
        if topic not in self.topic_index:
            return []
        
        indices = self.topic_index[topic]
        return [self.turns[i] for i in indices if i < len(self.turns)]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics."""
        return {
            "total_turns": len(self.turns),
            "important_turns": len(self.important_turns),
            "unique_entities": len(self.entity_index),
            "unique_topics": len(self.topic_index),
            "avg_importance": sum(t.importance for t in self.turns) / max(len(self.turns), 1),
            "avg_confidence": sum(t.confidence for t in self.turns) / max(len(self.turns), 1),
        }
    
    def clear(self) -> None:
        """Clear all memory."""
        self.turns.clear()
        self.important_turns.clear()
        self.entity_index.clear()
        self.topic_index.clear()


# Demo
if __name__ == "__main__":
    print("\n" + "="*70)
    print("🧠 KOLIBRI AI — CONVERSATION MEMORY SYSTEM")
    print("="*70 + "\n")
    
    memory = ConversationMemory(max_turns=50)
    
    # Simulate conversation
    conversations = [
        ("What is our Q4 revenue forecast?", "Based on trends, Q4 revenue projected at $2.5M with 15% growth.", 0.87),
        ("Should we approve the $50k marketing budget?", "Decision: APPROVED. Budget available, ROI expected positive.", 0.92),
        ("Calculate the average customer acquisition cost", "CAC calculated at $125 per customer for Q3.", 0.89),
        ("What about Q4 expenses?", "Q4 expenses tracking at $1.8M, within budget.", 0.85),
        ("Review the marketing budget decision", "Previous approval for $50k marketing spend remains valid.", 0.91),
    ]
    
    print("Adding conversation turns...\n")
    for query, response, confidence in conversations:
        turn = memory.add_turn(query, response, confidence)
        print(f"Q: {query}")
        print(f"A: {response}")
        print(f"   Importance: {turn.importance:.2f}, Entities: {turn.entities}, Topics: {turn.topics}\n")
    
    # Test context retrieval
    print("\n" + "-"*70)
    print("Testing context retrieval...\n")
    
    test_query = "What was our revenue forecast?"
    print(f"Query: {test_query}")
    relevant = memory.get_relevant_context(test_query, max_turns=3)
    print(f"Found {len(relevant)} relevant turns:")
    for turn in relevant:
        print(f"  - {turn.query[:50]}... (relevance score included)")
    
    # Statistics
    print("\n" + "-"*70)
    print("Memory Statistics:")
    import json
    print(json.dumps(memory.get_stats(), indent=2))
    
    print("\n" + "="*70 + "\n")
