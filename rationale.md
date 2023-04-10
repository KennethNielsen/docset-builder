# docset-builder
Build docsets from source code pulled from PyPI information and installed for seal

# Summary

The purpose of this project is to build a command line application to build docsets for Seal directly from PyPI/Github data. The idea was formed after readig [Hyneks blog post on Dash](https://hynek.me/articles/productive-fruit-fly-programmer/), which included a call to action to add more docsets to the respository of additional docsets that can be used by Dash and Seal, but isn't bundled with Dash.

In the article, Hynek mentions scanning the repo for a way to build the documentation and it occured to me that it might be possible to autodetect this and extra information such as an icon file.

After having built the documentation and found the extra information, a docset could be formed with doc2dash and copied in the appropriate location for Dash/Seals data.

A non-ignoreable side benefit of the project would be that if we are to have all the Python projects e.g. I would like to have, in the repo mentioned above, it would mean that it would become very Python heavy and might possibly incur more traffic in the content provider site of the author of Dash that would be good for the future. The somewhat solves this problem, by fetching the data from Github.

Plans to solve this problem is outlined below.

# Project details

## Functionality outline

As a command line app the following explains the flow of a single "install" run of the program, which is the primary function.

**For each of the projects to install docsets for**

* Fetch the project page from PyPI and extract the repository URL
* Clone the repository
* Find the requirements; to extract the documentation system (Sphinx/MkDocs) etc.
* Scan the configuration files of know task automation tools (nox, tox, invoke etc.) to find the documentation build command
* Scan project info (pyproject.toml/setup.py) to look for an icon
* (Possibly search for an icon by name or similar)
* Build the documentation
* Form the docset with doc2dash
* Copy it in location and update a register of installed packages

Besides from `install`, the tools should also have commands such as `list` and `remove`.

## Extra about the code

For me this project is also meant to be an exercise towards functional programming, so it will be pure functions and immutable data structures all the way down.

## Technologies

**click** for the command line interface functionality
**attrs** for immutable data structures
**GitPython** for git interop (still requires git installed and in PATH though)
**rich** for beatiful terminal output
**???** for fetching JSON from PyPI. Normally I would go with requests, but I would like to branch out

## Short design

* Main command line interface with one function per CLI function
* Core with one function per CLI function
* Each of the former calls out to helper functions in modules named by purpose

