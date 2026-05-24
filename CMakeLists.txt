cmake_minimum_required(VERSION 3.15)
project(AlphaEngine)

set(CMAKE_CXX_STANDARD 20)

# 1. Finds the pybind11 package
find_package(pybind11 REQUIRED)

# 2. Creates the Python module named "AlphaEngine" from the wrapper.cpp file
pybind11_add_module(AlphaEngine wrapper.cpp)

# 3. Links the headers and source files to the module
target_include_directories(AlphaEngine PRIVATE ${CMAKE_CURRENT_SOURCE_PATH})