# My Climate Dashboard
The purpose of this project is to create a dashboard that displays a user's climate data in one place. 
The dashboard is expected to contain multiple features, but development was first focused on delivering hourly
information regarding the status of power being delivered from their local Balancing Authority.  If the power is 
"greener" meaning containing more green sources than normal, an alert is sent to the user indicating that 
it is a better time to use power, for example plug in their electric vehicle.  If the power is less "green", an alert
tells the user to shed power loads.

This project was created as part of the team's final project in the `Terra.do` class
https://www.terra.do/climate-education/cohort-courses/software-stacks-in-climate-tech/
This project was developed by modifying code provided in class.

## Installation/Build Instructions

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

The BA data requires an API key in order to run it. You can generate the 
API key on the EIA website here: https://www.eia.gov/opendata/register.php

To run the app from the command line, you need to add the API key to your bash terminal session. 
You can do this by adding this line to your `.bashrc` file:

```commandline
export EIA_API_KEY=<enter_api_key_here>
```

The email feature requires a sending Google email account plus Oauth to be setup.  It is recommended you
create a separate email account for sending the alerts, rather than using a personal account.

To setup the oauth connection to the Gmail API perform the following steps in your sending account:
https://developers.google.com/gmail/api/quickstart/python

Add the `credentials.json` file to the `my_climate_dashboard_backend` folder in this repo.
Then run the `my_climate_dashboard_backend\google_quickstart.py` code to authenticate your email account. 

## Test API
```commandline
curl -i -H "Content-Type: application/json" -X POST -d '{"ba_name": "psei"}' 127.0.0.1:5000/my-climate-dashboard/green-energy-stats
```

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



