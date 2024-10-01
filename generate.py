import os
import string
import itertools
import math
from PIL import Image

# Constants
MIN_GRID_SIZE = 6  # Minimum grid size (6x6)
ANCHOR_SIZE = 3  # 3x3 anchor blocks in the corners
CHARS = string.ascii_lowercase + ' '  # Lowercase letters plus space (27 characters)

# Ensure the output directory exists
output_dir = './output'
os.makedirs(output_dir, exist_ok=True)

# Optimized Mapping for Single, Double, Triple, Quad, and Quint Letter Combinations
def generate_color_mapping():
    mapping = {}
    color_counter = 0
    max_colors = 0xFFFFFF  # Maximum number of colors in 24-bit RGB

    def add_combination(combo):
        nonlocal color_counter
        if color_counter <= max_colors:
            mapping[combo] = f'#{color_counter:06X}'
            color_counter += 1
        return color_counter <= max_colors

    # Generate combinations efficiently
    for length in range(1, 6):
        for combo in itertools.product(CHARS, repeat=length):
            if not add_combination(''.join(combo)):
                return mapping

    return mapping

# Calculate the required grid size based on message length
def calculate_grid_size(message_length):
    for size in range(MIN_GRID_SIZE, 100, 2):  # Start from MIN_GRID_SIZE and only consider odd sizes
        available_pixels = size * size - 3 * ANCHOR_SIZE * ANCHOR_SIZE
        if available_pixels >= message_length:
            return size
    return 101  # If we somehow need an enormous grid

# Create an empty grid with white background
def create_empty_grid(size):
    return [['#FFFFFF' for _ in range(size)] for _ in range(size)]

# Place anchor blocks in the grid
def place_anchors(grid):
    size = len(grid)
    anchor_colors = ['#000000', '#FF0000', '#00FF00']
    for start_row, start_col in [(0, 0), (0, size - ANCHOR_SIZE), (size - ANCHOR_SIZE, 0)]:
        for i in range(ANCHOR_SIZE):
            for j in range(ANCHOR_SIZE):
                grid[start_row + i][start_col + j] = anchor_colors[(i + j) % len(anchor_colors)]
    return grid

# Function to check if a cell is within the anchor block areas
def is_anchor_area(row, col, size):
    return any([
        row < ANCHOR_SIZE and col < ANCHOR_SIZE,
        row < ANCHOR_SIZE and col >= size - ANCHOR_SIZE,
        row >= size - ANCHOR_SIZE and col < ANCHOR_SIZE
    ])

# Snake-like pattern for filling grid while avoiding anchor areas
def encode_text(text, color_mapping):
    grid_size = calculate_grid_size(len(text))
    grid = place_anchors(create_empty_grid(grid_size))
    row, col = grid_size - 1, grid_size - 1
    direction = -1
    i = 0

    while i < len(text):
        if is_anchor_area(row, col, grid_size):
            if col == ANCHOR_SIZE - 1:  # If we've reached the left side
                row = grid_size - ANCHOR_SIZE - 1  # Move to just above the bottom left anchor
                col = 0  # Start from the left edge
                direction = 1  # Change direction to up
            else:
                col -= 1
            continue

        for length in range(5, 0, -1):
            if i + length <= len(text) and text[i:i+length] in color_mapping:
                grid[row][col] = color_mapping[text[i:i+length]]
                i += length
                break
        else:
            grid[row][col] = '#FFFFFF'
            i += 1

        row += direction
        if row < ANCHOR_SIZE or row >= grid_size - ANCHOR_SIZE:
            row -= direction  # Step back
            col -= 1  # Move left
            direction *= -1  # Change direction

        if col < 0:  # If we've filled the entire left side
            break

    return grid

# Convert the grid into an image and save it
def grid_to_image(grid, filename):
    size = len(grid)
    img = Image.new('RGB', (size, size), color="white")
    pixels = img.load()
    for row in range(size):
        for col in range(size):
            pixels[col, row] = tuple(int(grid[row][col][i:i+2], 16) for i in (1, 3, 5))
    img.save(f'{output_dir}/{filename}')
    return img

# Decode the image and extract the text
def decode_image(image_path, color_mapping):
    img = Image.open(image_path)
    size = img.size[0]  # Assuming square image
    pixels = img.load()
    inverse_mapping = {v: k for k, v in color_mapping.items()}
    decoded_text = ""
    row, col = size - 1, size - 1
    direction = -1

    while col >= 0:
        if is_anchor_area(row, col, size):
            if col == ANCHOR_SIZE - 1:  # If we've reached the left side
                row = size - ANCHOR_SIZE - 1  # Move to just above the bottom left anchor
                col = 0  # Start from the left edge
                direction = 1  # Change direction to up
            else:
                col -= 1
            continue

        color = '#{:02X}{:02X}{:02X}'.format(*pixels[col, row][:3])
        decoded_text += inverse_mapping.get(color, '')

        row += direction
        if row < ANCHOR_SIZE or row >= size - ANCHOR_SIZE:
            row -= direction  # Step back
            col -= 1  # Move left
            direction *= -1  # Change direction

        if col < 0:  # If we've filled the entire left side
            break

    return decoded_text

# Example usage
if __name__ == "__main__":
    color_mapping = generate_color_mapping()
    print(f"Generated {len(color_mapping)} unique color mappings")

    text = "hello world this is a test"
    encoded_grid = encode_text(text, color_mapping)
    grid_size = len(encoded_grid)
    print(f"Generated grid size: {grid_size}x{grid_size}")

    image = grid_to_image(encoded_grid, "encoded_adaptive_qr.png")
    print(f"Encoded adaptive QR code saved to {output_dir}/encoded_adaptive_qr.png")
    
    decoded_text = decode_image(f'{output_dir}/encoded_adaptive_qr.png', color_mapping)
    print(f"Decoded text: {decoded_text}")

    # Test with a very short message
    short_text = "hi"
    short_encoded_grid = encode_text(short_text, color_mapping)
    short_grid_size = len(short_encoded_grid)
    print(f"\nShort message grid size: {short_grid_size}x{short_grid_size}")

    short_image = grid_to_image(short_encoded_grid, "encoded_short_qr.png")
    print(f"Encoded short QR code saved to {output_dir}/encoded_short_qr.png")

    short_decoded_text = decode_image(f'{output_dir}/encoded_short_qr.png', color_mapping)
    print(f"Decoded short text: {short_decoded_text}")