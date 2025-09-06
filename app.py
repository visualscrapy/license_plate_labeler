"""
Vehicle Image Labeler

This Flask application serves as a web-based tool for the manual labeling of vehicle images. It is designed to be used by a single operator to quickly categorize and label images of vehicles, specifically focusing on the detection and transcription of license plates.

The application's core functionality is a Flask web server that handles:

1.  **Image Serving and Display.**
    -   It reads images from a hierarchical directory structure starting at 'unlabeled'.
    -   It dynamically serves a full-size vehicle image and an on-the-fly cropped license plate image for each file.
    -   The license plate crop is generated using an external utility function (`run_detection_on_image`) and is not stored on disk.

2.  **User Interaction and File Management.**
    -   The user interface is provided by `labeler.html`, which uses JavaScript to navigate through the image list and handle actions.
    -   Based on user input, the application moves the current image file from its source directory into one of three destination directories:
        -   `valid`: For images with a correct and confirmed license plate label. The filename is renamed to the provided label.
        -   `invalid`: For images where the license plate is not a valid candidate. The original filename is preserved.
        -   `skipped`: For images the user chooses to skip and label later. The original filename is preserved.

3.  **Directory Structure.**
    -   The application expects and maintains a specific folder structure to manage files:
        -   `unlabeled/`: The source directory for all new, un-processed images.
        -   `valid/`: The destination for successfully labeled images.
        -   `invalid/`: The destination for invalid images.
        -   `skipped/`: The destination for images that are skipped.
    -   The `move_image` function ensures that the subdirectory structure (e.g., `Goa/Ambre_Colony`) is preserved in the destination folders, avoiding improper nesting.

**Flask Routes:**

-   `GET /`: Serves the main `labeler.html` interface.
-   `GET /images/all`: Returns a JSON array of all image paths from all managed directories.
-   `GET /images/counts`: Returns the counts of images in each directory.
-   `GET /preview_crop/<path:filename>`: Generates and serves a cropped license plate image on-the-fly.
-   `POST /images/label`: Moves an image to the 'valid' directory and renames it with the provided label.
-   `POST /images/valid`: Moves an image to the 'valid' directory without changing the label.
-   `POST /images/invalid`: Moves an image to the 'invalid' directory.
-   `POST /images/skip`: Moves an image to the 'skipped' directory.
-   `GET /unlabeled/<path:filename>`: Serves images from the 'unlabeled' directory.

**Dependencies:**

-   `Flask`: For the web application framework.
-   `shutil`: For file operations (moving files).
-   `os`: For path manipulation.
-   `Pillow` (`PIL`): For image handling.
-   `YOLO` (`ultralytics`): Assumed to be available for the detection model in `utils.py`.
"""

import sys
import os
import re
import shutil
from flask import Flask, request, render_template, jsonify, send_from_directory, send_file
from io import BytesIO

# Import your local utility function for license plate detection
from utils import run_detection_on_image, count_images_in_directory

app = Flask(__name__)

current_dir = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.join(current_dir, 'datasets')
UNLABELED = os.path.join(BASE_DIR, 'unlabeled')
VALID_VEHICLE = os.path.join(BASE_DIR, 'valid')
SKIPPED_VEHICLE = os.path.join(BASE_DIR, 'skipped')
INVALID_VEHICLE = os.path.join(BASE_DIR, 'invalid')

# --- Directory Setup ---
def setup_directories():
    """Ensures that all necessary directories exist."""
    os.makedirs(UNLABELED, exist_ok=True)
    os.makedirs(VALID_VEHICLE, exist_ok=True)
    os.makedirs(INVALID_VEHICLE, exist_ok=True)
    os.makedirs(SKIPPED_VEHICLE, exist_ok=True)


def move_image(source_path, dest_dir, new_label=None):
    """
    Moves an image from its source path to a destination directory,
    preserving the subdirectory structure and renaming the file with the new label (if provided).
    """
    try:
        # The source_path from the front end is already relative to the 'unlabeled' folder
        src_full_path = os.path.join(BASE_DIR, source_path)
        # Check file exists
        if not os.path.exists(src_full_path):
            print(f"Source file not found: {src_full_path}")
            return None

        # Determine the relative subdirectory, removing the 'unlabeled' part from the path.
        if source_path.startswith('unlabeled/'):
            relative_subdir_path = os.path.dirname(source_path[len('unlabeled/'):])
        else:
            # For images already in other folders, this logic will still work.
            relative_subdir_path = os.path.dirname(source_path)

        dest_subdir = os.path.join(dest_dir, relative_subdir_path)

        # Ensure the destination subdirectory exists
        os.makedirs(dest_subdir, exist_ok=True)

        if new_label:
            # Sanitize the new label and get the file extension
            sanitized_label = re.sub(r'[^a-zA-Z0-9_-]', '', new_label).upper().replace(' ', '')
            _, extension = os.path.splitext(source_path)
            new_filename = f"{sanitized_label}{extension}"
        else:
            new_filename = os.path.basename(source_path)

        dst_full_path = os.path.join(dest_subdir, new_filename)

        # Move the file from the source to the new destination
        shutil.move(src_full_path, dst_full_path)
        print(f"Moved {src_full_path} to {dst_full_path}")

        # Return the new path relative to the BASE_DIR
        rel_path = os.path.relpath(dst_full_path, BASE_DIR)
        return rel_path.replace('\\', '/')
    except Exception as e:
        print(f"Error in move_image: {e}")
        return None

def get_image_counts():
    """Returns a dictionary with the counts of images in each folder."""
    return {
        'unlabeled': count_images_in_directory(UNLABELED),
        'valid': count_images_in_directory(VALID_VEHICLE),
        'invalid': count_images_in_directory(INVALID_VEHICLE),
        'skipped': count_images_in_directory(SKIPPED_VEHICLE),
    }

# --- API Endpoints ---
@app.route('/')
def index():
    """Serves the main labeling UI."""
    return render_template('labeler.html')

@app.route('/images/all')
def get_all_images():
    image_list = []
    # For each folder, get relative paths with the folder name prefixed
    folders = {
        'unlabeled': UNLABELED,
        'valid': VALID_VEHICLE,
        'invalid': INVALID_VEHICLE,
        'skipped': SKIPPED_VEHICLE,
    }
    for folder_name, folder_path in folders.items():
        for root, _, files in os.walk(folder_path):
            for file in files:
                if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                    rel_path = os.path.relpath(os.path.join(root, file), BASE_DIR)
                    rel_path = os.path.normpath(rel_path)
                    image_list.append(rel_path.replace('\\', '/'))  # Normalize slashes for URLs
    return jsonify(image_list)

@app.route('/images/counts')
def get_counts():
    """Returns the counts of images in each directory."""
    return jsonify(get_image_counts())

@app.route('/preview_crop/<path:filename>')
def preview_crop(filename):
    full_path = os.path.join(BASE_DIR, filename)
    if not os.path.exists(full_path):
        return jsonify({'error': 'Image not found at specified path'}), 404
    try:
        detection_result = run_detection_on_image(full_path)
        if detection_result and 'plate_crop' in detection_result:
            img_io = BytesIO()
            detection_result['plate_crop'].save(img_io, 'JPEG')
            img_io.seek(0)
            return send_file(img_io, mimetype='image/jpeg')
        else:
            return jsonify({'error': 'No license plate detected'}), 404
    except Exception as e:
        print(f"Error processing image for crop: {e}", file=sys.stderr)
        return jsonify({'error': f'An error occurred: {e}'}), 500

@app.route('/images/label', methods=['POST'])
def update_label():
    """Handles the 'update label' action."""
    relative_img_path = request.json['img']
    label = request.json['label']
    new_path = move_image(relative_img_path, VALID_VEHICLE, label)
    if new_path is None:
        return jsonify({'success': False, 'error': 'Failed to move image'}), 500
    counts = get_image_counts()
    return jsonify({'success': True, 'new_path': new_path, 'counts': counts})

@app.route('/images/valid', methods=['POST'])
def valid_image():
    """Handles the 'valid' action."""
    relative_img_path = request.json['img']
    label = request.json.get('label') or os.path.splitext(os.path.basename(relative_img_path))[0]
    new_path = move_image(relative_img_path, VALID_VEHICLE, label)
    if new_path is None:
        return jsonify({'success': False, 'error': 'Failed to move image'}), 500
    counts = get_image_counts()
    return jsonify({'success': True, 'new_path': new_path, 'counts': counts})

@app.route('/images/invalid', methods=['POST'])
def invalid_image():
    """Handles the 'invalid' action."""
    relative_img_path = request.json['img']
    new_path = move_image(relative_img_path, INVALID_VEHICLE)
    if new_path is None:
        return jsonify({'success': False, 'error': 'Failed to move image'}), 500
    counts = get_image_counts()
    return jsonify({'success': True, 'new_path': new_path, 'counts': counts})

@app.route('/images/skip', methods=['POST'])
def skip_image():
    """Handles the 'skip' action."""
    relative_img_path = request.json['img']
    new_path = move_image(relative_img_path, SKIPPED_VEHICLE)
    if new_path is None:
        return jsonify({'success': False, 'error': 'Failed to move image'}), 500
    counts = get_image_counts()
    return jsonify({'success': True, 'new_path': new_path, 'counts': counts})

@app.route('/images/serve/<path:filepath>')
def serve_image(filepath):
    """Serves an image from any directory relative to the BASE_DIR."""
    full_path = os.path.join(BASE_DIR, filepath)
    if not os.path.exists(full_path):
        print(f"File not found: {full_path}")
        return jsonify({'error': 'Image not found'}), 404
    # Serve file from its real folder
    # Serve relative to BASE_DIR
    folder = os.path.dirname(full_path)
    filename = os.path.basename(full_path)
    return send_from_directory(folder, filename)


# --- Image Serving Routes ---
@app.route('/unlabeled/<path:filename>')
def serve_unlabeled(filename):
    """Serves an unlabeled image from the directory."""
    return send_from_directory(UNLABELED, filename)

if __name__ == '__main__':
    setup_directories()
    app.run(debug=True, port=8000, use_reloader=True)
