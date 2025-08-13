# ----------------------------
# Usage
# ----------------------------
# Build everything
#   make all
# Build only Debian package (NOTE: change app version on debian/changelog)
#   make debian
# Clean everything
#   make clean
# ----------------------------

# Variables
APP_FILE = msxtileforge.py
DEPLOY_DIR = dist
DEB_PACKAGE = msx-tile-forge_*.deb

.PHONY: all clean release debian prepare

all: clean release debian 
	@echo "✅ All builds completed. Files in $(DEPLOY_DIR)/"

# ----------------------------
# App build
# ----------------------------
release:
	@echo "📦 Building release..."
	@pyinstaller \
		--onefile $(APP_FILE) \
		--hidden-import=PIL \
		--hidden-import=numpy \
		--hidden-import=scipy \
		--hidden-import=platformdirs \
		--hidden-import=tqdm \
		--clean
	@echo "✅ Application saved to $(DEPLOY_DIR)/"

# ----------------------------
# Debian package build
# ----------------------------
debian:
	@echo "📦 Building Debian package..."
	debuild -us -uc -b -tc
	@mv ../$(DEB_PACKAGE) $(DEPLOY_DIR)/
	@rm -f ../*.changes ../*.build ../*.buildinfo
	@echo "✅ Debian package saved to $(DEPLOY_DIR)/$(DEB_PACKAGE)"

# ----------------------------
# Cleanup
# ----------------------------
clean:
	@echo "🧹 Cleaning build artifacts..."
	@mkdir -p $(DEPLOY_DIR)
	rm -rf $(DEPLOY_DIR)/*
	@echo "✅ Clean complete."
