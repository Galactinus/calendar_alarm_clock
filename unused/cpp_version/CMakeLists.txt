cmake_minimum_required(VERSION 3.14)
project(ulticlock)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Find required packages
find_package(CURL REQUIRED)
find_package(SQLite3 REQUIRED)
find_package(LibICAL REQUIRED)
find_package(nlohmann_json REQUIRED)

# Add include directories
include_directories(${PROJECT_SOURCE_DIR}/include)

# Add library targets
add_library(ulticlock_lib
    src/sql_manager.cpp
    src/ical_manager.cpp
    src/config_manager.cpp
)

# Add executable target
add_executable(ulticlock
    src/main.cpp
)

# Link libraries
target_link_libraries(ulticlock_lib
    PRIVATE
    CURL::libcurl
    SQLite::SQLite3
    LibICAL::ical
    nlohmann_json::nlohmann_json
)

target_link_libraries(ulticlock
    PRIVATE
    ulticlock_lib
) 