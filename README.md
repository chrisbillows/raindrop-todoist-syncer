# Raindrop-Todoist-Syncer

Raindrop-Todoist-Syncer is a Python script designed to convert any favourited Raindrop into a task in Todoist. It is intended to be run as a background cron job.

> VERY MUCH A WORK IN PROGRESS

**Note: This is primarily a learning project for trying to explore more professional development practices, including:**
- **Documenting with Google python style-guide docstrings"**
- **Debugging with ipdb**
- **Type hinting** 
- **Proper error handling** 
- **Unit testing** 
- **Static testing/linting** 
- **Logging** 
- **Use of pre-commit hooks to enforce styling/tests etc**
- **Basic CI/CD for automated testing**

## Features

- Automatically syncs favorited Raindrops to Todoist tasks
- Runs as a background cron job

## Getting Started

These instructions will guide you through the process of setting up and running Raindrop-Todoist-Syncer on your own machine.

### Prerequisites

* Python 3.10 or higher
* A Raindrop account with favorited items and 
* A Todoist account

### Installation

1. Clone the repository: `git clone https://github.com/yourusername/raindrop-todoist-syncer.git`
2. Navigate into the project directory: `cd raindrop-todoist-syncer`
3. Install the required dependencies: `pip install -r requirements.txt`
4. Configure the application by editing the configuration file with your own Raindrop and Todoist account details

### API Access

To run this script requires API access to Todoist and Raindrop. For both applications
API access allows full access to view and modify your data. API tokens should be 
treated like a password and not shared.

Raindrop-Todoist-Syncer runs locally on your machine and no information is shared, but,
if in doubt, always CHECK WITH A GROWN-UP! Or Chat GPT. :0)

#### Todoist API

In Todoist, go to "Integrations" and under "Developer" copy your API key.

Save it to the .env file as:

TODOIST_API_KEY = 'abc123'

#### Raindrop API

Use of the Raindrop API requires an Oauth token.

First go to "Settings", "Integrations" and, under "For Developers", select "Create new app". 
Save your client ID and client secret to .env in the root directory as:

RAINDROP_CLIENT_ID = 'abc123'
RAINDROP_CLIENT_SECRET = 'def5456'
 
To get the oauth token follow the steps here:

https://developer.raindrop.io/

The script will handle this automatically in future.

### Usage

Currently:

1. Run the script: `python main.py`
2. The script will automatically sync any favorited Raindrops to Todoist tasks - AS LONG
AS THE TERMINAL REMAINS OPEN.  
3. This will run as a background cron job once I figure out error handling for SIGTERM, SIGKILL interrupts.

## Contact

If you want to contact me you can reach me at [christopherbillows@gmail.com](mailto:christopherbillows@gmail.com). I am currently seeking an entry level role.


# License

This project is licensed under the terms of the MIT license.




