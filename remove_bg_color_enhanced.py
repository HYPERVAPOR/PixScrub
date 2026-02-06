#!/usr/bin/env python3
"""Remove background by color with edge cleanup."""

import argparse
import sys
from datetime import datetime
from pathlib import Path

try:
    from PIL import Image, ImageFilter
except ImportError:
    print("Error: pillow not installed")
    print("Install with: pip install pillow")
    sys.exit(1)


def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """Convert hex color to RGB tuple."""
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def color_distance(c1: tuple, c2: tuple) -> float:
    """Calculate Euclidean distance between two colors."""
    return sum((a - b) ** 2 for a, b in zip(c1, c2)) ** 0.5


def is_blueish(r: int, g: int, b: int) -> bool:
    """Check if pixel has blue tint."""
    # Blue dominant or blue component significantly higher
    return b > r * 1.1 and b > g * 1.1


def main():
    parser = argparse.ArgumentParser(
        description="Remove background by color with edge cleanup"
    )
    parser.add_argument(
        "input",
        type=str,
        help="Input image file",
    )
    parser.add_argument(
        "-c",
        "--color",
        type=str,
        default="#34A0D4",
        help="Background color in hex format (default: #34A0D4)",
    )
    parser.add_argument(
        "-t",
        "--tolerance",
        type=float,
        default=40.0,
        help="Color tolerance threshold (default: 40.0)",
    )
    parser.add_argument(
        "-e",
        "--erode",
        type=int,
        default=1,
        help="Edge erosion in pixels to remove fringe (default: 1)",
    )
    parser.add_argument(
        "-b",
        "--blue-tolerance",
        type=float,
        default=25.0,
        help="Additional tolerance for blueish pixels (default: 25.0)",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default="outputs",
        help="Output directory (default: outputs/)",
    )

    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}")
        return 1

    # Parse background color
    try:
        bg_color = hex_to_rgb(args.color)
    except ValueError:
        print(f"Error: Invalid color format: {args.color}")
        return 1

    # Create output directory
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Open image
    print(f"Processing: {input_path}")
    img = Image.open(input_path)

    # Convert to RGBA if needed
    if img.mode != "RGBA":
        img = img.convert("RGBA")

    # Get pixel data
    pixels = img.load()
    width, height = img.size

    # Create alpha mask
    alpha_mask = Image.new("L", (width, height), 255)
    mask_pixels = alpha_mask.load()

    # Process each pixel - build alpha mask
    removed_count = 0
    for y in range(height):
        for x in range(width):
            r, g, b, a = pixels[x, y]

            # Calculate distance from background color
            distance = color_distance((r, g, b), bg_color)

            # Check if should be removed
            should_remove = False

            if distance < args.tolerance:
                # Very close to background color
                should_remove = True
            elif distance < args.tolerance + args.blue_tolerance:
                # Slightly further but has blue tint
                if is_blueish(r, g, b):
                    should_remove = True

            if should_remove:
                mask_pixels[x, y] = 0
                removed_count += 1
            else:
                # Gradual alpha based on distance
                if distance < args.tolerance + 20:
                    alpha_factor = min(1.0, (distance - args.tolerance) / 20)
                    mask_pixels[x, y] = int(255 * alpha_factor)

    total_pixels = width * height
    print(f"Removed {removed_count}/{total_pixels} pixels ({100*removed_count/total_pixels:.1f}%)")

    # Apply erosion to mask if requested
    if args.erode > 0:
        print(f"Applying erosion ({args.erode} pixels)...")
        for _ in range(args.erode):
            alpha_mask = alpha_mask.filter(ImageFilter.MinFilter(3))

    # Apply mask to image
    img.putalpha(alpha_mask)

    # Generate output filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
    output_path = output_dir / f"{input_path.stem}_clean_{timestamp}.png"

    # Save image
    img.save(output_path, "PNG")
    print(f"Saved: {output_path}")

    return 0


if __name__ == "__main__":
    exit(main())
