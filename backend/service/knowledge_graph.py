"""Knowledge Graph for structured AI reasoning.

Implements a semantic network of entities, relationships, and facts
to enable deeper reasoning and inference capabilities.
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

__all__ = [
    "EntityType",
    "RelationType",
    "Entity",
    "Relationship",
    "KnowledgeGraph",
]


class EntityType(str, Enum):
    """Types of entities in the knowledge graph."""
    CONCEPT = "concept"
    PERSON = "person"
    ORGANIZATION = "organization"
    METRIC = "metric"
    EVENT = "event"
    LOCATION = "location"
    DOCUMENT = "document"


class RelationType(str, Enum):
    """Types of relationships between entities."""
    IS_A = "is_a"  # Taxonomy
    PART_OF = "part_of"  # Composition
    RELATES_TO = "relates_to"  # General association
    CAUSES = "causes"  # Causal relationship
    DERIVED_FROM = "derived_from"  # Data lineage
    MEASURED_BY = "measured_by"  # Metrics
    OCCURRED_AT = "occurred_at"  # Temporal
    LOCATED_IN = "located_in"  # Spatial


@dataclass
class Entity:
    """Entity node in the knowledge graph."""
    
    id: str
    name: str
    entity_type: EntityType
    attributes: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0
    created_at: float = field(default_factory=time.time)
    
    def __hash__(self):
        return hash(self.id)
    
    def __eq__(self, other):
        if not isinstance(other, Entity):
            return False
        return self.id == other.id


@dataclass
class Relationship:
    """Relationship edge in the knowledge graph."""
    
    id: str
    source_id: str
    target_id: str
    relation_type: RelationType
    properties: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0
    created_at: float = field(default_factory=time.time)
    
    def __hash__(self):
        return hash(self.id)
    
    def __eq__(self, other):
        if not isinstance(other, Relationship):
            return False
        return self.id == other.id


class KnowledgeGraph:
    """
    Semantic knowledge graph for AI reasoning.
    
    Features:
    - Entity and relationship management
    - Path finding for inference
    - Transitive relationship discovery
    - Confidence propagation
    - Semantic queries
    """
    
    def __init__(self):
        """Initialize empty knowledge graph."""
        self.entities: Dict[str, Entity] = {}
        self.relationships: Dict[str, Relationship] = {}
        
        # Index for fast queries
        self.entity_by_type: Dict[EntityType, Set[str]] = {}
        self.outgoing_edges: Dict[str, Set[str]] = {}  # entity_id -> rel_ids
        self.incoming_edges: Dict[str, Set[str]] = {}  # entity_id -> rel_ids
        self.rel_by_type: Dict[RelationType, Set[str]] = {}
    
    def add_entity(
        self,
        entity_id: str,
        name: str,
        entity_type: EntityType,
        *,
        attributes: Optional[Dict[str, Any]] = None,
        confidence: float = 1.0,
    ) -> Entity:
        """Add or update an entity in the graph.
        
        Args:
            entity_id: Unique identifier
            name: Human-readable name
            entity_type: Type of entity
            attributes: Optional attributes dict
            confidence: Confidence score (0.0 to 1.0)
            
        Returns:
            Entity object
        """
        entity = Entity(
            id=entity_id,
            name=name,
            entity_type=entity_type,
            attributes=attributes or {},
            confidence=confidence,
        )
        
        self.entities[entity_id] = entity
        
        # Index by type
        if entity_type not in self.entity_by_type:
            self.entity_by_type[entity_type] = set()
        self.entity_by_type[entity_type].add(entity_id)
        
        # Initialize edge lists
        if entity_id not in self.outgoing_edges:
            self.outgoing_edges[entity_id] = set()
        if entity_id not in self.incoming_edges:
            self.incoming_edges[entity_id] = set()
        
        return entity
    
    def add_relationship(
        self,
        source_id: str,
        target_id: str,
        relation_type: RelationType,
        *,
        properties: Optional[Dict[str, Any]] = None,
        confidence: float = 1.0,
    ) -> Optional[Relationship]:
        """Add a relationship between two entities.
        
        Args:
            source_id: Source entity ID
            target_id: Target entity ID
            relation_type: Type of relationship
            properties: Optional properties dict
            confidence: Confidence score (0.0 to 1.0)
            
        Returns:
            Relationship object or None if entities don't exist
        """
        if source_id not in self.entities or target_id not in self.entities:
            return None
        
        rel_id = f"{source_id}_{relation_type.value}_{target_id}"
        
        relationship = Relationship(
            id=rel_id,
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type,
            properties=properties or {},
            confidence=confidence,
        )
        
        self.relationships[rel_id] = relationship
        
        # Index edges
        self.outgoing_edges[source_id].add(rel_id)
        self.incoming_edges[target_id].add(rel_id)
        
        # Index by type
        if relation_type not in self.rel_by_type:
            self.rel_by_type[relation_type] = set()
        self.rel_by_type[relation_type].add(rel_id)
        
        return relationship
    
    def get_entity(self, entity_id: str) -> Optional[Entity]:
        """Get entity by ID."""
        return self.entities.get(entity_id)
    
    def get_entities_by_type(self, entity_type: EntityType) -> List[Entity]:
        """Get all entities of a specific type."""
        entity_ids = self.entity_by_type.get(entity_type, set())
        return [self.entities[eid] for eid in entity_ids]
    
    def get_relationships(
        self,
        source_id: Optional[str] = None,
        target_id: Optional[str] = None,
        relation_type: Optional[RelationType] = None,
    ) -> List[Relationship]:
        """Query relationships by source, target, or type."""
        # Start with all relationships
        candidates = set(self.relationships.keys())
        
        # Filter by source
        if source_id:
            candidates &= self.outgoing_edges.get(source_id, set())
        
        # Filter by target
        if target_id:
            candidates &= self.incoming_edges.get(target_id, set())
        
        # Filter by type
        if relation_type:
            candidates &= self.rel_by_type.get(relation_type, set())
        
        return [self.relationships[rid] for rid in candidates]
    
    def find_path(
        self,
        start_id: str,
        end_id: str,
        *,
        max_depth: int = 5,
    ) -> Optional[List[str]]:
        """Find shortest path between two entities using BFS.
        
        Args:
            start_id: Starting entity ID
            end_id: Target entity ID
            max_depth: Maximum path length
            
        Returns:
            List of entity IDs forming path, or None if no path exists
        """
        if start_id not in self.entities or end_id not in self.entities:
            return None
        
        if start_id == end_id:
            return [start_id]
        
        # BFS
        queue = [(start_id, [start_id])]
        visited = {start_id}
        
        while queue:
            current_id, path = queue.pop(0)
            
            if len(path) > max_depth:
                continue
            
            # Get all neighbors (both outgoing and incoming)
            neighbors = set()
            for rel_id in self.outgoing_edges.get(current_id, []):
                rel = self.relationships[rel_id]
                neighbors.add(rel.target_id)
            
            for rel_id in self.incoming_edges.get(current_id, []):
                rel = self.relationships[rel_id]
                neighbors.add(rel.source_id)
            
            for neighbor_id in neighbors:
                if neighbor_id in visited:
                    continue
                
                new_path = path + [neighbor_id]
                
                if neighbor_id == end_id:
                    return new_path
                
                visited.add(neighbor_id)
                queue.append((neighbor_id, new_path))
        
        return None
    
    def infer_transitive_relationships(
        self,
        relation_type: RelationType,
        *,
        min_confidence: float = 0.5,
    ) -> List[Tuple[str, str, float]]:
        """Infer new transitive relationships.
        
        For example: If A -> B and B -> C, infer A -> C.
        
        Args:
            relation_type: Type of relationship to consider
            min_confidence: Minimum confidence for inferred relationships
            
        Returns:
            List of (source_id, target_id, confidence) tuples
        """
        inferred = []
        
        # Get all relationships of this type
        rels = [
            self.relationships[rid]
            for rid in self.rel_by_type.get(relation_type, [])
        ]
        
        # For each pair of relationships where target of first = source of second
        for rel1 in rels:
            for rel2 in rels:
                if rel1.target_id == rel2.source_id:
                    # Check if direct relationship already exists
                    direct = self.get_relationships(
                        source_id=rel1.source_id,
                        target_id=rel2.target_id,
                        relation_type=relation_type,
                    )
                    
                    if not direct:
                        # Infer with confidence = product of confidences
                        conf = rel1.confidence * rel2.confidence
                        if conf >= min_confidence:
                            inferred.append((rel1.source_id, rel2.target_id, conf))
        
        return inferred
    
    def query(self, pattern: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Query graph using a pattern.
        
        Pattern example:
        {
            "entity_type": "metric",
            "attributes": {"category": "finance"},
            "relationships": [{"type": "measured_by", "target_type": "concept"}]
        }
        
        Args:
            pattern: Query pattern dictionary
            
        Returns:
            List of matching results
        """
        results = []
        
        # Start with entities matching type
        if "entity_type" in pattern:
            candidates = self.get_entities_by_type(EntityType(pattern["entity_type"]))
        else:
            candidates = list(self.entities.values())
        
        # Filter by attributes
        if "attributes" in pattern:
            attr_filters = pattern["attributes"]
            candidates = [
                e for e in candidates
                if all(
                    e.attributes.get(k) == v
                    for k, v in attr_filters.items()
                )
            ]
        
        # Filter by relationships
        if "relationships" in pattern:
            for rel_pattern in pattern["relationships"]:
                rel_type = RelationType(rel_pattern["type"])
                target_type = EntityType(rel_pattern.get("target_type")) if "target_type" in rel_pattern else None
                
                filtered = []
                for entity in candidates:
                    rels = self.get_relationships(source_id=entity.id, relation_type=rel_type)
                    
                    if rels:
                        if target_type:
                            # Check target types
                            valid = any(
                                self.entities[rel.target_id].entity_type == target_type
                                for rel in rels
                            )
                            if valid:
                                filtered.append(entity)
                        else:
                            filtered.append(entity)
                
                candidates = filtered
        
        # Format results
        for entity in candidates:
            results.append({
                "entity": {
                    "id": entity.id,
                    "name": entity.name,
                    "type": entity.entity_type.value,
                    "attributes": entity.attributes,
                    "confidence": entity.confidence,
                },
                "relationships": [
                    {
                        "type": rel.relation_type.value,
                        "target": self.entities[rel.target_id].name,
                        "properties": rel.properties,
                    }
                    for rel_id in self.outgoing_edges.get(entity.id, [])
                    for rel in [self.relationships[rel_id]]
                ],
            })
        
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """Get graph statistics."""
        return {
            "total_entities": len(self.entities),
            "total_relationships": len(self.relationships),
            "entity_types": {
                etype.value: len(entities)
                for etype, entities in self.entity_by_type.items()
            },
            "relationship_types": {
                rtype.value: len(rels)
                for rtype, rels in self.rel_by_type.items()
            },
        }


# Demo
if __name__ == "__main__":
    print("\n" + "="*70)
    print("🔗 KOLIBRI AI — KNOWLEDGE GRAPH SYSTEM")
    print("="*70 + "\n")
    
    kg = KnowledgeGraph()
    
    # Build example knowledge graph
    print("Building knowledge graph...\n")
    
    # Entities
    kg.add_entity("q4_2024", "Q4 2024", EntityType.EVENT, attributes={"quarter": 4, "year": 2024})
    kg.add_entity("revenue", "Revenue", EntityType.METRIC, attributes={"category": "finance", "unit": "USD"})
    kg.add_entity("expenses", "Expenses", EntityType.METRIC, attributes={"category": "finance", "unit": "USD"})
    kg.add_entity("profit", "Profit", EntityType.METRIC, attributes={"category": "finance", "unit": "USD"})
    kg.add_entity("growth_rate", "Growth Rate", EntityType.METRIC, attributes={"category": "finance", "unit": "percent"})
    kg.add_entity("business_unit", "Business Unit Alpha", EntityType.ORGANIZATION)
    
    # Relationships
    kg.add_relationship("revenue", "q4_2024", RelationType.OCCURRED_AT, confidence=0.95)
    kg.add_relationship("expenses", "q4_2024", RelationType.OCCURRED_AT, confidence=0.95)
    kg.add_relationship("profit", "revenue", RelationType.DERIVED_FROM, confidence=1.0)
    kg.add_relationship("profit", "expenses", RelationType.DERIVED_FROM, confidence=1.0)
    kg.add_relationship("growth_rate", "revenue", RelationType.MEASURED_BY, confidence=0.9)
    kg.add_relationship("revenue", "business_unit", RelationType.MEASURED_BY, confidence=0.85)
    
    print(f"✓ Created {len(kg.entities)} entities and {len(kg.relationships)} relationships\n")
    
    # Path finding
    print("-"*70)
    print("\n🔍 Path Finding:\n")
    
    path = kg.find_path("growth_rate", "business_unit")
    if path:
        print("Path from 'growth_rate' to 'business_unit':")
        for i, entity_id in enumerate(path):
            entity = kg.get_entity(entity_id)
            if entity:
                print(f"  {i+1}. {entity.name} ({entity.entity_type.value})")
    
    # Transitive inference
    print("\n" + "-"*70)
    print("\nTransitive Inference:\n")
    
    inferred = kg.infer_transitive_relationships(RelationType.DERIVED_FROM)
    print(f"Found {len(inferred)} inferred relationships")
    for source_id, target_id, conf in inferred:
        source = kg.get_entity(source_id)
        target = kg.get_entity(target_id)
        if source and target:
            print(f"  {source.name} -> {target.name} (confidence: {conf:.2f})")
    
    # Query
    print("\n" + "-"*70)
    print("\n📊 Semantic Query:\n")
    
    results = kg.query({
        "entity_type": "metric",
        "attributes": {"category": "finance"},
    })
    
    print(f"Finance metrics: {len(results)} found")
    for result in results:
        entity = result["entity"]
        rels = result["relationships"]
        print(f"\n  {entity['name']}:")
        print(f"    Type: {entity['type']}")
        print(f"    Confidence: {entity['confidence']:.2f}")
        if rels:
            print("    Relationships:")
            for rel in rels:
                print(f"      - {rel['type']} -> {rel['target']}")
    
    # Statistics
    print("\n" + "-"*70)
    print("\n📈 Graph Statistics:\n")
    print(json.dumps(kg.get_stats(), indent=2))
    
    print("\n" + "="*70 + "\n")
