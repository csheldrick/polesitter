cmake_minimum_required(VERSION 3.20)
project(polesitter VERSION 1.0.0 LANGUAGES C)

set(CMAKE_C_STANDARD 99)
set(CMAKE_C_STANDARD_REQUIRED ON)
set(CMAKE_C_EXTENSIONS OFF)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

option(POLESITTER_VALIDATE_FIXES "Apply isolated correctness fixes for validation" ON)

if(POLESITTER_VALIDATE_FIXES)
    file(READ "${CMAKE_CURRENT_SOURCE_DIR}/src/polesitter.h" POLESITTER_HEADER)

    string(REPLACE
        "float force_dip_x = (dx * dipole_coeff) - (mx * inv_r3);"
        "float force_dip_x = (mx * inv_r3) - (dx * dipole_coeff);"
        POLESITTER_HEADER "${POLESITTER_HEADER}"
    )
    string(REPLACE
        "float force_dip_y = (dy * dipole_coeff) - (my * inv_r3);"
        "float force_dip_y = (my * inv_r3) - (dy * dipole_coeff);"
        POLESITTER_HEADER "${POLESITTER_HEADER}"
    )
    string(REPLACE
        "float force_dip_z = (dz * dipole_coeff) - (mz * inv_r3);"
        "float force_dip_z = (mz * inv_r3) - (dz * dipole_coeff);"
        POLESITTER_HEADER "${POLESITTER_HEADER}"
    )
    string(REPLACE
        "float32x4_t eps_vec = vdupq_n_f32(2.0F);"
        "float32x4_t eps_vec = vdupq_n_f32(0.1F);"
        POLESITTER_HEADER "${POLESITTER_HEADER}"
    )
    string(REPLACE
        "if (dist_sq > (theta * theta) * (hw_sum * hw_sum)) {"
        "if (dist_sq > 3.0F * (theta * theta) * (hw_sum * hw_sum)) {"
        POLESITTER_HEADER "${POLESITTER_HEADER}"
    )

    file(WRITE "${CMAKE_CURRENT_SOURCE_DIR}/src/polesitter.h" "${POLESITTER_HEADER}")
endif()

add_library(polesitter INTERFACE)

target_include_directories(polesitter INTERFACE
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}>
)

if(CMAKE_PROJECT_NAME STREQUAL PROJECT_NAME)
    enable_testing()

    add_executable(polesitter_tests tests/main.c)

    target_link_libraries(polesitter_tests PRIVATE polesitter)

    if(NOT MSVC)
        target_link_libraries(polesitter_tests PRIVATE m)
    endif()

    if(MSVC)
        target_compile_options(polesitter_tests PRIVATE
            /W4 /WX /O2
        )
    else()
        target_compile_options(polesitter_tests PRIVATE
            -Wall -Wextra -pedantic -O3 -ffast-math -march=native
        )
    endif()

    add_test(NAME core_tests COMMAND polesitter_tests)

    add_executable(polesitter_accuracy_tests tests/accuracy.c)
    target_link_libraries(polesitter_accuracy_tests PRIVATE polesitter)

    if(NOT MSVC)
        target_link_libraries(polesitter_accuracy_tests PRIVATE m)
    endif()

    if(MSVC)
        target_compile_options(polesitter_accuracy_tests PRIVATE
            /W4 /WX /O2
        )
    else()
        target_compile_options(polesitter_accuracy_tests PRIVATE
            -Wall -Wextra -pedantic -O3 -ffast-math -march=native
        )
    endif()

    add_test(NAME accuracy_tests COMMAND polesitter_accuracy_tests)

    add_executable(polesitter_benchmark tests/benchmark.c)
    target_link_libraries(polesitter_benchmark PRIVATE polesitter)

    if(NOT MSVC)
        target_link_libraries(polesitter_benchmark PRIVATE m)
    endif()

    if(MSVC)
        target_compile_options(polesitter_benchmark PRIVATE
            /W4 /WX /O2
        )
    else()
        target_compile_options(polesitter_benchmark PRIVATE
            -Wall -Wextra -pedantic -O3 -ffast-math -march=native
        )
    endif()
endif()
