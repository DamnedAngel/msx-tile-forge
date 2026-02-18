#!/usr/bin/env python3

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

# --- Program Identification ---
APP_VERSION = "<unreleased>"
SCRIPT_NAME = "MSX Tile Magic"
SCRIPT_VERSION = APP_VERSION
MSXTILEFORGE_VERSION = APP_VERSION

# --- Imports ---
import os
import sys
import argparse
from collections import Counter, defaultdict
import numpy as np
from PIL import Image
from tqdm import tqdm
import multiprocessing
from itertools import combinations
import heapq
import warnings

# --- Fixed tqdm configurations ---
tqdm_kwargs = {'file': sys.stdout or sys.__stdout__, 'mininterval': 0.1}
    
# --- Global Warning Filter ---
warnings.filterwarnings("ignore", message='.*"Matplotlib" related API features are not available.*')

# --- Optional Dependency Import for Advanced Color Metrics ---
try:
    import colour
    from colour.utilities import ColourUsageWarning
    COLOUR_SCIENCE_AVAILABLE = True
except ImportError:
    COLOUR_SCIENCE_AVAILABLE = False

# --- MSX2 Palette Constants ---
MSX2_MASTER_PALETTE_0_7 = [(r,g,b) for r in range(8) for g in range(8) for b in range(8)]
MSX2_MASTER_PALETTE_0_255 = [(r * 255 // 7, g * 255 // 7, b * 255 // 7) for r, g, b in MSX2_MASTER_PALETTE_0_7]

# --- Splash Screen ---
def print_splash_screen(script_name, script_version):
    COLOR_BLUE_DARK = '\033[34m'
    COLOR_BLUE_BRIGHT = '\033[94m'
    COLOR_ORANGE_DARK = '\033[33m'
    COLOR_ORANGE_BRIGHT = '\033[93m'
    COLOR_TITLE = '\033[1;97m'
    COLOR_VERSION = '\033[97m'
    COLOR_RESET = '\033[0m'

    if not sys.stdout.isatty():
        COLOR_BLUE_DARK = COLOR_BLUE_BRIGHT = COLOR_ORANGE_DARK = ""
        COLOR_ORANGE_BRIGHT = COLOR_TITLE = COLOR_VERSION = COLOR_RESET = ""

    block_char = "\u2588" * 2
    b_dark = f"{COLOR_BLUE_DARK}{block_char}{COLOR_RESET}"
    b_bright = f"{COLOR_BLUE_BRIGHT}{block_char}{COLOR_RESET}"
    o_dark = f"{COLOR_ORANGE_DARK}{block_char}{COLOR_RESET}"
    o_bright = f"{COLOR_ORANGE_BRIGHT}{block_char}{COLOR_RESET}"

    logo_lines = [
        f"{b_dark}{b_bright}{b_bright}{b_dark}",
        f"{b_bright}{o_dark}{o_bright}{b_bright}",
        f"{b_bright}{o_bright}{o_dark}{b_bright}",
        f"{b_dark}{b_bright}{b_bright}{b_dark}"
    ]

    text_lines = [
        f"{COLOR_TITLE}{script_name}{COLOR_RESET} (v{script_version})",
        f"{COLOR_VERSION}MSX Tile Forge suite, version {MSXTILEFORGE_VERSION}{COLOR_RESET}"
    ]

    print()
    print(f"{logo_lines[0]}")
    print(f"{logo_lines[1]}  {text_lines[0]}")
    print(f"{logo_lines[2]}  {text_lines[1]}")
    print(f"{logo_lines[3]}")
    print("-" * 60)

# --- Color Difference Functions ---
def color_distance_rgb(c1_rgb255, c2_rgb255):
    r1,g1,b1 = c1_rgb255
    r2,g2,b2 = c2_rgb255
    return (r1-r2)**2 + (g1-g2)**2 + (b1-b2)**2

def color_distance_weighted_rgb(c1_rgb255, c2_rgb255):
    r1,g1,b1 = c1_rgb255
    r2,g2,b2 = c2_rgb255
    dr, dg, db = r1-r2, g1-g2, b1-b2
    return (30*dr)**2 + (59*dg)**2 + (11*db)**2

if COLOUR_SCIENCE_AVAILABLE:
    def color_distance_cie76(c1_rgb255, c2_rgb255):
        rgb_array = np.array([c1_rgb255, c2_rgb255]) / 255.0
        xyz_array = colour.sRGB_to_XYZ(rgb_array)
        lab_array = colour.XYZ_to_Lab(xyz_array)
        delta_e = colour.delta_E(lab_array[0], lab_array[1], method='CIE 1976')
        return delta_e.item()

    def color_distance_ciede2000(c1_rgb255, c2_rgb255):
        rgb_array = np.array([c1_rgb255, c2_rgb255]) / 255.0
        xyz_array = colour.sRGB_to_XYZ(rgb_array)
        lab_array = colour.XYZ_to_Lab(xyz_array)
        delta_e = colour.delta_E(lab_array[0], lab_array[1], method='CIE 2000')
        return delta_e.item()

def get_color_distance_function(metric_name):
    if metric_name == 'rgb':
        return color_distance_rgb
    if metric_name == 'weighted-rgb':
        return color_distance_weighted_rgb
    if metric_name == 'cie76':
        return color_distance_cie76
    if metric_name == 'ciede2000':
        return color_distance_ciede2000
    return color_distance_weighted_rgb

# --- Helper Functions ---
def find_closest_msx_color(rgb_tuple_0_255, color_dist_func, exclude_colors_0_7=None):
    min_dist = float('inf')
    closest_msx_color_0_7 = (0,0,0)
    exclude_set = set(exclude_colors_0_7) if exclude_colors_0_7 else set()

    for idx, msx_color_candidate in enumerate(MSX2_MASTER_PALETTE_0_255):
        msx_color_0_7 = MSX2_MASTER_PALETTE_0_7[idx]
        if msx_color_0_7 in exclude_set:
            continue
            
        dist = color_dist_func(rgb_tuple_0_255, msx_color_candidate)
        if dist < min_dist:
            min_dist = dist
            closest_msx_color_0_7 = msx_color_0_7
        if dist == 0:
            break
    return closest_msx_color_0_7

def find_best_auto_colors_neutral(image: Image.Image, num_auto_colors: int, fixed_colors_0_7: list, color_dist_func):
    if num_auto_colors <= 0:
        return []
    
    if image.mode != 'RGB':
        image = image.convert('RGB')
        
    try:
        temp_quantized_img = image.quantize(colors=num_auto_colors, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    except Exception:
        temp_quantized_img = image.convert('P', palette=Image.Palette.ADAPTIVE, colors=num_auto_colors, dither=Image.Dither.NONE)
    
    pil_palette_255_flat = temp_quantized_img.getpalette()
    ideal_colors_255 = []
    if pil_palette_255_flat:
        num_ideal_colors = len(pil_palette_255_flat) // 3
        for i in range(num_ideal_colors):
            ideal_colors_255.append((pil_palette_255_flat[i*3], pil_palette_255_flat[i*3+1], pil_palette_255_flat[i*3+2]))

    auto_colors_0_7_set = set()
    auto_colors_0_7_list = []
    
    for r255,g255,b255 in ideal_colors_255:
        msx_color_0_7 = find_closest_msx_color((r255,g255,b255), color_dist_func, exclude_colors_0_7=fixed_colors_0_7)
        if msx_color_0_7 not in auto_colors_0_7_set and msx_color_0_7 not in fixed_colors_0_7:
            auto_colors_0_7_set.add(msx_color_0_7)
            auto_colors_0_7_list.append(msx_color_0_7)

    idx_master = 0
    combined_exclusions = auto_colors_0_7_set.union(set(fixed_colors_0_7))
    while len(auto_colors_0_7_list) < num_auto_colors and idx_master < len(MSX2_MASTER_PALETTE_0_7):
        candidate_color = MSX2_MASTER_PALETTE_0_7[idx_master]
        if candidate_color not in combined_exclusions:
            auto_colors_0_7_list.append(candidate_color)
            combined_exclusions.add(candidate_color)
        idx_master += 1
            
    return auto_colors_0_7_list[:num_auto_colors]

def find_best_auto_colors_sharp(image: Image.Image, num_auto_colors: int, fixed_colors_0_7: list, color_dist_func):
    return find_best_auto_colors_neutral(image, num_auto_colors, fixed_colors_0_7, color_dist_func)

def find_best_auto_colors_soft(image: Image.Image, num_auto_colors: int, fixed_colors_0_7: list, color_dist_func):
    if num_auto_colors <= 0:
        return []

    if image.mode != 'RGB':
        image = image.convert('RGB')
    try:
        temp_quantized_img = image.quantize(colors=256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    except Exception:
        temp_quantized_img = image.convert('P', palette=Image.Palette.ADAPTIVE, colors=256, dither=Image.Dither.NONE)
    
    pil_palette_255_flat = temp_quantized_img.getpalette()
    ideal_colors_255 = []
    if pil_palette_255_flat:
        num_ideal_colors = len(pil_palette_255_flat) // 3
        for i in range(num_ideal_colors):
            ideal_colors_255.append((pil_palette_255_flat[i*3], pil_palette_255_flat[i*3+1], pil_palette_255_flat[i*3+2]))

    auto_colors_0_7_set = set()
    auto_colors_0_7_list = []
    
    for r255,g255,b255 in ideal_colors_255:
        if len(auto_colors_0_7_list) >= num_auto_colors:
            break
        msx_color_0_7 = find_closest_msx_color((r255,g255,b255), color_dist_func, exclude_colors_0_7=fixed_colors_0_7)
        if msx_color_0_7 not in auto_colors_0_7_set and msx_color_0_7 not in fixed_colors_0_7:
            auto_colors_0_7_set.add(msx_color_0_7)
            auto_colors_0_7_list.append(msx_color_0_7)
    
    return auto_colors_0_7_list

def remap_image_to_palette(image: Image.Image, working_palette_0_7: list, dither_enabled: bool):
    if not working_palette_0_7:
        black_image = Image.new('P', image.size, color=0)
        black_image.putpalette([0,0,0]*256)
        return black_image

    working_palette_255 = [(r*255//7, g*255//7, b*255//7) for r,g,b in working_palette_0_7]
    
    full_pil_palette_255 = list(working_palette_255)
    full_pil_palette_255.extend([(0,0,0)] * (256 - len(working_palette_255)))
    pil_palette_flat = [c for rgb in full_pil_palette_255 for c in rgb]
    
    palette_image_for_remap = Image.new('P',(1,1))
    palette_image_for_remap.putpalette(pil_palette_flat)
    
    if image.mode != 'RGB':
        image = image.convert('RGB')
        
    dither_method = Image.Dither.FLOYDSTEINBERG if dither_enabled else Image.Dither.NONE
    quantized_image = image.quantize(palette=palette_image_for_remap, dither=dither_method)

    quantized_indices_np = np.array(quantized_image, dtype=np.uint8)
    
    lut = np.zeros(256, dtype=np.uint8)
    for i, rogue_color in enumerate(full_pil_palette_255):
        min_dist = float('inf')
        best_idx = 0
        for j, valid_color in enumerate(working_palette_255):
            dist = color_distance_rgb(rogue_color, valid_color)
            if dist < min_dist:
                min_dist = dist
                best_idx = j
            if min_dist == 0:
                break
        lut[i] = best_idx
    
    clean_indices_np = lut[quantized_indices_np]
    
    clean_image = Image.fromarray(clean_indices_np, 'P')
    minimal_palette_flat = [c for rgb in working_palette_255 for c in rgb]
    minimal_palette_flat.extend([0,0,0] * (256 - len(working_palette_255)))
    clean_image.putpalette(minimal_palette_flat)
    
    return clean_image

def process_palette_constraints(args):
    if args.palette:
        rules = [r.strip().lower() for r in args.palette.split(',')]
        if len(rules) != 16:
            print(f"Error: --palette argument must contain exactly 16 comma-separated rules. Found {len(rules)}.")
            sys.exit(1)
        return rules
        
    rules = [args.palette_all_slots.lower()] * 16

    if args.palette_constraints_file:
        try:
            with open(args.palette_constraints_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    parts = line.split()
                    if len(parts) != 2:
                        continue
                    idx_str, rule_str = parts
                    idx = int(idx_str)
                    if 0 <= idx <= 15:
                        rules[idx] = rule_str.lower()
        except FileNotFoundError:
            print(f"Warning: Constraint file '{args.palette_constraints_file}' not found. Ignoring.")

    if args.palette_slot:
        for idx_str, rule_str in args.palette_slot:
            try:
                idx = int(idx_str)
                if 0 <= idx <= 15:
                    rules[idx] = rule_str.lower()
                else:
                    print(f"Warning: Invalid slot index '{idx_str}' in --palette-slot. Must be 0-15. Ignoring.")
            except ValueError:
                print(f"Warning: Invalid slot index '{idx_str}' in --palette-slot. Must be an integer. Ignoring.")
    return rules

def _offset_worker_initializer(img_data):
    global worker_img_data, worker_height, worker_width
    worker_img_data = img_data
    worker_height, worker_width = img_data.shape

def _calculate_offset_score_worker(offset):
    dx, dy = offset
    current_score = 0
    num_tile_rows = (worker_height - dy) // 8
    num_tile_cols = (worker_width - dx) // 8

    for ty in range(num_tile_rows):
        for tx in range(num_tile_cols):
            y_start = dy + ty * 8
            x_start = dx + tx * 8
            tile = worker_img_data[y_start : y_start + 8, x_start : x_start + 8]
            
            if tile.shape != (8, 8):
                continue

            for r in range(8):
                if len(np.unique(tile[r, :])) > 2:
                    current_score += 1
    
    return current_score, offset

def find_best_tiling_offset(quantized_image, num_cores):
    img_data = np.array(quantized_image)
    tasks = [(dx, dy) for dy in range(8) for dx in range(8)]
    
    results = []
    init_args = (img_data,)
    with multiprocessing.Pool(processes=num_cores, initializer=_offset_worker_initializer, initargs=init_args) as pool:
        for result in tqdm(pool.imap_unordered(_calculate_offset_score_worker, tasks), total=len(tasks), desc="   Finding best offset", unit=" offsets", **tqdm_kwargs):
            results.append(result)
            
    if not results:
        return (0, 0)
        
    best_score, best_offset = min(results, key=lambda item: item[0])
    return best_offset

def process_tile_for_screen4(tile_indices_np, palette_0_255, color_dist_func):
    pattern_data=np.zeros(8,dtype=np.uint8)
    color_data=np.zeros(8,dtype=np.uint8)
    for r in range(8):
        row_indices=tile_indices_np[r]
        counts=Counter(row_indices)
        bg_idx,fg_idx=0,0
        if len(counts)>2:
            (c1_idx,_),(c2_idx,_) = counts.most_common(2)
            bg_idx,fg_idx=sorted([c1_idx,c2_idx])
            c1_rgb=palette_0_255[c1_idx]
            c2_rgb=palette_0_255[c2_idx]
            new_row=np.copy(row_indices)
            for c in range(8):
                original_idx=row_indices[c]
                if original_idx!=c1_idx and original_idx!=c2_idx:
                    original_rgb=palette_0_255[original_idx]
                    dist1=color_dist_func(original_rgb,c1_rgb)
                    dist2=color_dist_func(original_rgb,c2_rgb)
                    new_row[c]=c1_idx if dist1<=dist2 else c2_idx
            row_indices=new_row
        elif len(counts)==2:
            c1_idx,c2_idx=counts.keys()
            bg_idx,fg_idx=sorted([c1_idx,c2_idx])
        elif len(counts)==1:
            bg_idx=fg_idx=list(counts.keys())[0]
        color_data[r]=(fg_idx<<4)|bg_idx
        row_pattern_byte=0
        for c in range(8):
            if row_indices[c]==fg_idx:
                row_pattern_byte|=(1<<(7-c))
        pattern_data[r]=row_pattern_byte
    return pattern_data,color_data

def calculate_tile_difference(tile1_tuple, tile2_tuple, palette_255, color_dist_func):
    pattern1, color1 = tile1_tuple
    pattern2, color2 = tile2_tuple
    total_damage = 0
    def _get_pixel_rgb(row, col, pattern_data, color_data):
        pattern_byte = pattern_data[row]
        color_byte = color_data[row]
        is_foreground = (pattern_byte >> (7 - col)) & 1
        palette_idx = (color_byte >> 4) & 0x0F if is_foreground else color_byte & 0x0F
        return palette_255[palette_idx]
    for r in range(8):
        for c in range(8):
            rgb1 = _get_pixel_rgb(r, c, pattern1, color1)
            rgb2 = _get_pixel_rgb(r, c, pattern2, color2)
            total_damage += color_dist_func(rgb1, rgb2)
    return total_damage

def pad_image_to_tile_size(image: Image.Image):
    width, height = image.size
    pad_right = (8 - (width % 8)) % 8
    pad_bottom = (8 - (height % 8)) % 8
    if pad_right==0 and pad_bottom==0:
        return image
    new_width = width + pad_right
    new_height = height + pad_bottom
    padded_image = Image.new('P', (new_width, new_height), color=0)
    padded_image.putpalette(image.getpalette())
    padded_image.paste(image, (0, 0))
    return padded_image

# --- Multiprocessing Worker and Initializer ---
def _init_worker(tiles_data, palette, metric_name):
    global worker_tiles_data, worker_palette, worker_color_dist_func
    if COLOUR_SCIENCE_AVAILABLE:
        warnings.filterwarnings("ignore", category=ColourUsageWarning)
    worker_tiles_data = tiles_data
    worker_palette = palette
    worker_color_dist_func = get_color_distance_function(metric_name)

def _calculate_initial_costs_worker(pair):
    idx1, idx2 = pair
    tile1, tile2 = worker_tiles_data[idx1], worker_tiles_data[idx2]
    diff = calculate_tile_difference(tile1["data"], tile2["data"], worker_palette, worker_color_dist_func)
    if diff == 0:
        return None
    if tile1["count"] > tile2["count"]:
        loser_count = tile2["count"]
    elif tile2["count"] > tile1["count"]:
        loser_count = tile1["count"]
    else:
        loser_count = tile1["count"]
    cost = diff * loser_count
    return (cost, idx1, idx2)

def synthesize_ideal_tile(tile_group, palette_255, color_dist_func):
    num_tiles_in_group = len(tile_group)
    if num_tiles_in_group == 0:
        return np.zeros(8, dtype=np.uint8), np.zeros(8, dtype=np.uint8)

    avg_rgb_tile = np.zeros((8, 8, 3), dtype=np.float32)
    for tile_indices in tile_group:
        for r in range(8):
            for c in range(8):
                palette_idx = tile_indices[r, c]
                avg_rgb_tile[r, c] += palette_255[palette_idx]
    
    avg_rgb_tile /= num_tiles_in_group

    final_indices_tile = np.zeros((8, 8), dtype=np.uint8)
    for r in range(8):
        for c in range(8):
            avg_rgb = tuple(avg_rgb_tile[r, c])
            best_dist = float('inf')
            best_idx = 0
            for i, p_color in enumerate(palette_255):
                dist = color_distance_rgb(avg_rgb, p_color)
                if dist < best_dist:
                    best_dist = dist
                    best_idx = i
            final_indices_tile[r, c] = best_idx
            
    return process_tile_for_screen4(final_indices_tile, palette_255, color_dist_func)


def optimize_by_precomputation_and_heap(all_source_tiles_sc4, all_source_tiles_quantized, max_tiles, tm_width, tm_height, palette_255, num_cores, color_metric, synthesize, sort_strategy='cluster'):
    print("   Finding unique source tiles and their map counts...")
    unique_tile_groups = defaultdict(list)
    for i, tile_data in enumerate(all_source_tiles_sc4):
        key = tile_data[0].tobytes() + tile_data[1].tobytes()
        unique_tile_groups[key].append(i)
    
    initial_unique_count = len(unique_tile_groups)
    print(f"   [INFO] Found {initial_unique_count} unique tiles.")

    if initial_unique_count == 0:
        return [], np.zeros((tm_height, tm_width), dtype=np.int16)

    # --- Step 1: Build initial tile data and calculate all-pairs similarity ---
    unique_sc4_keys = list(unique_tile_groups.keys())
    unique_sc4_to_idx = {key: i for i, key in enumerate(unique_sc4_keys)}

    active_tiles = { i: {"data": all_source_tiles_sc4[locs[0]], "count": len(locs), "original_indices": {i}}
                     for i, (key, locs) in enumerate(unique_tile_groups.items()) }

    all_pairs = list(combinations(active_tiles.keys(), 2))
    print(f"   Generating memory structure for {len(all_pairs)} tile pairs...")
    
    merge_heap = []
    similarity_map = defaultdict(list)
    
    if all_pairs:
        print(f"   Initializing worker pool and transferring data to {num_cores} cores.\r\n      -> This may take some seconds, please wait..")
        chunksize = max(1, len(all_pairs) // (num_cores * 16))
        init_args = (active_tiles, palette_255, color_metric)
        with multiprocessing.Pool(processes=num_cores, initializer=_init_worker, initargs=init_args) as pool:
            tqdm_kwargs_for_costs = tqdm_kwargs.copy()
            tqdm_kwargs_for_costs['mininterval']=10.0
            for result in tqdm(pool.imap_unordered(_calculate_initial_costs_worker, all_pairs, chunksize=chunksize), total=len(all_pairs), desc="   Pre-calculating costs", unit=" tile pairs", **tqdm_kwargs):
                if result:
                    cost, idx1, idx2 = result
                    heapq.heappush(merge_heap, result)
                    similarity_map[idx1].append((cost, idx2))
                    similarity_map[idx2].append((cost, idx1))

    for idx in similarity_map:
        similarity_map[idx].sort()

    # --- Step 2: Merge tiles if necessary ---
    if initial_unique_count > max_tiles:
        num_merges_to_perform = len(active_tiles) - max_tiles
        print(f"   Performing {num_merges_to_perform} merges to reach target of {max_tiles} tiles...")
        is_active = {idx: True for idx in active_tiles.keys()}
        
        with tqdm(total=num_merges_to_perform, desc="   Merging tiles", unit=" merges", **tqdm_kwargs) as pbar:
            merges_done = 0
            while merges_done < num_merges_to_perform and merge_heap:
                cost, idx1, idx2 = heapq.heappop(merge_heap)
                if not (is_active.get(idx1) and is_active.get(idx2)):
                    continue
                
                tile1, tile2 = active_tiles[idx1], active_tiles[idx2]
                if tile1["count"] > tile2["count"]:
                    winner_idx, loser_idx = idx1, idx2
                elif tile2["count"] > tile1["count"]:
                    winner_idx, loser_idx = idx2, idx1
                else:
                    winner_idx, loser_idx = (idx1, idx2) if idx1 < idx2 else (idx2, idx1)
                
                active_tiles[winner_idx]["count"] += active_tiles[loser_idx]["count"]
                active_tiles[winner_idx]["original_indices"].update(active_tiles[loser_idx]["original_indices"])
                del active_tiles[loser_idx]
                is_active[loser_idx] = False
                merges_done += 1
                pbar.update(1)
    else:
        print(f"   [INFO] Initial unique tile count ({initial_unique_count}) is within limit. No merge needed.")

    # --- Step 3: Synthesize new tiles if requested ---
    if synthesize and initial_unique_count > max_tiles:
        print("   Synthesizing ideal tiles for merged groups...")
        color_dist_func = get_color_distance_function(color_metric)
        for tile_info in tqdm(active_tiles.values(), desc="   Synthesizing", unit=" tiles", **tqdm_kwargs):
            if len(tile_info["original_indices"]) > 1:
                group_locations = []
                for original_unique_idx in tile_info["original_indices"]:
                    key = unique_sc4_keys[original_unique_idx]
                    group_locations.extend(unique_tile_groups[key])
                
                quantized_tiles_for_group = [all_source_tiles_quantized[i] for i in group_locations]
                tile_info["data"] = synthesize_ideal_tile(quantized_tiles_for_group, palette_255, color_dist_func)

    # --- Step 4: Sort final tiles by similarity ---
    print("   Sorting final tileset for visual coherence...")
    sorted_tile_infos, old_winner_to_new_map = sort_items_by_similarity(
        list(active_tiles.values()),
        similarity_map,
        active_tiles,
        strategy=sort_strategy
    )
    
    # --- Step 5: Build final tileset and map based on sorted order ---
    print("   Building final tileset and map...")
    final_patterns = [info['data'] for info in sorted_tile_infos]
    
    # Create the final mapping from an original unique tile to its new sorted final index
    final_merge_map = {}
    for winner_idx, tile_info in active_tiles.items():
        if winner_idx not in old_winner_to_new_map: continue
        new_sorted_idx = old_winner_to_new_map[winner_idx]
        for original_unique_idx in tile_info["original_indices"]:
            final_merge_map[original_unique_idx] = new_sorted_idx

    final_tile_map = np.zeros((tm_height, tm_width), dtype=np.int16)
    for i, tile_data in enumerate(all_source_tiles_sc4):
        key = tile_data[0].tobytes() + tile_data[1].tobytes()
        if key in unique_sc4_to_idx:
            unique_idx = unique_sc4_to_idx[key]
            if unique_idx in final_merge_map:
                final_idx = final_merge_map[unique_idx]
                r, c = divmod(i, tm_width)
                final_tile_map[r, c] = final_idx
    
    return final_patterns, final_tile_map

def write_sc4_palette(filename, final_palette_0_7):
    with open(filename, "wb") as f:
        f.write(b'\x00' * 4) # Reserved header
        for r,g,b in final_palette_0_7:
            f.write(bytes([r, g, b]))

def write_sc4_tiles(filename, unique_patterns):
    num_tiles = len(unique_patterns)
    header_byte = num_tiles if num_tiles < 256 else 0
    with open(filename, "wb") as f:
        f.write(bytes([header_byte]))
        f.write(b'\x00' * 4)
        for pattern_data, _ in unique_patterns:
            f.write(pattern_data.tobytes())
        for _, color_data in unique_patterns:
            f.write(color_data.tobytes())

def write_sc4_supertiles(filename, supertile_definitions, super_w, super_h):
    num_supertiles = len(supertile_definitions)
    with open(filename, "wb") as f:
        if num_supertiles > 255:
            f.write(b'\x00')
            f.write(num_supertiles.to_bytes(2, 'little'))
        else:
            f.write(bytes([num_supertiles]))
        f.write(bytes([super_w, super_h]))
        f.write(b'\x00' * 4)
        for supertile_block in supertile_definitions:
            max_idx = np.max(supertile_block)
            bytes_per_idx = 2 if max_idx > 255 else 1
            for base_tile_idx in supertile_block.flat:
                f.write(int(base_tile_idx).to_bytes(bytes_per_idx, 'little'))

def write_sc4_map(filename, tile_map, num_supertiles):
    map_height, map_width = tile_map.shape
    bytes_per_index = 2 if num_supertiles > 255 else 1
    with open(filename, "wb") as f:
        f.write(map_width.to_bytes(2, 'little'))
        f.write(map_height.to_bytes(2, 'little'))
        f.write(b'\x00' * 4)
        for tile_idx in tile_map.flat:
            f.write(int(tile_idx).to_bytes(bytes_per_index, 'little'))

def reconstruct_sc4_tile_pil(pattern_data, color_data, pil_palette_flat):
    tile_img = Image.new('P', (8, 8))
    tile_img.putpalette(pil_palette_flat)
    pixels = tile_img.load()
    for r in range(8):
        color_byte = color_data[r]
        pattern_byte = pattern_data[r]
        bg_idx = int(color_byte & 0x0F)
        fg_idx = int((color_byte >> 4) & 0x0F)
        for c in range(8):
            is_fg_pixel = (pattern_byte >> (7 - c)) & 1
            pixels[c, r] = fg_idx if is_fg_pixel else bg_idx
    return tile_img

def discover_supertiles(tile_map, super_w, super_h):
    map_h, map_w = tile_map.shape
    if map_w % super_w != 0 or map_h % super_h != 0:
        print(f"Warning: Image dimensions ({map_w*8}px x {map_h*8}px) are not perfectly divisible by supertile dimensions ({super_w*8}px x {super_h*8}px).")
    
    super_map_w = map_w // super_w
    super_map_h = map_h // super_h
    supertile_map = np.zeros((super_map_h, super_map_w), dtype=np.int16)
    
    unique_supertiles = {}
    supertile_definitions = []
    
    for r_super in range(super_map_h):
        for c_super in range(super_map_w):
            r_start = r_super * super_h
            c_start = c_super * super_w
            block = tile_map[r_start : r_start + super_h, c_start : c_start + super_w]
            block_key = block.tobytes()
            
            if block_key not in unique_supertiles:
                new_supertile_id = len(supertile_definitions)
                unique_supertiles[block_key] = new_supertile_id
                supertile_definitions.append(block)
                supertile_map[r_super, c_super] = new_supertile_id
            else:
                supertile_id = unique_supertiles[block_key]
                supertile_map[r_super, c_super] = supertile_id
                
    return supertile_definitions, supertile_map

def translate_tile_indices(tile_tuple, working_to_final_map):
    pattern_data, color_data = tile_tuple
    final_color_data = np.zeros_like(color_data)
    for r in range(8):
        working_byte = color_data[r]
        working_fg = (working_byte >> 4) & 0x0F
        working_bg = working_byte & 0x0F
        
        final_fg = working_to_final_map[working_fg]
        final_bg = working_to_final_map[working_bg]
        
        final_color_data[r] = (final_fg << 4) | final_bg
    return (pattern_data, final_color_data)

def calculate_supertile_difference(st1_block, st2_block, base_tiles, final_pil_palette_flat, color_dist_func):
    total_damage = 0
    h, w = st1_block.shape
    for r in range(h):
        for c in range(w):
            idx1 = st1_block[r, c]
            idx2 = st2_block[r, c]
            if idx1 == idx2:
                continue
            # Ensure indices are within bounds before accessing
            if idx1 >= len(base_tiles) or idx2 >= len(base_tiles):
                continue
            tile1_data = base_tiles[idx1]
            tile2_data = base_tiles[idx2]
            total_damage += calculate_tile_difference(tile1_data, tile2_data, final_pil_palette_flat, color_dist_func)
    # Avoid division by zero if supertile is 1x1
    denominator = (w * h) if (w * h) > 0 else 1
    return total_damage / denominator

def _sort_greedy_chain(items_to_sort, similarity_map, old_indices):
    if not items_to_sort:
        return [], {}

    num_items = len(items_to_sort)
    remaining_indices = set(old_indices)
    
    # Start the chain with the first available index
    start_index = old_indices[0]
    sorted_indices = [start_index]
    remaining_indices.remove(start_index)
    
    current_index = start_index
    
    for _ in range(num_items - 1):
        if not remaining_indices: break
        
        best_next_index = -1
        min_dist = float('inf')
        
        # Find the closest neighbor to the current end of the chain
        if current_index in similarity_map:
            for dist, neighbor_idx in similarity_map[current_index]:
                if neighbor_idx in remaining_indices:
                    best_next_index = neighbor_idx
                    min_dist = dist
                    break # The list is sorted, so the first match is the best
        
        # Fallback if no pre-calculated neighbor is found (shouldn't happen)
        if best_next_index == -1:
            best_next_index = list(remaining_indices)[0]

        sorted_indices.append(best_next_index)
        remaining_indices.remove(best_next_index)
        current_index = best_next_index
        
    return sorted_indices

def _sort_cluster_aware(items_to_sort, similarity_map, old_indices, threshold_multiplier):
    if not items_to_sort:
        return [], {}

    # Find the average distance of the closest neighbor for all items
    avg_min_dist = 0
    valid_items = 0
    for idx in old_indices:
        if idx in similarity_map and similarity_map[idx]:
            avg_min_dist += similarity_map[idx][0][0] # cost of closest neighbor
            valid_items += 1
    if valid_items > 0:
        avg_min_dist /= valid_items
    
    # Set the threshold for what is considered "in the same cluster"
    cluster_threshold = avg_min_dist * threshold_multiplier

    # Identify seeds for clusters (items with many close neighbors)
    seeds = []
    for idx in old_indices:
        if idx in similarity_map:
            close_neighbors = sum(1 for cost, _ in similarity_map[idx] if cost < cluster_threshold)
            seeds.append((-close_neighbors, idx)) # Use negative for max-heap behavior
    heapq.heapify(seeds)

    # Group all items into clusters starting from the best seeds
    all_clusters = []
    remaining_indices = set(old_indices)
    
    while seeds:
        _, seed_idx = heapq.heappop(seeds)
        if seed_idx not in remaining_indices:
            continue
        
        current_cluster = []
        q = [seed_idx]
        visited_in_cluster = {seed_idx}
        
        while q:
            current_idx = q.pop(0)
            if current_idx in remaining_indices:
                current_cluster.append(current_idx)
                remaining_indices.remove(current_idx)

                if current_idx in similarity_map:
                    for cost, neighbor_idx in similarity_map[current_idx]:
                        if cost < cluster_threshold and neighbor_idx in remaining_indices and neighbor_idx not in visited_in_cluster:
                            q.append(neighbor_idx)
                            visited_in_cluster.add(neighbor_idx)
        
        if current_cluster:
            # Sort within the cluster using the greedy chain method
            sorted_sub_chain = _sort_greedy_chain(current_cluster, similarity_map, current_cluster)
            all_clusters.append(sorted_sub_chain)

    # Handle any remaining orphans
    if remaining_indices:
        all_clusters.append(list(remaining_indices))

    # Linearly order the clusters themselves by finding the closest connection
    final_sorted_indices = []
    if not all_clusters:
        return [], {}
        
    ordered_clusters = [all_clusters.pop(0)]
    
    while all_clusters:
        last_cluster = ordered_clusters[-1]
        last_idx = last_cluster[-1]
        best_next_cluster_idx = -1
        min_dist = float('inf')
        
        for i, candidate_cluster in enumerate(all_clusters):
            first_idx = candidate_cluster[0]
            if last_idx in similarity_map:
                for cost, neighbor_idx in similarity_map[last_idx]:
                    if neighbor_idx == first_idx:
                        if cost < min_dist:
                            min_dist = cost
                            best_next_cluster_idx = i
                        break
        
        if best_next_cluster_idx != -1:
            ordered_clusters.append(all_clusters.pop(best_next_cluster_idx))
        else: # Fallback
            ordered_clusters.append(all_clusters.pop(0))

    for cluster in ordered_clusters:
        final_sorted_indices.extend(cluster)
        
    return final_sorted_indices

def sort_items_by_similarity(items_to_sort, similarity_map, original_indices_map, strategy='cluster', threshold=2.5):
    old_indices = list(original_indices_map.keys())
    
    if strategy == 'cluster':
        sorted_indices = _sort_cluster_aware(items_to_sort, similarity_map, old_indices, threshold)
    elif strategy == 'greedy':
        sorted_indices = _sort_greedy_chain(items_to_sort, similarity_map, old_indices)
    else: # 'none' or invalid
        return items_to_sort, {i: i for i in range(len(items_to_sort))}

    old_to_new_map = {old_idx: new_idx for new_idx, old_idx in enumerate(sorted_indices)}
    
    final_sorted_items = [None] * len(items_to_sort)
    for old_idx, new_idx in old_to_new_map.items():
        original_item = original_indices_map[old_idx]
        final_sorted_items[new_idx] = original_item

    return final_sorted_items, old_to_new_map

def remap_indices(map_array, old_to_new_map):
    h, w = map_array.shape
    new_map = np.zeros_like(map_array)
    for r in range(h):
        for c in range(w):
            old_idx = map_array[r,c]
            if old_idx in old_to_new_map:
                new_map[r,c] = old_to_new_map[old_idx]
    return new_map

def _init_supertile_worker(st_defs, base_tiles, palette, metric_name):
    global worker_st_defs, worker_base_tiles, worker_palette, worker_color_dist_func
    if COLOUR_SCIENCE_AVAILABLE:
        warnings.filterwarnings("ignore", category=ColourUsageWarning)
    worker_st_defs = st_defs
    worker_base_tiles = base_tiles
    worker_palette = palette
    worker_color_dist_func = get_color_distance_function(metric_name)

def _calculate_supertile_cost_worker(pair):
    idx1, idx2 = pair
    st1_block = worker_st_defs[idx1]
    st2_block = worker_st_defs[idx2]
    dist = calculate_supertile_difference(st1_block, st2_block, worker_base_tiles, worker_palette, worker_color_dist_func)
    return dist, idx1, idx2

def main():
    if COLOUR_SCIENCE_AVAILABLE:
        warnings.filterwarnings("ignore", category=ColourUsageWarning)
        
    print_splash_screen(SCRIPT_NAME, SCRIPT_VERSION)
    
    parser = argparse.ArgumentParser(
        description=f"Transforming maps in MSX SC4 tiles like a charm.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("input_image", help="Input image file path")
    parser.add_argument("--term-columns", type=int, default=None, help="Force progress bars to comply to a fixed line width.")
    parser.add_argument("--output-dir", default=".", help="Directory for output files (defaults to current directory).")
    parser.add_argument("--output-basename", help="Basename for output files (defaults to the input file's name).")
    parser.add_argument("--cores", type=int, default=os.cpu_count(), help="Number of CPU cores to use. Defaults to all.")
    parser.add_argument("--no-maps", action="store_true", help="Generate only the palette and tileset, skipping supertile and map generation.")
    parser.add_argument("--find-best-offset", action="store_true", help="[EXPERIMENTAL] Test all 64 tile offsets in parallel and pick the one which reduces color clash.")
    parser.add_argument("--no-dithering", action="store_true", help="Disable dithering during color quantization.")
    parser.add_argument("--color-metric", choices=['rgb', 'weighted-rgb', 'cie76', 'ciede2000'], default='weighted-rgb',
                        help="Algorithm for color difference calculation. 'weighted-rgb' is default. CIE modes require 'pip install colormath'.")
    parser.add_argument("--optimization-mode", type=str, choices=['neutral', 'sharp', 'balanced', 'soft'], default='neutral', 
                        help="Palette strategy for optimization.\n"
                             "  neutral (default): Faithful, neutral color selection.\n"
                             "  sharp: High contrast palette for render and metrics.\n"
                             "  balanced: High contrast palette or rendering,low contrast palette for metrics (better tile reduction).\n"
                             "  soft: Low contrast for render and metrics (better tile reduction, 'washed' final image).")
    parser.add_argument("--max-tiles", type=int, default=256, help="Target maximum number of unique tiles")
    parser.add_argument("--synthesize-tiles", action="store_true", help="[EXPERIMENTAL] Generate new 'ideal' tiles for merged groups instead of picking an existing one.")
    parser.add_argument("--sort-tileset", type=str, choices=['none', 'greedy', 'cluster'], default='cluster',
                    help="Method to sort the final tileset for visual coherence.\n"
                            "  cluster (default): Groups tiles into visually similar clusters.\n"
                            "  greedy: Creates a continuous chain of most-similar tiles.\n"
                            "  none: Disables sorting, uses arbitrary order.")
    parser.add_argument("--supertile-width", type=int, default=4, help="Width of supertiles in tiles. Default: 4")
    parser.add_argument("--supertile-height", type=int, default=4, help="Height of supertiles in tiles. Default: 4")


    palette_group = parser.add_argument_group('Palette Constraints', 
        'Rules for controlling palette slots. Later rules override earlier ones.\n'
        'Rule formats: "auto", "block", or a color like "700" (R=7, G=0, B=0).\n'
        'Example: --palette-slot 0 700 --palette-slot 15 block')
    palette_group.add_argument("--palette", help="Defines all 16 palette slots in a single comma-separated string.\nIf used, this overrides all other palette arguments.\nExample: \"700,auto,auto,block,...\"")
    palette_group.add_argument("--palette-all-slots", metavar=('<RULE>'), default="auto", help="Baseline rule for all 16 slots.")
    palette_group.add_argument("--palette-constraints-file", help="Path to a text file with palette rules (e.g., '0 700').")
    palette_group.add_argument("--palette-slot", nargs=2, action='append', metavar=('<INDEX>', '<RULE>'), help="Set a rule for a specific slot. Can be used multiple times.")

    args = parser.parse_args()
    if args.term_columns:
        tqdm_kwargs['ncols'] = args.term_columns

    if (args.color_metric in ['cie76', 'ciede2000']) and not COLOUR_SCIENCE_AVAILABLE:
        print("\n--- ERROR ---")
        print(f"Color metric '{args.color_metric}' requires the 'colour-science' library.")
        print("Please install it using: pip install colour-science")
        return

    # --- 1. Process Palette Constraints ---
    print("1. Processing palette constraints...")
    final_rules = process_palette_constraints(args)
    
    fixed_colors_0_7 = []
    fixed_slot_indices = []
    auto_slot_indices = []
    
    for i, rule in enumerate(final_rules):
        if rule == 'auto':
            auto_slot_indices.append(i)
        elif rule == 'block':
            pass
        else:
            try:
                r, g, b = int(rule[0]), int(rule[1]), int(rule[2])
                if not all(0 <= c <= 7 for c in (r, g, b)): raise ValueError
                fixed_colors_0_7.append((r, g, b))
                fixed_slot_indices.append(i)
            except (ValueError, IndexError):
                print(f"Error: Invalid color rule '{rule}' for slot {i}. Rules must be either 3 digits from 0-7 (e.g., '700'), 'block' or 'auto'.")
                sys.exit(1)

    num_auto_colors = len(auto_slot_indices)
    num_valid_colors = len(fixed_colors_0_7) + num_auto_colors
    print(f"   [INFO] Palette config: {len(fixed_colors_0_7)} fixed, {num_auto_colors} auto, {16-num_valid_colors} blocked.")
    
    if num_valid_colors == 0:
        print("Error: All palette slots are blocked. Cannot process image.")
        return
    
    try:
        original_pil_image = Image.open(args.input_image)
    except FileNotFoundError:
        print(f"Error: Input image '{args.input_image}' not found.")
        return

    if args.output_basename:
        base_name = args.output_basename
    else:
        base_name = os.path.splitext(os.path.basename(args.input_image))[0]

    full_output_path = os.path.join(args.output_dir, base_name)
    color_dist_func = get_color_distance_function(args.color_metric)

    # --- 2. Generate Palettes based on Mode ---
    print(f"2. Generating palettes (mode: {args.optimization_mode})...")
    
    if args.optimization_mode == 'neutral':
        render_palette_func = find_best_auto_colors_neutral
        metric_palette_func = find_best_auto_colors_neutral
    elif args.optimization_mode == 'sharp':
        render_palette_func = find_best_auto_colors_sharp
        metric_palette_func = find_best_auto_colors_sharp
    elif args.optimization_mode == 'balanced':
        render_palette_func = find_best_auto_colors_sharp
        metric_palette_func = find_best_auto_colors_soft
    else: # soft
        render_palette_func = find_best_auto_colors_soft
        metric_palette_func = find_best_auto_colors_soft

    render_auto_colors = render_palette_func(original_pil_image, num_auto_colors, fixed_colors_0_7, color_dist_func)
    print(f"   [INFO] Found {len(render_auto_colors)} unique colors for final render palette.")
    render_working_palette_0_7 = fixed_colors_0_7 + render_auto_colors
    working_to_final_map = {i: final_slot for i, final_slot in enumerate(fixed_slot_indices + auto_slot_indices[:len(render_auto_colors)])}
    
    if args.optimization_mode == 'balanced':
        print(f"   [INFO] Generating separate 'soft' palette for optimization metrics...")
        metric_auto_colors = metric_palette_func(original_pil_image, num_auto_colors, fixed_colors_0_7, color_dist_func)
        metric_working_palette_0_7 = fixed_colors_0_7 + metric_auto_colors
    else:
        metric_working_palette_0_7 = render_working_palette_0_7

    # --- 3. Remap image colors ---
    print("3. Remapping image colors...")
    print(f"   [INFO] Using {len(render_working_palette_0_7)}-color render palette...")
    quantized_pil_image = remap_image_to_palette(original_pil_image, render_working_palette_0_7, not args.no_dithering)

    if args.find_best_offset:
        print(f"3a. Evaluating 64 possible offsets on {args.cores} cores...")
        best_offset = find_best_tiling_offset(quantized_pil_image, args.cores)
        dx, dy = best_offset
        print(f"   [INFO] Optimal offset found at ({dx}, {dy}). Cropping image.")
        width, height = quantized_pil_image.size
        quantized_pil_image = quantized_pil_image.crop((dx, dy, width, height))

    quantized_pil_image = pad_image_to_tile_size(quantized_pil_image)
    img_width, img_height = quantized_pil_image.size
    tile_map_width, tile_map_height = img_width // 8, img_height // 8

    # --- 4. Extracting tiles ---
    print("4. Extracting and processing source tiles...")
    all_source_tiles_sc4_render = []
    all_source_tiles_sc4_metric = []
    all_source_tiles_quantized = [] # For synthesis
    
    render_palette_255 = [(r*255//7, g*255//7, b*255//7) for r,g,b in render_working_palette_0_7]
    metric_palette_255 = [(r*255//7, g*255//7, b*255//7) for r,g,b in metric_working_palette_0_7]

    quantized_np_indices = np.array(quantized_pil_image.getdata(), dtype=np.uint8).reshape((img_height, img_width))
    for ty in tqdm(range(tile_map_height), desc="   Processing Tiles", unit=" map rows", **tqdm_kwargs):
        for tx in range(tile_map_width):
            tile_block = quantized_np_indices[ty*8:(ty+1)*8, tx*8:(tx+1)*8]
            all_source_tiles_quantized.append(tile_block)
            
            all_source_tiles_sc4_render.append(process_tile_for_screen4(tile_block, render_palette_255, color_dist_func))
            
            if args.optimization_mode == 'balanced':
                metric_remapped_tile_block = np.zeros_like(tile_block)
                for r in range(8):
                    for c in range(8):
                        render_idx = tile_block[r,c]
                        render_color_255 = render_palette_255[render_idx]
                        best_dist = float('inf')
                        best_metric_idx = 0
                        for i, metric_color_255 in enumerate(metric_palette_255):
                            dist = color_distance_rgb(render_color_255, metric_color_255)
                            if dist < best_dist:
                                best_dist = dist
                                best_metric_idx = i
                        metric_remapped_tile_block[r,c] = best_metric_idx
                all_source_tiles_sc4_metric.append(process_tile_for_screen4(metric_remapped_tile_block, metric_palette_255, color_dist_func))
            else:
                all_source_tiles_sc4_metric = all_source_tiles_sc4_render

    print(f"   [INFO] Image contains a total of {len(all_source_tiles_sc4_render)} tiles (including duplicates).")

    # --- 5. Optimize Tiles ---
    print("5. Optimizing tiles...")
    optimized_patterns_metric, final_tile_map_indices = optimize_by_precomputation_and_heap(
        all_source_tiles_sc4_metric, all_source_tiles_quantized, args.max_tiles, tile_map_width, tile_map_height,
        metric_palette_255, args.cores, args.color_metric, args.synthesize_tiles, args.sort_tileset)    
    # --- 6. Translate to Final Render Tiles ---
    print("6. Translating tiles to final format...")
    if args.optimization_mode == 'balanced':
        unique_metric_tile_groups = defaultdict(list)
        for i, tile_data in enumerate(all_source_tiles_sc4_metric):
            key = tile_data[0].tobytes() + tile_data[1].tobytes()
            unique_metric_tile_groups[key].append(i)
        
        final_render_patterns = []
        for metric_tile in optimized_patterns_metric:
            key = metric_tile[0].tobytes() + metric_tile[1].tobytes()
            original_location = unique_metric_tile_groups[key][0]
            final_render_patterns.append(all_source_tiles_sc4_render[original_location])
    else:
        final_render_patterns = optimized_patterns_metric

    final_unique_patterns = [translate_tile_indices(p, working_to_final_map) for p in final_render_patterns]
    num_unique_base_patterns = len(final_unique_patterns)
    print(f"   [INFO] Optimization complete. Final tile count: {num_unique_base_patterns}")

    # 6.1: Create the final MSX palette (must be done before sorting supertiles)
    final_palette_0_7 = [(0,0,0)] * 16
    for i, slot_rule in enumerate(final_rules):
        if slot_rule == 'block':
            final_palette_0_7[i] = (128, 0, 0)
    for i, color in enumerate(render_working_palette_0_7):
        final_slot = working_to_final_map[i]
        final_palette_0_7[final_slot] = color
    
    # --- 7. Supertile Discovery and Sorting ---
    if not args.no_maps:
        supertile_definitions = []
        final_map_to_write = final_tile_map_indices
        num_supertiles = num_unique_base_patterns
        use_supertiles = args.supertile_width > 1 or args.supertile_height > 1

        # Part 7.1: Discover unique supertiles
        if use_supertiles:
            print(f"7. Discovering {args.supertile_width}x{args.supertile_height} supertiles...")
            supertile_definitions, supertile_map = discover_supertiles(final_tile_map_indices, args.supertile_width, args.supertile_height)
            num_supertiles = len(supertile_definitions)
            final_map_to_write = supertile_map
            print(f"   [INFO] Found {num_supertiles} unique {args.supertile_width}x{args.supertile_height} supertiles.")
        else:
            print("7. Generating 1x1 supertile definitions...")
            for i in range(num_unique_base_patterns):
                supertile_definitions.append(np.array([[i]], dtype=np.int16))

        # 7.2: Sort the supertiles by visual similarity if requested
        if use_supertiles and args.sort_tileset != 'none' and num_supertiles > 1:
            # Create a PIL-compatible RGB 0-255 palette for the comparison function
            final_pil_palette_for_compare = [(c[0]*255//7, c[1]*255//7, c[2]*255//7) if c[0] < 128 else (0,0,0) for c in final_palette_0_7]
            pil_final_palette_flat_for_compare = [comp for rgb in final_pil_palette_for_compare for comp in rgb]
        
            print(f"   Sorting {num_supertiles} supertiles for visual coherence...")
            st_similarity_map = defaultdict(list)
            st_pairs = list(combinations(range(num_supertiles), 2))
        
            st_similarity_map = defaultdict(list)
            st_pairs = list(combinations(range(num_supertiles), 2))

            init_args = (supertile_definitions, final_unique_patterns, final_pil_palette_for_compare, args.color_metric)
            chunksize = max(1, len(st_pairs) // (args.cores * 16))

            with multiprocessing.Pool(processes=args.cores, initializer=_init_supertile_worker, initargs=init_args) as pool:
                for dist, idx1, idx2 in tqdm(pool.imap_unordered(_calculate_supertile_cost_worker, st_pairs, chunksize=chunksize), total=len(st_pairs), desc="   Clustering supertiles", unit=" supertile pairs", **tqdm_kwargs):
                    st_similarity_map[idx1].append((dist, idx2))
                    st_similarity_map[idx2].append((dist, idx1))

            for idx in st_similarity_map:
                st_similarity_map[idx].sort()

            original_st_map = {i: st for i, st in enumerate(supertile_definitions)}
            sorted_supertiles, old_st_to_new_map = sort_items_by_similarity(
                supertile_definitions,
                st_similarity_map,
                original_st_map,
                strategy=args.sort_tileset
            )

            # Update the definitions and map with the new sorted order
            supertile_definitions = sorted_supertiles
            final_map_to_write = remap_indices(supertile_map, old_st_to_new_map)

    # --- 8. Generate Output Files ---
    print("8. Generating output files...")
    os.makedirs(args.output_dir, exist_ok=True)
    
    final_palette_0_7 = [(0,0,0)] * 16
    for i, slot_rule in enumerate(final_rules):
        if slot_rule == 'block':
            # red channel bit 7 is the flag for MSX Tile Forge to skip importing blocked slot
            final_palette_0_7[i] = (128, 0, 0)
    for i, color in enumerate(render_working_palette_0_7):
        final_slot = working_to_final_map[i]
        final_palette_0_7[final_slot] = color
        
    write_sc4_palette(f"{full_output_path}.SC4Pal", final_palette_0_7)
    write_sc4_tiles(f"{full_output_path}.SC4Tiles", final_unique_patterns)

    if not args.no_maps:
        write_sc4_supertiles(f"{full_output_path}.SC4Super", supertile_definitions, args.supertile_width, args.supertile_height)
        write_sc4_map(f"{full_output_path}.SC4Map", final_map_to_write, num_supertiles)

    # --- 9. Generate Visual Outputs ---
    if not args.no_maps:
        print("9. Generating visual outputs...")
        final_pil_palette = [(0,0,0)] * 16
        for i, color in enumerate(final_palette_0_7):
            if color[0] < 128:
                final_pil_palette[i] = (color[0]*255//7, color[1]*255//7, color[2]*255//7)
    
        pil_final_palette_flat = [c for rgb in final_pil_palette for c in rgb]
        pil_final_palette_flat.extend([0,0,0] * (256-16))

        reconstructed_img = Image.new('P', (img_width, img_height), color=0)
        reconstructed_img.putpalette(pil_final_palette_flat)
        for r_map in range(tile_map_height):
            for c_map in range(tile_map_width):
                pattern_idx = final_tile_map_indices[r_map, c_map]
                if 0 <= pattern_idx < num_unique_base_patterns:
                    tile_to_paste = reconstruct_sc4_tile_pil(final_unique_patterns[pattern_idx][0], final_unique_patterns[pattern_idx][1], pil_final_palette_flat)
                    reconstructed_img.paste(tile_to_paste, (c_map * 8, r_map * 8))
        reconstructed_img.save(f"{full_output_path}_reconstructed.png")

        tiles_per_row = 16
        num_rows = (num_unique_base_patterns + tiles_per_row - 1) // tiles_per_row
        tileset_vis = Image.new('P', (tiles_per_row*8, num_rows*8), color=0)
        tileset_vis.putpalette(pil_final_palette_flat)
        for i, (p_data, c_data) in enumerate(final_unique_patterns):
            r_vis, c_vis = divmod(i, tiles_per_row)
            tile_to_paste = reconstruct_sc4_tile_pil(p_data, c_data, pil_final_palette_flat)
            tileset_vis.paste(tile_to_paste, (c_vis * 8, r_vis * 8))
        tileset_vis.save(f"{full_output_path}_tileset.png")
    
    print("\nProcessing complete.")

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)