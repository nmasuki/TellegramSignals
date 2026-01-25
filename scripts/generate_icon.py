"""Generate application icon based on golden geometric design"""
from PIL import Image, ImageDraw
import math
import random

def create_app_icon(size=256):
    """Create a golden geometric icon with diamond and ripples"""
    # Create black background
    img = Image.new('RGBA', (size, size), (0, 0, 0, 255))
    draw = ImageDraw.Draw(img)

    center_x = size // 2
    center_y = size // 2

    # Golden color palette
    gold_bright = (255, 215, 0, 255)       # Bright gold
    gold_medium = (218, 165, 32, 255)      # Golden rod
    gold_dark = (184, 134, 11, 255)        # Dark golden rod
    gold_glow = (255, 223, 100, 180)       # Gold with transparency for glow

    # Draw concentric ripple circles at the bottom
    ripple_center_y = int(size * 0.75)
    num_ripples = max(3, min(8, size // 32))
    for i in range(num_ripples, 0, -1):
        radius = int(size * 0.08 * i)
        alpha = max(40, 200 - i * 20)
        ripple_color = (218, 165, 32, alpha)

        # Draw ellipse (flattened circle for perspective)
        ellipse_height = max(1, radius // 3)
        bbox = [
            center_x - radius,
            ripple_center_y - ellipse_height,
            center_x + radius,
            ripple_center_y + ellipse_height
        ]
        draw.ellipse(bbox, outline=ripple_color, width=max(1, size // 128))

    # Draw the central pillar/tower
    pillar_width = size // 10
    pillar_top = int(size * 0.35)
    pillar_bottom = int(size * 0.72)

    # Pillar body with gradient effect (using multiple rectangles)
    half_width = max(1, pillar_width // 2)
    for i in range(pillar_width):
        intensity = 1.0 - abs(i - half_width) / half_width * 0.5
        r = int(218 * intensity)
        g = int(165 * intensity)
        b = int(32 * intensity)
        x = center_x - half_width + i
        draw.line([(x, pillar_top), (x, pillar_bottom)], fill=(r, g, b, 255), width=1)

    # Draw decorative X pattern on pillar (only for larger sizes)
    if size >= 64:
        x_top = int(size * 0.45)
        x_bottom = int(size * 0.65)
        x_left = center_x - half_width
        x_right = center_x + half_width
        line_width = max(1, size // 128)

        draw.line([(x_left, x_top), (x_right, x_bottom)], fill=gold_bright, width=line_width)
        draw.line([(x_right, x_top), (x_left, x_bottom)], fill=gold_bright, width=line_width)

    # Draw the main diamond at the top
    diamond_center_y = int(size * 0.2)
    diamond_size = int(size * 0.15)

    diamond_points = [
        (center_x, diamond_center_y - diamond_size),      # Top
        (center_x + diamond_size, diamond_center_y),       # Right
        (center_x, diamond_center_y + diamond_size),       # Bottom
        (center_x - diamond_size, diamond_center_y)        # Left
    ]

    # Draw diamond with glow effect (only for larger sizes)
    if size >= 64:
        for glow_size in range(3, 0, -1):
            glow_points = [
                (center_x, diamond_center_y - diamond_size - glow_size * 3),
                (center_x + diamond_size + glow_size * 3, diamond_center_y),
                (center_x, diamond_center_y + diamond_size + glow_size * 3),
                (center_x - diamond_size - glow_size * 3, diamond_center_y)
            ]
            alpha = 30 + glow_size * 20
            draw.polygon(glow_points, outline=(255, 223, 100, alpha), width=1)

    # Main diamond outline
    draw.polygon(diamond_points, outline=gold_bright, width=max(1, size // 86))

    # Inner diamond (only for larger sizes)
    if size >= 48:
        inner_size = int(diamond_size * 0.6)
        inner_diamond = [
            (center_x, diamond_center_y - inner_size),
            (center_x + inner_size, diamond_center_y),
            (center_x, diamond_center_y + inner_size),
            (center_x - inner_size, diamond_center_y)
        ]
        draw.polygon(inner_diamond, outline=gold_medium, width=max(1, size // 128))

    # Draw connecting line from diamond to pillar
    draw.line(
        [(center_x, diamond_center_y + diamond_size), (center_x, pillar_top)],
        fill=gold_medium,
        width=max(1, size // 128)
    )

    # Add sparkle dots around the diamond (only for larger sizes)
    if size >= 128:
        random.seed(42)  # Consistent sparkle positions
        num_sparkles = size // 8
        for _ in range(num_sparkles):
            angle = random.uniform(0, 2 * math.pi)
            distance = random.uniform(diamond_size * 1.5, diamond_size * 3)
            spark_x = int(center_x + math.cos(angle) * distance)
            spark_y = int(diamond_center_y + math.sin(angle) * distance * 0.7)

            if 0 <= spark_x < size and 0 <= spark_y < size * 0.4:
                spark_size = max(1, size // 128)
                alpha = random.randint(100, 255)
                draw.ellipse(
                    [spark_x - spark_size, spark_y - spark_size,
                     spark_x + spark_size, spark_y + spark_size],
                    fill=(255, 223, 100, alpha)
                )

    return img


def main():
    """Generate icons at various sizes"""
    from pathlib import Path

    # Output directory
    output_dir = Path(__file__).parent.parent / "src" / "gui" / "resources" / "icons"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate main app icon
    icon = create_app_icon(256)
    icon.save(output_dir / "app.png", "PNG")
    print(f"Created: {output_dir / 'app.png'}")

    # Generate ICO file for Windows (multiple sizes)
    sizes = [16, 32, 48, 64, 128, 256]
    icons = []
    for s in sizes:
        icons.append(create_app_icon(s))

    # Save ICO with multiple sizes
    icons[5].save(
        output_dir / "app.ico",
        format='ICO',
        sizes=[(s, s) for s in sizes]
    )
    print(f"Created: {output_dir / 'app.ico'}")

    # Generate tray icon (smaller, simpler version)
    tray_icon = create_app_icon(64)
    tray_icon.save(output_dir / "tray.png", "PNG")
    print(f"Created: {output_dir / 'tray.png'}")

    print("\nIcon generation complete!")


if __name__ == "__main__":
    main()
