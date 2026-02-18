#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# MSX Tile Forge - A tile and map editor for MSX2
# Copyright (C) 2026 DamnedAngel
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.
#
# ------------------------------------------------------------------------------
# OPTIONAL ATTRIBUTION REQUEST:
# If you use MSX Tile Forge to create assets for a published project or game, 
# a credit line such as "Graphics created with MSX Tile Forge by [Your Name]" 
# is not required by this license, but would be greatly appreciated by the 
# author and helps support the tool's development.
# ------------------------------------------------------------------------------

# --- Version info ---
APP_VERSION = "<unreleased>"

import argparse
import os
import struct
import random
import re
import sys

def parse_tile_group(group_string: str) -> set[int]:
    """
    Parses a string like "5,8,12-16" into a set of integers.
    """
    if not group_string:
        return set()
    
    final_set = set()
    parts = group_string.split(',')
    
    for part in parts:
        part = part.strip()
        if not part:
            continue
        
        # Check for range (e.g., "12-16")
        if '-' in part:
            match = re.match(r'^(\d+)-(\d+)$', part)
            if not match:
                raise ValueError(f"Invalid range format: '{part}'. Must be in the format 'start-end'.")
            
            start, end = int(match.group(1)), int(match.group(2))
            if start >= end:
                raise ValueError(f"Invalid range: '{part}'. Start number must be less than end number.")
            
            final_set.update(range(start, end + 1))
        # Handle single number
        else:
            final_set.add(int(part))
            
    return final_set

def get_backup_filepath(original_path: str) -> str:
    """
    Finds an available backup filename like *_old1.SC4Super, *_old2.SC4Super, etc.
    """
    base, ext = os.path.splitext(original_path)
    counter = 1
    while True:
        backup_path = f"{base}_old{counter}{ext}"
        if not os.path.exists(backup_path):
            return backup_path
        counter += 1

def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description="A tool to replace tile indexes in a .SC4Super file.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "file",
        help="Path to the input .SC4Super file."
    )
    parser.add_argument(
        "--source",
        required=True,
        help="The group of tile indexes to be replaced.\n"
             "Format: Comma-separated numbers and/or ranges.\n"
             "Example: --source \"5,8,12-16,25\""
    )
    parser.add_argument(
        "--dest",
        required=True,
        help="The group of tile indexes to use as replacements.\n"
             "A random tile will be chosen from this group.\n"
             "Example: --dest \"50-65,70\""
    )
    parser.add_argument(
        "--consistent",
        action="store_true",
        help="Use consistent mapping. If specified, every instance of a specific\n"
             "source tile (e.g., all #10s) will be replaced by the *same* randomly\n"
             "chosen destination tile. If omitted (default), each instance is\n"
             "replaced by a new random choice from the destination group."
    )
    
    args = parser.parse_args()

    # --- 1. Validate Inputs ---
    if not os.path.exists(args.file):
        print(f"Error: Input file not found at '{args.file}'")
        sys.exit(1)

    try:
        source_group = parse_tile_group(args.source)
        dest_group = parse_tile_group(args.dest)
    except (ValueError, TypeError) as e:
        print(f"Error: Invalid tile group format. {e}")
        sys.exit(1)

    if not source_group:
        print("Error: The source group is empty. Nothing to replace.")
        sys.exit(1)
        
    if not dest_group:
        print("Error: The destination group is empty. Cannot choose replacements.")
        sys.exit(1)
        
    print(f"Source file: {os.path.basename(args.file)}")
    print(f"Source tile indexes to replace: {sorted(list(source_group))}")
    print(f"Destination tile indexes for replacement: {sorted(list(dest_group))}")
    replacement_mode = "Consistent (every instance of a tile gets the same replacement)" if args.consistent else "Independent (every instance gets a new random replacement)"
    print(f"Replacement Mode: {replacement_mode}\n")


    # --- 2. Read Supertile File ---
    try:
        with open(args.file, "rb") as f:
            # Read header to determine its size and content
            first_count_byte = f.read(1)
            indicator = struct.unpack("B", first_count_byte)[0]
            header_size = 1
            st_count = indicator

            if indicator == 0:
                count_bytes_short = f.read(2)
                header_size += 2
                st_count = struct.unpack(">H", count_bytes_short)[0]
            
            dim_bytes = f.read(2)
            header_size += 2
            st_grid_w, st_grid_h = struct.unpack("BB", dim_bytes)

            # --- START FIX ---
            # Check for the presence of reserved bytes based on total file size
            file_data_size = os.path.getsize(args.file)
            expected_data_payload_size = st_count * st_grid_w * st_grid_h
            has_reserved_bytes = (file_data_size == header_size + 4 + expected_data_payload_size)
            
            # Re-read the full header to preserve it
            f.seek(0)
            header_data = f.read(header_size)

            if has_reserved_bytes:
                # Read and store the reserved bytes to write them back out
                reserved_data = f.read(4)
                header_data += reserved_data # Combine all non-tile data
            # --- END FIX ---

            # Read the rest of the file data, which is now just the tile payload
            raw_data_bytes = f.read()

    except (IOError, struct.error) as e:
        print(f"Error: Could not read or parse the supertile file. Is it a valid .SC4Super file?\nDetails: {e}")
        sys.exit(1)
        
    print(f"File contains {st_count} supertiles with dimensions {st_grid_w}x{st_grid_h}.")
    if has_reserved_bytes:
        print("Detected modern file format with 4 reserved bytes.")
    
    # --- 3. Perform Replacement ---
    print("Processing replacements...")
    
    dest_list = list(dest_group)
    replacement_map = {}
    
    if args.consistent:
        # Create a consistent mapping from each source tile to a random destination tile
        replacement_map = {src_idx: random.choice(dest_list) for src_idx in source_group}
        print("Generated consistent replacement map:")
        for src, dest in replacement_map.items():
            print(f"  - All instances of tile #{src} will be replaced by tile #{dest}")
    
    # Unpack all tile indexes, perform replacement, and re-pack
    tiles_per_def = st_grid_w * st_grid_h
    total_tiles = st_count * tiles_per_def
    
    unpack_format = f">{total_tiles}B"
    if len(raw_data_bytes) < struct.calcsize(unpack_format):
        print(f"Error: File data size is incorrect. Expected {struct.calcsize(unpack_format)} bytes of tile data, but found {len(raw_data_bytes)}.")
        sys.exit(1)

    unpacked_data = list(struct.unpack(unpack_format, raw_data_bytes))
    
    replacement_count = 0
    for i in range(len(unpacked_data)):
        if unpacked_data[i] in source_group:
            if args.consistent:
                unpacked_data[i] = replacement_map[unpacked_data[i]]
            else: # Default independent/random behavior
                unpacked_data[i] = random.choice(dest_list)
            replacement_count += 1
            
    modified_data_bytes = struct.pack(unpack_format, *unpacked_data)
    
    # --- 4. Backup Original and Save New File ---
    try:
        backup_path = get_backup_filepath(args.file)
        print(f"\nBacking up original file to '{os.path.basename(backup_path)}'...")
        os.rename(args.file, backup_path)
        
        print(f"Saving modified data to '{os.path.basename(args.file)}'...")
        with open(args.file, "wb") as f:
            f.write(header_data) # This now includes the reserved bytes if they were present
            f.write(modified_data_bytes)
            
    except (IOError, OSError) as e:
        print(f"Error: Could not save the new file or create a backup.\nDetails: {e}")
        sys.exit(1)
        
    # --- 5. Final Report ---
    print("\n--- Operation Complete ---")
    print(f"Total tile index replacements made: {replacement_count}")
    print("--------------------------")

if __name__ == "__main__":
    main()