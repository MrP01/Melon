cmake_minimum_required(VERSION 3.16)
project(libcppscheduler)

add_definitions("-std=c++20")
add_definitions("-O3")  # optimisation level 3
add_definitions("-g")  # gcc adds debug information (confer `man gcc`)
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

list(APPEND CMAKE_PREFIX_PATH "${CMAKE_BINARY_DIR}")
find_package(pybind11 REQUIRED)

pybind11_add_module(libcppscheduler melon/scheduler/libcppscheduler.cpp)
target_compile_definitions(libcppscheduler PRIVATE SILENT=1)
