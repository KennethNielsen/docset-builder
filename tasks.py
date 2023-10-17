# type: ignore
"""This file contains the tasks defined for invoke"""
import os
import platform
import shutil
from os import listdir
from pathlib import Path

# The first time invoke is called, it is to install dependencies, so toml is not yet installed
try:
    import toml
except ImportError:
    toml = None

# The first time invoke is called, it is to install dependencies, so at that point rich is not
# installed yet
try:
    from rich import print as rprint
except ImportError:
    rprint = print
from invoke import task

# Undocumented way to force color in mypy
my_vars = {"MYPY_FORCE_COLOR": "1"}
os.environ.update(my_vars)


THIS_DIR = Path(__file__).parent.resolve()
SOURCE_DIR = THIS_DIR / "src"
ZILIEN_QT_DIR = SOURCE_DIR / "docset_builder"
TEST_DIR = THIS_DIR / "tests"


# Checking tasks


@task(aliases=("ruff",))
def lint(context, fix=False):
    """Lint the source code with ruff"""
    rprint("\n[bold]Linting...")
    with context.cd(THIS_DIR):
        arg_string = ""
        if fix:
            arg_string += " --fix"
        result = context.run(f"ruff {SOURCE_DIR} {arg_string}")
        if result.return_code == 0:
            rprint("[bold green]Files linted. No errors.")
    return result.return_code


@task(aliases=("mypy", "tc"))
def type_check(context):
    """Run the static type checker on the source code"""
    rprint("\n[bold]Checking types...")
    with context.cd(THIS_DIR):
        result = context.run(f"mypy src/")
        if result.return_code == 0:
            rprint("[bold green]Files type checked. No errors.")
    return result.return_code


@task(aliases=("fc", "black"))
def format_code(context):
    """Format all of zilien_qt with black"""
    context.run(f"black {SOURCE_DIR}")


@task(aliases=("check_black", "cb", "ccf"))
def check_code_format(context):
    """Check that the code is black formatted"""
    rprint("\n[bold]Checking code style...")
    with context.cd(THIS_DIR):
        result = context.run(f"black --check {SOURCE_DIR}")
        if result.return_code == 0:
            rprint("[bold green]Code format checked. No issues.")
    return result.return_code


@task(
    aliases=["test", "pytest", "t"],
    help={
        "color": "Whether to display pytest output in color, 'yes' or 'no'",
        "verbose": "Makes the pytest output verbose",
        "s_no_capture": (
            "Prevents pytest from capturing output (making it possible to see prints etc.)"
        ),
        "k_only_run": (
            "Only run tests that matches the expression in STRING. See the help for pytest's `-k` "
            "option to read more about the options for expression"
        ),
        "x_exit_on_first_error": "Make pytest exit on first error",
    },
)
def tests(
    context,
    color="yes",
    verbose=False,
    s_no_capture=False,
    k_only_run=None,
    x_exit_on_first_error=False,
):
    """Run tests with pytest"""
    if platform.system() == "Windows":
        color = "no"
    args = []
    if verbose:
        args.append("--verbose")
    if s_no_capture:
        args.append("-s")
    if k_only_run:
        args.append(f"-k {k_only_run}")
    if x_exit_on_first_error:
        args.append("-x")
    rprint("\n[bold]Testing...")
    with context.cd(THIS_DIR):
        result = context.run(f'pytest --color "{color}" {" ".join(args)} {TEST_DIR}')
        if result.return_code == 0:
            rprint("[bold green]All tests passed")
    return result.return_code


@task(aliases=["check", "c"])
def checks(context):
    """Check code with black, flake8, mypy and run tests"""
    combined_return_code = check_code_format(context)
    combined_return_code += lint(context)
    combined_return_code += type_check(context)
    # combined_return_code += tests(context)
    if combined_return_code == 0:
        rprint()
        rprint(r"+----------+")
        rprint(r"| All good |")
        rprint(r"+----------+")
    else:
        rprint()
        rprint(r"+---------------------+")
        rprint(r"| [bold red]Some checks [blink]FAILED![/blink][/bold red] |")
        rprint(r"| [bold]Check output above[/bold]  |")
        rprint(r"+---------------------+")


# Setup tasks


@task(aliases=("pip", "deps"))
def dependencies(context):
    """Install all requirements and development requirements"""
    global toml
    if toml is None:
        context.run("python -m pip install toml")
        import toml
    with context.cd(THIS_DIR):
        context.run("python -m pip install --upgrade pip")
        data = toml.load(THIS_DIR / "pyproject.toml")
        context.run(f"pip install --upgrade {' '.join(data['project']['dependencies'])}")
        context.run(
            "pip install --upgrade "
            f"{' '.join(data['project']['optional-dependencies']['dev'])}"
        )


@task
def setup(context):
    """Install requirements and pre-commmit hook"""
    dependencies(context)
    with context.cd(THIS_DIR):
        context.run("pre-commit install --overwrite --hook-type pre-commit")
        context.run("pre-commit install --overwrite --hook-type pre-push")
        context.run("python -m pip install --upgrade -e .")


# Maintenance tasks
@task
def clean(context, docbuilds=False, pre_commit_envs=False, dryrun=False):
    """Clean temporary files and optionally builds and doc builds

    Args:
        docbuilds (bool): Whether to also clean out doc builds
        pre_commit-envs (bool): Whether to also clean out the pre-commit virtual environments
        dryrun (bool): Show which files would be deleted, but do not actually do it (does not
            affect dryrun)

    """
    if pre_commit_envs:
        with context.cd(THIS_DIR):
            context.run("pre-commit clean")

    prefix = "Would remove " if dryrun else "Removing "

    # Add build dirs and/or doc build dirs to clean patterns if requested
    patterns = []
    if docbuilds:
        patterns += [
            Path("docs") / "docbuilds" / "_build",
        ]

    # Add all sorts of temporary files to clean patterns
    patterns += [
        "**/__pycache__",
        "**/.mypy_cache",
        "**/*.pyc",
        "**/*.pyo",
        "**/dist",
    ]
    for pattern in patterns:
        # A pattern is either a glob pattern (str), or a relative path (Path)
        if isinstance(pattern, Path):
            patterns_to_iterate_over = [THIS_DIR / pattern]
        else:
            patterns_to_iterate_over = THIS_DIR.glob(pattern)

        for file_ in patterns_to_iterate_over:
            if ".venv" in str(file_):
                continue
            if not file_.exists():
                continue
            if file_.is_dir():
                print(prefix + "dir:", file_.relative_to(THIS_DIR))
                if not dryrun:
                    shutil.rmtree(file_)
            else:
                print(prefix + "file:", file_.relative_to(THIS_DIR))
                if not dryrun:
                    file_.unlink()

    rprint()
    rprint("--- build dir after clean ----------------------------------------")
    try:
        rprint(listdir("build"))
    except FileNotFoundError:
        rprint("'build' doesn't exist")
    rprint("--- build dir after clean ----------------------------------------")
    rprint()

    try:
        build_empty = not listdir("build")
    except FileNotFoundError:
        build_empty = True

    if not build_empty:
        print("Build not clean after attempting to clean it")
        raise SystemExit(1)

    return build_empty


@task(aliases=["cov"])
def coverage(context, show_missing=False):
    """Collect and display tests coverage"""
    if show_missing:
        report_type = "term-missing"
    else:
        report_type = "term"
    with context.cd(THIS_DIR):
        context.run(f"pytest --cov-report {report_type} --cov=src/zilien_qt/ tests/")


@task
def itch(context, verbose=False):
    """Build the docsets for the projects in the my-own-itch-list.txt file"""
    with context.cd(THIS_DIR):
        with open("my-own-itch-list.txt") as file_:
            for application in file_:
                if application.startswith("#"):
                    continue
                rprint(f"[b]# Try to build {application}[/b]")
                ret = context.run(
                    f"python -m docset_builder.main install -n {'-v' if verbose else ''} -b "
                    f"{application}")
                rprint("[b green] -> OK[b green]")
                print()
