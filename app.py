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
import shutil
from io import BytesIO
from flask import Flask, request, render_template, jsonify, send_from_directory, send_file

# Import your local utility function for license plate detection
from utils import run_detection_on_image, count_images_in_directory

app = Flask(__name__)

# Base directory setup
BASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'datasets')

# Define image category directories under datasets
UNLABELED_BASE = os.path.join(BASE_DIR, 'unlabeled')
VALID_BASE = os.path.join(BASE_DIR, 'valid')
SKIPPED_BASE = os.path.join(BASE_DIR, 'skipped')
INVALID_BASE = os.path.join(BASE_DIR, 'invalid')


def move_image(source_path, dest_dir, new_label=None):
    """
    Moves and optionally renames an image file from its current location to a target directory.
    Preserves subdirectory structure relative to category folder.
    """
    try:
        # Normalize path separators
        normalized_path = source_path.replace('\\', '/')
        # The source path is always relative to BASE_DIR
        src_full_path = os.path.join(BASE_DIR, normalized_path)
        # Check file exists
        if not os.path.exists(src_full_path):
            print(f"Source file not found: {src_full_path}", file=sys.stderr)
            return None

        _, ext = os.path.splitext(src_full_path)
        # Construct new filename: replace entirely with cleaned label + extension
        if new_label:
            safe_label = new_label.replace('/', '_').replace('\\', '_')
            new_filename = f"{safe_label}{ext}"
        else:
            new_filename = os.path.basename(src_full_path)

        # Remove the category folder name from the relative path to preserve subfolder structure
        parts = normalized_path.split('/')
        relative_dir = os.path.join(*parts[1:-1]) if len(parts) > 2 else ''
        dest_subdir = os.path.join(dest_dir, relative_dir)
        os.makedirs(dest_subdir, exist_ok=True)
        dst_full_path = os.path.join(dest_subdir, new_filename)
        # Remove destination file if exists to prevent errors
        if os.path.exists(dst_full_path):
            os.remove(dst_full_path)
        # Move the file
        shutil.move(src_full_path, dst_full_path)
        print(f"Moved {src_full_path} to {dst_full_path}")
        # Return relative path for UI and API usage (forward slashes)
        rel_path = os.path.relpath(dst_full_path, BASE_DIR).replace('\\', '/')
        return rel_path

    except Exception as e:
        print(f"Error in move_image: {e}", file=sys.stderr)
        return None

def get_image_counts():
    """Return counts of images in each managed directory."""
    return {
        'unlabeled': count_images_in_directory(UNLABELED_BASE),
        'valid': count_images_in_directory(VALID_BASE),
        'invalid': count_images_in_directory(INVALID_BASE),
        'skipped': count_images_in_directory(SKIPPED_BASE),
    }


def get_all_images():
    """Return sorted list of all image paths relative to datasets folder."""
    all_images = []
    folders = {
        'unlabeled': UNLABELED_BASE,
        'valid': VALID_BASE,
        'invalid': INVALID_BASE,
        'skipped': SKIPPED_BASE,
    }
    for folder_name, folder_path in folders.items():
        if os.path.exists(folder_path):
            for root, _, files in os.walk(folder_path):
                for file in files:
                    if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                        rel_path = os.path.relpath(os.path.join(root, file), BASE_DIR)
                        all_images.append(rel_path.replace('\\', '/'))
    return sorted(all_images)


@app.route('/')
def index():
    """Serves main labeling interface."""
    return render_template('labeler.html')


@app.route('/images/all')
def images_all():
    """Returns JSON array of all images for frontend."""
    return jsonify(get_all_images())


@app.route('/images/counts')
def images_counts():
    """Returns JSON counts for images in all categories."""
    return jsonify(get_image_counts())


@app.route('/images/image-details/<path:filename>')
def image_details(filename):
    """Returns details for a given image file."""
    full_path = os.path.join(BASE_DIR, filename)
    if not os.path.exists(full_path):
        return jsonify({}), 404

    base_filename = os.path.basename(filename)
    detected_label = os.path.splitext(base_filename)[0]

    return jsonify({
        'img': filename,
        'label': detected_label,
        'cropped_img_url': f'/preview_crop/{filename}'
    })


@app.route('/preview_crop/<path:filename>')
def preview_crop(filename):
    """Generates and serves cropped license plate image on the fly."""
    full_path = os.path.join(BASE_DIR, filename)
    if not os.path.exists(full_path):
        return jsonify({'error': 'Image not found'}), 404

    try:
        result = run_detection_on_image(full_path)
        if result and 'plate_crop' in result:
            buf = BytesIO()
            result['plate_crop'].save(buf, format='JPEG')
            buf.seek(0)
            return send_file(buf, mimetype='image/jpeg')
        else:
            return jsonify({'error': 'No license plate detected'}), 404
    except Exception as e:
        print(f"Error in preview_crop: {e}", file=sys.stderr)
        return jsonify({'error': str(e)}), 500


@app.route('/images/label', methods=['POST'])
def label_image():
    """Move image to valid with new label."""
    data = request.json
    new_path = move_image(data['img'], VALID_BASE, data.get('label'))
    return jsonify({'success': new_path is not None, 'new_path': new_path, 'counts': get_image_counts()})


@app.route('/images/valid', methods=['POST'])
def valid_image():
    """Move image to valid keeping current label or original filename."""
    data = request.json
    label = data.get('label') or os.path.splitext(os.path.basename(data['img']))[0]
    new_path = move_image(data['img'], VALID_BASE, label)
    return jsonify({'success': new_path is not None, 'new_path': new_path, 'counts': get_image_counts()})


@app.route('/images/invalid', methods=['POST'])
def invalid_image():
    """Move image to invalid."""
    data = request.json
    new_path = move_image(data['img'], INVALID_BASE)
    return jsonify({'success': new_path is not None, 'new_path': new_path, 'counts': get_image_counts()})


@app.route('/images/skip', methods=['POST'])
def skip_image():
    """Move image to skipped."""
    data = request.json
    new_path = move_image(data['img'], SKIPPED_BASE)
    return jsonify({'success': new_path is not None, 'new_path': new_path, 'counts': get_image_counts()})


@app.route('/unlabeled/<path:filename>')
def serve_unlabeled(filename):
    """Serve unlabeled image including subdirectories."""
    return send_from_directory(UNLABELED_BASE, filename)


@app.route('/valid/<path:filename>')
def serve_valid(filename):
    """Serve valid images."""
    return send_from_directory(VALID_BASE, filename)


@app.route('/invalid/<path:filename>')
def serve_invalid(filename):
    """Serve invalid images."""
    return send_from_directory(INVALID_BASE, filename)


@app.route('/skipped/<path:filename>')
def serve_skipped(filename):
    """Serve skipped images."""
    return send_from_directory(SKIPPED_BASE, filename)


if __name__ == '__main__':
    # Ensure all folders exist on start
    for folder in [UNLABELED_BASE, VALID_BASE, SKIPPED_BASE, INVALID_BASE]:
        os.makedirs(folder, exist_ok=True)
    app.run(debug=True, port=8000)
