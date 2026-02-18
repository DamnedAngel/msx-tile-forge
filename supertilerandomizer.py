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

def parse_supertile_group(group_string: str) -> set[int]:
    """
    Parses a string like "5,8,100-116" into a set of integers.
    """
    if not group_string:
        return set()
    
    final_set = set()
    parts = group_string.split(',')
    
    for part in parts:
        part = part.strip()
        if not part:
            continue
        
        # Check for range (e.g., "100-116")
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
    Finds an available backup filename like *_old1.SC4Map, *_old2.SC4Map, etc.
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
        description="A tool to replace supertile indexes in a .SC4Map file.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "file",
        help="Path to the input .SC4Map file."
    )
    parser.add_argument(
        "--source",
        required=True,
        help="The group of supertile indexes to be replaced.\n"
             "Format: Comma-separated numbers and/or ranges.\n"
             "Example: --source \"100,105,200-210\""
    )
    parser.add_argument(
        "--dest",
        required=True,
        help="The group of supertile indexes to use as replacements.\n"
             "A random supertile will be chosen from this group.\n"
             "Example: --dest \"500-550\""
    )
    parser.add_argument(
        "--consistent",
        action="store_true",
        help="Use consistent mapping. If specified, every instance of a specific\n"
             "source supertile (e.g., all #100s) will be replaced by the *same* randomly\n"
             "chosen destination supertile. If omitted (default), each instance is\n"
             "replaced by a new random choice from the destination group."
    )
    
    args = parser.parse_args()

    # --- 1. Validate Inputs ---
    if not os.path.exists(args.file):
        print(f"Error: Input file not found at '{args.file}'")
        sys.exit(1)

    try:
        source_group = parse_supertile_group(args.source)
        dest_group = parse_supertile_group(args.dest)
    except (ValueError, TypeError) as e:
        print(f"Error: Invalid supertile group format. {e}")
        sys.exit(1)

    if not source_group:
        print("Error: The source group is empty. Nothing to replace.")
        sys.exit(1)
        
    if not dest_group:
        print("Error: The destination group is empty. Cannot choose replacements.")
        sys.exit(1)
        
    print(f"Source file: {os.path.basename(args.file)}")
    print(f"Source supertile indexes to replace: {sorted(list(source_group))}")
    print(f"Destination supertile indexes for replacement: {sorted(list(dest_group))}")
    replacement_mode = "Consistent (every instance of a supertile gets the same replacement)" if args.consistent else "Independent (every instance gets a new random replacement)"
    print(f"Replacement Mode: {replacement_mode}\n")

    # --- 2. Read Map File and Determine Format ---
    try:
        with open(args.file, "rb") as f:
            # Read header to get dimensions
            dim_bytes = f.read(4)
            if len(dim_bytes) < 4:
                raise struct.error("Could not read map dimensions from header.")
            
            map_w, map_h = struct.unpack(">HH", dim_bytes)
            
            # Auto-detect index size (1-byte or 2-byte) and reserved bytes
            file_data_size = os.path.getsize(args.file)
            num_cells = map_w * map_h
            header_size = 4
            
            # Calculate expected sizes for all known formats
            expected_size_old_1b = header_size + (num_cells * 1)
            expected_size_new_1b = header_size + 4 + (num_cells * 1)
            expected_size_new_2b = header_size + 4 + (num_cells * 2)

            has_reserved_bytes, use_2byte_indices = False, False
            if file_data_size == expected_size_new_1b:
                has_reserved_bytes, use_2byte_indices = True, False
            elif file_data_size == expected_size_new_2b:
                has_reserved_bytes, use_2byte_indices = True, True
            elif file_data_size == expected_size_old_1b:
                has_reserved_bytes, use_2byte_indices = False, False
            else:
                raise ValueError(f"File size mismatch for {map_w}x{map_h} dimensions. Is this a valid .SC4Map file?")

            # Re-read the full header block to preserve it
            f.seek(0)
            header_data = f.read(header_size)
            if has_reserved_bytes:
                reserved_data = f.read(4)
                header_data += reserved_data
            
            # Read the rest of the file data (the supertile index payload)
            raw_data_bytes = f.read()

    except (IOError, struct.error, ValueError) as e:
        print(f"Error: Could not read or parse the map file.\nDetails: {e}")
        sys.exit(1)
        
    print(f"File contains a {map_w}x{map_h} map.")
    index_size_msg = "2-byte (short)" if use_2byte_indices else "1-byte (char)"
    format_msg = "modern (with reserved bytes)" if has_reserved_bytes else "old"
    print(f"Detected {index_size_msg} indexes in {format_msg} format.")

    # --- 3. Perform Replacement ---
    print("Processing replacements...")
    
    dest_list = list(dest_group)
    replacement_map = {}
    
    if args.consistent:
        replacement_map = {src_idx: random.choice(dest_list) for src_idx in source_group}
        print("Generated consistent replacement map:")
        for src, dest in replacement_map.items():
            print(f"  - All instances of supertile #{src} will be replaced by supertile #{dest}")
    
    # Define the struct format based on detected index size
    unpack_char = ">H" if use_2byte_indices else ">B"
    index_byte_size = 2 if use_2byte_indices else 1
    total_supertiles = map_w * map_h
    
    # Unpack all supertile indexes one by one
    unpacked_data = []
    for i in range(total_supertiles):
        offset = i * index_byte_size
        index_data = struct.unpack(unpack_char, raw_data_bytes[offset:offset+index_byte_size])[0]
        unpacked_data.append(index_data)

    replacement_count = 0
    for i in range(len(unpacked_data)):
        if unpacked_data[i] in source_group:
            if args.consistent:
                unpacked_data[i] = replacement_map[unpacked_data[i]]
            else:
                unpacked_data[i] = random.choice(dest_list)
            replacement_count += 1
            
    # Re-pack the modified data
    modified_data_bytes = b"".join([struct.pack(unpack_char, val) for val in unpacked_data])
    
    # --- 4. Backup Original and Save New File ---
    try:
        backup_path = get_backup_filepath(args.file)
        print(f"\nBacking up original file to '{os.path.basename(backup_path)}'...")
        os.rename(args.file, backup_path)
        
        print(f"Saving modified data to '{os.path.basename(args.file)}'...")
        with open(args.file, "wb") as f:
            f.write(header_data)
            f.write(modified_data_bytes)
            
    except (IOError, OSError) as e:
        print(f"Error: Could not save the new file or create a backup.\nDetails: {e}")
        sys.exit(1)
        
    # --- 5. Final Report ---
    print("\n--- Operation Complete ---")
    print(f"Total supertile index replacements made: {replacement_count}")
    print("--------------------------")

if __name__ == "__main__":
    main()