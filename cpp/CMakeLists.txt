cmake_minimum_required(VERSION 3.16)

project(ControlSystemBox
    VERSION 2.1.2
    DESCRIPTION "控制系统实时分析工具 - C++ Qt6 版本"
    LANGUAGES CXX
)

# C++ 标准
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Qt 自动处理
set(CMAKE_AUTOMOC ON)
set(CMAKE_AUTORCC ON)
set(CMAKE_AUTOUIC ON)

# Windows 下隐藏控制台窗口
if(WIN32)
    set(CMAKE_WIN32_EXECUTABLE ON)
endif()

# 查找 Qt6
find_package(Qt6 REQUIRED COMPONENTS
    Widgets
    SerialPort
    Network
    Concurrent
    Charts
)

# 查找可选库
find_package(FFTW3 QUIET)
find_package(Eigen3 QUIET)

# 如果没找到 Eigen，使用 header-only 模式
if(NOT Eigen3_FOUND)
    message(STATUS "Eigen3 not found, will use bundled headers if available")
endif()

# 源文件
set(CORE_SOURCES
    src/core/SerialManager.cpp
    src/core/SimulatorReceiver.cpp
    src/core/DataBuffer.cpp
    src/core/UnifiedDataProtocol.cpp
    src/core/SignalFilter.cpp
    src/core/PerformanceAnalyzer.cpp
    src/core/DataProcessor.cpp
)

set(UI_SOURCES
    src/ui/MainWindow.cpp
    src/ui/panels/SerialConfigPanel.cpp
    src/ui/panels/SimulatorConfigPanel.cpp
    src/ui/panels/PIDControlPanel.cpp
    src/ui/panels/SetpointPanel.cpp
    src/ui/panels/MetricsPanel.cpp
    src/ui/panels/DataControlPanel.cpp
    src/ui/panels/FilterPanel.cpp
    src/ui/panels/UnifiedControlPanel.cpp
    src/ui/widgets/DialWithLabel.cpp
    src/ui/widgets/SliderWithLabel.cpp
    src/ui/widgets/MetricCard.cpp
    src/ui/widgets/StabilityGauge.cpp
    src/ui/plots/RealtimePlotWidget.cpp
    src/ui/plots/FFTPlotWidget.cpp
    src/ui/plots/SimulatorPlotWidget.cpp
    src/ui/windows/AnalysisWindow.cpp
    src/ui/windows/ExtendedAnalysisWindow.cpp
)

set(HEADER_FILES
    include/core/SerialManager.h
    include/core/SimulatorReceiver.h
    include/core/DataBuffer.h
    include/core/UnifiedDataProtocol.h
    include/core/SignalFilter.h
    include/core/PerformanceAnalyzer.h
    include/core/DataProcessor.h
    include/ui/MainWindow.h
    include/ui/panels/SerialConfigPanel.h
    include/ui/panels/SimulatorConfigPanel.h
    include/ui/panels/PIDControlPanel.h
    include/ui/panels/SetpointPanel.h
    include/ui/panels/MetricsPanel.h
    include/ui/panels/DataControlPanel.h
    include/ui/panels/FilterPanel.h
    include/ui/panels/UnifiedControlPanel.h
    include/ui/widgets/DialWithLabel.h
    include/ui/widgets/SliderWithLabel.h
    include/ui/widgets/MetricCard.h
    include/ui/widgets/StabilityGauge.h
    include/ui/plots/RealtimePlotWidget.h
    include/ui/plots/FFTPlotWidget.h
    include/ui/plots/SimulatorPlotWidget.h
    include/ui/windows/AnalysisWindow.h
    include/ui/windows/ExtendedAnalysisWindow.h
)

# QCustomPlot (如果使用)
if(EXISTS "${CMAKE_SOURCE_DIR}/lib/qcustomplot/qcustomplot.cpp")
    set(QCUSTOMPLOT_SOURCES lib/qcustomplot/qcustomplot.cpp)
    set(QCUSTOMPLOT_HEADERS lib/qcustomplot/qcustomplot.h)
    add_definitions(-DUSE_QCUSTOMPLOT)
endif()

# 创建可执行文件
add_executable(${PROJECT_NAME}
    src/main.cpp
    ${CORE_SOURCES}
    ${UI_SOURCES}
    ${HEADER_FILES}
    ${QCUSTOMPLOT_SOURCES}
    resources/resources.qrc
)

# 头文件目录
target_include_directories(${PROJECT_NAME} PRIVATE
    ${CMAKE_SOURCE_DIR}/include
    ${CMAKE_SOURCE_DIR}/lib
)

# 链接 Qt 库
target_link_libraries(${PROJECT_NAME} PRIVATE
    Qt6::Widgets
    Qt6::SerialPort
    Qt6::Network
    Qt6::Concurrent
    Qt6::Charts
)

# 链接 FFTW3 (如果找到)
if(FFTW3_FOUND)
    target_link_libraries(${PROJECT_NAME} PRIVATE FFTW3::fftw3)
    target_compile_definitions(${PROJECT_NAME} PRIVATE USE_FFTW)
endif()

# 链接 Eigen (如果找到)
if(Eigen3_FOUND)
    target_link_libraries(${PROJECT_NAME} PRIVATE Eigen3::Eigen)
endif()

# 安装规则
install(TARGETS ${PROJECT_NAME}
    RUNTIME DESTINATION bin
)

# 复制资源文件
install(DIRECTORY resources/images/ DESTINATION bin/images)
install(DIRECTORY resources/styles/ DESTINATION bin/styles)

# Windows 下复制 Qt DLL
if(WIN32)
    # 获取 Qt 安装路径
    get_target_property(QT_QMAKE_EXECUTABLE Qt6::qmake IMPORTED_LOCATION)
    get_filename_component(QT_BIN_DIR "${QT_QMAKE_EXECUTABLE}" DIRECTORY)

    # 部署工具
    find_program(WINDEPLOYQT_EXECUTABLE windeployqt HINTS "${QT_BIN_DIR}")

    if(WINDEPLOYQT_EXECUTABLE)
        add_custom_command(TARGET ${PROJECT_NAME} POST_BUILD
            COMMAND "${WINDEPLOYQT_EXECUTABLE}"
                --no-translations
                --no-system-d3d-compiler
                --no-opengl-sw
                "$<TARGET_FILE:${PROJECT_NAME}>"
            COMMENT "Running windeployqt..."
        )
    endif()
endif()

# 输出配置信息
message(STATUS "===============================================")
message(STATUS "Control System Box - C++ Qt6 Version")
message(STATUS "===============================================")
message(STATUS "Version: ${PROJECT_VERSION}")
message(STATUS "Qt6 Found: YES")
message(STATUS "FFTW3 Found: ${FFTW3_FOUND}")
message(STATUS "Eigen3 Found: ${Eigen3_FOUND}")
message(STATUS "QCustomPlot: ${QCUSTOMPLOT_SOURCES}")
message(STATUS "===============================================")
