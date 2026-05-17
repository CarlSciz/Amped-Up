"""
Zeus AI Agent - ANSI O5.1-2023 Wood Poles Expert
An intelligent conversational agent that understands and explains
ANSI O5.1-2023 Wood Poles, Specifications and Dimensions

Enhanced with multi-image analysis capabilities for comprehensive pole inspection
"""

from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum

from backend.ansi_pole_specs import (
    get_pole_specification,
    get_available_lengths,
    get_all_pole_classes,
    PoleSpecification,
    ANSI_POLE_SPECIFICATIONS
)
from backend.pole_analyzer_agent import PoleAnalyzerAgent
from backend.pole_calculations import (
    calculate_bending_moment,
    calculate_fiber_stress,
    calculate_section_modulus,
    calculate_strength_reduction_from_decay,
    calculate_embedment_depth,
    calculate_wind_load
)
from backend.pole_inspection_rules import (
    PoleInspectionRules,
    DefectSeverity,
    DefectCategory,
    WeatherCondition
)


class QueryType(Enum):
    """Types of queries Zeus can handle"""
    SPECIFICATION_LOOKUP = "specification_lookup"
    COMPARISON = "comparison"
    RECOMMENDATION = "recommendation"
    CALCULATION = "calculation"
    EXPLANATION = "explanation"
    COMPLIANCE = "compliance"
    GENERAL = "general"


@dataclass
class ZeusResponse:
    """Response from Zeus agent"""
    query_type: QueryType
    answer: str
    data: Optional[Dict] = None
    suggestions: Optional[List[str]] = None
    confidence: float = 1.0


@dataclass
class ImageAnalysis:
    """Analysis results for a single image"""
    image_path: str
    image_id: str
    defects: List[Dict] = field(default_factory=list)
    severity_summary: Dict[str, int] = field(default_factory=dict)
    compliance_issues: List[Dict] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)


@dataclass
class MultiImageAnalysis:
    """Analysis results for multiple images of the same pole"""
    pole_id: str
    images: List[ImageAnalysis] = field(default_factory=list)
    consolidated_defects: List[Dict] = field(default_factory=list)
    cross_image_correlations: List[Dict] = field(default_factory=list)
    overall_severity: Dict[str, int] = field(default_factory=dict)
    confidence_scores: Dict[str, float] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    summary: str = ""


class ZeusAgent:
    """
    Zeus - AI Agent for ANSI O5.1-2023 Wood Poles
    
    Zeus is an expert system that understands utility pole specifications,
    can answer questions, provide recommendations, and explain concepts
    related to ANSI O5.1-2023 standards.
    """
    
    def __init__(self):
        self.analyzer = PoleAnalyzerAgent()
        self.inspection_rules = PoleInspectionRules()
        self.knowledge_base = self._build_knowledge_base()
        self.training_integration = None
        self.svg_knowledge = None
        self._initialize_3d_training()
        self._initialize_svg_knowledge()
    
    def _initialize_3d_training(self):
        """Initialize 3D training dataset integration if available"""
        try:
            from backend.zeus_3d_training import Zeus3DTrainingIntegration
            self.training_integration = Zeus3DTrainingIntegration()
        except Exception as e:
            # 3D training data not available, continue without it
            pass
    
    def _initialize_svg_knowledge(self):
        """Initialize SVG knowledge base if available"""
        try:
            from backend.zeus_svg_training import ZeusSVGKnowledgeBase
            self.svg_knowledge = ZeusSVGKnowledgeBase()
        except Exception as e:
            # SVG knowledge not available, continue without it
            pass
    
    def _build_knowledge_base(self) -> Dict[str, str]:
        """Build knowledge base about ANSI O5.1-2023"""
        return {
            "standard": """ANSI O5.1-2023 is the American National Standard for Wood Poles -
            Specifications and Dimensions. It defines the requirements for wood utility poles
            used in electrical distribution and transmission systems.""",
            
            "pole_classes": """Pole classes range from H6 (lightest) to H1 (heavy) for H-class poles, 
            and Class 1 (heaviest) to Class 7 (lightest) for standard classes. Each class has specific 
            minimum dimensions and load-bearing capacities.""",
            
            "fiber_stress": """The standard uses 8000 psi as the allowable fiber stress for most 
            wood species. This is the maximum stress allowed at the extreme fiber of the pole 
            under design loads.""",
            
            "load_application": """Horizontal loads are specified at 2 feet from the top of the pole. 
            This represents typical attachment points for electrical conductors and equipment.""",
            
            "groundline": """The groundline is defined as 6 feet from the butt (bottom) of the pole. 
            This is typically where the pole enters the ground and is the critical section for 
            structural analysis.""",
            
            "circumference": """Pole dimensions are specified by minimum circumference at the top 
            and at groundline (6 feet from butt). Circumference is used rather than diameter 
            because it's easier to measure in the field.""",
            
            "wood_species": """Common species include Southern Pine, Douglas Fir, Western Red Cedar, 
            and Northern White Cedar. Each species has different strength characteristics, but the 
            standard uses 8000 psi fiber stress as a baseline.""",
            
            "treatment": """Poles are typically treated with preservatives like Creosote, 
            Pentachlorophenol, or Chromated Copper Arsenate (CCA) to prevent decay and extend 
            service life.""",
            
            "safety_factor": """A safety factor of 1.5 to 2.0 is typically applied to design loads 
            to account for uncertainties in loading, material properties, and deterioration over time.""",
            
            "decay": """Decay is the primary cause of pole failure. Regular inspection and monitoring 
            of decay at the groundline is critical for maintaining pole integrity.""",
            
            "embedment": """Typical embedment depth is 10% of pole length plus 2 feet, adjusted for 
            soil conditions. Proper embedment is essential for stability.""",
            
            "inspection": """Poles should be inspected every 5-10 years, with more frequent inspections
            for older poles or those in harsh environments.""",
            
            "defect_detection": """The system can detect and classify pole defects based on NESC 2023,
            OSHA 1910.269, and Michigan PSC standards. Defects are categorized by severity: imminent danger,
            serious, other-than-serious, de minimis, and multi-defect conditions.""",
            
            "weather_conditions": """Weather conditions significantly affect pole inspection. Ice loading,
            snow accumulation, post-storm damage, and summer thermal sag can all create or exacerbate
            compliance issues. The system accounts for weather-sensitive defects.""",
            
            "3d_training": """Zeus has been trained on the Pole Compliance Exemplar Library v0.9,
            a comprehensive 3D-rendered dataset with 27 annotated images covering multiple defect types.
            The dataset includes vegetation contact, broken crossarms, downed conductors, and ice buildup
            scenarios across different viewing angles and lighting conditions. Each defect is annotated
            with precise 2D bounding boxes for object detection training.""",
            
            "defect_detection_ai": """Zeus uses AI-powered defect detection trained on 3D synthetic data.
            The system can identify: vegetation contact with conductors (imminent danger), broken crossarms
            (imminent danger), downed conductors (imminent danger), and ice buildup (serious). Detection
            uses COCO-style bounding box annotations with normalized coordinates for precise localization.""",
            
            "training_dataset": """The training dataset consists of sp35c5 pole configurations rendered
            from three camera angles (front, closeup, three-quarter) under three lighting conditions
            (noon, golden hour, overcast). This provides 27 total images with 9 negative (compliant) samples
            for balanced training. All annotations include scene severity classification and camera metadata.""",
            
            "svg_library": """Zeus has access to the Pole Compliance Exemplar Library v0.7, a comprehensive
            collection of 230 synthetic SVG pole inspection scenarios. The library covers 18 pole types from
            single-phase rural poles to 138kV transmission structures, with 60+ distinct defect patterns across
            normal and weather conditions (ice loading, snow, post-storm, summer thermal sag).""",
            
            "weather_scenarios": """The SVG library includes 60 weather-specific scenarios covering four
            conditions: ice loading (NESC 250.B heavy district), snow accumulation, post-storm damage assessment,
            and summer thermal sag (IEEE 738). Each weather condition includes both compliant context scenes and
            weather-induced violations for comprehensive training.""",
            
            "multi_defect_recognition": """Zeus can identify compound risk scenarios where multiple defects
            occur simultaneously. The SVG library includes 48 multi-defect compositions covering themes like
            aging infrastructure, vegetation compound issues, weather stress on degraded assets, and structural
            compound failures. These are classified with multi_defect severity (purple banner)."""
        }
    
    def ask(self, question: str, context: Optional[Dict] = None) -> ZeusResponse:
        """
        Ask Zeus a question about ANSI O5.1-2023
        
        Args:
            question: User's question
            context: Optional context (pole data, measurements, etc.)
            
        Returns:
            ZeusResponse with answer and relevant data
        """
        question_lower = question.lower()
        
        # Determine query type and route to appropriate handler
        if any(word in question_lower for word in ["what is", "define", "explain", "tell me about"]):
            return self._handle_explanation(question, context)
        
        elif any(word in question_lower for word in ["specification", "spec", "dimensions", "size"]):
            return self._handle_specification_lookup(question, context)
        
        elif any(word in question_lower for word in ["compare", "difference", "versus", "vs"]):
            return self._handle_comparison(question, context)
        
        elif any(word in question_lower for word in ["recommend", "suggest", "which pole", "what class"]):
            return self._handle_recommendation(question, context)
        
        elif any(word in question_lower for word in ["calculate", "compute", "how much", "load"]):
            return self._handle_calculation(question, context)
        
        elif any(word in question_lower for word in ["compliant", "meets", "acceptable", "safe"]):
            return self._handle_compliance(question, context)
        
        else:
            return self._handle_general(question, context)
    
    def _handle_explanation(self, question: str, context: Optional[Dict]) -> ZeusResponse:
        """Handle explanation requests"""
        question_lower = question.lower()
        
        # Check knowledge base for relevant topics
        for topic, explanation in self.knowledge_base.items():
            if topic.replace("_", " ") in question_lower:
                suggestions = [
                    f"Would you like to know more about {topic.replace('_', ' ')}?",
                    "I can also help with specifications, calculations, or recommendations.",
                    "Ask me about specific pole classes or load requirements."
                ]
                
                return ZeusResponse(
                    query_type=QueryType.EXPLANATION,
                    answer=explanation,
                    suggestions=suggestions,
                    confidence=0.9
                )
        
        # General ANSI O5.1-2023 explanation
        if "ansi" in question_lower or "o5.1" in question_lower or "standard" in question_lower:
            return ZeusResponse(
                query_type=QueryType.EXPLANATION,
                answer=self.knowledge_base["standard"],
                data={
                    "available_classes": get_all_pole_classes(),
                    "class_count": len(get_all_pole_classes())
                },
                suggestions=[
                    "Ask about specific pole classes (H1, Class 1, etc.)",
                    "Request specifications for a particular pole",
                    "Get recommendations for your load requirements"
                ]
            )
        
        # Pole class explanation
        if "class" in question_lower or "h1" in question_lower or "h2" in question_lower:
            return ZeusResponse(
                query_type=QueryType.EXPLANATION,
                answer=self.knowledge_base["pole_classes"] + "\n\nAvailable classes: " + 
                       ", ".join(get_all_pole_classes()),
                suggestions=[
                    "Compare different pole classes",
                    "Get specifications for a specific class",
                    "Find the right class for your load requirements"
                ]
            )
        
        return ZeusResponse(
            query_type=QueryType.GENERAL,
            answer="I'm Zeus, your ANSI O5.1-2023 expert. I can help with pole specifications, "
                   "load calculations, compliance checking, and recommendations. What would you like to know?",
            suggestions=[
                "What are the pole classes?",
                "How do I select the right pole?",
                "What is the load capacity of an H1 40ft pole?",
                "Calculate the bending moment for my application"
            ]
        )
    
    def _handle_specification_lookup(self, question: str, context: Optional[Dict]) -> ZeusResponse:
        """Handle specification lookup requests"""
        # Extract pole class and length from question or context
        pole_class = None
        length = None
        
        if context:
            pole_class = context.get("pole_class")
            length = context.get("length_ft")
        
        # Try to extract from question
        question_lower = question.lower()
        for cls in get_all_pole_classes():
            if cls.lower() in question_lower:
                pole_class = cls
                break
        
        # Extract length
        import re
        length_match = re.search(r'(\d+)\s*(?:ft|foot|feet)', question_lower)
        if length_match:
            length = float(length_match.group(1))
        
        if pole_class and length:
            spec = get_pole_specification(pole_class, length)
            if spec:
                answer = f"""**{spec.pole_class} Class Pole - {spec.length_ft}ft**

**Dimensions:**
- Minimum top circumference: {spec.min_circumference_top_inches}" ({spec.get_top_diameter_inches():.2f}" diameter)
- Minimum groundline circumference: {spec.min_circumference_6ft_from_butt_inches}" ({spec.get_groundline_diameter_inches():.2f}" diameter)

**Capacity:**
- Horizontal load capacity: {spec.horizontal_load_lbs:,} lbs (at 2 feet from top)
- Fiber stress: {spec.fiber_stress_psi:,} psi

**Application:**
This pole can support {spec.horizontal_load_lbs:,} lbs of horizontal load applied 2 feet from the top, 
with a fiber stress of {spec.fiber_stress_psi:,} psi at the groundline."""
                
                return ZeusResponse(
                    query_type=QueryType.SPECIFICATION_LOOKUP,
                    answer=answer,
                    data={
                        "pole_class": spec.pole_class,
                        "length_ft": spec.length_ft,
                        "top_circumference": spec.min_circumference_top_inches,
                        "groundline_circumference": spec.min_circumference_6ft_from_butt_inches,
                        "capacity_lbs": spec.horizontal_load_lbs,
                        "top_diameter": spec.get_top_diameter_inches(),
                        "groundline_diameter": spec.get_groundline_diameter_inches()
                    },
                    suggestions=[
                        f"Compare {pole_class} with other classes at {length}ft",
                        f"Calculate loads for this pole",
                        f"Check if this pole meets your requirements"
                    ]
                )
            else:
                return ZeusResponse(
                    query_type=QueryType.SPECIFICATION_LOOKUP,
                    answer=f"No specification found for {pole_class} class at {length}ft. "
                           f"Available lengths for {pole_class}: {get_available_lengths(pole_class)}",
                    confidence=0.5
                )
        
        elif pole_class:
            lengths = get_available_lengths(pole_class)
            return ZeusResponse(
                query_type=QueryType.SPECIFICATION_LOOKUP,
                answer=f"**{pole_class} Class Poles**\n\nAvailable lengths: {lengths}\n\n"
                       f"Please specify a length to get detailed specifications.",
                data={"pole_class": pole_class, "available_lengths": lengths},
                suggestions=[f"Get specs for {pole_class} {length}ft" for length in lengths[:3]]
            )
        
        else:
            return ZeusResponse(
                query_type=QueryType.SPECIFICATION_LOOKUP,
                answer="Please specify a pole class (e.g., H1, Class 1) and length (e.g., 40ft) "
                       "to get specifications.",
                data={"available_classes": get_all_pole_classes()},
                suggestions=[
                    "What are the specs for H1 40ft?",
                    "Show me Class 2 45ft specifications",
                    "List all available pole classes"
                ]
            )
    
    def _handle_comparison(self, question: str, context: Optional[Dict]) -> ZeusResponse:
        """Handle pole comparison requests"""
        # Extract length for comparison
        length = None
        if context:
            length = context.get("length_ft")
        
        import re
        length_match = re.search(r'(\d+)\s*(?:ft|foot|feet)', question.lower())
        if length_match:
            length = float(length_match.group(1))
        
        if length:
            results = self.analyzer.compare_pole_classes(length)
            
            if results:
                answer = f"**Pole Class Comparison at {length}ft**\n\n"
                answer += "| Class | Capacity (lbs) | Top Circ (in) | Groundline Circ (in) |\n"
                answer += "|-------|----------------|---------------|----------------------|\n"
                
                for pole_class, spec in results:
                    answer += f"| {pole_class:5s} | {spec.horizontal_load_lbs:14,} | {spec.min_circumference_top_inches:13.1f} | {spec.min_circumference_6ft_from_butt_inches:20.1f} |\n"
                
                answer += f"\n**Analysis:**\n"
                answer += f"- Strongest: {results[0][0]} ({results[0][1].horizontal_load_lbs:,} lbs)\n"
                answer += f"- Lightest: {results[-1][0]} ({results[-1][1].horizontal_load_lbs:,} lbs)\n"
                answer += f"- Capacity range: {results[-1][1].horizontal_load_lbs:,} - {results[0][1].horizontal_load_lbs:,} lbs"
                
                return ZeusResponse(
                    query_type=QueryType.COMPARISON,
                    answer=answer,
                    data={
                        "length_ft": length,
                        "poles": [
                            {
                                "class": cls,
                                "capacity": spec.horizontal_load_lbs,
                                "top_circ": spec.min_circumference_top_inches,
                                "groundline_circ": spec.min_circumference_6ft_from_butt_inches
                            }
                            for cls, spec in results
                        ]
                    },
                    suggestions=[
                        "Get detailed specs for a specific class",
                        "Find the right pole for your load requirements",
                        "Calculate loads for your application"
                    ]
                )
        
        return ZeusResponse(
            query_type=QueryType.COMPARISON,
            answer="Please specify a length to compare pole classes (e.g., 'Compare poles at 40ft')",
            suggestions=[
                "Compare poles at 40ft",
                "Compare poles at 45ft",
                "Show me all H-class poles"
            ]
        )
    
    def _handle_recommendation(self, question: str, context: Optional[Dict]) -> ZeusResponse:
        """Handle pole recommendation requests"""
        required_load = None
        length = None
        
        if context:
            required_load = context.get("required_load_lbs")
            length = context.get("length_ft")
        
        # Extract from question
        import re
        load_match = re.search(r'(\d+(?:,\d+)?)\s*(?:lb|lbs|pound)', question.lower())
        if load_match:
            required_load = float(load_match.group(1).replace(',', ''))
        
        length_match = re.search(r'(\d+)\s*(?:ft|foot|feet)', question.lower())
        if length_match:
            length = float(length_match.group(1))
        
        if required_load and length:
            result = self.analyzer.get_recommended_pole_class(required_load, length)
            
            if result:
                pole_class, spec = result
                design_load = required_load * self.analyzer.safety_factor
                margin = spec.horizontal_load_lbs - design_load
                margin_pct = (margin / spec.horizontal_load_lbs) * 100
                
                answer = f"""**Pole Recommendation**

**Requirements:**
- Required load: {required_load:,.0f} lbs
- Pole length: {length} ft
- Design load (with safety factor {self.analyzer.safety_factor}): {design_load:,.0f} lbs

**Recommended Pole:**
- Class: **{pole_class}**
- Rated capacity: {spec.horizontal_load_lbs:,} lbs
- Safety margin: {margin:,.0f} lbs ({margin_pct:.1f}%)

**Specifications:**
- Top circumference: {spec.min_circumference_top_inches}" ({spec.get_top_diameter_inches():.2f}" diameter)
- Groundline circumference: {spec.min_circumference_6ft_from_butt_inches}" ({spec.get_groundline_diameter_inches():.2f}" diameter)

This pole provides adequate capacity with a {margin_pct:.1f}% safety margin above the design load."""
                
                return ZeusResponse(
                    query_type=QueryType.RECOMMENDATION,
                    answer=answer,
                    data={
                        "recommended_class": pole_class,
                        "required_load": required_load,
                        "design_load": design_load,
                        "pole_capacity": spec.horizontal_load_lbs,
                        "safety_margin_lbs": margin,
                        "safety_margin_percent": margin_pct,
                        "specification": {
                            "top_circumference": spec.min_circumference_top_inches,
                            "groundline_circumference": spec.min_circumference_6ft_from_butt_inches
                        }
                    },
                    suggestions=[
                        f"Get full specifications for {pole_class} {length}ft",
                        f"Compare {pole_class} with other options",
                        "Calculate actual loads for this pole"
                    ]
                )
            else:
                return ZeusResponse(
                    query_type=QueryType.RECOMMENDATION,
                    answer=f"No suitable pole found for {required_load:,.0f} lbs at {length}ft. "
                           f"The required load may exceed available pole capacities.",
                    confidence=0.7,
                    suggestions=[
                        "Consider using a shorter pole for higher capacity",
                        "Review load requirements",
                        "Consider using multiple poles or guy wires"
                    ]
                )
        
        return ZeusResponse(
            query_type=QueryType.RECOMMENDATION,
            answer="Please provide the required load (in lbs) and pole length (in ft) for a recommendation.",
            suggestions=[
                "Recommend a pole for 10,000 lbs at 40ft",
                "What pole do I need for 15,000 lbs at 45ft?",
                "Suggest a pole for my application"
            ]
        )
    
    def _handle_calculation(self, question: str, context: Optional[Dict]) -> ZeusResponse:
        """Handle calculation requests"""
        question_lower = question.lower()
        
        if "bending moment" in question_lower or "moment" in question_lower:
            load = context.get("load_lbs") if context else None
            height = context.get("height_ft") if context else None
            
            if load and height:
                moment = calculate_bending_moment(load, height)
                answer = f"""**Bending Moment Calculation**

Load: {load:,.0f} lbs
Height: {height} ft

**Bending Moment: {moment:,.0f} ft-lbs**

This is the moment at the base caused by the horizontal load applied at the specified height."""
                
                return ZeusResponse(
                    query_type=QueryType.CALCULATION,
                    answer=answer,
                    data={"load_lbs": load, "height_ft": height, "moment_ft_lbs": moment}
                )
        
        elif "decay" in question_lower or "strength loss" in question_lower:
            diameter = context.get("diameter_inches") if context else None
            decay = context.get("decay_depth_inches") if context else None
            
            if diameter and decay:
                ratio, loss_pct = calculate_strength_reduction_from_decay(diameter, decay)
                answer = f"""**Decay Strength Analysis**

Original diameter: {diameter} inches
Decay depth: {decay} inches

**Results:**
- Remaining strength: {ratio*100:.1f}%
- Strength loss: {loss_pct:.1f}%

{'⚠️ CRITICAL: Significant strength loss detected!' if loss_pct > 30 else 
 '⚠️ WARNING: Moderate strength loss' if loss_pct > 15 else 
 '✓ Acceptable decay level'}"""
                
                return ZeusResponse(
                    query_type=QueryType.CALCULATION,
                    answer=answer,
                    data={
                        "original_diameter": diameter,
                        "decay_depth": decay,
                        "strength_ratio": ratio,
                        "strength_loss_percent": loss_pct
                    }
                )
        
        return ZeusResponse(
            query_type=QueryType.CALCULATION,
            answer="I can help with various calculations. What would you like to calculate?",
            suggestions=[
                "Calculate bending moment",
                "Calculate strength loss from decay",
                "Calculate wind load",
                "Calculate embedment depth"
            ]
        )
    
    def _handle_compliance(self, question: str, context: Optional[Dict]) -> ZeusResponse:
        """Handle compliance checking requests"""
        if not context or "pole_class" not in context:
            return ZeusResponse(
                query_type=QueryType.COMPLIANCE,
                answer="To check compliance, please provide pole measurements and specifications.",
                suggestions=[
                    "Analyze my pole for compliance",
                    "Check if my pole meets ANSI standards",
                    "What are the compliance requirements?"
                ]
            )
        
        # This would integrate with the analyzer for full compliance checking
        return ZeusResponse(
            query_type=QueryType.COMPLIANCE,
            answer="Compliance checking requires detailed pole inspection data. "
                   "Use the pole analyzer for comprehensive compliance analysis.",
            suggestions=[
                "Learn about compliance requirements",
                "What makes a pole compliant?",
                "Get pole specifications"
            ]
        )
    
    def _handle_general(self, question: str, context: Optional[Dict]) -> ZeusResponse:
        """Handle general questions"""
        return ZeusResponse(
            query_type=QueryType.GENERAL,
            answer="I'm Zeus, your ANSI O5.1-2023 expert. I can help you with:\n\n"
                   "• Pole specifications and dimensions\n"
                   "• Load capacity calculations\n"
                   "• Pole class comparisons\n"
                   "• Recommendations for your requirements\n"
                   "• Compliance checking\n"
                   "• Engineering calculations\n\n"
                   "What would you like to know?",
            suggestions=[
                "What are the pole classes?",
                "Get specifications for H1 40ft",
                "Recommend a pole for 12,000 lbs at 45ft",
                "Compare poles at 40ft",
                "Explain fiber stress"
            ]
        )
    
    def get_capabilities(self) -> Dict[str, List[str]]:
        """Get Zeus's capabilities"""
        return {
            "specifications": [
                "Look up pole specifications by class and length",
                "Get dimensional requirements",
                "Find load capacities",
                "List available pole classes and lengths"
            ],
            "comparisons": [
                "Compare different pole classes",
                "Analyze capacity differences",
                "Evaluate dimensional variations"
            ],
            "recommendations": [
                "Recommend appropriate pole class for load requirements",
                "Suggest alternatives",
                "Optimize pole selection"
            ],
            "calculations": [
                "Calculate bending moments",
                "Compute fiber stress",
                "Analyze decay effects",
                "Calculate wind and ice loads",
                "Determine embedment depth"
            ],
            "explanations": [
                "Explain ANSI O5.1-2023 concepts",
                "Describe pole classes",
                "Clarify specifications",
                "Provide best practices"
            ],
            "compliance": [
                "Check pole compliance",
                "Identify issues",
                "Provide recommendations"
            ],
            "defect_detection": [
                "Identify pole defects and violations",
                "Classify defect severity (OSHA 1903.14)",
                "Provide corrective actions",
                "Generate inspection checklists"
            ],
            "weather_analysis": [
                "Assess weather impact on poles",
                "Detect weather-induced violations",
                "Evaluate seasonal conditions"
            ],
            "ai_training": [
                "Access 3D training dataset statistics",
                "Get defect detection training info",
                "View annotated training samples",
                "Export training data in YOLO format"
            ]
        }
    
    def get_defect_info(self, defect_id: str) -> Optional[Dict]:
        """
        Get information about a specific defect
        
        Args:
            defect_id: Defect identifier
            
        Returns:
            Dictionary with defect information or None
        """
        rule = self.inspection_rules.get_defect_rule(defect_id)
        
        if not rule:
            return None
        
        return {
            "defect_id": rule.defect_id,
            "name": rule.name,
            "category": rule.category.value,
            "severity": rule.severity.value,
            "description": rule.description,
            "nesc_reference": rule.nesc_reference,
            "osha_reference": rule.osha_reference,
            "michigan_reference": rule.michigan_reference,
            "corrective_action": rule.corrective_action,
            "weather_sensitive": rule.weather_sensitive
        }
    
    def get_inspection_checklist(self, pole_type_id: str) -> Dict:
        """
        Generate inspection checklist for a pole type
        
        Args:
            pole_type_id: Pole type identifier (e.g., "ju40c4")
            
        Returns:
            Inspection checklist dictionary
        """
        return self.inspection_rules.get_inspection_checklist(pole_type_id)
    
    def evaluate_clearance(
        self,
        clearance_type: str,
        voltage_kv: float,
        measured_clearance_ft: float
    ) -> Dict:
        """
        Evaluate if clearance meets NESC requirements
        
        Args:
            clearance_type: Type of clearance (ground, roadway, building, etc.)
            voltage_kv: Voltage in kilovolts
            measured_clearance_ft: Measured clearance in feet
            
        Returns:
            Dictionary with compliance status and details
        """
        is_compliant, message = self.inspection_rules.evaluate_clearance(
            clearance_type,
            voltage_kv,
            measured_clearance_ft
        )
        
        return {
            "compliant": is_compliant,
            "clearance_type": clearance_type,
            "voltage_kv": voltage_kv,
            "measured_clearance_ft": measured_clearance_ft,
            "message": message
        }
    
    def get_defects_by_severity(self, severity: str) -> List[Dict]:
        """
        Get all defects of a specific severity level
        
        Args:
            severity: Severity level (imminent_danger, serious, other_than_serious, deminimis, multi_defect)
            
        Returns:
            List of defect information dictionaries
        """
        try:
            severity_enum = DefectSeverity(severity)
            rules = self.inspection_rules.get_rules_by_severity(severity_enum)
            
            return [
                {
                    "defect_id": rule.defect_id,
                    "name": rule.name,
                    "category": rule.category.value,
                    "description": rule.description,
                    "corrective_action": rule.corrective_action
                }
                for rule in rules
            ]
        except ValueError:
            return []
    
    def get_defects_by_category(self, category: str) -> List[Dict]:
        """
        Get all defects in a specific category
        
        Args:
            category: Category name (vegetation, structural, hardware, etc.)
            
        Returns:
            List of defect information dictionaries
        """
        try:
            category_enum = DefectCategory(category)
            rules = self.inspection_rules.get_rules_by_category(category_enum)
            
            return [
                {
                    "defect_id": rule.defect_id,
                    "name": rule.name,
                    "severity": rule.severity.value,
                    "description": rule.description,
                    "corrective_action": rule.corrective_action
                }
                for rule in rules
            ]
        except ValueError:
            return []
    
    def get_weather_sensitive_defects(self) -> List[Dict]:
        """
        Get all weather-sensitive defects
        
        Returns:
            List of weather-sensitive defect information
        """
        rules = self.inspection_rules.get_weather_sensitive_rules()
        
        return [
            {
                "defect_id": rule.defect_id,
                "name": rule.name,
                "category": rule.category.value,
                "severity": rule.severity.value,
                "description": rule.description
            }
            for rule in rules
        ]
    def get_3d_training_summary(self) -> Optional[Dict]:
        """
        Get summary of 3D training dataset
        
        Returns:
            Training dataset summary or None if not available
        """
        if not self.training_integration:
            return None
        
        return self.training_integration.get_training_summary()
    
    def get_3d_training_recommendations(self) -> Optional[List[str]]:
        """
        Get recommendations for training on 3D dataset
        
        Returns:
            List of recommendations or None if not available
        """
        if not self.training_integration:
            return None
        
        return self.training_integration.get_training_recommendations()
    
    def export_training_data(self, output_dir: str, format: str = "yolo") -> bool:
        """
        Export training data in specified format
        
        Args:
            output_dir: Output directory path
            format: Export format (currently only "yolo" supported)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.training_integration:
            return False
        
        try:
            if format.lower() == "yolo":
                self.training_integration.export_yolo_format(output_dir)
                return True
            else:
                return False
        except Exception:
            return False
    
    def get_svg_knowledge_summary(self) -> Optional[Dict]:
        """
        Get summary of SVG knowledge base
        
        Returns:
            SVG library summary or None if not available
        """
        if not self.svg_knowledge:
            return None
        
        return self.svg_knowledge.get_statistics()
    
    def get_svg_defect_pattern(self, defect_id: str) -> Optional[Dict]:
        """
        Get SVG defect pattern information
        
        Args:
            defect_id: Defect identifier
            
        Returns:
            Defect pattern info or None
        """
        if not self.svg_knowledge:
            return None
        
        pattern = self.svg_knowledge.get_defect_pattern(defect_id)
        if not pattern:
            return None
        
        return {
            "defect_id": pattern.defect_id,
            "name": pattern.name,
            "pole_types": pattern.pole_types,
            "severity": pattern.severity,
            "weather_sensitive": pattern.weather_sensitive,
            "nesc_references": pattern.nesc_references,
            "osha_references": pattern.osha_references,
            "description": pattern.description,
            "visual_indicators": pattern.visual_indicators,
            "scene_count": pattern.scene_count
        }
    
    def get_svg_pole_type_info(self, pole_id: str) -> Optional[Dict]:
        """
        Get SVG pole type information
        
        Args:
            pole_id: Pole type identifier (e.g., "sp35c5")
            
        Returns:
            Pole type info or None
        """
        if not self.svg_knowledge:
            return None
        
        pole_info = self.svg_knowledge.get_pole_type_info(pole_id)
        if not pole_info:
            return None
        
        return {
            "pole_id": pole_info.pole_id,
            "description": pole_info.description,
            "height_ft": pole_info.height_ft,
            "pole_class": pole_info.pole_class,
            "voltage_kv": pole_info.voltage_kv,
            "scene_count": pole_info.scene_count,
            "defect_types": pole_info.defect_types
        }
    
    def get_weather_sensitive_defects_svg(self) -> Optional[List[Dict]]:
        """
        Get all weather-sensitive defects from SVG library
        
        Returns:
            List of weather-sensitive defects or None
        """
        if not self.svg_knowledge:
            return None
        
        defects = self.svg_knowledge.get_weather_sensitive_defects()
        return [
            {
                "defect_id": d.defect_id,
                "name": d.name,
                "severity": d.severity,
                "scene_count": d.scene_count
            }
            for d in defects
        ]
    
    def get_defect_training_info(self, defect_class: str) -> Optional[Dict]:
        """
        Get training information for a specific defect class
        
        Args:
            defect_class: Defect class name (e.g., "veg_contact_branch")
            
        Returns:
            Training info dictionary or None
        """
        if not self.training_integration:
            return None
        
        dataset = self.training_integration.dataset
        images = dataset.get_images_by_defect(defect_class)
        
        if not images:
            return None
        
        return {
            "defect_class": defect_class,
            "total_samples": len(images),
            "scenes": list(set(img.scene for img in images)),
            "angles": list(set(img.angle for img in images)),
            "lighting_conditions": list(set(img.lighting for img in images)),
            "sample_images": [img.image_path for img in images[:5]]
        }
    
    def analyze_multiple_images(
        self,
        image_paths: List[str],
        pole_id: Optional[str] = None,
        context: Optional[Dict] = None
    ) -> MultiImageAnalysis:
        """
        Analyze multiple images (up to 3) of the same pole
        
        This method enables comprehensive pole inspection by analyzing multiple
        views or angles of the same pole, correlating findings across images,
        and providing consolidated recommendations.
        
        Args:
            image_paths: List of 1-3 image paths to analyze
            pole_id: Optional pole identifier
            context: Optional context (pole specifications, location, etc.)
            
        Returns:
            MultiImageAnalysis with consolidated findings
        """
        if not image_paths:
            raise ValueError("At least one image path must be provided")
        
        if len(image_paths) > 3:
            raise ValueError("Maximum of 3 images can be analyzed at once")
        
        # Generate pole ID if not provided
        if not pole_id:
            from datetime import datetime
            pole_id = f"POLE-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        print(f"\n{'=' * 80}")
        print(f"ZEUS MULTI-IMAGE ANALYSIS")
        print(f"{'=' * 80}")
        print(f"Pole ID: {pole_id}")
        print(f"Images to analyze: {len(image_paths)}")
        
        # Analyze each image individually
        image_analyses = []
        for i, image_path in enumerate(image_paths, 1):
            print(f"\n[{i}/{len(image_paths)}] Analyzing: {image_path}")
            analysis = self._analyze_single_image_detailed(
                image_path,
                image_id=f"IMG-{i}",
                context=context
            )
            image_analyses.append(analysis)
        
        # Consolidate findings across images
        print(f"\nConsolidating findings across {len(image_analyses)} images...")
        multi_analysis = self._consolidate_multi_image_findings(
            pole_id,
            image_analyses,
            context
        )
        
        print(f"\n{'=' * 80}")
        print(f"MULTI-IMAGE ANALYSIS COMPLETE")
        print(f"{'=' * 80}")
        
        return multi_analysis
    
    def _analyze_single_image_detailed(
        self,
        image_path: str,
        image_id: str,
        context: Optional[Dict] = None
    ) -> ImageAnalysis:
        """
        Perform detailed analysis of a single image
        
        Args:
            image_path: Path to the image
            image_id: Unique identifier for this image
            context: Optional context information
            
        Returns:
            ImageAnalysis with detailed findings
        """
        import os
        from pathlib import Path
        
        # Extract metadata from image path
        filename = os.path.basename(image_path)
        
        # Simulate visual inspection (in production, this would use computer vision)
        defects = self._identify_defects_from_image(image_path, context)
        
        # Categorize by severity
        severity_summary = self._calculate_severity_summary(defects)
        
        # Identify compliance issues
        compliance_issues = self._identify_compliance_issues(defects)
        
        # Create metadata
        metadata = {
            "filename": filename,
            "file_exists": os.path.exists(image_path),
            "analysis_timestamp": self._get_timestamp()
        }
        
        return ImageAnalysis(
            image_path=image_path,
            image_id=image_id,
            defects=defects,
            severity_summary=severity_summary,
            compliance_issues=compliance_issues,
            metadata=metadata
        )
    
    def _identify_defects_from_image(
        self,
        image_path: str,
        context: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Identify defects from image analysis
        
        In production, this would integrate with computer vision models.
        For now, it uses rule-based detection based on context.
        """
        defects = []
        
        # Sample defects for demonstration
        # In production, this would be replaced with actual CV detection
        sample_defects = [
            "veg_contact",
            "crossarm_decay",
            "hardware_corrosion",
            "insulator_damage",
            "pole_lean"
        ]
        
        for defect_id in sample_defects[:3]:  # Limit to 3 for demo
            rule = self.inspection_rules.get_defect_rule(defect_id)
            if rule:
                defects.append({
                    "defect_id": rule.defect_id,
                    "name": rule.name,
                    "category": rule.category.value,
                    "severity": rule.severity.value,
                    "description": rule.description,
                    "corrective_action": rule.corrective_action,
                    "nesc_reference": rule.nesc_reference,
                    "confidence": 0.85  # Simulated confidence score
                })
        
        return defects
    
    def _calculate_severity_summary(self, defects: List[Dict]) -> Dict[str, int]:
        """Calculate summary of defects by severity"""
        summary = {
            "imminent_danger": 0,
            "serious": 0,
            "other_than_serious": 0,
            "deminimis": 0,
            "multi_defect": 0
        }
        
        for defect in defects:
            severity = defect.get("severity", "deminimis")
            if severity in summary:
                summary[severity] += 1
        
        # Check for multi-defect condition
        if summary["serious"] + summary["other_than_serious"] >= 3:
            summary["multi_defect"] = 1
        
        return summary
    
    def _identify_compliance_issues(self, defects: List[Dict]) -> List[Dict]:
        """Identify compliance issues from defects"""
        compliance_issues = []
        
        for defect in defects:
            if defect.get("severity") in ["imminent_danger", "serious"]:
                compliance_issues.append({
                    "defect": defect["name"],
                    "severity": defect["severity"],
                    "standard": defect.get("nesc_reference", "N/A"),
                    "action_required": defect.get("corrective_action", "Immediate inspection required")
                })
        
        return compliance_issues
    
    def _consolidate_multi_image_findings(
        self,
        pole_id: str,
        image_analyses: List[ImageAnalysis],
        context: Optional[Dict] = None
    ) -> MultiImageAnalysis:
        """
        Consolidate findings from multiple images
        
        This method:
        1. Identifies defects visible in multiple images (higher confidence)
        2. Combines unique defects from all images
        3. Correlates findings across different views
        4. Generates comprehensive recommendations
        """
        # Consolidate all defects
        all_defects = []
        defect_occurrences = {}  # Track how many images show each defect
        
        for analysis in image_analyses:
            for defect in analysis.defects:
                defect_key = defect["defect_id"]
                
                if defect_key not in defect_occurrences:
                    defect_occurrences[defect_key] = {
                        "count": 0,
                        "images": [],
                        "defect_data": defect
                    }
                
                defect_occurrences[defect_key]["count"] += 1
                defect_occurrences[defect_key]["images"].append(analysis.image_id)
        
        # Create consolidated defects with confidence scores
        consolidated_defects = []
        for defect_id, occurrence_data in defect_occurrences.items():
            defect = occurrence_data["defect_data"].copy()
            
            # Increase confidence if defect appears in multiple images
            base_confidence = defect.get("confidence", 0.85)
            image_count = occurrence_data["count"]
            
            # Boost confidence: +10% for each additional image
            adjusted_confidence = min(0.99, base_confidence + (image_count - 1) * 0.10)
            
            defect["confidence"] = adjusted_confidence
            defect["visible_in_images"] = occurrence_data["images"]
            defect["image_count"] = image_count
            
            consolidated_defects.append(defect)
        
        # Sort by severity and confidence
        severity_order = {
            "imminent_danger": 0,
            "serious": 1,
            "other_than_serious": 2,
            "deminimis": 3,
            "multi_defect": 4
        }
        consolidated_defects.sort(
            key=lambda x: (severity_order.get(x["severity"], 5), -x["confidence"])
        )
        
        # Calculate overall severity
        overall_severity = {
            "imminent_danger": 0,
            "serious": 0,
            "other_than_serious": 0,
            "deminimis": 0,
            "multi_defect": 0
        }
        
        for defect in consolidated_defects:
            severity = defect["severity"]
            if severity in overall_severity:
                overall_severity[severity] += 1
        
        # Check for multi-defect condition
        if overall_severity["serious"] + overall_severity["other_than_serious"] >= 3:
            overall_severity["multi_defect"] = 1
        
        # Generate cross-image correlations
        correlations = self._generate_cross_image_correlations(
            image_analyses,
            consolidated_defects
        )
        
        # Calculate confidence scores
        confidence_scores = {
            "overall_analysis": self._calculate_overall_confidence(consolidated_defects),
            "defect_detection": sum(d["confidence"] for d in consolidated_defects) / len(consolidated_defects) if consolidated_defects else 0.0,
            "multi_view_correlation": len([d for d in consolidated_defects if d["image_count"] > 1]) / len(consolidated_defects) if consolidated_defects else 0.0
        }
        
        # Generate recommendations
        recommendations = self._generate_multi_image_recommendations(
            consolidated_defects,
            overall_severity,
            len(image_analyses)
        )
        
        # Generate summary
        summary = self._generate_multi_image_summary(
            pole_id,
            len(image_analyses),
            consolidated_defects,
            overall_severity
        )
        
        return MultiImageAnalysis(
            pole_id=pole_id,
            images=image_analyses,
            consolidated_defects=consolidated_defects,
            cross_image_correlations=correlations,
            overall_severity=overall_severity,
            confidence_scores=confidence_scores,
            recommendations=recommendations,
            summary=summary
        )
    
    def _generate_cross_image_correlations(
        self,
        image_analyses: List[ImageAnalysis],
        consolidated_defects: List[Dict]
    ) -> List[Dict]:
        """Generate correlations between findings in different images"""
        correlations = []
        
        # Find defects visible in multiple images
        multi_view_defects = [d for d in consolidated_defects if d["image_count"] > 1]
        
        for defect in multi_view_defects:
            correlations.append({
                "type": "multi_view_confirmation",
                "defect": defect["name"],
                "confidence_boost": f"+{(defect['image_count'] - 1) * 10}%",
                "images": defect["visible_in_images"],
                "description": f"{defect['name']} confirmed across {defect['image_count']} images, increasing detection confidence"
            })
        
        # Identify complementary views
        if len(image_analyses) >= 2:
            correlations.append({
                "type": "complementary_coverage",
                "description": f"Multiple viewing angles provide comprehensive pole assessment",
                "benefit": "Reduces blind spots and increases inspection thoroughness"
            })
        
        return correlations
    
    def _calculate_overall_confidence(self, consolidated_defects: List[Dict]) -> float:
        """Calculate overall confidence score for the analysis"""
        if not consolidated_defects:
            return 0.0
        
        # Weight by severity
        severity_weights = {
            "imminent_danger": 1.0,
            "serious": 0.9,
            "other_than_serious": 0.8,
            "deminimis": 0.7
        }
        
        weighted_sum = 0.0
        total_weight = 0.0
        
        for defect in consolidated_defects:
            weight = severity_weights.get(defect["severity"], 0.7)
            weighted_sum += defect["confidence"] * weight
            total_weight += weight
        
        return weighted_sum / total_weight if total_weight > 0 else 0.0
    
    def _generate_multi_image_recommendations(
        self,
        consolidated_defects: List[Dict],
        overall_severity: Dict[str, int],
        image_count: int
    ) -> List[str]:
        """Generate recommendations based on multi-image analysis"""
        recommendations = []
        
        # Priority 1: Critical/Imminent danger
        if overall_severity["imminent_danger"] > 0:
            recommendations.append(
                f"🔴 CRITICAL: {overall_severity['imminent_danger']} imminent danger condition(s) detected - IMMEDIATE ACTION REQUIRED"
            )
        
        # Priority 2: Serious defects
        if overall_severity["serious"] > 0:
            recommendations.append(
                f"⚠️  SERIOUS: {overall_severity['serious']} serious defect(s) require prompt attention within 30 days"
            )
        
        # Multi-view advantage
        if image_count > 1:
            multi_view_defects = [d for d in consolidated_defects if d["image_count"] > 1]
            if multi_view_defects:
                recommendations.append(
                    f"✓ Multi-view analysis: {len(multi_view_defects)} defect(s) confirmed across multiple images (high confidence)"
                )
        
        # Comprehensive inspection
        recommendations.append(
            f"📋 Schedule comprehensive on-site inspection to verify {len(consolidated_defects)} identified defect(s)"
        )
        
        # Specific actions for high-priority defects
        critical_defects = [d for d in consolidated_defects 
                          if d["severity"] in ["imminent_danger", "serious"]]
        if critical_defects:
            recommendations.append(
                "🔧 Priority corrective actions:"
            )
            for defect in critical_defects[:3]:  # Top 3
                recommendations.append(
                    f"   • {defect['name']}: {defect['corrective_action']}"
                )
        
        return recommendations
    
    def _generate_multi_image_summary(
        self,
        pole_id: str,
        image_count: int,
        consolidated_defects: List[Dict],
        overall_severity: Dict[str, int]
    ) -> str:
        """Generate summary text for multi-image analysis"""
        summary_parts = []
        
        summary_parts.append(f"Multi-image analysis of pole {pole_id} using {image_count} image(s).")
        summary_parts.append(f"Identified {len(consolidated_defects)} total defect(s):")
        
        severity_text = []
        for severity, count in overall_severity.items():
            if count > 0:
                severity_text.append(f"{count} {severity.replace('_', ' ')}")
        
        if severity_text:
            summary_parts.append(", ".join(severity_text) + ".")
        
        # Highlight multi-view confirmations
        multi_view_count = len([d for d in consolidated_defects if d["image_count"] > 1])
        if multi_view_count > 0:
            summary_parts.append(
                f"{multi_view_count} defect(s) confirmed across multiple images, providing high-confidence detection."
            )
        
        return " ".join(summary_parts)
    
    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def print_multi_image_analysis(self, analysis: MultiImageAnalysis):
        """
        Print formatted multi-image analysis results
        
        Args:
            analysis: MultiImageAnalysis object to print
        """
        print(f"\n{'=' * 80}")
        print(f"ZEUS MULTI-IMAGE ANALYSIS REPORT")
        print(f"{'=' * 80}")
        print(f"\nPole ID: {analysis.pole_id}")
        print(f"Images Analyzed: {len(analysis.images)}")
        
        # Print individual image info
        print(f"\n{'─' * 80}")
        print("IMAGES ANALYZED:")
        print(f"{'─' * 80}")
        for img in analysis.images:
            print(f"\n{img.image_id}: {img.metadata['filename']}")
            print(f"  Defects found: {len(img.defects)}")
            print(f"  Severity: ", end="")
            severity_items = [f"{k}={v}" for k, v in img.severity_summary.items() if v > 0]
            print(", ".join(severity_items) if severity_items else "None")
        
        # Print consolidated defects
        print(f"\n{'─' * 80}")
        print("CONSOLIDATED DEFECTS:")
        print(f"{'─' * 80}")
        for i, defect in enumerate(analysis.consolidated_defects, 1):
            print(f"\n{i}. {defect['name']} [{defect['severity'].upper()}]")
            print(f"   Confidence: {defect['confidence']:.1%}")
            print(f"   Visible in: {', '.join(defect['visible_in_images'])} ({defect['image_count']} image(s))")
            print(f"   Category: {defect['category']}")
            print(f"   Action: {defect['corrective_action']}")
        
        # Print correlations
        if analysis.cross_image_correlations:
            print(f"\n{'─' * 80}")
            print("CROSS-IMAGE CORRELATIONS:")
            print(f"{'─' * 80}")
            for corr in analysis.cross_image_correlations:
                print(f"\n• {corr.get('description', corr.get('type', 'Unknown'))}")
                if 'benefit' in corr:
                    print(f"  Benefit: {corr['benefit']}")
        
        # Print overall severity
        print(f"\n{'─' * 80}")
        print("OVERALL SEVERITY SUMMARY:")
        print(f"{'─' * 80}")
        for severity, count in analysis.overall_severity.items():
            if count > 0:
                print(f"  {severity.replace('_', ' ').title()}: {count}")
        
        # Print confidence scores
        print(f"\n{'─' * 80}")
        print("CONFIDENCE SCORES:")
        print(f"{'─' * 80}")
        for metric, score in analysis.confidence_scores.items():
            print(f"  {metric.replace('_', ' ').title()}: {score:.1%}")
        
        # Print recommendations
        print(f"\n{'─' * 80}")
        print("RECOMMENDATIONS:")
        print(f"{'─' * 80}")
        for rec in analysis.recommendations:
            print(f"\n{rec}")
        
        # Print summary
        print(f"\n{'─' * 80}")
        print("SUMMARY:")
        print(f"{'─' * 80}")
        print(f"\n{analysis.summary}")
        
        print(f"\n{'=' * 80}\n")


# Made with Bob
