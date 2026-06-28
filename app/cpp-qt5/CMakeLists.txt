cmake_minimum_required(VERSION 3.16)
project(IoTGateway VERSION 1.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_AUTOMOC ON)

find_package(Qt5 REQUIRED COMPONENTS Widgets Network)

add_executable(iot-gateway WIN32
    main.cpp
)

target_link_libraries(iot-gateway
    Qt5::Widgets
    Qt5::Network
    ws2_32
)

# Windows specific
if(WIN32)
    target_compile_definitions(iot-gateway PRIVATE _WIN32_WINNT=0x0601)
endif()
