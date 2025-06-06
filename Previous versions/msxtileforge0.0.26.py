# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk
from tkinter import colorchooser
from tkinter import filedialog
from tkinter import messagebox
from tkinter import simpledialog
import struct
import os
import math
import copy

# --- Constants ---
TILE_WIDTH = 8
TILE_HEIGHT = 8
EDITOR_PIXEL_SIZE = 30
VIEWER_TILE_SIZE = TILE_WIDTH * 2  # 16
PALETTE_SQUARE_SIZE = 20
NUM_TILES_ACROSS = 16
MAX_TILES = 256
SUPERTILE_GRID_DIM = 4
SUPERTILE_DEF_TILE_SIZE = TILE_WIDTH * 4  # 32
SUPERTILE_SELECTOR_PREVIEW_SIZE = TILE_WIDTH * 4  # 32
NUM_SUPERTILES_ACROSS = 8
MAX_SUPERTILES = 256
DEFAULT_MAP_WIDTH = 32  # In supertiles
DEFAULT_MAP_HEIGHT = 24  # In supertiles
DEFAULT_WIN_VIEW_WIDTH_TILES = 32  # Default screen size
DEFAULT_WIN_VIEW_HEIGHT_TILES = 24  # Default screen size
MAX_WIN_VIEW_HEIGHT_TILES = 27  # Allow up to 27 for half-tile logic

MINIMAP_INITIAL_WIDTH = 256  # Default desired width of minimap window in pixels
MINIMAP_INITIAL_HEIGHT = 212  # Default desired height of minimap window in pixels

# --- Palette Editor Constants ---
MSX2_PICKER_COLS = 32
MSX2_PICKER_ROWS = 16
MSX2_PICKER_SQUARE_SIZE = 15
CURRENT_PALETTE_SLOT_SIZE = 30

# --- MSX2 Default Palette (Indices & Colors) ---
MSX2_RGB7_VALUES = [
    (0, 0, 0),
    (0, 0, 0),
    (1, 6, 1),
    (3, 7, 3),
    (1, 1, 7),
    (2, 3, 7),
    (5, 1, 1),
    (2, 6, 7),
    (7, 1, 1),
    (7, 3, 3),
    (6, 6, 1),
    (6, 6, 4),
    (1, 4, 1),
    (6, 2, 5),
    (5, 5, 5),
    (7, 7, 7),
]
BLACK_IDX = 1
MED_GREEN_IDX = 2
WHITE_IDX = 15

# --- Placeholder Colors ---
INVALID_TILE_COLOR = "#FF00FF"
INVALID_SUPERTILE_COLOR = "#00FFFF"

# --- Grid & Overlay Constants ---
GRID_COLOR_CYCLE = [
    "#FFFFFF",
    "#000000",
    "#FF00FF",
    "#00FFFF",
    "#FFFF00",
]  # White, Black, Magenta, Cyan, Yellow
GRID_DASH_PATTERN = (5, 3)  # 5 pixels on, 3 pixels off
WIN_VIEW_HANDLE_SIZE = 8  # Pixel size of resize handles
WIN_VIEW_HALF_ROW_COLOR = "#80808080"  # Semi-transparent grey for overscan area (adjust alpha if needed, format depends on tk version)

# --- MSX2 Color Generation ---
msx2_512_colors_hex = []
msx2_512_colors_rgb7 = []
for r in range(8):
    for g in range(8):
        for b in range(8):
            r_255 = min(255, r * 36)
            g_255 = min(255, g * 36)
            b_255 = min(255, b * 36)
            hex_color = f"#{r_255:02x}{g_255:02x}{b_255:02x}"
            msx2_512_colors_hex.append(hex_color)
            msx2_512_colors_rgb7.append((r, g, b))

# --- Data Structures ---
tileset_patterns = [
    [[0] * TILE_WIDTH for _ in range(TILE_HEIGHT)] for _ in range(MAX_TILES)
]
tileset_colors = [
    [(WHITE_IDX, BLACK_IDX) for _ in range(TILE_HEIGHT)] for _ in range(MAX_TILES)
]
current_tile_index = 0
num_tiles_in_set = 1
selected_color_index = WHITE_IDX
last_drawn_pixel = None
supertiles_data = [
    [[0 for _ in range(SUPERTILE_GRID_DIM)] for _ in range(SUPERTILE_GRID_DIM)]
    for _ in range(MAX_SUPERTILES)
]
current_supertile_index = 0
num_supertiles = 1
selected_tile_for_supertile = 0
map_width = DEFAULT_MAP_WIDTH  # In supertiles
map_height = DEFAULT_MAP_HEIGHT  # In supertiles
map_data = [[0 for _ in range(map_width)] for _ in range(map_height)]
selected_supertile_for_map = 0
last_painted_map_cell = None
tile_clipboard_pattern = None
tile_clipboard_colors = None
supertile_clipboard_data = None

# --- Utility Functions ---
def get_contrast_color(hex_color):
    try:
        hex_color = hex_color.lstrip("#")
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
        return "#000000" if luminance > 0.5 else "#FFFFFF"
    except:
        return "#000000"


# --- Application Class ---
class TileEditorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("MSX2 Tile Studio - Untitled")
        self.root.state("zoomed")

        self.current_project_base_path = None
        self.project_modified = False

        # --- Dynamic Palette ---
        self.active_msx_palette = []
        for r, g, b in MSX2_RGB7_VALUES:
            canonical_hex = self._rgb7_to_hex(r, g, b)
            self.active_msx_palette.append(canonical_hex)
        self.selected_palette_slot = 0

        # --- Image Caches ---
        self.tile_image_cache = {}
        self.supertile_image_cache = {}

        # --- Drag and Drop State ---
        self.drag_active = False
        self.drag_item_type = None  # 'tile' or 'supertile'
        self.drag_start_index = -1
        self.drag_canvas = None  # The canvas where drag started
        self.drag_indicator_id = None  # ID for the visual drop indicator line

        # --- Map Editor State ---
        self.map_zoom_level = 1.0
        self.show_supertile_grid = tk.BooleanVar(value=False)
        self.show_window_view = tk.BooleanVar(value=False)
        self.grid_color_index = 1
        self.window_view_tile_x = 0
        self.window_view_tile_y = 0
        self.window_view_tile_w = tk.IntVar(value=DEFAULT_WIN_VIEW_WIDTH_TILES)
        self.window_view_tile_h = tk.IntVar(value=DEFAULT_WIN_VIEW_HEIGHT_TILES)
        self.window_view_resize_handle = None  # Keep for resize type
        self.drag_start_x = 0  # Keep for window move/resize calcs
        self.drag_start_y = 0
        self.drag_start_win_tx = 0  # Keep for window move/resize calcs
        self.drag_start_win_ty = 0
        self.drag_start_win_tw = 0  # Keep for window move/resize calcs
        self.drag_start_win_th = 0

        # --- Minimap State ---
        self.minimap_window = None
        self.minimap_canvas = None
        self.MINIMAP_WIDTH = 256
        self.MINIMAP_HEIGHT = 212
        self.MINIMAP_VIEWPORT_COLOR = "#FF0000"
        self.MINIMAP_WIN_VIEW_COLOR = "#0000FF"
        self.minimap_background_cache = None
        self.minimap_bg_rendered_width = 0
        self.minimap_bg_rendered_height = 0
        self.minimap_resize_timer = None
        self._minimap_resizing_internally = False

        # --- Interaction State ---
        self.is_ctrl_pressed = False  # Track if Control key is held down
        self.current_mouse_action = None  # None, 'panning', 'painting', 'window_dragging', 'window_resizing', 'map_selecting'
        self.pan_start_x = 0
        self.pan_start_y = 0

        self.last_placed_supertile_cell = (
            None  # Track last cell modified in supertile def drag
        )

        # --- Map Selection State ---
        self.is_shift_pressed = False  # Track Shift key state
        self.map_selection_active = False  # Is a selection drag in progress?
        self.map_selection_rect_id = None  # Canvas ID for the visual rectangle
        self.map_selection_start_st = None  # Start coords (col, row) in supertiles
        self.map_selection_end_st = None  # End coords (col, row) in supertiles
        self.map_clipboard_data = None  # Stores {'width':w, 'height':h, 'data':[[...]]}
        self.map_paste_preview_rect_id = None # ID for the paste preview rectangle

        # --- Menu State References --
        self.edit_menu = None  # To store the Edit menu object
        self.copy_menu_item_index = -1  # To store the index of "Copy"
        self.paste_menu_item_index = -1  # To store the index of "Paste"

        # --- UI Setup ---
        self.create_menu()
        self._setup_global_key_bindings()
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(pady=10, padx=10, expand=True, fill="both")

        self.tab_palette_editor = ttk.Frame(self.notebook, padding="10")
        self.tab_tile_editor = ttk.Frame(self.notebook, padding="10")
        self.tab_supertile_editor = ttk.Frame(self.notebook, padding="10")
        self.tab_map_editor = ttk.Frame(self.notebook, padding="10")

        self.notebook.add(self.tab_palette_editor, text="Palette Editor")
        self.notebook.add(self.tab_tile_editor, text="Tile Editor")
        self.notebook.add(self.tab_supertile_editor, text="Supertile Editor")
        self.notebook.add(self.tab_map_editor, text="Map Editor")

        # Call widget creation AFTER defining the tab frames
        self.create_palette_editor_widgets(self.tab_palette_editor)
        self.create_tile_editor_widgets(self.tab_tile_editor)
        self.create_supertile_editor_widgets(self.tab_supertile_editor)
        self.create_map_editor_widgets(self.tab_map_editor)

        self.update_all_displays(changed_level="all")
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_change)

        # --- Extra Bindings for Map Canvas ---
        self._setup_map_canvas_bindings()  # Setup bindings AFTER map canvas exists

        self._update_window_title()
        self._update_edit_menu_state()
        self._update_editor_button_states()

        self._update_map_cursor()

    # --- Palette Conversion Helpers ---
    def _hex_to_rgb7(self, hex_color):
        try:
            if not isinstance(hex_color, str):
                raise TypeError("Input must be a string.")
            if not hex_color.startswith("#") or len(hex_color) != 7:
                raise ValueError(f"Input '{hex_color}' is not a valid #RRGGBB format.")
            lookup_hex = hex_color.lower()
            idx512 = msx2_512_colors_hex.index(lookup_hex)
            return msx2_512_colors_rgb7[idx512]
        except ValueError:
            print(
                f"Warning: Could not find exact MSX2 RGB7 mapping for hex '{hex_color}'. Returning (0,0,0)."
            )
            return (0, 0, 0)
        except TypeError as e:
            print(f"Error in _hex_to_rgb7: Input type error for '{hex_color}'. {e}")
            return (0, 0, 0)
        except Exception as e:
            print(f"Unexpected error in _hex_to_rgb7 for '{hex_color}': {e}")
            return (0, 0, 0)

    def _rgb7_to_hex(self, r, g, b):
        try:
            safe_r = max(0, min(7, int(r)))
            safe_g = max(0, min(7, int(g)))
            safe_b = max(0, min(7, int(b)))
            r_255 = min(255, safe_r * 36)
            g_255 = min(255, safe_g * 36)
            b_255 = min(255, safe_b * 36)
            hex_color = f"#{r_255:02x}{g_255:02x}{b_255:02x}"
            return hex_color
        except (ValueError, TypeError) as e:
            print(f"Error in _rgb7_to_hex converting input ({r},{g},{b}): {e}")
            return "#000000"
        except Exception as e:
            print(f"Unexpected error in _rgb7_to_hex for ({r},{g},{b}): {e}")
            return "#000000"

    # --- Cache Management ---
    def invalidate_tile_cache(self, tile_index):
        keys_to_remove = [k for k in self.tile_image_cache if k[0] == tile_index]
        for key in keys_to_remove:
            self.tile_image_cache.pop(key, None)
        for st_index in range(num_supertiles):
            definition = supertiles_data[st_index]
            used = False
            for r in range(SUPERTILE_GRID_DIM):
                for c in range(SUPERTILE_GRID_DIM):
                    if definition[r][c] == tile_index:
                        used = True
                        break
                if used:
                    break
            if used:
                self.invalidate_supertile_cache(st_index)

    def invalidate_supertile_cache(self, supertile_index):
        keys_to_remove = [
            k for k in self.supertile_image_cache if k[0] == supertile_index
        ]
        for key in keys_to_remove:
            self.supertile_image_cache.pop(key, None)

    def clear_all_caches(self):
        self.tile_image_cache.clear()
        self.supertile_image_cache.clear()

    # --- Image Generation ---
    def create_tile_image(self, tile_index, size):
        cache_key = (tile_index, size)
        if cache_key in self.tile_image_cache:
            return self.tile_image_cache[cache_key]
        render_size = max(1, int(size))
        img = tk.PhotoImage(width=render_size, height=render_size)
        if not (0 <= tile_index < num_tiles_in_set):
            img.put(INVALID_TILE_COLOR, to=(0, 0, render_size, render_size))
            self.tile_image_cache[cache_key] = img
            return img
        pattern = tileset_patterns[tile_index]
        colors = tileset_colors[tile_index]
        pixel_w_ratio = TILE_WIDTH / render_size
        pixel_h_ratio = TILE_HEIGHT / render_size
        for y in range(render_size):
            tile_r = min(TILE_HEIGHT - 1, int(y * pixel_h_ratio))
            try:
                fg_idx, bg_idx = colors[tile_r]
                fg_color = self.active_msx_palette[fg_idx]
                bg_color = self.active_msx_palette[bg_idx]
            except IndexError:
                fg_color, bg_color = INVALID_TILE_COLOR, INVALID_TILE_COLOR
            row_colors_hex = []
            for x in range(render_size):
                tile_c = min(TILE_WIDTH - 1, int(x * pixel_w_ratio))
                try:
                    pixel_val = pattern[tile_r][tile_c]
                except IndexError:
                    pixel_val = 0
                color_hex = fg_color if pixel_val == 1 else bg_color
                row_colors_hex.append(color_hex)
            try:
                img.put("{" + " ".join(row_colors_hex) + "}", to=(0, y))
            except tk.TclError as e:
                print(
                    f"Warning [create_tile_image]: TclError tile {tile_index} size {size} row {y}: {e}"
                )
                if row_colors_hex:
                    img.put(row_colors_hex[0], to=(0, y, render_size, y + 1))
        self.tile_image_cache[cache_key] = img
        return img

    def create_supertile_image(self, supertile_index, total_size):
        cache_key = (supertile_index, total_size)
        if cache_key in self.supertile_image_cache:
            return self.supertile_image_cache[cache_key]
        render_size = max(1, int(total_size))
        img = tk.PhotoImage(width=render_size, height=render_size)
        if not (0 <= supertile_index < num_supertiles):
            img.put(INVALID_SUPERTILE_COLOR, to=(0, 0, render_size, render_size))
            self.supertile_image_cache[cache_key] = img
            return img
        definition = supertiles_data[supertile_index]
        mini_tile_size_float = render_size / SUPERTILE_GRID_DIM
        if mini_tile_size_float < 1:
            print(
                f"Warning [create_supertile_image]: ST {supertile_index} size {total_size} -> mini-tiles too small."
            )
            img.put(INVALID_SUPERTILE_COLOR, to=(0, 0, render_size, render_size))
            self.supertile_image_cache[cache_key] = img
            return img
        mini_tile_pixel_h_ratio = TILE_HEIGHT / mini_tile_size_float
        mini_tile_pixel_w_ratio = TILE_WIDTH / mini_tile_size_float
        for y in range(render_size):
            mini_tile_r = min(SUPERTILE_GRID_DIM - 1, int(y / mini_tile_size_float))
            y_in_mini_render = y % mini_tile_size_float
            row_colors_hex = []
            for x in range(render_size):
                mini_tile_c = min(SUPERTILE_GRID_DIM - 1, int(x / mini_tile_size_float))
                x_in_mini_render = x % mini_tile_size_float
                tile_idx = definition[mini_tile_r][mini_tile_c]
                pixel_color_hex = INVALID_TILE_COLOR  # Default
                if 0 <= tile_idx < num_tiles_in_set:
                    tile_r = min(
                        TILE_HEIGHT - 1, int(y_in_mini_render * mini_tile_pixel_h_ratio)
                    )
                    tile_c = min(
                        TILE_WIDTH - 1, int(x_in_mini_render * mini_tile_pixel_w_ratio)
                    )
                    try:
                        pattern_row = tileset_patterns[tile_idx][tile_r]
                        colors_row = tileset_colors[tile_idx][tile_r]
                        fg_idx = colors_row[0]
                        bg_idx = colors_row[1]
                        fg_color = self.active_msx_palette[fg_idx]
                        bg_color = self.active_msx_palette[bg_idx]
                        pixel_val = pattern_row[tile_c]
                        pixel_color_hex = fg_color if pixel_val == 1 else bg_color
                    except IndexError:
                        print(
                            f"Warning [create_supertile_image]: IndexError T:{tile_idx} P:[{tile_r},{tile_c}] PaletteIdx:[{fg_idx},{bg_idx}]"
                        )
                        pixel_color_hex = INVALID_TILE_COLOR
                row_colors_hex.append(pixel_color_hex)
            try:
                img.put("{" + " ".join(row_colors_hex) + "}", to=(0, y))
            except tk.TclError as e:
                print(
                    f"Warning [create_supertile_image]: TclError ST {supertile_index} size {total_size} row {y}: {e}"
                )
                if row_colors_hex:
                    img.put(row_colors_hex[0], to=(0, y, render_size, y + 1))
        self.supertile_image_cache[cache_key] = img
        return img

    # --- Menu Creation ---
    def create_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # --- File Menu ---
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(
            label="New Project (All)", command=self.new_project, accelerator="Ctrl+N"
        )
        file_menu.add_separator()
        file_menu.add_command(
            label="Open Project...", command=self.open_project, accelerator="Ctrl+O"
        )
        file_menu.add_command(
            label="Save Project", command=self.save_project, accelerator="Ctrl+S"
        )
        file_menu.add_command(
            label="Save Project As...",
            command=self.save_project_as,
            accelerator="Ctrl+Shift+S",
        )
        file_menu.add_separator()
        file_menu.add_command(
            label="Open Palette (.msxpal)...", command=self.open_palette
        )
        file_menu.add_command(
            label="Save Palette (.msxpal)...", command=self.save_palette
        )
        file_menu.add_separator()
        file_menu.add_command(
            label="Open Tileset (.SC4Tiles)...", command=self.open_tileset
        )
        file_menu.add_command(
            label="Save Tileset (.SC4Tiles)...", command=self.save_tileset
        )
        file_menu.add_separator()
        file_menu.add_command(
            label="Open Supertiles (.SC4Super)...", command=self.open_supertiles
        )
        file_menu.add_command(
            label="Save Supertiles (.SC4Super)...", command=self.save_supertiles
        )
        file_menu.add_separator()
        file_menu.add_command(label="Open Map (.SC4Map)...", command=self.open_map)
        file_menu.add_command(label="Save Map (.SC4Map)...", command=self.save_map)
        file_menu.add_separator()
        file_menu.add_command(
            label="Exit", command=self.root.quit, accelerator="Ctrl+Q"
        )

        # --- Edit Menu (Modified) ---
        self.edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=self.edit_menu)

        self.edit_menu.add_command(
            label="Copy",
            command=self.handle_generic_copy,
            state=tk.DISABLED,
            accelerator="Ctrl+C",
        )
        self.copy_menu_item_index = self.edit_menu.index(tk.END)

        self.edit_menu.add_command(
            label="Paste",
            command=self.handle_generic_paste,
            state=tk.DISABLED,
            accelerator="Ctrl+V",
        )
        self.paste_menu_item_index = self.edit_menu.index(tk.END)

        self.edit_menu.add_separator()
        self.edit_menu.add_command(
            label="Clear Current Tile", command=self.clear_current_tile
        )
        self.edit_menu.add_command(
            label="Clear Current Supertile", command=self.clear_current_supertile
        )
        self.edit_menu.add_command(label="Clear Map", command=self.clear_map)
        self.edit_menu.add_separator()
        self.edit_menu.add_command(
            label="Set Tileset Size...", command=self.set_tileset_size
        )
        self.edit_menu.add_command(
            label="Set Supertile Count...", command=self.set_supertile_count
        )
        self.edit_menu.add_command(
            label="Set Map Dimensions...", command=self.set_map_dimensions
        )

        # --- View Menu ---
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(
            label="Show/Hide Minimap", command=self.toggle_minimap, accelerator="Ctrl+M"
        )

        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About...", command=self.show_about_box)

    # --- Widget Creation ---
    def create_palette_editor_widgets(self, parent_frame):
        main_frame = ttk.Frame(parent_frame)
        main_frame.pack(expand=True, fill="both")
        left_frame = ttk.Frame(main_frame, padding=5)
        left_frame.grid(row=0, column=0, sticky="ns")
        right_frame = ttk.Frame(main_frame, padding=5)
        right_frame.grid(row=0, column=1, sticky="nsew")
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_columnconfigure(0, weight=0)
        main_frame.grid_columnconfigure(1, weight=1)
        # Left Frame Contents
        current_palette_frame = ttk.LabelFrame(
            left_frame, text="Active Palette (16 colors)"
        )
        current_palette_frame.pack(pady=(0, 10), fill="x")
        cp_canvas_width = 4 * (CURRENT_PALETTE_SLOT_SIZE + 2) + 2
        cp_canvas_height = 4 * (CURRENT_PALETTE_SLOT_SIZE + 2) + 2
        self.current_palette_canvas = tk.Canvas(
            current_palette_frame,
            width=cp_canvas_width,
            height=cp_canvas_height,
            borderwidth=0,
            highlightthickness=0,
        )
        self.current_palette_canvas.pack()
        self.current_palette_canvas.bind(
            "<Button-1>", self.handle_current_palette_click
        )
        info_frame = ttk.LabelFrame(left_frame, text="Selected Slot Info")
        info_frame.pack(pady=(0, 10), fill="x")
        self.selected_slot_label = ttk.Label(info_frame, text="Slot: 0")
        self.selected_slot_label.grid(
            row=0, column=0, columnspan=3, sticky="w", padx=5, pady=2
        )
        self.selected_slot_color_label = tk.Label(
            info_frame, text="      ", bg="#000000", relief="sunken", width=6
        )
        self.selected_slot_color_label.grid(row=1, column=0, padx=5, pady=2)
        self.selected_slot_rgb_label = ttk.Label(info_frame, text="RGB: #000000")
        self.selected_slot_rgb_label.grid(
            row=1, column=1, columnspan=2, sticky="w", padx=5
        )
        rgb_frame = ttk.LabelFrame(left_frame, text="Set Color (RGB 0-7)")
        rgb_frame.pack(pady=(0, 10), fill="x")
        r_label = ttk.Label(rgb_frame, text="R:")
        r_label.grid(row=0, column=0, padx=(5, 0))
        self.rgb_r_var = tk.StringVar(value="0")
        self.rgb_r_entry = ttk.Entry(rgb_frame, textvariable=self.rgb_r_var, width=2)
        self.rgb_r_entry.grid(row=0, column=1)
        g_label = ttk.Label(rgb_frame, text="G:")
        g_label.grid(row=0, column=2, padx=(5, 0))
        self.rgb_g_var = tk.StringVar(value="0")
        self.rgb_g_entry = ttk.Entry(rgb_frame, textvariable=self.rgb_g_var, width=2)
        self.rgb_g_entry.grid(row=0, column=3)
        b_label = ttk.Label(rgb_frame, text="B:")
        b_label.grid(row=0, column=4, padx=(5, 0))
        self.rgb_b_var = tk.StringVar(value="0")
        self.rgb_b_entry = ttk.Entry(rgb_frame, textvariable=self.rgb_b_var, width=2)
        self.rgb_b_entry.grid(row=0, column=5)
        apply_rgb_button = ttk.Button(
            rgb_frame, text="Set", command=self.handle_rgb_apply
        )
        apply_rgb_button.grid(row=0, column=6, padx=5, pady=5)
        reset_palette_button = ttk.Button(
            left_frame,
            text="Reset to MSX2 Default",
            command=self.reset_palette_to_default,
        )
        reset_palette_button.pack(pady=(0, 5), fill="x")
        # Right Frame Contents
        picker_frame = ttk.LabelFrame(right_frame, text="MSX2 512 Color Picker")
        picker_frame.pack(expand=True, fill="both")
        picker_canvas_width = MSX2_PICKER_COLS * (MSX2_PICKER_SQUARE_SIZE + 1) + 1
        picker_canvas_height = MSX2_PICKER_ROWS * (MSX2_PICKER_SQUARE_SIZE + 1) + 1
        picker_hbar = ttk.Scrollbar(picker_frame, orient=tk.HORIZONTAL)
        picker_vbar = ttk.Scrollbar(picker_frame, orient=tk.VERTICAL)
        self.msx2_picker_canvas = tk.Canvas(
            picker_frame,
            bg="lightgrey",
            scrollregion=(0, 0, picker_canvas_width, picker_canvas_height),
            xscrollcommand=picker_hbar.set,
            yscrollcommand=picker_vbar.set,
        )
        picker_hbar.config(command=self.msx2_picker_canvas.xview)
        picker_vbar.config(command=self.msx2_picker_canvas.yview)
        self.msx2_picker_canvas.grid(row=0, column=0, sticky="nsew")
        picker_vbar.grid(row=0, column=1, sticky="ns")
        picker_hbar.grid(row=1, column=0, sticky="ew")
        picker_frame.grid_rowconfigure(0, weight=1)
        picker_frame.grid_columnconfigure(0, weight=1)
        self.msx2_picker_canvas.bind("<Button-1>", self.handle_512_picker_click)
        self.draw_512_picker()

    def create_tile_editor_widgets(self, parent_frame):
        main_frame = ttk.Frame(parent_frame)
        main_frame.pack(expand=True, fill="both")

        # Left Frame (Editor, Attributes, Transform)
        left_frame = ttk.Frame(main_frame)
        left_frame.grid(row=0, column=0, sticky=tk.N, padx=(0, 10))

        editor_frame = ttk.LabelFrame(
            left_frame, text="Tile Editor (Left: FG, Right: BG)"
        )
        editor_frame.grid(row=0, column=0, pady=(0, 10), sticky="ew")
        self.editor_canvas = tk.Canvas(
            editor_frame,
            width=TILE_WIDTH * EDITOR_PIXEL_SIZE,
            height=TILE_HEIGHT * EDITOR_PIXEL_SIZE,
            bg="grey",
        )
        self.editor_canvas.grid(row=0, column=0)
        self.editor_canvas.bind("<Button-1>", self.handle_editor_click)
        self.editor_canvas.bind("<B1-Motion>", self.handle_editor_drag)
        self.editor_canvas.bind(
            "<Button-3>", self.handle_editor_click
        )  # Keep existing right-click for BG
        self.editor_canvas.bind("<B3-Motion>", self.handle_editor_drag)
        # --- vvv ADD CURSOR BINDINGS vvv ---
        self.editor_canvas.bind("<Enter>", self._set_pencil_cursor)
        self.editor_canvas.bind("<Leave>", self._reset_cursor)
        # --- ^^^ ADD CURSOR BINDINGS ^^^ ---

        attr_frame = ttk.LabelFrame(left_frame, text="Row Colors (Click to set FG/BG)")
        attr_frame.grid(row=1, column=0, pady=(0, 10), sticky="ew")
        self.attr_row_frames = []
        self.attr_fg_labels = []
        self.attr_bg_labels = []
        for r in range(TILE_HEIGHT):
            row_f = ttk.Frame(attr_frame)
            row_f.grid(row=r, column=0, sticky=tk.W, pady=1)
            row_label = ttk.Label(row_f, text=f"{r}:")
            row_label.grid(row=0, column=0, padx=(0, 5))
            fg_label = tk.Label(
                row_f, text=" FG ", width=3, relief="raised", borderwidth=2
            )
            fg_label.grid(row=0, column=1, padx=(0, 2))
            fg_label.bind("<Button-1>", lambda e, row=r: self.set_row_color(row, "fg"))
            self.attr_fg_labels.append(fg_label)
            bg_label = tk.Label(
                row_f, text=" BG ", width=3, relief="raised", borderwidth=2
            )
            bg_label.grid(row=0, column=2)
            bg_label.bind("<Button-1>", lambda e, row=r: self.set_row_color(row, "bg"))
            self.attr_bg_labels.append(bg_label)
            self.attr_row_frames.append(row_f)

        transform_frame = ttk.LabelFrame(left_frame, text="Transform")
        transform_frame.grid(row=2, column=0, pady=(0, 10), sticky="ew")
        flip_h_button = ttk.Button(
            transform_frame, text="Flip H", command=self.flip_tile_horizontal
        )
        flip_h_button.grid(row=0, column=0, padx=3, pady=3)
        flip_v_button = ttk.Button(
            transform_frame, text="Flip V", command=self.flip_tile_vertical
        )
        flip_v_button.grid(row=0, column=1, padx=3, pady=3)
        rotate_button = ttk.Button(
            transform_frame, text="Rotate", command=self.rotate_tile_90cw
        )
        rotate_button.grid(row=0, column=2, padx=3, pady=3)
        shift_up_button = ttk.Button(
            transform_frame, text="Shift Up", command=self.shift_tile_up
        )
        shift_up_button.grid(row=1, column=0, padx=3, pady=3)
        shift_down_button = ttk.Button(
            transform_frame, text="Shift Down", command=self.shift_tile_down
        )
        shift_down_button.grid(row=1, column=1, padx=3, pady=3)
        shift_left_button = ttk.Button(
            transform_frame, text="Shift Left", command=self.shift_tile_left
        )
        shift_left_button.grid(row=1, column=2, padx=3, pady=3)
        shift_right_button = ttk.Button(
            transform_frame, text="Shift Right", command=self.shift_tile_right
        )
        shift_right_button.grid(row=1, column=3, padx=3, pady=3)

        # Right Frame (Palette, Tileset Viewer, Buttons)
        right_frame = ttk.Frame(main_frame)
        right_frame.grid(
            row=0, column=1, sticky=(tk.N, tk.S, tk.W, tk.E)
        )  # Added sticky EW
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_columnconfigure(0, weight=0)  # Left frame fixed width
        main_frame.grid_columnconfigure(
            1, weight=1
        )  # Make right frame expand horizontally

        palette_frame = ttk.LabelFrame(
            right_frame, text="Color Selector (Click to draw)"
        )
        palette_frame.grid(row=0, column=0, pady=(0, 10), sticky=(tk.N, tk.W, tk.E))
        self.tile_editor_palette_canvas = tk.Canvas(
            palette_frame,
            width=4 * (PALETTE_SQUARE_SIZE + 2),
            height=4 * (PALETTE_SQUARE_SIZE + 2),
            borderwidth=0,
            highlightthickness=0,
        )
        self.tile_editor_palette_canvas.grid(row=0, column=0)
        self.tile_editor_palette_canvas.bind(
            "<Button-1>", self.handle_tile_editor_palette_click
        )

        viewer_frame = ttk.LabelFrame(right_frame, text="Tileset")
        # Make viewer frame expand vertically and horizontally within right_frame
        viewer_frame.grid(row=1, column=0, sticky=(tk.N, tk.S, tk.W, tk.E))
        right_frame.grid_rowconfigure(0, weight=0)  # Palette fixed height
        right_frame.grid_rowconfigure(1, weight=1)  # Viewer frame gets vertical weight
        right_frame.grid_rowconfigure(2, weight=0)  # Button frame fixed height
        right_frame.grid_rowconfigure(3, weight=0)  # Info label fixed height
        right_frame.grid_columnconfigure(
            0, weight=1
        )  # Viewer frame gets horizontal weight

        viewer_canvas_width = NUM_TILES_ACROSS * (VIEWER_TILE_SIZE + 1) + 1
        num_rows_in_viewer = math.ceil(MAX_TILES / NUM_TILES_ACROSS)
        viewer_canvas_height = num_rows_in_viewer * (VIEWER_TILE_SIZE + 1) + 1
        viewer_hbar = ttk.Scrollbar(viewer_frame, orient=tk.HORIZONTAL)
        viewer_vbar = ttk.Scrollbar(viewer_frame, orient=tk.VERTICAL)
        self.tileset_canvas = tk.Canvas(
            viewer_frame,
            bg="lightgrey",
            scrollregion=(0, 0, viewer_canvas_width, viewer_canvas_height),
            xscrollcommand=viewer_hbar.set,
            yscrollcommand=viewer_vbar.set,
        )
        viewer_hbar.config(command=self.tileset_canvas.xview)
        viewer_vbar.config(command=self.tileset_canvas.yview)
        self.tileset_canvas.grid(row=0, column=0, sticky=(tk.N, tk.S, tk.W, tk.E))
        viewer_vbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        viewer_hbar.grid(row=1, column=0, sticky=(tk.W, tk.E))
        viewer_frame.grid_rowconfigure(0, weight=1)
        viewer_frame.grid_columnconfigure(0, weight=1)

        # ---vvv Drag/Drop BINDINGS vvv---
        self.tileset_canvas.bind("<Button-1>", self.handle_tileset_click)
        self.tileset_canvas.bind("<B1-Motion>", self.handle_viewer_drag_motion)
        self.tileset_canvas.bind("<ButtonRelease-1>", self.handle_viewer_drag_release)
        # ---^^^ Drag/Drop BINDINGS ^^^---

        # --- Button Frame --- (Use a frame for layout)
        tile_button_frame = ttk.Frame(right_frame)
        tile_button_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(5, 0))

        # Store button references on self
        self.add_tile_button = ttk.Button(
            tile_button_frame, text="Add New", command=self.handle_add_tile
        )
        self.add_tile_button.pack(side=tk.LEFT, padx=(0, 3))

        self.insert_tile_button = ttk.Button(
            tile_button_frame, text="Insert", command=self.handle_insert_tile
        )
        self.insert_tile_button.pack(side=tk.LEFT, padx=3)

        self.delete_tile_button = ttk.Button(
            tile_button_frame, text="Delete", command=self.handle_delete_tile
        )
        self.delete_tile_button.pack(side=tk.LEFT, padx=3)
        # --- End Button Frame ---

        self.tile_info_label = ttk.Label(right_frame, text="Tile: 0/0")
        self.tile_info_label.grid(row=3, column=0, sticky=tk.W, pady=(2, 0))

    def create_supertile_editor_widgets(self, parent_frame):
        main_frame = ttk.Frame(parent_frame)
        main_frame.pack(expand=True, fill="both")
        left_frame = ttk.Frame(main_frame)
        left_frame.grid(row=0, column=0, sticky=tk.N, padx=(0, 10))  # Keep sticky N

        # Supertile Definition Frame (Row 0)
        def_frame = ttk.LabelFrame(
            left_frame, text="Supertile Definition (Click to place selected tile)"
        )
        def_frame.grid(row=0, column=0, pady=(0, 10), sticky="ew")  # Add sticky ew
        def_canvas_size = SUPERTILE_GRID_DIM * SUPERTILE_DEF_TILE_SIZE
        self.supertile_def_canvas = tk.Canvas(
            def_frame, width=def_canvas_size, height=def_canvas_size, bg="darkgrey"
        )
        self.supertile_def_canvas.grid(row=0, column=0)
        self.supertile_def_canvas.bind("<Button-1>", self.handle_supertile_def_click)
        self.supertile_def_canvas.bind("<B1-Motion>", self.handle_supertile_def_drag)
        self.supertile_def_canvas.bind(
            "<ButtonRelease-1>", self.handle_supertile_def_release
        )
        self.supertile_def_canvas.bind(
            "<Button-3>", self.handle_supertile_def_right_click
        )  # Eyedropper
        # --- vvv ADD CURSOR BINDINGS vvv ---
        self.supertile_def_canvas.bind("<Enter>", self._set_pencil_cursor)
        self.supertile_def_canvas.bind("<Leave>", self._reset_cursor)
        # --- ^^^ ADD CURSOR BINDINGS ^^^ ---

        # Info Labels Frame (Combine into one frame for better layout) (Row 1)
        info_labels_frame = ttk.Frame(left_frame)
        info_labels_frame.grid(
            row=1, column=0, pady=(0, 5), sticky="ew"
        )  # Add sticky ew
        self.supertile_def_info_label = ttk.Label(
            info_labels_frame, text=f"Editing Supertile: {current_supertile_index}"
        )
        self.supertile_def_info_label.pack(anchor=tk.W)  # Use pack within this frame
        self.supertile_tile_select_label = ttk.Label(
            info_labels_frame,
            text=f"Selected Tile for Placing: {selected_tile_for_supertile}",
        )
        self.supertile_tile_select_label.pack(anchor=tk.W)  # Use pack

        # Transformation Frame (Row 2)
        st_transform_frame = ttk.LabelFrame(left_frame, text="Transform Supertile")
        st_transform_frame.grid(
            row=2, column=0, pady=(5, 10), sticky="ew"
        )  # Added top padding

        # Row 0: Flip/Rotate
        st_flip_h_button = ttk.Button(
            st_transform_frame, text="Flip H", command=self.flip_supertile_horizontal
        )
        st_flip_h_button.grid(row=0, column=0, padx=3, pady=(5, 3))  # Added top padding
        st_flip_v_button = ttk.Button(
            st_transform_frame, text="Flip V", command=self.flip_supertile_vertical
        )
        st_flip_v_button.grid(row=0, column=1, padx=3, pady=(5, 3))
        st_rotate_button = ttk.Button(
            st_transform_frame, text="Rotate", command=self.rotate_supertile_90cw
        )
        st_rotate_button.grid(row=0, column=2, padx=3, pady=(5, 3))

        # Row 1: Shift Buttons
        st_shift_up_button = ttk.Button(
            st_transform_frame, text="Shift Up", command=self.shift_supertile_up
        )
        st_shift_up_button.grid(row=1, column=0, padx=3, pady=3)
        st_shift_down_button = ttk.Button(
            st_transform_frame, text="Shift Down", command=self.shift_supertile_down
        )
        st_shift_down_button.grid(row=1, column=1, padx=3, pady=3)
        st_shift_left_button = ttk.Button(
            st_transform_frame, text="Shift Left", command=self.shift_supertile_left
        )
        st_shift_left_button.grid(row=1, column=2, padx=3, pady=3)
        st_shift_right_button = ttk.Button(
            st_transform_frame, text="Shift Right", command=self.shift_supertile_right
        )
        st_shift_right_button.grid(row=1, column=3, padx=3, pady=3)  # Added 4th column
        # --- End Transformation Frame ---

        # Right Frame
        right_frame = ttk.Frame(main_frame)
        right_frame.grid(row=0, column=1, sticky=(tk.N, tk.S, tk.W, tk.E))
        main_frame.grid_columnconfigure(1, weight=1)  # Right frame expands
        main_frame.grid_rowconfigure(0, weight=1)  # Row 0 should have weight

        # Tileset Viewer Frame
        tileset_viewer_frame = ttk.LabelFrame(
            right_frame, text="Tileset (Click to select tile for definition)"
        )
        tileset_viewer_frame.grid(
            row=0, column=0, sticky=(tk.N, tk.S, tk.W, tk.E), pady=(0, 10)
        )
        right_frame.grid_rowconfigure(0, weight=1)  # Tileset viewer gets weight

        # Calculate dimensions for the Tileset viewer canvas
        viewer_canvas_width = NUM_TILES_ACROSS * (VIEWER_TILE_SIZE + 1) + 1
        num_rows_in_viewer = math.ceil(MAX_TILES / NUM_TILES_ACROSS)
        viewer_canvas_height = num_rows_in_viewer * (VIEWER_TILE_SIZE + 1) + 1

        # Setup scrollbars and canvas for the tileset viewer
        st_viewer_hbar = ttk.Scrollbar(tileset_viewer_frame, orient=tk.HORIZONTAL)
        st_viewer_vbar = ttk.Scrollbar(tileset_viewer_frame, orient=tk.VERTICAL)
        self.st_tileset_canvas = tk.Canvas(
            tileset_viewer_frame,
            bg="lightgrey",
            scrollregion=(0, 0, viewer_canvas_width, viewer_canvas_height),
            xscrollcommand=st_viewer_hbar.set,
            yscrollcommand=st_viewer_vbar.set,
        )

        # Configure scrollbars and grid layout
        st_viewer_hbar.config(command=self.st_tileset_canvas.xview)
        st_viewer_vbar.config(command=self.st_tileset_canvas.yview)
        self.st_tileset_canvas.grid(row=0, column=0, sticky=(tk.N, tk.S, tk.W, tk.E))
        st_viewer_vbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        st_viewer_hbar.grid(row=1, column=0, sticky=(tk.W, tk.E))
        tileset_viewer_frame.grid_rowconfigure(0, weight=1)
        tileset_viewer_frame.grid_columnconfigure(0, weight=1)

        # ---vvv Drag/Drop BINDINGS for st_tileset_canvas vvv---
        self.st_tileset_canvas.bind("<Button-1>", self.handle_st_tileset_click)
        self.st_tileset_canvas.bind("<B1-Motion>", self.handle_viewer_drag_motion)
        self.st_tileset_canvas.bind(
            "<ButtonRelease-1>", self.handle_viewer_drag_release
        )
        # ---^^^ Drag/Drop BINDINGS for st_tileset_canvas ^^^---

        # Supertile Selector Frame
        st_selector_frame = ttk.LabelFrame(
            right_frame, text="Supertile Selector (Click to edit)"
        )
        st_selector_frame.grid(row=1, column=0, sticky=(tk.N, tk.S, tk.W, tk.E))
        right_frame.grid_rowconfigure(1, weight=1)  # Supertile selector gets weight

        # Calculate dimensions for the Supertile Selector canvas
        st_sel_canvas_width = (
            NUM_SUPERTILES_ACROSS * (SUPERTILE_SELECTOR_PREVIEW_SIZE + 1) + 1
        )
        st_sel_num_rows = math.ceil(MAX_SUPERTILES / NUM_SUPERTILES_ACROSS)
        st_sel_canvas_height = (
            st_sel_num_rows * (SUPERTILE_SELECTOR_PREVIEW_SIZE + 1) + 1
        )

        # Setup scrollbars and canvas for the supertile selector
        st_sel_hbar = ttk.Scrollbar(st_selector_frame, orient=tk.HORIZONTAL)
        st_sel_vbar = ttk.Scrollbar(st_selector_frame, orient=tk.VERTICAL)
        self.supertile_selector_canvas = tk.Canvas(
            st_selector_frame,
            bg="lightgrey",
            scrollregion=(0, 0, st_sel_canvas_width, st_sel_canvas_height),
            xscrollcommand=st_sel_hbar.set,
            yscrollcommand=st_sel_vbar.set,
        )
        st_sel_hbar.config(command=self.supertile_selector_canvas.xview)
        st_sel_vbar.config(command=self.supertile_selector_canvas.yview)
        self.supertile_selector_canvas.grid(
            row=0, column=0, sticky=(tk.N, tk.S, tk.W, tk.E)
        )
        st_sel_vbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        st_sel_hbar.grid(row=1, column=0, sticky=(tk.W, tk.E))
        st_selector_frame.grid_rowconfigure(0, weight=1)
        st_selector_frame.grid_columnconfigure(0, weight=1)

        # ---vvv Drag/Drop BINDINGS for supertile_selector_canvas vvv---
        self.supertile_selector_canvas.bind(
            "<Button-1>", self.handle_supertile_selector_click
        )
        self.supertile_selector_canvas.bind(
            "<B1-Motion>", self.handle_viewer_drag_motion
        )
        self.supertile_selector_canvas.bind(
            "<ButtonRelease-1>", self.handle_viewer_drag_release
        )
        # ---^^^ Drag/Drop BINDINGS for supertile_selector_canvas ^^^---

        # Bottom Buttons/Labels Frame (Combine into one frame for better layout) (Row 2)
        bottom_controls_frame = ttk.Frame(right_frame)
        bottom_controls_frame.grid(
            row=2, column=0, sticky="ew", pady=(5, 0)
        )  # Use sticky ew
        right_frame.grid_rowconfigure(2, weight=0)  # Button frame fixed height

        # Store button references on self
        self.add_supertile_button = ttk.Button(
            bottom_controls_frame, text="Add New", command=self.handle_add_supertile
        )
        self.add_supertile_button.pack(side=tk.LEFT, padx=(0, 3))

        self.insert_supertile_button = ttk.Button(
            bottom_controls_frame, text="Insert", command=self.handle_insert_supertile
        )
        self.insert_supertile_button.pack(side=tk.LEFT, padx=3)

        self.delete_supertile_button = ttk.Button(
            bottom_controls_frame, text="Delete", command=self.handle_delete_supertile
        )
        self.delete_supertile_button.pack(side=tk.LEFT, padx=3)

        self.supertile_sel_info_label = ttk.Label(
            bottom_controls_frame, text=f"Supertiles: {num_supertiles}"
        )
        self.supertile_sel_info_label.pack(side=tk.LEFT, anchor=tk.W, padx=(10, 0))

    def create_map_editor_widgets(self, parent_frame):
        # Create the main container frame for this tab
        main_frame = ttk.Frame(parent_frame)
        main_frame.pack(expand=True, fill="both")

        # --- Create Left and Right Columns ---
        left_frame = ttk.Frame(main_frame)
        left_frame.grid(row=0, column=0, sticky=(tk.N, tk.S, tk.W, tk.E), padx=(0, 10))
        right_frame = ttk.Frame(main_frame)
        right_frame.grid(row=0, column=1, sticky=(tk.N, tk.S))

        # --- Configure Main Frame Grid Weights ---
        main_frame.grid_columnconfigure(0, weight=1)  # left_frame expands horizontally
        main_frame.grid_columnconfigure(1, weight=0)  # right_frame fixed width
        main_frame.grid_rowconfigure(0, weight=1)  # Row 0 expands vertically

        # --- Configure Left Frame Contents ---

        # Row 0: Map Size and Zoom Controls
        controls_frame = ttk.Frame(left_frame)
        controls_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        # Map Size
        size_label = ttk.Label(controls_frame, text="Map Size:")
        size_label.grid(row=0, column=0, padx=(0, 5), pady=2)
        self.map_size_label = ttk.Label(
            controls_frame, text=f"{map_width} x {map_height}"
        )
        self.map_size_label.grid(row=0, column=1, padx=(0, 10), pady=2)
        # Zoom
        zoom_frame = ttk.Frame(controls_frame)
        zoom_frame.grid(row=0, column=2, padx=(10, 0), pady=2)
        zoom_out_button = ttk.Button(
            zoom_frame,
            text="-",
            width=2,
            command=lambda: self.change_map_zoom_mult(1 / 1.25),
        )
        zoom_out_button.pack(side=tk.LEFT)
        self.map_zoom_label = ttk.Label(
            zoom_frame, text="100%", width=5, anchor=tk.CENTER
        )
        self.map_zoom_label.pack(side=tk.LEFT, padx=2)
        zoom_in_button = ttk.Button(
            zoom_frame,
            text="+",
            width=2,
            command=lambda: self.change_map_zoom_mult(1.25),
        )
        zoom_in_button.pack(side=tk.LEFT)
        zoom_reset_button = ttk.Button(
            zoom_frame, text="Reset", width=5, command=lambda: self.set_map_zoom(1.0)
        )
        zoom_reset_button.pack(side=tk.LEFT, padx=(5, 0))
        # Coords Label
        self.map_coords_label = ttk.Label(
            controls_frame, text="ST Coords: -, -", width=15
        )
        self.map_coords_label.grid(row=0, column=3, padx=(10, 5), sticky="w")

        # Row 1: Window View Toggle and Size Inputs
        win_controls_frame = ttk.Frame(left_frame)
        win_controls_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        win_view_check = ttk.Checkbutton(
            win_controls_frame,
            text="Show Window View",
            variable=self.show_window_view,
            command=self.toggle_window_view,
        )
        win_view_check.grid(row=0, column=0, padx=5, sticky="w")
        win_w_label = ttk.Label(win_controls_frame, text="Width:")
        win_w_label.grid(row=0, column=1, padx=(10, 0))
        self.win_view_w_entry = ttk.Entry(
            win_controls_frame, textvariable=self.window_view_tile_w, width=4
        )
        self.win_view_w_entry.grid(row=0, column=2)
        win_h_label = ttk.Label(win_controls_frame, text="Height:")
        win_h_label.grid(row=0, column=3, padx=(5, 0))
        self.win_view_h_entry = ttk.Entry(
            win_controls_frame, textvariable=self.window_view_tile_h, width=4
        )
        self.win_view_h_entry.grid(row=0, column=4)
        win_apply_button = ttk.Button(
            win_controls_frame,
            text="Apply Size",
            command=self.apply_window_size_from_entries,
        )
        win_apply_button.grid(row=0, column=5, padx=5)
        self.win_view_w_entry.bind(
            "<Return>", lambda e: self.apply_window_size_from_entries()
        )
        self.win_view_h_entry.bind(
            "<Return>", lambda e: self.apply_window_size_from_entries()
        )

        # Row 2: Grid Controls
        grid_controls_frame = ttk.Frame(left_frame)
        grid_controls_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        st_grid_check = ttk.Checkbutton(
            grid_controls_frame,
            text="Show Supertile Grid (Press 'G' to Cycle Colors)",  # MODIFIED TEXT
            variable=self.show_supertile_grid,
            command=self.toggle_supertile_grid,
        )
        st_grid_check.grid(row=0, column=0, padx=5, sticky="w")

        # Row 3: Map Canvas Frame
        map_canvas_frame = ttk.LabelFrame(left_frame, text="Map")
        map_canvas_frame.grid(row=3, column=0, sticky=(tk.N, tk.S, tk.W, tk.E))

        # --- Configure Left Frame Grid Weights ---
        left_frame.grid_rowconfigure(0, weight=0)
        left_frame.grid_rowconfigure(1, weight=0)
        left_frame.grid_rowconfigure(2, weight=0)
        left_frame.grid_rowconfigure(3, weight=1)  # Canvas frame expands vertically
        left_frame.grid_columnconfigure(0, weight=1)

        # --- Create Map Canvas and Scrollbars ---
        self.map_hbar = ttk.Scrollbar(map_canvas_frame, orient=tk.HORIZONTAL)
        self.map_vbar = ttk.Scrollbar(map_canvas_frame, orient=tk.VERTICAL)
        self.map_canvas = tk.Canvas(
            map_canvas_frame,
            bg="black",
            xscrollcommand=self.map_hbar.set,
            yscrollcommand=self.map_vbar.set,
        )
        self.map_hbar.config(command=self.map_canvas.xview)
        self.map_vbar.config(command=self.map_canvas.yview)
        self.map_canvas.grid(row=0, column=0, sticky=(tk.N, tk.S, tk.W, tk.E))
        self.map_vbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.map_hbar.grid(row=1, column=0, sticky=(tk.W, tk.E))

        # --- Configure Map Canvas Frame Grid Weights ---
        map_canvas_frame.grid_rowconfigure(0, weight=1)
        map_canvas_frame.grid_columnconfigure(0, weight=1)
        map_canvas_frame.grid_rowconfigure(1, weight=0)
        map_canvas_frame.grid_columnconfigure(1, weight=0)

        # --- Configure Right Frame Contents ---
        st_selector_frame = ttk.LabelFrame(
            right_frame, text="Supertile Palette (Click to select for map)"
        )
        st_selector_frame.grid(row=0, column=0, sticky=(tk.N, tk.S, tk.W, tk.E))
        right_frame.grid_rowconfigure(0, weight=1)
        right_frame.grid_rowconfigure(1, weight=0)
        right_frame.grid_columnconfigure(0, weight=1)

        # Supertile Palette Canvas Setup
        st_sel_canvas_width = (
            NUM_SUPERTILES_ACROSS * (SUPERTILE_SELECTOR_PREVIEW_SIZE + 1) + 1
        )
        st_sel_num_rows = math.ceil(MAX_SUPERTILES / NUM_SUPERTILES_ACROSS)
        st_sel_canvas_height = (
            st_sel_num_rows * (SUPERTILE_SELECTOR_PREVIEW_SIZE + 1) + 1
        )
        map_st_sel_hbar = ttk.Scrollbar(st_selector_frame, orient=tk.HORIZONTAL)
        map_st_sel_vbar = ttk.Scrollbar(st_selector_frame, orient=tk.VERTICAL)
        self.map_supertile_selector_canvas = tk.Canvas(
            st_selector_frame,
            bg="lightgrey",
            scrollregion=(0, 0, st_sel_canvas_width, st_sel_canvas_height),
            xscrollcommand=map_st_sel_hbar.set,
            yscrollcommand=map_st_sel_vbar.set,
        )
        map_st_sel_hbar.config(command=self.map_supertile_selector_canvas.xview)
        map_st_sel_vbar.config(command=self.map_supertile_selector_canvas.yview)
        self.map_supertile_selector_canvas.grid(
            row=0, column=0, sticky=(tk.N, tk.S, tk.W, tk.E)
        )
        map_st_sel_vbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        map_st_sel_hbar.grid(row=1, column=0, sticky=(tk.W, tk.E))
        st_selector_frame.grid_rowconfigure(0, weight=1)
        st_selector_frame.grid_columnconfigure(0, weight=1)
        st_selector_frame.grid_rowconfigure(1, weight=0)
        st_selector_frame.grid_columnconfigure(1, weight=0)

        self.map_supertile_selector_canvas.bind(
            "<Button-1>", self.handle_map_supertile_selector_click
        )
        self.map_supertile_selector_canvas.bind(
            "<B1-Motion>", self.handle_viewer_drag_motion
        )
        self.map_supertile_selector_canvas.bind(
            "<ButtonRelease-1>", self.handle_viewer_drag_release
        )

        self.map_supertile_select_label = ttk.Label(
            right_frame,
            text=f"Selected Supertile for Painting: {selected_supertile_for_map}",
        )
        self.map_supertile_select_label.grid(row=1, column=0, sticky=tk.W, pady=(5, 0))

    # --- Use this as the SINGLE definition for setting up bindings ---
    def _setup_map_canvas_bindings(self):
        """Sets up ALL event bindings for the map canvas and related root bindings.
        Includes initial unbind step for robustness.
        """
        canvas = self.map_canvas

        # --- Unbind ALL PREVIOUSLY POTENTIAL MAP CANVAS BINDINGS ---
        canvas.unbind("<Button-1>")
        canvas.unbind("<B1-Motion>")
        canvas.unbind("<ButtonRelease-1>")
        canvas.unbind("<Button-3>")
        canvas.unbind("<Control-ButtonPress-1>")
        canvas.unbind("<Control-B1-Motion>")
        canvas.unbind("<Shift-ButtonPress-1>")  # Unbind potential previous Shift binds
        canvas.unbind("<Shift-B1-Motion>")  # Unbind potential previous Shift binds
        canvas.unbind(
            "<Shift-ButtonRelease-1>"
        )  # Unbind potential previous Shift binds
        canvas.unbind("<Control-MouseWheel>")
        canvas.unbind("<Control-Button-4>")
        canvas.unbind("<Control-Button-5>")
        canvas.unbind("<FocusIn>")
        canvas.unbind("<FocusOut>")
        canvas.unbind("<KeyPress-w>")
        canvas.unbind("<KeyPress-a>")
        canvas.unbind("<KeyPress-s>")
        canvas.unbind("<KeyPress-d>")
        canvas.unbind("<KeyPress-W>")
        canvas.unbind("<KeyPress-A>")
        canvas.unbind("<KeyPress-S>")
        canvas.unbind("<KeyPress-D>")
        canvas.unbind("<KeyPress-Escape>")  # Unbind potential previous Escape binds
        canvas.unbind("<Enter>")
        canvas.unbind("<Leave>")
        canvas.unbind("<Motion>")
        # -------------------------------------------------------------

        # --- Mouse Button 1 (Primary) - Checks Shift/Ctrl internally ---
        canvas.bind("<Button-1>", self.handle_map_click_or_drag_start)
        canvas.bind("<B1-Motion>", self.handle_map_drag)
        canvas.bind("<ButtonRelease-1>", self.handle_map_drag_release)

        # --- Mouse Button 3 (Right-Click for Selection) ---
        canvas.bind("<Button-3>", self.handle_map_canvas_right_click)

        # --- Panning (Ctrl + Mouse Button 1) - Checks Shift internally ---
        canvas.bind("<Control-ButtonPress-1>", self.handle_pan_start)
        canvas.bind("<Control-B1-Motion>", self.handle_pan_motion)

        # --- Selection (Shift + Mouse Button 1) - NEW ---
        canvas.bind("<Shift-ButtonPress-1>", self.handle_map_selection_start)
        canvas.bind("<Shift-B1-Motion>", self.handle_map_selection_motion)
        canvas.bind("<Shift-ButtonRelease-1>", self.handle_map_selection_release)

        # --- Zooming (Ctrl + Mouse Wheel) ---
        canvas.bind(
            "<Control-MouseWheel>", self.handle_map_zoom_scroll
        )  # Windows/macOS
        canvas.bind(
            "<Control-Button-4>", self.handle_map_zoom_scroll
        )  # Linux scroll up
        canvas.bind(
            "<Control-Button-5>", self.handle_map_zoom_scroll
        )  # Linux scroll down

        # --- Keyboard ---
        canvas.bind("<FocusIn>", lambda e: self.map_canvas.focus_set())
        canvas.bind("<FocusOut>", lambda e: self._update_map_cursor())
        canvas.bind("<KeyPress-w>", self.handle_map_keypress)
        canvas.bind("<KeyPress-a>", self.handle_map_keypress)
        canvas.bind("<KeyPress-s>", self.handle_map_keypress)
        canvas.bind("<KeyPress-d>", self.handle_map_keypress)
        canvas.bind("<KeyPress-W>", self.handle_map_keypress)  # Allow uppercase
        canvas.bind("<KeyPress-A>", self.handle_map_keypress)
        canvas.bind("<KeyPress-S>", self.handle_map_keypress)
        canvas.bind("<KeyPress-D>", self.handle_map_keypress)
        canvas.bind(
            "<KeyPress-Escape>", self.handle_map_escape
        )  # NEW: For clearing selection

        # --- Modifier Key State Tracking (Bound to root window) ---
        # Ctrl
        self.root.bind("<KeyPress-Control_L>", self.handle_ctrl_press, add="+")
        self.root.bind("<KeyPress-Control_R>", self.handle_ctrl_press, add="+")
        self.root.bind("<KeyRelease-Control_L>", self.handle_ctrl_release, add="+")
        self.root.bind("<KeyRelease-Control_R>", self.handle_ctrl_release, add="+")
        # Shift - NEW
        self.root.bind("<KeyPress-Shift_L>", self.handle_shift_press, add="+")
        self.root.bind("<KeyPress-Shift_R>", self.handle_shift_press, add="+")
        self.root.bind("<KeyRelease-Shift_L>", self.handle_shift_release, add="+")
        self.root.bind("<KeyRelease-Shift_R>", self.handle_shift_release, add="+")

        # --- Mouse Enter/Leave/Motion Canvas (for cursor updates) ---
        canvas.bind("<Enter>", self.handle_canvas_enter)
        canvas.bind("<Leave>", self.handle_canvas_leave)
        canvas.bind("<Motion>", self._update_map_cursor_and_coords)  # Combine updates

        # --- Scrollbar Interaction (Update minimap) ---
        if hasattr(self, "map_hbar") and self.map_hbar:
            self.map_hbar.bind("<B1-Motion>", lambda e: self.draw_minimap())
            self.map_hbar.bind("<ButtonRelease-1>", lambda e: self.draw_minimap())
        if hasattr(self, "map_vbar") and self.map_vbar:
            self.map_vbar.bind("<B1-Motion>", lambda e: self.draw_minimap())
            self.map_vbar.bind("<ButtonRelease-1>", lambda e: self.draw_minimap())

    # --- Drawing Functions ---
    def update_all_displays(self, changed_level="all"):
        """Updates UI elements ONLY for the currently VISIBLE tab,
        based on the level of change indicated by changed_level.
        Also handles global updates like palette if necessary.
        """
        # Get current visible tab index (safer way)
        current_tab_index = -1
        try:
            if self.notebook and self.notebook.winfo_exists():
                selected_tab = self.notebook.select()
                if selected_tab:
                    current_tab_index = self.notebook.index(selected_tab)
        except tk.TclError:
            print("Warning: Could not get current tab index in update_all_displays.")
            return  # Avoid errors if notebook state is weird

        # --- Always handle Palette changes first, as they affect look of all tabs ---
        palette_changed = changed_level in ["all", "palette"]
        if palette_changed:
            # Update the palette editor widgets regardless of visibility
            # (They are cheap to update and data source for others)
            self.draw_current_palette()
            self.update_palette_info_labels()
            # Cache invalidation for palette changes is handled by the caller
            # (e.g., handle_rgb_apply, reset_palette...)

        # --- Update widgets ONLY for the VISIBLE tab ---

        # Palette Editor Tab (Index 0)
        if current_tab_index == 0:
            # Widgets already updated above if palette_changed is True.
            # No other data changes directly affect only this tab's display.
            pass  # print("Updating Palette Tab (Visible)")

        # Tile Editor Tab (Index 1)
        elif current_tab_index == 1:
            # Update if tile data changed OR palette changed (affects colors)
            if changed_level in ["all", "tile"] or palette_changed:
                # print(f"Updating Tile Tab (Visible), Level: {changed_level}, PaletteChanged: {palette_changed}")
                self.draw_editor_canvas()
                self.draw_attribute_editor()
                self.draw_palette()  # Uses active_msx_palette
                self.draw_tileset_viewer(
                    self.tileset_canvas, current_tile_index
                )  # Main viewer
                self.update_tile_info_label()
                # We intentionally DO NOT update self.st_tileset_canvas here.
                # It will be updated when the Supertile tab becomes visible.

        # Supertile Editor Tab (Index 2)
        elif current_tab_index == 2:
            # Update if supertile data changed, underlying tile data changed, OR palette changed
            if changed_level in ["all", "supertile", "tile"] or palette_changed:
                # print(f"Updating Supertile Tab (Visible), Level: {changed_level}, PaletteChanged: {palette_changed}")
                self.draw_supertile_definition_canvas()  # Uses tiles & palette
                self.draw_tileset_viewer(
                    self.st_tileset_canvas, selected_tile_for_supertile
                )  # Uses tiles & palette
                self.draw_supertile_selector(
                    self.supertile_selector_canvas, current_supertile_index
                )  # Uses tiles & palette
                self.update_supertile_info_labels()
                # We intentionally DO NOT update self.map_supertile_selector_canvas here.

        # Map Editor Tab (Index 3)
        elif current_tab_index == 3:
            # Update if map data changed, underlying supertile/tile data changed, OR palette changed
            if changed_level in ["all", "map", "supertile", "tile"] or palette_changed:
                # print(f"Updating Map Tab (Visible), Level: {changed_level}, PaletteChanged: {palette_changed}")
                # Map canvas redraw is complex, redraw if map changed OR dependencies changed
                self.draw_map_canvas()  # Handles overlays, uses ST/Tiles/Palette
                self.draw_supertile_selector(
                    self.map_supertile_selector_canvas, selected_supertile_for_map
                )  # Uses ST/Tiles/Palette
                self.update_map_info_labels()  # Update size/zoom/window entries
                self.draw_minimap()  # Uses Map/ST/Tiles/Palette

    # ... (draw_editor_canvas, draw_attribute_editor, draw_palette unchanged) ...
    def draw_editor_canvas(self):
        self.editor_canvas.delete("all")
        if not (0 <= current_tile_index < num_tiles_in_set):
            return
        pattern = tileset_patterns[current_tile_index]
        colors = tileset_colors[current_tile_index]
        for r in range(TILE_HEIGHT):
            try:
                fg_idx, bg_idx = colors[r]
                fg_color = self.active_msx_palette[fg_idx]
                bg_color = self.active_msx_palette[bg_idx]
            except IndexError:
                fg_color, bg_color = INVALID_TILE_COLOR, INVALID_TILE_COLOR
            for c in range(TILE_WIDTH):
                try:
                    pixel_val = pattern[r][c]
                except IndexError:
                    pixel_val = 0
                color = fg_color if pixel_val == 1 else bg_color
                x1 = c * EDITOR_PIXEL_SIZE
                y1 = r * EDITOR_PIXEL_SIZE
                x2 = x1 + EDITOR_PIXEL_SIZE
                y2 = y1 + EDITOR_PIXEL_SIZE
                self.editor_canvas.create_rectangle(
                    x1, y1, x2, y2, fill=color, outline="darkgrey", width=1
                )

    def draw_attribute_editor(self):
        if not (0 <= current_tile_index < num_tiles_in_set):
            return
        colors = tileset_colors[current_tile_index]
        for r in range(TILE_HEIGHT):
            try:
                fg_idx, bg_idx = colors[r]
                fg_color_hex = self.active_msx_palette[fg_idx]
                bg_color_hex = self.active_msx_palette[bg_idx]
            except IndexError:
                fg_color_hex, bg_color_hex = INVALID_TILE_COLOR, INVALID_TILE_COLOR
            self.attr_fg_labels[r].config(
                bg=fg_color_hex, fg=get_contrast_color(fg_color_hex)
            )
            self.attr_bg_labels[r].config(
                bg=bg_color_hex, fg=get_contrast_color(bg_color_hex)
            )

    def draw_palette(self):  # Renamed draw_palette to this for clarity
        """Draws the 16-color selector palette in the Tile Editor tab."""
        canvas = self.tile_editor_palette_canvas
        canvas.delete("all")
        size = PALETTE_SQUARE_SIZE
        padding = 2
        for i in range(16):
            row, col = divmod(i, 4)
            x1 = col * (size + padding) + padding
            y1 = row * (size + padding) + padding
            x2 = x1 + size
            y2 = y1 + size
            color = self.active_msx_palette[i]  # Use active palette
            outline_color = "red" if i == selected_color_index else "grey"
            outline_width = 2 if i == selected_color_index else 1
            canvas.create_rectangle(
                x1,
                y1,
                x2,
                y2,
                fill=color,
                outline=outline_color,
                width=outline_width,
                tags=f"pal_sel_{i}",
            )

    # --- vvv Palette Editor Drawing vvv ---
    def draw_current_palette(self):
        canvas = self.current_palette_canvas
        canvas.delete("all")
        size = CURRENT_PALETTE_SLOT_SIZE
        padding = 2
        for i in range(16):
            row, col = divmod(i, 4)
            x1 = col * (size + padding) + padding
            y1 = row * (size + padding) + padding
            x2 = x1 + size
            y2 = y1 + size
            color = self.active_msx_palette[i]
            outline_color = "red" if i == self.selected_palette_slot else "grey"
            outline_width = 3 if i == self.selected_palette_slot else 1
            canvas.create_rectangle(
                x1,
                y1,
                x2,
                y2,
                fill=color,
                outline=outline_color,
                width=outline_width,
                tags=f"pal_slot_{i}",
            )

    def draw_512_picker(self):
        canvas = self.msx2_picker_canvas
        canvas.delete("all")
        size = MSX2_PICKER_SQUARE_SIZE
        padding = 1
        cols = MSX2_PICKER_COLS
        for i in range(512):
            row, col = divmod(i, cols)
            x1 = col * (size + padding) + padding
            y1 = row * (size + padding) + padding
            x2 = x1 + size
            y2 = y1 + size
            hex_color = msx2_512_colors_hex[i]
            r, g, b = msx2_512_colors_rgb7[i]
            canvas.create_rectangle(
                x1,
                y1,
                x2,
                y2,
                fill=hex_color,
                outline="grey",
                width=1,
                tags=(f"msx2_picker_{i}", f"msx2_rgb_{r}_{g}_{b}"),
            )

    def update_palette_info_labels(self):
        slot = self.selected_palette_slot
        if 0 <= slot < 16:
            color_hex = self.active_msx_palette[slot]
            rgb7 = (-1, -1, -1)
            try:
                idx512 = msx2_512_colors_hex.index(color_hex)
                rgb7 = msx2_512_colors_rgb7[idx512]
            except ValueError:
                pass
            self.selected_slot_label.config(text=f"Slot: {slot}")
            self.selected_slot_color_label.config(bg=color_hex)
            self.selected_slot_rgb_label.config(
                text=f"RGB: {color_hex} ({rgb7[0]},{rgb7[1]},{rgb7[2]})"
            )
            self.rgb_r_var.set(str(rgb7[0]) if rgb7[0] != -1 else "?")
            self.rgb_g_var.set(str(rgb7[1]) if rgb7[1] != -1 else "?")
            self.rgb_b_var.set(str(rgb7[2]) if rgb7[2] != -1 else "?")
        else:
            self.selected_slot_label.config(text="Slot: -")
            self.selected_slot_color_label.config(bg="grey")
            self.selected_slot_rgb_label.config(text="RGB: -")
            self.rgb_r_var.set("")
            self.rgb_g_var.set("")
            self.rgb_b_var.set("")

    # --- ^^^ Palette Editor Drawing ^^^ ---

    # ... (draw_tileset_viewer, update_tile_info_label unchanged) ...
    def draw_tileset_viewer(self, canvas, highlighted_tile_index):
        canvas.delete("all")
        padding = 1
        size = VIEWER_TILE_SIZE
        max_rows = math.ceil(num_tiles_in_set / NUM_TILES_ACROSS)
        canvas_height = max_rows * (size + padding) + padding
        canvas_width = NUM_TILES_ACROSS * (size + padding) + padding
        str_scroll = f"0 0 {float(canvas_width)} {float(canvas_height)}"
        current_scroll = canvas.cget("scrollregion")
        if isinstance(current_scroll, tuple):
            current_scroll = " ".join(map(str, current_scroll))
        if current_scroll != str_scroll:
            canvas.config(scrollregion=(0, 0, canvas_width, canvas_height))
        for i in range(num_tiles_in_set):
            tile_r, tile_c = divmod(i, NUM_TILES_ACROSS)
            base_x = tile_c * (size + padding) + padding
            base_y = tile_r * (size + padding) + padding
            img = self.create_tile_image(i, size)
            canvas.create_image(
                base_x,
                base_y,
                image=img,
                anchor=tk.NW,
                tags=(f"tile_img_{i}", "tile_image"),
            )
            outline_color = "red" if i == highlighted_tile_index else "grey"
            outline_width = 2 if i == highlighted_tile_index else 1
            canvas.create_rectangle(
                base_x - padding / 2,
                base_y - padding / 2,
                base_x + size + padding / 2,
                base_y + size + padding / 2,
                outline=outline_color,
                width=outline_width,
                tags=f"tile_border_{i}",
            )

    def update_tile_info_label(self):
        self.tile_info_label.config(
            text=f"Tile: {current_tile_index}/{max(0, num_tiles_in_set-1)}"
        )

    # ... (draw_supertile_definition_canvas, draw_supertile_selector, update_supertile_info_labels unchanged) ...
    def draw_supertile_definition_canvas(self):
        canvas = self.supertile_def_canvas
        canvas.delete("all")
        if not (0 <= current_supertile_index < num_supertiles):
            return
        definition = supertiles_data[current_supertile_index]
        size = SUPERTILE_DEF_TILE_SIZE
        for r in range(SUPERTILE_GRID_DIM):
            for c in range(SUPERTILE_GRID_DIM):
                tile_idx = definition[r][c]
                base_x = c * size
                base_y = r * size
                img = self.create_tile_image(tile_idx, size)
                canvas.create_image(
                    base_x, base_y, image=img, anchor=tk.NW, tags=f"def_tile_{r}_{c}"
                )
                canvas.create_rectangle(
                    base_x, base_y, base_x + size, base_y + size, outline="grey"
                )

    def draw_supertile_selector(self, canvas, highlighted_supertile_index):
        """Draws supertile selector, highlighting selected and optionally dragged supertile."""
        # Check if drag is active and involves a supertile from *any* selector
        is_dragging_supertile = self.drag_active and self.drag_item_type == "supertile"
        dragged_supertile_index = self.drag_start_index if is_dragging_supertile else -1

        try:
            canvas.delete("all")
            padding = 1
            size = SUPERTILE_SELECTOR_PREVIEW_SIZE
            max_rows = math.ceil(num_supertiles / NUM_SUPERTILES_ACROSS)
            canvas_height = max(1, max_rows * (size + padding) + padding)  # Ensure > 0
            canvas_width = max(
                1, NUM_SUPERTILES_ACROSS * (size + padding) + padding
            )  # Ensure > 0
            str_scroll = f"0 0 {float(canvas_width)} {float(canvas_height)}"

            # Safely get current scroll region
            current_scroll = ""
            try:
                current_scroll_val = canvas.cget("scrollregion")
                if isinstance(current_scroll_val, tuple):
                    current_scroll = " ".join(map(str, current_scroll_val))
                else:
                    current_scroll = str(current_scroll_val)
            except tk.TclError:
                pass  # Canvas might not be fully ready

            # Update scrollregion if needed
            if current_scroll != str_scroll:
                canvas.config(scrollregion=(0, 0, canvas_width, canvas_height))

            # Draw each supertile
            for i in range(num_supertiles):
                st_r, st_c = divmod(i, NUM_SUPERTILES_ACROSS)
                base_x = st_c * (size + padding) + padding
                base_y = st_r * (size + padding) + padding

                # Get cached image
                img = self.create_supertile_image(i, size)
                canvas.create_image(
                    base_x,
                    base_y,
                    image=img,
                    anchor=tk.NW,
                    tags=(f"st_img_{i}", "st_image"),
                )

                # Determine outline style
                outline_color = "grey"  # Default
                outline_width = 1
                if i == dragged_supertile_index:
                    # Highlight for the item being dragged takes precedence
                    outline_color = "yellow"
                    outline_width = 3
                elif i == highlighted_supertile_index:
                    # Highlight for normal selection
                    outline_color = "red"
                    outline_width = 2

                # Draw the border rectangle
                bx1 = max(0, base_x - padding / 2)
                by1 = max(0, base_y - padding / 2)
                bx2 = base_x + size + padding / 2
                by2 = base_y + size + padding / 2
                canvas.create_rectangle(
                    bx1,
                    by1,
                    bx2,
                    by2,
                    outline=outline_color,
                    width=outline_width,
                    tags=f"st_border_{i}",
                )

        except tk.TclError as e:
            # Catch errors if the canvas is destroyed during redraw
            print(f"TclError during draw_supertile_selector: {e}")
        except Exception as e:
            print(f"Unexpected error during draw_supertile_selector: {e}")

    def update_supertile_info_labels(self):
        self.supertile_def_info_label.config(
            text=f"Editing Supertile: {current_supertile_index}/{max(0, num_supertiles-1)}"
        )
        self.supertile_tile_select_label.config(
            text=f"Selected Tile for Placing: {selected_tile_for_supertile}"
        )
        self.supertile_sel_info_label.config(text=f"Supertiles: {num_supertiles}")

    def draw_map_canvas(self):
        """Draws map, supertile grid, window view, selection, and paste preview."""
        canvas = self.map_canvas
        # Check if canvas exists before proceeding
        if not canvas.winfo_exists():
            return
        canvas.delete("all")  # Clear everything first

        # --- 1. Calculate Sizes ---
        zoomed_tile_size = self.get_zoomed_tile_size()
        if zoomed_tile_size <= 0: return # Avoid division by zero later
        zoomed_supertile_size = SUPERTILE_GRID_DIM * zoomed_tile_size
        if zoomed_supertile_size <= 0: return # Avoid division by zero later

        # --- 2. Update Scroll Region ---
        map_pixel_width = map_width * zoomed_supertile_size
        map_pixel_height = map_height * zoomed_supertile_size
        # Ensure scroll region dimensions are positive
        safe_scroll_width = max(1.0, float(map_pixel_width))
        safe_scroll_height = max(1.0, float(map_pixel_height))
        str_scroll = f"0 0 {safe_scroll_width} {safe_scroll_height}"
        current_scroll = ""
        try:
            current_scroll_val = canvas.cget("scrollregion")
            if isinstance(current_scroll_val, tuple):
                current_scroll = " ".join(map(str, current_scroll_val))
            else:
                current_scroll = str(current_scroll_val)
        except tk.TclError: pass # Ignore if canvas not ready

        if current_scroll != str_scroll:
            try:
                canvas.config(scrollregion=(0, 0, safe_scroll_width, safe_scroll_height))
            except tk.TclError: pass # Ignore if canvas not ready

        # --- 3. Draw Supertile Images ---
        # Determine visible area in canvas coordinates to optimize drawing (optional but good)
        # view_x1 = canvas.canvasx(0)
        # view_y1 = canvas.canvasy(0)
        # view_x2 = canvas.canvasx(canvas.winfo_width())
        # view_y2 = canvas.canvasy(canvas.winfo_height())
        # Determine range of supertiles potentially visible
        # start_col = max(0, int(view_x1 // zoomed_supertile_size))
        # start_row = max(0, int(view_y1 // zoomed_supertile_size))
        # end_col = min(map_width, int(math.ceil(view_x2 / zoomed_supertile_size)))
        # end_row = min(map_height, int(math.ceil(view_y2 / zoomed_supertile_size)))
        # --- Simplified: Draw all for now ---
        start_col, start_row = 0, 0
        end_col, end_row = map_width, map_height
        # --- End Simplification ---

        for r in range(start_row, end_row):
            for c in range(start_col, end_col):
                try:
                    supertile_idx = map_data[r][c]
                    base_x = c * zoomed_supertile_size
                    base_y = r * zoomed_supertile_size
                    # Optimization check (optional):
                    # if base_x + zoomed_supertile_size < view_x1 or base_x > view_x2 or \
                    #    base_y + zoomed_supertile_size < view_y1 or base_y > view_y2:
                    #     continue
                    img = self.create_supertile_image(supertile_idx, zoomed_supertile_size)
                    # Store image reference on canvas item to prevent garbage collection
                    item_id = canvas.create_image(
                        base_x, base_y, image=img, anchor=tk.NW, tags=("map_supertile_image", f"map_cell_{r}_{c}")
                    )
                    # canvas.itemconfig(item_id, image=img) # Re-assign might not be needed
                except IndexError:
                    print(f"Error: Map data index out of bounds at {r},{c}")
                except Exception as e:
                    print(f"Error drawing map cell {r},{c}: {e}")


        # --- 4. Draw Supertile Grid (if enabled) ---
        if self.show_supertile_grid.get():
            grid_color = GRID_COLOR_CYCLE[self.grid_color_index]
            # Draw vertical lines
            for c_grid in range(map_width + 1):
                x = c_grid * zoomed_supertile_size
                canvas.create_line(x, 0, x, map_pixel_height, fill=grid_color, dash=GRID_DASH_PATTERN, tags="supertile_grid")
            # Draw horizontal lines
            for r_grid in range(map_height + 1):
                y = r_grid * zoomed_supertile_size
                canvas.create_line(0, y, map_pixel_width, y, fill=grid_color, dash=GRID_DASH_PATTERN, tags="supertile_grid")

        # --- 5. Draw FINAL Selection Rectangle (if selection exists and not dragging) ---
        # Use the existing helper which draws if state is correct
        self._draw_selection_rectangle() # Draws if start/end exist and not active drag

        # --- 6. Draw Window View Overlay (if enabled) ---
        if self.show_window_view.get():
            grid_color = GRID_COLOR_CYCLE[self.grid_color_index]
            win_tx = self.window_view_tile_x
            win_ty = self.window_view_tile_y
            win_tw = self.window_view_tile_w.get()
            win_th = self.window_view_tile_h.get()
            win_px = win_tx * zoomed_tile_size
            win_py = win_ty * zoomed_tile_size
            win_pw = win_tw * zoomed_tile_size
            win_ph = win_th * zoomed_tile_size

            canvas.create_rectangle(win_px, win_py, win_px + win_pw, win_py + win_ph, outline=grid_color, width=2, tags=("window_view_rect", "window_view_item"))
            # Draw half-tile overlay if max height
            if win_th == MAX_WIN_VIEW_HEIGHT_TILES:
                half_tile_h_px = zoomed_tile_size / 2
                dark_y1 = win_py + win_ph - half_tile_h_px
                dark_y2 = win_py + win_ph
                canvas.create_rectangle(win_px, dark_y1, win_px + win_pw, dark_y2, fill="gray50", stipple="gray50", outline="", tags=("window_view_overscan", "window_view_item"))
            # Draw Handles
            handle_size = WIN_VIEW_HANDLE_SIZE
            hs2 = handle_size // 2
            handle_fill = grid_color
            handle_outline = "black" if grid_color != "#000000" else "white"
            handles = {
                "nw": (win_px, win_py), "n": (win_px + win_pw / 2, win_py), "ne": (win_px + win_pw, win_py),
                "w": (win_px, win_py + win_ph / 2),                            "e": (win_px + win_pw, win_py + win_ph / 2),
                "sw": (win_px, win_py + win_ph), "s": (win_px + win_pw / 2, win_py + win_ph), "se": (win_px + win_pw, win_py + win_ph),
            }
            for tag, (cx, cy) in handles.items():
                x1, y1, x2, y2 = cx - hs2, cy - hs2, cx + hs2, cy + hs2
                canvas.create_rectangle(x1, y1, x2, y2, fill=handle_fill, outline=handle_outline, width=1, tags=("window_view_handle", f"handle_{tag}", "window_view_item"))

        # --- 7. Draw Paste Preview Rectangle (if applicable) --- >> NEW SECTION << ---
        self._clear_paste_preview_rect() # Clear any old one first
        if self.map_clipboard_data: # Check if clipboard has data
            is_map_tab_active = False
            if self.notebook and self.notebook.winfo_exists():
                try:
                    if self.notebook.index(self.notebook.select()) == 3:
                        is_map_tab_active = True
                except tk.TclError: pass

            if is_map_tab_active: # Check if map tab is active
                try:
                    # Get current pointer position relative to the map canvas widget
                    pointer_x = canvas.winfo_pointerx() - canvas.winfo_rootx()
                    pointer_y = canvas.winfo_pointery() - canvas.winfo_rooty()
                    # Check if mouse is currently within the map canvas bounds
                    if (0 <= pointer_x < canvas.winfo_width() and
                        0 <= pointer_y < canvas.winfo_height()):
                        # Convert widget coords to canvas coords
                        canvas_x = canvas.canvasx(pointer_x)
                        canvas_y = canvas.canvasy(pointer_y)
                        # Use the existing draw function, passing coords explicitly
                        self._draw_paste_preview_rect(canvas_coords=(canvas_x, canvas_y))
                except Exception as e:
                     print(f"Error getting pointer for paste preview redraw: {e}") # Log error
                     self._clear_paste_preview_rect() # Clear if error occurs

        # --- 8. Update Zoom Label ---
        # Ensure label exists before configuring
        if hasattr(self, 'map_zoom_label') and self.map_zoom_label.winfo_exists():
            self.map_zoom_label.config(text=f"{int(self.map_zoom_level * 100)}%")

    def update_map_info_labels(self):
        self.map_size_label.config(text=f"{map_width} x {map_height}")
        self.map_supertile_select_label.config(
            text=f"Selected Supertile for Painting: {selected_supertile_for_map}"
        )
        # Update window size entries from state variables
        self.window_view_tile_w.set(
            self.window_view_tile_w.get()
        )  # Ensure IntVar reflects internal state if needed
        self.window_view_tile_h.set(self.window_view_tile_h.get())
        # Zoom label updated in draw_map_canvas

    def on_tab_change(self, event):
        """Handles tab switching. Refreshes the newly visible tab fully."""

        # --- Clear Map-Specific Visuals (Before Switch) ---
        # Clear paste preview regardless of which tab is being left, as it's only for map tab
        self._clear_paste_preview_rect()
        # If a selection was active on map tab, clear it visually (state cleared elsewhere if needed)
        # self._clear_map_selection() # Don't clear selection state just on tab change

        # --- Refresh the newly selected tab's content ---
        self.update_all_displays(changed_level="all")

        # --- Update Edit menu state based on the NEW tab ---
        self._update_edit_menu_state()

        # --- Update Add/Insert/Delete button states based on NEW tab ---
        self._update_editor_button_states()

        # --- Manage Map Tab Specific Keybindings and State ---
        selected_tab_index = -1
        try:
            if self.notebook and self.notebook.winfo_exists():
                selected_tab = self.notebook.select()
                if selected_tab:
                    selected_tab_index = self.notebook.index(selected_tab)
        except tk.TclError:
            pass

        # --- Unbind G key first, regardless of tab ---
        try:
            self.root.unbind("<KeyPress-g>")
            self.root.unbind("<KeyPress-G>")
        except tk.TclError:
            pass # Ignore if bindings didn't exist

        if selected_tab_index == 3:  # Map Editor Tab is selected
            # Bind 'g'/'G' for grid color cycling
            self.root.bind("<KeyPress-g>", self.handle_map_tab_keypress, add="+")
            self.root.bind("<KeyPress-G>", self.handle_map_tab_keypress, add="+")
            # Ensure map canvas gets focus for keyboard input
            self.root.after(50, self.map_canvas.focus_set)

            # --- Redraw paste preview if applicable when switching TO map tab ---
            if self.map_clipboard_data:
                try:
                    # Get current pointer position relative to the map canvas widget
                    pointer_x = self.map_canvas.winfo_pointerx() - self.map_canvas.winfo_rootx()
                    pointer_y = self.map_canvas.winfo_pointery() - self.map_canvas.winfo_rooty()
                    # Check if mouse is currently within the map canvas bounds
                    if (0 <= pointer_x < self.map_canvas.winfo_width() and
                        0 <= pointer_y < self.map_canvas.winfo_height()):
                        # Convert widget coords to canvas coords and draw preview
                         canvas_x = self.map_canvas.canvasx(pointer_x)
                         canvas_y = self.map_canvas.canvasy(pointer_y)
                         self._draw_paste_preview_rect(canvas_coords=(canvas_x, canvas_y))
                except Exception:
                     # Ignore errors getting pointer position (e.g., window not focused)
                     pass
        # No 'else' needed here, preview cleared at the top of the function

    # --- Palette Editor Handlers ---
    def handle_current_palette_click(self, event):
        canvas = self.current_palette_canvas
        size = CURRENT_PALETTE_SLOT_SIZE
        padding = 2
        col = event.x // (size + padding)
        row = event.y // (size + padding)
        clicked_slot = row * 4 + col
        if 0 <= clicked_slot < 16:
            if self.selected_palette_slot != clicked_slot:
                self.selected_palette_slot = clicked_slot
                self.draw_current_palette()  # Redraw highlight
                self.update_palette_info_labels()  # Update info display

    def handle_512_picker_click(self, event):
        if not (0 <= self.selected_palette_slot < 16):
            return
        canvas = self.msx2_picker_canvas
        size = MSX2_PICKER_SQUARE_SIZE
        padding = 1
        cols = MSX2_PICKER_COLS
        canvas_x = canvas.canvasx(event.x)
        canvas_y = canvas.canvasy(event.y)
        col = int(canvas_x // (size + padding))
        row = int(canvas_y // (size + padding))
        clicked_index = row * cols + col
        if 0 <= clicked_index < 512:
            new_color_hex = msx2_512_colors_hex[clicked_index]
            target_slot = self.selected_palette_slot
            if self.active_msx_palette[target_slot] != new_color_hex:
                self._mark_project_modified()
                self.active_msx_palette[target_slot] = new_color_hex
                print(f"Set Palette Slot {target_slot} to {new_color_hex}")
                self.clear_all_caches()
                self.update_all_displays(changed_level="all")
        else:
            print("Clicked outside valid color range in picker.")

    def handle_rgb_apply(self):
        if not (0 <= self.selected_palette_slot < 16):
            return
        try:
            r = int(self.rgb_r_var.get())
            g = int(self.rgb_g_var.get())
            b = int(self.rgb_b_var.get())
            if not (0 <= r <= 7 and 0 <= g <= 7 and 0 <= b <= 7):
                raise ValueError("RGB values must be 0-7.")
            new_color_hex = self._rgb7_to_hex(r, g, b)
            target_slot = self.selected_palette_slot
            if self.active_msx_palette[target_slot] != new_color_hex:
                self._mark_project_modified()
                self.active_msx_palette[target_slot] = new_color_hex
                print(f"Set Palette Slot {target_slot} to {new_color_hex} via RGB")
                self.clear_all_caches()
                self.update_all_displays(changed_level="all")
        except ValueError as e:
            messagebox.showerror("Invalid RGB", f"Invalid RGB input: {e}")

    def reset_palette_to_default(self):
        confirm = messagebox.askokcancel(
            "Reset Palette",
            "Reset the active palette to the MSX2 default colors?\nThis will affect the appearance of all tiles and supertiles.",
        )
        if confirm:
            new_default_palette = []
            for r, g, b in MSX2_RGB7_VALUES:
                new_default_palette.append(self._rgb7_to_hex(r, g, b))
            if self.active_msx_palette != new_default_palette:
                self._mark_project_modified()
                self.active_msx_palette = new_default_palette
                self.selected_palette_slot = 0
                global selected_color_index
                selected_color_index = 0
                self.clear_all_caches()
                self.update_all_displays(changed_level="all")
                print("Palette reset to MSX2 defaults.")
            else:
                print("Palette is already set to MSX2 defaults.")

    # --- Tile Editor Handlers ---
    def handle_editor_click(self, event):
        global last_drawn_pixel, current_tile_index, tileset_patterns
        if not (0 <= current_tile_index < num_tiles_in_set):
            return
        c = event.x // EDITOR_PIXEL_SIZE
        r = event.y // EDITOR_PIXEL_SIZE
        if 0 <= r < TILE_HEIGHT and 0 <= c < TILE_WIDTH:
            pixel_value = 1 if event.num == 1 else 0
            if tileset_patterns[current_tile_index][r][c] != pixel_value:
                self._mark_project_modified()
                tileset_patterns[current_tile_index][r][c] = pixel_value
                self.invalidate_tile_cache(current_tile_index)
                self.update_all_displays(changed_level="tile")
            last_drawn_pixel = (r, c)

    def handle_editor_drag(self, event):
        global last_drawn_pixel, current_tile_index, tileset_patterns
        if not (0 <= current_tile_index < num_tiles_in_set):
            return
        c = event.x // EDITOR_PIXEL_SIZE
        r = event.y // EDITOR_PIXEL_SIZE
        if 0 <= r < TILE_HEIGHT and 0 <= c < TILE_WIDTH:
            if (r, c) != last_drawn_pixel:
                pixel_value = (
                    1 if event.state & 0x100 else (0 if event.state & 0x400 else -1)
                )
                if (
                    pixel_value != -1
                    and tileset_patterns[current_tile_index][r][c] != pixel_value
                ):
                    self._mark_project_modified()
                    tileset_patterns[current_tile_index][r][c] = pixel_value
                    self.invalidate_tile_cache(current_tile_index)
                    self.update_all_displays(changed_level="tile")
                last_drawn_pixel = (r, c)

    def handle_tile_editor_palette_click(self, event):
        global selected_color_index
        canvas = self.tile_editor_palette_canvas
        size = PALETTE_SQUARE_SIZE
        padding = 2
        col = event.x // (size + padding)
        row = event.y // (size + padding)
        clicked_index = row * 4 + col
        if 0 <= clicked_index < 16:
            if selected_color_index != clicked_index:
                selected_color_index = clicked_index
                self.draw_palette()  # Redraw this palette only

    def set_row_color(self, row, fg_or_bg):
        global tileset_colors, current_tile_index, selected_color_index
        if not (0 <= current_tile_index < num_tiles_in_set):
            return
        if not (0 <= selected_color_index < 16):
            return
        if 0 <= row < TILE_HEIGHT:
            current_fg_idx, current_bg_idx = tileset_colors[current_tile_index][row]
            changed = False
            if fg_or_bg == "fg" and current_fg_idx != selected_color_index:
                tileset_colors[current_tile_index][row] = (
                    selected_color_index,
                    current_bg_idx,
                )
                changed = True
            elif fg_or_bg == "bg" and current_bg_idx != selected_color_index:
                tileset_colors[current_tile_index][row] = (
                    current_fg_idx,
                    selected_color_index,
                )
                changed = True
            if changed:
                self._mark_project_modified()
                self.invalidate_tile_cache(current_tile_index)
                self.update_all_displays(changed_level="tile")

    def handle_tileset_click(self, event):
        """Handles Button-1 click on the main tileset viewer. Records potential drag start."""
        canvas = event.widget
        clicked_index = self._get_index_from_canvas_coords(
            canvas, event.x, event.y, "tile"
        )

        # --- Reset all drag state variables ---
        # This ensures a clean slate for every new click
        self.drag_active = False
        self.drag_item_type = None
        self.drag_start_index = -1
        self.drag_canvas = None
        if self.drag_indicator_id:
            try:  # Clean up previous indicator just in case
                canvas.delete(self.drag_indicator_id)
            except tk.TclError:
                pass
            self.drag_indicator_id = None
        try:  # Reset cursor
            canvas.config(cursor="")
        except tk.TclError:
            pass
        # --- End Reset ---

        # Record potential drag info ONLY if a valid tile item was clicked
        if 0 <= clicked_index < num_tiles_in_set:
            # Store info needed IF a drag starts later in the motion handler
            self.drag_item_type = "tile"
            self.drag_start_index = clicked_index
            self.drag_canvas = canvas
            # *** DO NOT set self.drag_active = True here ***
            # print(f"Potential Drag Start Tile: {self.drag_start_index} on canvas {canvas}") # Debug
        else:
            # Clicked outside valid items or beyond last item. Clear potential drag info.
            self.drag_item_type = None
            self.drag_start_index = -1
            self.drag_canvas = None
            # print(f"Click on tileset viewer ignored for drag start (index: {clicked_index})") # Debug

    def flip_tile_horizontal(self):
        global tileset_patterns, current_tile_index, num_tiles_in_set
        if not (0 <= current_tile_index < num_tiles_in_set):
            return
        current_pattern = tileset_patterns[current_tile_index]
        new_pattern = [[0] * TILE_WIDTH for _ in range(TILE_HEIGHT)]
        for r in range(TILE_HEIGHT):
            new_pattern[r] = current_pattern[r][::-1]
        tileset_patterns[current_tile_index] = new_pattern
        self.invalidate_tile_cache(current_tile_index)
        self.update_all_displays(changed_level="tile")
        self._mark_project_modified()
        print(f"Tile {current_tile_index} flipped horizontally.")

    def flip_tile_vertical(self):
        global tileset_patterns, tileset_colors, current_tile_index, num_tiles_in_set
        if not (0 <= current_tile_index < num_tiles_in_set):
            return
        tileset_patterns[current_tile_index].reverse()
        tileset_colors[current_tile_index].reverse()
        self.invalidate_tile_cache(current_tile_index)
        self.update_all_displays(changed_level="tile")
        self._mark_project_modified()
        print(f"Tile {current_tile_index} flipped vertically.")

    def rotate_tile_90cw(self):
        global tileset_patterns, tileset_colors, current_tile_index, num_tiles_in_set, WHITE_IDX, BLACK_IDX
        if not (0 <= current_tile_index < num_tiles_in_set):
            return
        current_pattern = tileset_patterns[current_tile_index]
        new_pattern = [[0 for _ in range(TILE_WIDTH)] for _ in range(TILE_HEIGHT)]
        for r in range(TILE_HEIGHT):
            for c in range(TILE_WIDTH):
                new_pattern[c][(TILE_HEIGHT - 1) - r] = current_pattern[r][c]
        tileset_patterns[current_tile_index] = new_pattern
        tileset_colors[current_tile_index] = [
            (WHITE_IDX, BLACK_IDX) for _ in range(TILE_HEIGHT)
        ]  # Reset colors
        self._mark_project_modified()
        messagebox.showinfo(
            "Rotation Complete", "Tile rotated.\nRow colors have been reset to default."
        )
        self.invalidate_tile_cache(current_tile_index)
        self.update_all_displays(changed_level="tile")
        print(f"Tile {current_tile_index} rotated 90 CW (colors reset).")

    def shift_tile_up(self):
        global tileset_patterns, tileset_colors, current_tile_index, num_tiles_in_set
        if not (0 <= current_tile_index < num_tiles_in_set):
            return
        current_pattern = tileset_patterns[current_tile_index]
        current_colors = tileset_colors[current_tile_index]
        first_pattern_row = current_pattern[0]
        first_color_row = current_colors[0]
        for i in range(TILE_HEIGHT - 1):
            current_pattern[i] = current_pattern[i + 1]
            current_colors[i] = current_colors[i + 1]
        current_pattern[TILE_HEIGHT - 1] = first_pattern_row
        current_colors[TILE_HEIGHT - 1] = first_color_row
        self.invalidate_tile_cache(current_tile_index)
        self.update_all_displays(changed_level="tile")
        self._mark_project_modified()
        print(f"Tile {current_tile_index} shifted up.")

    def shift_tile_down(self):
        global tileset_patterns, tileset_colors, current_tile_index, num_tiles_in_set
        if not (0 <= current_tile_index < num_tiles_in_set):
            return
        current_pattern = tileset_patterns[current_tile_index]
        current_colors = tileset_colors[current_tile_index]
        last_pattern_row = current_pattern[TILE_HEIGHT - 1]
        last_color_row = current_colors[TILE_HEIGHT - 1]
        for i in range(TILE_HEIGHT - 1, 0, -1):
            current_pattern[i] = current_pattern[i - 1]
            current_colors[i] = current_colors[i - 1]
        current_pattern[0] = last_pattern_row
        current_colors[0] = last_color_row
        self.invalidate_tile_cache(current_tile_index)
        self.update_all_displays(changed_level="tile")
        self._mark_project_modified()
        print(f"Tile {current_tile_index} shifted down.")

    def shift_tile_left(self):
        global tileset_patterns, current_tile_index, num_tiles_in_set
        if not (0 <= current_tile_index < num_tiles_in_set):
            return
        current_pattern = tileset_patterns[current_tile_index]
        for r in range(TILE_HEIGHT):
            row_data = current_pattern[r]
            if TILE_WIDTH > 0:
                first_pixel = row_data[0]
            for c in range(TILE_WIDTH - 1):
                row_data[c] = row_data[c + 1]
            row_data[TILE_WIDTH - 1] = first_pixel
        self.invalidate_tile_cache(current_tile_index)
        self.update_all_displays(changed_level="tile")
        self._mark_project_modified()
        print(f"Tile {current_tile_index} shifted left.")

    def shift_tile_right(self):
        global tileset_patterns, current_tile_index, num_tiles_in_set
        if not (0 <= current_tile_index < num_tiles_in_set):
            return
        current_pattern = tileset_patterns[current_tile_index]
        for r in range(TILE_HEIGHT):
            row_data = current_pattern[r]
            if TILE_WIDTH > 0:
                last_pixel = row_data[TILE_WIDTH - 1]
            for c in range(TILE_WIDTH - 1, 0, -1):
                row_data[c] = row_data[c - 1]
            row_data[0] = last_pixel
        self.invalidate_tile_cache(current_tile_index)
        self.update_all_displays(changed_level="tile")
        self._mark_project_modified()
        print(f"Tile {current_tile_index} shifted right.")

    # --- Supertile Editor Handlers ---
    def handle_st_tileset_click(self, event):
        """Handles Button-1 click on the supertile editor's tileset viewer. Records potential drag start."""
        canvas = event.widget
        clicked_index = self._get_index_from_canvas_coords(
            canvas, event.x, event.y, "tile"
        )

        # --- Reset all drag state variables ---
        self.drag_active = False
        self.drag_item_type = None
        self.drag_start_index = -1
        self.drag_canvas = None
        if self.drag_indicator_id:
            try:
                canvas.delete(self.drag_indicator_id)
            except tk.TclError:
                pass
            self.drag_indicator_id = None
        try:
            canvas.config(cursor="")
        except tk.TclError:
            pass
        # --- End Reset ---

        # Record potential drag info ONLY if a valid tile item was clicked
        if 0 <= clicked_index < num_tiles_in_set:
            self.drag_item_type = "tile"
            self.drag_start_index = clicked_index
            self.drag_canvas = canvas
            # *** DO NOT set self.drag_active = True here ***
            # print(f"Potential Drag Start Tile (ST): {self.drag_start_index} on canvas {canvas}") # Debug
        else:
            # Clear potential drag info if click was invalid
            self.drag_item_type = None
            self.drag_start_index = -1
            self.drag_canvas = None
            # print(f"Click on st_tileset viewer ignored for drag start (index: {clicked_index})") # Debug

    def handle_supertile_def_click(self, event):
        # Handles the initial click for placing a tile in the supertile definition.

        # --- Check if a valid tile is selected FIRST ---
        if not (0 <= selected_tile_for_supertile < num_tiles_in_set):
            messagebox.showwarning("Place Tile", "Please select a valid tile first.")
            return

        # --- Calculate Target Cell ---
        canvas = self.supertile_def_canvas
        size = SUPERTILE_DEF_TILE_SIZE
        # Basic check for valid canvas/size before division
        if size <= 0 or not canvas.winfo_exists():
            return
        col = event.x // size
        row = event.y // size

        # --- Reset Drag State ---
        self.last_placed_supertile_cell = None

        # --- Attempt Placement using Helper ---
        placed = self._place_tile_in_supertile(row, col)

        # --- Update Drag State if Placement Occurred ---
        if placed:
            self.last_placed_supertile_cell = (row, col)

    def handle_supertile_selector_click(self, event):
        """Handles Button-1 click on the supertile editor's supertile selector. Records potential drag start."""
        canvas = event.widget
        clicked_index = self._get_index_from_canvas_coords(
            canvas, event.x, event.y, "supertile"
        )

        # --- Reset all drag state variables ---
        self.drag_active = False
        self.drag_item_type = None
        self.drag_start_index = -1
        self.drag_canvas = None
        if self.drag_indicator_id:
            try:
                canvas.delete(self.drag_indicator_id)
            except tk.TclError:
                pass
            self.drag_indicator_id = None
        try:
            canvas.config(cursor="")
        except tk.TclError:
            pass
        # --- End Reset ---

        # Record potential drag info ONLY if a valid supertile item was clicked
        if 0 <= clicked_index < num_supertiles:
            self.drag_item_type = "supertile"
            self.drag_start_index = clicked_index
            self.drag_canvas = canvas
            # *** DO NOT set self.drag_active = True here ***
            # print(f"Potential Drag Start Supertile: {self.drag_start_index} on canvas {canvas}") # Debug
        else:
            # Clear potential drag info if click was invalid
            self.drag_item_type = None
            self.drag_start_index = -1
            self.drag_canvas = None
            # print(f"Click on supertile_selector viewer ignored for drag start (index: {clicked_index})") # Debug

    # --- Map Editor Handlers ---
    def handle_map_supertile_selector_click(self, event):
        """Handles Button-1 click on the map editor's supertile selector. Records potential drag start."""
        canvas = event.widget
        clicked_index = self._get_index_from_canvas_coords(
            canvas, event.x, event.y, "supertile"
        )

        # --- Reset all drag state variables ---
        self.drag_active = False
        self.drag_item_type = None
        self.drag_start_index = -1
        self.drag_canvas = None
        if self.drag_indicator_id:
            try:
                canvas.delete(self.drag_indicator_id)
            except tk.TclError:
                pass
            self.drag_indicator_id = None
        try:
            canvas.config(cursor="")
        except tk.TclError:
            pass
        # --- End Reset ---

        # Record potential drag info ONLY if a valid supertile item was clicked
        if 0 <= clicked_index < num_supertiles:
            self.drag_item_type = "supertile"
            self.drag_start_index = clicked_index
            self.drag_canvas = canvas
            # *** DO NOT set self.drag_active = True here ***
            # print(f"Potential Drag Start Supertile (Map): {self.drag_start_index} on canvas {canvas}") # Debug
        else:
            # Clear potential drag info if click was invalid
            self.drag_item_type = None
            self.drag_start_index = -1
            self.drag_canvas = None
            # print(f"Click on map_supertile_selector viewer ignored for drag start (index: {clicked_index})") # Debug

    def _paint_map_cell(self, canvas_x, canvas_y):
        """Paints a supertile on the map at the given CANVAS coordinates."""
        global map_data, last_painted_map_cell, selected_supertile_for_map  # Ensure globals are accessible

        canvas = self.map_canvas
        zoomed_supertile_size = SUPERTILE_GRID_DIM * self.get_zoomed_tile_size()
        if zoomed_supertile_size <= 0:
            return

        # Convert scrolled canvas coords to map cell coords (supertile grid)
        c = int(canvas_x // zoomed_supertile_size)
        r = int(canvas_y // zoomed_supertile_size)

        # Check bounds first
        if not (0 <= r < map_height and 0 <= c < map_width):
            return  # Clicked outside map bounds

        current_cell_id = (r, c)
        # Get current data before checks (needed for comparison)
        # Add a try-except just in case r,c is somehow invalid despite bounds check
        try:
            current_data = map_data[r][c]
        except IndexError:
            print(
                f"  ERROR: IndexError accessing map_data[{r}][{c}]. Map size: {map_width}x{map_height}"
            )
            return

        # --- CORE LOGIC FOR CONTINUOUS PAINT ---
        if current_cell_id != last_painted_map_cell:
            # Check if the data actually needs updating for this new cell
            if current_data != selected_supertile_for_map:
                self._mark_project_modified()
                map_data[r][c] = selected_supertile_for_map
                self.invalidate_minimap_background_cache()  # Map data changed

                # --- Redraw only the specific cell's visual ---
                base_x = c * zoomed_supertile_size
                base_y = r * zoomed_supertile_size
                img = self.create_supertile_image(
                    selected_supertile_for_map, zoomed_supertile_size
                )
                tag = f"map_cell_{r}_{c}"

                items = canvas.find_withtag(tag)
                if items:
                    canvas.itemconfig(items[0], image=img)
                else:
                    canvas.create_image(
                        base_x,
                        base_y,
                        image=img,
                        anchor=tk.NW,
                        tags=(tag, "map_supertile_image"),
                    )
                    # Only attempt to lower the tag if the grid is actually visible
                    if self.show_supertile_grid.get():
                        # Check if the tag exists before trying to lower below it
                        if canvas.find_withtag("supertile_grid"):
                            canvas.tag_lower(tag, "supertile_grid")
                self.draw_minimap()  # Update minimap only if data changed

            last_painted_map_cell = current_cell_id

    # --- Map Grid/Window Event Handlers ---
    def toggle_supertile_grid(self):
        """Callback for the supertile grid checkbutton."""
        self.draw_map_canvas()  # Redraw map to show/hide grid

    def toggle_window_view(self):
        """Callback for the window view checkbutton."""
        self.draw_map_canvas()
        self.root.update_idletasks()
        self.draw_minimap()

    def cycle_grid_color(self):
        """Cycles through the available grid colors."""
        self.grid_color_index = (self.grid_color_index + 1) % len(GRID_COLOR_CYCLE)
        # Redraw map if grids are visible
        if self.show_supertile_grid.get() or self.show_window_view.get():
            self.draw_map_canvas()
        print(f"Grid color set to: {GRID_COLOR_CYCLE[self.grid_color_index]}")

    def apply_window_size_from_entries(self):
        """Applies the W/H values from the Entry widgets."""
        try:
            new_w = self.window_view_tile_w.get()  # Get value from IntVar
            new_h = self.window_view_tile_h.get()

            # Validate range
            min_w, max_w = 1, 32
            min_h, max_h = 1, MAX_WIN_VIEW_HEIGHT_TILES  # Use constant
            if not (min_w <= new_w <= max_w and min_h <= new_h <= max_h):
                messagebox.showerror(
                    "Invalid Size",
                    f"Window width must be {min_w}-{max_w}, height {min_h}-{max_h}.",
                )
                # Reset entries to current state if invalid
                self.update_window_size_entries()
                return

            # If size changed, redraw the map
            # (IntVar should already hold the value, no need to set self.window_view_tile_w/h directly)
            self.draw_map_canvas()
            print(f"Window view size set to {new_w}x{new_h} tiles via input.")

        except tk.TclError:
            messagebox.showerror(
                "Invalid Input",
                "Please enter valid integer numbers for width and height.",
            )
            self.update_window_size_entries()  # Reset on error
        except Exception as e:
            messagebox.showerror("Error", f"Could not apply size: {e}")
            self.update_window_size_entries()

    def update_window_size_entries(self):
        """Updates the W/H entry boxes to match the current state."""
        # This ensures IntVars linked to entries have the correct value
        self.window_view_tile_w.set(self.window_view_tile_w.get())
        self.window_view_tile_h.set(self.window_view_tile_h.get())

    def _do_window_move_drag(self, current_canvas_x, current_canvas_y):
        """Helper function to handle window view movement during drag."""
        zoomed_tile_size = self.get_zoomed_tile_size()
        if zoomed_tile_size <= 0:
            return

        # Calculate drag distance in canvas pixels
        delta_x = current_canvas_x - self.drag_start_x
        delta_y = current_canvas_y - self.drag_start_y

        # Calculate drag distance in TILES (integer steps)
        delta_tile_x = round(delta_x / zoomed_tile_size)
        delta_tile_y = round(delta_y / zoomed_tile_size)

        # Calculate new top-left TILE coordinate
        new_tx = self.drag_start_win_tx + delta_tile_x
        new_ty = self.drag_start_win_ty + delta_tile_y

        # Clamp position within map bounds (in tile units)
        max_tile_x = (map_width * SUPERTILE_GRID_DIM) - self.window_view_tile_w.get()
        max_tile_y = (map_height * SUPERTILE_GRID_DIM) - self.window_view_tile_h.get()
        clamped_tx = max(0, min(new_tx, max_tile_x))
        clamped_ty = max(0, min(new_ty, max_tile_y))

        # Update state only if position changed
        if (
            self.window_view_tile_x != clamped_tx
            or self.window_view_tile_y != clamped_ty
        ):
            self.window_view_tile_x = clamped_tx
            self.window_view_tile_y = clamped_ty
            self.draw_map_canvas()  # Redraw to show moved window

    def _do_window_resize_drag(self, current_canvas_x, current_canvas_y):
        """Helper function to handle window view resizing during drag."""
        zoomed_tile_size = self.get_zoomed_tile_size()
        if zoomed_tile_size <= 0:
            return

        # Get starting dimensions and position in TILE units
        start_tx = self.drag_start_win_tx
        start_ty = self.drag_start_win_ty
        start_tw = self.drag_start_win_tw
        start_th = self.drag_start_win_th

        # Calculate current mouse position in TILE units (relative to map 0,0)
        current_tile_x = round(current_canvas_x / zoomed_tile_size)
        current_tile_y = round(current_canvas_y / zoomed_tile_size)

        # Calculate new dimensions based on handle and mouse position
        new_tx = start_tx
        new_ty = start_ty
        new_tw = start_tw
        new_th = start_th
        handle = self.window_view_resize_handle

        # Adjust X and Width based on handle
        if "w" in handle:  # West handles affect left edge (tx) and width
            new_tx = min(
                current_tile_x, start_tx + start_tw - 1
            )  # Don't allow negative width
            new_tw = start_tw + (start_tx - new_tx)
        elif "e" in handle:  # East handles affect width only
            new_tw = max(1, current_tile_x - start_tx + 1)  # Ensure at least 1 width

        # Adjust Y and Height based on handle
        if "n" in handle:  # North handles affect top edge (ty) and height
            new_ty = min(current_tile_y, start_ty + start_th - 1)
            new_th = start_th + (start_ty - new_ty)
        elif "s" in handle:  # South handles affect height only
            new_th = max(1, current_tile_y - start_ty + 1)

        # Clamp dimensions to valid range (1x1 to 32xMaxH)
        min_w, max_w = 1, 32
        min_h, max_h = 1, MAX_WIN_VIEW_HEIGHT_TILES
        clamped_tw = max(min_w, min(new_tw, max_w))
        clamped_th = max(min_h, min(new_th, max_h))

        # If width/height changed due to clamping, adjust position if necessary
        # (e.g., if dragging 'w' handle and clamped_tw < new_tw)
        if "w" in handle and clamped_tw != new_tw:
            new_tx = start_tx + start_tw - clamped_tw
        if "n" in handle and clamped_th != new_th:
            new_ty = start_ty + start_th - clamped_th

        # Clamp position within map bounds (0,0 to max_map_tile - current_size)
        max_map_tile_x = map_width * SUPERTILE_GRID_DIM
        max_map_tile_y = map_height * SUPERTILE_GRID_DIM
        clamped_tx = max(0, min(new_tx, max_map_tile_x - clamped_tw))
        clamped_ty = max(0, min(new_ty, max_map_tile_y - clamped_th))

        # Update state only if position or size changed
        if (
            self.window_view_tile_x != clamped_tx
            or self.window_view_tile_y != clamped_ty
            or self.window_view_tile_w.get() != clamped_tw
            or self.window_view_tile_h.get() != clamped_th
        ):
            #
            self.window_view_tile_x = clamped_tx
            self.window_view_tile_y = clamped_ty
            self.window_view_tile_w.set(clamped_tw)  # Update IntVars
            self.window_view_tile_h.set(clamped_th)
            # self.update_window_size_entries() # Update entries visually
            self.draw_map_canvas()  # Redraw to show resize

    def move_window_view_keyboard(self, dx, dy):
        """Moves the window view by dx, dy TILE steps."""
        if not self.show_window_view.get():
            return  # Only move if visible

        # Calculate new target position
        new_tx = self.window_view_tile_x + dx
        new_ty = self.window_view_tile_y + dy

        # Clamp within map bounds
        current_w = self.window_view_tile_w.get()
        current_h = self.window_view_tile_h.get()
        max_tile_x = (map_width * SUPERTILE_GRID_DIM) - current_w
        max_tile_y = (map_height * SUPERTILE_GRID_DIM) - current_h
        clamped_tx = max(0, min(new_tx, max_tile_x))
        clamped_ty = max(0, min(new_ty, max_tile_y))

        # Update if position changed
        if (
            self.window_view_tile_x != clamped_tx
            or self.window_view_tile_y != clamped_ty
        ):
            self.window_view_tile_x = clamped_tx
            self.window_view_tile_y = clamped_ty
            self.draw_map_canvas()  # Redraw

    def handle_map_keypress(self, event):
        """Handles key presses when the map canvas has focus (WASD, G)."""
        key = event.keysym.lower()  # Get lowercase keysym

        if key == "g":  # MODIFIED CHECK
            self.cycle_grid_color()
            return "break"  # Prevent other 'g' bindings
        elif self.show_window_view.get():  # Only move window if visible
            moved = False
            if key == "w":
                self.move_window_view_keyboard(0, -1)
                moved = True
            elif key == "a":
                self.move_window_view_keyboard(-1, 0)
                moved = True
            elif key == "s":
                self.move_window_view_keyboard(0, 1)
                moved = True
            elif key == "d":
                self.move_window_view_keyboard(1, 0)
                moved = True

            if moved:
                return "break"

    # --- Map Zoom Handlers ---
    def handle_map_zoom_scroll(self, event):
        """Handles Ctrl+MouseWheel zooming."""
        # Determine zoom direction
        zoom_in = False
        if (
            event.num == 4 or event.delta > 0
        ):  # Button 4 (Linux scroll up) or positive delta
            zoom_in = True
        elif (
            event.num == 5 or event.delta < 0
        ):  # Button 5 (Linux scroll down) or negative delta
            zoom_in = False
        else:
            return  # Unknown scroll event

        # Calculate zoom factor (multiplicative)
        factor = 1.1 if zoom_in else (1 / 1.1)

        # Get mouse position relative to canvas for zoom point
        canvas_x = self.map_canvas.canvasx(event.x)
        canvas_y = self.map_canvas.canvasy(event.y)

        # Perform zoom centered on the cursor
        self.zoom_map_at_point(factor, canvas_x, canvas_y)

    def change_map_zoom_mult(self, factor):
        """Applies multiplicative zoom, centered on the current canvas center."""
        canvas = self.map_canvas
        # Get current canvas view center
        cx = canvas.canvasx(canvas.winfo_width() / 2)
        cy = canvas.canvasy(canvas.winfo_height() / 2)
        # Zoom towards the center
        self.zoom_map_at_point(factor, cx, cy)

    def set_map_zoom(self, new_zoom_level):
        """Sets absolute zoom level, centered on current canvas center."""
        safe_zoom = max(0.1, min(6.0, float(new_zoom_level)))  # Clamp to new limits
        current_zoom = self.map_zoom_level
        if current_zoom != safe_zoom:
            factor = safe_zoom / current_zoom
            # Calculate center point to zoom around
            canvas = self.map_canvas
            cx = canvas.canvasx(canvas.winfo_width() / 2)
            cy = canvas.canvasy(canvas.winfo_height() / 2)
            # Apply zoom using the calculated factor
            self.zoom_map_at_point(factor, cx, cy)  # zoom_map_at_point handles redraw

    def get_zoomed_tile_size(self):
        """Calculates the current TILE size (base 8x8) based on zoom."""
        # Base size for 100% zoom is 8 pixels per tile edge
        zoomed_size = 8 * self.map_zoom_level
        # Ensure minimum size of 1 pixel
        return max(1, int(zoomed_size))

    def zoom_map_at_point(self, factor, zoom_x_canvas, zoom_y_canvas):
        """Zooms the map by 'factor', keeping the point (zoom_x/y_canvas) stationary,
        and clamps scroll to prevent top/left gaps when map is smaller than canvas."""
        canvas = self.map_canvas
        current_zoom = self.map_zoom_level
        min_zoom, max_zoom = 0.1, 6.0  # Use defined limits
        new_zoom = max(min_zoom, min(max_zoom, current_zoom * factor))

        # Only proceed if zoom actually changes significantly
        if abs(new_zoom - current_zoom) < 1e-9:
            return

        # --- Calculate scaling and update zoom level ---
        scale_change = new_zoom / current_zoom
        self.map_zoom_level = new_zoom  # Update zoom level state FIRST

        # --- Initial Scroll Adjustment (Zoom to Cursor) ---
        # Calculate where the map point under the cursor *would* move to
        new_x = zoom_x_canvas * scale_change
        new_y = zoom_y_canvas * scale_change

        # Calculate how much the view needs to shift to counteract this movement
        delta_x = new_x - zoom_x_canvas
        delta_y = new_y - zoom_y_canvas

        # Apply the initial scroll adjustment based on cursor position
        canvas.xview_scroll(int(round(delta_x)), "units")
        canvas.yview_scroll(int(round(delta_y)), "units")

        # --- vvv NEW: Clamping Scroll Position vvv ---
        # Calculate the total pixel dimensions of the map content at the NEW zoom level
        # Note: get_zoomed_tile_size() now uses the updated self.map_zoom_level
        zoomed_tile_size_after_zoom = (
            self.get_zoomed_tile_size()
        )  # Base tile size * new_zoom
        map_total_pixel_width_new = (
            map_width * SUPERTILE_GRID_DIM * zoomed_tile_size_after_zoom
        )
        map_total_pixel_height_new = (
            map_height * SUPERTILE_GRID_DIM * zoomed_tile_size_after_zoom
        )

        # Get the actual pixel dimensions of the canvas widget itself
        canvas_widget_width = canvas.winfo_width()
        canvas_widget_height = canvas.winfo_height()

        # Get the current scroll position *after* the initial adjustment
        current_xview = canvas.xview()
        current_yview = canvas.yview()

        # Check and clamp horizontal scroll if map is narrower than canvas
        needs_x_clamp = False
        if map_total_pixel_width_new < canvas_widget_width:
            # If map is smaller, top-left must be at 0. Check if it isn't (allow small float error).
            if current_xview[0] > 1e-6:
                needs_x_clamp = True

        # Check and clamp vertical scroll if map is shorter than canvas
        needs_y_clamp = False
        if map_total_pixel_height_new < canvas_widget_height:
            # If map is smaller, top-left must be at 0.
            if current_yview[0] > 1e-6:
                needs_y_clamp = True

        # Apply clamping if needed
        if needs_x_clamp:
            canvas.xview_moveto(0.0)
        if needs_y_clamp:
            canvas.yview_moveto(0.0)

        self.draw_map_canvas()
        self.draw_minimap()

    # --- File Menu Commands ---
    # ... (new_project, save/load tileset/supertile/map remain mostly unchanged,
    #      ensure new_project resets new state like grid toggles, window view) ...
    def new_project(self):
        global tileset_patterns, tileset_colors, current_tile_index, num_tiles_in_set
        global supertiles_data, current_supertile_index, num_supertiles, selected_tile_for_supertile
        global map_data, map_width, map_height, selected_supertile_for_map, last_painted_map_cell
        global tile_clipboard_pattern, tile_clipboard_colors, supertile_clipboard_data

        confirm = True
        if self.project_modified:  # Only ask if modified
            confirm = messagebox.askokcancel(
                "New Project", "Discard all current unsaved changes and start new?"
            )

        if confirm:
            # Reset data structures
            tileset_patterns = [
                [[0] * TILE_WIDTH for _ in range(TILE_HEIGHT)] for _ in range(MAX_TILES)
            ]
            tileset_colors = [
                [(WHITE_IDX, BLACK_IDX) for _ in range(TILE_HEIGHT)]
                for _ in range(MAX_TILES)
            ]
            current_tile_index = 0
            num_tiles_in_set = 1
            selected_tile_for_supertile = 0

            supertiles_data = [
                [[0] * SUPERTILE_GRID_DIM for _ in range(SUPERTILE_GRID_DIM)]
                for _ in range(MAX_SUPERTILES)
            ]
            current_supertile_index = 0
            num_supertiles = 1
            selected_supertile_for_map = 0

            map_width = DEFAULT_MAP_WIDTH
            map_height = DEFAULT_MAP_HEIGHT
            map_data = [[0 for _ in range(map_width)] for _ in range(map_height)]
            last_painted_map_cell = None

            # Reset clipboards
            tile_clipboard_pattern = None
            tile_clipboard_colors = None
            supertile_clipboard_data = None
            self.map_clipboard_data = None # Clear map clipboard

            # Reset Palette
            self.active_msx_palette = []
            for r, g, b in MSX2_RGB7_VALUES: # Use explicit loop
                 self.active_msx_palette.append(self._rgb7_to_hex(r, g, b))
            self.selected_palette_slot = 0
            global selected_color_index
            selected_color_index = WHITE_IDX

            # --- Reset UI state ---
            self.map_zoom_level = 1.0
            self.show_supertile_grid.set(False)
            self.show_window_view.set(False)
            self.grid_color_index = 1
            self.window_view_tile_x = 0
            self.window_view_tile_y = 0
            self.window_view_tile_w.set(DEFAULT_WIN_VIEW_WIDTH_TILES)
            self.window_view_tile_h.set(DEFAULT_WIN_VIEW_HEIGHT_TILES)
            self.current_mouse_action = None
            self.window_view_resize_handle = None

            # --- Reset Map Selection and Preview State ---
            self._clear_map_selection()  # Use helper to clear visual and state
            self._clear_paste_preview_rect() # Clear paste preview
            self.is_shift_pressed = False  # Ensure modifier keys are reset
            self.is_ctrl_pressed = False

            # Reset project tracking
            self.current_project_base_path = None
            self.project_modified = False
            self._update_window_title()

            # Clear caches and update displays
            self.clear_all_caches()
            self.invalidate_minimap_background_cache()
            self._trigger_minimap_reconfigure()
            self.update_all_displays(changed_level="all")

            self._update_editor_button_states()
            self._update_edit_menu_state()
            # print("New project started.")

    def save_palette(self, filepath=None):
        """Saves the current 16 active palette colors to a binary file.
        Returns True on success, False on failure/cancel.
        If filepath is None, prompts the user.
        """
        save_path = filepath
        # Prompt user if no path provided
        if not save_path:
            save_path = filedialog.asksaveasfilename(
                defaultextension=".msxpal",
                filetypes=[("MSX Palette File", "*.msxpal"), ("All Files", "*.*")],
                title="Save MSX Palette As...",
            )
        # Return False if user cancelled dialog
        if not save_path:
            return False

        try:
            # Open file in binary write mode
            with open(save_path, "wb") as f:
                # Sanity check palette length
                if len(self.active_msx_palette) != 16:
                    # Use internal print for non-interactive error
                    print("ERROR: Active palette length is not 16 during save!")
                    # Show message box only if called directly by user
                    if filepath is None:
                        messagebox.showerror(
                            "Palette Error",
                            "Internal Error: Active palette does not contain 16 colors.",
                        )
                    return False  # Indicate failure

                # Write each color as 3 bytes (R,G,B 0-7)
                for i in range(16):
                    hex_color = self.active_msx_palette[i]
                    r, g, b = self._hex_to_rgb7(hex_color)  # Convert hex to 0-7 range
                    packed_bytes = struct.pack("BBB", r, g, b)  # Pack as 3 bytes
                    f.write(packed_bytes)

            # Show success message ONLY if called directly by user
            if filepath is None:
                messagebox.showinfo(
                    "Save Successful",
                    f"Palette saved successfully to {os.path.basename(save_path)}",
                )
            return True  # Indicate success

        except Exception as e:
            # Always show error message on failure
            messagebox.showerror(
                "Save Palette Error",
                f"Failed to save palette file '{os.path.basename(save_path)}':\n{e}",
            )
            return False  # Indicate failure

    def open_palette(self, filepath=None):
        """Loads a 16-color palette from a binary file.
        Returns True on success, False on failure/cancel.
        If filepath is None, prompts the user.
        """
        load_path = filepath
        # Prompt user if no path provided
        if not load_path:
            load_path = filedialog.askopenfilename(
                filetypes=[("MSX Palette File", "*.msxpal"), ("All Files", "*.*")],
                title="Open MSX Palette",
            )
        # Return False if user cancelled dialog
        if not load_path:
            return False

        try:
            expected_size = 16 * 3  # 16 colors * 3 bytes/color
            new_palette_hex = []  # Temp list for loaded colors

            # Open file in binary read mode
            with open(load_path, "rb") as f:
                # Read expected bytes (+1 to check size)
                palette_data = f.read(expected_size + 1)

                # Validate file size
                if len(palette_data) < expected_size:
                    raise ValueError(
                        f"Invalid file size. Expected {expected_size} bytes, got {len(palette_data)}."
                    )
                if len(palette_data) > expected_size:
                    # Warn but proceed if file is larger
                    print(
                        f"Warning: File '{os.path.basename(load_path)}' is larger than expected ({expected_size} bytes). Extra data ignored."
                    )

                # Process the 16 colors (48 bytes)
                for i in range(16):
                    offset = i * 3
                    # Unpack 3 bytes for R, G, B (0-7)
                    r, g, b = struct.unpack_from("BBB", palette_data, offset)

                    # Validate RGB range (0-7)
                    if not (0 <= r <= 7 and 0 <= g <= 7 and 0 <= b <= 7):
                        print(
                            f"Warning: Invalid RGB ({r},{g},{b}) at slot {i} in '{os.path.basename(load_path)}'. Clamping."
                        )
                        r = max(0, min(7, r))
                        g = max(0, min(7, g))
                        b = max(0, min(7, b))

                    # Convert valid/clamped RGB(0-7) to hex string
                    hex_color = self._rgb7_to_hex(r, g, b)
                    new_palette_hex.append(hex_color)

            # --- Confirmation and Update ---
            confirm = True  # Assume confirmed if called internally
            if filepath is None:  # Ask only if user initiated this specific load
                confirm = messagebox.askokcancel(
                    "Load Palette",
                    "Replace the current active palette with data from this file?",
                )

            if confirm:
                # Commit the loaded palette
                self.active_msx_palette = new_palette_hex
                # Reset palette editor selection
                self.selected_palette_slot = 0
                # Reset tile editor color selection
                global selected_color_index
                selected_color_index = 0
                # Palette change invalidates everything visual
                self.clear_all_caches()
                self.invalidate_minimap_background_cache()  # Also invalidate minimap
                self.update_all_displays(changed_level="all")
                # Switch tab only if loading individually
                if filepath is None:
                    self.notebook.select(self.tab_palette_editor)
                    messagebox.showinfo(
                        "Load Successful",
                        f"Loaded palette from {os.path.basename(load_path)}",
                    )
                return True  # Indicate success
            else:
                # User cancelled confirmation
                return False

        # --- Exception Handling ---
        except FileNotFoundError:
            messagebox.showerror("Open Error", f"File not found:\n{load_path}")
            return False
        except (
            struct.error,
            ValueError,
            EOFError,
        ) as e:  # Catch struct, validation, and read errors
            messagebox.showerror(
                "Open Palette Error",
                f"Invalid data, size, or format in palette file '{os.path.basename(load_path)}':\n{e}",
            )
            return False
        except Exception as e:
            messagebox.showerror(
                "Open Palette Error",
                f"Failed to open or parse palette file '{os.path.basename(load_path)}':\n{e}",
            )
            return False

    def save_tileset(self, filepath=None):
        """Saves the current tileset data to a binary file.
        Returns True on success, False on failure/cancel.
        If filepath is None, prompts the user.
        """
        global num_tiles_in_set, tileset_patterns, tileset_colors
        save_path = filepath
        if not save_path:
            save_path = filedialog.asksaveasfilename(
                defaultextension=".SC4Tiles",
                filetypes=[("MSX Tileset", "*.SC4Tiles"), ("All Files", "*.*")],
                title="Save Tileset As...",
            )
        if not save_path:
            return False

        try:
            with open(save_path, "wb") as f:
                # Write number of tiles
                num_byte = struct.pack("B", num_tiles_in_set)
                f.write(num_byte)
                # Write data for each tile
                for i in range(num_tiles_in_set):
                    # Write pattern data (8 bytes)
                    pattern = tileset_patterns[i]
                    for r in range(TILE_HEIGHT):
                        byte_val = 0
                        row_pattern = pattern[r]
                        for c in range(TILE_WIDTH):
                            if row_pattern[c] == 1:
                                byte_val = byte_val | (1 << (7 - c))
                        pattern_byte = struct.pack("B", byte_val)
                        f.write(pattern_byte)
                    # Write color data (8 bytes)
                    colors = tileset_colors[i]
                    for r in range(TILE_HEIGHT):
                        fg_idx, bg_idx = colors[r]
                        color_byte_val = ((fg_idx & 0x0F) << 4) | (bg_idx & 0x0F)
                        color_byte = struct.pack("B", color_byte_val)
                        f.write(color_byte)
            # Show success message ONLY if called directly by user
            if filepath is None:
                messagebox.showinfo(
                    "Save Successful",
                    f"Tileset saved successfully to {os.path.basename(save_path)}",
                )
            return True  # Indicate success
        except Exception as e:
            messagebox.showerror(
                "Save Tileset Error",
                f"Failed to save tileset file '{os.path.basename(save_path)}':\n{e}",
            )
            return False  # Indicate failure

    def open_tileset(self, filepath=None):
        """Loads tileset data from a binary file.
        Returns True on success, False on failure/cancel.
        If filepath is None, prompts the user.
        """
        global tileset_patterns, tileset_colors, current_tile_index, num_tiles_in_set, selected_tile_for_supertile
        load_path = filepath
        if not load_path:
            load_path = filedialog.askopenfilename(
                filetypes=[("MSX Tileset", "*.SC4Tiles"), ("All Files", "*.*")],
                title="Open Tileset",
            )
        if not load_path:
            return False

        try:
            with open(load_path, "rb") as f:
                # Read count
                num_tiles_byte = f.read(1)
                if not num_tiles_byte:
                    raise ValueError("File empty or missing tile count byte.")
                loaded_num_tiles = struct.unpack("B", num_tiles_byte)[0]
                # Use 0 if file says 0 tiles? For now, require at least 1.
                if not (1 <= loaded_num_tiles <= MAX_TILES):
                    raise ValueError(
                        f"Invalid tile count in file: {loaded_num_tiles} (must be 1-{MAX_TILES})"
                    )

                # Prepare temp storage
                new_patterns = [
                    [[0] * TILE_WIDTH for _r in range(TILE_HEIGHT)]
                    for _i in range(MAX_TILES)
                ]
                new_colors = [
                    [(WHITE_IDX, BLACK_IDX) for _r in range(TILE_HEIGHT)]
                    for _i in range(MAX_TILES)
                ]

                # Read data
                for i in range(loaded_num_tiles):
                    # Pattern
                    pattern_bytes = f.read(
                        TILE_HEIGHT
                    )  # Read all 8 pattern bytes at once
                    if len(pattern_bytes) < TILE_HEIGHT:
                        raise EOFError(f"EOF pattern T:{i}")
                    for r in range(TILE_HEIGHT):
                        byte_val = pattern_bytes[r]  # Directly use byte value
                        for c in range(TILE_WIDTH):
                            pixel_bit = (byte_val >> (7 - c)) & 1
                            new_patterns[i][r][c] = pixel_bit
                    # Color
                    color_bytes = f.read(TILE_HEIGHT)  # Read all 8 color bytes at once
                    if len(color_bytes) < TILE_HEIGHT:
                        raise EOFError(f"EOF color T:{i}")
                    for r in range(TILE_HEIGHT):
                        byte_val = color_bytes[r]
                        fg_idx = (byte_val >> 4) & 0x0F
                        bg_idx = byte_val & 0x0F
                        # Basic validation for palette indices read from file
                        if not (0 <= fg_idx < 16 and 0 <= bg_idx < 16):
                            print(
                                f"Warning: Invalid palette index T:{i} R:{r} ({fg_idx},{bg_idx}). Using default."
                            )
                            new_colors[i][r] = (WHITE_IDX, BLACK_IDX)
                        else:
                            new_colors[i][r] = (fg_idx, bg_idx)

            # --- Confirmation and Update ---
            confirm = True
            if filepath is None:  # Ask only if user initiated this specific load
                confirm = messagebox.askokcancel(
                    "Load Tileset",
                    f"Replace current tileset with {loaded_num_tiles} tile(s) from this file?",
                )

            if confirm:
                # Commit changes
                tileset_patterns = new_patterns
                tileset_colors = new_colors
                num_tiles_in_set = loaded_num_tiles
                # Clamp selections to new range
                current_tile_index = max(
                    0, min(current_tile_index, num_tiles_in_set - 1)
                )
                selected_tile_for_supertile = max(
                    0, min(selected_tile_for_supertile, num_tiles_in_set - 1)
                )

                # Clear relevant caches and update UI
                self.clear_all_caches()  # Tile changes affect supertiles and map
                self.invalidate_minimap_background_cache()
                self.update_all_displays(changed_level="all")
                self._update_editor_button_states()  # <<< ADDED HERE
                self._update_edit_menu_state()  # Update copy/paste

                # Switch tab only if loading individually
                if filepath is None:
                    self.notebook.select(self.tab_tile_editor)
                    messagebox.showinfo(
                        "Load Successful",
                        f"Loaded {num_tiles_in_set} tiles from {os.path.basename(load_path)}",
                    )
                # Mark project as modified only if loaded individually
                if filepath is None:
                    self._mark_project_modified()
                return True  # Indicate success
            else:
                return False  # User cancelled confirmation

        # --- Exception Handling ---
        except FileNotFoundError:
            messagebox.showerror("Open Error", f"File not found:\n{load_path}")
            return False
        except (EOFError, ValueError, struct.error) as e:
            messagebox.showerror(
                "Open Tileset Error",
                f"Invalid data, size, or format in tileset file '{os.path.basename(load_path)}':\n{e}",
            )
            return False
        except Exception as e:
            messagebox.showerror(
                "Open Tileset Error",
                f"Failed to open or parse tileset file '{os.path.basename(load_path)}':\n{e}",
            )
            return False

    def save_supertiles(self, filepath=None):
        """Saves the current supertile definitions to a binary file.
        Returns True on success, False on failure/cancel.
        If filepath is None, prompts the user.
        """
        global num_supertiles, supertiles_data
        save_path = filepath
        if not save_path:
            save_path = filedialog.asksaveasfilename(
                defaultextension=".SC4Super",
                filetypes=[("MSX Supertiles", "*.SC4Super"), ("All Files", "*.*")],
                title="Save Supertiles As...",
            )
        if not save_path:
            return False

        try:
            with open(save_path, "wb") as f:
                # Write count
                num_byte = struct.pack("B", num_supertiles)
                f.write(num_byte)
                # Write data
                for i in range(num_supertiles):
                    definition = supertiles_data[i]
                    for r in range(SUPERTILE_GRID_DIM):
                        row_data = definition[r]
                        for c in range(SUPERTILE_GRID_DIM):
                            tile_index = row_data[c]
                            index_byte = struct.pack("B", tile_index)
                            f.write(index_byte)
            # Show success message ONLY if called directly
            if filepath is None:
                messagebox.showinfo(
                    "Save Successful",
                    f"Supertiles saved successfully to {os.path.basename(save_path)}",
                )
            return True  # Indicate success
        except Exception as e:
            messagebox.showerror(
                "Save Supertile Error",
                f"Failed to save supertiles file '{os.path.basename(save_path)}':\n{e}",
            )
            return False  # Indicate failure

    def open_supertiles(self, filepath=None):
        """Loads supertile definitions from a binary file.
        Returns True on success, False on failure/cancel.
        If filepath is None, prompts the user.
        """
        global supertiles_data, num_supertiles, current_supertile_index, selected_supertile_for_map, num_tiles_in_set
        load_path = filepath
        if not load_path:
            load_path = filedialog.askopenfilename(
                filetypes=[("MSX Supertiles", "*.SC4Super"), ("All Files", "*.*")],
                title="Open Supertiles",
            )
        if not load_path:
            return False

        try:
            with open(load_path, "rb") as f:
                # Read count
                num_st_byte = f.read(1)
                if not num_st_byte:
                    raise ValueError("File empty or missing supertile count.")
                loaded_num_st = struct.unpack("B", num_st_byte)[0]
                if not (1 <= loaded_num_st <= MAX_SUPERTILES):
                    raise ValueError(
                        f"Invalid supertile count in file: {loaded_num_st} (must be 1-{MAX_SUPERTILES})"
                    )

                # Prepare temp storage
                new_st_data = [
                    [[0] * SUPERTILE_GRID_DIM for _r in range(SUPERTILE_GRID_DIM)]
                    for _i in range(MAX_SUPERTILES)
                ]

                # Read data
                bytes_per_supertile = SUPERTILE_GRID_DIM * SUPERTILE_GRID_DIM
                for i in range(loaded_num_st):
                    st_bytes = f.read(bytes_per_supertile)
                    if len(st_bytes) < bytes_per_supertile:
                        raise EOFError(f"EOF supertile {i}")
                    byte_idx = 0
                    for r in range(SUPERTILE_GRID_DIM):
                        for c in range(SUPERTILE_GRID_DIM):
                            tile_index = st_bytes[byte_idx]  # Directly use byte value
                            byte_idx += 1
                            # Validate tile index read from file against current tileset size
                            if not (0 <= tile_index < num_tiles_in_set):
                                print(
                                    f"Warning: Invalid Tile index {tile_index} in Supertile {i} at [{r},{c}]. Resetting to 0."
                                )
                                new_st_data[i][r][c] = 0
                            else:
                                new_st_data[i][r][c] = tile_index

            # --- Confirmation and Update ---
            confirm = True
            if filepath is None:  # Ask only if user initiated this specific load
                confirm = messagebox.askokcancel(
                    "Load Supertiles",
                    f"Replace current supertiles with {loaded_num_st} definition(s) from this file?",
                )

            if confirm:
                # Commit changes
                supertiles_data = new_st_data
                num_supertiles = loaded_num_st
                # Clamp selections to new range
                current_supertile_index = max(
                    0, min(current_supertile_index, num_supertiles - 1)
                )
                selected_supertile_for_map = max(
                    0, min(selected_supertile_for_map, num_supertiles - 1)
                )

                # Clear caches and update UI
                self.supertile_image_cache.clear()
                self.invalidate_minimap_background_cache()  # Map appearance might change
                self.update_all_displays(
                    changed_level="supertile"
                )  # Update ST editor + Map stuff
                self._update_editor_button_states()  # <<< ADDED HERE
                self._update_edit_menu_state()  # Update copy/paste

                # Switch tab only if loading individually
                if filepath is None:
                    self.notebook.select(self.tab_supertile_editor)
                    messagebox.showinfo(
                        "Load Successful",
                        f"Loaded {num_supertiles} supertiles from {os.path.basename(load_path)}",
                    )
                # Mark project as modified only if loaded individually
                if filepath is None:
                    self._mark_project_modified()
                return True  # Indicate success
            else:
                return False  # User cancelled confirmation

        # --- Exception Handling ---
        except FileNotFoundError:
            messagebox.showerror("Open Error", f"File not found:\n{load_path}")
            return False
        except (EOFError, ValueError, struct.error) as e:
            messagebox.showerror(
                "Open Supertile Error",
                f"Invalid data, size, or format in supertile file '{os.path.basename(load_path)}':\n{e}",
            )
            return False
        except Exception as e:
            messagebox.showerror(
                "Open Supertile Error",
                f"Failed to open or parse supertiles file '{os.path.basename(load_path)}':\n{e}",
            )
            return False

    def save_map(self, filepath=None):
        """Saves the current map data to a binary file.
        Returns True on success, False on failure/cancel.
        If filepath is None, prompts the user.
        """
        global map_width, map_height, map_data
        save_path = filepath
        if not save_path:
            save_path = filedialog.asksaveasfilename(
                defaultextension=".SC4Map",
                filetypes=[("MSX Map", "*.SC4Map"), ("All Files", "*.*")],
                title="Save Map As...",
            )
        if not save_path:
            return False

        try:
            with open(save_path, "wb") as f:
                # Write dimensions (Big-endian)
                dim_bytes = struct.pack(">HH", map_width, map_height)
                f.write(dim_bytes)
                # Write map data
                for r in range(map_height):
                    row_data = map_data[r]
                    for c in range(map_width):
                        supertile_index = row_data[c]
                        index_byte = struct.pack("B", supertile_index)
                        f.write(index_byte)
            # Show success message ONLY if called directly
            if filepath is None:
                messagebox.showinfo(
                    "Save Successful",
                    f"Map saved successfully to {os.path.basename(save_path)}",
                )
            return True  # Indicate success
        except Exception as e:
            messagebox.showerror(
                "Save Map Error",
                f"Failed to save map file '{os.path.basename(save_path)}':\n{e}",
            )
            return False  # Indicate failure

    def open_map(self, filepath=None):
        """Loads map data from a binary file.
        Returns True on success, False on failure/cancel.
        If filepath is None, prompts the user.
        """
        global map_data, map_width, map_height
        load_path = filepath
        if not load_path:
            load_path = filedialog.askopenfilename(
                filetypes=[("MSX Map", "*.SC4Map"), ("All Files", "*.*")],
                title="Open Map",
            )
        if not load_path:
            return False

        try:
            with open(load_path, "rb") as f:
                # Read header
                dim_bytes = f.read(4)
                if len(dim_bytes) < 4:
                    raise ValueError("Invalid map header")
                # Unpack dimensions
                loaded_w, loaded_h = struct.unpack(">HH", dim_bytes)
                # Validate dimensions
                min_dim, max_dim = 1, 1024
                if not (
                    min_dim <= loaded_w <= max_dim and min_dim <= loaded_h <= max_dim
                ):
                    raise ValueError(f"Invalid dimensions: {loaded_w}x{loaded_h}")

                # Prepare temp storage
                new_map_data = [[0 for _c in range(loaded_w)] for _r in range(loaded_h)]

                # Read data
                for r in range(loaded_h):
                    for c in range(loaded_w):
                        st_idx_byte = f.read(1)
                        if not st_idx_byte:
                            raise EOFError(f"EOF map at row {r}, col {c}")
                        supertile_index = struct.unpack("B", st_idx_byte)[0]
                        new_map_data[r][c] = supertile_index

            # --- Confirmation and Update ---
            confirm = True
            if filepath is None:
                confirm = messagebox.askokcancel("Load Map", "Replace current map?")

            if confirm:
                # Commit changes
                map_width = loaded_w
                map_height = loaded_h
                map_data = new_map_data
                # Invalidate minimap cache and update UI
                self.invalidate_minimap_background_cache()
                self.update_all_displays(changed_level="map")
                self._trigger_minimap_reconfigure()  # Check/fix minimap aspect AFTER map update
                # Switch tab only if loading individually
                if filepath is None:
                    self.notebook.select(self.tab_map_editor)
                    messagebox.showinfo(
                        "Load Successful",
                        f"Loaded {map_width}x{map_height} map from {os.path.basename(load_path)}",
                    )
                return True  # Indicate success
            else:
                return False  # User cancelled confirmation

        # --- Exception Handling ---
        except FileNotFoundError:
            messagebox.showerror("Open Error", f"File not found:\n{load_path}")
            return False
        except (EOFError, ValueError, struct.error) as e:
            messagebox.showerror(
                "Open Map Error",
                f"Invalid data, size, or format in map file '{os.path.basename(load_path)}':\n{e}",
            )
            return False
        except Exception as e:
            messagebox.showerror(
                "Open Map Error",
                f"Failed to open or parse map file '{os.path.basename(load_path)}':\n{e}",
            )
            return False

    # --- Project Save/Load Methods ---

    def save_project_as(self):
        """Prompts user for a base project name and saves all four component files."""
        # Ask for base path (user types name, selects directory)
        base_path = filedialog.asksaveasfilename(
            filetypes=[("MSX Project (Enter Base Name)", "*.*")],  # Filter description
            title="Save Project As (Enter Base Name)",
        )
        # Exit if cancelled
        if not base_path:
            return

        # Construct full paths for each component file
        pal_path = base_path + ".msxpal"
        til_path = base_path + ".SC4Tiles"
        sup_path = base_path + ".SC4Super"
        map_path = base_path + ".SC4Map"

        # Attempt to save all components sequentially
        # Use the modified save methods which return True/False
        # Stop saving if any component fails
        success = True
        if success:
            success = self.save_palette(pal_path)
        if success:
            success = self.save_tileset(til_path)
        if success:
            success = self.save_supertiles(sup_path)
        if success:
            success = self.save_map(map_path)

        # Update state and UI if all saves were successful
        if success:
            self.current_project_base_path = base_path  # Store the base path
            self.project_modified = False
            self._update_window_title()
        else:
            # Individual error messages should have been shown by the failing save_* method
            messagebox.showerror(
                "Project Save Error", "One or more project components failed to save."
            )

    def save_project(self):
        """Saves the project using the current base path, or calls Save As if none."""
        # Check if a project path is already known
        if self.current_project_base_path:
            base_path = self.current_project_base_path
            # Construct component paths
            pal_path = base_path + ".msxpal"
            til_path = base_path + ".SC4Tiles"
            sup_path = base_path + ".SC4Super"
            map_path = base_path + ".SC4Map"

            # Attempt to save all components
            success = True
            if success:
                success = self.save_palette(pal_path)
            if success:
                success = self.save_tileset(til_path)
            if success:
                success = self.save_supertiles(sup_path)
            if success:
                success = self.save_map(map_path)

            # Show appropriate message
            if success:
                self.project_modified = False
                self._update_window_title()
            else:
                messagebox.showerror(
                    "Project Save Error",
                    "One or more project components failed to save.",
                )
        else:
            # If no project path is known, act like "Save As..."
            self.save_project_as()

    def open_project(self):
        """Prompts user to select ONE project file, then loads all four components."""
        # Ask user to select any component file
        filepath = filedialog.askopenfilename(
            filetypes=[
                (
                    "MSX Tileset File (*.SC4Tiles)",
                    "*.SC4Tiles",
                ),  # Suggest tileset first
                ("MSX Palette File (*.msxpal)", "*.msxpal"),
                ("MSX Supertile File (*.SC4Super)", "*.SC4Super"),
                ("MSX Map File (*.SC4Map)", "*.SC4Map"),
                ("All Files", "*.*"),
            ],
            title="Open Project (Select Any Component File)",
        )
        # Exit if cancelled
        if not filepath:
            return

        # --- Determine Base Path ---
        directory = os.path.dirname(filepath)
        base_name_with_ext = os.path.basename(filepath)
        base_name, _ = os.path.splitext(base_name_with_ext)
        base_path = os.path.join(directory, base_name)

        # --- Construct Expected Paths ---
        pal_path = base_path + ".msxpal"
        til_path = base_path + ".SC4Tiles"
        sup_path = base_path + ".SC4Super"
        map_path = base_path + ".SC4Map"

        # --- Check Existence ---
        missing_files = []
        if not os.path.exists(pal_path):
            missing_files.append(os.path.basename(pal_path))
        if not os.path.exists(til_path):
            missing_files.append(os.path.basename(til_path))
        if not os.path.exists(sup_path):
            missing_files.append(os.path.basename(sup_path))
        if not os.path.exists(map_path):
            missing_files.append(os.path.basename(map_path))

        # Abort if files are missing
        if missing_files:
            messagebox.showerror(
                "Open Project Error",
                f"Cannot open project '{base_name}'.\n"
                f"Missing component file(s):\n" + "\n".join(missing_files),
            )
            return

        # --- Confirmation (Check for unsaved changes) ---
        if self.project_modified:
            confirm_discard = messagebox.askokcancel(
                "Unsaved Changes",
                f"Discard current unsaved changes and open project '{base_name}'?",
                icon="warning"
            )
            if not confirm_discard:
                return
        # If no unsaved changes, proceed without extra confirmation

        # --- >> ADDED: Reset interaction state BEFORE loading << ---
        # This ensures state from dialogs doesn't interfere
        self.is_ctrl_pressed = False
        self.is_shift_pressed = False
        self.current_mouse_action = None
        # --- End Reset ---

        # --- Clear existing state BEFORE loading ---
        # Clear clipboards and previews
        global tile_clipboard_pattern, tile_clipboard_colors, supertile_clipboard_data
        tile_clipboard_pattern = None
        tile_clipboard_colors = None
        supertile_clipboard_data = None
        self.map_clipboard_data = None
        self._clear_map_selection() # Clear selection state/visual
        self._clear_paste_preview_rect() # Clear paste preview visual

        # Clear caches BEFORE loading new data
        self.clear_all_caches()
        self.invalidate_minimap_background_cache()

        # --- Attempt to Load All Components ---
        success = True
        print(f"Loading project '{base_name}'...")

        # Load sequentially, checking success
        if success:
            print(f"  Loading palette: {pal_path}")
            success = self.open_palette(pal_path)
        if success:
            print(f"  Loading tileset: {til_path}")
            success = self.open_tileset(til_path)
        if success:
            print(f"  Loading supertiles: {sup_path}")
            success = self.open_supertiles(sup_path)
        if success:
            print(f"  Loading map: {map_path}")
            success = self.open_map(map_path)

        # --- >> ADDED: Reset interaction state AGAIN AFTER loading << ---
        # Ensures clean state before final UI updates and user interaction
        self.is_ctrl_pressed = False
        self.is_shift_pressed = False
        self.current_mouse_action = None
        # --- End Reset ---

        # --- Final Actions ---
        if success:
            self.project_modified = False # Project is now unmodified after successful load
            self.current_project_base_path = base_path
            self._update_window_title()
            self._update_editor_button_states()
            self.notebook.select(self.tab_map_editor) # Default to map tab after load
            # Update everything visually after all loads complete successfully
            self.update_all_displays(changed_level="all")
            self._update_edit_menu_state()
            # Explicitly update cursor after everything is loaded and map tab selected
            self.root.after(10, self._update_map_cursor) # Short delay might help ensure focus is set
        else:
            messagebox.showerror(
                "Project Open Error",
                f"Failed to load one or more components for project '{base_name}'. The application state might be inconsistent.",
            )
            # Still update states even on failure, as some parts might have loaded
            self.project_modified = True # Mark as modified if load failed partially
            self._update_window_title()
            self._update_editor_button_states()
            self.update_all_displays(changed_level="all")
            self._update_edit_menu_state()
            # Explicitly update cursor even on failure
            self.root.after(10, self._update_map_cursor)

    # --- Edit Menu Commands ---

    def set_tileset_size(self):
        global num_tiles_in_set, current_tile_index, selected_tile_for_supertile

        prompt = f"Enter number of tiles (1-{MAX_TILES}):"
        new_size_str = simpledialog.askstring(
            "Set Tileset Size", prompt, initialvalue=str(num_tiles_in_set)
        )

        if new_size_str:
            try:
                new_size = int(new_size_str)

                # Validate range first
                if not (1 <= new_size <= MAX_TILES):
                    messagebox.showerror(
                        "Invalid Size", f"Size must be between 1 and {MAX_TILES}."
                    )
                    return  # Exit if invalid

                if new_size == num_tiles_in_set:
                    return  # No change

                reduced = new_size < num_tiles_in_set
                # Assume confirmed unless reducing
                confirmed = True
                if reduced:
                    # Check usage before confirming reduction
                    affected_supertiles = set()
                    for del_idx in range(new_size, num_tiles_in_set):
                        usage = self._check_tile_usage(del_idx)
                        for st_idx in usage:
                            affected_supertiles.add(st_idx)

                    confirm_prompt = f"Reducing size to {new_size} will discard tiles {new_size} to {num_tiles_in_set-1}."
                    if affected_supertiles:
                        confirm_prompt += "\n\n*** WARNING! ***\nDiscarded tiles are used by Supertile(s):\n"
                        affected_list = sorted(list(affected_supertiles))
                        confirm_prompt += ", ".join(map(str, affected_list[:10]))
                        if len(affected_list) > 10:
                            confirm_prompt += "..."
                        confirm_prompt += "\n\nReferences to discarded tiles in these Supertiles will be reset to Tile 0."

                    confirmed = messagebox.askokcancel(
                        "Reduce Size", confirm_prompt, icon="warning"
                    )

                # Proceed if confirmed (or not reducing)
                if confirmed:
                    self._mark_project_modified()  # Mark modified before changing data

                    # Handle reduction: Clear references *before* resizing lists
                    if reduced:
                        for del_idx in range(new_size, num_tiles_in_set):
                            # This sets references to 0, which is safe even after resize
                            self._update_supertile_refs_for_tile_change(
                                del_idx, "delete"
                            )
                        # Invalidate cache for tiles being removed
                        for i in range(new_size, num_tiles_in_set):
                            self.invalidate_tile_cache(i)
                        # Resize lists AFTER clearing refs
                        del tileset_patterns[new_size:]
                        del tileset_colors[new_size:]

                    # Handle expansion: Add blank tiles
                    elif new_size > num_tiles_in_set:
                        for _ in range(new_size - num_tiles_in_set):
                            tileset_patterns.append(
                                [[0] * TILE_WIDTH for _r in range(TILE_HEIGHT)]
                            )
                            tileset_colors.append(
                                [(WHITE_IDX, BLACK_IDX) for _r in range(TILE_HEIGHT)]
                            )

                    # Update global count
                    num_tiles_in_set = new_size

                    # Clamp indices to the new valid range
                    current_tile_index = max(
                        0, min(current_tile_index, num_tiles_in_set - 1)
                    )
                    selected_tile_for_supertile = max(
                        0, min(selected_tile_for_supertile, num_tiles_in_set - 1)
                    )

                    # Update displays, caches, and buttons
                    self.clear_all_caches()  # Easiest after resizing potentially used tiles
                    self.invalidate_minimap_background_cache()
                    self.update_all_displays(changed_level="all")
                    self._update_editor_button_states()  # <<< ADDED HERE
                    self._update_edit_menu_state()

            except ValueError:
                messagebox.showerror(
                    "Invalid Input", "Please enter a valid whole number."
                )
            except Exception as e:
                messagebox.showerror("Error", f"An error occurred: {e}")
                print(f"Error setting tileset size: {e}")  # Log detailed error

    def set_supertile_count(self):
        global num_supertiles, current_supertile_index, selected_supertile_for_map

        prompt = f"Enter number of supertiles (1-{MAX_SUPERTILES}):"
        new_count_str = simpledialog.askstring(
            "Set Supertile Count", prompt, initialvalue=str(num_supertiles)
        )

        if new_count_str:
            try:
                new_count = int(new_count_str)

                # Validate range first
                if not (1 <= new_count <= MAX_SUPERTILES):
                    messagebox.showerror(
                        "Invalid Count",
                        f"Count must be between 1 and {MAX_SUPERTILES}.",
                    )
                    return  # Exit if invalid

                if new_count == num_supertiles:
                    return  # No change

                reduced = new_count < num_supertiles
                # Assume confirmed unless reducing
                confirmed = True
                if reduced:
                    # Check usage before confirming reduction
                    affected_map_cells = []
                    for del_idx in range(new_count, num_supertiles):
                        usage = self._check_supertile_usage(del_idx)
                        affected_map_cells.extend(usage)

                    confirm_prompt = f"Reducing count to {new_count} will discard supertiles {new_count} to {num_supertiles-1}."
                    if affected_map_cells:
                        confirm_prompt += "\n\n*** WARNING! ***\nDiscarded supertiles are used on the Map."
                        # Optionally list some coordinates if needed, but maybe too verbose
                        # confirm_prompt += f" (e.g., at {affected_map_cells[0]})."
                        confirm_prompt += (
                            "\n\nReferences on the Map will be reset to Supertile 0."
                        )

                    confirmed = messagebox.askokcancel(
                        "Reduce Count", confirm_prompt, icon="warning"
                    )

                # Proceed if confirmed (or not reducing)
                if confirmed:
                    self._mark_project_modified()  # Mark modified before changing data

                    # Handle reduction: Clear references *before* resizing lists
                    if reduced:
                        for del_idx in range(new_count, num_supertiles):
                            # This sets references to 0, which is safe even after resize
                            self._update_map_refs_for_supertile_change(
                                del_idx, "delete"
                            )
                        # Invalidate cache for supertiles being removed
                        for i in range(new_count, num_supertiles):
                            self.invalidate_supertile_cache(i)
                        # Resize list AFTER clearing refs
                        del supertiles_data[new_count:]

                    # Handle expansion: Add blank supertiles
                    elif new_count > num_supertiles:
                        for _ in range(new_count - num_supertiles):
                            supertiles_data.append(
                                [
                                    [0] * SUPERTILE_GRID_DIM
                                    for _r in range(SUPERTILE_GRID_DIM)
                                ]
                            )

                    # Update global count
                    num_supertiles = new_count

                    # Clamp indices to the new valid range
                    current_supertile_index = max(
                        0, min(current_supertile_index, num_supertiles - 1)
                    )
                    selected_supertile_for_map = max(
                        0, min(selected_supertile_for_map, num_supertiles - 1)
                    )

                    # Update displays, caches, and buttons
                    self.supertile_image_cache.clear()  # Clear ST cache
                    self.invalidate_minimap_background_cache()
                    self.update_all_displays(
                        changed_level="supertile"
                    )  # Update ST + Map
                    self._update_editor_button_states()  # <<< ADDED HERE
                    self._update_edit_menu_state()

            except ValueError:
                messagebox.showerror(
                    "Invalid Input", "Please enter a valid whole number."
                )
            except Exception as e:
                messagebox.showerror("Error", f"An error occurred: {e}")
                print(f"Error setting supertile count: {e}")  # Log detailed error

    def set_map_dimensions(self):
        global map_width, map_height, map_data

        prompt = "Enter new dimensions (Width x Height):"
        dims_str = simpledialog.askstring(
            "Set Map Dimensions", prompt, initialvalue=f"{map_width}x{map_height}"
        )

        if dims_str:
            try:
                parts = dims_str.lower().split("x")
                if len(parts) != 2:
                    # Raise error for incorrect format
                    raise ValueError("Format must be WidthxHeight")

                # Parse dimensions
                new_w_str = parts[0].strip()
                new_h_str = parts[1].strip()
                new_w = int(new_w_str)
                new_h = int(new_h_str)

                # Define and check limits
                min_dim, max_dim = 1, 1024
                if not (min_dim <= new_w <= max_dim):
                    raise ValueError(f"Width must be between {min_dim} and {max_dim}")
                if not (min_dim <= new_h <= max_dim):
                    raise ValueError(f"Height must be between {min_dim} and {max_dim}")

                # Check if dimensions actually changed
                if new_w == map_width and new_h == map_height:
                    return  # No change needed

                # Ask for confirmation only if reducing size
                reducing = new_w < map_width or new_h < map_height
                confirmed = True  # Assume confirmed unless reducing
                if reducing:
                    confirm_prompt = "Reducing map size will discard data outside boundaries. Proceed?"
                    confirmed = messagebox.askokcancel("Resize Map", confirm_prompt)

                # Proceed if confirmed
                if confirmed:
                    self._mark_project_modified()
                    # Create new empty map structure
                    new_map_data = [[0 for _ in range(new_w)] for _ in range(new_h)]
                    # Determine copy boundaries
                    rows_to_copy = min(map_height, new_h)
                    cols_to_copy = min(map_width, new_w)
                    # Copy existing data
                    for r in range(rows_to_copy):
                        for c in range(cols_to_copy):
                            new_map_data[r][c] = map_data[r][c]

                    # Update global variables
                    map_width = new_w
                    map_height = new_h
                    map_data = new_map_data

                    # Redraw map display
                    self.update_all_displays(changed_level="map")
                    self._trigger_minimap_reconfigure()  # Check/fix minimap aspect AFTER map update

            except ValueError as e:
                # Handle parsing errors or validation errors
                messagebox.showerror("Invalid Input", f"Error setting dimensions: {e}")
            except Exception as e:
                # Catch other potential errors during resize/copy
                messagebox.showerror(
                    "Error", f"An unexpected error occurred during resize: {e}"
                )

    # ... (clear_current_tile, clear_current_supertile, clear_map unchanged) ...
    def clear_current_tile(self):
        global tileset_patterns, tileset_colors, current_tile_index, WHITE_IDX, BLACK_IDX
        if not (0 <= current_tile_index < num_tiles_in_set):
            return
        prompt = f"Clear pattern and reset colors for tile {current_tile_index}?"
        if messagebox.askokcancel("Clear Tile", prompt):
            self._mark_project_modified()
            tileset_patterns[current_tile_index] = [
                [0] * TILE_WIDTH for _ in range(TILE_HEIGHT)
            ]
            tileset_colors[current_tile_index] = [
                (WHITE_IDX, BLACK_IDX) for _ in range(TILE_HEIGHT)
            ]
            self.invalidate_tile_cache(current_tile_index)
            self.update_all_displays(changed_level="tile")

    def clear_current_supertile(self):
        global supertiles_data, current_supertile_index
        if not (0 <= current_supertile_index < num_supertiles):
            return
        prompt = f"Clear definition (set all to tile 0) for supertile {current_supertile_index}?"
        if messagebox.askokcancel("Clear Supertile", prompt):
            self._mark_project_modified()
            supertiles_data[current_supertile_index] = [
                [0] * SUPERTILE_GRID_DIM for _ in range(SUPERTILE_GRID_DIM)
            ]
            self.invalidate_supertile_cache(current_supertile_index)
            self.update_all_displays(changed_level="supertile")

    def clear_map(self):
        global map_data, map_width, map_height
        prompt = "Clear entire map (set all to supertile 0)?"
        if messagebox.askokcancel("Clear Map", prompt):
            self._mark_project_modified()
            map_data = [[0 for _ in range(map_width)] for _ in range(map_height)]
            self.invalidate_minimap_background_cache()
            self.update_all_displays(changed_level="map")

    def copy_current_tile(self):
        global tile_clipboard_pattern, tile_clipboard_colors, current_tile_index, num_tiles_in_set, tileset_patterns, tileset_colors
        if not (0 <= current_tile_index < num_tiles_in_set):
            messagebox.showwarning("Copy Tile", "No valid tile selected.")
            return
        tile_clipboard_pattern = copy.deepcopy(tileset_patterns[current_tile_index])
        tile_clipboard_colors = copy.deepcopy(tileset_colors[current_tile_index])
        print(f"Tile {current_tile_index} copied.")
        self._update_edit_menu_state()

    def paste_tile(self):
        global tile_clipboard_pattern, tile_clipboard_colors, current_tile_index, num_tiles_in_set, tileset_patterns, tileset_colors
        if tile_clipboard_pattern is None or tile_clipboard_colors is None:
            messagebox.showinfo("Paste Tile", "Tile clipboard is empty.")
            return
        if not (0 <= current_tile_index < num_tiles_in_set):
            messagebox.showwarning("Paste Tile", "No valid tile selected.")
            return
        self._mark_project_modified()
        tileset_patterns[current_tile_index] = copy.deepcopy(tile_clipboard_pattern)
        tileset_colors[current_tile_index] = copy.deepcopy(tile_clipboard_colors)
        self.invalidate_tile_cache(current_tile_index)
        self.update_all_displays(changed_level="tile")
        print(f"Pasted onto Tile {current_tile_index}.")

    def copy_current_supertile(self):
        global supertile_clipboard_data, current_supertile_index, num_supertiles, supertiles_data
        if not (0 <= current_supertile_index < num_supertiles):
            messagebox.showwarning("Copy Supertile", "No valid supertile selected.")
            return
        supertile_clipboard_data = copy.deepcopy(
            supertiles_data[current_supertile_index]
        )
        print(f"Supertile {current_supertile_index} copied.")
        self._update_edit_menu_state()

    def paste_supertile(self):
        global supertile_clipboard_data, current_supertile_index, num_supertiles, supertiles_data
        if supertile_clipboard_data is None:
            messagebox.showinfo("Paste Supertile", "Supertile clipboard is empty.")
            return
        if not (0 <= current_supertile_index < num_supertiles):
            messagebox.showwarning("Paste Supertile", "No valid supertile selected.")
            return
        supertiles_data[current_supertile_index] = copy.deepcopy(
            supertile_clipboard_data
        )
        self._mark_project_modified()
        self.invalidate_supertile_cache(current_supertile_index)
        self.invalidate_minimap_background_cache()  # Appearance of map cells using this ST changed
        self.update_all_displays(changed_level="supertile")
        print(f"Pasted onto Supertile {current_supertile_index}.")

    def add_new_tile(self):
        global num_tiles_in_set, current_tile_index, WHITE_IDX, BLACK_IDX
        if num_tiles_in_set >= MAX_TILES:
            messagebox.showwarning("Maximum Tiles", f"Max {MAX_TILES} tiles reached.")
            return
        num_tiles_in_set += 1
        new_tile_idx = num_tiles_in_set - 1
        self._mark_project_modified()
        tileset_patterns[new_tile_idx] = [[0] * TILE_WIDTH for _ in range(TILE_HEIGHT)]
        tileset_colors[new_tile_idx] = [
            (WHITE_IDX, BLACK_IDX) for _ in range(TILE_HEIGHT)
        ]
        current_tile_index = new_tile_idx
        self.update_all_displays(changed_level="tile")
        self.scroll_viewers_to_tile(current_tile_index)

    def add_new_supertile(self):
        global num_supertiles, current_supertile_index
        if num_supertiles >= MAX_SUPERTILES:
            messagebox.showwarning(
                "Maximum Supertiles", f"Max {MAX_SUPERTILES} supertiles reached."
            )
            return
        num_supertiles += 1
        new_st_idx = num_supertiles - 1
        self._mark_project_modified()
        supertiles_data[new_st_idx] = [
            [0] * SUPERTILE_GRID_DIM for _ in range(SUPERTILE_GRID_DIM)
        ]
        current_supertile_index = new_st_idx
        self.update_all_displays(changed_level="supertile")
        self.scroll_selectors_to_supertile(current_supertile_index)

    # ... (shift methods unchanged) ...
    def shift_tile_up(self):
        global tileset_patterns, tileset_colors, current_tile_index, num_tiles_in_set
        if not (0 <= current_tile_index < num_tiles_in_set):
            return
        current_pattern = tileset_patterns[current_tile_index]
        current_colors = tileset_colors[current_tile_index]
        first_pattern_row = current_pattern[0]
        first_color_row = current_colors[0]
        for i in range(TILE_HEIGHT - 1):
            current_pattern[i] = current_pattern[i + 1]
            current_colors[i] = current_colors[i + 1]
        current_pattern[TILE_HEIGHT - 1] = first_pattern_row
        current_colors[TILE_HEIGHT - 1] = first_color_row
        self.invalidate_tile_cache(current_tile_index)
        self.update_all_displays(changed_level="tile")
        print(f"Tile {current_tile_index} shifted up.")

    def shift_tile_down(self):
        global tileset_patterns, tileset_colors, current_tile_index, num_tiles_in_set
        if not (0 <= current_tile_index < num_tiles_in_set):
            return
        current_pattern = tileset_patterns[current_tile_index]
        current_colors = tileset_colors[current_tile_index]
        last_pattern_row = current_pattern[TILE_HEIGHT - 1]
        last_color_row = current_colors[TILE_HEIGHT - 1]
        for i in range(TILE_HEIGHT - 1, 0, -1):
            current_pattern[i] = current_pattern[i - 1]
            current_colors[i] = current_colors[i - 1]
        current_pattern[0] = last_pattern_row
        current_colors[0] = last_color_row
        self.invalidate_tile_cache(current_tile_index)
        self.update_all_displays(changed_level="tile")
        print(f"Tile {current_tile_index} shifted down.")

    def shift_tile_left(self):
        global tileset_patterns, current_tile_index, num_tiles_in_set
        if not (0 <= current_tile_index < num_tiles_in_set):
            return
        current_pattern = tileset_patterns[current_tile_index]
        for r in range(TILE_HEIGHT):
            row_data = current_pattern[r]
            if TILE_WIDTH > 0:
                first_pixel = row_data[0]
            for c in range(TILE_WIDTH - 1):
                row_data[c] = row_data[c + 1]
            row_data[TILE_WIDTH - 1] = first_pixel
        self.invalidate_tile_cache(current_tile_index)
        self.update_all_displays(changed_level="tile")
        print(f"Tile {current_tile_index} shifted left.")

    def shift_tile_right(self):
        global tileset_patterns, current_tile_index, num_tiles_in_set
        if not (0 <= current_tile_index < num_tiles_in_set):
            return
        current_pattern = tileset_patterns[current_tile_index]
        for r in range(TILE_HEIGHT):
            row_data = current_pattern[r]
            if TILE_WIDTH > 0:
                last_pixel = row_data[TILE_WIDTH - 1]
            for c in range(TILE_WIDTH - 1, 0, -1):
                row_data[c] = row_data[c - 1]
            row_data[0] = last_pixel
        self.invalidate_tile_cache(current_tile_index)
        self.update_all_displays(changed_level="tile")
        print(f"Tile {current_tile_index} shifted right.")

    # --- Zoom Methods ---
    def change_map_zoom_mult(self, factor):  # Renamed from change_map_zoom
        """Applies multiplicative zoom, centered on the current canvas center."""
        canvas = self.map_canvas
        view_x1, view_y1, view_x2, view_y2 = (
            canvas.xview()[0],
            canvas.yview()[0],
            canvas.xview()[1],
            canvas.yview()[1],
        )
        center_x_canvas = canvas.canvasx(
            (canvas.winfo_width() / 2)
        )  # Approximation of center
        center_y_canvas = canvas.canvasy((canvas.winfo_height() / 2))
        self.zoom_map_at_point(factor, center_x_canvas, center_y_canvas)

    def set_map_zoom(self, new_zoom_level):
        """Sets absolute zoom level, centered on current canvas center."""
        min_zoom, max_zoom = 0.1, 6.0  # New limits
        safe_zoom = max(min_zoom, min(max_zoom, float(new_zoom_level)))
        current_zoom = self.map_zoom_level
        if abs(current_zoom - safe_zoom) > 1e-9:  # Avoid floating point noise
            factor = safe_zoom / current_zoom if current_zoom > 1e-9 else 1.0
            canvas = self.map_canvas
            center_x_canvas = canvas.canvasx(canvas.winfo_width() / 2)
            center_y_canvas = canvas.canvasy(canvas.winfo_height() / 2)
            self.zoom_map_at_point(factor, center_x_canvas, center_y_canvas)

    def get_zoomed_tile_size(self):
        """Calculates the current TILE size based on 8x8 base and zoom."""
        base_tile_size = 8  # 100% zoom = 8 pixels
        zoomed_size = base_tile_size * self.map_zoom_level
        return max(1, int(zoomed_size))  # Ensure at least 1 pixel

    def zoom_map_at_point(self, factor, zoom_x_canvas, zoom_y_canvas):
        """Zooms the map by 'factor', keeping the point (zoom_x/y_canvas) stationary,
        and clamps scroll to prevent gaps and ensure edges align correctly."""
        canvas = self.map_canvas
        current_zoom = self.map_zoom_level
        min_zoom, max_zoom = 0.1, 6.0
        new_zoom = max(min_zoom, min(max_zoom, current_zoom * factor))

        # Only proceed if zoom actually changes significantly
        if abs(new_zoom - current_zoom) < 1e-9:
            return

        # --- 1. Get map coordinates under cursor BEFORE zoom ---
        map_coord_x_at_cursor = canvas.canvasx(zoom_x_canvas)
        map_coord_y_at_cursor = canvas.canvasy(zoom_y_canvas)

        # --- 2. Update zoom level ---
        scale_change = new_zoom / current_zoom
        self.map_zoom_level = new_zoom  # Update state

        # --- 3. Calculate IDEAL scroll position (absolute pixels) for zoom-to-cursor ---
        # The map point map_coord_x_at_cursor should end up at the screen
        # position zoom_x_canvas after zooming.
        new_map_coord_x = map_coord_x_at_cursor * scale_change
        new_map_coord_y = map_coord_y_at_cursor * scale_change

        # Ideal absolute coordinate for the viewport's top-left (scroll position):
        ideal_scroll_x_abs = new_map_coord_x - zoom_x_canvas
        ideal_scroll_y_abs = new_map_coord_y - zoom_y_canvas

        # --- 4. Calculate new total map dimensions and widget size ---
        zoomed_tile_size_new = (
            self.get_zoomed_tile_size()
        )  # Uses updated self.map_zoom_level
        map_total_pixel_width_new = (
            map_width * SUPERTILE_GRID_DIM * zoomed_tile_size_new
        )
        map_total_pixel_height_new = (
            map_height * SUPERTILE_GRID_DIM * zoomed_tile_size_new
        )

        # Ensure dimensions are at least 1 for calculations
        safe_map_width = max(1.0, map_total_pixel_width_new)
        safe_map_height = max(1.0, map_total_pixel_height_new)

        canvas_widget_width = canvas.winfo_width()
        canvas_widget_height = canvas.winfo_height()

        # --- 5. Calculate the MAXIMUM possible scroll position (absolute pixels) ---
        # This is how far the top-left corner can move from (0,0) before the
        # map's right/bottom edge hits the canvas's right/bottom edge.
        # If map is smaller than canvas, max scroll is 0.
        max_scroll_x_abs = max(0.0, map_total_pixel_width_new - canvas_widget_width)
        max_scroll_y_abs = max(0.0, map_total_pixel_height_new - canvas_widget_height)

        # --- 6. Clamp the IDEAL scroll position to the valid range [0, max_scroll_abs] ---
        final_scroll_x_abs = max(0.0, min(ideal_scroll_x_abs, max_scroll_x_abs))
        final_scroll_y_abs = max(0.0, min(ideal_scroll_y_abs, max_scroll_y_abs))

        # --- 7. Convert the FINAL absolute clamped scroll position to fractions ---
        # This handles the case where the map is smaller than the canvas automatically,
        # because max_scroll_x_abs/max_scroll_y_abs would be 0, clamping final_scroll_*_abs to 0.
        # The fraction is relative to the total map size.
        final_x_fraction = final_scroll_x_abs / safe_map_width
        final_y_fraction = final_scroll_y_abs / safe_map_height

        # --- 8. Apply the FINAL definite scroll position using moveto ---
        # Ensure fractions are within [0, 1] just in case of float issues, although clamping should handle it.
        canvas.xview_moveto(max(0.0, min(1.0, final_x_fraction)))
        canvas.yview_moveto(max(0.0, min(1.0, final_y_fraction)))

        # --- 9. Final Redraw ---
        # Redraw the map. This uses the final scroll position set by moveto
        # and updates the scrollregion based on the new total map dimensions.
        self.draw_map_canvas()

        # Update the minimap viewport
        self.draw_minimap()

    def handle_map_zoom_scroll(self, event):
        """Handles Ctrl+MouseWheel zooming, centered on cursor."""
        factor = 0.0
        # Determine zoom direction and set multiplicative factor
        if event.num == 4 or event.delta > 0:  # Zoom In
            factor = 1.1  # Smaller steps often feel better for scroll wheel
        elif event.num == 5 or event.delta < 0:  # Zoom Out
            factor = 1 / 1.1
        else:
            return  # Ignore other wheel events

        # Get mouse position relative to canvas content (scrolled coords)
        canvas = self.map_canvas
        zoom_x_canvas = canvas.canvasx(event.x)
        zoom_y_canvas = canvas.canvasy(event.y)

        # Perform zoom centered on the cursor
        self.zoom_map_at_point(factor, zoom_x_canvas, zoom_y_canvas)

    # --- Scrolling Methods ---

    def scroll_viewers_to_tile(self, tile_index):
        """Scrolls the tileset viewers to make the specified tile index visible."""
        # Basic input validation
        if tile_index < 0:
            return

        # Define layout parameters
        padding = 1
        tile_size = VIEWER_TILE_SIZE
        items_per_row = NUM_TILES_ACROSS

        # Calculate target row and y-coordinate
        row, _ = divmod(tile_index, items_per_row)
        target_y = row * (tile_size + padding)

        # --- Scroll main viewer ---
        canvas_main = self.tileset_canvas
        try:
            # Get scroll region info (might be tuple or string)
            scroll_info_tuple = canvas_main.cget("scrollregion")
            # Convert to string and split for consistent parsing
            scroll_info = str(scroll_info_tuple).split()

            # Check if format is valid ("0 0 width height")
            if len(scroll_info) == 4:
                # Extract total height
                total_height = float(scroll_info[3])

                # Avoid division by zero
                if total_height > 0:
                    # Calculate scroll fraction
                    fraction = target_y / total_height
                    # Clamp fraction to valid range [0.0, 1.0]
                    clamped_fraction = min(1.0, max(0.0, fraction))
                    # Perform the scroll
                    canvas_main.yview_moveto(clamped_fraction)
            # else: (Optional: handle invalid scrollregion format if needed)
            #     print(f"Warning: Invalid scrollregion format for main tileset viewer: {scroll_info}")

        except Exception as e:
            # Catch any error during scrolling
            print(f"Error scrolling main tileset viewer: {e}")

        # --- Scroll Supertile tab's viewer ---
        canvas_st = self.st_tileset_canvas
        try:
            scroll_info_st_tuple = canvas_st.cget("scrollregion")
            scroll_info_st = str(scroll_info_st_tuple).split()

            if len(scroll_info_st) == 4:
                total_height_st = float(scroll_info_st[3])

                if total_height_st > 0:
                    fraction_st = target_y / total_height_st
                    clamped_fraction_st = min(1.0, max(0.0, fraction_st))
                    canvas_st.yview_moveto(clamped_fraction_st)
            # else:
            #     print(f"Warning: Invalid scrollregion format for ST tileset viewer: {scroll_info_st}")

        except Exception as e:
            print(f"Error scrolling ST tileset viewer: {e}")

    def scroll_selectors_to_supertile(self, supertile_index):
        """Scrolls the supertile selectors to make the specified index visible."""
        # Basic input validation
        if supertile_index < 0:
            return

        # Define layout parameters
        padding = 1
        item_size = SUPERTILE_SELECTOR_PREVIEW_SIZE
        items_per_row = NUM_SUPERTILES_ACROSS

        # Calculate target row and y-coordinate
        row, _ = divmod(supertile_index, items_per_row)
        target_y = row * (item_size + padding)

        # --- Scroll Supertile tab's selector ---
        canvas_st = self.supertile_selector_canvas
        try:
            scroll_info_tuple = canvas_st.cget("scrollregion")
            scroll_info = str(scroll_info_tuple).split()

            if len(scroll_info) == 4:
                total_height = float(scroll_info[3])

                if total_height > 0:
                    fraction = target_y / total_height
                    clamped_fraction = min(1.0, max(0.0, fraction))
                    canvas_st.yview_moveto(clamped_fraction)
            # else:
            #     print(f"Warning: Invalid scrollregion format for ST selector: {scroll_info}")

        except Exception as e:
            print(f"Error scrolling ST selector: {e}")

        # --- Scroll Map tab's selector ---
        canvas_map = self.map_supertile_selector_canvas
        try:
            scroll_info_map_tuple = canvas_map.cget("scrollregion")
            scroll_info_map = str(scroll_info_map_tuple).split()

            if len(scroll_info_map) == 4:
                total_height_map = float(scroll_info_map[3])

                if total_height_map > 0:
                    fraction_map = target_y / total_height_map
                    clamped_fraction_map = min(1.0, max(0.0, fraction_map))
                    canvas_map.yview_moveto(clamped_fraction_map)
            # else:
            #     print(f"Warning: Invalid scrollregion format for Map selector: {scroll_info_map}")

        except Exception as e:
            print(f"Error scrolling Map selector: {e}")

    # --- vvv NEW Grid/Window Handlers vvv ---
    def toggle_supertile_grid(self):
        """Callback for the supertile grid checkbutton."""
        self.draw_map_canvas()  # Redraw map to show/hide grid

    def toggle_window_view(self):
        """Callback for the window view checkbutton."""
        self.draw_map_canvas()  # Redraw map to show/hide window view
        self.draw_minimap()

    def cycle_grid_color(self):
        """Cycles through the available grid colors."""
        self.grid_color_index = (self.grid_color_index + 1) % len(GRID_COLOR_CYCLE)
        # Redraw map if grids are visible
        if self.show_supertile_grid.get() or self.show_window_view.get():
            self.draw_map_canvas()
        print(f"Grid color set to: {GRID_COLOR_CYCLE[self.grid_color_index]}")

    def apply_window_size_from_entries(self):
        """Applies the W/H values from the Entry widgets."""
        try:
            new_w = self.window_view_tile_w.get()  # Get value from IntVar
            new_h = self.window_view_tile_h.get()

            # Validate range
            min_w, max_w = 1, 32
            min_h, max_h = 1, MAX_WIN_VIEW_HEIGHT_TILES
            valid = True
            if not (min_w <= new_w <= max_w):
                messagebox.showerror(
                    "Invalid Width", f"Window width must be {min_w}-{max_w}."
                )
                valid = False
            if not (min_h <= new_h <= max_h):
                messagebox.showerror(
                    "Invalid Height", f"Window height must be {min_h}-{max_h}."
                )
                valid = False

            if not valid:
                # Reset entries to current state if invalid
                self._update_window_size_vars_from_state()  # Use internal helper
                return

            # If size changed (or even if not, just redraw for simplicity)
            self._clamp_window_view_position()  # Ensure position is valid for new size
            self.draw_map_canvas()
            self.draw_minimap()
            print(f"Window view size set to {new_w}x{new_h} tiles via input.")

        except tk.TclError:  # Handles non-integer input in IntVars
            messagebox.showerror(
                "Invalid Input",
                "Please enter valid integer numbers for width and height.",
            )
            self._update_window_size_vars_from_state()  # Reset on error
        except Exception as e:
            messagebox.showerror("Error", f"Could not apply size: {e}")
            self._update_window_size_vars_from_state()

    def _update_window_size_vars_from_state(self):
        """Internal helper to set IntVars from the state variables."""
        # Needed because the IntVars are bound to entries, direct setting is best
        self.window_view_tile_w.set(
            self.window_view_tile_w.get()
        )  # Trigger update if needed
        self.window_view_tile_h.set(self.window_view_tile_h.get())

    def _clamp_window_view_position(self):
        """Ensures the window view's top-left position is valid for its current size."""
        current_w = self.window_view_tile_w.get()
        current_h = self.window_view_tile_h.get()
        # Calculate max valid top-left tile coord
        max_tile_x = max(0, (map_width * SUPERTILE_GRID_DIM) - current_w)
        max_tile_y = max(0, (map_height * SUPERTILE_GRID_DIM) - current_h)
        # Clamp current position
        self.window_view_tile_x = max(0, min(self.window_view_tile_x, max_tile_x))
        self.window_view_tile_y = max(0, min(self.window_view_tile_y, max_tile_y))

    def move_window_view_keyboard(self, dx_tile, dy_tile):
        """Moves the window view by dx, dy TILE steps."""
        if not self.show_window_view.get():
            return  # Only move if visible

        # Calculate new target position
        new_tx = self.window_view_tile_x + dx_tile
        new_ty = self.window_view_tile_y + dy_tile

        # Clamp within map bounds (recalculate max based on current size)
        current_w = self.window_view_tile_w.get()
        current_h = self.window_view_tile_h.get()
        max_tile_x = max(0, (map_width * SUPERTILE_GRID_DIM) - current_w)
        max_tile_y = max(0, (map_height * SUPERTILE_GRID_DIM) - current_h)
        clamped_tx = max(0, min(new_tx, max_tile_x))
        clamped_ty = max(0, min(new_ty, max_tile_y))

        # Update if position changed
        if (
            self.window_view_tile_x != clamped_tx
            or self.window_view_tile_y != clamped_ty
        ):
            self.window_view_tile_x = clamped_tx
            self.window_view_tile_y = clamped_ty
            self.draw_map_canvas()  # Redraw to show moved window
            self.draw_minimap()

    def handle_map_keypress(self, event):
        """Handles key presses when the map canvas has focus."""
        key = event.keysym.lower()  # Get lowercase keysym

        if key == "c":
            self.cycle_grid_color()
        elif self.show_window_view.get():  # Only move window if visible
            if key == "w":
                self.move_window_view_keyboard(0, -1)  # Move up
            elif key == "a":
                self.move_window_view_keyboard(-1, 0)  # Move left
            elif key == "s":
                self.move_window_view_keyboard(0, 1)  # Move down
            elif key == "d":
                self.move_window_view_keyboard(1, 0)  # Move right

    # --- Window View Drag/Resize Handlers ---
    def _get_handle_at(self, canvas_x, canvas_y):
        """Checks if the click is on a resize handle, returns handle tag ('nw', 'n', etc.) or None."""
        if not self.show_window_view.get():
            return None
        # Find items tagged 'window_view_handle' near the click
        search_radius = WIN_VIEW_HANDLE_SIZE  # Search slightly larger than handle
        items = self.map_canvas.find_overlapping(
            canvas_x - search_radius,
            canvas_y - search_radius,
            canvas_x + search_radius,
            canvas_y + search_radius,
        )
        for item_id in items:
            tags = self.map_canvas.gettags(item_id)
            if "window_view_handle" in tags:
                for t in tags:
                    if t.startswith("handle_"):
                        return t.split("_")[1]  # Return 'nw', 'n', etc.
        return None  # No handle found

    def _is_inside_window_view(self, canvas_x, canvas_y):
        """Checks if the click is inside the window view rectangle bounds."""
        if not self.show_window_view.get():
            return False
        zoomed_tile_size = self.get_zoomed_tile_size()
        win_px = self.window_view_tile_x * zoomed_tile_size
        win_py = self.window_view_tile_y * zoomed_tile_size
        win_pw = self.window_view_tile_w.get() * zoomed_tile_size
        win_ph = self.window_view_tile_h.get() * zoomed_tile_size
        return (
            win_px <= canvas_x < win_px + win_pw
            and win_py <= canvas_y < win_py + win_ph
        )

    def handle_map_click_or_drag_start(self, event):
        """Handles initial NON-CTRL click: determines action (paint/window drag/resize).
        Sets up state AND performs the initial paint action if applicable.
        Also clears map selection if starting a paint/window action.
        """
        global last_painted_map_cell

        # --- Check for active modifiers that override this handler ---
        if self.is_shift_pressed:
            # print("Shift pressed, ignoring Button-1 for paint/window ops.")
            return "break"
        ctrl_pressed_at_click = event.state & 0x0004  # Check state at event time
        if ctrl_pressed_at_click:
            # print("Ctrl pressed, ignoring Button-1 for paint/window ops.")
            return "break"
        if self.current_mouse_action is not None:
            # print(f"Warning: Button-1 pressed while action '{self.current_mouse_action}' active.")
            return "break"
        # --- End Modifier Check ---

        # --- Clear previous selection when starting a new action ---
        self._clear_map_selection()  # Clear selection visual and state
        # --- End Clear Selection ---

        canvas = self.map_canvas
        canvas.focus_set()
        canvas_x = canvas.canvasx(event.x)
        canvas_y = canvas.canvasy(event.y)

        action_determined = None
        handle = self._get_handle_at(canvas_x, canvas_y)

        # Determine action based on click location
        if handle and self.show_window_view.get():
            action_determined = "window_resizing"
            self.current_mouse_action = action_determined
            self.window_view_resize_handle = handle
            self.drag_start_x = canvas_x
            self.drag_start_y = canvas_y
            self.drag_start_win_tx = self.window_view_tile_x
            self.drag_start_win_ty = self.window_view_tile_y
            self.drag_start_win_tw = self.window_view_tile_w.get()
            self.drag_start_win_th = self.window_view_tile_h.get()

        elif (
            self._is_inside_window_view(canvas_x, canvas_y)
            and self.show_window_view.get()
        ):
            action_determined = "window_dragging"
            self.current_mouse_action = action_determined
            self.drag_start_x = canvas_x
            self.drag_start_y = canvas_y
            self.drag_start_win_tx = self.window_view_tile_x
            self.drag_start_win_ty = self.window_view_tile_y

        else:  # Painting case
            action_determined = "painting"
            self.current_mouse_action = action_determined
            last_painted_map_cell = None  # Reset for this paint sequence
            self._paint_map_cell(canvas_x, canvas_y)  # Perform first paint

        self._update_map_cursor()  # Update cursor based on the determined action

        return "break"

    def handle_map_drag(self, event):
        """Handles motion for non-panning actions (paint, window drag/resize)."""

        # Ignore if panning or no suitable action is set from Button-1 press
        # This prevents interference if Ctrl was pressed *after* Button-1 was down but before motion.
        if self.current_mouse_action not in [
            "painting",
            "window_dragging",
            "window_resizing",
        ]:
            return  # Don't handle if not in a valid non-pan drag state

        canvas = self.map_canvas
        canvas_x = canvas.canvasx(event.x)
        canvas_y = canvas.canvasy(event.y)

        # Perform action based on the current state
        if self.current_mouse_action == "painting":
            self._paint_map_cell(canvas_x, canvas_y)
        elif self.current_mouse_action == "window_dragging":
            self._do_window_move_drag(canvas_x, canvas_y)
        elif self.current_mouse_action == "window_resizing":
            self._do_window_resize_drag(canvas_x, canvas_y)

        return "break"  # Prevent other B1-Motion bindings

    def handle_map_drag_release(self, event):
        """Handles mouse button release: ends the current action (paint, pan, window ops)."""
        global last_painted_map_cell  # Ensure global is accessible
        action_at_release = self.current_mouse_action

        last_painted_map_cell = None  # Stop continuous paint if it was happening

        # Reset the current action state FIRST
        self.current_mouse_action = None

        # Perform any finalization based on the action that just finished
        if action_at_release == "panning":
            pass  # No explicit action needed, scan_dragto stopped with motion

        elif action_at_release == "window_dragging":
            # Position is already snapped during drag, just update minimap (done below)
            pass

        elif action_at_release == "window_resizing":
            # Clamp final position and update entries/IntVar state just in case
            self._clamp_window_view_position()
            self._update_window_size_vars_from_state()  # Sync IntVars post-resize
            self.window_view_resize_handle = None
            # Redraw needed to finalize visual state and ensure entries match
            self.draw_map_canvas()  # Redraw map canvas to remove potential temp visuals

        elif action_at_release == "painting":
            pass  # No specific finalization needed

        self._update_map_cursor()
        self.draw_minimap()

    def _do_window_move_drag(self, current_canvas_x, current_canvas_y):
        """Helper: Calculates and applies window movement during drag."""
        zoomed_tile_size = self.get_zoomed_tile_size()
        if zoomed_tile_size <= 0:
            return

        delta_x_pixels = current_canvas_x - self.drag_start_x
        delta_y_pixels = current_canvas_y - self.drag_start_y

        # Calculate movement in TILE units, snapping to grid
        # Use floor for consistent snapping direction
        delta_tile_x = math.floor(delta_x_pixels / zoomed_tile_size)
        delta_tile_y = math.floor(delta_y_pixels / zoomed_tile_size)

        # Calculate potential new top-left TILE coordinate
        new_tx = self.drag_start_win_tx + delta_tile_x
        new_ty = self.drag_start_win_ty + delta_tile_y

        # Clamp position within map bounds (using current W/H)
        current_w = self.window_view_tile_w.get()
        current_h = self.window_view_tile_h.get()
        max_tile_x = max(0, (map_width * SUPERTILE_GRID_DIM) - current_w)
        max_tile_y = max(0, (map_height * SUPERTILE_GRID_DIM) - current_h)
        clamped_tx = max(0, min(new_tx, max_tile_x))
        clamped_ty = max(0, min(new_ty, max_tile_y))

        # Update state and redraw ONLY if position actually changes
        if (
            self.window_view_tile_x != clamped_tx
            or self.window_view_tile_y != clamped_ty
        ):
            self.window_view_tile_x = clamped_tx
            self.window_view_tile_y = clamped_ty
            self.draw_map_canvas()  # Redraw to show moved window
            self.draw_minimap()

    def _do_window_resize_drag(self, current_canvas_x, current_canvas_y):
        """Helper: Calculates and applies window resize during drag."""
        zoomed_tile_size = self.get_zoomed_tile_size()
        if zoomed_tile_size <= 0:
            return

        # Starting state in TILE units
        start_tx = self.drag_start_win_tx
        start_ty = self.drag_start_win_ty
        start_tw = self.drag_start_win_tw
        start_th = self.drag_start_win_th
        start_br_tx = start_tx + start_tw  # Bottom-right tile X (exclusive)
        start_br_ty = start_ty + start_th  # Bottom-right tile Y (exclusive)

        # Current mouse position snapped to TILE grid
        current_tile_x = math.floor(current_canvas_x / zoomed_tile_size)
        current_tile_y = math.floor(current_canvas_y / zoomed_tile_size)

        # Calculate new potential corners based on handle
        new_tx = start_tx
        new_ty = start_ty
        new_br_tx = start_br_tx
        new_br_ty = start_br_ty
        handle = self.window_view_resize_handle

        # Adjust based on handle dragged
        if "n" in handle:
            new_ty = current_tile_y
        if "s" in handle:
            new_br_ty = current_tile_y + 1  # +1 because BR is exclusive
        if "w" in handle:
            new_tx = current_tile_x
        if "e" in handle:
            new_br_tx = current_tile_x + 1

        # Ensure top-left is never beyond bottom-right
        new_tx = min(new_tx, new_br_tx - 1)  # Ensure width >= 1
        new_ty = min(new_ty, new_br_ty - 1)  # Ensure height >= 1
        new_br_tx = max(new_br_tx, new_tx + 1)
        new_br_ty = max(new_br_ty, new_ty + 1)

        # Calculate new width and height in tiles
        new_tw = new_br_tx - new_tx
        new_th = new_br_ty - new_ty

        # Clamp dimensions to allowed limits
        min_w, max_w = 1, 32
        min_h, max_h = 1, MAX_WIN_VIEW_HEIGHT_TILES
        clamped_tw = max(min_w, min(new_tw, max_w))
        clamped_th = max(min_h, min(new_th, max_h))

        # Adjust position if clamping changed dimensions, preserving the fixed corner/edge
        if "n" in handle and clamped_th != new_th:
            new_ty = new_br_ty - clamped_th
        if "w" in handle and clamped_tw != new_tw:
            new_tx = new_br_tx - clamped_tw
        if "s" in handle:
            new_br_ty = (
                new_ty + clamped_th
            )  # Recalculate needed? No, height is clamped.
        if "e" in handle:
            new_br_tx = new_tx + clamped_tw

        # Clamp position to stay within map boundaries
        max_map_tile_x = map_width * SUPERTILE_GRID_DIM
        max_map_tile_y = map_height * SUPERTILE_GRID_DIM
        clamped_tx = max(0, min(new_tx, max_map_tile_x - clamped_tw))
        clamped_ty = max(0, min(new_ty, max_map_tile_y - clamped_th))

        # Final check if clamping position changed dimensions again (shouldn't drastically)
        final_tw = min(clamped_tw, max_map_tile_x - clamped_tx)
        final_th = min(clamped_th, max_map_tile_y - clamped_ty)

        # Update state only if position or size changed
        if (
            self.window_view_tile_x != clamped_tx
            or self.window_view_tile_y != clamped_ty
            or self.window_view_tile_w.get() != final_tw
            or self.window_view_tile_h.get() != final_th
        ):
            #
            self.window_view_tile_x = clamped_tx
            self.window_view_tile_y = clamped_ty
            self.window_view_tile_w.set(final_tw)  # Update IntVars
            self.window_view_tile_h.set(final_th)
            # self._update_window_size_vars_from_state() # Update entries
            self.draw_map_canvas()  # Redraw to show resize
            self.draw_minimap()

    # --- Minimap Methods ---

    def toggle_minimap(self):
        """Opens/raises the resizable minimap window."""
        if self.minimap_window is None or not tk.Toplevel.winfo_exists(
            self.minimap_window
        ):
            self.minimap_window = tk.Toplevel(self.root)
            self.minimap_window.title("Minimap")
            # Set initial size, but allow resizing
            self.minimap_window.geometry(
                f"{MINIMAP_INITIAL_WIDTH}x{MINIMAP_INITIAL_HEIGHT}"
            )
            # self.minimap_window.resizable(False, False) # REMOVE or set True

            self.minimap_canvas = tk.Canvas(
                self.minimap_window, bg="dark slate gray", highlightthickness=0
            )
            # Make canvas fill the resizable window
            self.minimap_canvas.pack(fill=tk.BOTH, expand=True)  # MODIFIED pack options
            self.minimap_window.protocol("WM_DELETE_WINDOW", self._on_minimap_close)
            self.minimap_window.bind("<Configure>", self._on_minimap_configure)

            # Initial draw (will use initial geometry)
            # Need to ensure canvas has dimensions before first draw
            self.minimap_window.update_idletasks()  # Process geometry requests
            self.draw_minimap()
        else:
            self.minimap_window.lift()
            self.minimap_window.focus_set()

    def _on_minimap_close(self):
        """Handles the closing of the minimap window."""
        if self.minimap_window:
            self.minimap_window.destroy()  # Destroy the window
        self.minimap_window = None  # Reset state variable
        self.minimap_canvas = None

    def draw_minimap(self):
        """Draws the minimap content: rendered background, viewport, window view."""
        if self.minimap_window is None or self.minimap_canvas is None:
            return
        if not tk.Toplevel.winfo_exists(self.minimap_window):
            self._on_minimap_close()
            return

        canvas = self.minimap_canvas
        canvas.delete("all")

        # --- 1. Get Current Minimap Canvas Dimensions ---
        current_minimap_w = canvas.winfo_width()
        current_minimap_h = canvas.winfo_height()
        # If dimensions are 1, window hasn't been drawn properly yet, skip draw
        if current_minimap_w <= 1 or current_minimap_h <= 1:
            return

        # --- 2. Draw Rendered Map Background ---
        # Check cache first, also check if rendered size matches current canvas size
        if (
            self.minimap_background_cache is None
            or self.minimap_bg_rendered_width != current_minimap_w
            or self.minimap_bg_rendered_height != current_minimap_h
        ):
            # Regenerate if cache is invalid or size changed
            self.minimap_background_cache = self._create_minimap_background_image(
                current_minimap_w, current_minimap_h
            )

        # Draw the cached background image (if successfully created)
        if self.minimap_background_cache:
            canvas.create_image(
                0,
                0,
                image=self.minimap_background_cache,
                anchor=tk.NW,
                tags="minimap_bg_image",
            )
        else:
            # Fallback: draw simple background if image creation failed
            canvas.create_rectangle(
                0, 0, current_minimap_w, current_minimap_h, fill="gray10"
            )

        # --- 3. Calculate Scaling for Overlays ---
        map_total_pixel_w = map_width * SUPERTILE_GRID_DIM * TILE_WIDTH
        map_total_pixel_h = map_height * SUPERTILE_GRID_DIM * TILE_HEIGHT
        if map_total_pixel_w <= 0 or map_total_pixel_h <= 0:
            return

        # Calculate scale factors based on CURRENT minimap size
        scale_x = current_minimap_w / map_total_pixel_w
        scale_y = current_minimap_h / map_total_pixel_h
        scale = min(scale_x, scale_y)  # Fit entirely, maintain aspect ratio

        # Calculate centering offsets based on CURRENT minimap size
        scaled_map_w = map_total_pixel_w * scale
        scaled_map_h = map_total_pixel_h * scale
        offset_x = (current_minimap_w - scaled_map_w) / 2
        offset_y = (current_minimap_h - scaled_map_h) / 2

        # --- 4. Draw Main Map Viewport Rectangle (Bolder) ---
        try:
            main_canvas = self.map_canvas
            scroll_x_frac = main_canvas.xview()
            scroll_y_frac = main_canvas.yview()

            # Calculate total BASE map pixel dimensions (at 100% zoom)
            map_total_base_w = map_width * SUPERTILE_GRID_DIM * TILE_WIDTH
            map_total_base_h = map_height * SUPERTILE_GRID_DIM * TILE_HEIGHT

            # Check if base dimensions are valid
            if map_total_base_w > 0 and map_total_base_h > 0:
                # Calculate visible area in BASE map pixel coordinates directly from scroll fractions
                map_base_px_x1 = scroll_x_frac[0] * map_total_base_w
                map_base_px_y1 = scroll_y_frac[0] * map_total_base_h
                map_base_px_x2 = scroll_x_frac[1] * map_total_base_w
                map_base_px_y2 = scroll_y_frac[1] * map_total_base_h

                # Scale these correct base map pixel coordinates to minimap coordinates
                vp_x1 = offset_x + map_base_px_x1 * scale
                vp_y1 = offset_y + map_base_px_y1 * scale
                vp_x2 = offset_x + map_base_px_x2 * scale
                vp_y2 = offset_y + map_base_px_y2 * scale

                canvas.create_rectangle(
                    vp_x1,
                    vp_y1,
                    vp_x2,
                    vp_y2,
                    outline=self.MINIMAP_VIEWPORT_COLOR,
                    width=2,  # <-- Bolder line
                    tags="minimap_viewport",
                )
        except Exception as e:
            print(f"Error drawing minimap viewport: {e}")

        # --- 5. Draw Window View Rectangle (Bolder, if enabled) ---
        current_state = self.show_window_view.get()
        print(
            f"--- draw_minimap: Value of self.show_window_view.get() is {current_state}"
        )
        if current_state:
            try:
                win_tx = self.window_view_tile_x
                win_ty = self.window_view_tile_y
                win_tw = self.window_view_tile_w.get()
                win_th = self.window_view_tile_h.get()

                win_map_px1 = win_tx * TILE_WIDTH
                win_map_py1 = win_ty * TILE_HEIGHT
                win_map_px2 = win_map_px1 + (win_tw * TILE_WIDTH)
                win_map_py2 = win_map_py1 + (win_th * TILE_HEIGHT)

                wv_x1 = offset_x + win_map_px1 * scale
                wv_y1 = offset_y + win_map_py1 * scale
                wv_x2 = offset_x + win_map_px2 * scale
                wv_y2 = offset_y + win_map_py2 * scale

                canvas.create_rectangle(
                    wv_x1,
                    wv_y1,
                    wv_x2,
                    wv_y2,
                    outline=self.MINIMAP_WIN_VIEW_COLOR,
                    width=2,  # <-- Bolder line
                    dash=(4, 4),  # Keep dashed to differentiate
                    tags="minimap_window_view",
                )
            except Exception as e:
                print(f"Error drawing minimap window view: {e}")

    def _on_minimap_configure(self, event):
        """Callback when the minimap window is resized/moved."""
        # We only care about size changes for redrawing
        # Basic debouncing: wait a short time after the last configure event
        # before redrawing to avoid excessive calls during drag-resizing.
        debounce_ms = 150  # Adjust as needed (milliseconds)

        # Cancel any pending redraw timer
        if self.minimap_resize_timer is not None:
            self.root.after_cancel(self.minimap_resize_timer)

        # Schedule a new redraw after the debounce period
        self.minimap_resize_timer = self.root.after(
            debounce_ms, self._redraw_minimap_after_resize
        )

    def _redraw_minimap_after_resize(self):
        """Handles aspect ratio enforcement and redraws after resize debounce."""
        self.minimap_resize_timer = None  # Reset timer ID

        if not self.minimap_window or not tk.Toplevel.winfo_exists(self.minimap_window):
            return  # Exit if window is gone

        if self._minimap_resizing_internally:
            # If we are already in the process of resizing programmatically, bail out
            # to prevent potential infinite loops from the geometry() call triggering Configure.
            return

        # --- Aspect Ratio Enforcement ---
        try:
            current_width = self.minimap_window.winfo_width()
            current_height = self.minimap_window.winfo_height()

            # Check for valid map dimensions and window size
            if (
                map_height <= 0
                or map_width <= 0
                or current_width <= 1
                or current_height <= 1
            ):
                # Cannot calculate aspect ratio, just draw content
                self.invalidate_minimap_background_cache()
                self.draw_minimap()
                return  # Exit aspect ratio logic

            map_aspect = map_width / map_height
            ideal_height = int(round(current_width / map_aspect))

            # Check if height needs adjustment (allow 1-pixel tolerance)
            if abs(current_height - ideal_height) > 1:
                self._minimap_resizing_internally = True  # Set flag BEFORE resizing
                new_geometry = f"{current_width}x{ideal_height}"
                print(
                    f"Minimap Configure: Forcing aspect ratio. New geometry: {new_geometry}"
                )
                self.minimap_window.geometry(new_geometry)
                # After setting geometry, the configure event will likely fire again.
                # The flag _minimap_resizing_internally prevents immediate recursion.
                # We schedule the flag reset. Redraw will happen on the *next* configure event.
                self.root.after(
                    50, setattr, self, "_minimap_resizing_internally", False
                )
                # Don't redraw immediately here, let the next configure event handle it after resize.
                return  # Exit, wait for next configure event

        except Exception as e:
            print(f"Error during minimap aspect ratio enforcement: {e}")
            # Ensure flag is reset even on error
            self._minimap_resizing_internally = False

        # --- If no resize was needed, proceed with drawing ---
        print(
            f"Minimap Configure: Aspect ratio OK ({current_width}x{current_height}). Redrawing."
        )
        self.invalidate_minimap_background_cache()  # Invalidate on any size change
        self.draw_minimap()

    def _trigger_minimap_reconfigure(self):
        """Forces the minimap to re-evaluate its size and aspect ratio if it exists."""
        if self.minimap_window and tk.Toplevel.winfo_exists(self.minimap_window):
            # A simple way to trigger <Configure> is to slightly change the size
            # We can just call the resize logic directly though.
            print("Map dimensions changed, triggering minimap aspect check/redraw.")
            # Reset the resize timer to avoid duplicate calls if configure is also pending
            if self.minimap_resize_timer is not None:
                self.root.after_cancel(self.minimap_resize_timer)
                self.minimap_resize_timer = None
            # Directly call the logic that handles resizing and drawing
            self._redraw_minimap_after_resize()

    def invalidate_minimap_background_cache(self):
        """Clears the cached minimap background image."""
        self.minimap_background_cache = None
        # Reset rendered size trackers too
        self.minimap_bg_rendered_width = 0
        self.minimap_bg_rendered_height = 0

    def _create_minimap_background_image(self, target_width, target_height):
        """Generates a single PhotoImage of the entire map scaled to fit, preserving aspect ratio."""
        if target_width <= 0 or target_height <= 0:
            return None

        minimap_img = tk.PhotoImage(width=target_width, height=target_height)
        map_pixel_w = map_width * SUPERTILE_GRID_DIM * TILE_WIDTH
        map_pixel_h = map_height * SUPERTILE_GRID_DIM * TILE_HEIGHT

        if map_pixel_w <= 0 or map_pixel_h <= 0:
            print("Warning: Invalid base map pixel dimensions for minimap.")
            minimap_img.put("black", to=(0, 0, target_width, target_height))
            return minimap_img

        # --- Calculate aspect-preserving scale and offset (same logic as draw_minimap) ---
        scale_x = target_width / map_pixel_w
        scale_y = target_height / map_pixel_h
        scale = min(scale_x, scale_y)
        scaled_map_w = map_pixel_w * scale
        scaled_map_h = map_pixel_h * scale
        offset_x = (target_width - scaled_map_w) / 2
        offset_y = (target_height - scaled_map_h) / 2
        # --- End scale/offset calculation ---

        # Define background color for areas outside the scaled map (letter/pillarboxing)
        # Match the canvas background for seamless look if possible, else use black/grey
        # Using canvas bg might be tricky if it changes, black is safe.
        bg_fill_color_hex = "#000000"

        # --- Iterate through target minimap pixels ---
        for y_pix in range(target_height):
            row_hex_colors = []
            for x_pix in range(target_width):
                pixel_color_hex = bg_fill_color_hex  # Default to background/fill color

                # Check if this minimap pixel falls within the centered, scaled map area
                if (
                    offset_x <= x_pix < offset_x + scaled_map_w
                    and offset_y <= y_pix < offset_y + scaled_map_h
                ):

                    # Map this minimap pixel back to the corresponding base map pixel coordinate
                    # Use max(1, ...) to prevent division by zero if scale is tiny
                    map_base_x = (x_pix - offset_x) / max(1e-9, scale)
                    map_base_y = (y_pix - offset_y) / max(1e-9, scale)

                    # Clamp coordinates to be within the valid base map pixel range
                    map_base_x = max(0, min(map_pixel_w - 1, map_base_x))
                    map_base_y = max(0, min(map_pixel_h - 1, map_base_y))

                    # Determine the source supertile, tile, and pixel within tile
                    map_pixel_col = int(map_base_x)
                    map_pixel_row = int(map_base_y)

                    st_col = map_pixel_col // (SUPERTILE_GRID_DIM * TILE_WIDTH)
                    st_row = map_pixel_row // (SUPERTILE_GRID_DIM * TILE_HEIGHT)

                    tile_col_in_st = (
                        map_pixel_col % (SUPERTILE_GRID_DIM * TILE_WIDTH)
                    ) // TILE_WIDTH
                    tile_row_in_st = (
                        map_pixel_row % (SUPERTILE_GRID_DIM * TILE_HEIGHT)
                    ) // TILE_HEIGHT

                    pixel_col_in_tile = map_pixel_col % TILE_WIDTH
                    pixel_row_in_tile = map_pixel_row % TILE_HEIGHT

                    # Get color using the indices (similar to original logic but using calculated coords)
                    try:
                        supertile_idx = map_data[st_row][st_col]
                        if 0 <= supertile_idx < num_supertiles:
                            tile_idx = supertiles_data[supertile_idx][tile_row_in_st][
                                tile_col_in_st
                            ]
                            if 0 <= tile_idx < num_tiles_in_set:
                                pattern_val = tileset_patterns[tile_idx][
                                    pixel_row_in_tile
                                ][pixel_col_in_tile]
                                fg_idx, bg_idx = tileset_colors[tile_idx][
                                    pixel_row_in_tile
                                ]
                                fg_color = self.active_msx_palette[fg_idx]
                                bg_color = self.active_msx_palette[bg_idx]
                                pixel_color_hex = (
                                    fg_color if pattern_val == 1 else bg_color
                                )
                            else:
                                pixel_color_hex = (
                                    INVALID_TILE_COLOR  # Invalid tile index
                                )
                        else:
                            pixel_color_hex = (
                                INVALID_SUPERTILE_COLOR  # Invalid supertile index
                            )
                    except IndexError:
                        # Error case (e.g., map coords out of bounds, though clamping should prevent most)
                        pixel_color_hex = "#FF0000"  # Bright Red Error

                # Append the determined color (either map color or background fill)
                row_hex_colors.append(pixel_color_hex)

            # Put the row data onto the PhotoImage
            try:
                minimap_img.put("{" + " ".join(row_hex_colors) + "}", to=(0, y_pix))
            except tk.TclError as e:
                print(f"Warning [Minimap BG]: TclError put row {y_pix}: {e}")
                if row_hex_colors:
                    minimap_img.put(
                        row_hex_colors[0], to=(0, y_pix, target_width, y_pix + 1)
                    )

        print("Minimap background generated.")
        # Store generated size along with image for cache validation
        self.minimap_bg_rendered_width = target_width
        self.minimap_bg_rendered_height = target_height
        self.minimap_background_cache = minimap_img  # Store in cache
        return minimap_img

    def _update_window_title(self):
        """Updates the main window title based on the current project path."""
        base_title = "MSX Tile Forge"
        modifier = "*" if self.project_modified else ""

        if self.current_project_base_path:
            # Extract just the filename part
            project_name = os.path.basename(self.current_project_base_path)
            self.root.title(
                f"{base_title} - {project_name}{modifier}"
            )  # Prepend modifier
        else:
            self.root.title(f"{base_title} - Untitled{modifier}")  # Prepend modifier

    def _update_map_cursor(self):
        """Sets the map canvas cursor based on current action and modifier keys."""
        if not hasattr(self, "map_canvas") or not self.map_canvas.winfo_exists():
            return

        new_cursor = ""  # Default arrow cursor

        # Determine cursor based on the active operation FIRST
        if self.current_mouse_action == "panning":
            new_cursor = "fleur"
        elif self.current_mouse_action == "window_dragging":
            new_cursor = "fleur"
        elif self.current_mouse_action == "window_resizing":
            new_cursor = "sizing"  # Generic resize
        elif self.map_selection_active:  # NEW: Selection in progress
            new_cursor = "crosshair"
        # --- Modifier key hints (if NO mouse action is active) ---
        elif self.is_ctrl_pressed:
            try:  # Check location for hinting
                canvas_x = self.map_canvas.canvasx(
                    self.map_canvas.winfo_pointerx() - self.map_canvas.winfo_rootx()
                )
                canvas_y = self.map_canvas.canvasy(
                    self.map_canvas.winfo_pointery() - self.map_canvas.winfo_rooty()
                )
                handle = (
                    self._get_handle_at(canvas_x, canvas_y)
                    if self.show_window_view.get()
                    else None
                )
                if handle:
                    new_cursor = "sizing"  # Hint resize
                elif (
                    self._is_inside_window_view(canvas_x, canvas_y)
                    and self.show_window_view.get()
                ):
                    new_cursor = "fleur"  # Hint window drag
                else:
                    new_cursor = "hand2"  # Hint panning
            except tk.TclError:
                new_cursor = "hand2"  # Default hint for Ctrl pressed
        elif self.is_shift_pressed:  # NEW: Shift held, no action -> hint selection
            new_cursor = "crosshair"
        # --- Default action (if no action and no relevant modifier) ---
        else:
            new_cursor = "pencil"  # Default paint cursor

        # Only change the cursor if it's different
        try:
            current_cursor = self.map_canvas.cget("cursor")
            if current_cursor != new_cursor:
                self.map_canvas.config(cursor=new_cursor)
        except tk.TclError:
            pass

    def handle_ctrl_press(self, event):
        """Handles Control key press."""
        # Check if the key is actually Control_L or Control_R
        if "Control" in event.keysym:
            # Only update state and cursor if Ctrl wasn't already considered pressed
            if not self.is_ctrl_pressed:
                self.is_ctrl_pressed = True
                # Update cursor only if no mouse action is currently happening
                # If a mouse button is down, let the existing action determine cursor
                if self.current_mouse_action is None:
                    self._update_map_cursor()

    def handle_ctrl_release(self, event):
        """Handles Control key release. Stops panning if active."""
        # Check if the key is actually Control_L or Control_R
        if "Control" in event.keysym:
            # Only update state if Ctrl was actually considered pressed
            if self.is_ctrl_pressed:
                self.is_ctrl_pressed = False
                # If panning was the current action, stop it.
                # Window dragging/resizing continues until mouse release even if Ctrl comes up.
                if self.current_mouse_action == "panning":
                    self.current_mouse_action = None
                self._update_map_cursor()

    def handle_pan_start(self, event):
        """Handles the start of panning (Ctrl + Left Click) OR window dragging with Ctrl."""
        # --- Check for Shift modifier ---
        if self.is_shift_pressed:
            # print("Shift pressed, ignoring Ctrl-Button-1 for pan/window drag.")
            return "break"
        # --- End Shift Check ---

        ctrl_pressed_at_click = event.state & 0x0004  # Check state at event time
        if not ctrl_pressed_at_click or self.current_mouse_action is not None:
            return

        canvas = self.map_canvas
        canvas_x = canvas.canvasx(event.x)
        canvas_y = canvas.canvasy(event.y)

        # --- Clear previous selection when starting pan/window drag ---
        self._clear_map_selection()  # Clear selection visual and state
        # --- End Clear Selection ---

        if (
            self._is_inside_window_view(canvas_x, canvas_y)
            and self.show_window_view.get()
        ):
            self.current_mouse_action = "window_dragging"
            self.drag_start_x = canvas_x
            self.drag_start_y = canvas_y
            self.drag_start_win_tx = self.window_view_tile_x
            self.drag_start_win_ty = self.window_view_tile_y
            self._update_map_cursor()
        else:
            # Initiate PANNING
            self.current_mouse_action = "panning"
            canvas.scan_mark(event.x, event.y)
            self._update_map_cursor()

        return "break"

    def handle_pan_motion(self, event):
        """Handles mouse motion during panning OR window dragging with Ctrl."""
        # Only process if an action initiated by Ctrl+Click is active
        if self.current_mouse_action not in ["panning", "window_dragging"]:
            return

        canvas = self.map_canvas

        if self.current_mouse_action == "panning":
            canvas.scan_dragto(
                event.x, event.y, gain=1
            )  # Use event x/y for scan_dragto

            # *** Clamp scroll position ***
            x_view = canvas.xview()
            y_view = canvas.yview()
            clamped = False
            if x_view[0] < 0.0:
                canvas.xview_moveto(0.0)
                clamped = True
            if y_view[0] < 0.0:
                canvas.yview_moveto(0.0)
                clamped = True

            self.draw_minimap()

        elif self.current_mouse_action == "window_dragging":
            # Handle window dragging motion (which was initiated by Ctrl+Click)
            canvas_x = canvas.canvasx(event.x)
            canvas_y = canvas.canvasy(event.y)
            self._do_window_move_drag(canvas_x, canvas_y)

        return "break"  # Prevent other <B1-Motion> handlers

    def handle_canvas_enter(self, event):
        """Handles mouse entering the canvas area."""
        # Set cursor based on current state
        self._update_map_cursor()

        # --- >> ADDED: Draw paste preview on enter if applicable << ---
        if event.widget == self.map_canvas:
            is_map_tab_active = False
            if self.notebook and self.notebook.winfo_exists():
                try:
                     selected_tab_index = self.notebook.index(self.notebook.select())
                     if selected_tab_index == 3: # Map Editor tab index
                         is_map_tab_active = True
                except tk.TclError:
                    pass # Ignore if notebook not ready

            # Draw preview if map tab active and clipboard has data
            if is_map_tab_active and self.map_clipboard_data:
                self._draw_paste_preview_rect(event=event)

    def handle_canvas_leave(self, event):
        """Handles mouse leaving the canvas area."""
        # Reset cursor to default when leaving, unless an action is in progress
        if self.current_mouse_action is None:
            # Only reset if the specific widget leaving is the map canvas
            if event.widget == self.map_canvas:
                try:
                    if self.map_canvas.winfo_exists():
                        self.map_canvas.config(cursor="")
                except tk.TclError:
                    pass # Ignore if destroyed

        # Reset coordinate display when mouse leaves map canvas
        if event.widget == self.map_canvas and hasattr(self, "map_coords_label"):
            self.map_coords_label.config(text="ST Coords: -, -")

        # Clear paste preview when leaving map canvas
        if event.widget == self.map_canvas:
            self._clear_paste_preview_rect()

    def _update_edit_menu_state(self):
        """Updates the state (enabled/disabled) and labels of generic Edit menu items
        based on the active tab and clipboard state.
        """
        if not self.edit_menu:
            return  # Menu not ready
        if self.copy_menu_item_index == -1 or self.paste_menu_item_index == -1:
            return  # Cannot proceed if indices weren't stored correctly

        selected_tab_index = 0  # Default
        try:
            if self.notebook and self.notebook.winfo_exists():
                current_selection = self.notebook.select()
                if current_selection:
                    selected_tab_index = self.notebook.index(current_selection)
        except tk.TclError:
            selected_tab_index = 0

        can_copy = False
        can_paste = False
        copy_label = "Copy"
        paste_label = "Paste"

        if selected_tab_index == 1:  # Tile Editor Tab (index 1)
            copy_label = "Copy Tile"
            paste_label = "Paste Tile"
            can_copy = 0 <= current_tile_index < num_tiles_in_set
            can_paste = (
                tile_clipboard_pattern is not None
                and 0 <= current_tile_index < num_tiles_in_set
            )

        elif selected_tab_index == 2:  # Supertile Editor Tab (index 2)
            copy_label = "Copy Supertile"
            paste_label = "Paste Supertile"
            can_copy = 0 <= current_supertile_index < num_supertiles
            can_paste = (
                supertile_clipboard_data is not None
                and 0 <= current_supertile_index < num_supertiles
            )

        elif selected_tab_index == 3:  # Map Editor Tab (index 3)
            copy_label = "Copy Map Region"
            paste_label = "Paste Map Region"
            can_copy = (
                self.map_selection_start_st is not None
                and self.map_selection_end_st is not None
            )
            can_paste = self.map_clipboard_data is not None

        else:  # Palette (0) tab
            copy_label = "Copy"
            paste_label = "Paste"
            can_copy = False
            can_paste = False

        copy_state = tk.NORMAL if can_copy else tk.DISABLED
        paste_state = tk.NORMAL if can_paste else tk.DISABLED

        try:
            current_copy_type = self.edit_menu.type(self.copy_menu_item_index)
            current_paste_type = self.edit_menu.type(self.paste_menu_item_index)
            if current_copy_type == "command":
                self.edit_menu.entryconfig(
                    self.copy_menu_item_index, state=copy_state, label=copy_label
                )
            # else:
            # print(f"  ERROR: Item at copy index {self.copy_menu_item_index} is not a 'command' type!")

            if current_paste_type == "command":
                self.edit_menu.entryconfig(
                    self.paste_menu_item_index, state=paste_state, label=paste_label
                )
            # else:
            # print(f"  ERROR: Item at paste index {self.paste_menu_item_index} is not a 'command' type!")

        except tk.TclError as e:
            # print(f"  ERROR during entryconfig: {e}")
            pass
        except Exception as e:
            # print(f"  UNEXPECTED ERROR during menu update: {e}")
            pass

    def handle_generic_copy(self):
        """Handles the generic 'Copy' menu command based on the active tab."""
        active_tab_index = -1
        try:
            if self.notebook and self.notebook.winfo_exists():
                active_tab_index = self.notebook.index(self.notebook.select())
        except tk.TclError:
            return # Cannot determine active tab

        # Clear map clipboard and preview ONLY if copy action is NOT for map region
        if active_tab_index != 3:
            # Check if map clipboard actually needs clearing before doing work
            if self.map_clipboard_data is not None:
                self.map_clipboard_data = None
                self._clear_paste_preview_rect()
                # Update menu state since map paste is now disabled
                self._update_edit_menu_state() # Update only if clipboard was cleared

        # Perform copy based on active tab
        if active_tab_index == 1:  # Tile Editor Tab
            self.copy_current_tile()
        elif active_tab_index == 2:  # Supertile Editor Tab
            self.copy_current_supertile()
        elif active_tab_index == 3:  # Map Editor Tab
            norm_coords = self._get_normalized_selection_st()
            if norm_coords: # If a selection exists, perform the copy
                min_c, min_r, max_c, max_r = norm_coords
                sel_w = max_c - min_c + 1
                sel_h = max_r - min_r + 1
                copied_data = []
                for r_idx in range(min_r, max_r + 1):
                    row_data = []
                    for c_idx in range(min_c, max_c + 1):
                        if 0 <= r_idx < map_height and 0 <= c_idx < map_width:
                            row_data.append(map_data[r_idx][c_idx])
                        else:
                            row_data.append(0)  # Append default if outside map
                    copied_data.append(row_data)

                # Set the map clipboard
                self.map_clipboard_data = {
                    "width": sel_w,
                    "height": sel_h,
                    "data": copied_data,
                }
                # Clear selection visual/state after successful copy
                self._clear_map_selection()
                # Explicitly clear any old paste preview visual
                self._clear_paste_preview_rect()
                # Redraw map canvas to remove selection rectangle
                self.draw_map_canvas()
                # Update menu state (enables Paste)
                self._update_edit_menu_state()
                # Attempt to draw the *new* paste preview based on current mouse pos
                try:
                    pointer_x = self.map_canvas.winfo_pointerx() - self.map_canvas.winfo_rootx()
                    pointer_y = self.map_canvas.winfo_pointery() - self.map_canvas.winfo_rooty()
                    if (0 <= pointer_x < self.map_canvas.winfo_width() and
                        0 <= pointer_y < self.map_canvas.winfo_height()):
                        canvas_x = self.map_canvas.canvasx(pointer_x)
                        canvas_y = self.map_canvas.canvasy(pointer_y)
                        self._draw_paste_preview_rect(canvas_coords=(canvas_x, canvas_y))
                except Exception:
                     pass # Ignore errors getting pointer position

            # else: # If no selection exists, simply do nothing for the map clipboard
            #    print("Copy Map Region: No selection active.") # Optional info message

    def handle_generic_paste(self):
        """Handles the generic 'Paste' menu command based on the active tab."""
        active_tab_index = -1
        try:
            if self.notebook and self.notebook.winfo_exists():
                active_tab_index = self.notebook.index(self.notebook.select())
        except tk.TclError:
            return # Cannot determine active tab

        if active_tab_index == 1:  # Tile Editor Tab
            self.paste_tile()
        elif active_tab_index == 2:  # Supertile Editor Tab
            self.paste_supertile()
        elif active_tab_index == 3:  # Map Editor Tab - NEW
            if self.map_clipboard_data:
                canvas = self.map_canvas
                # Get current mouse position relative to canvas for paste target
                try:
                    pointer_x = canvas.winfo_pointerx()
                    pointer_y = canvas.winfo_pointery()
                    root_x = canvas.winfo_rootx()
                    root_y = canvas.winfo_rooty()
                    canvas_x = canvas.canvasx(pointer_x - root_x)
                    canvas_y = canvas.canvasy(pointer_y - root_y)
                except tk.TclError:
                    messagebox.showerror("Paste Error", "Could not get mouse position.")
                    return

                paste_coords = self._get_supertile_coords_from_canvas(canvas_x, canvas_y)
                if paste_coords is None:
                    # Don't paste if mouse is outside map bounds
                    return

                paste_st_col, paste_st_row = paste_coords
                clip_w = self.map_clipboard_data["width"]
                clip_h = self.map_clipboard_data["height"]
                clip_data = self.map_clipboard_data["data"]
                modified = False

                # Perform the paste operation on map_data
                for r_offset in range(clip_h):
                    for c_offset in range(clip_w):
                        target_map_row = paste_st_row + r_offset
                        target_map_col = paste_st_col + c_offset

                        if (0 <= target_map_row < map_height and 0 <= target_map_col < map_width):
                            if r_offset < len(clip_data) and c_offset < len(clip_data[r_offset]):
                                st_index_to_paste = clip_data[r_offset][c_offset]
                                if map_data[target_map_row][target_map_col] != st_index_to_paste:
                                    map_data[target_map_row][target_map_col] = st_index_to_paste
                                    modified = True

                if modified:
                    self._mark_project_modified()
                    self.invalidate_minimap_background_cache()
                    # --- >> REMOVED redraw call for paste preview here << ---
                    self.draw_map_canvas()  # Redraw map; this will now include the paste preview
                    self.draw_minimap()  # Update minimap too
                # else:
                #    print("Paste: No changes made to map.")

            else:
                messagebox.showinfo("Paste", "Map clipboard is empty.")

    def _setup_global_key_bindings(self):
        """Sets up global keyboard shortcuts (accelerators) for menu commands."""
        # File Menu Bindings
        self.root.bind_all("<Control-n>", lambda event: self.new_project())
        self.root.bind_all("<Control-o>", lambda event: self.open_project())
        self.root.bind_all("<Control-s>", lambda event: self.save_project())
        # Note: Use <Control-Shift-KeyPress-S> for Ctrl+Shift+S reliably
        self.root.bind_all(
            "<Control-Shift-KeyPress-S>", lambda event: self.save_project_as()
        )
        self.root.bind_all("<Control-q>", lambda event: self.root.quit())

        # Edit Menu Bindings (Call the generic handlers)
        # Check state *within* the handler to see if action is allowed for the current tab
        self.root.bind_all("<Control-c>", lambda event: self.handle_generic_copy())
        self.root.bind_all("<Control-v>", lambda event: self.handle_generic_paste())

        # View Menu Bindings
        self.root.bind_all("<Control-m>", lambda event: self.toggle_minimap())

        # Add a print statement for confirmation (optional)
        print("Global key bindings set up.")

        # IMPORTANT: Prevent default text widget bindings for Copy/Paste if needed
        # This stops Ctrl+C/V from trying to act on focused widgets like Entries
        # if you want the menu action to ALWAYS take precedence.
        # Use with caution, might interfere with expected text editing.
        # self.root.event_delete("<<Copy>>", "<Control-c>")
        # self.root.event_delete("<<Paste>>", "<Control-v>")

    def handle_map_tab_keypress(self, event):
        """Handles key presses specifically bound when the Map Tab is active."""
        key = event.keysym.lower()

        if key == "g":  # MODIFIED CHECK
            # Only cycle color if the key is 'g' (this handler is only active on map tab)
            self.cycle_grid_color()
            return "break"  # Prevent any other default actions for 'g'

    def _place_tile_in_supertile(self, r, c):
        """Places the selected tile into the supertile definition at (r, c) and updates."""
        global supertiles_data, current_supertile_index, selected_tile_for_supertile
        # --- Validity Checks ---
        if not (0 <= current_supertile_index < num_supertiles):
            return False
        if not (0 <= selected_tile_for_supertile < num_tiles_in_set):
            return False
        if not (0 <= r < SUPERTILE_GRID_DIM and 0 <= c < SUPERTILE_GRID_DIM):
            return False

        # --- Check if Placement is Needed ---
        if (
            supertiles_data[current_supertile_index][r][c]
            != selected_tile_for_supertile
        ):
            # --- Perform Placement ---
            supertiles_data[current_supertile_index][r][c] = selected_tile_for_supertile
            self.invalidate_supertile_cache(current_supertile_index)
            # Need to redraw definition canvas, ST selector, and Map's ST selector
            self.update_all_displays(changed_level="supertile")
            self._mark_project_modified()
            return True  # Placed successfully
        else:
            return False  # No change needed

    def handle_supertile_def_drag(self, event):
        """Handles dragging the mouse while button 1 is pressed on the supertile definition canvas."""

        # --- Check if a valid tile is selected ---
        if not (0 <= selected_tile_for_supertile < num_tiles_in_set):
            return  # Don't drag-place if no valid tile is selected

        # --- Calculate Target Cell ---
        canvas = self.supertile_def_canvas
        size = SUPERTILE_DEF_TILE_SIZE
        # Basic check for valid canvas/size before division
        if size <= 0 or not canvas.winfo_exists():
            return
        col = event.x // size
        row = event.y // size

        current_cell = (row, col)

        # --- Check Bounds and If Cell is New ---
        if (
            0 <= row < SUPERTILE_GRID_DIM
            and 0 <= col < SUPERTILE_GRID_DIM
            and current_cell != self.last_placed_supertile_cell
        ):

            # --- Attempt Placement using Helper ---
            placed = self._place_tile_in_supertile(row, col)

            # --- Update Drag State if Placement Occurred ---
            if placed:
                self.last_placed_supertile_cell = current_cell

    def handle_supertile_def_release(self, event):
        """Resets the drag state when the mouse button is released over the supertile definition canvas."""
        self.last_placed_supertile_cell = None

    def _update_map_coords_display(self, event):
        """Updates the coordinate label based on mouse motion over the map canvas."""
        if not hasattr(self, "map_canvas") or not self.map_canvas.winfo_exists():
            return  # Canvas not ready

        canvas = self.map_canvas
        try:
            # Get coords relative to canvas content (handles scrolling)
            canvas_x = canvas.canvasx(event.x)
            canvas_y = canvas.canvasy(event.y)

            # Calculate supertile size at current zoom
            zoomed_tile_size = self.get_zoomed_tile_size()
            if zoomed_tile_size <= 0:
                return  # Avoid division by zero
            zoomed_supertile_size = SUPERTILE_GRID_DIM * zoomed_tile_size
            if zoomed_supertile_size <= 0:
                return  # Avoid division by zero

            # Calculate supertile row/col
            st_col = int(canvas_x // zoomed_supertile_size)
            st_row = int(canvas_y // zoomed_supertile_size)

            # Check map bounds
            if 0 <= st_row < map_height and 0 <= st_col < map_width:
                coords_text = f"ST Coords: {st_col}, {st_row}"  # Column first
            else:
                coords_text = "ST Coords: Out"

            # Update label if it exists
            if hasattr(self, "map_coords_label"):
                self.map_coords_label.config(text=coords_text)

        except Exception as e:
            # Avoid crashing if something goes wrong during coordinate calculation
            # print(f"Error updating map coords: {e}") # Optional debug
            if hasattr(self, "map_coords_label"):
                self.map_coords_label.config(text="ST Coords: Error")

    def _mark_project_modified(self):
        """Sets the project modified flag to True and updates the window title if needed."""
        if not self.project_modified:
            self.project_modified = True
            self._update_window_title()  # Update title when first marked as modified

    def flip_supertile_horizontal(self):
        global supertiles_data, current_supertile_index, num_supertiles
        if not (0 <= current_supertile_index < num_supertiles):
            return

        # Get the current definition (list of rows)
        current_definition = supertiles_data[current_supertile_index]
        new_definition = []
        for r in range(SUPERTILE_GRID_DIM):
            # Reverse each row individually
            new_definition.append(current_definition[r][::-1])  # Create reversed copy

        # Update the global data structure
        supertiles_data[current_supertile_index] = new_definition

        self._mark_project_modified()
        self.invalidate_supertile_cache(current_supertile_index)
        self.invalidate_minimap_background_cache()  # Map appearance using this ST changes
        self.update_all_displays(
            changed_level="supertile"
        )  # Update ST editor + Map stuff
        print(f"Supertile {current_supertile_index} flipped horizontally.")

    def flip_supertile_vertical(self):
        global supertiles_data, current_supertile_index, num_supertiles
        if not (0 <= current_supertile_index < num_supertiles):
            return

        # Get the current definition (list of rows)
        current_definition = supertiles_data[current_supertile_index]
        # Reverse the order of the rows
        current_definition.reverse()  # Modifies in-place

        # No need to reassign `supertiles_data[current_supertile_index]` as it was modified in-place

        self._mark_project_modified()
        self.invalidate_supertile_cache(current_supertile_index)
        self.invalidate_minimap_background_cache()  # Map appearance using this ST changes
        self.update_all_displays(
            changed_level="supertile"
        )  # Update ST editor + Map stuff
        print(f"Supertile {current_supertile_index} flipped vertically.")

    def rotate_supertile_90cw(self):
        global supertiles_data, current_supertile_index, num_supertiles
        if not (0 <= current_supertile_index < num_supertiles):
            return

        current_definition = supertiles_data[current_supertile_index]
        dim = SUPERTILE_GRID_DIM
        # Create a new grid initialized with zeros (or any placeholder)
        new_definition = [[0 for _ in range(dim)] for _ in range(dim)]

        # Perform the rotation: new[c][dim-1-r] = old[r][c]
        for r in range(dim):
            for c in range(dim):
                new_definition[c][(dim - 1) - r] = current_definition[r][c]

        # Update the global data structure
        supertiles_data[current_supertile_index] = new_definition

        self._mark_project_modified()
        self.invalidate_supertile_cache(current_supertile_index)
        self.invalidate_minimap_background_cache()  # Map appearance using this ST changes
        self.update_all_displays(
            changed_level="supertile"
        )  # Update ST editor + Map stuff
        print(f"Supertile {current_supertile_index} rotated 90 CW.")

    # Inside class TileEditorApp:

    # --- (After rotate_supertile_90cw method) ---

    def shift_supertile_up(self):
        global supertiles_data, current_supertile_index, num_supertiles
        dim = SUPERTILE_GRID_DIM
        if not (0 <= current_supertile_index < num_supertiles) or dim <= 0:
            return

        current_definition = supertiles_data[current_supertile_index]
        first_row = current_definition[0]  # Store the first row

        # Shift rows up
        for r in range(dim - 1):
            current_definition[r] = current_definition[r + 1]

        # Wrap the first row to the bottom
        current_definition[dim - 1] = first_row

        self._mark_project_modified()
        self.invalidate_supertile_cache(current_supertile_index)
        self.invalidate_minimap_background_cache()
        self.update_all_displays(changed_level="supertile")
        print(f"Supertile {current_supertile_index} shifted up.")

    def shift_supertile_down(self):
        global supertiles_data, current_supertile_index, num_supertiles
        dim = SUPERTILE_GRID_DIM
        if not (0 <= current_supertile_index < num_supertiles) or dim <= 0:
            return

        current_definition = supertiles_data[current_supertile_index]
        last_row = current_definition[dim - 1]  # Store the last row

        # Shift rows down
        for r in range(dim - 1, 0, -1):
            current_definition[r] = current_definition[r - 1]

        # Wrap the last row to the top
        current_definition[0] = last_row

        self._mark_project_modified()
        self.invalidate_supertile_cache(current_supertile_index)
        self.invalidate_minimap_background_cache()
        self.update_all_displays(changed_level="supertile")
        print(f"Supertile {current_supertile_index} shifted down.")

    def shift_supertile_left(self):
        global supertiles_data, current_supertile_index, num_supertiles
        dim = SUPERTILE_GRID_DIM
        if not (0 <= current_supertile_index < num_supertiles) or dim <= 0:
            return

        current_definition = supertiles_data[current_supertile_index]

        # Shift each row individually
        for r in range(dim):
            row_data = current_definition[r]
            first_tile_index = row_data[0]  # Store the first element
            # Shift elements left
            for c in range(dim - 1):
                row_data[c] = row_data[c + 1]
            # Wrap the first element to the end
            row_data[dim - 1] = first_tile_index

        self._mark_project_modified()
        self.invalidate_supertile_cache(current_supertile_index)
        self.invalidate_minimap_background_cache()
        self.update_all_displays(changed_level="supertile")
        print(f"Supertile {current_supertile_index} shifted left.")

    def shift_supertile_right(self):
        global supertiles_data, current_supertile_index, num_supertiles
        dim = SUPERTILE_GRID_DIM
        if not (0 <= current_supertile_index < num_supertiles) or dim <= 0:
            return

        current_definition = supertiles_data[current_supertile_index]

        # Shift each row individually
        for r in range(dim):
            row_data = current_definition[r]
            last_tile_index = row_data[dim - 1]  # Store the last element
            # Shift elements right
            for c in range(dim - 1, 0, -1):
                row_data[c] = row_data[c - 1]
            # Wrap the last element to the beginning
            row_data[0] = last_tile_index

        self._mark_project_modified()
        self.invalidate_supertile_cache(current_supertile_index)
        self.invalidate_minimap_background_cache()
        self.update_all_displays(changed_level="supertile")
        print(f"Supertile {current_supertile_index} shifted right.")

    def handle_supertile_def_right_click(self, event):
        """Handles right-click on the supertile definition canvas to select the clicked tile."""
        global selected_tile_for_supertile, current_supertile_index, num_supertiles, num_tiles_in_set, supertiles_data

        canvas = self.supertile_def_canvas
        size = SUPERTILE_DEF_TILE_SIZE
        if size <= 0 or not canvas.winfo_exists():
            return

        # Calculate column and row in the definition grid
        col = event.x // size
        row = event.y // size

        # Check if the click is within the grid bounds and a valid supertile is being edited
        if (
            0 <= row < SUPERTILE_GRID_DIM
            and 0 <= col < SUPERTILE_GRID_DIM
            and 0 <= current_supertile_index < num_supertiles
        ):
            try:
                # Get the tile index at the clicked position
                clicked_tile_index = supertiles_data[current_supertile_index][row][col]

                # Check if the retrieved tile index is valid within the current tileset
                if 0 <= clicked_tile_index < num_tiles_in_set:
                    # Check if the selection actually changed
                    if selected_tile_for_supertile != clicked_tile_index:
                        selected_tile_for_supertile = clicked_tile_index
                        print(
                            f"Right-click selected Tile: {selected_tile_for_supertile}"
                        )
                        # Redraw the tileset selector in the supertile tab
                        self.draw_tileset_viewer(
                            self.st_tileset_canvas, selected_tile_for_supertile
                        )
                        # Update the info label
                        self.update_supertile_info_labels()
                        # Scroll the viewer to the selected tile
                        self.scroll_viewers_to_tile(selected_tile_for_supertile)
                else:
                    print(
                        f"Right-click: Tile index {clicked_tile_index} at [{row},{col}] is out of bounds (max {num_tiles_in_set-1})."
                    )

            except IndexError:
                print(
                    f"Right-click: Error accessing supertile data for index {current_supertile_index} at [{row},{col}]."
                )
            except Exception as e:
                print(f"Right-click: Unexpected error in supertile def handler: {e}")

    def handle_map_canvas_right_click(self, event):
        """Handles right-click on the map canvas to select the clicked supertile."""
        global selected_supertile_for_map, map_data, map_width, map_height, num_supertiles

        # Prevent interference with panning or other actions
        if self.current_mouse_action is not None:
            return "break"  # Stop event propagation if another action is active

        canvas = self.map_canvas
        if not canvas.winfo_exists():
            return

        # Calculate zoomed supertile size
        zoomed_tile_size = self.get_zoomed_tile_size()
        if zoomed_tile_size <= 0:
            return
        zoomed_supertile_size = SUPERTILE_GRID_DIM * zoomed_tile_size
        if zoomed_supertile_size <= 0:
            return

        # Get canvas coordinates (handles scrolling)
        canvas_x = canvas.canvasx(event.x)
        canvas_y = canvas.canvasy(event.y)

        # Calculate map column and row in supertile units
        map_col = int(canvas_x // zoomed_supertile_size)
        map_row = int(canvas_y // zoomed_supertile_size)

        # Check if the click is within the map bounds
        if 0 <= map_row < map_height and 0 <= map_col < map_width:
            try:
                # Get the supertile index at the clicked map cell
                clicked_supertile_index = map_data[map_row][map_col]

                # Check if the retrieved supertile index is valid
                if 0 <= clicked_supertile_index < num_supertiles:
                    # Check if the selection actually changed
                    if selected_supertile_for_map != clicked_supertile_index:
                        selected_supertile_for_map = clicked_supertile_index
                        print(
                            f"Right-click selected Supertile: {selected_supertile_for_map}"
                        )
                        # Redraw the supertile selector in the map tab
                        self.draw_supertile_selector(
                            self.map_supertile_selector_canvas,
                            selected_supertile_for_map,
                        )
                        # Update the info label
                        self.update_map_info_labels()
                        # Scroll the selector to the selected supertile
                        self.scroll_selectors_to_supertile(selected_supertile_for_map)
                else:
                    print(
                        f"Right-click: Supertile index {clicked_supertile_index} at map [{map_row},{map_col}] is out of bounds (max {num_supertiles-1})."
                    )

            except IndexError:
                print(
                    f"Right-click: Error accessing map data at [{map_row},{map_col}]."
                )
            except Exception as e:
                print(f"Right-click: Unexpected error in map canvas handler: {e}")

    def _check_tile_usage(self, tile_index):
        """Checks if a tile_index is used in any supertile definitions.
        Returns a list of supertile indices that use it.
        """
        used_in_supertiles = []
        if not (0 <= tile_index < num_tiles_in_set):
            return used_in_supertiles  # Invalid index

        for st_idx in range(num_supertiles):
            definition = supertiles_data[st_idx]
            for r in range(SUPERTILE_GRID_DIM):
                for c in range(SUPERTILE_GRID_DIM):
                    if definition[r][c] == tile_index:
                        if st_idx not in used_in_supertiles:
                            used_in_supertiles.append(st_idx)
                        break  # Found in this supertile, move to next one
                if st_idx in used_in_supertiles:
                    break  # Already found in this ST
        return used_in_supertiles

    def _check_supertile_usage(self, supertile_index):
        """Checks if a supertile_index is used in the map data.
        Returns a list of (row, col) map coordinates that use it.
        """
        used_in_map = []
        if not (0 <= supertile_index < num_supertiles):
            return used_in_map  # Invalid index

        for r in range(map_height):
            for c in range(map_width):
                if map_data[r][c] == supertile_index:
                    used_in_map.append((r, c))
        return used_in_map

    # --- NEW: Reference Update Helpers ---
    def _update_supertile_refs_for_tile_change(self, index, action):
        """Updates tile indices in ALL supertile definitions after a tile insert/delete.

        Args:
            index (int): The index where the tile insert/delete occurred.
            action (str): 'insert' or 'delete'.
        """
        if action == "insert":
            # Increment references >= index
            for st_idx in range(num_supertiles):
                definition = supertiles_data[st_idx]
                for r in range(SUPERTILE_GRID_DIM):
                    for c in range(SUPERTILE_GRID_DIM):
                        if definition[r][c] >= index:
                            supertiles_data[st_idx][r][c] += 1
        elif action == "delete":
            # Decrement references > index, set == index to 0
            for st_idx in range(num_supertiles):
                definition = supertiles_data[st_idx]
                for r in range(SUPERTILE_GRID_DIM):
                    for c in range(SUPERTILE_GRID_DIM):
                        if definition[r][c] == index:
                            supertiles_data[st_idx][r][
                                c
                            ] = 0  # Replace deleted with tile 0
                        elif definition[r][c] > index:
                            supertiles_data[st_idx][r][c] -= 1
        else:
            print(
                f"Warning: Unknown action '{action}' in _update_supertile_refs_for_tile_change"
            )

    def _update_map_refs_for_supertile_change(self, index, action):
        """Updates supertile indices in the map data after a supertile insert/delete.

        Args:
            index (int): The index where the supertile insert/delete occurred.
            action (str): 'insert' or 'delete'.
        """
        if action == "insert":
            # Increment references >= index
            for r in range(map_height):
                for c in range(map_width):
                    if map_data[r][c] >= index:
                        map_data[r][c] += 1
        elif action == "delete":
            # Decrement references > index, set == index to 0
            for r in range(map_height):
                for c in range(map_width):
                    if map_data[r][c] == index:
                        map_data[r][c] = 0  # Replace deleted with supertile 0
                    elif map_data[r][c] > index:
                        map_data[r][c] -= 1
        else:
            print(
                f"Warning: Unknown action '{action}' in _update_map_refs_for_supertile_change"
            )

    def _insert_tile(self, index):
        """Core logic to insert a blank tile at the specified index.

        Args:
            index (int): The index at which to insert.

        Returns:
            bool: True if insertion was successful, False otherwise.
        """
        global num_tiles_in_set, tileset_patterns, tileset_colors, WHITE_IDX, BLACK_IDX

        if not (
            0 <= index <= num_tiles_in_set
        ):  # Allow inserting at the end (index == count)
            print(
                f"Error: Insert tile index {index} out of range [0, {num_tiles_in_set}]."
            )
            return False
        if num_tiles_in_set >= MAX_TILES:
            print("Error: Cannot insert tile, maximum tiles reached.")
            # Optionally show messagebox if needed later, but core logic just returns False
            # messagebox.showwarning("Maximum Tiles", f"Cannot insert: Max {MAX_TILES} tiles reached.")
            return False

        # Create blank tile data
        blank_pattern = [[0] * TILE_WIDTH for _ in range(TILE_HEIGHT)]
        blank_colors = [(WHITE_IDX, BLACK_IDX) for _ in range(TILE_HEIGHT)]

        # Insert into data lists
        tileset_patterns.insert(index, blank_pattern)
        tileset_colors.insert(index, blank_colors)
        # Remove the overflow if MAX_TILES was exceeded by insert (shouldn't happen due to check)
        # Although Python lists grow, our MAX_TILES implies a fixed-size array conceptually
        if len(tileset_patterns) > MAX_TILES:
            tileset_patterns.pop()
        if len(tileset_colors) > MAX_TILES:
            tileset_colors.pop()

        # Update references in supertiles
        self._update_supertile_refs_for_tile_change(index, "insert")

        # Mark modified AFTER successful data changes
        self._mark_project_modified()
        return True

    def _delete_tile(self, index):
        """Core logic to delete the tile at the specified index.

        Args:
            index (int): The index of the tile to delete.

        Returns:
            bool: True if deletion was successful, False otherwise.
        """
        global num_tiles_in_set, tileset_patterns, tileset_colors

        if not (0 <= index < num_tiles_in_set):
            print(
                f"Error: Delete tile index {index} out of range [0, {num_tiles_in_set - 1}]."
            )
            return False
        if num_tiles_in_set <= 1:
            print("Error: Cannot delete the last tile.")
            # messagebox.showwarning("Cannot Delete", "Cannot delete the last remaining tile.")
            return False

        # --- Confirmation is handled by the UI caller ---

        # Delete from data lists
        del tileset_patterns[index]
        del tileset_colors[index]

        # Append dummy data to keep list size MAX_TILES (conceptually)
        # Or adjust MAX_TILES usage if lists are truly dynamic
        # For now, let's assume we might refill later, so keep placeholders?
        # Alternative: just let list shrink. Let's let it shrink.
        # tileset_patterns.append([[0]*TILE_WIDTH for _ in range(TILE_HEIGHT)])
        # tileset_colors.append([(WHITE_IDX, BLACK_IDX) for _ in range(TILE_HEIGHT)])

        # Update references in supertiles
        self._update_supertile_refs_for_tile_change(index, "delete")

        # Mark modified AFTER successful data changes
        self._mark_project_modified()
        return True

    def _insert_supertile(self, index):
        """Core logic to insert a blank supertile at the specified index.

        Args:
            index (int): The index at which to insert.

        Returns:
            bool: True if insertion was successful, False otherwise.
        """
        global num_supertiles, supertiles_data

        if not (0 <= index <= num_supertiles):  # Allow insert at end
            print(
                f"Error: Insert supertile index {index} out of range [0, {num_supertiles}]."
            )
            return False
        if num_supertiles >= MAX_SUPERTILES:
            print("Error: Cannot insert supertile, maximum reached.")
            # messagebox.showwarning("Maximum Supertiles", f"Cannot insert: Max {MAX_SUPERTILES} supertiles reached.")
            return False

        # Create blank supertile data (all point to tile 0)
        blank_definition = [[0] * SUPERTILE_GRID_DIM for _ in range(SUPERTILE_GRID_DIM)]

        # Insert into data list
        supertiles_data.insert(index, blank_definition)
        if len(supertiles_data) > MAX_SUPERTILES:
            supertiles_data.pop()  # Maintain conceptual limit

        # Update references in map
        self._update_map_refs_for_supertile_change(index, "insert")

        self._mark_project_modified()
        return True

    def _delete_supertile(self, index):
        """Core logic to delete the supertile at the specified index.

        Args:
            index (int): The index of the supertile to delete.

        Returns:
            bool: True if deletion was successful, False otherwise.
        """
        global num_supertiles, supertiles_data

        if not (0 <= index < num_supertiles):
            print(
                f"Error: Delete supertile index {index} out of range [0, {num_supertiles - 1}]."
            )
            return False
        if num_supertiles <= 1:
            print("Error: Cannot delete the last supertile.")
            # messagebox.showwarning("Cannot Delete", "Cannot delete the last remaining supertile.")
            return False

        # --- Confirmation is handled by the UI caller ---

        # Delete from data list
        del supertiles_data[index]
        # Let list shrink

        # Update references in map
        self._update_map_refs_for_supertile_change(index, "delete")

        self._mark_project_modified()
        return True

    def _update_editor_button_states(self):
        """Updates the enable/disable state of Add/Insert/Delete buttons."""
        global num_tiles_in_set, num_supertiles

        # --- Tile Editor Buttons ---
        can_add_tile = num_tiles_in_set < MAX_TILES
        can_insert_tile = num_tiles_in_set < MAX_TILES
        can_delete_tile = num_tiles_in_set > 1

        if hasattr(self, "add_tile_button"):
            self.add_tile_button.config(
                state=tk.NORMAL if can_add_tile else tk.DISABLED
            )
        if hasattr(self, "insert_tile_button"):
            self.insert_tile_button.config(
                state=tk.NORMAL if can_insert_tile else tk.DISABLED
            )
        if hasattr(self, "delete_tile_button"):
            self.delete_tile_button.config(
                state=tk.NORMAL if can_delete_tile else tk.DISABLED
            )

        # --- Supertile Editor Buttons ---
        can_add_supertile = num_supertiles < MAX_SUPERTILES
        can_insert_supertile = num_supertiles < MAX_SUPERTILES
        can_delete_supertile = num_supertiles > 1

        if hasattr(self, "add_supertile_button"):
            self.add_supertile_button.config(
                state=tk.NORMAL if can_add_supertile else tk.DISABLED
            )
        if hasattr(self, "insert_supertile_button"):
            self.insert_supertile_button.config(
                state=tk.NORMAL if can_insert_supertile else tk.DISABLED
            )
        if hasattr(self, "delete_supertile_button"):
            self.delete_supertile_button.config(
                state=tk.NORMAL if can_delete_supertile else tk.DISABLED
            )

    def handle_add_tile(self):  # Renamed from add_new_tile
        global num_tiles_in_set, current_tile_index
        # Use core insert logic at the end
        success = self._insert_tile(num_tiles_in_set)  # Insert at the very end

        if success:
            num_tiles_in_set += 1
            new_tile_idx = num_tiles_in_set - 1
            current_tile_index = new_tile_idx  # Select the newly added tile

            # Update displays and scroll
            self.clear_all_caches()  # Tile added affects STs, Map
            self.invalidate_minimap_background_cache()
            self.update_all_displays(changed_level="all")  # Update everything
            self.scroll_viewers_to_tile(current_tile_index)
            self._update_editor_button_states()  # Update button states
            print(f"Added new tile {new_tile_idx}")
        else:
            messagebox.showwarning(
                "Add Tile Failed", f"Could not add tile. Maximum {MAX_TILES} reached?"
            )

    def handle_insert_tile(self):
        global num_tiles_in_set, current_tile_index, selected_tile_for_supertile

        insert_idx = current_tile_index
        success = self._insert_tile(insert_idx)

        if success:
            num_tiles_in_set += 1
            # Selection stays at insert_idx (which is the new blank tile)
            current_tile_index = insert_idx

            # Adjust other selections if they were >= insert_idx
            if selected_tile_for_supertile >= insert_idx:
                selected_tile_for_supertile += 1

            self.clear_all_caches()
            self.invalidate_minimap_background_cache()
            self.update_all_displays(changed_level="all")
            self.scroll_viewers_to_tile(current_tile_index)
            self._update_editor_button_states()
            print(f"Inserted tile at index {insert_idx}")
        else:
            messagebox.showwarning(
                "Insert Tile Failed",
                f"Could not insert tile. Maximum {MAX_TILES} reached?",
            )

    def handle_delete_tile(self):
        global num_tiles_in_set, current_tile_index, selected_tile_for_supertile

        if num_tiles_in_set <= 1:
            messagebox.showinfo("Delete Tile", "Cannot delete the last tile.")
            return

        delete_idx = current_tile_index
        if not (0 <= delete_idx < num_tiles_in_set):
            messagebox.showerror("Delete Tile Error", "Invalid tile index selected.")
            return

        # --- Confirmation ---
        usage = self._check_tile_usage(delete_idx)
        confirm_msg = f"Delete Tile {delete_idx}?"
        if usage:
            confirm_msg += "\n\n*** WARNING! ***\nThis tile is used by the following Supertile(s):\n"
            confirm_msg += ", ".join(map(str, usage[:10]))  # Show first 10 usages
            if len(usage) > 10:
                confirm_msg += "..."
            confirm_msg += (
                f"\n\nReferences in these Supertiles will be reset to Tile 0."
            )

        if not messagebox.askokcancel("Confirm Delete", confirm_msg, icon="warning"):
            return
        # --- End Confirmation ---

        success = self._delete_tile(delete_idx)

        if success:
            num_tiles_in_set -= 1
            # Adjust selection: stay at index if possible, else clamp to new max
            current_tile_index = min(delete_idx, num_tiles_in_set - 1)

            # Adjust other selections if they pointed to deleted or higher index
            if selected_tile_for_supertile == delete_idx:
                selected_tile_for_supertile = 0
            elif selected_tile_for_supertile > delete_idx:
                selected_tile_for_supertile -= 1

            self.clear_all_caches()
            self.invalidate_minimap_background_cache()
            self.update_all_displays(changed_level="all")
            self.scroll_viewers_to_tile(current_tile_index)  # Scroll to new selection
            self._update_editor_button_states()
            print(f"Deleted tile at index {delete_idx}")
        else:
            # Core logic failure (shouldn't happen if checks pass, but good practice)
            messagebox.showerror(
                "Delete Tile Failed", "An error occurred during tile deletion."
            )

    def handle_add_supertile(self):  # Renamed from add_new_supertile
        global num_supertiles, current_supertile_index

        success = self._insert_supertile(num_supertiles)  # Insert at end

        if success:
            num_supertiles += 1
            new_st_idx = num_supertiles - 1
            current_supertile_index = new_st_idx  # Select the new one

            self.supertile_image_cache.clear()  # Clear ST cache only
            self.invalidate_minimap_background_cache()
            self.update_all_displays(
                changed_level="supertile"
            )  # Update ST editor + Map stuff
            self.scroll_selectors_to_supertile(current_supertile_index)
            self._update_editor_button_states()
            print(f"Added new supertile {new_st_idx}")
        else:
            messagebox.showwarning(
                "Add Supertile Failed",
                f"Could not add supertile. Maximum {MAX_SUPERTILES} reached?",
            )

    def handle_insert_supertile(self):
        global num_supertiles, current_supertile_index, selected_supertile_for_map

        insert_idx = current_supertile_index
        success = self._insert_supertile(insert_idx)

        if success:
            num_supertiles += 1
            # Selection stays at insert_idx
            current_supertile_index = insert_idx

            # Adjust other selections if they were >= insert_idx
            if selected_supertile_for_map >= insert_idx:
                selected_supertile_for_map += 1

            self.supertile_image_cache.clear()
            self.invalidate_minimap_background_cache()
            self.update_all_displays(changed_level="supertile")
            self.scroll_selectors_to_supertile(current_supertile_index)
            self._update_editor_button_states()
            print(f"Inserted supertile at index {insert_idx}")
        else:
            messagebox.showwarning(
                "Insert Supertile Failed",
                f"Could not insert supertile. Maximum {MAX_SUPERTILES} reached?",
            )

    def handle_delete_supertile(self):
        global num_supertiles, current_supertile_index, selected_supertile_for_map

        if num_supertiles <= 1:
            messagebox.showinfo("Delete Supertile", "Cannot delete the last supertile.")
            return

        delete_idx = current_supertile_index
        if not (0 <= delete_idx < num_supertiles):
            messagebox.showerror(
                "Delete Supertile Error", "Invalid supertile index selected."
            )
            return

        # --- Confirmation ---
        usage = self._check_supertile_usage(delete_idx)
        confirm_msg = f"Delete Supertile {delete_idx}?"
        if usage:
            map_coords_str = ", ".join(
                [f"({r},{c})" for r, c in usage[:10]]
            )  # Show first 10 usages
            confirm_msg += (
                "\n\n*** WARNING! ***\nThis supertile is used on the Map at:\n"
            )
            confirm_msg += map_coords_str
            if len(usage) > 10:
                confirm_msg += "..."
            confirm_msg += f"\n\nReferences on the Map will be reset to Supertile 0."

        if not messagebox.askokcancel("Confirm Delete", confirm_msg, icon="warning"):
            return
        # --- End Confirmation ---

        success = self._delete_supertile(delete_idx)

        if success:
            num_supertiles -= 1
            # Adjust selection
            current_supertile_index = min(delete_idx, num_supertiles - 1)

            # Adjust other selections
            if selected_supertile_for_map == delete_idx:
                selected_supertile_for_map = 0
            elif selected_supertile_for_map > delete_idx:
                selected_supertile_for_map -= 1

            self.supertile_image_cache.clear()
            self.invalidate_minimap_background_cache()
            self.update_all_displays(changed_level="supertile")
            self.scroll_selectors_to_supertile(current_supertile_index)
            self._update_editor_button_states()
            print(f"Deleted supertile at index {delete_idx}")
        else:
            messagebox.showerror(
                "Delete Supertile Failed",
                "An error occurred during supertile deletion.",
            )

    def _reposition_tile(self, source_index, target_index):
        """Moves a tile from source_index to target_index, updating references. (Corrected)"""
        global num_tiles_in_set, tileset_patterns, tileset_colors
        global current_tile_index, selected_tile_for_supertile  # Need to update selections

        original_num_tiles = num_tiles_in_set  # Store original count

        if source_index == target_index or not (0 <= source_index < original_num_tiles):
            return False  # No move needed or invalid source

        # Clamp target index based on original count (can drop after the end)
        target_index = max(0, min(target_index, original_num_tiles))

        print(f"Attempting to move Tile from {source_index} to target {target_index}")

        # 1. Store the data of the tile being moved
        moved_pattern = copy.deepcopy(tileset_patterns[source_index])
        moved_colors = copy.deepcopy(tileset_colors[source_index])

        # 2. Delete the tile at the source index (using original count for validation within _delete_tile)
        success_delete = self._delete_tile(source_index)
        if not success_delete:
            print(f"  ERROR: _delete_tile failed for index {source_index}")
            # Don't change count if delete failed
            return False

        # 3. *** AFTER successful delete, NOW decrement the count ***
        num_tiles_in_set -= 1

        # 4. Determine the actual insertion index based on potentially shifted target
        #    If target was after source, deletion shifted indices down by 1
        actual_insert_index = target_index
        if target_index > source_index:
            actual_insert_index -= 1
        # Clamp against the *current* (decremented) count for insertion range
        actual_insert_index = max(0, min(actual_insert_index, num_tiles_in_set))

        # 5. *** BEFORE insert, increment the count back ***
        num_tiles_in_set += 1

        # 6. Insert a *blank* tile at the actual insert index (using restored count for validation within _insert_tile)
        success_insert = self._insert_tile(actual_insert_index)
        if not success_insert:
            # This is tricky - need to revert the deletion if insert fails.
            # For now, log error. Mark modified as data is inconsistent.
            print(
                f"  CRITICAL ERROR: _insert_tile failed at {actual_insert_index} after successful delete!"
            )
            # Attempt to restore count to reflect failed insert
            num_tiles_in_set -= 1
            self._mark_project_modified()
            return False

        # 7. Replace the newly inserted blank tile with the stored data
        tileset_patterns[actual_insert_index] = moved_pattern
        tileset_colors[actual_insert_index] = moved_colors

        # 8. Update selections (use original_num_tiles for comparisons if needed, but logic should be ok)
        if current_tile_index == source_index:
            current_tile_index = actual_insert_index
        elif (
            source_index < current_tile_index < target_index
        ):  # Item between source and target (moving down)
            current_tile_index -= 1
        elif (
            target_index <= current_tile_index < source_index
        ):  # Item between target and source (moving up)
            current_tile_index += 1

        if selected_tile_for_supertile == source_index:
            selected_tile_for_supertile = actual_insert_index
        elif source_index < selected_tile_for_supertile < target_index:
            selected_tile_for_supertile -= 1
        elif target_index <= selected_tile_for_supertile < source_index:
            selected_tile_for_supertile += 1

        # Clamp selections just in case they somehow went out of bounds
        current_tile_index = max(0, min(current_tile_index, num_tiles_in_set - 1))
        selected_tile_for_supertile = max(
            0, min(selected_tile_for_supertile, num_tiles_in_set - 1)
        )

        self._mark_project_modified()
        # Invalidate caches - tile itself, all supertiles using tiles, and minimap
        self.invalidate_tile_cache(actual_insert_index)
        self.supertile_image_cache.clear()
        self.invalidate_minimap_background_cache()
        print(f"  Successfully moved Tile {source_index} to {actual_insert_index}")
        return True

    def _reposition_supertile(self, source_index, target_index):
        """Moves a supertile from source_index to target_index, updating references. (Corrected)"""
        global num_supertiles, supertiles_data
        global current_supertile_index, selected_supertile_for_map  # Selections

        original_num_supertiles = num_supertiles  # Store original count

        if source_index == target_index or not (
            0 <= source_index < original_num_supertiles
        ):
            return False  # No move needed or invalid source

        # Clamp target index based on original count
        target_index = max(0, min(target_index, original_num_supertiles))
        print(
            f"Attempting to move Supertile from {source_index} to target {target_index}"
        )

        # 1. Store data
        moved_definition = copy.deepcopy(supertiles_data[source_index])

        # 2. Delete (using original count for validation within _delete_supertile)
        success_delete = self._delete_supertile(source_index)
        if not success_delete:
            print(f"  ERROR: _delete_supertile failed for index {source_index}")
            return False

        # 3. *** AFTER successful delete, NOW decrement the count ***
        num_supertiles -= 1

        # 4. Determine actual insert index
        actual_insert_index = target_index
        if target_index > source_index:
            actual_insert_index -= 1
        # Clamp against the *current* (decremented) count
        actual_insert_index = max(0, min(actual_insert_index, num_supertiles))

        # 5. *** BEFORE insert, increment the count back ***
        num_supertiles += 1

        # 6. Insert blank (using restored count for validation within _insert_supertile)
        success_insert = self._insert_supertile(actual_insert_index)
        if not success_insert:
            print(
                f"  CRITICAL ERROR: _insert_supertile failed at {actual_insert_index} after successful delete!"
            )
            num_supertiles -= 1  # Attempt to restore count
            self._mark_project_modified()
            return False

        # 7. Replace blank with stored data
        supertiles_data[actual_insert_index] = moved_definition

        # 8. Update selections
        if current_supertile_index == source_index:
            current_supertile_index = actual_insert_index
        elif source_index < current_supertile_index < target_index:
            current_supertile_index -= 1
        elif target_index <= current_supertile_index < source_index:
            current_supertile_index += 1

        if selected_supertile_for_map == source_index:
            selected_supertile_for_map = actual_insert_index
        elif source_index < selected_supertile_for_map < target_index:
            selected_supertile_for_map -= 1
        elif target_index <= selected_supertile_for_map < source_index:
            selected_supertile_for_map += 1

        # Clamp selections
        current_supertile_index = max(
            0, min(current_supertile_index, num_supertiles - 1)
        )
        selected_supertile_for_map = max(
            0, min(selected_supertile_for_map, num_supertiles - 1)
        )

        self._mark_project_modified()
        # Invalidate caches - supertile itself and minimap (map refs updated internally)
        self.invalidate_supertile_cache(actual_insert_index)
        self.invalidate_minimap_background_cache()
        print(f"  Successfully moved Supertile {source_index} to {actual_insert_index}")
        return True

    def _get_index_from_canvas_coords(self, canvas, x, y, item_type):
        """Helper to get tile or supertile index from canvas coords.

        Args:
            canvas (tk.Canvas): The canvas that was clicked.
            x (int): Event x coordinate relative to the canvas widget.
            y (int): Event y coordinate relative to the canvas widget.
            item_type (str): 'tile' or 'supertile'.

        Returns:
            int: The calculated index (0 to max_items-1),
                 or max_items if clicked after the last item in the grid area,
                 or -2 if clicked outside the grid content area (but within canvas bounds),
                 or -1 on error (invalid type, zero size).
        """
        padding = 1
        items_across = 0
        item_size = 0
        max_items = 0  # This will be the *count* (e.g., num_tiles_in_set)

        # Determine layout parameters based on item type
        if item_type == "tile":
            items_across = NUM_TILES_ACROSS
            item_size = VIEWER_TILE_SIZE
            max_items = num_tiles_in_set
        elif item_type == "supertile":
            items_across = NUM_SUPERTILES_ACROSS
            item_size = SUPERTILE_SELECTOR_PREVIEW_SIZE
            max_items = num_supertiles
        else:
            print(
                f"Error: Invalid item_type '{item_type}' in _get_index_from_canvas_coords"
            )
            return -1  # Invalid type

        # Basic safety checks
        if item_size <= 0 or items_across <= 0:
            print(
                f"Error: Invalid item_size ({item_size}) or items_across ({items_across})"
            )
            return -1

        # Get coordinates relative to the canvas's scrollable content
        try:
            canvas_x = canvas.canvasx(x)
            canvas_y = canvas.canvasy(y)
        except tk.TclError:
            # Might happen if canvas is not fully configured yet
            return -1

        # Calculate the total pixel dimensions of the grid content area
        # Use max_items for calculation, ensuring at least one row/col conceptually
        num_rows = max(1, math.ceil(max_items / items_across))
        total_width = items_across * (item_size + padding) + padding
        total_height = num_rows * (item_size + padding) + padding

        # Check if click is outside the logical grid content area
        # (Allow clicks slightly outside top/left due to padding/rounding)
        if not (
            -padding <= canvas_x < total_width and -padding <= canvas_y < total_height
        ):
            # print(f"Debug: Click ({canvas_x},{canvas_y}) outside grid area ({total_width}x{total_height})")
            return -2  # Clicked outside grid content area

        # Calculate column and row based on the grid layout
        col = int(canvas_x // (item_size + padding))
        row = int(canvas_y // (item_size + padding))

        # Clamp row/col just in case calculation goes slightly negative near edge
        col = max(0, col)
        row = max(0, row)

        # Calculate the potential index
        index = row * items_across + col

        # Check if the calculated index is within the valid range of actual items
        if 0 <= index < max_items:
            return index
        else:
            # Clicked within grid area but beyond the last *valid* item index.
            # This signifies a potential drop target at the end of the list.
            # print(f"Debug: Index {index} >= max_items {max_items}. Returning max_items.")
            return max_items  # Return the count to indicate "end of list" target

    def handle_viewer_drag_motion(self, event):
        """Handles mouse motion during drag over viewer/selector canvases.
        Activates drag state on first significant motion after a potential start.
        """
        # Check if a potential drag was initiated on Button-1 press
        # (drag_start_index is set, but drag_active is still False)
        if self.drag_start_index != -1 and not self.drag_active:
            # *** This is the first motion event after the click on a valid item ***
            # -> Activate the drag state now!
            self.drag_active = True
            print(
                f"Drag Activated for {self.drag_item_type} index {self.drag_start_index}"
            )  # Debug

            # Redraw the source canvas immediately to show the yellow highlight
            if self.drag_canvas and self.drag_canvas.winfo_exists():
                if self.drag_item_type == "tile":
                    # Find the appropriate highlighted index for the *other* tile viewer
                    other_highlight = -1
                    if self.drag_canvas == self.tileset_canvas:
                        other_highlight = selected_tile_for_supertile
                    elif self.drag_canvas == self.st_tileset_canvas:
                        other_highlight = current_tile_index
                    self.draw_tileset_viewer(
                        self.drag_canvas, other_highlight
                    )  # Redraw source
                elif self.drag_item_type == "supertile":
                    # Find the appropriate highlighted index for the *other* supertile selector
                    other_highlight = -1
                    if self.drag_canvas == self.supertile_selector_canvas:
                        other_highlight = selected_supertile_for_map
                    elif self.drag_canvas == self.map_supertile_selector_canvas:
                        other_highlight = current_supertile_index
                    self.draw_supertile_selector(
                        self.drag_canvas, other_highlight
                    )  # Redraw source

        # If drag is not active (either never started or cancelled), do nothing more
        if not self.drag_active:
            return

        # --- Drag is active, proceed with indicator logic ---
        canvas = event.widget  # The canvas where the motion event occurred

        # Safety check: ensure the drag canvas is still valid
        if not self.drag_canvas or not self.drag_canvas.winfo_exists():
            print(
                "Warning: Drag cancelled because originating canvas no longer exists."
            )
            self.drag_active = False
            if self.drag_indicator_id and canvas.winfo_exists():
                try:
                    canvas.delete(self.drag_indicator_id)
                except tk.TclError:
                    pass
            self.drag_indicator_id = None
            self.drag_canvas = None
            self.drag_item_type = None
            self.drag_start_index = -1
            return

        # Get the potential target index under the cursor on the CURRENT event canvas
        target_index = self._get_index_from_canvas_coords(
            canvas, event.x, event.y, self.drag_item_type
        )

        # --- Update Drop Indicator Line ---
        if self.drag_indicator_id:
            try:
                self.drag_canvas.delete(self.drag_indicator_id)
            except tk.TclError:
                pass
            self.drag_indicator_id = None

        # Draw the *new* indicator only if the target is valid (>= 0) and on the original drag canvas
        if target_index >= 0 and canvas == self.drag_canvas:
            padding = 1
            item_size = 0
            items_across = 0
            max_items = 0

            if self.drag_item_type == "tile":
                item_size = VIEWER_TILE_SIZE
                items_across = NUM_TILES_ACROSS
                max_items = num_tiles_in_set
            elif self.drag_item_type == "supertile":
                item_size = SUPERTILE_SELECTOR_PREVIEW_SIZE
                items_across = NUM_SUPERTILES_ACROSS
                max_items = num_supertiles

            if item_size > 0 and items_across > 0:
                indicator_pos_index = min(target_index, max_items)
                row, col = divmod(indicator_pos_index, items_across)
                line_x = col * (item_size + padding) + padding / 2
                line_y1 = row * (item_size + padding) + padding / 2
                line_y2 = line_y1 + item_size

                self.drag_indicator_id = self.drag_canvas.create_line(
                    line_x,
                    line_y1,
                    line_x,
                    line_y2,
                    fill="yellow",
                    width=3,
                    tags="drop_indicator",
                )

        # Update cursor to indicate dragging state
        try:
            if canvas.cget("cursor") != "hand2":
                canvas.config(cursor="hand2")
        except tk.TclError:
            pass

    def handle_viewer_drag_release(self, event):
        """Handles mouse button release over viewer/selector canvases.
        Completes either a click selection or a drag-and-drop repositioning.
        """
        global current_tile_index, selected_tile_for_supertile  # Selections
        global current_supertile_index, selected_supertile_for_map  # Selections

        canvas = event.widget  # Canvas where release occurred
        was_dragging = self.drag_active  # Check drag state BEFORE resetting

        # --- Always clean up visual drag indicators first ---
        if self.drag_indicator_id:
            # Try deleting from original drag canvas first, then current canvas
            try:
                if self.drag_canvas and self.drag_canvas.winfo_exists():
                    self.drag_canvas.delete(self.drag_indicator_id)
                elif canvas.winfo_exists():  # Fallback to current canvas
                    canvas.delete(self.drag_indicator_id)
            except tk.TclError:
                pass  # Ignore if already gone
            self.drag_indicator_id = None
        try:
            if canvas.winfo_exists():
                canvas.config(cursor="")  # Reset cursor on the current canvas
        except tk.TclError:
            pass

        # --- Determine Item Type and Max Items based on Canvas ---
        # This is needed for both click and drag-release scenarios
        item_type = None
        max_items = 0
        source_canvas_type = None  # Track where drag started for potential validation

        if canvas == self.tileset_canvas:
            item_type = "tile"
            max_items = num_tiles_in_set
            source_canvas_type = "tile_editor_main"
        elif canvas == self.st_tileset_canvas:
            item_type = "tile"
            max_items = num_tiles_in_set
            source_canvas_type = "supertile_editor_tile"
        elif canvas == self.supertile_selector_canvas:
            item_type = "supertile"
            max_items = num_supertiles
            source_canvas_type = "supertile_editor_main"
        elif canvas == self.map_supertile_selector_canvas:
            item_type = "supertile"
            max_items = num_supertiles
            source_canvas_type = "map_editor_palette"
        else:
            # Should not happen if bindings are correct
            print(f"Warning: Drag release on unknown canvas: {canvas}")
            # Reset drag state fully and exit
            self.drag_active = False
            self.drag_item_type = None
            self.drag_start_index = -1
            self.drag_canvas = None
            return

        # --- Get Index Under Cursor ---
        index_at_release = self._get_index_from_canvas_coords(
            canvas, event.x, event.y, item_type
        )

        # --- Handle Release ---
        if not was_dragging:
            # --- Scenario 1: It was just a CLICK (no drag initiated or minimal movement) ---
            if 0 <= index_at_release < max_items:  # Ensure click was on a valid item
                # Perform the original selection logic based on the canvas type
                if item_type == "tile":
                    if (
                        source_canvas_type == "tile_editor_main"
                    ):  # Main tile editor viewer
                        if current_tile_index != index_at_release:
                            current_tile_index = index_at_release
                            self.update_all_displays(
                                changed_level="tile"
                            )  # Redraw editor, viewers
                            self.scroll_viewers_to_tile(
                                current_tile_index
                            )  # Scroll to selection
                    elif (
                        source_canvas_type == "supertile_editor_tile"
                    ):  # Supertile's tile selector
                        if selected_tile_for_supertile != index_at_release:
                            selected_tile_for_supertile = index_at_release
                            # Only redraw this specific viewer and label
                            self.draw_tileset_viewer(
                                self.st_tileset_canvas, selected_tile_for_supertile
                            )
                            self.update_supertile_info_labels()
                            self.scroll_viewers_to_tile(
                                selected_tile_for_supertile
                            )  # Scroll this viewer
                elif item_type == "supertile":
                    if (
                        source_canvas_type == "supertile_editor_main"
                    ):  # Main supertile selector
                        if current_supertile_index != index_at_release:
                            current_supertile_index = index_at_release
                            self.update_all_displays(changed_level="supertile")
                            self.scroll_selectors_to_supertile(
                                current_supertile_index
                            )  # Scroll
                    elif (
                        source_canvas_type == "map_editor_palette"
                    ):  # Map's supertile selector
                        if selected_supertile_for_map != index_at_release:
                            selected_supertile_for_map = index_at_release
                            # Only redraw this specific selector and label
                            self.draw_supertile_selector(
                                self.map_supertile_selector_canvas,
                                selected_supertile_for_map,
                            )
                            self.update_map_info_labels()
                            self.scroll_selectors_to_supertile(
                                selected_supertile_for_map
                            )  # Scroll

        else:
            # --- Scenario 2: It was a DRAG RELEASE ---
            source_index = self.drag_start_index
            dragged_item_type = self.drag_item_type  # Get type from drag state

            # Basic validation: Drag type must match release canvas type
            if dragged_item_type != item_type:
                print(
                    f"Warning: Drag type mismatch. Started '{dragged_item_type}', dropped on '{item_type}'. Cancelling."
                )
                # Redraw the source canvas to remove drag highlight
                if self.drag_canvas and self.drag_canvas.winfo_exists():
                    if dragged_item_type == "tile":
                        self.draw_tileset_viewer(
                            self.drag_canvas, -1
                        )  # Use dummy highlight index
                    elif dragged_item_type == "supertile":
                        self.draw_supertile_selector(self.drag_canvas, -1)
                # Reset state fully handled below
            else:
                # Determine the final target index for the repositioning logic
                # index_at_release == max_items means drop at the end
                # index_at_release == -2 means dropped outside valid grid area
                # index_at_release == -1 means error in calculation
                valid_drop_target = False
                final_target_index = -1

                if index_at_release == max_items:  # Drop at the very end
                    final_target_index = max_items  # Pass count to reposition logic
                    valid_drop_target = True
                elif 0 <= index_at_release < max_items:  # Drop onto a specific index
                    final_target_index = index_at_release
                    valid_drop_target = True

                if valid_drop_target and final_target_index != source_index:
                    # Proceed with repositioning
                    success = False
                    print(
                        f"Completing Drag: Moving {item_type} from {source_index} to target {final_target_index}"
                    )
                    if item_type == "tile":
                        success = self._reposition_tile(
                            source_index, final_target_index
                        )
                    elif item_type == "supertile":
                        success = self._reposition_supertile(
                            source_index, final_target_index
                        )

                    if success:
                        # Repositioning handles index updates and marking modified
                        # Need full redraw and cache clear due to potential cascading reference changes
                        self.clear_all_caches()
                        self.invalidate_minimap_background_cache()
                        self.update_all_displays(changed_level="all")
                        # Scroll viewers/selectors to the *new* location of the primary selection index
                        if item_type == "tile":
                            self.scroll_viewers_to_tile(current_tile_index)
                        elif item_type == "supertile":
                            self.scroll_selectors_to_supertile(current_supertile_index)
                    else:
                        # Repositioning failed (e.g., internal error, should be rare)
                        messagebox.showerror(
                            "Reposition Error",
                            f"Failed to move {item_type} from {source_index} to {final_target_index}.",
                        )
                        # Attempt redraw even on failure to show current state
                        self.update_all_displays(changed_level="all")

                else:
                    # Dropped outside (-2), on itself, or calculation error (-1)
                    # Just redraw the relevant displays to remove drag highlight
                    print(
                        f"Drag cancelled or no move needed (target_index: {index_at_release}, source: {source_index})."
                    )
                    if item_type == "tile":
                        self.update_all_displays(changed_level="tile")
                    elif item_type == "supertile":
                        self.update_all_displays(changed_level="supertile")

        # --- Final Reset of Drag State (regardless of click or drag) ---
        self.drag_active = False
        self.drag_item_type = None
        self.drag_start_index = -1
        self.drag_canvas = None
        # Indicator ID and cursor should already be cleaned up above

    def draw_tileset_viewer(self, canvas, highlighted_tile_index):
        """Draws tileset viewer, highlighting selected and optionally dragged tile."""
        # Check if drag is active and involves a tile from *any* tileset viewer
        is_dragging_tile = self.drag_active and self.drag_item_type == "tile"
        dragged_tile_index = self.drag_start_index if is_dragging_tile else -1

        try:
            canvas.delete("all")
            padding = 1
            size = VIEWER_TILE_SIZE
            max_rows = math.ceil(num_tiles_in_set / NUM_TILES_ACROSS)
            canvas_height = max(1, max_rows * (size + padding) + padding)  # Ensure > 0
            canvas_width = max(
                1, NUM_TILES_ACROSS * (size + padding) + padding
            )  # Ensure > 0
            str_scroll = f"0 0 {float(canvas_width)} {float(canvas_height)}"

            # Safely get current scroll region
            current_scroll = ""
            try:
                current_scroll_val = canvas.cget("scrollregion")
                if isinstance(current_scroll_val, tuple):
                    current_scroll = " ".join(map(str, current_scroll_val))
                else:
                    current_scroll = str(current_scroll_val)
            except tk.TclError:
                # Canvas might not be fully ready
                pass

            # Update scrollregion if needed
            if current_scroll != str_scroll:
                canvas.config(scrollregion=(0, 0, canvas_width, canvas_height))

            # Draw each tile
            for i in range(num_tiles_in_set):
                tile_r, tile_c = divmod(i, NUM_TILES_ACROSS)
                base_x = tile_c * (size + padding) + padding
                base_y = tile_r * (size + padding) + padding

                # Get cached image
                img = self.create_tile_image(i, size)
                canvas.create_image(
                    base_x,
                    base_y,
                    image=img,
                    anchor=tk.NW,
                    tags=(f"tile_img_{i}", "tile_image"),
                )

                # Determine outline style
                outline_color = "grey"  # Default
                outline_width = 1
                if i == dragged_tile_index:
                    # Highlight for the item being dragged takes precedence
                    outline_color = "yellow"
                    outline_width = 3
                elif i == highlighted_tile_index:
                    # Highlight for normal selection
                    outline_color = "red"
                    outline_width = 2

                # Draw the border rectangle
                # Use max(0, ...) for coords to prevent potential negative values if padding is odd?
                bx1 = max(0, base_x - padding / 2)
                by1 = max(0, base_y - padding / 2)
                bx2 = base_x + size + padding / 2
                by2 = base_y + size + padding / 2
                canvas.create_rectangle(
                    bx1,
                    by1,
                    bx2,
                    by2,
                    outline=outline_color,
                    width=outline_width,
                    tags=f"tile_border_{i}",
                )

        except tk.TclError as e:
            # Catch errors if the canvas is destroyed during redraw
            print(f"TclError during draw_tileset_viewer: {e}")
        except Exception as e:
            print(f"Unexpected error during draw_tileset_viewer: {e}")

    def _set_pencil_cursor(self, event):
        """Sets the cursor to 'pencil' for the widget that received the event."""
        try:
            # Check if widget still exists before configuring
            if event.widget.winfo_exists():
                event.widget.config(cursor="pencil")
        except tk.TclError:
            pass  # Ignore if widget is destroyed during event handling

    def _reset_cursor(self, event):
        """Resets the cursor to default for the widget that received the event."""
        try:
            if event.widget.winfo_exists():
                # Don't reset map canvas blindly, let its own logic handle it on leave
                if event.widget != self.map_canvas:
                    event.widget.config(cursor="")
                # If it *is* the map canvas, its existing <Leave> handler will take care of it
        except tk.TclError:
            pass  # Ignore if widget is destroyed

    # --- New Handlers and Helpers for Map Selection ---

    def handle_shift_press(self, event):
        """Handles Shift key press."""
        if "Shift" in event.keysym:
            if not self.is_shift_pressed:
                self.is_shift_pressed = True
                if self.current_mouse_action is None:
                    self._update_map_cursor()

    def handle_shift_release(self, event):
        """Handles Shift key release."""
        if "Shift" in event.keysym:
            if self.is_shift_pressed:
                self.is_shift_pressed = False
                if self.current_mouse_action is None:
                    self._update_map_cursor()

    def _get_supertile_coords_from_canvas(self, canvas_x, canvas_y):
        """Calculates supertile column and row from canvas coordinates.
        Returns (col, row) tuple if within map bounds, otherwise None.
        """
        zoomed_tile_size = self.get_zoomed_tile_size()
        if zoomed_tile_size <= 0:
            return None
        zoomed_supertile_size = SUPERTILE_GRID_DIM * zoomed_tile_size
        if zoomed_supertile_size <= 0:
            return None

        st_col = int(canvas_x // zoomed_supertile_size)
        st_row = int(canvas_y // zoomed_supertile_size)

        if 0 <= st_row < map_height and 0 <= st_col < map_width:
            return (st_col, st_row)
        else:
            return None

    def _get_normalized_selection_st(self):
        """Returns normalized selection bounds (min_c, min_r, max_c, max_r) or None."""
        if self.map_selection_start_st is None or self.map_selection_end_st is None:
            return None

        start_c, start_r = self.map_selection_start_st
        end_c, end_r = self.map_selection_end_st

        min_c = min(start_c, end_c)
        min_r = min(start_r, end_r)
        max_c = max(start_c, end_c)
        max_r = max(start_r, end_r)

        return (min_c, min_r, max_c, max_r)

    def _draw_selection_rectangle(self):
        """Draws or updates the visual selection rectangle based on start/end coords."""
        canvas = self.map_canvas
        if not canvas.winfo_exists():
            return

        if self.map_selection_rect_id:
            try:
                canvas.delete(self.map_selection_rect_id)
            except tk.TclError:
                pass
            self.map_selection_rect_id = None

        norm_coords = self._get_normalized_selection_st()
        if norm_coords is None:
            return

        min_c, min_r, max_c, max_r = norm_coords

        zoomed_tile_size = self.get_zoomed_tile_size()
        zoomed_supertile_size = SUPERTILE_GRID_DIM * zoomed_tile_size
        if zoomed_supertile_size <= 0:
            return

        px1 = min_c * zoomed_supertile_size
        py1 = min_r * zoomed_supertile_size
        px2 = (max_c + 1) * zoomed_supertile_size
        py2 = (max_r + 1) * zoomed_supertile_size

        self.map_selection_rect_id = canvas.create_rectangle(
            px1,
            py1,
            px2,
            py2,
            # Use a semi-transparent fill (stipple is an alternative)
            # fill="#FFFF00", # Yellow base color
            # stipple="gray25", # 25% transparency effect
            outline="yellow",  # Keep outline distinct
            dash=(4, 4),
            width=2,
            tags=("selection_rect",),
        )
        # Ensure it's drawn below other interactive elements like window view handles
        try:
            if canvas.find_withtag("window_view_item"):
                canvas.tag_lower(self.map_selection_rect_id, "window_view_item")
            elif canvas.find_withtag("supertile_grid"):  # Otherwise below grid
                canvas.tag_lower(self.map_selection_rect_id, "supertile_grid")
        except tk.TclError:
            pass

    def _clear_map_selection(self):
        """Clears ONLY the map selection visual and related state variables."""
        canvas = self.map_canvas
        # Clear the visual rectangle
        if self.map_selection_rect_id:
            try:
                if canvas.winfo_exists():
                    canvas.delete(self.map_selection_rect_id)
            except tk.TclError:
                pass
            self.map_selection_rect_id = None

        # Check if state needs updating before resetting (for menu update trigger)
        needs_menu_update = self.map_selection_start_st is not None

        # Reset selection state variables
        self.map_selection_start_st = None
        self.map_selection_end_st = None
        self.map_selection_active = False # Ensure selection drag state is reset

        # Update menu if selection was active
        if needs_menu_update:
            self._update_edit_menu_state()
        # Do not redraw map here, let the caller handle redraw if needed
        # Do not clear paste preview or clipboard here

    def handle_map_selection_start(self, event):
        """Handles Shift + Button-1 press to start map selection."""
        if self.is_ctrl_pressed or self.current_mouse_action is not None:
            return

        canvas = self.map_canvas
        canvas_x = canvas.canvasx(event.x)
        canvas_y = canvas.canvasy(event.y)

        self._clear_map_selection()

        start_coords = self._get_supertile_coords_from_canvas(canvas_x, canvas_y)

        if start_coords:
            self.map_selection_start_st = start_coords
            self.map_selection_end_st = start_coords
            self.map_selection_active = True
            self._draw_selection_rectangle()
            self._update_map_cursor()
        else:
            self.map_selection_start_st = None
            self.map_selection_end_st = None
            self.map_selection_active = False

        return "break"

    def handle_map_selection_motion(self, event):
        """Handles Shift + B1 motion to update selection rectangle."""
        if not self.map_selection_active:
            return

        canvas = self.map_canvas
        canvas_x = canvas.canvasx(event.x)
        canvas_y = canvas.canvasy(event.y)

        current_coords = self._get_supertile_coords_from_canvas(canvas_x, canvas_y)

        if current_coords:
            if self.map_selection_end_st != current_coords:
                self.map_selection_end_st = current_coords
                self._draw_selection_rectangle()
        # else: # Keep last valid end_st when mouse is outside

        return "break"

    def handle_map_selection_release(self, event):
        """Handles Shift + Button-1 release to finalize map selection."""
        if not self.map_selection_active:
            self._clear_map_selection()
            return

        self.map_selection_active = False

        if (
            self.map_selection_start_st is not None
            and self.map_selection_end_st is not None
        ):
            # print(f"Selection finalized: {self.map_selection_start_st} to {self.map_selection_end_st}")
            # Final rectangle drawn by motion handler, redraw map to make it persistent
            self.draw_map_canvas()
            self._update_edit_menu_state()
        else:
            self._clear_map_selection()

        self._update_map_cursor()

        return "break"

    def handle_map_escape(self, event):
        """Handles Escape key press on map canvas to clear clipboard, paste preview, and selection."""
        # print("Escape pressed, clearing clipboard, paste preview, and selection.")

        # Check what was active before clearing
        cleared_clipboard = self.map_clipboard_data is not None
        cleared_preview = self.map_paste_preview_rect_id is not None
        cleared_selection = self.map_selection_start_st is not None

        # Always attempt to clear clipboard, preview, and selection state
        self.map_clipboard_data = None
        self._clear_paste_preview_rect()
        self._clear_map_selection() # This now only clears selection visuals/state

        # Update menu state if the clipboard was cleared
        if cleared_clipboard:
            self._update_edit_menu_state()

        # Redraw map if the selection rectangle was visible to ensure it's removed
        # Clearing the paste preview doesn't require a full map redraw
        if cleared_selection and self.map_canvas.winfo_exists():
             self.draw_map_canvas()

        return "break" # Prevent other Escape bindings

    def _update_map_cursor_and_coords(self, event):
        """Combined handler for Motion to update both cursor and coords, and manage paste preview."""
        # Update coordinate display first
        self._update_map_coords_display(event)

        # Update cursor based on current state (e.g., pan, select, paint)
        self._update_map_cursor()

        # --- Paste Preview Logic ---
        is_map_tab_active = False
        if self.notebook and self.notebook.winfo_exists():
            try:
                 selected_tab_index = self.notebook.index(self.notebook.select())
                 if selected_tab_index == 3: # Map Editor tab index
                     is_map_tab_active = True
            except tk.TclError:
                pass # Ignore if notebook not ready

        # Conditions to show paste preview: Map tab active AND map clipboard has data
        if is_map_tab_active and self.map_clipboard_data:
            self._draw_paste_preview_rect(event=event)
        else:
            # Clear preview if conditions are not met (e.g., wrong tab, no clipboard data)
            # This handles cases where clipboard is cleared while mouse is over canvas
            self._clear_paste_preview_rect()

    # --- New Paste Preview Methods ---
    def _draw_paste_preview_rect(self, event=None, canvas_coords=None):
        """Draws the blue stippled paste preview rectangle."""
        canvas = self.map_canvas
        # Ensure required components exist and conditions are met
        if not canvas.winfo_exists() or not self.map_clipboard_data or not self.notebook:
            self._clear_paste_preview_rect() # Clear if conditions aren't met
            return
        try: # Check if map tab is active
            if self.notebook.index(self.notebook.select()) != 3: # 3 is Map Editor tab index
                 self._clear_paste_preview_rect()
                 return
        except tk.TclError:
            self._clear_paste_preview_rect()
            return # Notebook not ready or tab not found

        # Determine cursor position (either from event or passed coords)
        current_canvas_x, current_canvas_y = -1, -1
        if canvas_coords:
            current_canvas_x, current_canvas_y = canvas_coords
        elif event:
            try:
                current_canvas_x = canvas.canvasx(event.x)
                current_canvas_y = canvas.canvasy(event.y)
            except tk.TclError:
                self._clear_paste_preview_rect()
                return # Error getting coords
        else:
             self._clear_paste_preview_rect()
             return # No position provided

        # Get top-left supertile coordinates for the paste
        paste_st_coords = self._get_supertile_coords_from_canvas(current_canvas_x, current_canvas_y)

        # If cursor is outside map bounds, clear preview and exit
        if paste_st_coords is None:
            self._clear_paste_preview_rect()
            return

        paste_st_col, paste_st_row = paste_st_coords
        clip_w = self.map_clipboard_data.get('width', 0)
        clip_h = self.map_clipboard_data.get('height', 0)

        if clip_w <= 0 or clip_h <= 0:
            self._clear_paste_preview_rect() # Invalid clipboard data
            return

        # Calculate pixel bounds
        zoomed_tile_size = self.get_zoomed_tile_size()
        zoomed_supertile_size = SUPERTILE_GRID_DIM * zoomed_tile_size
        if zoomed_supertile_size <= 0:
             self._clear_paste_preview_rect()
             return

        px1 = paste_st_col * zoomed_supertile_size
        py1 = paste_st_row * zoomed_supertile_size
        px2 = px1 + (clip_w * zoomed_supertile_size)
        py2 = py1 + (clip_h * zoomed_supertile_size)

        # Draw or update the rectangle
        fill_color = "#0000FF" # Blue base
        stipple_pattern = "gray50" # Simulate transparency

        if self.map_paste_preview_rect_id:
            try:
                # Update coordinates and ensure it's visible and styled correctly
                canvas.coords(self.map_paste_preview_rect_id, px1, py1, px2, py2)
                canvas.itemconfig(self.map_paste_preview_rect_id, state=tk.NORMAL, fill=fill_color, stipple=stipple_pattern)
            except tk.TclError:
                self.map_paste_preview_rect_id = None # ID invalid, force redraw below
        # If no existing ID or it was invalid, create it
        if not self.map_paste_preview_rect_id:
            try:
                self.map_paste_preview_rect_id = canvas.create_rectangle(
                    px1, py1, px2, py2,
                    fill=fill_color,
                    stipple=stipple_pattern,
                    outline="", # No outline for the mask itself
                    width=0,
                    tags=("paste_preview_rect",) # Add tag for identification
                )
            except tk.TclError:
                 self.map_paste_preview_rect_id = None # Creation failed
                 return # Exit if creation failed

        # Ensure preview is drawn below selection and window view items
        try:
            # Lower below selection rect if it exists
            if self.map_selection_rect_id:
                 canvas.tag_lower(self.map_paste_preview_rect_id, self.map_selection_rect_id)
            # Then lower below window view items if they exist
            if canvas.find_withtag("window_view_item"):
                canvas.tag_lower(self.map_paste_preview_rect_id, "window_view_item")
            # Otherwise, lower below grid if it exists
            elif canvas.find_withtag("supertile_grid"):
                 canvas.tag_lower(self.map_paste_preview_rect_id, "supertile_grid")
        except tk.TclError:
            pass # Ignore tag errors if items don't exist


    def _clear_paste_preview_rect(self):
        """Safely deletes the paste preview rectangle from the canvas."""
        canvas = self.map_canvas
        if self.map_paste_preview_rect_id:
            try:
                if canvas.winfo_exists():
                    canvas.delete(self.map_paste_preview_rect_id)
            except tk.TclError:
                pass # Ignore error if item already deleted or canvas gone
            finally:
                 # Ensure ID is cleared even if deletion fails
                 self.map_paste_preview_rect_id = None

    def show_about_box(self):
        """Displays the About information box."""
        messagebox.showinfo(
            "About MSX2 Tile Forge",
            "MSX2 Tile/Map/Palette Editor\n\nVersion: 0.9\nAuthor: Damned Angel (+ Google Gemini)"
        )

# --- Main Execution ---
if __name__ == "__main__":
    root = tk.Tk()
    app = TileEditorApp(root)
    root.mainloop()
