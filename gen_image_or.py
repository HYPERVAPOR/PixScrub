#!/usr/bin/env python3
"""Generate images using OpenRouter Gemini Flash Image model."""

import argparse
import base64
import os
import sys
from datetime import datetime
from pathlib import Path

try:
    import requests
except ImportError:
    print("Error: requests not installed")
    print("Install with: pip install requests")
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
        description="Generate images using OpenRouter Gemini Flash Image"
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

    args = parser.parse_args()

    # Get API key from environment
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        print("Error: OPENROUTER_API_KEY environment variable not set")
        print("Please set it with: export OPENROUTER_API_KEY='your-api-key'")
        return 1

    # Parse image size
    width, height = parse_size(args.size)

    # Create output directory
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate image using OpenRouter API
    print(f"Generating image with prompt: {args.prompt}")
    print(f"Size: {width}x{height}")

    try:
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "google/gemini-2.5-flash-image",
                "messages": [
                    {
                        "role": "user",
                        "content": args.prompt
                    }
                ],
                "modalities": ["image", "text"],
                "stream": False,
            },
            timeout=120,
        )

        response.raise_for_status()
        result = response.json()

        # Extract image from response
        # Format: .choices[0].message.images[0].image_url.url
        if "choices" not in result or len(result["choices"]) == 0:
            print(f"Error: No choices in response")
            print(f"Response: {result}")
            return 1

        message = result["choices"][0]["message"]

        if "images" not in message or len(message["images"]) == 0:
            print(f"Error: No images in response")
            print(f"Message: {message}")
            return 1

        # Get base64 data URI
        image_data_uri = message["images"][0]["image_url"]["url"]

        # Remove "data:image/png;base64," or similar prefix
        if image_data_uri.startswith("data:"):
            # Format: data:image/png;base64,<base64_data>
            _, base64_data = image_data_uri.split(",", 1)
            image_bytes = base64.b64decode(base64_data)
        else:
            # Assume it's a direct URL
            print(f"Downloading from URL: {image_data_uri}")
            img_response = requests.get(image_data_uri, timeout=60)
            img_response.raise_for_status()
            image_bytes = img_response.content

        # Save image
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        filename = f"gen_{timestamp}_1.png"
        filepath = output_dir / filename

        with open(filepath, "wb") as f:
            f.write(image_bytes)

        print(f"Saved: {filepath}")
        return 0

    except requests.exceptions.RequestException as e:
        print(f"Error generating image: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
