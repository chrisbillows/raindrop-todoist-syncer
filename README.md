# Raindrop-Todoist-Syncer

Convert any favourited Raindrop into a task in Todoist.

> VERY MUCH A WORK IN PROGRESS

**Note: This was originally created as a learning project. I still use it - it works -
but it's a mess!**

## Features

- Automatically syncs favorited Raindrops to Todoist tasks
- Can run in the automatically in the background via launchctl
- Stop leaving browser windows open as "todos" - Raindrop and favourite them and they
  appear in Todoist to be scheduled

## Getting Started

These instructions will guide you through the process of setting up and running
Raindrop-Todoist-Syncer on your own machine.

### Prerequisites

* Python 3.10 or higher
* A Raindrop account with favorited items and
* A Todoist account
* Mac only, tested on Sequoia (it relies on launchctl / plist files for automation)

### Installation

1. Installation with the uv package manager (or pipx) is recommended. (See
[here](https://docs.astral.sh/uv/getting-started/installation/) for how to install uv)
1. Run `uv tool install git+https://github.com/chrisbillows/raindrop-todoist-syncer.git`
1. Confirm the installation by running `which rts`. You should see something like:
```
    /Users/<your_user_name>/.local/bin/rts
```
1. Run the command `rts --help` and the Raindrop Todoist Syncer CLI help should appear.

The package now needs to be configured.

### `.env` file

The package requires the following file:

```
    ~/.config/rts/.env
```

To create it run this command:

```bash
    mkdir -p "$HOME/.config/rts" && touch "$HOME/.config/rts/.env"
```

Open the empty file

```
open "$HOME/.config/rts/.env"  # Uses TextEdit. Can use nano with `nano`, VScode with `code` etc.
```


### API Access Tokens

Raindrop Todoist Syncer requires API access to Todoist and Raindrop.

This is configured by adding API tokens to the `.env` file.

! > WARNING
> For both applications API access allows full access to view and modify your data. API
tokens should be treated like a password and not shared.

Raindrop-Todoist-Syncer runs locally on your machine and no information is shared, but,
if in doubt, always CHECK WITH A GROWN-UP! Or Chat GPT. :0)

#### Todoist API

In Todoist, go to "Integrations" and under "Developer" copy your API key.

Save it to the .env file as:

```
TODOIST_API_KEY = 'abc123'
```

#### Raindrop API

Use of the Raindrop API requires an Oauth token.

First go to "Settings", "Integrations" and, under "For Developers", select "Create new
app". Save your client ID and client secret to .env in the root directory as:

```
RAINDROP_CLIENT_ID = 'abc123'
RAINDROP_CLIENT_SECRET = 'def5456'
```

To get the oauth token follow the steps here:

https://developer.raindrop.io/

You should end up with:

```
RAINDROP_REFRESH_TOKEN = 'abc123'
RAINDROP_ACCESS_TOKEN = 'def456'
```

### Usage

####  Collect


#### Automate syncing

Raindrop Todoist Syncer can run in the background. To enable this run:

`rts automate_enable`

This will install a plist file in ~/LaunchAgents and it will tell OSX to run the script
in the background every 5 minutes.

To disable this run:

`rts automate_enable`

## Uninstall

You can remove the package via uv with the command `uv`

All logs and application files are stored in `~/.config/rts`.  No other files are
or clutter are added to your machine.

You can delete all Raindrop Todoist Syncer files with `rm -rf ~/.config/rts`

## Contact

If you want to contact me you can reach me at [christopherbillows@gmail.com](mailto:christopherbillows@gmail.com).

# License

This project is licensed under the terms of the MIT license.
