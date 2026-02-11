# Init RustBCA submodule, build it, and install Python bindings. Then build the Python extension module.
# Detect OS (MacOS vs Linux) for sed in-place editing
UNAME_S := $(shell uname -s)
ifeq ($(UNAME_S),Darwin)
    SED_INPLACE = sed -i ''
else
    SED_INPLACE = sed -i
endif

build: clone
	git submodule update --rebase --remote || { \
		echo "Failed to update RustBCA submodule. Is git installed?"; \
		exit 1; \
	}
	@echo "Building RustBCA submodule..."
	cd RustBCA && cargo build --release || { \
		echo "Failed to build RustBCA submodule. Is Cargo installed?"; \
		exit 1; \
	}
	@echo "RustBCA submodule built successfully."
	@echo "Installing Python bindings..."
	cd RustBCA && pip install . || { \
		echo "Failed to install Python bindings. Is pip installed?"; \
		exit 1; \
	}
	@echo "Python bindings installed successfully."
	@echo "Building Python extension module..."
	cd src && $(SED_INPLACE) "s|^SRC_DIR = .*|SRC_DIR = \"$(CURDIR)/src\"|" diamond_simulations/config.py || { \
		echo "Failed to update config.py with correct SRC_DIR. Is sed installed?"; \
		exit 1; \
	}
	@echo "Updated config.py with correct SRC_DIR."
	python3 -m pip uninstall -y diamond_simulations
	python3 -m pip install -e . || { \
		echo "Failed to build Python extension module. Is pip installed?"; \
		exit 1; \
	}
	@echo "Python extension module built successfully."
	
help:
	@echo "Custom wrapper and build system for RustBCA and custom Python bindings"
	@echo ""
	@echo "Targets:"
	@echo "  make          - Check dependencies and build everything"
	@echo "  make clone    - Initialize/update RustBCA submodule"
	@echo "  make clean    - Remove build artifacts"
	@echo ""


clone:
	@echo "Cloning RustBCA submodule..."
	git submodule update --init --recursive || { \
		echo "Failed to clone RustBCA submodule. Is git installed?"; \
		exit 1; \
	}
	@echo "RustBCA submodule cloned successfully."

clean: 
	cd RustBCA && cargo clean
	python3 -m pip uninstall -y diamond_simulations
	rm -rf build dist *.egg-info
	@echo "Cleaned build artifacts and uninstalled diamond_simulations package."