import os
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
import difflib

logger = logging.getLogger(__name__)

@dataclass
class KnowledgeSource:
    """Represents a knowledge source with metadata"""
    source_type: str  # "document", "prompt", "market"
    content: Dict[str, Any]
    confidence: float
    timestamp: str
    source_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class ConflictResolution:
    """Represents a conflict resolution decision"""
    field: str
    sources: List[str]
    resolution: str
    confidence: float
    reasoning: str

class KnowledgeFusionService:
    """
    Intelligent knowledge fusion service that combines knowledge from multiple sources
    (documents, prompts, market data) with conflict resolution and confidence scoring.
    """
    
    def __init__(self):
        self.fusion_strategies = {
            "document": {"priority": 0.9, "weight": 0.4},
            "prompt": {"priority": 0.7, "weight": 0.3},
            "market": {"priority": 0.8, "weight": 0.3}
        }
        
        # Conflict resolution strategies
        self.conflict_resolution_strategies = {
            "highest_confidence": self._resolve_by_highest_confidence,
            "weighted_voting": self._resolve_by_weighted_voting,
            "source_priority": self._resolve_by_source_priority,
            "consensus": self._resolve_by_consensus,
            "merge": self._resolve_by_merge
        }
    
    def fuse_knowledge(self, 
                       document_knowledge: Dict[str, Any], 
                       prompt_knowledge: Dict[str, Any], 
                       market_knowledge: Dict[str, Any]) -> Dict[str, Any]:
        """
        Combines knowledge from documents, user prompts, and market intelligence into a single,
        coherent knowledge base, resolving conflicts based on predefined strategies.
        
        Args:
            document_knowledge: Knowledge extracted from uploaded documents.
            prompt_knowledge: Knowledge derived from user's prompt analysis.
            market_knowledge: Knowledge from real-time market intelligence.
            
        Returns:
            A dictionary representing the fused and reconciled knowledge.
        """
        logger.info("Starting knowledge fusion process...")
        
        # Use the existing combine_knowledge_sources method
        return self.combine_knowledge_sources(
            document_knowledge=document_knowledge,
            prompt_knowledge=prompt_knowledge,
            market_data=market_knowledge
        )

    def combine_knowledge_sources(self, document_knowledge: Dict[str, Any] = None,
                                prompt_knowledge: Dict[str, Any] = None,
                                market_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Combine knowledge from multiple sources into a unified knowledge base.
        
        Args:
            document_knowledge: Knowledge extracted from documents
            prompt_knowledge: Knowledge generated from prompts
            market_data: Market intelligence data
            
        Returns:
            Unified knowledge structure with conflict resolution
        """
        logger.info("Starting knowledge fusion process")
        
        # Prepare knowledge sources
        sources = []
        
        if document_knowledge:
            sources.append(KnowledgeSource(
                source_type="document",
                content=document_knowledge,
                confidence=0.9,
                timestamp=datetime.now().isoformat(),
                metadata={"extraction_method": "claude_ai"}
            ))
        
        if prompt_knowledge:
            sources.append(KnowledgeSource(
                source_type="prompt",
                content=prompt_knowledge,
                confidence=0.7,
                timestamp=datetime.now().isoformat(),
                metadata={"extraction_method": "llm_generated"}
            ))
        
        if market_data:
            sources.append(KnowledgeSource(
                source_type="market",
                content=market_data,
                confidence=0.8,
                timestamp=datetime.now().isoformat(),
                metadata={"extraction_method": "grok_api"}
            ))
        
        if not sources:
            logger.warning("No knowledge sources provided for fusion")
            return self._get_empty_knowledge_structure()
        
        # Perform fusion
        fused_knowledge = self._fuse_knowledge_sources(sources)
        
        # Add fusion metadata
        fused_knowledge["fusion_metadata"] = {
            "sources_used": [s.source_type for s in sources],
            "fusion_timestamp": datetime.now().isoformat(),
            "conflicts_resolved": len(fused_knowledge.get("conflicts", [])),
            "overall_confidence": self.calculate_unified_confidence(sources)
        }
        
        logger.info(f"Knowledge fusion completed with {len(sources)} sources")
        return fused_knowledge
    
    def _fuse_knowledge_sources(self, sources: List[KnowledgeSource]) -> Dict[str, Any]:
        """Fuse multiple knowledge sources into a unified structure"""
        logger.info(f"Fusing {len(sources)} knowledge sources")
        
        # Initialize unified structure
        unified = self._get_empty_knowledge_structure()
        conflicts = []
        
        # Define knowledge fields to fuse
        knowledge_fields = [
            "company_info", "products", "value_propositions", "target_audience",
            "sales_approach", "competitive_advantages", "key_messages"
        ]
        
        # Process each field
        for field in knowledge_fields:
            field_values = []
            
            # Collect values from all sources
            for source in sources:
                if field in source.content:
                    field_values.append({
                        "source": source.source_type,
                        "value": source.content[field],
                        "confidence": source.confidence,
                        "metadata": source.metadata
                    })
            
            if not field_values:
                continue
            
            # Fuse field values
            fused_field, field_conflicts = self._fuse_field_values(field, field_values)
            unified[field] = fused_field
            
            if field_conflicts:
                conflicts.extend(field_conflicts)
        
        # Add conflicts to unified structure
        if conflicts:
            unified["conflicts"] = conflicts
        
        return unified
    
    def _fuse_field_values(self, field: str, field_values: List[Dict[str, Any]]) -> Tuple[Any, List[Dict[str, Any]]]:
        """Fuse values for a specific field from multiple sources"""
        conflicts = []
        
        if len(field_values) == 1:
            # Single source, no conflicts
            return field_values[0]["value"], conflicts
        
        # Check for conflicts
        conflicts = self._detect_conflicts(field, field_values)
        
        if conflicts:
            # Resolve conflicts
            resolved_value = self.resolve_conflicts(field, field_values, conflicts)
            return resolved_value, conflicts
        else:
            # No conflicts, merge values
            merged_value = self._merge_field_values(field, field_values)
            return merged_value, conflicts
    
    def _detect_conflicts(self, field: str, field_values: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect conflicts between field values from different sources"""
        conflicts = []
        
        if field == "company_info":
            conflicts.extend(self._detect_company_info_conflicts(field_values))
        elif field == "target_audience":
            conflicts.extend(self._detect_target_audience_conflicts(field_values))
        elif field == "value_propositions":
            conflicts.extend(self._detect_value_proposition_conflicts(field_values))
        elif field == "sales_approach":
            conflicts.extend(self._detect_sales_approach_conflicts(field_values))
        
        return conflicts
    
    def _detect_company_info_conflicts(self, field_values: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect conflicts in company information"""
        conflicts = []
        
        # Group by source
        source_values = {fv["source"]: fv["value"] for fv in field_values}
        
        # Check for conflicting company names
        company_names = []
        for source, value in source_values.items():
            if isinstance(value, dict) and "company_name" in value:
                company_names.append((source, value["company_name"]))
        
        if len(set(name[1] for name in company_names)) > 1:
            conflicts.append({
                "field": "company_name",
                "sources": [name[0] for name in company_names],
                "values": [name[1] for name in company_names],
                "conflict_type": "value_mismatch"
            })
        
        # Check for conflicting industries
        industries = []
        for source, value in source_values.items():
            if isinstance(value, dict) and "industry" in value:
                industries.append((source, value["industry"]))
        
        if len(set(ind[1] for ind in industries)) > 1:
            conflicts.append({
                "field": "industry",
                "sources": [ind[0] for ind in industries],
                "values": [ind[1] for ind in industries],
                "conflict_type": "value_mismatch"
            })
        
        return conflicts
    
    def _detect_target_audience_conflicts(self, field_values: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect conflicts in target audience information"""
        conflicts = []
        
        # Check for conflicting roles
        all_roles = []
        for fv in field_values:
            value = fv["value"]
            if isinstance(value, dict) and "roles" in value:
                roles = value["roles"] if isinstance(value["roles"], list) else [value["roles"]]
                all_roles.extend([(fv["source"], role) for role in roles])
        
        # Group by role and check for conflicts
        role_sources = {}
        for source, role in all_roles:
            if role not in role_sources:
                role_sources[role] = []
            role_sources[role].append(source)
        
        # Check for roles mentioned by conflicting sources
        for role, sources in role_sources.items():
            if len(set(sources)) > 1:
                conflicts.append({
                    "field": f"target_audience.roles.{role}",
                    "sources": sources,
                    "values": [role] * len(sources),
                    "conflict_type": "source_disagreement"
                })
        
        return conflicts
    
    def _detect_value_proposition_conflicts(self, field_values: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect conflicts in value propositions"""
        conflicts = []
        
        # Check for contradictory value propositions
        all_vps = []
        for fv in field_values:
            value = fv["value"]
            if isinstance(value, list):
                all_vps.extend([(fv["source"], vp) for vp in value])
            elif isinstance(value, str):
                all_vps.append((fv["source"], value))
        
        # Check for contradictory language
        contradictory_pairs = [
            ("increase", "decrease"),
            ("reduce", "increase"),
            ("save", "cost"),
            ("fast", "slow"),
            ("simple", "complex")
        ]
        
        for source1, vp1 in all_vps:
            for source2, vp2 in all_vps:
                if source1 != source2:
                    for pos_word, neg_word in contradictory_pairs:
                        if pos_word in vp1.lower() and neg_word in vp2.lower():
                            conflicts.append({
                                "field": "value_propositions",
                                "sources": [source1, source2],
                                "values": [vp1, vp2],
                                "conflict_type": "contradictory_language"
                            })
        
        return conflicts
    
    def _detect_sales_approach_conflicts(self, field_values: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect conflicts in sales approach"""
        conflicts = []
        
        # Check for conflicting methodologies
        methodologies = []
        for fv in field_values:
            value = fv["value"]
            if isinstance(value, dict) and "methodology" in value:
                methodologies.append((fv["source"], value["methodology"]))
            elif isinstance(value, str):
                methodologies.append((fv["source"], value))
        
        if len(set(meth[1] for meth in methodologies)) > 1:
            conflicts.append({
                "field": "sales_approach",
                "sources": [meth[0] for meth in methodologies],
                "values": [meth[1] for meth in methodologies],
                "conflict_type": "methodology_mismatch"
            })
        
        return conflicts
    
    def resolve_conflicts(self, field: str, field_values: List[Dict[str, Any]], 
                         conflicts: List[Dict[str, Any]]) -> Any:
        """
        Resolve conflicts using intelligent strategies.
        
        Args:
            field: Field name
            field_values: Values from different sources
            conflicts: Detected conflicts
            
        Returns:
            Resolved value
        """
        logger.info(f"Resolving {len(conflicts)} conflicts for field: {field}")
        
        resolved_values = []
        
        for conflict in conflicts:
            conflict_field = conflict["field"]
            sources = conflict["sources"]
            values = conflict["values"]
            
            # Select resolution strategy based on conflict type
            strategy = self._select_resolution_strategy(conflict)
            
            # Apply resolution strategy
            resolution = self.conflict_resolution_strategies[strategy](
                conflict_field, sources, values, field_values
            )
            
            resolved_values.append(resolution)
        
        # Apply resolved values to field
        return self._apply_resolutions(field, field_values, resolved_values)
    
    def _select_resolution_strategy(self, conflict: Dict[str, Any]) -> str:
        """Select the best resolution strategy for a conflict"""
        conflict_type = conflict.get("conflict_type", "value_mismatch")
        
        strategy_map = {
            "value_mismatch": "highest_confidence",
            "source_disagreement": "weighted_voting",
            "contradictory_language": "consensus",
            "methodology_mismatch": "source_priority"
        }
        
        return strategy_map.get(conflict_type, "highest_confidence")
    
    def _resolve_by_highest_confidence(self, field: str, sources: List[str], 
                                     values: List[str], field_values: List[Dict[str, Any]]) -> ConflictResolution:
        """Resolve conflict by selecting the value with highest confidence"""
        # Find the field value with highest confidence
        best_value = None
        best_confidence = 0
        best_source = None
        
        for fv in field_values:
            if fv["source"] in sources and fv["confidence"] > best_confidence:
                best_confidence = fv["confidence"]
                best_value = fv["value"]
                best_source = fv["source"]
        
        return ConflictResolution(
            field=field,
            sources=sources,
            resolution=best_value,
            confidence=best_confidence,
            reasoning=f"Selected value from {best_source} with highest confidence ({best_confidence:.2f})"
        )
    
    def _resolve_by_weighted_voting(self, field: str, sources: List[str], 
                                  values: List[str], field_values: List[Dict[str, Any]]) -> ConflictResolution:
        """Resolve conflict using weighted voting based on source priority"""
        # Calculate weighted scores
        weighted_scores = {}
        
        for fv in field_values:
            if fv["source"] in sources:
                source_type = fv["source"]
                weight = self.fusion_strategies.get(source_type, {}).get("weight", 0.5)
                confidence = fv["confidence"]
                
                score = weight * confidence
                
                if fv["value"] not in weighted_scores:
                    weighted_scores[fv["value"]] = 0
                weighted_scores[fv["value"]] += score
        
        # Select value with highest weighted score
        best_value = max(weighted_scores.items(), key=lambda x: x[1])
        
        return ConflictResolution(
            field=field,
            sources=sources,
            resolution=best_value[0],
            confidence=best_value[1],
            reasoning=f"Weighted voting selected value with score {best_value[1]:.2f}"
        )
    
    def _resolve_by_source_priority(self, field: str, sources: List[str], 
                                  values: List[str], field_values: List[Dict[str, Any]]) -> ConflictResolution:
        """Resolve conflict by source priority (document > prompt > market)"""
        source_priority = {"document": 3, "prompt": 2, "market": 1}
        
        best_value = None
        best_priority = 0
        best_source = None
        
        for fv in field_values:
            if fv["source"] in sources:
                priority = source_priority.get(fv["source"], 0)
                if priority > best_priority:
                    best_priority = priority
                    best_value = fv["value"]
                    best_source = fv["source"]
        
        return ConflictResolution(
            field=field,
            sources=sources,
            resolution=best_value,
            confidence=0.8,  # High confidence for priority-based resolution
            reasoning=f"Selected value from {best_source} based on source priority"
        )
    
    def _resolve_by_consensus(self, field: str, sources: List[str], 
                            values: List[str], field_values: List[Dict[str, Any]]) -> ConflictResolution:
        """Resolve conflict by finding consensus or most common value"""
        # Count occurrences of each value
        value_counts = {}
        for value in values:
            value_counts[value] = value_counts.get(value, 0) + 1
        
        # Find most common value
        most_common = max(value_counts.items(), key=lambda x: x[1])
        
        return ConflictResolution(
            field=field,
            sources=sources,
            resolution=most_common[0],
            confidence=most_common[1] / len(values),
            reasoning=f"Consensus resolution: {most_common[0]} appears {most_common[1]} times"
        )
    
    def _resolve_by_merge(self, field: str, sources: List[str], 
                        values: List[str], field_values: List[Dict[str, Any]]) -> ConflictResolution:
        """Resolve conflict by merging values intelligently"""
        merged_value = None
        
        if field == "company_info":
            merged_value = self._merge_company_info(values)
        elif field == "target_audience":
            merged_value = self._merge_target_audience(values)
        elif field == "value_propositions":
            merged_value = self._merge_value_propositions(values)
        else:
            # Default: combine unique values
            merged_value = list(set(values))
        
        return ConflictResolution(
            field=field,
            sources=sources,
            resolution=merged_value,
            confidence=0.7,
            reasoning="Merged conflicting values intelligently"
        )
    
    def _merge_company_info(self, values: List[Any]) -> Dict[str, Any]:
        """Merge company information from multiple sources"""
        merged = {}
        
        for value in values:
            if isinstance(value, dict):
                for key, val in value.items():
                    if val and val != "Not specified":
                        if key not in merged or merged[key] == "Not specified":
                            merged[key] = val
        
        return merged
    
    def _merge_target_audience(self, values: List[Any]) -> Dict[str, Any]:
        """Merge target audience information"""
        merged = {
            "roles": [],
            "industries": [],
            "company_sizes": [],
            "pain_points": []
        }
        
        for value in values:
            if isinstance(value, dict):
                for key, val in value.items():
                    if key in merged and isinstance(val, list):
                        merged[key].extend(val)
                    elif key in merged and val:
                        merged[key].append(val)
        
        # Remove duplicates
        for key in merged:
            if isinstance(merged[key], list):
                merged[key] = list(set(merged[key]))
        
        return merged
    
    def _merge_value_propositions(self, values: List[Any]) -> List[str]:
        """Merge value propositions from multiple sources"""
        all_vps = []
        
        for value in values:
            if isinstance(value, list):
                all_vps.extend(value)
            elif isinstance(value, str):
                all_vps.append(value)
        
        # Remove duplicates and empty values
        unique_vps = list(set([vp for vp in all_vps if vp and vp.strip()]))
        
        return unique_vps
    
    def _apply_resolutions(self, field: str, field_values: List[Dict[str, Any]], 
                         resolutions: List[ConflictResolution]) -> Any:
        """Apply conflict resolutions to create final field value"""
        if not resolutions:
            return self._merge_field_values(field, field_values)
        
        # For now, use the first resolution
        # In a more sophisticated implementation, we could combine multiple resolutions
        return resolutions[0].resolution
    
    def _merge_field_values(self, field: str, field_values: List[Dict[str, Any]]) -> Any:
        """Merge field values when no conflicts exist"""
        if field == "company_info":
            return self._merge_company_info([fv["value"] for fv in field_values])
        elif field == "target_audience":
            return self._merge_target_audience([fv["value"] for fv in field_values])
        elif field == "value_propositions":
            return self._merge_value_propositions([fv["value"] for fv in field_values])
        elif field in ["products", "competitive_advantages", "key_messages"]:
            # Merge lists
            all_values = []
            for fv in field_values:
                value = fv["value"]
                if isinstance(value, list):
                    all_values.extend(value)
                elif value:
                    all_values.append(value)
            return list(set(all_values))  # Remove duplicates
        else:
            # Default: use highest confidence value
            best_fv = max(field_values, key=lambda x: x["confidence"])
            return best_fv["value"]
    
    def calculate_unified_confidence(self, sources: List[KnowledgeSource]) -> float:
        """Calculate unified confidence score for fused knowledge"""
        if not sources:
            return 0.0
        
        # Weighted average based on source priority and confidence
        total_weight = 0
        weighted_confidence = 0
        
        for source in sources:
            weight = self.fusion_strategies.get(source.source_type, {}).get("weight", 0.5)
            total_weight += weight
            weighted_confidence += weight * source.confidence
        
        return weighted_confidence / total_weight if total_weight > 0 else 0.0
    
    def create_unified_knowledge_base(self, fused_knowledge: Dict[str, Any]) -> Dict[str, Any]:
        """Create a final unified knowledge base with metadata"""
        unified = fused_knowledge.copy()
        
        # Add metadata
        unified["metadata"] = {
            "created_at": datetime.now().isoformat(),
            "version": "1.0",
            "fusion_service": "KnowledgeFusionService",
            "quality_score": self._calculate_quality_score(unified),
            "completeness_score": self._calculate_completeness_score(unified)
        }
        
        return unified
    
    def _calculate_quality_score(self, knowledge: Dict[str, Any]) -> float:
        """Calculate overall quality score for fused knowledge"""
        scores = []
        
        # Check each major section
        sections = ["company_info", "products", "value_propositions", "target_audience"]
        
        for section in sections:
            if section in knowledge and knowledge[section]:
                scores.append(0.8)  # Good if present
            else:
                scores.append(0.2)  # Poor if missing
        
        # Penalize conflicts
        conflict_penalty = len(knowledge.get("conflicts", [])) * 0.1
        base_score = sum(scores) / len(scores)
        
        return max(base_score - conflict_penalty, 0.0)
    
    def _calculate_completeness_score(self, knowledge: Dict[str, Any]) -> float:
        """Calculate completeness score for fused knowledge"""
        required_fields = [
            "company_info", "products", "value_propositions", 
            "target_audience", "sales_approach"
        ]
        
        present_fields = sum(1 for field in required_fields if field in knowledge and knowledge[field])
        
        return present_fields / len(required_fields)
    
    def _get_empty_knowledge_structure(self) -> Dict[str, Any]:
        """Get empty knowledge structure template"""
        return {
            "company_info": {},
            "products": [],
            "value_propositions": [],
            "target_audience": {
                "roles": [],
                "industries": [],
                "company_sizes": [],
                "pain_points": []
            },
            "sales_approach": "",
            "competitive_advantages": [],
            "key_messages": [],
            "conflicts": [],
            "fusion_metadata": {}
        }
    
    def get_fusion_statistics(self) -> Dict[str, Any]:
        """Get statistics about knowledge fusion operations"""
        return {
            "fusion_strategies": self.fusion_strategies,
            "conflict_resolution_strategies": list(self.conflict_resolution_strategies.keys()),
            "service_version": "1.0",
            "last_updated": datetime.now().isoformat()
        }
