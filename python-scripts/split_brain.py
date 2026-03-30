"""
Split the brain PNG into 3 clickable regions using POLYGON masks
that follow the organic contours from the user's reference image.

Regions:
  - Top (red contour)   → Automação eSocial
  - Bottom-left (green) → Arquivos, Folhas e Tabelas
  - Bottom-right (yellow) → Rubricas

The division lines follow the brain's natural sulci:
  - Horizontal: lateral sulcus (separates top from bottom halves)
  - Vertical: longitudinal fissure (separates left from right in bottom half)

Each output image has the same dimensions as the original (1536×1024).
Non-region pixels are fully transparent, so when stacked they reform the original.
"""
from PIL import Image, ImageDraw, ImageChops, ImageFilter
import numpy as np
import os

src = os.path.join(os.path.dirname(__file__), '..', 'docs', 'image.png')
dst_dir = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'public')

img = Image.open(src).convert('RGBA')
w, h = img.size
print(f"Brain image size: {w}x{h}")

# ─── REMOVE BACKGROUND ─────────────────────────────────────────────────
# The original image has a white/light gray background (not transparent).
# Remove it by making light-colored pixels transparent.
arr = np.array(img)
r, g, b, a = arr[:,:,0], arr[:,:,1], arr[:,:,2], arr[:,:,3]

# Background pixels are very light (R,G,B all > 200) and grayish
# The brain itself is dark navy/blue, so we can threshold
is_background = (r > 200) & (g > 200) & (b > 200)

# Also catch the light gray shadow/gradient around the brain
# by checking if the pixel is close to white
brightness = r.astype(int) + g.astype(int) + b.astype(int)
is_light = brightness > 600  # > 200 average per channel

# Combine: if it's light/white, make transparent
background_mask = is_background | is_light
arr[background_mask, 3] = 0

# Smooth the edges: for pixels near the boundary, apply gradual alpha
# to avoid hard edges
# Smooth the edges: for pixels near the boundary, apply gradual alpha
# to avoid hard edges
try:
    from scipy import ndimage
    brain_mask = ~background_mask
    dist = ndimage.distance_transform_edt(brain_mask)
    edge_zone = (dist > 0) & (dist < 3)
    edge_alpha = np.clip(dist[edge_zone] / 3 * 255, 0, 255).astype(np.uint8)
    arr[edge_zone, 3] = np.minimum(arr[edge_zone, 3], edge_alpha)
    print("Applied edge smoothing with scipy")
except ImportError:
    print("scipy not available, skipping edge smoothing")

img = Image.fromarray(arr)
transparent_count = (arr[:,:,3] == 0).sum()
total_pixels = w * h
print(f"Made {transparent_count}/{total_pixels} pixels transparent ({100*transparent_count/total_pixels:.1f}%)")
img.save(os.path.join(dst_dir, 'brain-full.png'))

# ─── POLYGON DEFINITIONS ───────────────────────────────────────────────
# Based on the user's reference image with colored contours.
# The brain is 1536x1024. The division follows organic curves.
#
# Key anatomical landmarks in the image:
#   - Brain top center: ~(768, 45)
#   - Brain bottom center: ~(768, 940)
#   - Left edge: ~(135, 500)
#   - Right edge: ~(1400, 500)
#   - Longitudinal fissure (center line from top to bottom): x ≈ 768
#   - Lateral sulcus level: y ≈ 490-540 (varies left to right)
#
# The horizontal boundary (between top and bottom regions) follows a gentle
# curve based on the red/green/yellow outlines in the reference:
#   - Dips lower on the left (~y=530), rises at center (~y=470), dips on right (~y=500)
#
# The vertical boundary (between bottom-left and bottom-right) follows the
# longitudinal fissure — approximately x=768 but with a slight organic wobble.

# Horizontal dividing line (from left edge to right edge)
# This is the boundary between TOP region and BOTTOM regions.
# Points go left-to-right.
horizontal_boundary = [
    (0, 530),        # far left (off-brain, extended to edge)
    (135, 530),      # left brain edge
    (200, 525),      # left outer lobe
    (280, 510),      # approaching lateral sulcus
    (380, 490),      # left mid
    (480, 475),      # left of center
    (580, 465),      # approaching center
    (680, 458),      # near center-left
    (768, 455),      # center (highest point of curve)
    (850, 458),      # near center-right
    (940, 470),      # right of center
    (1040, 480),     # right mid
    (1140, 490),     # right lobe area
    (1240, 500),     # right outer
    (1350, 510),     # right brain edge
    (1400, 515),     # right edge
    (1536, 515),     # far right (extended)
]

# Vertical dividing line (from horizontal boundary down to bottom)
# This separates bottom-left from bottom-right.
# Points go top-to-bottom following the longitudinal fissure.
vertical_boundary = [
    (768, 455),      # starts at center of horizontal boundary
    (766, 500),      # slight wobble left
    (764, 550),      # continuing down
    (762, 600),      # mid-lower
    (760, 650),      # approaching bottom
    (758, 700),      # lower
    (756, 750),      # near bottom
    (755, 800),      # very bottom area
    (754, 850),      # approaching base
    (753, 900),      # base area
    (752, 940),      # bottom of brain
    (750, 1024),     # extended to bottom edge
]

# ─── BUILD POLYGONS ─────────────────────────────────────────────────────

# TOP region polygon: everything above the horizontal boundary
# Goes: top-left → top-right → along horizontal boundary right-to-left → close
poly_top = (
    [(0, 0), (w, 0)]  # top edge
    + list(reversed(horizontal_boundary))  # horizontal boundary right-to-left
)

# BOTTOM-LEFT polygon: below horizontal boundary, left of vertical boundary
# Goes: horizontal boundary left-to-center → vertical boundary top-to-bottom →
#        bottom-left corner → left edge → close
poly_bl = (
    [pt for pt in horizontal_boundary if pt[0] <= 768]  # horizontal boundary left half
    + vertical_boundary  # down the center
    + [(0, h)]  # bottom-left corner
)

# BOTTOM-RIGHT polygon: below horizontal boundary, right of vertical boundary
# Goes: vertical boundary bottom-to-top → horizontal boundary center-to-right →
#        right edge bottom → close
poly_br = (
    list(reversed(vertical_boundary))  # vertical boundary bottom-to-top
    + [pt for pt in horizontal_boundary if pt[0] >= 768]  # horizontal boundary right half
    + [(w, h)]  # bottom-right corner
)


def apply_polygon_mask(image, polygon):
    """Create a version of the image with only the polygon region visible."""
    mask = Image.new('L', (w, h), 0)
    draw = ImageDraw.Draw(mask)
    draw.polygon(polygon, fill=255)

    result = image.copy()
    r, g, b, a = result.split()
    masked_alpha = ImageChops.multiply(a, mask)
    result.putalpha(masked_alpha)
    return result


# Generate the 3 pieces
top = apply_polygon_mask(img, poly_top)
bottom_left = apply_polygon_mask(img, poly_bl)
bottom_right = apply_polygon_mask(img, poly_br)

# Save
top.save(os.path.join(dst_dir, 'brain-top.png'))
bottom_left.save(os.path.join(dst_dir, 'brain-bottom-left.png'))
bottom_right.save(os.path.join(dst_dir, 'brain-bottom-right.png'))
img.save(os.path.join(dst_dir, 'brain-full.png'))

print("Saved: brain-top.png, brain-bottom-left.png, brain-bottom-right.png, brain-full.png")
print(f"All images are {w}x{h} pixels")

# Verification: reassemble and compare
reassembled = Image.new('RGBA', (w, h), (0, 0, 0, 0))
reassembled = Image.alpha_composite(reassembled, bottom_left)
reassembled = Image.alpha_composite(reassembled, bottom_right)
reassembled = Image.alpha_composite(reassembled, top)

# Check pixel-perfect match
import numpy as np
orig_arr = np.array(img)
reasm_arr = np.array(reassembled)
diff = np.abs(orig_arr.astype(int) - reasm_arr.astype(int))
max_diff = diff.max()
mean_diff = diff.mean()
mismatched = (diff > 0).any(axis=2).sum()
total_pixels = w * h
print(f"\nVerification:")
print(f"  Max pixel diff: {max_diff}")
print(f"  Mean pixel diff: {mean_diff:.4f}")
print(f"  Mismatched pixels: {mismatched}/{total_pixels} ({100*mismatched/total_pixels:.2f}%)")
if max_diff == 0:
    print("  ✅ PERFECT MATCH — reassembled image is identical to original!")
else:
    print("  ⚠️  Some differences detected — check boundary regions")
