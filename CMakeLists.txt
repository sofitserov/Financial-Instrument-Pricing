cmake_minimum_required(VERSION 3.15)
project(AlphaEngine)

set(CMAKE_CXX_STANDARD 20)

# 1. This tells CMake to go find the pybind11 we just installed
find_package(pybind11 REQUIRED)

# 2. This creates your Python module
# Note: Ensure strategy.hpp and wrapper.cpp are in the same folder as this file
# or update the paths below.
pybind11_add_module(AlphaEngine wrapper.cpp)

# 3. This links the headers so the red squiggles go away
target_include_directories(AlphaEngine PRIVATE ${CMAKE_CURRENT_SOURCE_PATH})