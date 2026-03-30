"""
Extract smooth contour from the brand logo PNG and output smooth SVG bezier path.
"""
import cv2
import numpy as np

# Load image with alpha
img = cv2.imread(
    r"c:\Users\xandao\Documents\GitHub\Easy-Social\backend\src\ChatGPT_Image_26_de_mar._de_2026__22_06_02-removebg-preview.png",
    cv2.IMREAD_UNCHANGED
)

h, w = img.shape[:2]
alpha = img[:, :, 3]

# Binary mask
_, mask = cv2.threshold(alpha, 30, 255, cv2.THRESH_BINARY)
mask = cv2.GaussianBlur(mask, (5, 5), 0)
_, mask = cv2.threshold(mask, 128, 255, cv2.THRESH_BINARY)

# Find contours - use more points for smoothness
contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_TC89_L1)
significant = [c for c in contours if cv2.contourArea(c) > 500]

print(f"Image: {w}x{h}")
print(f"Contours: {len(significant)}")

def smooth_contour_to_bezier(contour, epsilon=3.0):
    """Convert contour to smooth cubic Bézier SVG path using Catmull-Rom → Cubic Bézier."""
    approx = cv2.approxPolyDP(contour, epsilon, True)
    pts = approx.reshape(-1, 2).tolist()
    n = len(pts)
    
    if n < 3:
        return None
    
    # Catmull-Rom to Cubic Bézier conversion
    # For each segment between pts[i] and pts[i+1], we need pts[i-1] and pts[i+2]
    def catmull_to_cubic(p0, p1, p2, p3, tension=0.5):
        """Convert Catmull-Rom segment to Cubic Bézier control points."""
        t = tension
        cp1x = p1[0] + (p2[0] - p0[0]) / (6 * t)
        cp1y = p1[1] + (p2[1] - p0[1]) / (6 * t)
        cp2x = p2[0] - (p3[0] - p1[0]) / (6 * t)
        cp2y = p2[1] - (p3[1] - p1[1]) / (6 * t)
        return (round(cp1x), round(cp1y)), (round(cp2x), round(cp2y))
    
    # Start path
    parts = [f"M{pts[0][0]},{pts[0][1]}"]
    
    for i in range(n):
        p0 = pts[(i - 1) % n]
        p1 = pts[i]
        p2 = pts[(i + 1) % n]
        p3 = pts[(i + 2) % n]
        
        cp1, cp2 = catmull_to_cubic(p0, p1, p2, p3)
        parts.append(f"C{cp1[0]},{cp1[1]} {cp2[0]},{cp2[1]} {p2[0]},{p2[1]}")
    
    parts.append("Z")
    return " ".join(parts)

# Generate smooth path
for eps in [2.5, 2.0, 1.5]:
    path_d = smooth_contour_to_bezier(significant[0], eps)
    if path_d:
        # Count points
        n_curves = path_d.count("C")
        path_length = cv2.arcLength(significant[0], True)
        print(f"eps={eps}: {n_curves} curves, length≈{path_length:.0f}px")

# Use eps=2.0 for good balance
path_d = smooth_contour_to_bezier(significant[0], 2.0)
n_curves = path_d.count("C")
print(f"\nFinal: {n_curves} curves")

# Save smooth SVG
svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" fill="none">\n'
svg += f'  <path d="{path_d}" stroke="#0066FF" stroke-width="3" fill="none"/>\n'
svg += '</svg>'

with open(r"c:\Users\xandao\Documents\GitHub\Easy-Social\frontend\public\logo-contour.svg", "w") as f:
    f.write(svg)

# Print path for use in Vue component
print(f'\nviewBox="0 0 {w} {h}"')
print(f'path d="{path_d}"')
print(f'\nPath length (for animation): ~{cv2.arcLength(significant[0], True):.0f}px')
