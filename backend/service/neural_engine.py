"""Lightweight neural inference engine for Kolibri AI.

This module provides a self-contained neural network that performs
intent classification and prompt selection using only standard Python.
It offers an actual learning component (training with gradient descent)
that operates entirely offline, matching the project's requirements for
verifiable, energy-efficient AI behaviour.
"""

from __future__ import annotations

import hashlib
import json
import math
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

from backend.service.prompt_catalog import PROMPT_CATALOG, select_variant


def _contains_cyrillic(text: str) -> bool:
    """Return ``True`` when the text includes Cyrillic characters."""

    return any("\u0400" <= char <= "\u04FF" for char in text)


class HashingVectorizer:
    """Very small hashing vectorizer with deterministic tokenisation."""

    def __init__(self, *, num_features: int = 128) -> None:
        self._num_features = num_features

    @property
    def dimension(self) -> int:
        return self._num_features

    def _tokenise(self, text: str) -> List[str]:
        tokens: List[str] = []
        buffer: List[str] = []
        for char in text.lower():
            if char.isalnum():
                buffer.append(char)
            else:
                if buffer:
                    tokens.append("".join(buffer))
                    buffer.clear()
        if buffer:
            tokens.append("".join(buffer))

        # Add bigrams for more context when possible
        if len(tokens) >= 2:
            bigrams = [f"{tokens[i]}_{tokens[i + 1]}" for i in range(len(tokens) - 1)]
        else:
            bigrams = []
        return tokens + bigrams

    def transform(self, text: str) -> Tuple[List[float], List[str], Dict[str, int]]:
        """Transform text into a hashed feature vector.

        Returns a tuple: ``(features, tokens, token_counts)``.
        """

        tokens = self._tokenise(text)
        counts: Dict[int, float] = {}
        token_counts: Dict[str, int] = {}

        for token in tokens:
            digest = hashlib.sha1(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self._num_features
            counts[index] = counts.get(index, 0.0) + 1.0
            token_counts[token] = token_counts.get(token, 0) + 1

        if counts:
            max_count = max(counts.values())
        else:
            max_count = 1.0

        features = [0.0] * self._num_features
        for index, value in counts.items():
            features[index] = value / max_count

        return features, tokens, token_counts


def _relu(value: float) -> float:
    return value if value > 0 else 0.0


def _softmax(values: Sequence[float]) -> List[float]:
    if not values:
        return []
    max_val = max(values)
    exps = [math.exp(v - max_val) for v in values]
    total = sum(exps)
    if total == 0:
        return [1.0 / len(values)] * len(values)
    return [value / total for value in exps]


class _FeedForwardNetwork:
    """Small fully-connected neural network (one hidden layer)."""

    def __init__(
        self,
        *,
        input_dim: int,
        hidden_dim: int,
        output_dim: int,
        learning_rate: float = 0.05,
        seed: int = 42,
    ) -> None:
        random.seed(seed)
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.output_dim = output_dim
        self.learning_rate = learning_rate

        self.W1 = [
            [random.uniform(-0.5, 0.5) / max(1, input_dim) for _ in range(input_dim)]
            for _ in range(hidden_dim)
        ]
        self.b1 = [0.0 for _ in range(hidden_dim)]
        self.W2 = [
            [random.uniform(-0.5, 0.5) / max(1, hidden_dim) for _ in range(hidden_dim)]
            for _ in range(output_dim)
        ]
        self.b2 = [0.0 for _ in range(output_dim)]

    def _forward(self, features: Sequence[float]) -> Tuple[List[float], List[float], List[float]]:
        hidden_pre: List[float] = []
        hidden: List[float] = []
        for j in range(self.hidden_dim):
            total = self.b1[j]
            weights = self.W1[j]
            total += sum(weights[i] * features[i] for i in range(self.input_dim))
            hidden_pre.append(total)
            hidden.append(_relu(total))

        logits: List[float] = []
        for k in range(self.output_dim):
            total = self.b2[k]
            weights = self.W2[k]
            total += sum(weights[j] * hidden[j] for j in range(self.hidden_dim))
            logits.append(total)

        return hidden_pre, hidden, logits

    def predict_proba(self, features: Sequence[float]) -> List[float]:
        _, _, logits = self._forward(features)
        return _softmax(logits)

    def train(self, dataset: Iterable[Tuple[Sequence[float], int]], epochs: int = 400) -> None:
        dataset = list(dataset)
        if not dataset:
            return

        for epoch in range(epochs):
            total_loss = 0.0
            for features, label in dataset:
                hidden_pre, hidden, logits = self._forward(features)
                probs = _softmax(logits)

                # Cross-entropy loss gradient
                grad_logits = [prob for prob in probs]
                grad_logits[label] -= 1.0
                total_loss += -math.log(probs[label] + 1e-12)

                # Back-propagate into the hidden layer (before updating weights)
                grad_hidden: List[float] = []
                for j in range(self.hidden_dim):
                    backflow = sum(self.W2[k][j] * grad_logits[k] for k in range(self.output_dim))
                    grad_hidden.append(backflow * (1.0 if hidden_pre[j] > 0 else 0.0))

                # Update output weights
                for k in range(self.output_dim):
                    for j in range(self.hidden_dim):
                        self.W2[k][j] -= self.learning_rate * grad_logits[k] * hidden[j]
                    self.b2[k] -= self.learning_rate * grad_logits[k]

                # Update input weights
                for j in range(self.hidden_dim):
                    grad_value = grad_hidden[j]
                    if grad_value == 0:
                        continue
                    weights = self.W1[j]
                    for i in range(self.input_dim):
                        weights[i] -= self.learning_rate * grad_value * features[i]
                    self.b1[j] -= self.learning_rate * grad_value

            if total_loss / max(1, len(dataset)) < 1e-4:
                break


@dataclass(frozen=True)
class NeuralInferenceResult:
    """Structured response returned by :class:`NeuralReasoner`."""

    response: str
    confidence: float
    trace: List[Dict[str, object]]
    energy_cost_j: float


class NeuralReasoner:
    """Hybrid neural intent classifier and prompt composer."""

    def __init__(self) -> None:
        data_path = Path(__file__).with_name("data") / "intent_samples.json"
        payload = json.loads(data_path.read_text(encoding="utf-8"))
        samples = payload.get("samples", [])
        if not samples:
            raise ValueError("Intent dataset is empty")

        self.vectorizer = HashingVectorizer(num_features=128)
        intents = sorted({sample["intent"] for sample in samples if "intent" in sample})
        self.intent_to_index = {intent: idx for idx, intent in enumerate(intents)}
        self.index_to_intent = {idx: intent for intent, idx in self.intent_to_index.items()}

        # Prepare training data
        training_examples: List[Tuple[List[float], int]] = []
        for sample in samples:
            intent = sample.get("intent")
            text = sample.get("text", "")
            if not intent or intent not in self.intent_to_index:
                continue
            features, _, _ = self.vectorizer.transform(text)
            training_examples.append((features, self.intent_to_index[intent]))

        self.network = _FeedForwardNetwork(
            input_dim=self.vectorizer.dimension,
            hidden_dim=48,
            output_dim=len(self.intent_to_index),
            learning_rate=0.08,
        )
        self.network.train(training_examples, epochs=500)

    def _compose_response(
        self,
        *,
        intent: str,
        query: str,
        language: str,
        top_terms: List[Tuple[str, int]],
    ) -> Tuple[str, Dict[str, object]]:
        variant = select_variant(query)
        prompts, settings = PROMPT_CATALOG.get_prompts(intent, variant, language=language)

        if prompts:
            body_segments = [prompt.body for prompt in prompts[:2]]
            prompt_ids = [prompt.id for prompt in prompts[:3]]
        else:
            body_segments = [
                "Я продолжаю анализ, чтобы предложить релевантные шаги.",
            ]
            prompt_ids = []

        key_terms = ", ".join(term for term, _ in top_terms[:3]) or "контекст уточняется"
        response = " ".join(body_segments)
        response += f"\n\n🔍 Фокусируюсь на сигналах: {key_terms}."

        metadata: Dict[str, object] = {
            "variant": variant,
            "prompt_ids": prompt_ids,
            "tone": settings.get("tone") if settings else None,
            "temperature": settings.get("temperature") if settings else None,
        }
        return response, metadata

    def infer(self, query: str) -> NeuralInferenceResult:
        features, tokens, token_counts = self.vectorizer.transform(query)
        probabilities = self.network.predict_proba(features)

        if not probabilities:
            raise ValueError("Neural network returned empty distribution")

        top_index = max(range(len(probabilities)), key=lambda idx: probabilities[idx])
        top_intent = self.index_to_intent[top_index]
        confidence = probabilities[top_index]

        language = "ru" if _contains_cyrillic(query) else "en"
        sorted_terms = sorted(token_counts.items(), key=lambda item: (-item[1], item[0]))
        response, prompt_metadata = self._compose_response(
            intent=top_intent,
            query=query,
            language=language,
            top_terms=sorted_terms,
        )

        intent_distribution = [
            {
                "intent": self.index_to_intent[idx],
                "probability": round(prob, 4),
            }
            for idx, prob in sorted(
                enumerate(probabilities), key=lambda item: item[1], reverse=True
            )
        ]

        trace: List[Dict[str, object]] = [
            {
                "stage": "neural_vectorization",
                "token_count": len(tokens),
                "feature_dimension": self.vectorizer.dimension,
                "top_terms": sorted_terms[:5],
            },
            {
                "stage": "neural_inference",
                "intent_distribution": intent_distribution[:5],
                "predicted_intent": top_intent,
                "confidence": round(confidence, 4),
            },
            {
                "stage": "prompt_selection",
                **prompt_metadata,
            },
        ]

        energy_cost = 0.35 + 0.02 * len(tokens)

        return NeuralInferenceResult(
            response=response,
            confidence=confidence,
            trace=trace,
            energy_cost_j=round(energy_cost, 3),
        )

