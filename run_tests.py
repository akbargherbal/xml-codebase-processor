#!/usr/bin/env python3
"""
Test execution script for XML Directory Processor
Implements the testing strategy with phased execution and early warning system
"""

import subprocess
import sys
import time
import os
import psutil
import argparse


class TestRunner:
    def __init__(self, verbose=False, log_file="test_execution.log"):
        self.verbose = verbose
        self.log_file = log_file
        self.results = {
            "critical": {"passed": 0, "failed": 0, "errors": []},
            "important": {"passed": 0, "failed": 0, "errors": []},
            "integration": {"passed": 0, "failed": 0, "errors": []},
            "performance": {"passed": 0, "failed": 0, "errors": []},
        }
        self.coverage_met = True

    def log(self, message):
        """Log message to both console and file"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        if self.verbose:
            print(log_entry)
        with open(self.log_file, "a") as f:
            f.write(log_entry + "\n")

    def check_coverage_threshold(self, coverage_output, threshold=80):
        """Check if coverage meets minimum threshold"""
        try:
            for line in coverage_output.split("\n"):
                if "TOTAL" in line and "%" in line:
                    parts = line.split()
                    for part in parts:
                        if part.endswith("%"):
                            coverage_pct = int(part.rstrip("%"))
                            return coverage_pct >= threshold
        except:
            pass
        return False

    def run_pytest_command(self, command, description):
        """Execute pytest command and capture results"""
        self.log(f"Starting: {description}")
        self.log(f"Command: {' '.join(command)}")
        start_time = time.time()
        try:
            result = subprocess.run(
                command, capture_output=True, text=True, timeout=300
            )
            duration = time.time() - start_time
            if result.returncode == 0:
                self.log(f"SUCCESS: {description} in {duration:.2f}s")
                return {"success": True, "output": result.stdout, "errors": []}
            else:
                self.log(f"FAILURE: {description}")
                self.log(f"STDERR: {result.stderr}")
                errors = [
                    line.strip()
                    for line in result.stdout.split("\n")
                    if "FAILED" in line or "ERROR" in line
                ]
                return {
                    "success": False,
                    "output": result.stdout,
                    "stderr": result.stderr,
                    "errors": errors,
                }
        except Exception as e:
            self.log(f"ERROR: {description} - {str(e)}")
            return {"success": False, "errors": [str(e)]}

    def phase_1_critical_tests(self):
        """Execute Phase 1: Critical tests"""
        self.log("=== PHASE 1: CRITICAL TESTS ===")
        command = [
            "python",
            "-m",
            "pytest",
            "tests/critical/",
            "-v",
            "--tb=short",
            "--cov=xml_directory_processor",
            "--cov-report=term-missing",
        ]
        result = self.run_pytest_command(command, "Critical Tests")
        if result["success"]:
            self.results["critical"]["passed"] = 1
            return True
        else:
            self.results["critical"]["failed"] = 1
            self.results["critical"]["errors"] = result["errors"]
            return False

    def phase_2_important_tests(self):
        """Execute Phase 2: Important tests"""
        self.log("=== PHASE 2: IMPORTANT TESTS ===")
        command = [
            "python",
            "-m",
            "pytest",
            "tests/important/",
            "-v",
            "--cov=xml_directory_processor",
            "--cov-append",
        ]
        result = self.run_pytest_command(command, "Important Tests")
        if result["success"]:
            self.results["important"]["passed"] = 1
        else:
            self.results["important"]["failed"] = 1
            self.results["important"]["errors"] = result["errors"]

    def phase_3_integration_tests(self):
        """Execute Phase 3: Integration tests"""
        self.log("=== PHASE 3: INTEGRATION TESTS ===")
        command = [
            "python",
            "-m",
            "pytest",
            "tests/integration/",
            "-v",
            "--cov=xml_directory_processor",
            "--cov-append",
            "--cov-report=term-missing",
        ]
        result = self.run_pytest_command(command, "Integration Tests")
        if result["success"]:
            self.results["integration"]["passed"] = 1

            # Check coverage after integration tests
            coverage_cmd = ["python", "-m", "coverage", "report"]
            try:
                cov_result = subprocess.run(
                    coverage_cmd, capture_output=True, text=True, timeout=10
                )
                if cov_result.returncode == 0:
                    self.coverage_met = self.check_coverage_threshold(
                        cov_result.stdout, threshold=80
                    )
                    if not self.coverage_met:
                        self.log("WARNING: Code coverage below 80% threshold")
            except Exception as e:
                self.log(f"Error checking coverage: {str(e)}")
        else:
            self.results["integration"]["failed"] = 1
            self.results["integration"]["errors"] = result["errors"]

    def generate_report(self):
        """Generate final test report"""
        self.log("=== FINAL TEST REPORT ===")
        total_passed = sum(p["passed"] for p in self.results.values())
        total_failed = sum(p["failed"] for p in self.results.values())
        self.log(f"Total Passed: {total_passed}, Total Failed: {total_failed}")

        if not self.coverage_met:
            self.log("⚠️ Coverage below 80% threshold")

        if self.results["critical"]["failed"] > 0:
            self.log("✗ NOT READY: Critical tests failed.")
            return "FAILED"
        elif self.results["important"]["failed"] > 0 or not self.coverage_met:
            self.log("⚠️ PROCEED WITH CAUTION: Important tests failed or coverage low.")
            return "CAUTION"
        else:
            self.log("✓ READY FOR PRODUCTION: All critical and important tests passed.")
            return "READY"

    def run_full_test_suite(self):
        """Execute the complete test suite"""
        with open(self.log_file, "w") as f:
            f.write(f"Test execution started at {time.strftime('%Y-%m-%d %H:%M:%S')}\n")

        if not self.phase_1_critical_tests():
            self.log("Critical tests failed - stopping execution.")
            return self.generate_report()

        self.phase_2_important_tests()
        self.phase_3_integration_tests()
        return self.generate_report()


def main():
    parser = argparse.ArgumentParser(
        description="Run XML Directory Processor Test Suite"
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument(
        "--log-file", default="test_execution.log", help="Log file path"
    )
    args = parser.parse_args()
    runner = TestRunner(verbose=args.verbose, log_file=args.log_file)
    status = runner.run_full_test_suite()
    if status == "FAILED":
        sys.exit(2)
    elif status == "CAUTION":
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
