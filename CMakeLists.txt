PROJECT(GR-SPECEST)

CMAKE_MINIMUM_REQUIRED(VERSION 2.8)

IF(UNIX AND EXISTS "/usr/lib64")
	LIST(APPEND BOOST_LIBRARYDIR "/usr/lib64") #fedora 64-bit fix
	SET(LIB_POSTFIX 64)
ENDIF(UNIX AND EXISTS "/usr/lib64")

LIST(APPEND CMAKE_MODULE_PATH ${CMAKE_SOURCE_DIR}/CMake)

###############################################################################
# Search for the required packages
###############################################################################

FIND_PACKAGE(Boost REQUIRED)
FIND_PACKAGE(CppUnit REQUIRED)
FIND_PACKAGE(BLAS REQUIRED)
FIND_PACKAGE(LAPACK REQUIRED)
FIND_PACKAGE(Doxygen)
FIND_PACKAGE(UHD)

FIND_PACKAGE(Armadillo)
INCLUDE(Armadillo)

INCLUDE(FindPkgConfig)
PKG_CHECK_MODULES(GNURADIO_CORE REQUIRED gnuradio-core)
PKG_CHECK_MODULES(GNURADIO_UHD REQUIRED gnuradio-uhd)

INCLUDE_DIRECTORIES(${GNURADIO_CORE_INCLUDE_DIRS})
LINK_DIRECTORIES(${GNURADIO_CORE_LIBRARY_DIRS})

INCLUDE_DIRECTORIES(SYSTEM ${CMAKE_SOURCE_DIR}/src ${CMAKE_BINARY_DIR}/src)

SUBDIRS(src swig python grc apps doc)

#TODO generate the specest.i out of source
CONFIGURE_FILE(${CMAKE_SOURCE_DIR}/swig/specest.i.in ${CMAKE_SOURCE_DIR}/swig/specest.i)
CONFIGURE_FILE(${CMAKE_SOURCE_DIR}/src/config.h.in ${CMAKE_BINARY_DIR}/src/config.h)
CONFIGURE_FILE(${CMAKE_SOURCE_DIR}/gnuradio-specest.pc.in ${CMAKE_BINARY_DIR}/gnuradio-specest.pc @ONLY)

ENABLE_TESTING()

INSTALL(FILES ${CMAKE_BINARY_DIR}/gnuradio-specest.pc DESTINATION ${CMAKE_INSTALL_PREFIX}/lib${LIB_POSTFIX}/pkgconfig)
