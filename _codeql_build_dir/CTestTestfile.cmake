# CMake generated Testfile for 
# Source directory: /home/runner/work/os-main-8/os-main-8
# Build directory: /home/runner/work/os-main-8/os-main-8/_codeql_build_dir
# 
# This file includes the relevant testing commands required for 
# testing this directory and lists subdirectories to be tested as well.
add_test(kolibri_tests "/home/runner/work/os-main-8/os-main-8/_codeql_build_dir/kolibri_tests")
set_tests_properties(kolibri_tests PROPERTIES  _BACKTRACE_TRIPLES "/home/runner/work/os-main-8/os-main-8/CMakeLists.txt;204;add_test;/home/runner/work/os-main-8/os-main-8/CMakeLists.txt;0;")
add_test(ks_compiler_roundtrip "/usr/local/bin/cmake" "-Dks_compiler=/home/runner/work/os-main-8/os-main-8/_codeql_build_dir/ks_compiler" "-P" "/home/runner/work/os-main-8/os-main-8/_codeql_build_dir/ks_compiler_roundtrip.cmake")
set_tests_properties(ks_compiler_roundtrip PROPERTIES  _BACKTRACE_TRIPLES "/home/runner/work/os-main-8/os-main-8/CMakeLists.txt;209;add_test;/home/runner/work/os-main-8/os-main-8/CMakeLists.txt;0;")
add_test(kolibri_node_custom_key_inline "/usr/bin/python3.12" "/home/runner/work/os-main-8/os-main-8/tests/run_kolibri_node_hmac.py" "/home/runner/work/os-main-8/os-main-8/_codeql_build_dir/kolibri_node" "inline")
set_tests_properties(kolibri_node_custom_key_inline PROPERTIES  _BACKTRACE_TRIPLES "/home/runner/work/os-main-8/os-main-8/CMakeLists.txt;216;add_test;/home/runner/work/os-main-8/os-main-8/CMakeLists.txt;0;")
add_test(kolibri_node_custom_key_file "/usr/bin/python3.12" "/home/runner/work/os-main-8/os-main-8/tests/run_kolibri_node_hmac.py" "/home/runner/work/os-main-8/os-main-8/_codeql_build_dir/kolibri_node" "file")
set_tests_properties(kolibri_node_custom_key_file PROPERTIES  _BACKTRACE_TRIPLES "/home/runner/work/os-main-8/os-main-8/CMakeLists.txt;221;add_test;/home/runner/work/os-main-8/os-main-8/CMakeLists.txt;0;")
add_test(kolibri_node_usage "/home/runner/work/os-main-8/os-main-8/_codeql_build_dir/kolibri_node" "--help")
set_tests_properties(kolibri_node_usage PROPERTIES  _BACKTRACE_TRIPLES "/home/runner/work/os-main-8/os-main-8/CMakeLists.txt;228;add_test;/home/runner/work/os-main-8/os-main-8/CMakeLists.txt;0;")
add_test(kolibri_indexer_usage "/home/runner/work/os-main-8/os-main-8/_codeql_build_dir/kolibri_indexer")
set_tests_properties(kolibri_indexer_usage PROPERTIES  WILL_FAIL "TRUE" _BACKTRACE_TRIPLES "/home/runner/work/os-main-8/os-main-8/CMakeLists.txt;230;add_test;/home/runner/work/os-main-8/os-main-8/CMakeLists.txt;0;")
add_test(kolibri_queue_usage "/home/runner/work/os-main-8/os-main-8/_codeql_build_dir/kolibri_queue")
set_tests_properties(kolibri_queue_usage PROPERTIES  WILL_FAIL "TRUE" _BACKTRACE_TRIPLES "/home/runner/work/os-main-8/os-main-8/CMakeLists.txt;233;add_test;/home/runner/work/os-main-8/os-main-8/CMakeLists.txt;0;")
add_test(kolibri_sim_usage "/home/runner/work/os-main-8/os-main-8/_codeql_build_dir/kolibri_sim")
set_tests_properties(kolibri_sim_usage PROPERTIES  WILL_FAIL "TRUE" _BACKTRACE_TRIPLES "/home/runner/work/os-main-8/os-main-8/CMakeLists.txt;236;add_test;/home/runner/work/os-main-8/os-main-8/CMakeLists.txt;0;")
