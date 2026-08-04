cmake_minimum_required(VERSION 3.20)
project(polesitter VERSION 1.0.0 LANGUAGES C)

set(CMAKE_C_STANDARD 99)
set(CMAKE_C_STANDARD_REQUIRED ON)
set(CMAKE_C_EXTENSIONS OFF)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

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

    function(ps_configure_accuracy_target target source_file)
        add_executable(${target} ${source_file})
        target_link_libraries(${target} PRIVATE polesitter)
        target_include_directories(${target} PRIVATE ${CMAKE_CURRENT_BINARY_DIR})

        if(NOT MSVC)
            target_link_libraries(${target} PRIVATE m)
        endif()

        if(MSVC)
            target_compile_options(${target} PRIVATE
                /W4 /WX /O2
            )
        else()
            target_compile_options(${target} PRIVATE
                -Wall -Wextra -pedantic -O3 -ffast-math -march=native
            )
        endif()
    endfunction()

    ps_configure_accuracy_target(polesitter_accuracy_baseline tests/accuracy.c)
    add_test(NAME accuracy_baseline COMMAND polesitter_accuracy_baseline)

    function(ps_add_fixed_accuracy_variant variant mac_factor)
        file(READ "${CMAKE_CURRENT_SOURCE_DIR}/src/polesitter.h" variant_header)

        string(REPLACE
            "float force_dip_x = (dx * dipole_coeff) - (mx * inv_r3);"
            "float force_dip_x = (mx * inv_r3) - (dx * dipole_coeff);"
            variant_header "${variant_header}"
        )
        string(REPLACE
            "float force_dip_y = (dy * dipole_coeff) - (my * inv_r3);"
            "float force_dip_y = (my * inv_r3) - (dy * dipole_coeff);"
            variant_header "${variant_header}"
        )
        string(REPLACE
            "float force_dip_z = (dz * dipole_coeff) - (mz * inv_r3);"
            "float force_dip_z = (mz * inv_r3) - (dz * dipole_coeff);"
            variant_header "${variant_header}"
        )
        string(REPLACE
            "float32x4_t eps_vec = vdupq_n_f32(2.0F);"
            "float32x4_t eps_vec = vdupq_n_f32(0.1F);"
            variant_header "${variant_header}"
        )
        string(REPLACE
            "if (dist_sq > (theta * theta) * (hw_sum * hw_sum)) {"
            "if (dist_sq > ${mac_factor}F * (theta * theta) * (hw_sum * hw_sum)) {"
            variant_header "${variant_header}"
        )

        if(ARGC GREATER 2 AND "${ARGV2}" STREQUAL "soft")
            string(REPLACE
                "        float dist   = sqrtf(dist_sq);\n        float inv_r3 = 1.0F / (dist * dist_sq);\n        float inv_r5 = inv_r3 / dist_sq;"
                "        float soft_dist_sq = dist_sq + 0.1F;\n        float dist         = sqrtf(soft_dist_sq);\n        float inv_r3       = 1.0F / (dist * soft_dist_sq);\n        float inv_r5       = inv_r3 / soft_dist_sq;"
                variant_header "${variant_header}"
            )
        endif()

        set(variant_header_name "polesitter_${variant}.h")
        file(WRITE "${CMAKE_CURRENT_BINARY_DIR}/${variant_header_name}"
             "${variant_header}")

        file(READ "${CMAKE_CURRENT_SOURCE_DIR}/tests/accuracy.c" variant_source)
        string(REPLACE
            "#include \"../src/polesitter.h\""
            "#include \"${variant_header_name}\""
            variant_source "${variant_source}"
        )
        string(REPLACE
            "source.x = 10.0F;"
            "source.x = 100.0F;"
            variant_source "${variant_source}"
        )
        string(REPLACE
            "target.local[1], 0.008, 1e-6"
            "target.local[1], 0.000098, 5e-9"
            variant_source "${variant_source}"
        )

        set(variant_source_path "${CMAKE_CURRENT_BINARY_DIR}/accuracy_${variant}.c")
        file(WRITE "${variant_source_path}" "${variant_source}")

        set(target "polesitter_accuracy_${variant}")
        ps_configure_accuracy_target(${target} "${variant_source_path}")
        add_test(NAME accuracy_${variant} COMMAND ${target})
    endfunction()

    ps_add_fixed_accuracy_variant(mac3 3.0)
    ps_add_fixed_accuracy_variant(mac12 12.0)
    ps_add_fixed_accuracy_variant(mac27 27.0)
    ps_add_fixed_accuracy_variant(mac48 48.0)
    ps_add_fixed_accuracy_variant(soft3 3.0 soft)
    ps_add_fixed_accuracy_variant(soft12 12.0 soft)
    ps_add_fixed_accuracy_variant(soft48 48.0 soft)

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
