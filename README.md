# MSX Tile Forge
v1.0.0RC15

An integrated Palette, Tile, Supertile and Map Editor for MSX, built with Python and Tkinter.

## Introduction

MSX Tile Forge is a desktop application created to assist in the development of graphical assets for MSX2 computers and similar retro systems that utilize tile-based graphics and have specific palette limitations. It provides an integrated environment for designing 16-color palettes, creating 8x8 pixel tiles with row-specific colors, composing supertiles (e.g., 4x4, but dimensions are project-configurable) from these tiles, and arranging them into larger game maps. The tool aims to streamline the asset creation workflow for retro game developers, specially for MSX.

All project components (palette, tiles, supertiles, map) can be saved and loaded individually or as a complete project, using custom binary file formats designed for ease of use and integration into MSX development pipelines.

## Features

*   **Palette Editor:**
    *   Manage a 16-color active MSX2 palette.
    *   Select colors from a 512-color MSX2 visual picker or by direct RGB (0-7 per channel) input.
    *   **Advanced Drag-and-Drop:**
        *   **Swap (LMB Drag):** Drag a color slot and drop it onto another to swap their positions and all color references throughout the tileset.
        *   **Replace All (Alt+LMB Drop):** Hold `ALT` while dropping a source color onto a target color to replace all uses of the target color with the source color across the entire project. A visual confirmation dialog will appear.
    *   **Interactive Info Panel:** The "Used in..." label is a clickable link that will highlight all tiles using the selected color and switch to the Tile Editor tab.
    *   Save/Load custom `.SC4Pal` palette files.
    *   Reset to the standard MSX2 default palette.

*   **Tile Editor (8x8 pixels):**
    *   Pixel-level drawing with selectable foreground/background colors.
    *   Assign unique foreground and background palette indices to each of the 8 rows within a tile.
    *   Tileset viewer (up to 256 tiles) with selection and advanced drag-and-drop.
    *   **Advanced Drag-and-Drop:**
        *   **Move (LMB Drag):** Reorder tiles by dragging and dropping.
        *   **Swap (Ctrl+LMB Drop):** Hold `CTRL` while dropping a tile onto another to swap their positions and all references.
        *   **Replace All (Alt+LMB Drop):** Hold `ALT` while dropping a source tile onto a target tile to replace all uses of the target tile with the source tile across all supertile definitions.
    *   Operations: Add New, Add Many..., Insert, Delete tiles.
    *   Transformations: Flip Horizontal/Vertical, Rotate 90° CW (colors reset for rows), Shift Up/Down/Left/Right.
    *   Copy/Paste functionality for tile patterns and row colors.
    *   "Mark Unused" feature to highlight tiles not referenced in any supertile.
    *   **Interactive Info Panel:** The "Used...in...supertiles" label is a clickable link that highlights all supertiles using the selected tile and switches to the Supertile Editor tab.
    *   **Deep Dive Editing (Double-Click):** Double-clicking a color in the "Color Selector Palette" will jump to the main Palette Editor tab with that color selected.
    *   Save/Load tilesets as `.SC4Tiles` binary files.

*   **Supertile Editor (Project-Configurable Dimensions, e.g., 2x2, 4x4, 8x2 tiles):**
    *   Define supertiles by arranging existing tiles in a grid of **user-defined width and height** (1-32 tiles per dimension, set per project).
    *   Tileset viewer for selecting component tiles from the current tileset.
    *   Supertile selector (up to 65535 supertiles) with selection and advanced drag-and-drop.
    *   **Advanced Drag-and-Drop:**
        *   **Move (LMB Drag):** Reorder supertiles by dragging and dropping.
        *   **Swap (Ctrl+LMB Drop):** Hold `CTRL` while dropping a supertile onto another to swap their positions and all references.
        *   **Replace All (Alt+LMB Drop):** Hold `ALT` while dropping a source supertile onto a target supertile to replace all uses of the target supertile with the source supertile across the entire map.
    *   Operations: Add New, Add Many..., Insert, Delete supertiles.
    *   Transformations: Flip Horizontal/Vertical, Rotate 90° CW (**enabled only for square supertiles**), Shift Up/Down/Left/Right for the supertile definition.
    *   Copy/Paste functionality for supertile definitions.
    *   "Mark Unused" feature: Highlights unused supertiles (not used on the map) and also re-highlights unused base tiles (not used in any supertile definition) within this tab's context.
    *   **Interactive Info Panels:** The "Used on Map" label is a clickable link that highlights all map locations using the selected supertile and switches to the Map Editor tab. The global tile usage label is also clickable.
    *   **Deep Dive Editing (Double-Click):**
        *   Double-clicking a tile in the **Definition Canvas** will jump to the main Tile Editor tab with that tile selected for editing.
        *   Double-clicking a tile in the **Tileset Viewer** will also jump to the Tile Editor tab with that tile selected.
    *   Save/Load supertile definitions as `.SC4Super` binary files (these files store the supertile dimensions).

*   **Map Editor:**
    *   Construct maps by placing supertiles on a grid (default 32x24 supertiles, dimensions configurable up to 1024x1024 supertiles per project).
    *   Supertile palette for selecting supertiles (from the current project's supertile set) to paint onto the map.
    *   Zoomable (Ctrl+MouseWheel or buttons) and pannable (Ctrl+LMB Drag) map canvas.
    *   Optional supertile grid overlay with cyclable colors (toggled by 'Show Supertile Grid' checkbox; 'G' key cycles colors when map tab is active).
    *   "Window View" overlay:
        *   Visualizes a screen-like boundary on the map.
        *   Dimensions configurable in 8x8 base tiles (Width: 1-32, Height: 1-27). Max height of 27 accommodates MSX half-tile overscan concepts.
        *   Draggable on the map canvas (when not holding Ctrl).
        *   Resizable via its handles.
        *   Can be nudged one tile at a time using WASD keys when the Window View is active and the map canvas has focus.
    *   Resizable Minimap window (toggled via View menu or Ctrl+M):
        *   Displays a scaled-down overview of the entire map.
        *   Shows a red rectangle indicating the main Map Canvas's current viewport.
        *   Shows a dashed blue rectangle indicating the "Window View" overlay's position and size, if active.
        *   Maintains the map's aspect ratio when resized by the user.
    *   Map region selection using Shift+LMB Drag for Copy/Paste operations within the map.
    *   Eyedropper functionality (Right-Click on map) to select the supertile under the cursor and make it active in the Supertile Palette.
    *   "ST Coords" display the supertile coordinates under the mouse.
    *   Paste Preview: When map data is on the clipboard, a semi-transparent preview of the paste area follows the mouse cursor.
    *   **Deep Dive Editing (Double-Click):**
        *   Double-clicking a supertile on the **Map Canvas** will jump to the Supertile Editor tab with that supertile selected for editing.
        *   Double-clicking a supertile in the **Supertile Palette** will also jump to the Supertile Editor tab with that supertile selected.
    *   Save/Load maps as `.SC4Map` binary files.

*   **Usage Analysis Windows (View Menu):**
    *   **Color Usage (F1):** A sortable list showing how many times each of the 16 palette colors is used. **Clicking a usage count** will highlight all tiles that use that color.
    *   **Tile Usage (F2):** A sortable list showing how many times each tile is used within all supertile definitions. **Clicking a usage count** will highlight all supertiles that use that tile.
    *   **Supertile Usage (F3):** A sortable list showing how many times each supertile is used on the map, with a lazy-loading preview. **Clicking a usage count** will highlight all map locations where that supertile is used.

*   **Import Features:**
    *   **ROM Importer (`Import -> Import Tiles from ROM...`):** Imports 8x8 tile data directly from ROM files. Features a visual browser, live preview, advanced multi-selection (Click, Shift+Click, Ctrl+Click, Ctrl+Shift+Click), base colors control, and a fine tile start offset control.
        *   **Per-Selection Properties:** For each selected tile (or group), the fine offset and FG/BG colors are captured and used for both previewing and the final import.
    *   **Image Importer (`Import -> Import Tiles from Image...`):** Creates a new tileset and palette by analyzing a standard image file (PNG, BMP, etc.). This powerful feature replaces the current tileset and palette. Options include:
        *   Using the current active palette or generating a new optimized 16-color palette from the image.
        *   Enabling dithering for color reduction.
        *   Ignoring and skipping duplicate tiles found in the source image.

*   **Project Management & UX:**
    *   Projects bundle all asset types: palettes, tilesets, supertiles and maps.
    *   Ability to save and load individual asset components (palette, tileset, supertiles, map) separately.
    *   **Automatic Startup:** The application remembers and automatically re-opens the last used project on startup. If it can't be found, a new blank project is created.
    *   Automatic tracking of unsaved changes within a project, with prompts to prevent data loss.
    *   **Recent Files Menu:** Remembers recently opened projects and individual module files.
        *   Use `Ctrl+R` / `Alt+R` to pop up the menus at the cursor.
        *   Use `Ctrl+1`..`0` / `Alt+1`..`0` to directly open recent items.
    *   **Persistent Window State:** The size and position of the main window, Usage windows, and editor sash dividers are saved and restored between sessions.

## Getting Started

This section explains how to set up your system and run MSX Tile Forge, including the dependencies required for its advanced import/export features.

### System Requirements & Dependencies

To run MSX Tile Forge and use all its features, your system will need the following:

*   **Python:**
    *   Version 3.x is required. The application has been primarily developed and tested with Python 3.12, but it is expected to be compatible with other recent Python 3 releases (e.g., Python 3.7 and newer).
    *   Ensure Python 3 is installed on your system and that the `python` (or `python3` on some systems) command is accessible from your command line or terminal.

*   **Tkinter (GUI Library):**
    *   Tkinter is Python's standard GUI (Graphical User Interface) package and is essential for the application's interface.
    *   It is typically included with most Python installations on Windows, macOS, and Linux.
    *   On some Linux distributions, Tkinter (often named `python3-tk` or similar) might need to be installed separately via the system's package manager if it wasn't included in a minimal Python installation. For example, on Debian/Ubuntu-based systems, you can install it by running:
        ```bash
        sudo apt-get update
        sudo apt-get install python3-tk
        ```

*   **Required Python Libraries:**
    These libraries provide the core functionality for image processing, numerical operations, and advanced algorithms used by the application and its integrated scripts. You can install them all at once using pip. Open your terminal or command prompt and execute:
    ```bash
    pip install Pillow numpy scipy platformdirs tqdm
    ```
    *   **Pillow:** The Python Imaging Library Fork is required for all image processing tasks.
    *   **NumPy:** A fundamental package for scientific computing, used by the import scripts for efficient array manipulation.
    *   **SciPy:** This library provides scientific algorithms. It is specifically used for the "Hungarian algorithm" (`linear_sum_assignment`) to perform optimal color and tile remapping during paste operations.
    *   **platformdirs:** Used to find the correct user-specific directory for saving application settings (`settings.json`).
    *   **tqdm:** Used by the `MSX Tile Magic` script to display progress bars in the console, which are streamed to the application's process runner window.

*   **Optional `colour-science` Library (for advanced color accuracy):**
    *   For the highest quality color palette generation and analysis, MSX Tile Forge can use the `colour-science` library. This enables the "CIE76" and "CIEDE2000" color difference metrics, which are based on human perceptual models.
    *   This dependency is optional. If it is not installed, the application will default to its high-quality `weighted-rgb` metric.
    *   To install it for advanced use, run:
        ```bash
        pip install colour-science
        ```

### Installing the Application

Download or [clone](https://github.com/DamnedAngel/msx-tile-forge.git) the [msxtileforge.py](https://github.com/DamnedAngel/msx-tile-forge/blob/master/msxtileforge.py) script and its required companion script [msxtilemagic.py](https://github.com/DamnedAngel/msx-tile-forge/blob/master/msxtilemagic.py). **Both files must be in the same directory for the application to function correctly.**

Also, you can download an install package from [GitHub releases](https://github.com/DamnedAngel/msx-tile-forge/releases) assets area.

*   **Linux**
    * Install via debian package (.deb) or download the correspondent binary asset (msxtileforge-*-linux-x64-bin.zip).
 
*   **Windows**
    * Download the correspondent binary asset (msxtileforge-*-windows-x64-bin.zip).

*   **MacOS**
    * Download the correspondent binary asset (msxtileforge-*-mac-x86_64-bin.zip).

### Running the Application

1.  **Ensure Dependencies are Installed:**
    Verify that Python 3 and all the required Python libraries listed above are installed.

2.  **Obtain the Scripts:**
    Download or [clone](https://github.com/DamnedAngel/msx-tile-forge.git) the [msxtileforge.py](https://github.com/DamnedAngel/msx-tile-forge/blob/master/msxtileforge.py) script and its required companion script [msxtilemagic.py](https://github.com/DamnedAngel/msx-tile-forge/blob/master/msxtilemagic.py). **Both files must be in the same directory for the application to function correctly.**

3.  **Navigate to the Scripts' Directory:**
    Open your command line interface (Terminal, Command Prompt, PowerShell, etc.) and navigate to the directory where you saved the `.py` files.
    ```bash
    cd path/to/your/msx-tile-forge-directory
    ```

4.  **Execute the Script:**
    Run the main application using the Python interpreter:
    ```bash
    python msxtileforge.py
    ```
    *   On some systems, particularly Linux or macOS where Python 2 might also be present, you may need to use `python3` explicitly:
        ```bash
        python3 msxtileforge.py
        ```

5.  **Optional Debug Mode:**
    To launch the application with detailed diagnostic messages printed to the console (useful for troubleshooting or development), use the `--debug` flag:
    ```bash
    python msxtileforge.py --debug
    ```

Upon successful execution, the MSX Tile Forge application window should appear after a brief splash screen.

## Manual

This manual provides an overview of MSX Tile Forge's functionalities, organized by its main interface components.

### Global Operations (Menu Bar & General UX)

The main menu bar provides access to project-wide operations and settings.

*   **File Menu:**
    *   **Project Management:**
        *   `New Project (Ctrl+N)`: Starts a new project, prompting for supertile dimensions. Clears all current data (palette, tiles, supertiles, map).
        *   `Open Project... (Ctrl+O)`: Loads an existing project. Select any of its four component files (`.SC4Pal`, `.SC4Tiles`, `.SC4Super`, `.SC4Map`); the application loads all associated files. Supertile dimensions are restored from the `.SC4Super` file.
        *   `Save Project (Ctrl+S)`: Saves all four components of the current project. If unsaved, acts like "Save Project As...".
        *   `Save Project As... (Ctrl+Shift+S)`: Saves all four project components under a new base name and location chosen by the user.
    *   **Individual File Operations:** Allows loading or saving specific asset types independently:
        *   Palette (`.SC4Pal`)
        *   Tileset (`.SC4Tiles`)
        *   Supertiles (`.SC4Super`)
        *   Map (`.SC4Map`)
    *   **Recent Projects / Modules:** Quick access to recently opened project files or individual component files (`Ctrl+R` / `Alt+R`).
    *   **Exit (Ctrl+Q):** Closes the application. Prompts to save if there are unsaved changes to the current project.

*   **Edit Menu:**
    *   **Copy/Paste (Ctrl+C / Ctrl+V):** Context-sensitive actions.
        *   **Tile Editor:** Copies/pastes the current tile's pattern and row colors.
        *   **Supertile Editor:** Copies/pastes the current supertile's definition.
        *   **Map Editor:** Copies/pastes a selected rectangular region of supertiles on the map.
    *   **Clear Operations:**
        *   `Clear Current Tile`: Resets the selected tile's pattern and row colors to default.
        *   `Clear Current Supertile`: Resets the selected supertile's definition to all tile 0s.
        *   `Clear Map`: Resets all cells in the current map to supertile 0.
    *   **Set Data Dimensions:**
        *   `Set Map Dimensions...`: Changes the map's width and height in supertile units (1-1024 per side).

*   **View Menu:**
    *   `Show/Hide Minimap (Ctrl+M)`: Toggles the resizable Minimap window for the Map Editor.
    *   `Color Usage (F1)`, `Tile Usage (F2)`, `Supertile Usage (F3)`: Toggles the visibility of the respective usage analysis windows.

*   **Import Menu:**
    *   `Append Tileset from File...`: Appends tiles from another project's `.SC4Tiles` file to the current tileset.
    *   `Append Supertiles from File...`: Appends supertiles and their associated tiles from another project's `.SC4Super` and `.SC4Tiles` files.
    *   `Import Tiles from ROM...`: Opens the ROM Importer dialog to extract tile data from external binary files.
    *   `Import Tiles from Image...`: Opens the Image Importer to create a new tileset and palette from a standard image file.

*   **Help Menu:**
    *   `About...`: Displays application information (version, author).

*   **General User Experience:**
    *   **Unsaved Changes:** The window title is marked with an asterisk (*) if the project has unsaved modifications. Prompts to save are given before closing, opening, or creating new projects if changes are pending.
    *   **Deep Dive Editing (Double-Click):** Double-clicking an item (like a tile on a supertile canvas, or a supertile on the map) will automatically switch to that item's editor tab and select it. This allows for rapid, intuitive navigation between asset levels.
    *   **Drag-and-Drop Operations:**
        *   **Move (LMB Drag):** Reorder items by dragging and dropping.
        *   **Swap (Ctrl+Drop):** Hold `CTRL` while dropping an item onto another to swap their positions and update all data references.
        *   **Replace All (Alt+Drop):** Hold `ALT` while dropping a source item onto a target to replace all uses of the target item with the source item project-wide.
    *   **Persistent Window State:** The size/position of the main window and all utility windows, as well as the position of editor dividers (sashes), are saved and restored between sessions.

### 1. Palette Editor Tab

This tab is dedicated to managing the 16-color active palette used for all graphics.

*   **Active Palette Display:** A 4x4 grid shows the 16 colors. Click a slot to select it for modification (highlighted red).
*   **Selected Slot Information:** Shows the selected slot's index, a color preview, its hexadecimal RGB value, its MSX2-specific RGB values (0-7 per channel), and a count of how many times it's used. The usage count is a **clickable link** to find all tiles using that color.
*   **Color Modification:**
    *   **MSX2 512 Color Picker:** A large grid displaying all 512 possible MSX2 colors. Clicking a color here applies it to the selected active palette slot.
    *   **Set Color (RGB 0-7):** Input R, G, B values (0-7 each) and click "Set" to apply them to the selected slot.
*   **Reset Palette:** A button to revert the active 16-color palette to the standard MSX2 hardware default colors.

### 2. Tile Editor Tab

Used for creating and editing individual 8x8 pixel base tiles.

*   **Tile Editing Area (Left):**
    *   **Editor Canvas:** An 8x8 magnified grid for pixel drawing.
        *   Left-Click: Draws a foreground pixel (marks as '1').
        *   Right-Click: Draws a background pixel (marks as '0').
        *   Uses the color selected in the "Color Selector Palette".
    *   **Row Colors Attributes:** Adjacent to the editor canvas, displays 8 pairs of FG and BG color swatches. Click a swatch to assign the currently selected color as that row's FG or BG palette index.
    *   **Selected Tile Info:** A panel showing a preview of the selected tile and its usage counts. The usage count is a **clickable link** to find all supertiles using that tile.
    *   **Transformations:** Buttons for the currently edited tile: Flip Horizontal/Vertical, Rotate 90° Clockwise (resets row colors), Shift (Up, Down, Left, Right).
    *   **Mark Unused:** Highlights tiles in the viewer not used in any supertile.

*   **Tileset Management (Right):**
    *   **Color Selector Palette:** A 4x4 grid of the 16 active palette colors. Click to choose the active color for drawing. Double-click a color to jump to the Palette Editor tab.
    *   **Tileset Viewer:** Displays all tiles in the project (up to 256). Click to select a tile; drag-and-drop for advanced operations (Move/Swap/Replace).
    *   **Tile Operations:** Buttons for "Add New", "Add Many...", "Insert", "Delete" tiles.
    *   **Info Label:** Shows total number of tiles in the set.

### 3. Supertile Editor Tab

For creating composite "supertiles" from base tiles. Supertile grid dimensions (e.g., 4x4, 2x8 tiles) are defined per-project.

*   **Supertile Definition Area (Left):**
    *   **Definition Canvas:** A grid matching the project's supertile dimensions.
        *   Left-Click a cell: Places the currently selected tile.
        *   **Double-Click a cell: Jumps to the Tile Editor to edit that specific tile.**
        *   Right-Click a cell (Eyedropper): Selects the tile within that cell, making it active.
    *   **Information Panels:** Show detailed info for the selected tile and the selected supertile. The usage count labels are **clickable links**.
    *   **Transformations:** Buttons for the current supertile definition: Flip Horizontal/Vertical, Rotate 90° Clockwise (enabled for square supertiles), Shift (Up, Down, Left, Right).
    *   **Mark Unused:** Highlights unused supertiles (not on map) and unused base tiles.

*   **Asset Selection (Right):**
    *   **Tileset Viewer:** Displays all base tiles. Click to select a tile for placing. Double-click a tile to jump to the Tile Editor.
    *   **Supertile Selector:** A resizable panel displaying all supertiles in the project (up to 65535). Click to select a supertile for editing; drag-and-drop for advanced operations (Move/Swap/Replace).
    *   **Supertile Operations:** Buttons for "Add New", "Add Many...", "Insert", "Delete" supertiles.

### 4. Map Editor Tab

For arranging supertiles to construct game maps.

*   **Main Map Area (Left):**
    *   **Controls Bar:** Displays map dimensions, zoom level, and provides controls for the grid and "Window View" overlay.
    *   **Map Canvas:** The main drawing area for the map.
        *   **Painting (LMB):** Places the selected supertile.
        *   **Deep Dive (Double-Click): Jumps to the Supertile Editor to edit the supertile under the cursor.**
        *   **Eyedropper (RMB):** Selects the supertile under the cursor.
        *   **Navigation:** Pan with Ctrl+LMB Drag; Zoom with Ctrl+MouseWheel.
        *   **Region Selection (Shift+LMB Drag):** Selects a rectangular area for copy/paste.
        *   **Window View Nudge (WASD Keys):** Moves the "Window View" overlay.
        *   **Clear Selection/Clipboard (Escape Key):** Deselects map region and clears map clipboard/preview.
    *   **Window View Overlay (if active):** A draggable and resizable rectangle representing a screen area.

*   **Supertile Selection (Right):**
    *   **Supertile Palette:** A resizable panel displaying all supertiles in the project. Click to select a supertile for painting; drag-and-drop for advanced operations (Move/Swap/Replace). Double-click a supertile to jump to the Supertile Editor.

*   **Minimap Window (View Menu or Ctrl+M):**
    *   A separate, resizable window providing an overview of the entire map.
    *   Displays the main Map Canvas's current viewport (red rectangle) and the "Window View" overlay's position/size (dashed blue rectangle).

### 5. Importing Tiles from ROM

This feature (accessible via `Import -> Import Tiles from ROM...`) allows loading an external binary file to extract 8x8 pixel, 1bpp tile data and add it to the current project's tileset.

**Importer Dialog Features:**
*   **Live Preview:** Magnified view of the tile currently under the mouse cursor.
*   **Fine Offset Slider:** Adjusts the global default starting byte offset (0-7 bytes) for interpreting tile data.
*   **Preview/Import Colors:** Two clickable swatches (FG/BG) allow choosing colors from the main palette.
*   **ROM Tile Grid:** Shows ROM data interpreted as a sequence of tiles.
*   **Multi-Selection in Grid:**
    *   **Click (LMB):** Selects a single tile.
    *   **Shift + Click (LMB):** Selects a range of tiles.
    *   **Ctrl + Click (LMB):** Toggles selection of a single tile.
    *   **Ctrl + Shift + Click (LMB):** Adds a range to the existing selection.
    *   **Right-Click / Escape Key:** Clears current selection.
*   **Importing:** The "Import" button appends selected tiles to the project's tileset. Each imported tile's row colors are set using the offset and FG/BG palette indices stored with it at its time of selection in the importer.

## Technical Description of Generated Files

All project assets are saved in custom binary file formats. Multi-byte numerical values are stored in **Big-Endian** format.

**File Format Versioning Note:**
Project component files (`.SC4Pal`, `.SC4Tiles`, `.SC4Super`, `.SC4Map`) now include **4 reserved bytes** immediately following their primary header information. The application can still open older files that do not have these reserved bytes.

### 1. Palette File (`.SC4Pal`)

*   **Purpose:** Stores the 16-color active MSX2 palette.
*   **Structure:**
    *   **Reserved Bytes (4 bytes):** For future use.
    *   **Color Data (48 bytes total):** A sequence of 16 color entries (3 bytes each: R, G, B, values 0-7).

### 2. Tileset File (`.SC4Tiles`)

*   **Purpose:** Stores definitions for 8x8 pixel tiles.
*   **Structure:**
    *   **Header (1 byte):** `num_tiles_in_file`. A value of `0` indicates 256 tiles.
    *   **Reserved Bytes (4 bytes):** For future use.
    *   **All Pattern Data Block (Total: `num_tiles` \* 8 bytes):** Pattern data for all tiles, stored consecutively. Each tile is 8 bytes (1 byte per row).
    *   **All Color Attribute Data Block (Total: `num_tiles` \* 8 bytes):** Color attribute data for all tiles, stored consecutively. Each tile is 8 bytes (1 byte per row). High nibble is FG index, low nibble is BG index.

### 3. Supertile Definition File (`.SC4Super`)

*   **Purpose:** Stores supertile definitions and their grid dimensions.
*   **Structure:**
    *   **Supertile Count (1 or 3 bytes):** If the first byte is `1-255`, it's the count. If `0`, the next 2 bytes are the count (up to 65535).
    *   **Supertile Grid Dimensions (2 bytes):** `width` (1 byte), `height` (1 byte).
    *   **Reserved Bytes (4 bytes):** For future use.
    *   **Supertile Definition Blocks:** Each block is `width * height` bytes, with each byte being a tile index (0-255).

### 4. Map File (`.SC4Map`)

*   **Purpose:** Stores the overall map layout.
*   **Structure:**
    *   **Header (4 bytes):** `map_width` (2 bytes), `map_height` (2 bytes).
    *   **Reserved Bytes (4 bytes):** For future use.
    *   **Map Data (Variable size):** A sequence of `map_width * map_height` supertile indices.
        *   **Index Size:** If the project's total supertile count was > 255 at save time, each index is **2 bytes**. Otherwise, each index is **1 byte**. The application detects this based on file size.

## Contributing

Contributions to MSX Tile Forge are welcome! If you have bug reports, feature suggestions, or would like to contribute code:

1.  **Issues:** Please feel free to open an issue on the project's GitHub repository to discuss bugs or propose new features.
2.  **Pull Requests:** For code contributions, please fork the repository, make your changes in a separate branch, and then submit a pull request for review.

Clear descriptions and, where applicable, steps to reproduce issues are greatly appreciated.

## License

This project is licensed under the **GNU Affero General Public License v3.0 (AGPL-3.0)**.

The full text of the license should be included with the software (typically in a `LICENSE` or `COPYING` file). It can also be found online at:
[https://www.gnu.org/licenses/agpl-3.0.en.html](https://www.gnu.org/licenses/agpl-3.0.en.html)