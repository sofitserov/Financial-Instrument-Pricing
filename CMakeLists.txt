cmake_minimum_required(VERSION 3.15)
project(AlphaEngine)

set(CMAKE_CXX_STANDARD 20)

find_package(pybind11 REQUIRED)
pybind11_add_module(AlphaEngine wrapper.cpp)
target_include_directories(AlphaEngine PRIVATE ${CMAKE_CURRENT_SOURCE_PATH})

pybind11_add_module(AlphaEnginePairs wrapper_pairs.cpp)
target_include_directories(AlphaEnginePairs PRIVATE ${CMAKE_CURRENT_SOURCE_PATH})
