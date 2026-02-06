#!/usr/bin/env python3
"""Generate images using ZhipuAI GLM-Image model (standalone version)."""

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path
from urllib.request import urlretrieve

try:
    from zai import ZhipuAiClient
except ImportError:
    print("Error: zai-sdk not installed")
    print("Install with: pip install zai-sdk")
    sys.exit(1)


def parse_size(size_str: str) -> tuple[int, int]:
    """Parse size string like '1024x1024' to (1024, 1024)."""
    try:
        width, height = size_str.lower().split("x")
        return int(width), int(height)
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"Invalid size format: {size_str}. Use format like '1024x1024'"
        )


def main():
    parser = argparse.ArgumentParser(
        description="Generate images using ZhipuAI GLM-Image model"
    )
    parser.add_argument(
        "prompt",
        type=str,
        help="Text prompt for image generation",
    )
    parser.add_argument(
        "-s",
        "--size",
        type=str,
        default="1024x1024",
        help="Image size in format WxH (default: 1024x1024)",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default="images",
        help="Output directory (default: images/)",
    )
    parser.add_argument(
        "-n",
        "--count",
        type=int,
        default=1,
        choices=[1, 2, 4],
        help="Number of images to generate (default: 1)",
    )

    args = parser.parse_args()

    # Get API key from environment
    api_key = os.environ.get("ZHIPUAI_API_KEY") or os.environ.get("ZHIPU_API_KEY")
    if not api_key:
        print("Error: ZHIPUAI_API_KEY environment variable not set")
        print("Please set it with: export ZHIPUAI_API_KEY='your-api-key'")
        return 1

    # Parse image size
    width, height = parse_size(args.size)

    # Create output directory
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Initialize client
    client = ZhipuAiClient(api_key=api_key)

    # Generate image
    print(f"Generating image with prompt: {args.prompt}")
    print(f"Size: {width}x{height}")

    try:
        response = client.images.generations(
            model="glm-image",
            prompt=args.prompt,
            size=f"{width}x{height}",
            n=args.count,
        )
    except Exception as e:
        print(f"Error generating image: {e}")
        return 1

    # Download and save images
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
    saved_files = []

    for idx, image in enumerate(response.data, 1):
        filename = f"gen_{timestamp}_{idx}.png"
        filepath = output_dir / filename

        print(f"Downloading: {image.url}")
        urlretrieve(image.url, filepath)
        saved_files.append(filepath)
        print(f"Saved: {filepath}")

    print(f"\nGenerated {len(saved_files)} image(s)")
    return 0


if __name__ == "__main__":
    exit(main())
