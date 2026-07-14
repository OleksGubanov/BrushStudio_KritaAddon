cmake_minimum_required(VERSION 3.14)
project(brush_studio_engine)

# Find pybind11
find_package(pybind11 REQUIRED)

# This module requires Krita source and headers to build.
# You must set KRITA_SOURCE_DIR and KRITA_BUILD_DIR to your Krita setup.
if (NOT DEFINED KRITA_SOURCE_DIR)
    message(FATAL_ERROR "Please define KRITA_SOURCE_DIR pointing to Krita source tree")
endif()

# We need Qt5
find_package(Qt5 COMPONENTS Core Gui REQUIRED)

# Include Krita directories (adjust as needed for Krita 5 layout)
include_directories(
    ${KRITA_SOURCE_DIR}/libs/image
    ${KRITA_SOURCE_DIR}/libs/ui
    ${KRITA_SOURCE_DIR}/libs/pigment
    ${KRITA_SOURCE_DIR}/libs/global
    ${KRITA_BUILD_DIR}/libs/image
)

pybind11_add_module(brush_studio_engine preview_engine.cpp)

# Link against Krita libraries and Qt5
target_link_libraries(brush_studio_engine PRIVATE 
    Qt5::Core Qt5::Gui 
    kritaimage kritaui kritaglobal
)
