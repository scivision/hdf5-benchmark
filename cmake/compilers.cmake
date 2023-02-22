# check C and Fortran compiler ABI compatibility

if(NOT abi_ok)
  message(CHECK_START "checking that compilers can link together")
  try_compile(abi_ok
  ${CMAKE_CURRENT_BINARY_DIR}/abi_check ${CMAKE_CURRENT_LIST_DIR}/abi_check
  abi_check
  )
  if(abi_ok)
    message(CHECK_PASS "OK")
  else()
    set(err_log ${CMAKE_CURRENT_BINARY_DIR}/abi_check/CMakeError.log)
    message(FATAL_ERROR "ABI-incompatible compilers:
    C compiler ${CMAKE_C_COMPILER_ID} ${CMAKE_C_COMPILER_VERSION}
    Fortran compiler ${CMAKE_Fortran_COMPILER_ID} ${CMAKE_Fortran_COMPILER_VERSION}")
  endif()
endif()

# --- C compile flags
if(CMAKE_C_COMPILER_ID MATCHES "Clang|GNU|^Intel")
  add_compile_options(
  "$<$<AND:$<COMPILE_LANGUAGE:C>,$<CONFIG:Debug>>:-Wextra>"
  "$<$<COMPILE_LANGUAGE:C>:-Wall>"
  "$<$<COMPILE_LANGUAGE:C>:-Werror=implicit-function-declaration>"
  )
elseif(CMAKE_C_COMPILER_ID MATCHES "MSVC")
  add_compile_options("$<$<COMPILE_LANGUAGE:C>:/W3>")
endif()

if(WIN32)
  if(CMAKE_C_COMPILER_ID MATCHES "^Intel|MSVC")
    add_compile_options($<$<AND:$<COMPILE_LANGUAGE:C>,$<CONFIG:Debug>>:/Od>)
  endif()
elseif(CMAKE_C_COMPILER_ID MATCHES "^Intel")
  add_compile_options($<$<AND:$<COMPILE_LANGUAGE:C>,$<CONFIG:Debug>>:-O0>)
endif()

# --- Fortran compile flags
if(CMAKE_Fortran_COMPILER_ID MATCHES "^Intel")

add_compile_options(
"$<$<COMPILE_LANGUAGE:Fortran>:-warn>"
"$<$<AND:$<COMPILE_LANGUAGE:Fortran>,$<CONFIG:Debug>>:-traceback;-check;-debug>"
)

if(WIN32)
  add_compile_options($<$<AND:$<COMPILE_LANGUAGE:Fortran>,$<CONFIG:Debug>>:/Od>)
else()
  add_compile_options($<$<AND:$<COMPILE_LANGUAGE:Fortran>,$<CONFIG:Debug>>:-O0>)
endif()

elseif(CMAKE_Fortran_COMPILER_ID STREQUAL "GNU")

add_compile_options(
"$<$<COMPILE_LANGUAGE:Fortran>:-Wall;-fimplicit-none;-Wno-maybe-uninitialized>"
"$<$<AND:$<COMPILE_LANGUAGE:Fortran>,$<CONFIG:Debug>>:-Wextra;-fcheck=all;-Werror=array-bounds>"
"$<$<AND:$<COMPILE_LANGUAGE:Fortran>,$<CONFIG:Release>>:-fno-backtrace>"
)

endif()

# --- code coverage
if(coverage)
  include(${CMAKE_CURRENT_LIST_DIR}/Modules/CodeCoverage.cmake)
  append_coverage_compiler_flags()
  set(COVERAGE_EXCLUDES ${PROJECT_SOURCE_DIR}/test)
endif()

# --- clang-tidy
if(tidy)
  find_program(CLANG_TIDY_EXE NAMES "clang-tidy" REQUIRED)
  set(CMAKE_C_CLANG_TIDY ${CLANG_TIDY_EXE})
  set(CMAKE_CXX_CLANG_TIDY ${CLANG_TIDY_EXE})
endif()
