"""
Extract the outline contour from the brand logo PNG and output an SVG path.
Uses OpenCV to find contours from the alpha channel of the transparent PNG.
"""
import cv2
import numpy as np
import json

# Load image with alpha channel
img = cv2.imread(
    r"c:\Users\xandao\Documents\GitHub\Easy-Social\backend\src\ChatGPT_Image_26_de_mar._de_2026__22_06_02-removebg-preview.png",
    cv2.IMREAD_UNCHANGED
)

print(f"Image shape: {img.shape}")
h, w = img.shape[:2]

# Extract alpha channel
if img.shape[2] == 4:
    alpha = img[:, :, 3]
else:
    # Convert to grayscale if no alpha
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, alpha = cv2.threshold(gray, 10, 255, cv2.THRESH_BINARY)

# Threshold alpha to get binary mask
_, mask = cv2.threshold(alpha, 30, 255, cv2.THRESH_BINARY)

# Optional: smooth the mask slightly to reduce noise
mask = cv2.GaussianBlur(mask, (3, 3), 0)
_, mask = cv2.threshold(mask, 128, 255, cv2.THRESH_BINARY)

# Find contours
contours, hierarchy = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_TC89_L1)

print(f"Found {len(contours)} contours")
for i, c in enumerate(contours):
    print(f"  Contour {i}: {len(c)} points, area={cv2.contourArea(c):.0f}")

# Get only significant contours (filter tiny noise)
significant = [c for c in contours if cv2.contourArea(c) > 500]
print(f"Significant contours (area>500): {len(significant)}")

# We want to normalize to a viewBox. Let's use the image dimensions.
# Target viewBox: 0 0 {w} {h}  (original pixel coords)

def contour_to_svg_path(contour, simplify_epsilon=1.5):
    """Convert an OpenCV contour to an SVG path string."""
    # Simplify the contour
    approx = cv2.approxPolyDP(contour, simplify_epsilon, True)
    points = approx.reshape(-1, 2)
    
    if len(points) < 3:
        return None, 0
    
    # Build SVG path
    parts = [f"M{points[0][0]},{points[0][1]}"]
    for p in points[1:]:
        parts.append(f"L{p[0]},{p[1]}")
    parts.append("Z")
    
    return " ".join(parts), len(points)

# Convert each significant contour to SVG path
paths = []
for i, c in enumerate(significant):
    # Try different simplification levels
    for eps in [2.0, 1.5, 1.0]:
        path_d, n_points = contour_to_svg_path(c, eps)
        if path_d and n_points >= 4:
            paths.append({"d": path_d, "points": n_points, "area": cv2.contourArea(c)})
            print(f"  Path {i}: {n_points} points (eps={eps}), area={cv2.contourArea(c):.0f}")
            break

# Calculate total path length for animation
total_length = 0
for c in significant:
    total_length += cv2.arcLength(c, True)
print(f"\nTotal contour perimeter: {total_length:.0f}px")

# Output SVG for testing
svg_content = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" fill="none">\n'
for p in paths:
    svg_content += f'  <path d="{p["d"]}" stroke="#0066FF" stroke-width="3" fill="none"/>\n'
svg_content += '</svg>'

# Save test SVG
with open(r"c:\Users\xandao\Documents\GitHub\Easy-Social\frontend\public\logo-contour.svg", "w") as f:
    f.write(svg_content)

# Also output the path data as JSON for use in Vue component
output = {
    "viewBox": f"0 0 {w} {h}",
    "width": w,
    "height": h,
    "totalLength": round(total_length),
    "paths": [{"d": p["d"], "points": p["points"]} for p in paths]
}

with open(r"c:\Users\xandao\Documents\GitHub\Easy-Social\python-scripts\contour_data.json", "w") as f:
    json.dump(output, f, indent=2)

print(f"\nSaved SVG to frontend/public/logo-contour.svg")
print(f"Saved JSON to python-scripts/contour_data.json")
print(f"\nPath data for Vue component:")
for p in paths:
    print(f'  d="{p["d"][:100]}..."' if len(p["d"]) > 100 else f'  d="{p["d"]}"')
