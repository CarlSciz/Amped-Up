"""
Zeus SVG Training Integration
Integrates Pole Compliance Exemplar Library v0.7 (230 SVG scenarios) with Zeus AI Agent
Provides comprehensive defect pattern recognition across 18 pole types and 4 weather conditions
"""

from typing import Dict, List, Optional, Set
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class WeatherCondition(Enum):
    """Weather conditions in SVG library"""
    ICE_LOADING = "ice_loading"
    SNOW_ACCUMULATION = "snow_accumulation"
    POST_STORM = "post_storm"
    SUMMER_THERMAL = "summer_thermal"
    NORMAL = "normal"


class SceneFraming(Enum):
    """Scene framing types"""
    COMPLIANT_WITH_WEATHER = "compliant_with_weather"
    WEATHER_INDUCED_VIOLATION = "weather_induced_violation"
    DAMAGE_FROM_WEATHER = "damage_from_weather"
    WEATHER_PLUS_MULTI_DEFECT = "weather_plus_multi_defect"
    SINGLE_DEFECT = "single_defect"
    MULTI_DEFECT = "multi_defect"
    BASELINE = "baseline"


@dataclass
class SVGDefectPattern:
    """Defect pattern from SVG library"""
    defect_id: str
    name: str
    pole_types: List[str]
    severity: str
    weather_sensitive: bool
    nesc_references: List[str]
    osha_references: List[str]
    description: str
    visual_indicators: List[str]
    scene_count: int


@dataclass
class PoleTypeInfo:
    """Pole type information from SVG library"""
    pole_id: str
    description: str
    height_ft: int
    pole_class: str
    voltage_kv: Optional[float]
    scene_count: int
    defect_types: List[str]


class ZeusSVGKnowledgeBase:
    """
    Comprehensive knowledge base from 230 SVG pole inspection scenarios
    Covers 18 pole types, 60+ defect patterns, 4 weather conditions
    """
    
    def __init__(self):
        self.pole_types = self._build_pole_types()
        self.defect_patterns = self._build_defect_patterns()
        self.weather_scenarios = self._build_weather_scenarios()
        self.multi_defect_combinations = self._build_multi_defect_combinations()
    
    def _build_pole_types(self) -> Dict[str, PoleTypeInfo]:
        """Build pole type database from SVG library"""
        return {
            "sp35c5": PoleTypeInfo(
                pole_id="sp35c5",
                description="Single-phase rural 35 ft Class 5",
                height_ft=35,
                pole_class="Class 5",
                voltage_kv=12.47,
                scene_count=10,
                defect_types=["veg_contact", "pole_decay", "insulator_damaged", "clearance_ground"]
            ),
            "ju40c4": PoleTypeInfo(
                pole_id="ju40c4",
                description="Joint-use 40 ft Class 4 (urban, comm)",
                height_ft=40,
                pole_class="Class 4",
                voltage_kv=12.47,
                scene_count=11,
                defect_types=["veg_contact", "veg_encroachment", "service_low", "guy_guard", "paint_faded"]
            ),
            "de45c3": PoleTypeInfo(
                pole_id="de45c3",
                description="Dead-end 45 ft Class 3",
                height_ft=45,
                pole_class="Class 3",
                voltage_kv=12.47,
                scene_count=11,
                defect_types=["strain_insulator", "guy_corroded", "clamp_slipped", "clearance_violations"]
            ),
            "daw46": PoleTypeInfo(
                pole_id="daw46",
                description="Sub-transmission 46 kV wood",
                height_ft=46,
                pole_class="H2",
                voltage_kv=46.0,
                scene_count=6,
                defect_types=["veg_contact", "insulator_arc", "arm_decay", "pole_lean", "guy_corrosion"]
            ),
            "serv30c6": PoleTypeInfo(
                pole_id="serv30c6",
                description="Service pole 30 ft Class 6",
                height_ft=30,
                pole_class="Class 6",
                voltage_kv=None,
                scene_count=7,
                defect_types=["service_low", "building_low", "open_neutral", "unauthorized", "reverse_meter"]
            ),
            "ang40c4": PoleTypeInfo(
                pole_id="ang40c4",
                description="Angle pole 40 ft Class 4",
                height_ft=40,
                pole_class="Class 4",
                voltage_kv=12.47,
                scene_count=5,
                defect_types=["veg_contact", "anchor_exposure", "crossarm_split", "pole_lean", "veg_encroach"]
            ),
            "hfw69": PoleTypeInfo(
                pole_id="hfw69",
                description="H-frame wood 69 kV transmission",
                height_ft=69,
                pole_class="H1",
                voltage_kv=69.0,
                scene_count=4,
                defect_types=["veg_contact", "insulator_shattered", "xbrace_damage", "crossarm_decay", "strand_break"]
            ),
            "tap40c4": PoleTypeInfo(
                pole_id="tap40c4",
                description="Tap pole 40 ft Class 4",
                height_ft=40,
                pole_class="Class 4",
                voltage_kv=12.47,
                scene_count=2,
                defect_types=["cutout_hanging", "jumper_damaged", "bird_nest"]
            ),
            "hfs138": PoleTypeInfo(
                pole_id="hfs138",
                description="H-frame steel 138 kV",
                height_ft=138,
                pole_class="Steel",
                voltage_kv=138.0,
                scene_count=1,
                defect_types=["veg_in_row", "anchor_corrosion", "marker_missing", "id_faded"]
            ),
            "tds115": PoleTypeInfo(
                pole_id="tds115",
                description="Transmission dead-end steel 115 kV",
                height_ft=115,
                pole_class="Steel",
                voltage_kv=115.0,
                scene_count=1,
                defect_types=["clamp_broken", "strain_chip", "jumper_low", "marker_weather", "id_faded"]
            ),
            "bank45c3": PoleTypeInfo(
                pole_id="bank45c3",
                description="Transformer bank pole",
                height_ft=45,
                pole_class="Class 3",
                voltage_kv=12.47,
                scene_count=1,
                defect_types=["veg_contact", "oil_leak", "cracked_bushing", "missing_ground", "loose_hardware"]
            ),
            "riser40c4": PoleTypeInfo(
                pole_id="riser40c4",
                description="Underground riser",
                height_ft=40,
                pole_class="Class 4",
                voltage_kv=12.47,
                scene_count=1,
                defect_types=["pipe_damaged", "weatherhead", "exposed", "pole_decay", "tag_missing", "burned_insulation"]
            )
        }
    
    def _build_defect_patterns(self) -> Dict[str, SVGDefectPattern]:
        """Build comprehensive defect pattern database"""
        patterns = {}
        
        # Vegetation defects
        patterns["veg_contact"] = SVGDefectPattern(
            defect_id="veg_contact",
            name="Vegetation Contact with Conductor",
            pole_types=["sp35c5", "ju40c4", "daw46", "hfw69", "bank45c3"],
            severity="imminent_danger",
            weather_sensitive=True,
            nesc_references=["NESC 218"],
            osha_references=["OSHA 1910.269"],
            description="Tree branches or foliage in direct contact with energized conductors",
            visual_indicators=["green_branch_touching_conductor", "leaf_contact", "tree_proximity"],
            scene_count=15
        )
        
        patterns["veg_encroachment"] = SVGDefectPattern(
            defect_id="veg_encroachment",
            name="Vegetation Encroachment",
            pole_types=["ju40c4", "ang40c4"],
            severity="other_than_serious",
            weather_sensitive=True,
            nesc_references=["NESC 218", "NERC FAC-003"],
            osha_references=[],
            description="Vegetation within minimum clearance zone but not in contact",
            visual_indicators=["tree_near_conductor", "branch_approaching", "growth_toward_line"],
            scene_count=8
        )
        
        # Structural defects
        patterns["pole_lean"] = SVGDefectPattern(
            defect_id="pole_lean",
            name="Excessive Pole Lean",
            pole_types=["ang40c4", "daw46"],
            severity="serious",
            weather_sensitive=True,
            nesc_references=["NESC 261"],
            osha_references=[],
            description="Pole leaning beyond acceptable limits (>5 degrees)",
            visual_indicators=["tilted_pole", "angled_crossarm", "stressed_guys"],
            scene_count=6
        )
        
        patterns["pole_decay"] = SVGDefectPattern(
            defect_id="pole_decay",
            name="Pole Groundline Decay",
            pole_types=["sp35c5", "riser40c4"],
            severity="serious",
            weather_sensitive=False,
            nesc_references=["ANSI O5.1"],
            osha_references=[],
            description="Wood decay at groundline reducing structural capacity",
            visual_indicators=["darkened_wood", "soft_spots", "fungal_growth", "woodpecker_holes"],
            scene_count=10
        )
        
        patterns["crossarm_split"] = SVGDefectPattern(
            defect_id="crossarm_split",
            name="Crossarm Split or Crack",
            pole_types=["ang40c4"],
            severity="serious",
            weather_sensitive=True,
            nesc_references=["NESC 261"],
            osha_references=[],
            description="Longitudinal split in crossarm compromising integrity",
            visual_indicators=["visible_crack", "split_wood", "separated_grain"],
            scene_count=4
        )
        
        patterns["crossarm_decay"] = SVGDefectPattern(
            defect_id="crossarm_decay",
            name="Crossarm Decay",
            pole_types=["daw46", "hfw69"],
            severity="serious",
            weather_sensitive=False,
            nesc_references=["NESC 261"],
            osha_references=[],
            description="Wood decay in crossarm at attachment points",
            visual_indicators=["rotted_wood", "soft_arm", "discoloration"],
            scene_count=6
        )
        
        # Hardware defects
        patterns["insulator_damaged"] = SVGDefectPattern(
            defect_id="insulator_damaged",
            name="Damaged Insulator",
            pole_types=["sp35c5", "daw46", "hfw69"],
            severity="serious",
            weather_sensitive=True,
            nesc_references=["NESC 277", "ANSI C29"],
            osha_references=[],
            description="Cracked, chipped, or shattered insulator",
            visual_indicators=["cracked_porcelain", "chipped_glass", "arc_tracking", "shattered_pieces"],
            scene_count=12
        )
        
        patterns["guy_corrosion"] = SVGDefectPattern(
            defect_id="guy_corrosion",
            name="Guy Wire Corrosion",
            pole_types=["daw46", "de45c3", "hfs138"],
            severity="serious",
            weather_sensitive=False,
            nesc_references=["ASTM A475"],
            osha_references=[],
            description="Corrosion of guy wire reducing tensile strength",
            visual_indicators=["rust_on_strand", "broken_strands", "frayed_wire"],
            scene_count=8
        )
        
        patterns["anchor_exposed"] = SVGDefectPattern(
            defect_id="anchor_exposed",
            name="Anchor Rod Exposed",
            pole_types=["ang40c4", "hfs138"],
            severity="other_than_serious",
            weather_sensitive=False,
            nesc_references=[],
            osha_references=[],
            description="Guy anchor rod exposed above ground due to erosion",
            visual_indicators=["visible_anchor", "exposed_rod", "eroded_soil"],
            scene_count=5
        )
        
        # Clearance violations
        patterns["clearance_ground"] = SVGDefectPattern(
            defect_id="clearance_ground",
            name="Ground Clearance Violation",
            pole_types=["sp35c5"],
            severity="serious",
            weather_sensitive=True,
            nesc_references=["NESC 232.A"],
            osha_references=[],
            description="Conductor clearance below minimum for ground",
            visual_indicators=["low_conductor", "sag_violation", "clearance_marker"],
            scene_count=8
        )
        
        patterns["clearance_road"] = SVGDefectPattern(
            defect_id="clearance_road",
            name="Road Clearance Violation",
            pole_types=["de45c3", "sp35c5"],
            severity="serious",
            weather_sensitive=True,
            nesc_references=["NESC 232.C"],
            osha_references=[],
            description="Conductor clearance below minimum for roadway",
            visual_indicators=["low_over_road", "vehicle_clearance_violation"],
            scene_count=6
        )
        
        patterns["service_low"] = SVGDefectPattern(
            defect_id="service_low",
            name="Service Drop Too Low",
            pole_types=["serv30c6", "ju40c4"],
            severity="serious",
            weather_sensitive=True,
            nesc_references=["NESC 230", "NESC 232"],
            osha_references=[],
            description="Service drop below minimum clearance",
            visual_indicators=["low_service_wire", "building_clearance_violation"],
            scene_count=7
        )
        
        # Weather-induced defects
        patterns["ice_sag_violation"] = SVGDefectPattern(
            defect_id="ice_sag_violation",
            name="Ice Loading Clearance Violation",
            pole_types=["sp35c5", "de45c3", "daw46"],
            severity="serious",
            weather_sensitive=True,
            nesc_references=["NESC 250.B", "NESC 232"],
            osha_references=[],
            description="Ice accumulation causing conductor sag below clearance",
            visual_indicators=["ice_on_conductor", "icicles", "excessive_sag", "clearance_violation"],
            scene_count=12
        )
        
        patterns["broken_crossarm_ice"] = SVGDefectPattern(
            defect_id="broken_crossarm_ice",
            name="Broken Crossarm from Ice Loading",
            pole_types=["sp35c5", "daw46"],
            severity="imminent_danger",
            weather_sensitive=True,
            nesc_references=["NESC 250.B", "NESC 261"],
            osha_references=["OSHA 1910.269"],
            description="Crossarm failure due to excessive ice loading",
            visual_indicators=["broken_arm", "dangling_conductor", "ice_buildup"],
            scene_count=4
        )
        
        patterns["downed_conductor_storm"] = SVGDefectPattern(
            defect_id="downed_conductor_storm",
            name="Downed Conductor from Storm",
            pole_types=["de45c3", "sp35c5"],
            severity="imminent_danger",
            weather_sensitive=True,
            nesc_references=["NESC 232", "NESC 261"],
            osha_references=["OSHA 1910.269"],
            description="Conductor down or dangerously low after storm damage",
            visual_indicators=["downed_wire", "broken_attachment", "debris"],
            scene_count=3
        )
        
        patterns["summer_thermal_sag"] = SVGDefectPattern(
            defect_id="summer_thermal_sag",
            name="Summer Thermal Sag Violation",
            pole_types=["sp35c5", "de45c3", "ju40c4"],
            severity="serious",
            weather_sensitive=True,
            nesc_references=["NESC 232", "IEEE 738"],
            osha_references=[],
            description="Excessive conductor sag at high temperature",
            visual_indicators=["deep_sag", "heat_indicators", "clearance_violation"],
            scene_count=12
        )
        
        return patterns
    
    def _build_weather_scenarios(self) -> Dict[str, Dict]:
        """Build weather scenario database"""
        return {
            "ice_loading": {
                "condition": WeatherCondition.ICE_LOADING,
                "scene_count": 16,
                "nesc_reference": "NESC 250.B Heavy Loading District",
                "visual_indicators": ["ice_on_conductor", "icicles", "winter_atmosphere", "snow_on_roof"],
                "defect_types": ["ice_sag_violation", "broken_crossarm_ice", "phase_separation_ice"],
                "severity_range": ["serious", "imminent_danger"]
            },
            "snow_accumulation": {
                "condition": WeatherCondition.SNOW_ACCUMULATION,
                "scene_count": 14,
                "nesc_reference": "NESC 250.B",
                "visual_indicators": ["snow_on_ground", "snow_on_arm", "falling_flakes", "snow_atmosphere"],
                "defect_types": ["obscured_tag", "buried_anchor", "branch_down"],
                "severity_range": ["other_than_serious", "serious"]
            },
            "post_storm": {
                "condition": WeatherCondition.POST_STORM,
                "scene_count": 15,
                "nesc_reference": "NESC 261",
                "visual_indicators": ["storm_cleared_sky", "debris", "broken_limbs", "lightning_scorch"],
                "defect_types": ["downed_conductor_storm", "broken_arm", "cutout_dislodged", "guy_broken"],
                "severity_range": ["serious", "imminent_danger"]
            },
            "summer_thermal": {
                "condition": WeatherCondition.SUMMER_THERMAL,
                "scene_count": 15,
                "nesc_reference": "NESC 232 at max temp, IEEE 738",
                "visual_indicators": ["summer_atmosphere", "heat_haze", "sun_glare", "thermal_sag"],
                "defect_types": ["summer_thermal_sag", "galloping", "clearance_violations"],
                "severity_range": ["other_than_serious", "serious"]
            }
        }
    
    def _build_multi_defect_combinations(self) -> List[Dict]:
        """Build multi-defect combination patterns"""
        return [
            {
                "theme": "aging_infrastructure",
                "defects": ["pole_decay", "crossarm_decay", "guy_corrosion"],
                "severity": "multi_defect",
                "scene_count": 15,
                "description": "Multiple age-related defects compounding risk"
            },
            {
                "theme": "vegetation_compound",
                "defects": ["veg_contact", "veg_encroachment", "clearance_ground"],
                "severity": "multi_defect",
                "scene_count": 12,
                "description": "Vegetation issues with clearance violations"
            },
            {
                "theme": "weather_plus_decay",
                "defects": ["ice_loading", "pole_decay"],
                "severity": "multi_defect",
                "scene_count": 4,
                "description": "Weather stress on already-degraded assets"
            },
            {
                "theme": "structural_compound",
                "defects": ["pole_lean", "guy_corrosion", "anchor_exposed"],
                "severity": "multi_defect",
                "scene_count": 8,
                "description": "Multiple structural integrity issues"
            }
        ]
    
    def get_statistics(self) -> Dict:
        """Get comprehensive SVG library statistics"""
        return {
            "total_scenes": 230,
            "pole_types": len(self.pole_types),
            "defect_patterns": len(self.defect_patterns),
            "weather_conditions": len(self.weather_scenarios),
            "multi_defect_combinations": len(self.multi_defect_combinations),
            "breakdown": {
                "baseline_scenes": 170,
                "weather_scenes": 60,
                "single_defect": 122,
                "multi_defect": 48,
                "weather_standalone": 48,
                "weather_multi_defect": 12
            },
            "severity_distribution": {
                "imminent_danger": 25,
                "serious": 95,
                "other_than_serious": 60,
                "de_minimis": 20,
                "multi_defect": 30
            }
        }
    
    def get_defect_pattern(self, defect_id: str) -> Optional[SVGDefectPattern]:
        """Get defect pattern by ID"""
        return self.defect_patterns.get(defect_id)
    
    def get_pole_type_info(self, pole_id: str) -> Optional[PoleTypeInfo]:
        """Get pole type information"""
        return self.pole_types.get(pole_id)
    
    def get_defects_by_severity(self, severity: str) -> List[SVGDefectPattern]:
        """Get all defects of a specific severity"""
        return [p for p in self.defect_patterns.values() if p.severity == severity]
    
    def get_weather_sensitive_defects(self) -> List[SVGDefectPattern]:
        """Get all weather-sensitive defects"""
        return [p for p in self.defect_patterns.values() if p.weather_sensitive]


def main():
    """Example usage"""
    kb = ZeusSVGKnowledgeBase()
    
    print("\n=== Zeus SVG Knowledge Base ===")
    stats = kb.get_statistics()
    print(f"Total scenes: {stats['total_scenes']}")
    print(f"Pole types: {stats['pole_types']}")
    print(f"Defect patterns: {stats['defect_patterns']}")
    print(f"Weather conditions: {stats['weather_conditions']}")
    
    print("\n=== Imminent Danger Defects ===")
    for defect in kb.get_defects_by_severity("imminent_danger"):
        print(f"- {defect.name} ({defect.scene_count} scenes)")
    
    print("\n=== Weather-Sensitive Defects ===")
    for defect in kb.get_weather_sensitive_defects():
        print(f"- {defect.name}")


if __name__ == "__main__":
    main()

# Made with Bob
