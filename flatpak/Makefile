# msx-tile-forge Makefile for Flathub

# Defaults (can be overridden by environment/flatpak-builder)
APP_VERSION ?= 0.0.0
FLATPAK_ID ?= io.github.DamnedAngel.msx-tile-forge
FLATPAK_DEST ?= /app
APP_SRC := ..
FLATPAK_SRC := .

PY_SCRIPTS := \
	$(APP_SRC)/msxtileforge.py \
	$(APP_SRC)/msxtileexport.py \
	$(APP_SRC)/msxtilemagic.py \
	$(APP_SRC)/supertilerandomizer.py \
	$(APP_SRC)/tilerandomizer.py

ICON := $(FLATPAK_SRC)/io.github.DamnedAngel.msx-tile-forge.png
DESKTOP := $(FLATPAK_SRC)/io.github.DamnedAngel.msx-tile-forge.desktop
METAINFO := $(FLATPAK_SRC)/io.github.DamnedAngel.msx-tile-forge.metainfo.xml
WRAPPER := $(FLATPAK_SRC)/wrapper.sh

# Default target
all:

# Install, to use only by io.github.DamnedAngel.msx-tile-forge.yaml
install:
	@echo "==> Building $(FLATPAK_ID) version $(APP_VERSION)"
	# Patch version in Python scripts
	find $(APP_SRC) -type f -name "*.py" -exec sed -i "s/<unreleased>/$(APP_VERSION)/g" {} +
	# Install Python entry points
	for f in $(PY_SCRIPTS); do \
		install -Dm644 $$f $(FLATPAK_DEST)/bin/$$(basename $$f); \
	done
	# Install wrapper
	install -Dm755 $(WRAPPER) $(FLATPAK_DEST)/bin/msxtileforge
	# Install icon
	install -Dm644 $(ICON) \
		$(FLATPAK_DEST)/share/icons/hicolor/256x256/apps/$(notdir $(ICON))
	# Install desktop entry
	install -Dm644 $(DESKTOP) \
		$(FLATPAK_DEST)/share/applications/$(notdir $(DESKTOP))
	# Install metainfo
	install -Dm644 $(METAINFO) \
		$(FLATPAK_DEST)/share/metainfo/$(FLATPAK_ID).metainfo.xml
	@echo "==> Build completed."

# Smoke test
smoketest:
	@echo "==> Smoke test starting..."
	# local install
	@flatpak-builder --install --force-clean --user build-dir io.github.DamnedAngel.msx-tile-forge.yaml
	# list installed applications
	@flatpak list --app --user
	# local run
	@flatpak run io.github.DamnedAngel.msx-tile-forge
	# uninstall
	@flatpak uninstall -y io.github.DamnedAngel.msx-tile-forge
	@echo "==> Smoke test completed."

# Full test
fulltest:
	@echo "==> Full test with lint starting..."
	# Clean old builds
	@rm -rf build-dir
	# Show flatpak runtime installed python version
	@flatpak run --command=python3 org.freedesktop.Platform//24.08 --version
	# Lint manifest
	@flatpak run --command=flatpak-builder-lint org.flatpak.Builder manifest io.github.DamnedAngel.msx-tile-forge.yaml
	# Build completely (install app files)
	@flatpak-builder --force-clean build-dir io.github.DamnedAngel.msx-tile-forge.yaml
	# Lint appdir content
	@flatpak run --command=flatpak-builder-lint org.flatpak.Builder builddir build-dir || true | tee lint.log
	@if grep -q "error" lint.log && ! grep -q "appstream-external-screenshot-url" lint.log; then exit 1; fi
	# Test run
	@flatpak-builder --run build-dir io.github.DamnedAngel.msx-tile-forge.yaml msxtileforge
	@echo "==> Full test completed."

.PHONY: all install smoketest fulltest

