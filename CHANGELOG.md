# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

---

## [01.00.00] - YYYY-MM-DD

### Core Editors

-   **Palette Editor:**
    -   Manages a 16-color active palette for the project.
    -   Provides a full 512-color MSX2 visual color picker.
    -   Allows direct color editing via 3-bit (0-7) RGB values.
    -   Supports drag-and-drop to swap palette slots.
-   **Tile Editor:**
    -   Pixel editor for creating 8x8, 1-bit-per-pixel (2-color) tiles.
    -   Supports MSX-specific graphics modes by allowing each of the 8 rows in a tile to have its own unique foreground and background color.
    -   Includes a full suite of tile transformation tools: Flip (Horizontal/Vertical), Rotate, and Shift (Up/Down/Left/Right with wrap-around).
-   **Supertile Editor:**
    -   Constructs larger, composite "supertiles" by arranging 8x8 tiles into a user-defined grid.
    -   Provides a tile palette for painting tiles onto the supertile definition grid.
    -   Includes a full suite of supertile transformation tools: Flip, Rotate (for square supertiles), and Shift.
-   **Map Editor:**
    -   Designs large game maps by arranging supertiles on a grid.
    -   Features a zoomable canvas for detailed work and overview.
    -   Includes a real-time, resizable **Minimap** for quick navigation.
    -   Provides visual overlays for the Supertile Grid and a configurable "Window View" to visualize screen boundaries.

### Workflow & Productivity Features

-   **Undo/Redo System:** Comprehensive, multi-level undo and redo for all data-modifying actions.
-   **Usage Analytics Windows:**
    -   **Color Usage:** A dockable window that lists all 16 palette colors and details their usage count across all tiles.
    -   **Tile Usage:** A dockable window that lists all tiles and details how many times each is used and in which supertiles.
    -   **Supertile Usage:** A dockable window that lists all supertiles and details how many times each is used on the map.
-   **Drag-and-Drop Workflow:**
    -   **Reorder:** Tiles, supertiles, and palette colors can be reordered.
    -   **Swap:** `Ctrl+Drag` swaps the positions of two items.
    -   **Replace All References:** `Alt+Drag` replaces all uses of a target item (color, tile, or supertile) with a source item.
-   **"Deep Dive" Editing:** Double-clicking an element allows for quick navigation between editors.
-   **Advanced Copy/Paste:**
    -   Copies tiles and supertiles to the system clipboard in a self-contained format.
    -   Intelligently remaps colors and tiles when pasting between projects with different palettes or tilesets using the CIELAB color space and the Hungarian algorithm.

### Import/Export & Developer Integration

-   **Project & Module System:** Saves and loads projects as a set of interoperable component files (`.SC4Pal`, `.SC4Tiles`, `.SC4Super`, `.SC4Map`).
-   **Automated Build & Release System:** Implemented a GitHub Actions workflow to automatically build, package, and release the application for Windows, Linux, and Debian.
-   **Import from Image:**
    -   **Project Import:** Can generate an entire new project from a single source image via `msxtilemagic.py`.
    -   **Tile Import:** Can derive and quantize a new tileset and palette from an image.
-   **Import from ROM:** Includes a graphical tool to scan binary ROM files and visually extract 1bpp tile graphics.
-   **Developer Export:** Can export project data to raw binary and generate assembly (`.s`) and C header (`.h`) files via `msxtileexport.py`.
-   **Standalone Helper Scripts:** Provides command-line scripts (`tilerandomizer.py`, `supertilerandomizer.py`) for programmatic asset manipulation.
-   **Versioning:** The version string is no longer hardcoded and is now dynamically inserted at build time.

### Licensing

-   **License:** MSX Tile Forge is licensed under the **GNU General Public License v3.0 or later**, with an additional term under Section 7(b): modified versions must preserve the original copyright notice and the "Damned Angel" author attribution in the legal notices they display (e.g., the About dialog). All source files carry the corresponding header.
-   **Your output is yours:** projects and exported files (binaries, assembly and C headers) carry no license obligation.
-   **About dialog:** updated credits ("Made with Gemini AI") and an optional "Made with MSX Tile Forge" attribution request.
