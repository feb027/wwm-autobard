"""Add rounded corners to an icon image."""

from PIL import Image, ImageDraw
import sys
from pathlib import Path


def add_rounded_corners(input_path: str, output_path: str = None, radius: int = 50):
    """Add rounded corners to an image.
    
    Args:
        input_path: Path to input PNG image
        output_path: Path to output PNG (defaults to input with _rounded suffix)
        radius: Corner radius in pixels (default 50 for 256x256 image)
    """
    img = Image.open(input_path).convert("RGBA")
    
    # Create rounded mask
    mask = Image.new("L", img.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle([(0, 0), img.size], radius=radius, fill=255)
    
    # Apply mask
    result = Image.new("RGBA", img.size, (0, 0, 0, 0))
    result.paste(img, mask=mask)
    
    # Output path
    if output_path is None:
        p = Path(input_path)
        output_path = str(p.parent / f"{p.stem}_rounded{p.suffix}")
    
    result.save(output_path, "PNG")
    print(f"Saved: {output_path}")
    return output_path


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python round_icon.py <input.png> [output.png] [radius]")
        print("Example: python round_icon.py icon.png icon_rounded.png 50")
        sys.exit(1)
    
    input_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None
    radius = int(sys.argv[3]) if len(sys.argv) > 3 else 50
    
    add_rounded_corners(input_path, output_path, radius)
