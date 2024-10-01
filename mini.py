from PIL import Image, ImageOps
import os
import string

# Constants
GRID_SIZE = 12  # 21x21 grid (QR code v1)
ANCHOR_SIZE = 3  # 3x3 anchor blocks in the corners
SMALL_ANCHOR_SIZE = 3  # 3x3 smaller bottom-right anchor
TOLERANCE = 16  # Using 5 digits in hex color, leaving the last as tolerance
CHARS = string.ascii_lowercase + ' '  # Lowercase letters plus space (27 characters)

# Ensure the output directory exists
output_dir = './output'
os.makedirs(output_dir, exist_ok=True)

# Mapping for Single, Double, Triple, Quad Letter Combinations
def generate_color_mapping():
    mapping = {}
    color_counter = 0

    # Single letter mappings (include all lowercase + space)
    for char in CHARS:
        hex_color = f'{color_counter:05X}'  # Use 5 hex digits, leaving last as tolerance
        mapping[char] = '#' + hex_color + '0'  # Append 0 for tolerance
        color_counter += 1

    # Double letter mappings (lowercase letters + space)
    for char1 in CHARS:
        for char2 in CHARS:
            hex_color = f'{color_counter:05X}'
            mapping[char1 + char2] = '#' + hex_color + '0'
            color_counter += 1

    # Triple letter mappings (lowercase letters + space)
    for char1 in CHARS:
        for char2 in CHARS:
            for char3 in CHARS:
                hex_color = f'{color_counter:05X}'
                mapping[char1 + char2 + char3] = '#' + hex_color + '0'
                color_counter += 1

    # Quad letter mappings (lowercase letters + space)
    for char1 in CHARS:
        for char2 in CHARS:
            for char3 in CHARS:
                for char4 in CHARS:
                    hex_color = f'{color_counter:05X}'
                    mapping[char1 + char2 + char3 + char4] = '#' + hex_color + '0'
                    color_counter += 1

    return mapping

# Create an empty grid with white background
def create_empty_grid():
    return [['#FFFFFF' for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]

# Place anchor blocks in the grid (reuse for color mappings)
def place_anchors(grid):
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

    # Bottom-right small anchor (3x3)
    for i in range(GRID_SIZE - SMALL_ANCHOR_SIZE, GRID_SIZE):
        for j in range(GRID_SIZE - SMALL_ANCHOR_SIZE, GRID_SIZE):
            grid[i][j] = anchor_colors[(i + j) % len(anchor_colors)]

    return grid

# Function to check if a cell is within the anchor block areas
def is_anchor_area(row, col):
    # Top-left anchor
    if row < ANCHOR_SIZE and col < ANCHOR_SIZE:
        return True
    # Top-right anchor
    if row < ANCHOR_SIZE and col >= GRID_SIZE - ANCHOR_SIZE:
        return True
    # Bottom-left anchor
    if row >= GRID_SIZE - ANCHOR_SIZE and col < ANCHOR_SIZE:
        return True
    # Bottom-right small anchor
    if row >= GRID_SIZE - SMALL_ANCHOR_SIZE and col >= GRID_SIZE - SMALL_ANCHOR_SIZE:
        return True
    return False

# Snake-like pattern for filling grid while avoiding anchor areas
def encode_text(text, color_mapping):
    grid = create_empty_grid()
    grid = place_anchors(grid)

    # Start from the top-right corner of the bottom-right anchor
    row, col = GRID_SIZE - SMALL_ANCHOR_SIZE - 1, GRID_SIZE - 1
    direction = -1  # Start moving upward (-1 = up, 1 = down)
    i = 0  # Text index

    while i < len(text):
        # Skip anchor areas
        if is_anchor_area(row, col):
            col -= 1
            continue

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

        # Place color in the grid
        grid[row][col] = color

        # Move to the next position based on the snake pattern
        row += direction
        if row < 0 or row >= GRID_SIZE:  # If we hit the top or bottom, switch direction
            row -= direction  # Step back to stay in bounds
            col -= 1  # Move left
            direction *= -1  # Change vertical direction

    return grid

# Convert the grid into an image and save it
def grid_to_image(grid, filename):
    img = Image.new('RGB', (GRID_SIZE, GRID_SIZE), color="white")
    pixels = img.load()
    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
            pixels[col, row] = tuple(int(grid[row][col][i:i+2], 16) for i in (1, 3, 5))  # Convert hex to RGB
    img.save(f'{output_dir}/{filename}')  # Save the image in output directory
    return img

# Decode the image and extract the text
def decode_image(image_path, color_mapping):
    img = Image.open(image_path)
    img = ImageOps.exif_transpose(img)  # Handle orientation issues
    img = img.resize((GRID_SIZE, GRID_SIZE))  # Resize to match our grid

    pixels = img.load()
    inverse_mapping = {v: k for k, v in color_mapping.items()}  # Invert the color mapping for decoding

    decoded_text = ""
    row, col = GRID_SIZE - SMALL_ANCHOR_SIZE - 1, GRID_SIZE - 1  # Start decoding from the top-right corner of the bottom-right anchor
    direction = -1  # Start moving upward (-1 = up, 1 = down)

    while col >= 0:
        # Skip anchor areas
        if is_anchor_area(row, col):
            col -= 1
            continue

        # Read the color
        color = '#{:02X}{:02X}{:02X}'.format(*pixels[col, row][:3])  # Convert RGB to hex
        color = color[:-1] + '0'  # Normalize with tolerance

        # Decode the color back to the corresponding text
        decoded_text += inverse_mapping.get(color, '')

        # Move to the next position in snake pattern
        row += direction
        if row < 0 or row >= GRID_SIZE:
            row -= direction  # Stay in bounds
            col -= 1  # Move left
            direction *= -1  # Change vertical direction

    return decoded_text

# Example usage for encoding and decoding
if __name__ == "__main__":
    color_mapping = generate_color_mapping()

    # Example text to encode
    text = "hello world this is a test of the mini model. it has almost instant generation, and is great for compressing text. that is the main and only real functioanlity, as it is for rapid text receival"
    
    # Encode and save the image
    encoded_grid = encode_text(text, color_mapping)
    image = grid_to_image(encoded_grid, "encoded_qr_snake.png")
    print(f"Encoded QR code saved to {output_dir}/encoded_qr_snake.png")
    
    # Decode the image and print the decoded text
    decoded_text = decode_image(f'{output_dir}/encoded_qr_snake.png', color_mapping)
    print(f"Decoded text: {decoded_text}")
