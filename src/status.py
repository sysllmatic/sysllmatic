from enum import Enum

class Status(Enum):
    COMPILATION_ERROR = "Compilation Error"
    RUNTIME_ERROR_OR_TEST_FAILED = "Runtime Error/Test Failed"
    ALL_TEST_PASSED = "All Test Passed"
    PERFORMANCE_IMPROVED = "Performance Improved"