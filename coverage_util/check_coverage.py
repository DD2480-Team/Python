import argparse
import fnmatch
import os
import re
import shutil
import subprocess
from collections import defaultdict
import time

ignored_wildcards = ["project_euler", "__init__.py", "*/tests", "*/__pycache__"]
root_dir = os.path.abspath(__file__).replace("/coverage_util/check_coverage.py", "")
save_file = False
dir_cov = {}


def extend_wildcards():
    """add the contents of the gitignore to ignored_wildcards"""
    global ignored_wildcards
    try:
        ignore = open("../.gitignore")
    except FileNotFoundError:
        pass
    else:
        wildcards = [
            line for line in ignore.read().splitlines() if line and line[0] != "#"
        ]
        ignored_wildcards.extend(wildcards)


def create_dir_file_dict():
    """
    creates a dictionary relating directories to the python files within
    excludes files and directories contained in the gitingore
    as well as those passed in as command line arguments using the flag '-i'

    Returns:
        dict: key: directory path, value, list of pythton files in the directory
    """
    dir_file_dict = defaultdict(list)
    # creates long regex for matching filenames/paths based on the wildcards
    excluded = r"|".join([fnmatch.translate(wc) for wc in ignored_wildcards])
    for dirpath, dirnames, filenames in os.walk(root_dir):
        if re.match(excluded, dirpath):
            continue
        dirnames[:] = [dir for dir in dirnames if not re.match(excluded, dir)]
        filenames[:] = [file for file in filenames if not re.match(excluded, file)]
        [dir_file_dict[dirpath].append(f) for f in filenames if ".py" in f]
    return dir_file_dict


def save_results(dir, result):
    """
    writes the results to the file 'coverage_results.txt' in the
    directory

    Args:
        dir (str): a directory string
        result (str): the string result of running coverage
    """
    result_path = f"{dir}/coverage_results.txt"
    if os.path.exists(result_path):
        with open(result_path, "w") as f:
            f.write(result)
        f.close()
    else:
        with open(result_path, "a") as f:
            f.write(result)
        f.close()


def display_n_worst():
    """
    displays to the terminal the n 'worst' (least covered) directories, and their
    respective coverages as a percent value
    n = 10 by default, or can be passed as an argument using '-n'
    """
    global dir_cov
    if not dir_cov:
        print("No Results")
        return
    dir_cov = {k: v for k, v in sorted(dir_cov.items(), key=lambda item: item[1])}
    k, v = dir_cov.keys(), dir_cov.values()
    width = shutil.get_terminal_size().columns

    print(f"Checked Directory:{root_dir}".center(width, "="))
    max_dir_len = max(len(s) for s in k)
    for i in range(min(n_worst, len(dir_cov))):
        dir = f"{list(k)[i]}"
        percent = f"{list(v)[i]}% coverage"
        print(
            "{}{}{}{}{}".format(
                dir,
                " " * (max_dir_len - len(dir)),
                ":",
                " " * (width - 1 - max_dir_len - len(percent)),
                percent,
            )
        )


def save_directory_results(dir, result):
    """
    parses the result of running coverage checks in the directory (dir)
    to get the percengage coverage, and saves the value to the global dict
    dir_cov. key = dir, value = percent_coverage

    Args:
        dir (str): a directory string
        result (str): the string result of running coverage
    """
    global dir_cov
    dir = dir.replace(root_dir, "")
    # one line monstrosity that parses the stdout-put of
    # 'coverage report' to find the coverage% of the directory
    percent_coverage = int(
        [line for line in result.split("\n") if "TOTAL" in line][0].split(" ")[-1][0:-1]
    )
    dir_cov[dir] = percent_coverage


def run_coverage(dir_file_dict):
    """
    visits every directory that contains python files, and runs three coverage commands
    in the directory
    1) 'coverage run --source=. -m unittest *py'
        checks the unittest coverage of the directory
    2) 'coverage run -a --source=. -m pytest --doctest-module'
        appends the coverage results of doctests in the directory
    3) 'coveage report'
        generates the results of the coverage checks

    If save_file = True (if coverage_check is called with the -s flag set),
    the results of the coverage report are saved in the directory
    where the coverage tests are run

    Otherwise, the only output is written to the terminal by the
    display_n_worst() function which displays the n 'least covered' directories
    n=10 by default but can be set with command line flag '-n'

    Args:
        dir_file_dict (dict): a dictionary with
            key = directories containing python files,
            value = the python files within the directory
    """
    directories = dir_file_dict.keys()
    for dir in directories:
        os.chdir(dir)
        subprocess.run(
            "coverage run --source=. -m unittest *.py",
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        subprocess.run(
            f"coverage run -a --source=. -m pytest --doctest-modules",
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        subprocess_output = subprocess.run(
            "coverage report -m", shell=True, capture_output=True
        )
        result = subprocess_output.stdout.decode()
        if "No" in result:
            print(f"There was an error running coverage tests in {dir}.")
            continue
        if save_file:
            save_results(dir, result)
        save_directory_results(dir, result)
    display_n_worst()


def main():
    extend_wildcards()
    dir_file_dict = create_dir_file_dict()
    run_coverage(dir_file_dict)
    return


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="This is a tool for checking the test coverage of directories."
    )
    parser.add_argument(
        "-o",
        metavar="file",
        nargs="*",
        type=str,
        required=False,
        help="strings of shell-style wildcards of filepaths/ filensames to omit \
                in coverage check  (.gitignore is omitted by default) \
                MUST BE IN SINGLE QUOTES ex. -o '*/tests/*' ",
    )
    parser.add_argument(
        "-d",
        metavar="directory",
        type=str,
        required=False,
        help="the relative path of the directory to be checked \
                e.g. -d datastructures/binary_tree",
    )
    parser.add_argument(
        "-n",
        metavar="num_results",
        type=int,
        required=False,
        default=10,
        help="show the n least covered directories, default = 10",
    )
    parser.add_argument(
        "-s", action="store_true", help="save results of coverage in each directory"
    )
    args = parser.parse_args()
    if args.d:
        root_dir += f"/{args.d.strip('/')}"
    if args.o:
        ignored_wildcards.extend(args.o)
    save_file = args.s
    n_worst = args.n
    main()
