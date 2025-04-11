from datetime import datetime
import json
import os

from typing import Any

from loguru import logger

from raindrop_todoist_syncer.config import UserConfigProtocol
from raindrop_todoist_syncer.rd_object import Raindrop


class DatabaseManager:
    """
    A class to manage JSON files which serve as the database for the project.

    The database stores basic information about every favourited raindrop that has been
    processed and successfully created as a task in Todoist.

    The database is stored in 'database' in the project root.

    A metafile, stored in 'metafile' in the project root, tracks the path to the most
    recent database version.

    Parameters
    ----------
    user_config : UserConfig
        A user config.

    Attributes
    ----------
    database_directory : str
        Directory where the database files are located.
    metafile_directory : str
        Directory where the metafile is located.
    metafile_path : str
        Path of the metafile.
    """

    def __init__(self, user_config: UserConfigProtocol):
        self.user_config = user_config
        self.database_directory = self.user_config.database_dir
        self.metafile_directory = self.user_config.metafile_dir
        self.metafile_path = self.user_config.metafile_path

    def update_database(self, new_favourited_raindrop_objects: list[Raindrop]) -> bool:
        """
        Update the database with new favourite raindrop objects and update the metafile.

        Parameters
        ----------
        new_favourited_raindrop_objects : List[Raindrop]
            List of Raindrop objects that are newly favourited.

        Returns
        -------
        bool
            True if database and metafile are updated successfully.
        """

        rds_to_add = []
        for raindrop_object in new_favourited_raindrop_objects:
            rds_to_add.append(raindrop_object.to_dict())

        db: dict[str, list[dict[str, Any]]] = self.get_latest_database()

        previous_rds: list = db["Processed Raindrops"]
        logger.info(f"Previous db length {len(previous_rds)}")

        db["Processed Raindrops"] = previous_rds + rds_to_add
        logger.info(f"New db length {len(db['Processed Raindrops'])}")

        file_number = len(os.listdir(self.database_directory)) + 1

        output_file = (
            f"{file_number:03d}_processed_raindrops_"
            f"{datetime.now().strftime('%Y%m%d_%H%M')}.json"
        )

        new_database_file_name = os.path.join(self.database_directory, output_file)

        with open(new_database_file_name, "w") as f:
            json.dump(db, f, indent=4)
        logger.info(f"New db file created: {new_database_file_name}")

        with open(self.metafile_path, "w") as metafile:
            metafile.write(new_database_file_name)
        logger.info("Metafile updated")

    def get_latest_database(self) -> dict[str, Any]:
        """
        Load the most recent JSON database into memory or, if none exists,
        create a new, empty, database (with "Processed Raindrops" as the key, and an
        empty list as the value).

        Returns
        -------
        Dict[str, Any]
            The latest JSON database.
        """

        os.makedirs(self.metafile_directory, exist_ok=True)
        os.makedirs(self.database_directory, exist_ok=True)

        if len(os.listdir(self.metafile_directory)) == 0:
            self._create_new_database_and_metafile()

        with open(self.metafile_path, "r") as metafile:
            latest_version = metafile.read().strip()

        with open(latest_version, "r") as f:
            json_data = f.read()
            latest_db = json.loads(json_data)

        return latest_db

    def _create_new_database_and_metafile(self) -> bool:
        """
        Create a new, empty JSON database and metafile, essentially from template.

        Returns
        -------
        bool
            True if a new JSON database and metafile are created successfully.
        """
        processed_raindrops_blank = {"Processed Raindrops": []}

        output_file = (
            f"001_processed_raindrops_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
        )

        database_file_name = os.path.join(self.database_directory, output_file)

        with open(database_file_name, "w") as f:
            json.dump(processed_raindrops_blank, f, indent=4)

        with open(self.metafile_path, "w") as metafile:
            metafile.write(database_file_name)
