from setuptools import setup, find_packages

setup(
    name="raindrop-todoist-syncer",
    version="0.1.0",
    description="Converts favourited Raindrops into tasks in Todoist.",
    author="Chris Billows",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    entry_points={
        "console_scripts": [
            "raindrop-todoist-syncer=raindrop_todoist_syncer.main:main",
            "rts=raindrop_todoist_syncer.main:main",
        ],
    },
)
