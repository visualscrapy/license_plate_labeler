# License Plate Labeler

A web-based application for manually labeling and validating vehicle images, with a focus on license plate transcription and dataset organization. This tool helps create clean and well-organized datasets for license plate recognition systems.

## Features

- **Dual Image Display**: Shows both full vehicle images and automatic license plate crop previews.
- **Smart Label Management**: Editable label field with auto-capitalization and filtering.
- **Flexible Organization**: Move images between `unlabeled`, `valid`, `invalid`, and `skipped` folders.
- **Preserved Directory Structure**: Keeps subdirectory organization (e.g., `Goa/Ambre_Colony`).
- **Keyboard Shortcuts**: Use Ctrl + keys for fast navigation and actions.
- **Real-time Stats**: Live counters for each image category.

## Folder Structure

```

datasets/
├── unlabeled/               \# Input images
├── valid/                   \# Labeled/validated images
│   └── vehicle_images/
├── invalid/                 \# Invalid images
│   └── vehicle_images/
└── skipped/                 \# Skipped images
└── vehicle_images/

```

## Installation & Setup

### Prerequisites
- Python 3.8+
- pip package manager

### Steps

1. **Install dependencies**

    ```
   
    pip install -r requirements.txt
   
    ```

2. **Setup folders**

    ```
    Note: Not needed it will automatically create the folder strcture. 
    
    mkdir -p datasets/unlabeled
    mkdir -p datasets/valid/vehicle_images
    mkdir -p datasets/invalid/vehicle_images
    mkdir -p datasets/skipped/vehicle_images
    
    # Place your images under datasets/unlabeled (optionally in subfolders)
    
    ```

3. **Run the app**

    ```
    
    python app.py
    
    ```

4. **Access in browser**

Go to: `http://localhost:5000`

5. **Start labeling!**

## UI Overview

- Displays vehicle image and cropped plate side-by-side.
- Editable label field pre-filled with filename.
- Buttons: Previous, Next, Valid, Invalid, Skip, Update Label.
- Keyboard shortcuts implemented.
- Displays counts of images in each category.

## Keyboard Shortcuts

| Shortcut  | Action                |
|-----------|-----------------------|
| Ctrl + P  | Previous Image        |
| Ctrl + N  | Next Image            |
| Ctrl + V  | Mark as Valid         |
| Ctrl + I  | Mark as Invalid       |
| Ctrl + S  | Skip Image            |

## API Endpoints Overview

| Method | Route                    | Description                       |
|--------|--------------------------|-----------------------------------|
| GET    | /                        | Main UI page                      |
| GET    | /images/all              | Returns all image paths           |
| GET    | /images/counts           | Returns images count per category |
| GET    | /preview/<filename>      | Returns cropped plate image       |
| POST   | /images/label            | Rename image and move to valid    |
| POST   | /images/valid            | Mark image as valid (no rename)   |
| POST   | /images/invalid          | Mark image as invalid             |
| POST   | /images/skip             | Mark image as skipped             |
| GET    | /images/serve/<filepath> | Serve image from any folder       |

## Troubleshooting

- **No images loaded?** Confirm images exist in `datasets/unlabeled` and subfolders.
- **No plate crop?** Ensure detection logic in `utils.py` works and images show plates.
- **File move fails?** Check filesystem permissions and folder ownership.
- **Frontend not updating?** Confirm API responses and browser console for JS errors.


This document provides a comprehensive overview of the application, setup, usage, API, and core file handling logic.

If you want assistance with separating JavaScript into external files or integrating the frontend, feel free to ask!```

