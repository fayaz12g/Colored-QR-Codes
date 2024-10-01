from PIL import Image
import string

# Constants
GRID_SIZE = 21  # 21x21 grid (QR code v1)
ANCHOR_SIZE = 3  # 3x3 anchor blocks in the corners
TOLERANCE = 16  # Using 5 digits in hex color, leaving the last as tolerance
ASCII_CHARS = string.ascii_letters + string.digits + string.punctuation + ' '

# Mapping for Single, Double, Triple, Quad Letter Combinations
def generate_color_mapping():
    mapping = {}
    color_counter = 0

    # Single letter mappings (include all ASCII)
    for char in ASCII_CHARS:
        hex_color = f'{color_counter:05X}'  # Use 5 hex digits, leaving last as tolerance
        mapping[char] = '#' + hex_color + '0'  # Append 0 for tolerance
        color_counter += 1

    # Double letter mappings (lowercase letters only)
    for char1 in string.ascii_lowercase:
        for char2 in string.ascii_lowercase:
            hex_color = f'{color_counter:05X}'
            mapping[char1 + char2] = '#' + hex_color + '0'
            color_counter += 1

    # Triple letter mappings (lowercase letters only)
    for char1 in string.ascii_lowercase:
        for char2 in string.ascii_lowercase:
            for char3 in string.ascii_lowercase:
                hex_color = f'{color_counter:05X}'
                mapping[char1 + char2 + char3] = '#' + hex_color + '0'
                color_counter += 1

    # Quad letter mappings (lowercase letters only)
    for char1 in string.ascii_lowercase:
        for char2 in string.ascii_lowercase:
            for char3 in string.ascii_lowercase:
                for char4 in string.ascii_lowercase:
                    hex_color = f'{color_counter:05X}'
                    mapping[char1 + char2 + char3 + char4] = '#' + hex_color + '0'
                    color_counter += 1

    return mapping

# Create an empty grid with white background
def create_empty_grid():
    return [['#FFFFFF' for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]

# Place anchor blocks in the grid (reuse for color mappings)
def place_anchors(grid, color_mapping):
    # Top-left anchor (3x3)
    anchor_colors = ['#000000', '#FF0000', '#00FF00']  # Example calibration colors
    for i in range(ANCHOR_SIZE):
        for j in range(ANCHOR_SIZE):
            grid[i][j] = anchor_colors[(i + j) % len(anchor_colors)]  # Use for calibration

    # Top-right anchor (3x3)
    for i in range(ANCHOR_SIZE):
        for j in range(GRID_SIZE - ANCHOR_SIZE, GRID_SIZE):
            grid[i][j] = anchor_colors[(i + j) % len(anchor_colors)]

    # Bottom-left anchor (3x3)
    for i in range(GRID_SIZE - ANCHOR_SIZE, GRID_SIZE):
        for j in range(ANCHOR_SIZE):
            grid[i][j] = anchor_colors[(i + j) % len(anchor_colors)]

    return grid

# Encode the text data into the grid
def encode_text(text, color_mapping):
    grid = create_empty_grid()
    grid = place_anchors(grid, color_mapping)

    # Place data into grid (avoid anchor areas)
    row, col = ANCHOR_SIZE, ANCHOR_SIZE
    i = 0
    while i < len(text):
        # Try to encode 4-letter, 3-letter, 2-letter, or single letter
        if i + 3 < len(text) and text[i:i+4] in color_mapping:
            color = color_mapping[text[i:i+4]]
            i += 4
        elif i + 2 < len(text) and text[i:i+3] in color_mapping:
            color = color_mapping[text[i:i+3]]
            i += 3
        elif i + 1 < len(text) and text[i:i+2] in color_mapping:
            color = color_mapping[text[i:i+2]]
            i += 2
        else:
            color = color_mapping.get(text[i], '#FFFFFF')  # Default to white if unknown
            i += 1

        # Place color in the grid (skip over anchors)
        if row < GRID_SIZE and col < GRID_SIZE:
            grid[row][col] = color
            col += 1
            if col >= GRID_SIZE:
                row += 1
                col = 0
                if row in [0, GRID_SIZE - 1] or col in [0, GRID_SIZE - 1]:  # Skip anchor areas
                    col += ANCHOR_SIZE

    return grid

# Convert the grid into an image
def grid_to_image(grid):
    img = Image.new('RGB', (GRID_SIZE, GRID_SIZE), color="white")
    pixels = img.load()
    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
            pixels[col, row] = tuple(int(grid[row][col][i:i+2], 16) for i in (1, 3, 5))  # Convert hex to RGB
    return img

# Example usage
color_mapping = generate_color_mapping()
text = "hello world this is a test"
encoded_grid = encode_text(text, color_mapping)
image = grid_to_image(encoded_grid)
image.show()  # Display the image
