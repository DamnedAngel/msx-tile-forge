from PIL import Image
import struct
import sys

# tiles
def convert_palette_to_rgb(palette):
    rgb_palette = {}
    for index, (r, g, b) in palette.items():
        # Scale each component from 0-7 to 0-255
        scaled_r = round((r / 7) * 255)
        scaled_g = round((g / 7) * 255)
        scaled_b = round((b / 7) * 255)
        rgb_palette[index] = (scaled_r, scaled_g, scaled_b)
    return rgb_palette

def decode_tile_to_image(tile_data, tile_color_data, palette, tile_index):
    # Extract the 8 bytes representing the tile's pixel data
    tile_bytes = tile_data[tile_index]
    # Extract the color info (high nibble = color for bit=1, low nibble = color for bit=0)

    # Create an 8x8 RGB image
    img = Image.new("RGB", (8, 8))
    pixels = img.load()

    for y in range(8):
        byte = tile_bytes[y]
        color_info = tile_color_data[tile_index][y]
        color_bit1 = (color_info >> 4) & 0xF  # High 4 bits
        color_bit0 = color_info & 0xF         # Low 4 bits
        for x in range(8):
            # Check if the bit is set (left-to-right: MSB to LSB)
            bit = (byte >> (7 - x)) & 1
            # Get the color index based on the bit
            color_index = color_bit1 if bit else color_bit0
            # Get the RGB value from the palette
            r, g, b = palette.get(color_index, (0, 0, 0))  # Default to black if not found
            pixels[x, y] = (r, g, b)

    return img

def create_tilemap_image(tile_data, tile_color_data, palette):
    """Combine all tiles into a 256x256 image (16x16 tiles)."""
    # Convert palette to 0-255 RGB
    rgb_palette = convert_palette_to_rgb(palette)

    # Create a blank 256x256 image
    tilemap = Image.new("RGB", (256, 256))
    
    # Process each tile and paste it into the correct position
    for tile_index in range(256):
        if tile_index not in tile_data or tile_index not in tile_color_data:
            continue  # Skip missing tiles (or fill with a default color)
        
        tile_img = decode_tile_to_image(tile_data, tile_color_data, rgb_palette, tile_index)
        
        # Calculate position (16 tiles per row)
        x = (tile_index % 16) * 8
        y = (tile_index // 16) * 8
        
        # Paste the tile into the tilemap
        tilemap.paste(tile_img, (x, y))
    
    # Save and return the tilemap
    #tilemap.save(output_path)
    return tilemap

def render_supertile_to_image(supertile, tile_data, tile_color_data, rgb_palette):
    """
    Renders a single supertile (n x m tile matrix) into a PIL Image.
    
    Args:
        supertile (list): 2D list of tile indices
        tile_data (dict): Tile definitions (index -> 8 bytes)
        tile_color_data (dict): Tile color info (index -> byte)
        rgb_palette (dict): Color palette in 0-255 RGB format
    
    Returns:
        PIL.Image: Rendered supertile image
    """
    n_rows = len(supertile)
    n_cols = len(supertile[0]) if n_rows > 0 else 0
    
    # Create blank image for this supertile
    supertile_img = Image.new("RGB", (n_cols * 8, n_rows * 8))
    
    for tile_row_idx, tile_row in enumerate(supertile):
        for tile_col_idx, tile_index in enumerate(tile_row):
            if tile_index in tile_data and tile_index in tile_color_data:
                tile_img = decode_tile_to_image(
                    tile_data, 
                    tile_color_data, 
                    rgb_palette, 
                    tile_index
                )
                supertile_img.paste(tile_img, (tile_col_idx * 8, tile_row_idx * 8))
    
    return supertile_img

def render_supertiles(supertiles_dict, tile_data, tile_color_data, palette, supertile_width=8):
    """
    Renders all supertiles into a single PIL.Image using render_supertile_to_image.
    
    Args:
        supertiles_dict (dict): Dictionary of supertiles (key: supertile ID, value: n x m matrix)
        tile_data (dict): Dictionary mapping tile indices to their 8-byte data
        tile_color_data (dict): Dictionary mapping tile indices to their color info
        palette (dict): Color palette mapping indices to RGB tuples
        supertile_width (int): Number of supertiles per row in the output image
    
    Returns:
        PIL.Image: Composite image of all supertiles
    """
    # Convert palette to 0-255 RGB
    rgb_palette = convert_palette_to_rgb(palette)
    
    # Get dimensions from first supertile
    sample_supertile = next(iter(supertiles_dict.values()))
    n_rows = len(sample_supertile)
    n_cols = len(sample_supertile[0]) if n_rows > 0 else 0
    
    # Calculate layout
    num_supertiles = len(supertiles_dict)
    supertile_rows = (num_supertiles - 1) // supertile_width + 1
    
    # Create output image
    output_img = Image.new(
        "RGB", 
        (supertile_width * n_cols * 8, supertile_rows * n_rows * 8)
    )
    
    # Render and position each supertile
    for supertile_idx, supertile in enumerate(supertiles_dict.values()):
        row = supertile_idx // supertile_width
        col = supertile_idx % supertile_width
        
        supertile_img = render_supertile_to_image(
            supertile,
            tile_data,
            tile_color_data,
            rgb_palette
        )
        
        output_img.paste(
            supertile_img,
            (col * n_cols * 8, row * n_rows * 8)
        )
    
    return output_img


def parse_map_file(map_file):
    """
    Parses a binary map file with the following format:
    - First 2 bytes: map width in supertiles (big-endian unsigned short)
    - Next 2 bytes: map height in supertiles (big-endian unsigned short)
    - Next 4 bytes: unknown/unused data
    - Remaining bytes: supertile map data (1 byte per supertile, row-major order)
    
    Returns:
        tuple: (width, height, supertile_map)
        where supertile_map is a 2D list [row][column] of supertile indices
    """
    with open(map_file, 'rb') as f:
        # Read width and height (first 4 bytes)
        width, height = struct.unpack('<HH', f.read(4))
        
        # Skip next 4 unknown bytes
        f.read(4)
        
        # Read supertile map data
        map_data = f.read()
        
        # Convert to 2D array (row-major order)
        supertile_map = []
        for row in range(height):
            start = row * width
            end = start + width
            supertile_map.append(list(map_data[start:end]))
            
    return width, height, supertile_map


def map_to_image(map_file, super_data, tile_data, tile_color_data, palette):
    """
    Converts a binary map file into a PIL Image using supertiles.
    
    Args:
        map_file (str): Path to the binary map file
        tile_data (dict): Tile definitions (index -> 8 bytes)
        tile_color_data (dict): Tile color info (index -> byte)
        palette (dict): Color palette (index -> (r,g,b))
    
    Returns:
        PIL.Image: Rendered map image
    
    Example:
        >>> map_img = map_to_image("level1.map", tile_data, tile_color_data, palette)
        >>> map_img.save("map.png")
    """
    # 1. Parse the map file
    map_width, map_height, supertile_indices = parse_map_file(map_file)

    # get supertile size
    sample_supertile = next(iter(super_data.values()))
    n_rows = len(sample_supertile)
    n_cols = len(sample_supertile[0]) if n_rows > 0 else 0
    
    # 2. Convert palette to 0-255 RGB
    rgb_palette = convert_palette_to_rgb(palette)
    
    # 3. Create output image (8 pixels per tile)
    output_img = Image.new( "RGB", (map_width * n_cols *  8, map_height * n_rows * 8 ) )
    
    # 4. Render each supertile row
    for row in range(map_height):
        for col in range(map_width):
            supertile_idx = supertile_indices[row][col]
            
            # Create a 1x1 "supertile" (since map uses direct tile indices)
            single_supertile = super_data[supertile_idx]
            
            # Render just this tile
            tile_img = render_supertile_to_image(
                single_supertile,
                tile_data,
                tile_color_data,
                rgb_palette
            )
            
            # Paste at correct position
            output_img.paste(tile_img, (col * n_cols * 8, row * n_rows * 8 ) )
    
    return output_img


#
#
#
def main( project_name ):
    #project_name = "track2"
    palette_file  = f'{project_name}.SC4Pal'
    tiles_file    = f'{project_name}.SC4Tiles'
    super_file    = f'{project_name}.SC4Super'
    map_file      = f'{project_name}.SC4Map'
    
    
    # le a paleta de cores
    with open( palette_file, 'rb' ) as f:
        palette_data = f.read()
    # 4 primeiros bytes = ?
    palette = {}
    for c in range( 0, 16 ):
        i = 4 + c * 3
        palette[c] = ( palette_data[i],palette_data[i+1],palette_data[i+2] )
    
    # le tiles
    with open( tiles_file, 'rb' ) as f:
        tile_data = f.read()
    tile_qty = tile_data[0]
    # próximos 4 bytes = ??
    
    tile = {}
    tile_color = {}
    for t in range( tile_qty ):
        i = 5 + t * 8
        tile[ t ] = []
        for j in range( i, i + 8 ):
            tile[ t ].append( tile_data[ j ] )
    
        i = 5 + ( t + tile_qty ) * 8
        tile_color[ t ] = []
        for j in range( i, i + 8 ):
            tile_color[ t ].append( tile_data[ j ] )
    
    rgb_palette = convert_palette_to_rgb( palette )
    
    decode_tile_to_image( tile, tile_color, rgb_palette, 0 )
    
    create_tilemap_image( tile, tile_color, palette )
    
    # supertile
    
    with open( super_file, 'rb' ) as f:
        super_data = f.read()
    ( super_qty, super_size_x, super_size_y ) = super_data[0:3]
    super_qty, super_size_x, super_size_y
    #próximos 2 bytes = ??
    
    # 4 primeiros bytes = ?
    super = {}
    size_in_bytes = super_size_x * super_size_y
    for s in range( super_qty ):
        i = 7 + s * size_in_bytes
        super[ s ] = [ list( super_data[j:j+super_size_x] ) for j in range( i, i+size_in_bytes, super_size_x ) ]
    
    
    
    return map_to_image( map_file, super, tile, tile_color, palette )

if __name__ == '__main__':
    if len( sys.argv ) != 2:
        print( f"Use: {sys.argv[0]} <nome do projeto>" )
        exit(0)
    else:
        project_name = sys.argv[1]
        map = main( project_name )
        image_filename = f'{project_name}.png'
        map.save( image_filename )