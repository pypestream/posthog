import re
import sys

def extract_failed_tests(log_file_path):
    fail_pattern = re.compile(r"FAILED (.*) -")
    failed_tests = []

    with open(log_file_path, 'r') as file:
        for line in file:
            match = fail_pattern.search(line)
            if match:
                failed_tests.append(match.group(1))

    return failed_tests

def create_pytest_command(failed_tests):
    return "pytest -k " + " or ".join(f'"{test}"' for test in failed_tests)

def main():
    if len(sys.argv) != 2:
        print("Usage: python script.py <path_to_log_file>")
        sys.exit(1)

    log_file_path = sys.argv[1]
    failed_tests = extract_failed_tests(log_file_path)
    command = create_pytest_command(failed_tests)
    print(command)

if __name__ == "__main__":
    main()