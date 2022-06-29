# Copyright 2022 Edgeworx, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import sys
import traceback
from importlib import import_module


def run_tests(test_dir: str) -> bool:
    """
    Runs the test file in the test_dir directory.

    # Arguments
    test_dir (str): The directory containing the test to run.

    # Returns
    bool: True if the test passes, False otherwise.
    """
    sys.stdout.write(f"\rRunning {test_dir} tests...")
    test_name = f"{test_dir}.test"

    test_module = import_module(test_name)

    try:
        sot = test_module.Test()
        sot.act()
        sot.verify()
        sys.stdout.write(f"\rRunning {test_dir} tests... PASSED\n")
    except Exception:
        sys.stdout.write(f"\rRunning {test_dir} tests... FAILED\n")
        _, _, tb = sys.exc_info()
        traceback.print_tb(tb)
        return True
    finally:
        sot.cleanup()

    return False


if __name__ == "__main__":
    #pylint: disable=protected-access
    failed = False
    if len(sys.argv) > 1:
        tests_dir = sys.argv[1]
        failed = run_tests(tests_dir)
    else:
        for test_folder in os.scandir("."):
            if not test_folder.is_dir() or str.startswith(test_folder.name, "__"):
                continue

            failed = failed or run_tests(test_folder.name)

    os._exit(0 if not failed else 1)
