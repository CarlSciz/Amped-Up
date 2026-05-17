# Zeus 3D Training Integration

## Overview

Zeus AI Agent has been enhanced with comprehensive 3D training capabilities using the **Pole Compliance Exemplar Library v0.9**. This integration provides AI-powered defect detection training based on photorealistic 3D-rendered pole inspection scenarios.

## Features

### 1. 3D Training Dataset

The training dataset includes:
- **27 high-resolution images** (1024x1024) of utility poles
- **3 scene types**: compliant, vegetation contact, ice-induced broken crossarm
- **3 camera angles**: front, closeup, three-quarter view
- **3 lighting conditions**: noon, golden hour, overcast
- **9 negative samples** (compliant poles) for balanced training
- **Precise 2D bounding box annotations** for all defects

### 2. Defect Classes

Zeus can detect and classify the following defects:

| Class ID | Defect Type | Severity | NESC Reference |
|----------|-------------|----------|----------------|
| 1 | Vegetation Contact (Branch) | Imminent Danger | NESC 218.A |
| 2 | Broken Crossarm | Imminent Danger | NESC 261.H |
| 3 | Downed Conductor | Imminent Danger | NESC 232, 261 |
| 4 | Ice Buildup | Serious | NESC 250.B |

### 3. Enhanced Inspection Rules

New defect rules have been added to [`pole_inspection_rules.py`](backend/pole_inspection_rules.py):

- **`broken_crossarm`**: Complete or partial crossarm failure detection with 3D model class ID integration
- **`downed_conductor`**: Fallen or dangerously low conductor detection
- **`veg_contact_branch`**: Direct branch-to-conductor contact detection
- **`ice_buildup`**: Ice accumulation monitoring on conductors

Each rule includes:
- Severity classification (OSHA 29 CFR 1903.14)
- NESC and OSHA references
- Detection criteria including 3D model class IDs
- Bounding box detection flags
- Corrective action recommendations
- Weather sensitivity indicators

## Usage

### Accessing Training Data

```python
from backend.zeus_agent import ZeusAgent

# Initialize Zeus with 3D training
zeus = ZeusAgent()

# Get training dataset summary
summary = zeus.get_3d_training_summary()
print(summary)
```

**Output:**
```json
{
  "dataset_info": {
    "version": "0.9.0",
    "description": "Pole Compliance Exemplar Library with 3D rendered scenes",
    "total_images": 27,
    "total_annotations": 27,
    "negative_samples": 9
  },
  "defect_classes": {
    "1": {
      "name": "veg_contact_branch",
      "severity": "imminent_danger",
      "nesc_reference": "NESC 218.A",
      "detection_priority": "high"
    },
    ...
  },
  "scene_distribution": {
    "compliant": 9,
    "vegcontact": 9,
    "ice_broken_arm": 9
  },
  "angle_distribution": {
    "front": 9,
    "closeup": 9,
    "three_quarter": 9
  },
  "lighting_distribution": {
    "noon": 9,
    "golden_hour": 9,
    "overcast": 9
  }
}
```

### Getting Training Recommendations

```python
# Get recommendations for improving training
recommendations = zeus.get_3d_training_recommendations()
for rec in recommendations:
    print(f"- {rec}")
```

### Getting Defect-Specific Training Info

```python
# Get training info for a specific defect
info = zeus.get_defect_training_info("veg_contact_branch")
print(info)
```

**Output:**
```json
{
  "defect_class": "veg_contact_branch",
  "total_samples": 9,
  "scenes": ["vegcontact"],
  "angles": ["front", "closeup", "three_quarter"],
  "lighting_conditions": ["noon", "golden_hour", "overcast"],
  "sample_images": [
    "dataset/3d models/renders/sp35c5_vegcontact_front_noon.png",
    ...
  ]
}
```

### Exporting Training Data

```python
# Export in YOLO format for training
success = zeus.export_training_data(
    output_dir="training_export",
    format="yolo"
)
```

This creates:
- `training_export/labels/*.txt` - YOLO format annotations
- `training_export/classes.txt` - Class names list

## Direct Dataset Access

For advanced use cases, access the dataset directly:

```python
from backend.zeus_3d_training import Zeus3DTrainingIntegration

# Initialize training integration
training = Zeus3DTrainingIntegration()

# Access dataset
dataset = training.dataset

# Get statistics
stats = dataset.get_statistics()

# Get images by scene
compliant_images = dataset.get_images_by_scene("compliant")
defect_images = dataset.get_images_by_defect("broken_crossarm")

# Get negative samples
negative_samples = dataset.get_negative_samples()

# Get defect classes
defect_classes = dataset.get_defect_classes()
```

## Annotation Format

Each image has a corresponding JSON annotation file with this structure:

```json
{
  "image": "sp35c5_vegcontact_front_noon.png",
  "resolution": [1024, 1024],
  "scene": "vegcontact",
  "scene_severity": "imminent_danger",
  "angle": "front",
  "lighting": "noon",
  "camera": {
    "location": [0.0, -18.0, 2.5],
    "rotation_euler_rad": [1.7012, 0.0, 0.0],
    "lens_mm": 50.0,
    "sensor_width_mm": 36.0
  },
  "annotations": [
    {
      "class": "veg_contact_branch",
      "pass_index": 1,
      "bounding_box_2d": {
        "normalized": {
          "x_min": 0.4979,
          "x_max": 0.6799,
          "y_min": 0.2283,
          "y_max": 0.2858
        },
        "pixels": {
          "x_min": 509,
          "x_max": 696,
          "y_min": 233,
          "y_max": 292
        }
      },
      "object_name": "TreeBranchContact"
    }
  ],
  "defect_count_visible": 1,
  "defect_count_in_scene": 1,
  "is_negative_sample": false,
  "defects_off_frame": false
}
```

## Dataset Structure

```
dataset/3d models/
├── README.md                    # Dataset documentation
├── classes.json                 # Defect class definitions
├── generate_v9.py              # Blender generation script
├── draw_bbox_overlays.py       # Visualization script
├── annotations/                 # JSON annotations
│   ├── _index.json             # Combined dataset index
│   └── *.json                  # Per-image annotations (27 files)
├── renders/                     # Rendered images
│   └── *.png                   # Training images (27 files)
├── bbox_overlays/              # Visualization overlays
│   └── *.png                   # Images with bboxes drawn (27 files)
├── assets/                      # Blender assets
│   └── pole_asset_library.blend
└── scene_blends/               # Scene files
    ├── sp35c5_compliant.blend
    ├── sp35c5_vegcontact.blend
    └── sp35c5_ice_broken_arm.blend
```

## Training Pipeline Integration

### Object Detection Training

The dataset is ready for training with popular object detection frameworks:

**YOLOv8/YOLOv9:**
```python
# Export to YOLO format
zeus.export_training_data("yolo_dataset", format="yolo")

# Train with ultralytics
from ultralytics import YOLO
model = YOLO('yolov8n.pt')
model.train(data='yolo_dataset/data.yaml', epochs=100)
```

**Custom Training:**
```python
from backend.zeus_3d_training import Zeus3DTrainingDataset

dataset = Zeus3DTrainingDataset()

for image in dataset.images:
    # Load image
    img_path = image.image_path
    
    # Get annotations
    for ann in image.annotations:
        bbox = ann.bounding_box
        class_id = ann.class_id
        
        # Your training logic here
```

## Bounding Box Utilities

The training module includes utilities for working with bounding boxes:

```python
from backend.zeus_3d_training import BoundingBox2D

# Create bounding box
bbox1 = BoundingBox2D(x_min=0.1, x_max=0.5, y_min=0.2, y_max=0.6)

# Convert to pixels
bbox_pixels = bbox1.to_pixels(width=1024, height=1024)

# Calculate area
area = bbox1.area()

# Calculate IoU with another bbox
bbox2 = BoundingBox2D(x_min=0.3, x_max=0.7, y_min=0.3, y_max=0.7)
iou = bbox1.iou(bbox2)
```

## Validation and Evaluation

```python
from backend.zeus_3d_training import Zeus3DTrainingIntegration

training = Zeus3DTrainingIntegration()

# Validate detection
predicted_bbox = BoundingBox2D(x_min=0.49, x_max=0.68, y_min=0.22, y_max=0.29)
ground_truth_bbox = BoundingBox2D(x_min=0.4979, x_max=0.6799, y_min=0.2283, y_max=0.2858)

is_valid = training.validate_detection(
    predicted_bbox,
    ground_truth_bbox,
    iou_threshold=0.5
)
```

## Integration with MVI

Zeus 3D training integrates seamlessly with the MVI (Machine Vision Inspection) system:

```python
from backend.mvi_zeus_integration import MVIZeusIntegration

# Initialize integration
integration = MVIZeusIntegration()

# Analyze image with Zeus-trained detection
result = integration.analyze_pole_image(
    image_path="path/to/pole_image.jpg",
    pole_id="SP35C5-001"
)

# Results include defect detections with bounding boxes
for defect in result['defects']:
    print(f"Detected: {defect['type']} at {defect['bbox']}")
```

## Best Practices

1. **Balanced Training**: Use all 27 images including the 9 negative samples for balanced model training
2. **Data Augmentation**: Apply augmentation to increase dataset size (rotation, brightness, contrast)
3. **Multi-Angle Training**: Leverage the 3 camera angles for robust detection from any viewpoint
4. **Lighting Invariance**: Use all 3 lighting conditions to ensure detection works in various conditions
5. **Validation Split**: Reserve 20% of data for validation (recommended: 5-6 images)
6. **IoU Threshold**: Use 0.5 IoU threshold for detection validation
7. **Class Weighting**: Consider weighting imminent danger defects higher during training

## Future Enhancements

Planned improvements for v1.0:
- Segmentation masks for pixel-level detection
- Additional pole types (ju40c4, de45c3, daw46, hfw69)
- More defect variants (groundline decay, leaning pole, missing guy)
- Occlusion handling
- Oriented bounding boxes
- Weather condition variations (rain, fog, snow)

## References

- [Pole Compliance Exemplar Library v0.9 README](dataset/3d%20models/README.md)
- [Zeus Agent Documentation](ZEUS_AGENT_README.md)
- [MVI Integration Guide](MVI_ZEUS_INTEGRATION.md)
- [Pole Inspection Rules](backend/pole_inspection_rules.py)
- NESC 2023 (IEEE C2)
- OSHA 29 CFR 1910.269
- ANSI O5.1-2023 Wood Poles

## Support

For questions or issues with the 3D training integration:
1. Check the [dataset README](dataset/3d%20models/README.md)
2. Review the [Zeus agent code](backend/zeus_agent.py)
3. Examine the [training integration module](backend/zeus_3d_training.py)
4. Consult the [inspection rules](backend/pole_inspection_rules.py)