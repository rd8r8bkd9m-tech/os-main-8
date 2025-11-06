"""Adaptive learning system for continuous AI improvement.

Enables the AI to learn from user feedback and adapt its behavior over time.
Implements reinforcement learning-style feedback integration and rule refinement.
"""
from __future__ import annotations

import json
import logging
import time
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

__all__ = [
    "FeedbackType",
    "UserFeedback",
    "LearningSystem",
]

LOGGER = logging.getLogger("kolibri.ai.learning")


class FeedbackType(str, Enum):
    """Types of feedback the system can receive."""
    POSITIVE = "positive"  # Response was helpful
    NEGATIVE = "negative"  # Response was not helpful
    CORRECTION = "correction"  # User provides correct answer
    CLARIFICATION = "clarification"  # Response was unclear


@dataclass
class UserFeedback:
    """User feedback on an AI decision."""
    
    timestamp: float
    query: str
    response: str
    feedback_type: FeedbackType
    feedback_text: Optional[str] = None
    correct_answer: Optional[str] = None
    rating: Optional[float] = None  # 0.0 to 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            k: v.value if isinstance(v, Enum) else v
            for k, v in asdict(self).items()
        }


@dataclass
class PatternLearning:
    """Learned pattern from feedback."""
    
    pattern_id: str
    query_pattern: str  # What kind of queries this applies to
    learned_behavior: str  # What to do differently
    confidence: float = 0.5  # 0.0 to 1.0
    positive_examples: int = 0
    negative_examples: int = 0
    last_updated: float = field(default_factory=time.time)
    
    def update_from_feedback(self, is_positive: bool) -> None:
        """Update pattern confidence based on feedback."""
        if is_positive:
            self.positive_examples += 1
        else:
            self.negative_examples += 1
        
        total = self.positive_examples + self.negative_examples
        if total > 0:
            # Bayesian update with smoothing
            alpha = 1.0  # Prior strength
            self.confidence = (self.positive_examples + alpha) / (total + 2 * alpha)
        
        self.last_updated = time.time()


class LearningSystem:
    """
    Adaptive learning system for Kolibri AI.
    
    Features:
    - Feedback collection and aggregation
    - Pattern extraction from feedback
    - Confidence adjustment based on performance
    - Behavior adaptation rules
    """
    
    def __init__(
        self,
        *,
        learning_rate: float = 0.1,
        min_examples_for_pattern: int = 3,
    ):
        """Initialize learning system.
        
        Args:
            learning_rate: How quickly to adapt (0.0 to 1.0)
            min_examples_for_pattern: Minimum feedback to form pattern
        """
        self.learning_rate = learning_rate
        self.min_examples_for_pattern = min_examples_for_pattern
        
        # Storage
        self.feedback_history: List[UserFeedback] = []
        self.learned_patterns: Dict[str, PatternLearning] = {}
        self.topic_performance: Dict[str, Dict[str, float]] = defaultdict(lambda: {
            "positive_count": 0.0,
            "total_count": 0.0,
            "avg_rating": 0.5,
        })
        
        # Adaptation parameters
        self.confidence_adjustments: Dict[str, float] = {}  # topic -> adjustment
        self.response_strategies: Dict[str, str] = {}  # pattern -> strategy
    
    def add_feedback(
        self,
        query: str,
        response: str,
        feedback_type: FeedbackType,
        *,
        feedback_text: Optional[str] = None,
        correct_answer: Optional[str] = None,
        rating: Optional[float] = None,
    ) -> UserFeedback:
        """Record user feedback on a decision.
        
        Args:
            query: Original query
            response: AI response
            feedback_type: Type of feedback
            feedback_text: Optional text feedback
            correct_answer: Optional correct answer for corrections
            rating: Optional numeric rating (0.0 to 1.0)
            
        Returns:
            UserFeedback object
        """
        feedback = UserFeedback(
            timestamp=time.time(),
            query=query,
            response=response,
            feedback_type=feedback_type,
            feedback_text=feedback_text,
            correct_answer=correct_answer,
            rating=rating,
        )
        
        self.feedback_history.append(feedback)
        
        # Update learning immediately
        self._update_from_feedback(feedback)
        
        LOGGER.info(f"Feedback recorded: {feedback_type.value} for query: {query[:50]}...")
        
        return feedback
    
    def _extract_topic(self, text: str) -> str:
        """Extract primary topic from text."""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ["revenue", "sales", "profit"]):
            return "finance"
        elif any(word in text_lower for word in ["approve", "decision", "budget"]):
            return "approval"
        elif any(word in text_lower for word in ["calculate", "compute", "average"]):
            return "calculation"
        elif any(word in text_lower for word in ["forecast", "predict", "project"]):
            return "forecasting"
        elif any(word in text_lower for word in ["code", "function", "algorithm"]):
            return "technical"
        else:
            return "general"
    
    def _update_from_feedback(self, feedback: UserFeedback) -> None:
        """Update learning parameters based on feedback."""
        topic = self._extract_topic(feedback.query)
        
        # Update topic performance
        perf = self.topic_performance[topic]
        perf["total_count"] += 1
        
        if feedback.feedback_type == FeedbackType.POSITIVE:
            perf["positive_count"] += 1
        
        if feedback.rating is not None:
            # Exponential moving average
            alpha = self.learning_rate
            current_avg = perf["avg_rating"]
            perf["avg_rating"] = alpha * feedback.rating + (1 - alpha) * current_avg
        
        # Calculate confidence adjustment
        if perf["total_count"] >= 3:
            success_rate = perf["positive_count"] / perf["total_count"]
            # Adjust confidence based on performance
            # Good performance (>70%) -> increase confidence
            # Poor performance (<50%) -> decrease confidence
            if success_rate > 0.7:
                self.confidence_adjustments[topic] = min(0.15, (success_rate - 0.7) * 0.5)
            elif success_rate < 0.5:
                self.confidence_adjustments[topic] = max(-0.15, (success_rate - 0.5) * 0.3)
        
        # Learn patterns from corrections
        if feedback.feedback_type == FeedbackType.CORRECTION and feedback.correct_answer:
            self._learn_correction_pattern(feedback)
        
        # Learn from negative feedback
        if feedback.feedback_type == FeedbackType.NEGATIVE:
            self._learn_avoidance_pattern(feedback)
    
    def _learn_correction_pattern(self, feedback: UserFeedback) -> None:
        """Learn from user corrections."""
        pattern_id = f"correction_{self._extract_topic(feedback.query)}"
        
        if pattern_id not in self.learned_patterns:
            self.learned_patterns[pattern_id] = PatternLearning(
                pattern_id=pattern_id,
                query_pattern=self._extract_topic(feedback.query),
                learned_behavior=f"For {self._extract_topic(feedback.query)} queries, user prefers: {(feedback.correct_answer or '')[:100]}",
            )
        
        pattern = self.learned_patterns[pattern_id]
        pattern.update_from_feedback(is_positive=True)
        
        LOGGER.info(f"Learned correction pattern: {pattern_id} (confidence: {pattern.confidence:.2f})")
    
    def _learn_avoidance_pattern(self, feedback: UserFeedback) -> None:
        """Learn what to avoid from negative feedback."""
        pattern_id = f"avoid_{self._extract_topic(feedback.query)}"
        
        if pattern_id not in self.learned_patterns:
            self.learned_patterns[pattern_id] = PatternLearning(
                pattern_id=pattern_id,
                query_pattern=self._extract_topic(feedback.query),
                learned_behavior=f"Avoid response style: {feedback.response[:50]}... for {self._extract_topic(feedback.query)}",
            )
        
        pattern = self.learned_patterns[pattern_id]
        pattern.update_from_feedback(is_positive=False)
    
    def get_confidence_adjustment(self, topic: str) -> float:
        """Get learned confidence adjustment for a topic.
        
        Returns:
            Adjustment value (-0.15 to +0.15) to apply to base confidence
        """
        return self.confidence_adjustments.get(topic, 0.0)
    
    def get_topic_performance(self, topic: str) -> Dict[str, float]:
        """Get performance metrics for a topic."""
        if topic not in self.topic_performance:
            return {
                "positive_count": 0.0,
                "total_count": 0.0,
                "avg_rating": 0.5,
                "success_rate": 0.5,
            }
        
        perf = self.topic_performance[topic]
        success_rate = perf["positive_count"] / max(perf["total_count"], 1)
        
        return {
            "positive_count": perf["positive_count"],
            "total_count": perf["total_count"],
            "avg_rating": perf["avg_rating"],
            "success_rate": success_rate,
        }
    
    def get_learned_patterns(
        self,
        *,
        min_confidence: float = 0.6,
        topic: Optional[str] = None,
    ) -> List[PatternLearning]:
        """Get learned patterns above confidence threshold.
        
        Args:
            min_confidence: Minimum confidence to include
            topic: Optional filter by topic
            
        Returns:
            List of learned patterns
        """
        patterns = []
        
        for pattern in self.learned_patterns.values():
            if pattern.confidence < min_confidence:
                continue
            
            if topic and pattern.query_pattern != topic:
                continue
            
            patterns.append(pattern)
        
        # Sort by confidence
        patterns.sort(key=lambda p: p.confidence, reverse=True)
        return patterns
    
    def should_adjust_response(self, query: str) -> Tuple[bool, Optional[str]]:
        """Check if response should be adjusted based on learned patterns.
        
        Returns:
            (should_adjust, adjustment_reason)
        """
        topic = self._extract_topic(query)
        
        # Check for high-confidence patterns
        relevant_patterns = [
            p for p in self.learned_patterns.values()
            if p.query_pattern == topic and p.confidence > 0.7
        ]
        
        if relevant_patterns:
            best_pattern = max(relevant_patterns, key=lambda p: p.confidence)
            return True, best_pattern.learned_behavior
        
        # Check topic performance
        if topic in self.topic_performance:
            perf = self.topic_performance[topic]
            if perf["total_count"] >= 5:
                success_rate = perf["positive_count"] / perf["total_count"]
                if success_rate < 0.5:
                    return True, f"Low success rate ({success_rate:.1%}) for {topic} queries - increase detail"
        
        return False, None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get learning system statistics."""
        total_feedback = len(self.feedback_history)
        positive_feedback = sum(
            1 for f in self.feedback_history
            if f.feedback_type == FeedbackType.POSITIVE
        )
        
        return {
            "total_feedback": total_feedback,
            "positive_feedback": positive_feedback,
            "success_rate": positive_feedback / max(total_feedback, 1),
            "learned_patterns": len(self.learned_patterns),
            "high_confidence_patterns": len([
                p for p in self.learned_patterns.values()
                if p.confidence > 0.7
            ]),
            "topics_tracked": len(self.topic_performance),
            "avg_rating": sum(
                f.rating for f in self.feedback_history if f.rating is not None
            ) / max(sum(1 for f in self.feedback_history if f.rating is not None), 1),
        }
    
    def export_knowledge(self) -> Dict[str, Any]:
        """Export learned knowledge for persistence."""
        return {
            "version": "1.0",
            "timestamp": time.time(),
            "learned_patterns": [
                {
                    "pattern_id": p.pattern_id,
                    "query_pattern": p.query_pattern,
                    "learned_behavior": p.learned_behavior,
                    "confidence": p.confidence,
                    "positive_examples": p.positive_examples,
                    "negative_examples": p.negative_examples,
                }
                for p in self.learned_patterns.values()
            ],
            "topic_performance": dict(self.topic_performance),
            "confidence_adjustments": self.confidence_adjustments,
        }
    
    def import_knowledge(self, knowledge: Dict[str, Any]) -> None:
        """Import previously learned knowledge."""
        if "learned_patterns" in knowledge:
            for p_dict in knowledge["learned_patterns"]:
                pattern = PatternLearning(
                    pattern_id=p_dict["pattern_id"],
                    query_pattern=p_dict["query_pattern"],
                    learned_behavior=p_dict["learned_behavior"],
                    confidence=p_dict["confidence"],
                    positive_examples=p_dict["positive_examples"],
                    negative_examples=p_dict["negative_examples"],
                )
                self.learned_patterns[pattern.pattern_id] = pattern
        
        if "topic_performance" in knowledge:
            self.topic_performance.update(knowledge["topic_performance"])
        
        if "confidence_adjustments" in knowledge:
            self.confidence_adjustments.update(knowledge["confidence_adjustments"])
        
        LOGGER.info(f"Imported {len(self.learned_patterns)} patterns and {len(self.topic_performance)} topic metrics")


# Demo
if __name__ == "__main__":
    print("\n" + "="*70)
    print("📚 KOLIBRI AI — ADAPTIVE LEARNING SYSTEM")
    print("="*70 + "\n")
    
    learning = LearningSystem(learning_rate=0.15)
    
    # Simulate feedback
    print("Simulating user feedback...\n")
    
    # Positive feedback on finance
    learning.add_feedback(
        "What is our Q4 revenue?",
        "Q4 revenue projected at $2.5M",
        FeedbackType.POSITIVE,
        rating=0.9,
    )
    
    learning.add_feedback(
        "Show me sales forecast",
        "Sales forecast shows 15% growth",
        FeedbackType.POSITIVE,
        rating=0.85,
    )
    
    # Negative feedback on calculations
    learning.add_feedback(
        "Calculate average order value",
        "Calculation completed",
        FeedbackType.NEGATIVE,
        feedback_text="Too vague, need actual numbers",
        rating=0.3,
    )
    
    # Correction
    learning.add_feedback(
        "Calculate average order value",
        "Calculation completed",
        FeedbackType.CORRECTION,
        correct_answer="Average order value is $125.50 based on 1,000 orders totaling $125,500",
        rating=0.4,
    )
    
    # More positive on finance
    learning.add_feedback(
        "Quarterly profit margins?",
        "Q3 profit margin at 23%, up from Q2",
        FeedbackType.POSITIVE,
        rating=0.88,
    )
    
    print("\nLearned Patterns:")
    patterns = learning.get_learned_patterns(min_confidence=0.4)
    for pattern in patterns:
        print(f"\n  Pattern: {pattern.pattern_id}")
        print(f"  Topic: {pattern.query_pattern}")
        print(f"  Behavior: {pattern.learned_behavior}")
        print(f"  Confidence: {pattern.confidence:.2%}")
        print(f"  Examples: +{pattern.positive_examples}, -{pattern.negative_examples}")
    
    print("\n" + "-"*70)
    print("\nTopic Performance:")
    for topic in ["finance", "calculation"]:
        perf = learning.get_topic_performance(topic)
        print(f"\n  {topic.upper()}:")
        print(f"    Success rate: {perf['success_rate']:.1%}")
        print(f"    Avg rating: {perf['avg_rating']:.2f}")
        print(f"    Total feedback: {int(perf['total_count'])}")
        
        adj = learning.get_confidence_adjustment(topic)
        if adj != 0:
            print(f"    Confidence adjustment: {adj:+.2f}")
    
    print("\n" + "-"*70)
    print("\nStatistics:")
    print(json.dumps(learning.get_stats(), indent=2))
    
    # Test adjustment recommendation
    print("\n" + "-"*70)
    print("\nTesting adjustment recommendations:")
    
    test_queries = [
        "What is our revenue?",
        "Calculate the total cost",
    ]
    
    for query in test_queries:
        should_adjust, reason = learning.should_adjust_response(query)
        print(f"\nQuery: {query}")
        print(f"  Should adjust: {should_adjust}")
        if reason:
            print(f"  Reason: {reason}")
    
    print("\n" + "="*70 + "\n")
