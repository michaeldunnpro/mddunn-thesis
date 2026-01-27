# Init RustBCA Subdirectory

build: clone
	$(info Building RustBCA submodule...)
	cd RustBCA && cargo build --release || { \
		echo "Failed to build RustBCA submodule. Is Cargo installed?"; \
		exit 1; \
	}
	$(info RustBCA submodule built successfully.)
	$(info Installing Python bindings...)
	cd RustBCA && pip install . || { \
		echo "Failed to install Python bindings. Is pip installed?"; \
		exit 1; \
	}
	$(info Python bindings installed successfully.)
	
clone:
	$(info Cloning RustBCA submodule...)
	git submodule update --init --recursive || { \
		echo "Failed to clone RustBCA submodule. Is git installed?"; \
		exit 1; \
	}
	$(info RustBCA submodule cloned successfully.)