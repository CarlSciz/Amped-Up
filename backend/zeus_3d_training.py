"""
Zeus 3D Model Training Integration
Integrates Pole Compliance Exemplar Library v0.9 with Zeus AI Agent
Provides training data loading, defect detection, and model evaluation capabilities
"""

import json
import os
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


@dataclass
class BoundingBox2D:
    """2D bounding box for defect detection"""
    x_min: float
    x_max: float
    y_min: float
    y_max: float
    normalized: bool = True
    
    def to_pixels(self, width: int, height: int) -> 'BoundingBox2D':
        """Convert normalized coordinates to pixel coordinates"""
        if not self.normalized:
            return self
        return BoundingBox2D(
            x_min=int(self.x_min * width),
            x_max=int(self.x_max * width),
            y_min=int(self.y_min * height),
            y_max=int(self.y_max * height),
            normalized=False
        )
    
    def area(self) -> float:
        """Calculate bounding box area"""
        return (self.x_max - self.x_min) * (self.y_max - self.y_min)
    
    def iou(self, other: 'BoundingBox2D') -> float:
        """Calculate Intersection over Union with another bounding box"""
        x_left = max(self.x_min, other.x_min)
        y_top = max(self.y_min, other.y_min)
        x_right = min(self.x_max, other.x_max)
        y_bottom = min(self.y_max, other.y_max)
        
        if x_right < x_left or y_bottom < y_top:
            return 0.0
        
        intersection = (x_right - x_left) * (y_bottom - y_top)
        union = self.area() + other.area() - intersection
        
        return intersection / union if union > 0 else 0.0


@dataclass
class DefectAnnotation:
    """Defect annotation from 3D model dataset"""
    defect_class: str
    class_id: int
    bounding_box: BoundingBox2D
    object_name: str
    pass_index: int


@dataclass
class TrainingImage:
    """Training image with annotations"""
    image_path: str
    resolution: Tuple[int, int]
    scene: str
    scene_severity: str
    angle: str
    lighting: str
    camera: Dict
    annotations: List[DefectAnnotation]
    defect_count_visible: int
    defect_count_in_scene: int
    is_negative_sample: bool
    defects_off_frame: bool


@dataclass
class DefectClass:
    """Defect class definition"""
    id: int
    name: str
    is_defect: bool
    severity: str = "unknown"
    description: str = ""


class Zeus3DTrainingDataset:
    """
    Zeus 3D Training Dataset Loader
    Loads and manages the Pole Compliance Exemplar Library v0.9
    """
    
    def __init__(self, dataset_path: str = "dataset/3d models"):
        self.dataset_path = Path(dataset_path)
        self.annotations_path = self.dataset_path / "annotations"
        self.renders_path = self.dataset_path / "renders"
        self.bbox_overlays_path = self.dataset_path / "bbox_overlays"
        
        self.classes: Dict[int, DefectClass] = {}
        self.images: List[TrainingImage] = []
        self.index_data: Optional[Dict] = None
        
        self._load_classes()
        self._load_index()
        self._load_annotations()
    
    def _load_classes(self):
        """Load defect class definitions"""
        classes_file = self.dataset_path / "classes.json"
        if not classes_file.exists():
            logger.warning(f"Classes file not found: {classes_file}")
            return
        
        with open(classes_file, 'r') as f:
            data = json.load(f)
        
        for cls in data.get("classes", []):
            defect_class = DefectClass(
                id=cls["id"],
                name=cls["name"],
                is_defect=cls.get("is_defect", False)
            )
            self.classes[cls["id"]] = defect_class
        
        logger.info(f"Loaded {len(self.classes)} defect classes")
    
    def _load_index(self):
        """Load dataset index"""
        index_file = self.annotations_path / "_index.json"
        if not index_file.exists():
            logger.warning(f"Index file not found: {index_file}")
            return
        
        with open(index_file, 'r') as f:
            self.index_data = json.load(f)
        
        if self.index_data:
            version = self.index_data.get('info', {}).get('version', 'unknown')
            logger.info(f"Loaded dataset index v{version}")
    
    def _load_annotations(self):
        """Load all image annotations"""
        if not self.annotations_path.exists():
            logger.warning(f"Annotations path not found: {self.annotations_path}")
            return
        
        annotation_files = list(self.annotations_path.glob("*.json"))
        annotation_files = [f for f in annotation_files if f.name != "_index.json"]
        
        for ann_file in annotation_files:
            try:
                with open(ann_file, 'r') as f:
                    data = json.load(f)
                
                # Parse annotations
                annotations = []
                for ann in data.get("annotations", []):
                    bbox_data = ann["bounding_box_2d"]["normalized"]
                    bbox = BoundingBox2D(
                        x_min=bbox_data["x_min"],
                        x_max=bbox_data["x_max"],
                        y_min=bbox_data["y_min"],
                        y_max=bbox_data["y_max"],
                        normalized=True
                    )
                    
                    defect_ann = DefectAnnotation(
                        defect_class=ann["class"],
                        class_id=ann["pass_index"],
                        bounding_box=bbox,
                        object_name=ann["object_name"],
                        pass_index=ann["pass_index"]
                    )
                    annotations.append(defect_ann)
                
                # Create training image
                image = TrainingImage(
                    image_path=str(self.renders_path / data["image"]),
                    resolution=tuple(data["resolution"]),
                    scene=data["scene"],
                    scene_severity=data["scene_severity"],
                    angle=data["angle"],
                    lighting=data["lighting"],
                    camera=data["camera"],
                    annotations=annotations,
                    defect_count_visible=data["defect_count_visible"],
                    defect_count_in_scene=data["defect_count_in_scene"],
                    is_negative_sample=data["is_negative_sample"],
                    defects_off_frame=data["defects_off_frame"]
                )
                
                self.images.append(image)
            
            except Exception as e:
                logger.error(f"Error loading annotation {ann_file}: {e}")
        
        logger.info(f"Loaded {len(self.images)} training images")
    
    def get_statistics(self) -> Dict:
        """Get dataset statistics"""
        stats = {
            "total_images": len(self.images),
            "total_classes": len(self.classes),
            "defect_classes": sum(1 for c in self.classes.values() if c.is_defect),
            "negative_samples": sum(1 for img in self.images if img.is_negative_sample),
            "total_annotations": sum(len(img.annotations) for img in self.images),
            "scenes": {},
            "angles": {},
            "lighting_conditions": {},
            "defect_distribution": {}
        }
        
        for img in self.images:
            # Count scenes
            stats["scenes"][img.scene] = stats["scenes"].get(img.scene, 0) + 1
            
            # Count angles
            stats["angles"][img.angle] = stats["angles"].get(img.angle, 0) + 1
            
            # Count lighting
            stats["lighting_conditions"][img.lighting] = stats["lighting_conditions"].get(img.lighting, 0) + 1
            
            # Count defects
            for ann in img.annotations:
                stats["defect_distribution"][ann.defect_class] = \
                    stats["defect_distribution"].get(ann.defect_class, 0) + 1
        
        return stats
    
    def get_images_by_scene(self, scene: str) -> List[TrainingImage]:
        """Get all images for a specific scene"""
        return [img for img in self.images if img.scene == scene]
    
    def get_images_by_defect(self, defect_class: str) -> List[TrainingImage]:
        """Get all images containing a specific defect"""
        return [img for img in self.images 
                if any(ann.defect_class == defect_class for ann in img.annotations)]
    
    def get_negative_samples(self) -> List[TrainingImage]:
        """Get all negative (compliant) samples"""
        return [img for img in self.images if img.is_negative_sample]
    
    def get_defect_classes(self) -> List[DefectClass]:
        """Get all defect classes"""
        return [cls for cls in self.classes.values() if cls.is_defect]


class Zeus3DTrainingIntegration:
    """
    Integration layer between Zeus AI Agent and 3D training dataset
    Provides defect detection training and evaluation capabilities
    """
    
    def __init__(self, dataset_path: str = "dataset/3d models"):
        self.dataset = Zeus3DTrainingDataset(dataset_path)
        self.training_config = self._build_training_config()
    
    def _build_training_config(self) -> Dict:
        """Build training configuration"""
        return {
            "version": "0.9.0",
            "dataset_type": "pole_compliance_exemplar",
            "annotation_format": "coco_style_2d_bbox",
            "image_resolution": [1024, 1024],
            "defect_classes": {
                1: {
                    "name": "veg_contact_branch",
                    "severity": "imminent_danger",
                    "nesc_reference": "NESC 218.A",
                    "detection_priority": "high"
                },
                2: {
                    "name": "broken_crossarm",
                    "severity": "imminent_danger",
                    "nesc_reference": "NESC 261.H",
                    "detection_priority": "critical"
                },
                3: {
                    "name": "downed_conductor",
                    "severity": "imminent_danger",
                    "nesc_reference": "NESC 232, 261",
                    "detection_priority": "critical"
                },
                4: {
                    "name": "ice_buildup",
                    "severity": "serious",
                    "nesc_reference": "NESC 250.B",
                    "detection_priority": "medium"
                }
            },
            "training_parameters": {
                "batch_size": 8,
                "learning_rate": 0.001,
                "epochs": 100,
                "validation_split": 0.2,
                "augmentation": True
            },
            "evaluation_metrics": [
                "precision",
                "recall",
                "f1_score",
                "mAP",
                "iou_threshold"
            ]
        }
    
    def get_training_summary(self) -> Dict:
        """Get comprehensive training dataset summary"""
        stats = self.dataset.get_statistics()
        
        return {
            "dataset_info": {
                "version": "0.9.0",
                "description": "Pole Compliance Exemplar Library with 3D rendered scenes",
                "total_images": stats["total_images"],
                "total_annotations": stats["total_annotations"],
                "negative_samples": stats["negative_samples"]
            },
            "defect_classes": self.training_config["defect_classes"],
            "scene_distribution": stats["scenes"],
            "angle_distribution": stats["angles"],
            "lighting_distribution": stats["lighting_conditions"],
            "defect_distribution": stats["defect_distribution"],
            "training_config": self.training_config["training_parameters"]
        }
    
    def validate_detection(self, predicted_bbox: BoundingBox2D, 
                          ground_truth_bbox: BoundingBox2D,
                          iou_threshold: float = 0.5) -> bool:
        """Validate a detection against ground truth"""
        iou = predicted_bbox.iou(ground_truth_bbox)
        return iou >= iou_threshold
    
    def get_training_recommendations(self) -> List[str]:
        """Get recommendations for training Zeus on this dataset"""
        stats = self.dataset.get_statistics()
        recommendations = []
        
        # Check dataset balance
        if stats["negative_samples"] < stats["total_images"] * 0.3:
            recommendations.append(
                "Consider adding more negative (compliant) samples for better model balance"
            )
        
        # Check defect distribution
        defect_counts = stats["defect_distribution"]
        if defect_counts:
            min_count = min(defect_counts.values())
            max_count = max(defect_counts.values())
            if max_count > min_count * 3:
                recommendations.append(
                    "Defect class distribution is imbalanced. Consider data augmentation or resampling"
                )
        
        # Check scene variety
        if len(stats["scenes"]) < 5:
            recommendations.append(
                "Limited scene variety. Consider adding more pole types and configurations"
            )
        
        # Check angle coverage
        if len(stats["angles"]) < 3:
            recommendations.append(
                "Limited viewing angles. Add more camera perspectives for robust detection"
            )
        
        # Check lighting conditions
        if len(stats["lighting_conditions"]) < 3:
            recommendations.append(
                "Limited lighting conditions. Add varied lighting for real-world robustness"
            )
        
        if not recommendations:
            recommendations.append(
                "Dataset is well-balanced and ready for training"
            )
        
        return recommendations
    
    def export_yolo_format(self, output_dir: str):
        """Export annotations in YOLO format for training"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        labels_dir = output_path / "labels"
        labels_dir.mkdir(exist_ok=True)
        
        for img in self.dataset.images:
            # Create YOLO format label file
            label_file = labels_dir / f"{Path(img.image_path).stem}.txt"
            
            with open(label_file, 'w') as f:
                for ann in img.annotations:
                    # YOLO format: class_id center_x center_y width height (normalized)
                    bbox = ann.bounding_box
                    center_x = (bbox.x_min + bbox.x_max) / 2
                    center_y = (bbox.y_min + bbox.y_max) / 2
                    width = bbox.x_max - bbox.x_min
                    height = bbox.y_max - bbox.y_min
                    
                    f.write(f"{ann.class_id} {center_x} {center_y} {width} {height}\n")
        
        # Create classes.txt
        classes_file = output_path / "classes.txt"
        with open(classes_file, 'w') as f:
            defect_classes = sorted(
                [c for c in self.dataset.classes.values() if c.is_defect],
                key=lambda x: x.id
            )
            for cls in defect_classes:
                f.write(f"{cls.name}\n")
        
        logger.info(f"Exported YOLO format to {output_dir}")


def main():
    """Example usage of Zeus 3D Training Integration"""
    # Initialize training integration
    training = Zeus3DTrainingIntegration()
    
    # Get training summary
    summary = training.get_training_summary()
    print("\n=== Zeus 3D Training Dataset Summary ===")
    print(json.dumps(summary, indent=2))
    
    # Get recommendations
    recommendations = training.get_training_recommendations()
    print("\n=== Training Recommendations ===")
    for i, rec in enumerate(recommendations, 1):
        print(f"{i}. {rec}")
    
    # Export YOLO format
    # training.export_yolo_format("dataset/3d models/yolo_export")


if __name__ == "__main__":
    main()

# Made with Bob
