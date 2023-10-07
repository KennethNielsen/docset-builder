
# Next project objectives

- [x] Implement preferentially checking out last tagged release
- [ ] Implement checkout of specific version
- [x] Fix docset build to use found index page
- [x] Implement tests of information collection
- [ ] Implement CI with GithubActions
- [x] Hide logs behind -v flag
- [ ] Prettify output with rich
- [ ] Unify abbrev names (e.g. information vs. info)
- [ ] Change so docsets are built in permanent data dir and linked into install dir
- [ ] Refuse to install if docset is there, unless --upgrade and the installed docset is ours 

# Longer term objectives

- [ ] Look into a good Python package for git archive manipulation
- [ ] Look into a good Python package for virtual environment handling or look into leveraging 
      support already in e.g. tox

# Supported package goal list

To start with, the packages in the "my-own-itch-list.txt".

- [ ] arrow
- [ ] pytest
- [ ] attrs
- [ ] flask
- [ ] requests
- [ ] pyserial
- [ ] appdirs, NO has no docs
- [ ] numpy
- [ ] psutil
- [ ] cx_Freeze
- [ ] invoke
- [ ] toml
- [ ] pathvalidate
- [ ] pyqtgraph
- [ ] rich
- [ ] pyyaml
- [ ] black
- [ ] ruff

Then proceed with pypi top 100.