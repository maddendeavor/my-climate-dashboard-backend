[![testcoverage](/doc/testcoverage_badge.svg)](/doc/testcoverage.txt)
[![maintainability](/doc/maintainability_badge.svg)](/doc/maintainability.txt)
[![docstring_coverage](/doc/docstringcoverage_badge.svg)](/doc/docstringcoverage.txt)
[![doc_style](https://img.shields.io/badge/%20style-numpy-459db9.svg)](https://numpydoc.readthedocs.io/en/latest/format.html)

# My Climate Dashboard
The purpose of this project is to create a dashboard that displays a user's climate data in one place. 
The dashboard is expected to contain multiple features, but development was first focused on delivering hourly
information regarding the status of power being delivered from their local Balancing Authority.  If the power is 
"greener" meaning containing more green sources than normal, an alert is sent to the user indicating that 
it is a better time to use power, for example plug in their electric vehicle.  If the power is less "green", an alert
tells the user to shed power loads.

## Installation/Build Instructions
In order for Github Actions/Workflows to run you will need to create a `GITFLOW_PAT`
personal access token in Github that gives access rights to the repo. 
You then need to add this as an `Actions` secret to the github respository.
Note the same PAT needs to be added to the dependabot secrets.

* First Create virtual environment
```commandline
python3 -m venv .venv
source .venv/bin/activate (linux) or source .venv/Scripts/activate (windows)
pip install -e .[dev]
```

* Run the flask app by opening a command window and typing the following
```commandline
flask --app my_climate_dashboard_backend run --debug
```
## Test API
curl -i -H "Content-Type: application/json" -X POST -d '{"ba_name": "psei"}' 127.0.0.1:5000/my-climate-dashboard/green-energy-stats


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



