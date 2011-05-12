EXECUTE_PROCESS(
    COMMAND ${PYTHON_EXECUTABLE} -c "from distutils import sysconfig; print sysconfig.get_python_lib(prefix='${CMAKE_INSTALL_PREFIX}')"
    OUTPUT_VARIABLE PYTHON_DIR OUTPUT_STRIP_TRAILING_WHITESPACE
)


################################################################################
# Add your tests here (don't put the qa_ ) in front
################################################################################

SET(PYTHON_QA
	specest_gendpss
	specest_burg
	specest_esprit
	specest_esprit_spectrum_vcf
	specest_fcov
	specest_fmcov
	specest_mtm
	specest_welch
	specest_vectormanip)

################################################################################
# Here we add the tests you added above
################################################################################

FOREACH(testcase ${PYTHON_QA})
ADD_TEST(${testcase}_py
	${CMAKE_CURRENT_SOURCE_DIR}/test_runner.py --test ${CMAKE_CURRENT_SOURCE_DIR}/qa_${testcase}.py --path ${CMAKE_BINARY_DIR}/swig)
ENDFOREACH(testcase ${PYTHON_QA})

IF(ARMADIOLLO_FOUND)
	ADD_TEST(py_specest_music
		${CMAKE_CURRENT_SOURCE_DIR}/test_runner.py --test ${CMAKE_CURRENT_SOURCE_DIR}/qa_specest_music.py --path ${CMAKE_BINARY_DIR}/swig)
ENDIF(ARMADIOLLO_FOUND)


############################$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$#
# Here we add our python sourcecode that needs to be installed
############################$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$#

#TODO add all
SET(SPECEST_PY_SRCS
	__init__.py
	specest_mtm.py
	specest_gendpss.py)

INSTALL(FILES ${SPECEST_PY_SRCS} DESTINATION ${PYTHON_DIR}/specest)
