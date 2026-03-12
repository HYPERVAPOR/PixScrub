#!/usr/bin/env python3
"""Crop image by percentage from edges."""

import argparse
import sys
from datetime import datetime
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("Error: pillow not installed")
    print("Install with: pip install pillow")
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Crop image by percentage from edges"
    )
    parser.add_argument(
        "input",
        type=str,
        help="Input image file",
    )
    parser.add_argument(
        "-t",
        "--top",
        type=float,
        default=20.0,
        help="Percentage to crop from top (default: 20.0)",
    )
    parser.add_argument(
        "-b",
        "--bottom",
        type=float,
        default=20.0,
        help="Percentage to crop from bottom (default: 20.0)",
    )
    parser.add_argument(
        "-l",
        "--left",
        type=float,
        default=0.0,
        help="Percentage to crop from left (default: 0.0)",
    )
    parser.add_argument(
        "-r",
        "--right",
        type=float,
        default=0.0,
        help="Percentage to crop from right (default: 0.0)",
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

    # Create output directory
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Processing: {input_path}")

    # Open image
    img = Image.open(input_path)
    width, height = img.size

    print(f"Original size: {width}x{height}")

    # Calculate crop box
    left = int(width * args.left / 100)
    top = int(height * args.top / 100)
    right = int(width * (100 - args.right) / 100)
    bottom = int(height * (100 - args.bottom) / 100)

    print(f"Crop: top={args.top}%, bottom={args.bottom}%, left={args.left}%, right={args.right}%")
    print(f"Crop box: ({left}, {top}, {right}, {bottom})")

    # Crop image
    cropped = img.crop((left, top, right, bottom))

    print(f"Cropped size: {cropped.size[0]}x{cropped.size[1]}")

    # Generate output filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
    output_path = output_dir / f"{input_path.stem}_cropped_{timestamp}.png"

    # Save image
    cropped.save(output_path, "PNG")
    print(f"Saved: {output_path}")

    return 0


if __name__ == "__main__":
    exit(main())
