import os
from PIL import Image
from ultralytics import YOLO

DETECTION_MODEL_PATH = "models/license_plate_detect_v1_E160.pt"
UNLABELED = 'unlabeled/vehicle_images'
SKIPPED_VEHICLE = 'skipped/vehicle_images'
VALID_VEHICLE = 'valid/vehicle_images_with_label'
INVALID_VEHICLE = 'invalid/vehicle_images'



def run_detection_on_image(image_path):
    img = Image.open(image_path).convert("RGB")
    model_path = DETECTION_MODEL_PATH
    model = YOLO(model_path)
    results = model(img)
    # Find the first box with class==0 (assuming 0 = license plate)
    for box in results[0].boxes:
        class_id = int(box.cls[0])
        if class_id == 0:
            x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
            plate_crop = img.crop((x1, y1, x2, y2))
            return {"plate_crop": plate_crop}
    return {}


def save_cropped_plate_by_label(src_img_path, dest_folder, label):
    result = run_detection_on_image(src_img_path)
    if result and 'plate_crop' in result:
        plate_crop = result['plate_crop']
        crop_path = os.path.join(dest_folder, f"{label}.jpg")
        plate_crop.save(crop_path)

def count_images_in_directory(directory):
    """Recursively counts the number of files in a directory."""
    count = 0
    if os.path.exists(directory):
        for root, _, files in os.walk(directory):
            for file in files:
                if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                    count += 1
    return count

def get_base_folder(path):
    """
    Determine which base folder a path belongs to, based on its prefix.
    """
    path = path.replace("\\", "/")
    if path.startswith("valid/"):
        return VALID_VEHICLE
    elif path.startswith("invalid/"):
        return INVALID_VEHICLE
    elif path.startswith("skipped/"):
        return SKIPPED_VEHICLE
    else:
        return UNLABELED

