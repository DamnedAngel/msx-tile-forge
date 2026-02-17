#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# --- Version info ---
APP_VERSION = "<unreleased>"

import os
import sys
import struct
import math
import argparse

# --- Constants ---
MSXTILEFORGE_VERSION = APP_VERSION
EXPORTER_VERSION = APP_VERSION
RESERVED_BYTES_COUNT = 4
TILE_WIDTH = 8
TILE_HEIGHT = 8
MAX_TILES = 256
MAX_SUPERTILES = 65535

def print_splash_header(version, exporter_version):
    """
    Prints a visually distinct header for the MSX Tile Export CLI tool,
    with the logo on the left and text on the right.
    """
    # ANSI escape codes for standard and bright colors
    COLOR_BLUE_DARK = '\033[34m'
    COLOR_BLUE_BRIGHT = '\033[94m'
    COLOR_ORANGE_DARK = '\033[33m'
    COLOR_ORANGE_BRIGHT = '\033[93m'
    COLOR_TITLE = '\033[1;97m'
    COLOR_VERSION = '\033[97m'
    COLOR_RESET = '\033[0m'

    # Fallback to no color if the terminal doesn't support it
    if not sys.stdout.isatty():
        COLOR_BLUE_DARK = COLOR_BLUE_BRIGHT = COLOR_ORANGE_DARK = ""
        COLOR_ORANGE_BRIGHT = COLOR_TITLE = COLOR_VERSION = COLOR_RESET = ""

    # Define the building block for the logo using the Unicode code point
    block_char = "\u2588" * 2

    # Assign colors to each block type
    b_dark = f"{COLOR_BLUE_DARK}{block_char}{COLOR_RESET}"
    b_bright = f"{COLOR_BLUE_BRIGHT}{block_char}{COLOR_RESET}"
    o_dark = f"{COLOR_ORANGE_DARK}{block_char}{COLOR_RESET}"
    o_bright = f"{COLOR_ORANGE_BRIGHT}{block_char}{COLOR_RESET}"

    # Define the logo as a list of strings, with no leading whitespace
    logo_lines = [
        f"{b_dark}{b_bright}{b_bright}{b_dark}",
        f"{b_bright}{o_dark}{o_bright}{b_bright}",
        f"{b_bright}{o_bright}{o_dark}{b_bright}",
        f"{b_dark}{b_bright}{b_bright}{b_dark}"
    ]

    # Define the text lines that will go next to the logo
    text_lines = [
        f"{COLOR_TITLE}MSX Tile Export{COLOR_RESET} (v{exporter_version})",
        f"{COLOR_VERSION}MSX Tile Forge suite, version {version}{COLOR_RESET}"
    ]

    # Print the combined logo and text, line by line
    print() # Start with a blank line for spacing
    print(f"{logo_lines[0]}")
    print(f"{logo_lines[1]}  {text_lines[0]}")
    print(f"{logo_lines[2]}  {text_lines[1]}")
    print(f"{logo_lines[3]}")
    print("-" * 60)

class ProjectConverter:
    """
    Handles the loading of an MSX Tile Forge project from disk and exporting it
    to various raw formats.
    """
    def __init__(self):
        self.palette_data = []
        self.tileset_patterns = []
        self.tileset_colors = []
        self.supertiles_data = []
        self.map_data = b""
        self.map_data = []
        self.num_tiles_in_set = 0
        self.num_supertiles = 0
        self.supertile_grid_width = 0
        self.supertile_grid_height = 0
        self.map_width = 0
        self.map_height = 0

    def load_project_from_disk(self, source_filepath):
        """
        Loads all components of a project given a path to any one of its files.
        """
        if not os.path.exists(source_filepath):
            raise FileNotFoundError(f"Source file not found: {source_filepath}")

        base_path, _ = os.path.splitext(source_filepath)

        pal_path = base_path + ".SC4Pal"
        if os.path.exists(pal_path):
            self._load_palette(pal_path)

        tiles_path = base_path + ".SC4Tiles"
        if os.path.exists(tiles_path):
            self._load_tileset(tiles_path)

        super_path = base_path + ".SC4Super"
        if os.path.exists(super_path):
            self._load_supertiles(super_path)

        map_path = base_path + ".SC4Map"
        if os.path.exists(map_path):
            self._load_map(map_path)

        print("Project data loaded successfully.")

    def _load_palette(self, filepath):
        with open(filepath, "rb") as f:
            f.read(RESERVED_BYTES_COUNT) # Skip header
            for _ in range(16):
                color_bytes = f.read(3)
                if len(color_bytes) < 3:
                    raise ValueError("Incomplete palette file.")
                self.palette_data.append(struct.unpack("BBB", color_bytes))

    def _load_tileset(self, filepath):
        with open(filepath, "rb") as f:
            count_byte = f.read(1)
            self.num_tiles_in_set = struct.unpack("B", count_byte)[0]
            if self.num_tiles_in_set == 0:
                self.num_tiles_in_set = 256
            
            f.read(RESERVED_BYTES_COUNT)

            for _ in range(self.num_tiles_in_set):
                self.tileset_patterns.append(f.read(TILE_HEIGHT))
            
            for _ in range(self.num_tiles_in_set):
                self.tileset_colors.append(f.read(TILE_HEIGHT))

    def _load_supertiles(self, filepath):
        with open(filepath, "rb") as f:
            indicator_byte = struct.unpack("B", f.read(1))[0]
            if indicator_byte == 0:
                count_bytes = f.read(2)
                self.num_supertiles = struct.unpack("<H", count_bytes)[0]
            else:
                self.num_supertiles = indicator_byte
            
            dim_bytes = f.read(2)
            self.supertile_grid_width, self.supertile_grid_height = struct.unpack("BB", dim_bytes)
            
            f.read(RESERVED_BYTES_COUNT)

            bytes_per_st = self.supertile_grid_width * self.supertile_grid_height
            for _ in range(self.num_supertiles):
                self.supertiles_data.append(f.read(bytes_per_st))

    def _load_map(self, filepath):
        with open(filepath, "rb") as f:
            dim_bytes = f.read(4)
            self.map_width, self.map_height = struct.unpack("<HH", dim_bytes)
            
            f.read(RESERVED_BYTES_COUNT)
            
            use_2byte_indices = (self.num_supertiles > 255)
            bytes_per_cell = 2 if use_2byte_indices else 1
            total_cells = self.map_width * self.map_height
            
            self.map_data = f.read(total_cells * bytes_per_cell)

    def export_raw_palette(self, f):
        for r, g, b in self.palette_data:
            f.write(struct.pack("BBB", r, g, b))

    def export_raw_tileset(self, f):
        for pattern_bytes in self.tileset_patterns:
            f.write(pattern_bytes)
        for color_bytes in self.tileset_colors:
            f.write(color_bytes)

    def export_raw_supertiles(self, f):
        for st_data in self.supertiles_data:
            f.write(st_data)

    def export_raw_map(self, f):
        f.write(self.map_data)

    def generate_assembly_include(self, filepath, basename, inc_pal, inc_tiles, inc_super, inc_map):
        map_index_size = 2 if self.num_supertiles > 255 else 1
        content = f"; MSX Tile Forge Project Export Data\n"
        content += f"; Project Basename: {basename}\n\n"

        if inc_tiles:
            content += f"; --- Tileset Data ---\n"
            content += f"PROJECT_TILE_COUNT:   .equ {self.num_tiles_in_set}\n\n"

        if inc_super:
            content += f"; --- Supertile Data ---\n"
            content += f"PROJECT_SUPERTILE_COUNT: .equ {self.num_supertiles}\n"
            content += f"SUPERTILE_GRID_WIDTH:  .equ {self.supertile_grid_width}\n"
            content += f"SUPERTILE_GRID_HEIGHT: .equ {self.supertile_grid_height}\n\n"

        if inc_map:
            content += f"; --- Map Data ---\n"
            content += f"PROJECT_MAP_WIDTH:    .equ {self.map_width}\n"
            content += f"PROJECT_MAP_HEIGHT:   .equ {self.map_height}\n"
            content += f"PROJECT_MAP_INDEX_SIZE: .equ {map_index_size}\n"
        with open(filepath, "w") as f:
            f.write(content)
        print(f"Generated Assembly include file: {os.path.basename(filepath)}")

    def generate_c_header_meta(self, filepath, basename, inc_pal, inc_tiles, inc_super, inc_map):
        """Generates the C header file with only metadata #defines."""
        header_guard = f"{basename.upper().replace(' ', '_')}_META_H"
        map_index_size = 2 if self.num_supertiles > 255 else 1
        
        with open(filepath, "w") as f:
            f.write(f"/*\n * MSX Tile Forge Project Metadata: {basename}\n */\n\n")
            f.write(f"#ifndef {header_guard}\n#define {header_guard}\n\n")
            f.write("// --- Defines for Metadata ---\n")
            if inc_tiles:
                f.write(f"#define PROJECT_TILE_COUNT      {self.num_tiles_in_set}\n")
            if inc_super:
                f.write(f"#define PROJECT_SUPERTILE_COUNT {self.num_supertiles}\n")
                f.write(f"#define SUPERTILE_GRID_WIDTH    {self.supertile_grid_width}\n")
                f.write(f"#define SUPERTILE_GRID_HEIGHT   {self.supertile_grid_height}\n")
            if inc_map:
                f.write(f"#define PROJECT_MAP_WIDTH       {self.map_width}\n")
                f.write(f"#define PROJECT_MAP_HEIGHT      {self.map_height}\n")
                f.write(f"#define PROJECT_MAP_INDEX_SIZE  {map_index_size}\n")
            f.write(f"\n#endif // {header_guard}\n")
        print(f"Generated C metadata header: {os.path.basename(filepath)}")

    def generate_c_header_data(self, filepath, basename, inc_pal, inc_tiles, inc_super, inc_map):
        """Generates the C header file with only the data arrays."""
        header_guard = f"{basename.upper().replace(' ', '_')}_DATA_H"
        
        with open(filepath, "w") as f:
            f.write(f"/*\n * MSX Tile Forge Project Data: {basename}\n */\n\n")
            f.write(f"#ifndef {header_guard}\n#define {header_guard}\n\n")
            f.write("#include <stdint.h>\n")
            f.write(f'#include "{basename}_meta.h"\n\n')

            # Palette
            if inc_pal:
                f.write("// --- Palette Data (16 colors, 3 bytes each: R, G, B) ---\n")
                f.write("const uint8_t palette_data[16][3] = {\n")
                for i, (r,g,b) in enumerate(self.palette_data):
                    f.write(f"    {{{r},{g},{b}}}")
                    if i < 15: f.write(",")
                    if (i + 1) % 8 == 0: f.write("\n")
                f.write("};\n\n")

            # Tileset Patterns and Colors
            if inc_tiles:
                f.write("// --- Tileset Pattern Data (8 bytes per tile) ---\n")
                f.write("const uint8_t tileset_patterns[PROJECT_TILE_COUNT][8] = {\n")
                for i, p_data in enumerate(self.tileset_patterns):
                    f.write("    {" + ", ".join([f"0x{b:02X}" for b in p_data]) + "}")
                    if i < len(self.tileset_patterns) - 1: f.write(",\n")
                f.write("\n};\n\n")
                
                f.write("// --- Tileset Color Data (8 bytes per tile, FG/BG nibbles) ---\n")
                f.write("const uint8_t tileset_colors[PROJECT_TILE_COUNT][8] = {\n")
                for i, c_data in enumerate(self.tileset_colors):
                    f.write("    {" + ", ".join([f"0x{b:02X}" for b in c_data]) + "}")
                    if i < len(self.tileset_colors) - 1: f.write(",\n")
                f.write("\n};\n\n")

            # Supertile Data
            if inc_super:
                f.write("// --- Supertile Definition Data ---\n")
                f.write(f"const uint8_t supertiles_data[PROJECT_SUPERTILE_COUNT][SUPERTILE_GRID_HEIGHT][SUPERTILE_GRID_WIDTH] = {{\n")
                for i, st_data in enumerate(self.supertiles_data):
                    f.write("    {")
                    for r in range(self.supertile_grid_height):
                        row_data = st_data[r*self.supertile_grid_width:(r+1)*self.supertile_grid_width]
                        f.write("{" + ",".join(map(str, row_data)) + "}")
                        if r < self.supertile_grid_height - 1: f.write(",")
                    f.write("}")
                    if i < len(self.supertiles_data) - 1: f.write(",\n")
                f.write("\n};\n\n")

            # Map Data
            if inc_map:
                map_index_size = 2 if len(self.map_data) > (self.map_width * self.map_height) else 1
                f.write("// --- Map Data ---\n")
                if map_index_size == 1:
                    f.write(f"const uint8_t map_data[PROJECT_MAP_HEIGHT][PROJECT_MAP_WIDTH] = {{\n")
                    for r in range(self.map_height):
                        row_data = self.map_data[r*self.map_width:(r+1)*self.map_width]
                        f.write("    {" + ", ".join(map(str, row_data)) + "}")
                        if r < self.map_height - 1: f.write(",\n")
                else:
                    f.write(f"const uint16_t map_data[PROJECT_MAP_HEIGHT][PROJECT_MAP_WIDTH] = {{\n")
                    for r in range(self.map_height):
                        row_str = ""
                        for c in range(self.map_width):
                            offset = (r * self.map_width + c) * 2
                            val = struct.unpack("<H", self.map_data[offset:offset+2])[0]
                            row_str += str(val) + ", "
                        f.write("    {" + row_str.rstrip(", ") + "}")
                        if r < self.map_height - 1: f.write(",\n")
                f.write("\n};\n\n")

            f.write(f"#endif // {header_guard}\n")
        print(f"Generated C data header: {os.path.basename(filepath)}")

def main():
    print_splash_header(MSXTILEFORGE_VERSION, EXPORTER_VERSION)

    parser = argparse.ArgumentParser(description="Exports MSX Tile Forge projects to raw binary and include files.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("source_filepath", help="Path to any source project file (e.g., project.SC4Map).")
    parser.add_argument("--output-dir", default=".", help="Directory to save the exported files (defaults to the current directory).")
    parser.add_argument("--output-basename", help="Base name for exported files. (Defaults to the source file's name).")

    parser.add_argument("--nopal", dest="export_pal", action="store_false", help="Disable palette binary export.")
    parser.add_argument("--notiles", dest="export_tiles", action="store_false", help="Disable tileset binary export.")
    parser.add_argument("--nosuper", dest="export_super", action="store_false", help="Disable supertiles binary export.")
    parser.add_argument("--nomap", dest="export_map", action="store_false", help="Disable map binary export.")

    # C Header exclusion flags
    parser.add_argument("--c-nopal", dest="c_pal", action="store_false", help="Exclude palette from C header.")
    parser.add_argument("--c-notiles", dest="c_tiles", action="store_false", help="Exclude tileset from C header.")
    parser.add_argument("--c-nosuper", dest="c_super", action="store_false", help="Exclude supertiles from C header.")
    parser.add_argument("--c-nomap", dest="c_map", action="store_false", help="Exclude map from C header.")
    
    # ASM exclusion flags
    parser.add_argument("--asm-nopal", dest="asm_pal", action="store_false", help="Exclude palette from ASM include.")
    parser.add_argument("--asm-notiles", dest="asm_tiles", action="store_false", help="Exclude tileset from ASM include.")
    parser.add_argument("--asm-nosuper", dest="asm_super", action="store_false", help="Exclude supertiles from ASM include.")
    parser.add_argument("--asm-nomap", dest="asm_map", action="store_false", help="Exclude map from ASM include.")
    
    parser.set_defaults(
        bin_pal=True, bin_tiles=True, bin_super=True, bin_map=True,
        c_pal=True, c_tiles=True, c_super=True, c_map=True,
        asm_pal=True, asm_tiles=True, asm_super=True, asm_map=True
    )

    parser.add_argument("--asm", action="store_true", help="Generate an assembly include file (.s).")
    parser.add_argument("--c-header", action="store_true", help="Generate C header files for metadata (_meta.h) and data (_data.h).")
    args = parser.parse_args()

    # If output-basename is not provided, derive it from the source filepath
    if not args.output_basename:
        args.output_basename = os.path.splitext(os.path.basename(args.source_filepath))[0]

    try:
        if not os.path.isdir(args.output_dir):
            print(f"Output directory not found. Creating '{args.output_dir}'...")
            os.makedirs(args.output_dir, exist_ok=True)
        
        converter = ProjectConverter()
        converter.load_project_from_disk(args.source_filepath)
        
        file_types = []
        if args.export_pal:
            file_types.append(("SC4Pal", converter.export_raw_palette))
        if args.export_tiles:
            file_types.append(("SC4Tiles", converter.export_raw_tileset))
        if args.export_super:
            file_types.append(("SC4Super", converter.export_raw_supertiles))
        if args.export_map:
            file_types.append(("SC4Map", converter.export_raw_map))

        for ext, export_func in file_types:
            filepath = os.path.join(args.output_dir, f"{args.output_basename}_{ext}.bin")
            with open(filepath, "wb") as f:
                export_func(f)
            print(f"Exported raw binary: {os.path.basename(filepath)}")
        
        if args.asm:
            asm_filepath = os.path.join(args.output_dir, f"{args.output_basename}.s")
            converter.generate_assembly_include(asm_filepath, args.output_basename, args.asm_pal, args.asm_tiles, args.asm_super, args.asm_map)

        if args.c_header:
            meta_h_filepath = os.path.join(args.output_dir, f"{args.output_basename}_meta.h")
            converter.generate_c_header_meta(meta_h_filepath, args.output_basename, args.c_pal, args.c_tiles, args.c_super, args.c_map)
            data_h_filepath = os.path.join(args.output_dir, f"{args.output_basename}_data.h")
            converter.generate_c_header_data(data_h_filepath, args.output_basename, args.c_pal, args.c_tiles, args.c_super, args.c_map)
        
        print("\nExport complete.")
        return 0

    except Exception as e:
        print(f"\nERROR: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
