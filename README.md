[![testcoverage](/doc/testcoverage_badge.svg)](/doc/testcoverage.txt)
[![maintainability](/doc/maintainability_badge.svg)](/doc/maintainability.txt)
[![docstring_coverage](/doc/docstringcoverage_badge.svg)](/doc/docstringcoverage.txt)
[![doc_style](https://img.shields.io/badge/%20style-numpy-459db9.svg)](https://numpydoc.readthedocs.io/en/latest/format.html)

# Project Name
Overview that explains **what** this project is about.

## Installation/Build Instructions
If appropriate, explain **how** to install/build this project.

In order for Github Actions/Workflows to run you will need to create a `GITFLOW_PAT`
personal access token in Github that gives access rights to the repo. 
You then need to add this as an `Actions` secret to the github respository.
Note the same PAT needs to be added to the dependabot secrets.

## References
* Links to where the reference documents live, including API reference docs.
* Links to important things like the JIRA project associated with this git project.

## Release History
If appropriate, describe the revision history.

## Contributing
* To contribute to the repository use the following:
```commandline
git clone <ENTER SSH HERE>
cd reponame
git lfs install
git checkout -b feature/feature_name
git add <files>
git commit -m "Add my feature"
git push origin feature/feature_name
```

* Create virtual environment
```commandline
python3 -m venv .venv
source .venv/bin/activate (linux) or source .venv/Scripts/activate (windows)
```

