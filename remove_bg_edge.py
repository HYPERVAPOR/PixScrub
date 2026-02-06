#!/usr/bin/env python3
"""Remove background using edge detection and GrabCut algorithm."""

import argparse
import sys
from datetime import datetime
from pathlib import Path

try:
    import cv2
    import numpy as np
    from PIL import Image
except ImportError as e:
    print(f"Error: {e}")
    print("Install with: pip install opencv-python pillow numpy")
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Remove background using edge detection and GrabCut"
    )
    parser.add_argument(
        "input",
        type=str,
        help="Input image file",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default="outputs",
        help="Output directory (default: outputs/)",
    )
    parser.add_argument(
        "-i",
        "--iterations",
        type=int,
        default=5,
        help="GrabCut iterations (default: 5, higher = better but slower)",
    )
    parser.add_argument(
        "-m",
        "--margin",
        type=int,
        default=10,
        help="Margin from edges for initial foreground rectangle (default: 10 pixels)",
    )
    parser.add_argument(
        "--erode",
        type=int,
        default=2,
        help="Edge erosion in pixels (default: 2)",
    )
    parser.add_argument(
        "--blur",
        type=int,
        default=5,
        help="Blur radius for smoothing (default: 5, set to 0 to disable)",
    )

    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}")
        return 1

    # Create output directory
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Processing: {input_path}")

    # Read image
    img = cv2.imread(str(input_path))
    if img is None:
        print(f"Error: Could not read image: {input_path}")
        return 1

    height, width = img.shape[:2]

    # Create initial mask for GrabCut
    mask = np.zeros(img.shape[:2], np.uint8)

    # Define foreground rectangle (with margin from edges)
    # This assumes the main object is in the center, not touching edges
    rect = (
        args.margin,  # x
        args.margin,  # y
        width - 2 * args.margin,  # width
        height - 2 * args.margin,  # height
    )

    print(f"Initial foreground rectangle: {rect}")

    # Initialize foreground and background models
    bgd_model = np.zeros((1, 65), np.float64)
    fgd_model = np.zeros((1, 65), np.float64)

    # Run GrabCut algorithm
    print(f"Running GrabCut ({args.iterations} iterations)...")
    cv2.grabCut(
        img,
        mask,
        rect,
        bgd_model,
        fgd_model,
        args.iterations,
        cv2.GC_INIT_WITH_RECT,
    )

    # Extract foreground mask
    # Values: 0=background, 1=foreground, 2=likely background, 3=likely foreground
    mask_binary = np.where((mask == 1) | (mask == 3), 255, 0).astype('uint8')

    # Apply morphological operations to clean up the mask
    print("Cleaning up mask...")

    # Remove small noise
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    mask_binary = cv2.morphologyEx(mask_binary, cv2.MORPH_OPEN, kernel, iterations=2)

    # Fill holes
    mask_binary = cv2.morphologyEx(mask_binary, cv2.MORPH_CLOSE, kernel, iterations=2)

    # Edge erosion if requested
    if args.erode > 0:
        print(f"Applying erosion ({args.erode} pixels)...")
        kernel_erode = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        mask_binary = cv2.erode(mask_binary, kernel_erode, iterations=args.erode)

    # Optional blur for smoother edges
    if args.blur > 0:
        print(f"Applying blur (radius={args.blur})...")
        mask_binary = cv2.GaussianBlur(mask_binary, (args.blur, args.blur), 0)

    # Apply mask to image
    print("Applying mask to image...")
    mask_rgb = cv2.cvtColor(mask_binary, cv2.COLOR_GRAY2RGB)
    result = cv2.bitwise_and(img, img, mask=mask_binary)

    # Add alpha channel
    result_bgra = cv2.cvtColor(result, cv2.COLOR_BGR2BGRA)

    # Set transparent pixels
    alpha = mask_binary
    result_bgra[:, :, 3] = alpha

    # Convert to PIL for saving
    result_pil = Image.fromarray(cv2.cvtColor(result_bgra, cv2.COLOR_BGRA2RGBA))

    # Generate output filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
    output_path = output_dir / f"{input_path.stem}_edge_removed_{timestamp}.png"

    # Save image
    result_pil.save(output_path, "PNG")
    print(f"Saved: {output_path}")

    return 0


if __name__ == "__main__":
    exit(main())
