# License Plate Labeler

This repository contains a minimal web application for manually labeling and validating vehicle images, with a focus on license plate transcription and dataset organization.

---

## Folder Structure & Workflow

- **unlabeled/**  
  All input vehicle images (with number plates) are placed here. This is the primary input directory for the labeling process.

- **valid/**  
  When a user marks an image as "Valid" or "Update Label," the image is moved to this directory. The file is renamed to the specified license plate label for a cleaner, properly labeled dataset.

- **invalid/**  
  Images marked as "Invalid" (e.g., license plate not present or unreadable) are moved here.

- **skipped/**  
  When the user chooses "Skip," the image is moved here for later review.

Subdirectory structures (e.g., `state/city`) are preserved when moving images between these folders.

---

## UI/Frontend Layout (Per Image)

- **Vehicle Image & Cropped Numberplate:**  
  Shows the full-size vehicle image alongside a dynamically generated cropped numberplate, displayed via the backend.

- **label_name:**  
  Editable text field showing the vehicle number.  
  - Automatically capitalizes all letters and filters non-alphanumeric characters.
  - Cursor position is preserved while editing (does not jump to the end on input).

- **Control Buttons:**  
  - **Previous:** Show previous image in the loaded list.
  - **Next:** Show next image in the loaded list.
  - **Valid:** Move current image to the valid/ directory; then show the next image.
  - **Invalid:** Move current image to the invalid/ directory; then show the next image.
  - **Skip:** Move current image to the skipped/ directory; then show the next image.
  - **Update Label:** Rename the file using new label, move to valid/, then show the next image.

---

## Application Flow (Step by Step)

### Startup

- Loads the full list of image paths from `/images/all`.
- The first image is loaded and displayed (vehicle and cropped plate).

### User Actions

- **Navigation:**  
  Users can navigate through the image list using "Previous" & "Next" — all on the client side.
- **Validation:**  
  - **Valid:** Moves the file to valid/ with its label (possibly updating its filename).
  - **Update Label:** User edits the label field, confirms, and the image is renamed/moved to valid/.
- **Invalidation:**  
  - **Invalid:** Moves file to invalid/.
- **Skipping:**  
  - **Skip:** Moves file to skipped/.

All actions load the next image automatically.

---

## Backend Implementation (Python Flask)

- Serves the UI and all image files from managed folders (`unlabeled`, `valid`, `invalid`, and `skipped`).
- Provides RESTful API endpoints for all client actions and file management.
- Dynamically generates cropped numberplate images using YOLO detection (no cropped images stored on disk).
- Properly maintains subdirectory structure for moved files.

### API Endpoints

- `GET /`  
  Serves the main `labeler.html` UI.

- `GET /images/all`  
  Returns a JSON list of all (relative) image paths for navigation.

- `GET /images/image-details/<path:filename>`  
  Returns JSON data for a specific image, including detected label and cropped preview path.

- `GET /preview_crop/<path:filename>`  
  Dynamically generates and serves a cropped license plate image.

- `POST /images/label`  
  Handles the "Update Label" action (rename + move to valid/).

- `POST /images/valid`  
  Handles the "Valid" action (move to valid/).

- `POST /images/invalid`  
  Handles the "Invalid" action (move to invalid/).

- `POST /images/skip`  
  Handles the "Skip" action (move to skipped/).

- `GET /{folder_name}/<path:filename>`  
  Serves images from their respective directories.

---

## Frontend (HTML/JavaScript)

- Fetches and caches the comprehensive image list from the backend.
- Displays vehicle image, cropped numberplate, and editable label field.
- All controls are bound with event listeners that trigger relevant backend API actions.
- Navigation (Previous/Next) is handled entirely client-side for fast UX.
- Cropped plate images are generated on-request and displayed via the `/preview_crop/` endpoint.

---

## Features

- ✅ Full vehicle and cropped numberplate display.
- ✅ Editable, auto-cleaned label field for direct text entry.
- ✅ Valid, Invalid, Skip, and Label actions move files as required.
- ✅ Quick navigation using Previous and Next buttons.
- ✅ Dynamic, YOLO-based license plate cropping, never saved to disk.
- ✅ Subdirectory preservation when moving/renaming images to maintain context.

---

## Installation & Setup

**Prerequisites:**
- Python 3.8+
- pip

**Install Dependencies:**

\`\`\`
pip install flask Pillow ultralytics
\`\`\`

---

## TODO LIST

⏳ Add batch actions & keyboard shortcuts  
⏳ Improve image loading performance for very large datasets  
⏳ User authentication for labeling app  
⏳ Support for video file input and frame extraction

---

## Code Reference

- **UI/HTML:** See \`templates/labeler.html\`
- **Backend:** See \`app.py\` for Flask route implementations
- **Detection Logic:** See \`utils.py\` for license plate detection (YOLO) integration

---
