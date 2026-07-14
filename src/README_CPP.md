# Brush Studio C++ Engine

This folder contains a C++ extension (`brush_studio_engine.pyd`) for rendering Krita brush previews.

## Prerequisites
To compile this, you must have the **Krita build environment** set up on your machine. This includes:
1. The Krita source tree (e.g., `krita/`)
2. The compiled Krita binaries and libraries (e.g., `krita-build/`)
3. `pybind11` installed in your Python environment (`pip install pybind11`)
4. CMake and MSVC / MinGW.

## How to build

1. Open a terminal (e.g., x64 Native Tools Command Prompt for VS 2022).
2. Navigate to this `src` folder.
3. Run CMake:
   ```bash
   mkdir build
   cd build
   cmake -DKRITA_SOURCE_DIR="C:/path/to/krita/src" -DKRITA_BUILD_DIR="C:/path/to/krita/build" ..
   cmake --build . --config Release
   ```
4. Once compiled, copy the resulting `brush_studio_engine.pyd` (or `.so` on Linux) from the `build` directory directly into the main `brush_studio` python plugin directory.
