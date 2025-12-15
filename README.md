# MSX Tile Forge

[![Latest Release](https://img.shields.io/github/v/release/DamnedAngel/msx-tile-forge?include_prereleases&label=Latest%20Release&color=blue)](https://github.com/DamnedAngel/msx-tile-forge/releases/latest)
[![Nightly Build Status](https://github.com/DamnedAngel/msx-tile-forge/actions/workflows/nightly-build.yml/badge.svg)](https://github.com/DamnedAngel/msx-tile-forge/actions/workflows/nightly-build.yml)

An integrated Palette, Tile, Supertile and Map Editor for MSX, built with Python and Tkinter.

## Introduction

MSX Tile Forge is a desktop application created to assist in the development of graphical assets for MSX2 computers and similar retro systems that utilize tile-based graphics and have specific palette limitations. It provides an integrated environment for designing 16-color palettes, creating 8x8 pixel tiles with row-specific colors, composing supertiles (e.g., 4x4, but dimensions are project-configurable) from these tiles, and arranging them into larger game maps. The tool aims to streamline the asset creation workflow for retro game developers, specially for MSX.

All project components (palette, tiles, supertiles, map) can be saved and loaded individually or as a complete project, using custom binary file formats designed for ease of use and integration into MSX development pipelines.

## Downloads

You can download pre-compiled, ready-to-run versions of MSX Tile Forge for various operating systems.

*   **Latest Official Release & Release Candidates:** For the most stable versions (yet to be populated), please visit the **[Releases Page](https://github.com/DamnedAngel/msx-tile-forge/releases)**. (Note: The first official release is coming soon!)

*   **Nightly Builds:** For the latest "bleeding-edge" features and fixes, you can download a build from the most recent successful nightly run. These builds are generated automatically and are not guaranteed to be stable, but they represent the most up-to-date version of the software.
    *   **[Browse All Nightly Builds on the Internet Archive](https://archive.org/search.php?query=subject%3A"msxtileforge_nightly_build"&sort=-addeddate)**

*   **Source Code:** If you prefer to run the application from source, you can download the latest source archive from the [Releases Page](https://github.com/DamnedAngel/msx-tile-forge/releases) or clone the repository directly. This is a much smaller download, but it requires you to set up your own Python environment as described in the [Running from Source Code](#running-from-source-code) section.

## Features

*   **Palette Editor:**
    *   Manage a 16-color active MSX2 palette.
    *   Select colors from a 512-color MSX2 visual picker or by direct RGB (0-7 per channel) input.
    *   **Consolidated Color Editor Panel:**
        *   Features linked 9-bit (MSX, 0-7) and 24-bit (Standard RGB, 0-255) inputs.
        *   Changes in one format instantly update the other in real-time.
        *   Live preview swatches show the user-defined 24-bit color and the closest resulting 9-bit MSX2 color.
    *   **Informative Tooltips:** Hover over any color in the Active Palette or the 512 Color Picker to see a tooltip with its slot/index and both 9-bit and 24-bit RGB values.
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
    *   Define supertiles by arranging existing tiles in a grid. The **grid dimensions (width and height, 1-32 tiles each) are set per-project** when you create a new project via `File -> New Project`.
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
    *   **Color Usage (F1):** A sortable list showing how many times each of the 16 palette colors is used. **Clicking on a data cell** for a used color will highlight all tiles that use that color.
    *   **Tile Usage (F2):** A sortable list showing how many times each tile is used within all supertile definitions. **Clicking on a data cell** for a used tile will highlight all supertiles that use that tile.
    *   **Supertile Usage (F3):** A sortable list showing how many times each supertile is used on the map, with a lazy-loading preview. **Clicking on a data cell** for a used supertile will highlight all map locations where that supertile is used.

*   **Import / Export Features:**
    *   **Create Project from Image (`Import/Export -> Create Project from Image...`):** A powerful tool to generate a complete new project from a single image file. This feature **replaces the entire current project** and uses an external script (`msxtilemagic.py`) to perform advanced analysis. The import dialog provides extensive control over the conversion process:
        *   **Palette Constraints:** Lock, block, or automatically select each of the 16 palette slots to guide the color generation.
        *   **Optimization:** Choose between quality modes (`sharp`, `balanced`, `soft`) to influence color reduction and tile matching.
        *   **Configurable Dimensions:** Set the desired Supertile width and height for the generated project.
        *   **Advanced Options:** Enable dithering, find the best 8x8 grid offset in the source image, and synthesize new tiles to represent merged tile groups for better visual fidelity.
        *   **Color Metrics:** For advanced users, select the color difference algorithm used for analysis (including `CIE76` and `CIEDE2000` if the `colour-science` library is installed).

    *   **Import Tiles from Image (`Import/Export -> Import Tiles from Image...`):** Generates a new tileset from an image file. This feature **replaces the current project palette** with a new, optimized 16-color palette generated from the image. It then presents all generated tiles in a selection dialog, allowing you to choose which ones to **append** to your current project's tileset. This uses the same powerful analysis engine as the full project importer, with options for palette constraints, optimization, and more.

    *   **Import Tiles from File (`Import/Export -> Import Tiles from File...`):** Allows you to add tiles from another MSX Tile Forge project. It opens a `.SC4Tiles` file, displays all the tiles it contains using the *current project's active palette*, and lets you select which ones to **append** to your current tileset. This is useful for building a "master" tileset from multiple sources.

    *   **ROM Importer (`Import -> Import Tiles from ROM...`):** Imports 8x8, 1-bit-per-pixel tile data directly from a binary file (e.g., a ROM dump). Features a visual browser, live preview, advanced multi-selection (Click, Shift+Click, Ctrl+Click), and controls for preview colors and the base byte offset.
        *   **Per-Selection Properties:** This is the key feature of the importer. When you select a tile or a range of tiles, the **current Fine Offset and FG/BG Colors are saved with that selection**. This allows you to select tiles from different parts of the ROM file (using different offsets) and assign them different colors, all within a single import operation. The final import will use the specific properties saved for each tile.

    *   **Export Raw Project (`Import/Export -> Export Raw Project...`):** Exports all project data into their raw binary formats. This feature runs an external script (`msxtileexport.py`) and provides options to automatically generate include files for assembly (`.s`) and C (`.h`), defining labels and arrays for the exported assets. This makes integrating the graphics into a development toolchain straightforward.
    
    *   **Export Map as Image (`Import/Export -> Export Map as Image...`):** Generates a full-resolution image file (PNG, BMP, JPG, TIFF) of the entire map. The export uses the project's native resolution (1:1 scale), rendering every Supertile pixel-perfectly using the current palette. This is ideal for creating level previews, documentation, or large background assets for modern engines.

*   **Project Management & UX:**
    *   Projects bundle all asset types: palettes, tilesets, supertiles and maps.
    *   Ability to save and load individual asset components (palette, tileset, supertiles, map) separately.
    *   **Comprehensive Undo/Redo System (`Ctrl+Z` / `Ctrl+Y`):** Nearly every action in the application is undoable, including painting strokes, transformations, adding/deleting assets, and palette changes. The `Edit` menu shows the specific action that will be undone or redone.
    *   **Automatic Startup:** The application remembers and automatically re-opens the last used project on startup. If it can't be found, a new blank project is created.
    *   Automatic tracking of unsaved changes within a project, with prompts to prevent data loss.
    *   **Recent Files Menu:** Remembers recently opened projects and individual module files.
        *   Use `Ctrl+R` / `Alt+R` to pop up the menus at the cursor.
        *   Use `Ctrl+1`..`0` / `Alt+1`..`0` to directly open recent items.
    *   **Persistent Window State:** The size and position of the main window, Usage windows, and editor sash dividers are saved and restored between sessions.

## Installation

Getting MSX Tile Forge up and running is straightforward. You can choose between using pre-compiled binaries for convenience or running directly from the source code if you are a developer.

### Choosing a Version

First, decide which version is right for you:

*   **Official Release (Recommended):** This is the most stable and tested version. If you want a reliable tool for your projects, start here. You can find the "Latest" release on the **[Releases Page](https://github.com/DamnedAngel/msx-tile-forge/releases/latest)**.

*   **Release Candidate (RC):** These are pre-release versions that are considered stable but are in a final testing phase before becoming the official release. They are a great way to try out new features early. RCs are also found on the **[Releases Page](https://github.com/DamnedAngel/msx-tile-forge/releases)** and will be marked as "Pre-release".

*   **Nightly Build (Advanced Users):** This is a build generated automatically every night from the very latest source code, when there are updates to the project. It contains the newest features and bug fixes but is also the least tested and may contain bugs. This is for users who want to follow development closely or test a very recent change. You can find these on the **[Internet Archive](https://archive.org/search.php?query=subject%3A"msxtileforge_nightly_build")**.

### Running a Pre-compiled Version (Windows, Linux)

This is the easiest way to get started and applies to Official, Release Candidate, and Nightly builds.

1.  **Download:** Go to the appropriate page (Releases or Internet Archive) and download the archive for your operating system (e.g., `..._win.zip` for Windows, `..._lin.tar.gz` or `..._deb.deb` for Linux).
2.  **Extract:** Unzip or extract the archive to a permanent location on your computer.
3.  **Run:**
    *   **On Windows:** Open the extracted folder and double-click `msxtileforge.exe`.
    *   **On Linux:** Open the extracted folder. You may need to make the main executable runnable first. Open a terminal in the directory and run `chmod +x msxtileforge`, then you can run it with `./msxtileforge`.
    *   **For Debian/Ubuntu users:** Alternatively, you can install the `.deb` package directly by double-clicking it or using the command line: `sudo dpkg -i /path/to/your/..._deb.deb`. After installation, you should be able to run `msxtileforge` from your terminal or find it in your application menu.

### Running from Source Code

This option is for users who are comfortable with Python and the command line.

1.  **Download:** Download the source code archive (e.g., `..._src.zip`) from the [Releases Page](https://github.com/DamnedAngel/msx-tile-forge/releases).
2.  **Install Dependencies:** Make sure you have Python 3 installed. Then, open a terminal in the directory where you extracted the source files and install the required libraries using the provided `requirements.txt` file:
    ```bash
    pip install -r requirements.txt
    ```
3.  **Run the Application:** Execute the main script with Python:
    ```bash
    python msxtileforge.py
    ```
    *(Note: On some systems, you may need to use `python3` instead of `python`)*.

## User Guide

This manual provides an overview of MSX Tile Forge's functionalities, organized by its main interface components.

### Global Operations (Menu Bar & General UX)

The main menu bar provides access to project-wide operations and settings.

*   **File Menu:**
    *   **Project Management:**
        *   `New Project (Ctrl+N)`: Starts a new project. You will first be prompted to define the **width and height of your supertiles** for this project. This dimension is then saved with the project and cannot be changed later. The action clears all current data (palette, tiles, supertiles, map).
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
        *   **Tile Editor:** Copies/pastes the current tile's pattern and row colors. When pasting a tile from a project with a different palette, colors are intelligently remapped to the closest available colors in the current project's palette.
        *   **Supertile Editor:** Copies/pastes the current supertile's definition. On paste, referenced tiles are visually matched to the most similar tiles in the current project's tileset.
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

*   **Import/Export Menu:**
    *   `Append Tileset from File...`: Appends tiles from another project's `.SC4Tiles` file to the current tileset.
    *   `Append Supertiles from File...`: Appends supertiles and their associated tiles from another project's `.SC4Super` and `.SC4Tiles` files.
    *   `Import Tiles from ROM...`: Opens the ROM Importer dialog to extract tile data from external binary files.
    *   `Import Tiles from Image...`: Opens the Image Importer to create a new tileset and palette from a standard image file.
    *   `Import Project from Image...`: Opens the advanced dialog to generate a complete new project from an image.
    *   `Export Raw Project...`: Opens a dialog to export all raw binary data (`.SC4Pal`, `.SC4Tiles`, etc.) to a specified folder. It includes options to generate assembly (`.s`) and C/C++ header (`.h`) files that define labels and arrays for the exported data, streamlining integration with game development projects.
    *   `Export Map as Image...`: Opens a save dialog to export the current map as a full-size image. The file format is automatically determined by the extension you choose (e.g., saving as `map.png` creates a PNG file).    

*   **Help Menu:**
    *   `About...`: Displays application information (version, author).

*   **General User Experience:**
    *   **Unsaved Changes:** The window title is marked with an asterisk (*) if the project has unsaved modifications. Prompts to save are given before closing, opening, or creating new projects if changes are pending.
    *   **Deep Dive Editing (Double-Click):** Double-clicking an item (like a tile on a supertile canvas, or a supertile on the map) will automatically switch to that item's editor tab and select it. This allows for rapid, intuitive navigation between asset levels.
    *   **Drag-and-Drop Operations:**
        *   **Move (LMB Drag):** Reorder items by dragging and dropping.
        *   **Swap (Ctrl+Drop):** Hold `CTRL` while dropping an item onto another to swap their positions and update all data references.
        *   **Replace All (Alt+Drop):** Hold `ALT` while dropping a source item onto a target to replace all uses of the target item with the source item project-wide.
    *   **Contextual Escape Key:** The `Escape` key has several functions depending on the context. In the Map Editor, it clears the current selection and clipboard. In the ROM Importer, it clears the selection. In the Tile and Supertile Editors, it clears any "Mark Unused" highlights.
    *   **Persistent Window State:** The size/position of the main window and all utility windows, as well as the position of editor dividers (sashes), are saved and restored between sessions.

### 1. Palette Editor Tab

This tab is dedicated to managing the 16-color active palette used for all graphics.

*   **Active Palette Display:** A 4x4 grid shows the 16 colors. Click a slot to select it for modification (highlighted red).
*   **Selected Slot Information:** Shows the selected slot's index, a color preview, its hexadecimal RGB value, its MSX2-specific RGB values (0-7 per channel), and a count of how many times it's used. The usage count is a **clickable link** to find all tiles using that color.
*   **Color Modification:**
    *   **MSX2 512 Color Picker:** A large grid displaying all 512 possible MSX2 colors. Clicking a color here applies it to the selected active palette slot.
    *   **Set Selected Color Panel:** This panel provides two synchronized ways to define a color:
        *   **MSX (0-7):** Input R, G, and B values from 0-7 in this row.
        *   **RGB (0-255):** Input standard R, G, and B values from 0-255 in this row.
        *   As you type in one set of boxes, the other set and the preview swatches will update in real-time to show the closest match. Invalid characters are blocked, and out-of-range numbers are automatically corrected when you leave an input box.
        *   Click the **"Set Color"** button to apply the final MSX2 color to the selected palette slot. This action is undoable.
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
    *   **Tile Operations:** Buttons for "Add New", **"Add Many..." (opens a dialog to add multiple blank tiles at once)**, "Insert", "Delete" tiles.
    *   **Info Label:** Shows total number of tiles in the set.
    *   **Project Tile Limit:** Set a custom limit (1-256) for the number of tiles in the project. This limit is saved with the project's `.SC4Tiles` file and prevents adding more tiles than intended for a specific project. Truncating the tileset via this feature is a fully undoable action.

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
    *   **Supertile Operations:** Buttons for "Add New", **"Add Many..." (opens a dialog to add multiple blank supertiles at once)**, "Insert", "Delete" supertiles.
    *   **Project Supertile Limit:** Set a custom limit (1-65535) for the number of supertiles in the project. This limit is saved with the `.SC4Super` file. Truncating the supertile set is a fully undoable action.


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

### 6. Importing Project from Image

This powerful feature (accessible via `Import -> Import Project from Image...`) generates a complete, new MSX Tile Forge project by analyzing a standard image file (e.g., PNG, BMP). It replaces the entire current project.

The import process uses the `msxtilemagic.py` script to perform the complex analysis and asset generation, providing a dialog with extensive options to control the outcome:
*   **Palette Constraints:** You can force the importer to use specific colors from your currently active palette (`Fixed`), prevent certain palette slots from being used (`Blocked`), or let the script choose the best color for a slot (`Auto`).
*   **Optimization Mode:** Choose a quality setting (`neutral`, `sharp`, `soft`, etc.) that influences how the script prioritizes color accuracy versus tile reuse.
*   **Supertile Dimensions:** Define the width and height of the supertiles that will be generated for the new project.
*   **Advanced Options:**
    *   **Dithering:** Enables dithering during the initial color quantization step, which can produce smoother gradients at the cost of more complex patterns.
    *   **Find Best Offset:** The script will test all 8 possible start offsets for the 8x8 tile grid on the source image and pick the one that yields the best compression (fewest unique tiles).
    *   **Synthesize Tiles:** If multiple visually similar but distinct 8x8 tiles from the image are merged into a single "best" tile, this option will try to create a new, hybrid tile that better represents the merged group, potentially improving visual fidelity.
    *   **Color Metrics:** For advanced color science enthusiasts, this allows choosing the mathematical model for comparing colors (`weighted-rgb`, `CIEDE2000`, etc.), which can affect palette generation and tile matching. `CIEDE2000` is the most perceptually accurate but requires the optional `colour-science` library.

## Technical Description of Generated Files

All project assets are saved in custom binary file formats. Multi-byte numerical values (like map dimensions or 16-bit counts) are stored in **Little-Endian** format (`<H`).

**File Format Versioning Note:**
Project component files created with this version (`.SC4Pal`, `.SC4Tiles`, `.SC4Super`, `.SC4Map`) include **4 reserved bytes** immediately following their primary header information. The application can still open older files that do not have these reserved bytes.

### 1. Palette File (`.SC4Pal`)

*   **Purpose:** Stores the 16-color active MSX2 palette.
*   **Structure:**
    *   **Reserved Bytes (4 bytes):** For future use.
    *   **Color Data (48 bytes total):** A sequence of 16 color entries (3 bytes each: R, G, B, with values 0-7 per channel).

### 2. Tileset File (`.SC4Tiles`)

*   **Purpose:** Stores definitions for 8x8 pixel tiles.
*   **Structure:**
    *   **Header:**
        *  `num_tiles_in_file`(1 byte): A value of `0` indicates 256 tiles.
        *  **Project Tile Limit** (1 byte): A value of `0` indicates 256 tiles.
        *  **Reserved Bytes (3 bytes):** Currently unused.
    *   **All Pattern Data Block (Total: `num_tiles` \* 8 bytes):** Pattern data for all tiles, stored consecutively. Each tile is 8 bytes (1 byte per row). In each byte, the most significant bit is the leftmost pixel.
    *   **All Color Attribute Data Block (Total: `num_tiles` \* 8 bytes):** Color attribute data for all tiles, stored consecutively. Each tile is 8 bytes (1 byte per row). The high nibble (4 bits) is the foreground palette index, and the low nibble is the background palette index.

### 3. Supertile Definition File (`.SC4Super`)

*   **Purpose:** Stores supertile definitions and their grid dimensions.
*   **Structure:**
    *   **Header:**
        *   **Supertile Count (1 or 3 bytes):** If the first byte is `1-255`, it's the count. If `0`, the next 2 bytes (a Little-Endian unsigned short) are the count (up to 65535).
        *   **Supertile Grid Dimensions (2 bytes):** `width` (1 byte), `height` (1 byte).
        *   **Project Supertile Limit (2 bytes, Little-Endian)):** A value of `0xFFFF` indicates 65535.
        *   **Reserved Bytes (2 bytes):** Currently unused.
    *   **Supertile Definition Blocks:** Each block is `width * height` bytes, with each byte being a tile index (0-255).

### 4. Map File (`.SC4Map`)

*   **Purpose:** Stores the overall map layout.
*   **Structure:**
    *   **Header:**
        * `map_width` (2 bytes, Little-Endian).
        * `map_height` (2 bytes, Little-Endian).
        * **Reserved Bytes (4 bytes):** Currently unused.
    *   **Map Data (Variable size):** A sequence of `map_width * map_height` supertile indices.
        *   **Index Size:** If the project's total supertile count was > 255 at save time, each index is **2 bytes** (Little-Endian). Otherwise, each index is **1 byte**. The application detects this based on file size during loading.

## Contributing

Contributions to MSX Tile Forge are welcome! If you have bug reports, feature suggestions, or would like to contribute code:

1.  **Issues:** Please feel free to open an issue on the project's GitHub repository to discuss bugs or propose new features.
2.  **Pull Requests:** For code contributions, please fork the repository, make your changes in a separate branch, and then submit a pull request for review.

Clear descriptions and, where applicable, steps to reproduce issues are greatly appreciated.

## License

This project is licensed under the **GNU Affero General Public License v3.0 (AGPL-3.0)**.

The full text of the license should be included with the software (typically in a `LICENSE` or `COPYING` file). It can also be found online at:
[https://www.gnu.org/licenses/agpl-3.0.en.html](https://www.gnu.org/licenses/agpl-3.0.en.html)