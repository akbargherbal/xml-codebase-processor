#!/usr/bin/env python3
"""
Quick test runner for critical tests - Windows compatible
Focuses on fast execution and clear results
"""

import subprocess
import sys
import time
import os


def run_command(command, description, timeout=60):
    """Execute command with timeout protection"""
    print(f"\n=== {description} ===")
    print(f"Running: {' '.join(command)}")

    start_time = time.time()
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding="utf-8",
            errors="replace",  # Handle encoding issues gracefully
        )
        duration = time.time() - start_time

        if result.returncode == 0:
            print(f"✓ SUCCESS in {duration:.2f}s")
            if result.stdout.strip():
                print("Output:", result.stdout[-500:])  # Show last 500 chars
            return True
        else:
            print(f"✗ FAILED after {duration:.2f}s")
            print("STDERR:", result.stderr[-500:])
            if result.stdout:
                print("STDOUT:", result.stdout[-500:])
            return False

    except subprocess.TimeoutExpired:
        print(f"✗ TIMEOUT after {timeout}s")
        return False
    except Exception as e:
        print(f"✗ ERROR: {e}")
        return False


def check_coverage_threshold(coverage_output, threshold=80):
    """Check if coverage meets minimum threshold"""
    try:
        for line in coverage_output.split("\n"):
            if "TOTAL" in line and "%" in line:
                # Extract percentage from line like "TOTAL    100    25    75%"
                parts = line.split()
                for part in parts:
                    if part.endswith("%"):
                        coverage_pct = int(part.rstrip("%"))
                        return coverage_pct >= threshold
    except:
        pass
    return False


def main():
    """Run critical tests with Windows compatibility"""
    print("XML Directory Processor - Quick Test Runner")
    print("=" * 50)

    # Ensure we're in the right directory
    if not os.path.exists("xml_directory_processor.py"):
        print("ERROR: xml_directory_processor.py not found in current directory")
        print(f"Current directory: {os.getcwd()}")
        sys.exit(1)

    # Check if pytest is available
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            print("ERROR: pytest not available")
            sys.exit(1)
    except:
        print("ERROR: Cannot run pytest")
        sys.exit(1)

    # Test phases with coverage
    phases = [
        {
            "name": "Critical - Encoding Tests",
            "command": [
                sys.executable,
                "-m",
                "pytest",
                "tests/critical/test_encoding_handling.py",
                "-v",
                "--tb=short",
                "--timeout=30",
                "--cov=xml_directory_processor",
                "--cov-report=term-missing",
            ],
            "timeout": 45,
        },
        {
            "name": "Critical - Memory Tests (Basic)",
            "command": [
                sys.executable,
                "-m",
                "pytest",
                "tests/critical/test_memory_management.py::TestMemoryManagement::test_token_counting_memory_basic",
                "-v",
                "--tb=short",
                "--timeout=20",
                "--cov=xml_directory_processor",
                "--cov-append",
            ],
            "timeout": 30,
        },
        {
            "name": "Critical - File System Tests",
            "command": [
                sys.executable,
                "-m",
                "pytest",
                "tests/critical/test_filesystem_access.py",
                "-v",
                "--tb=short",
                "--timeout=20",
                "--cov=xml_directory_processor",
                "--cov-append",
            ],
            "timeout": 30,
        },
        {
            "name": "Important - Project Detection",
            "command": [
                sys.executable,
                "-m",
                "pytest",
                "tests/important/test_project_detection.py",
                "-v",
                "--tb=short",
                "--timeout=20",
                "--cov=xml_directory_processor",
                "--cov-append",
            ],
            "timeout": 30,
        },
        {
            "name": "Important - Token Counting",
            "command": [
                sys.executable,
                "-m",
                "pytest",
                "tests/important/test_token_counting.py",
                "-v",
                "--tb=short",
                "--timeout=15",
                "--cov=xml_directory_processor",
                "--cov-append",
                "--cov-report=term-missing",
            ],
            "timeout": 25,
        },
    ]

    results = []
    coverage_met = True

    for phase in phases:
        success = run_command(phase["command"], phase["name"], phase["timeout"])
        results.append((phase["name"], success))

        # Check coverage on final phase
        if "Token Counting" in phase["name"] and success:
            # Get coverage report
            coverage_cmd = [sys.executable, "-m", "coverage", "report"]
            try:
                cov_result = subprocess.run(
                    coverage_cmd, capture_output=True, text=True, timeout=10
                )
                if cov_result.returncode == 0:
                    coverage_met = check_coverage_threshold(
                        cov_result.stdout, threshold=80
                    )
                    if not coverage_met:
                        print("⚠️ WARNING: Code coverage below 80% threshold")
            except:
                pass

        # Stop on critical test failures
        if not success and "Critical" in phase["name"]:
            print(f"\n⛔ STOPPING: Critical test failed: {phase['name']}")
            break

    # Summary
    print(f"\n{'='*50}")
    print("TEST SUMMARY")
    print(f"{'='*50}")

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for name, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status:<8} {name}")

    print(f"\nTotal: {passed}/{total} tests passed")
    if not coverage_met:
        print("⚠️ Coverage: Below 80% threshold")

    if passed == total and coverage_met:
        print("🎉 ALL TESTS PASSED - Ready for production!")
        sys.exit(0)
    elif any("Critical" in name and not success for name, success in results):
        print("⛔ CRITICAL TESTS FAILED - Do not proceed to production")
        sys.exit(2)
    else:
        print("⚠️ SOME TESTS FAILED - Proceed with caution")
        sys.exit(1)


if __name__ == "__main__":
    main()
