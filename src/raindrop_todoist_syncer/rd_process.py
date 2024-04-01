from typing import Any

from loguru import logger

from raindrop_todoist_syncer.raindrop import DatabaseManager
from raindrop_todoist_syncer.rd_class import Raindrop


class RaindropsProcessor:
    """
    A class to process a list of all a user's Raindrops,

    Class Attributes:
    all_raindrops_api_response :  The list of raindrops (rds) collected from multiple API
                                  calls by RaindropClient.
    """

    def __init__(self, all_rds: dict[str, Any]):
        """
        Initalise an instance of the Raindrops Process, taking all_rds as state.

        Parameters:
            all_rds : list of all a users raindrops(rds).

        """
        self.all_rds = all_rds

    def newly_favourited_raindrops_extractor(self) -> list[Raindrop]:
        """
        Process favourited rds from a list of rds.

        This is the primary method for extracting newly favourited (unprocessed) rds
        from a list of rds.

        It takes a list of rds and extracts favourited rds. Compares this with the
        favourites the system has already processed, producing a list of newly
        favourited/unprocessed rds. Converts these to Raindrops objects for passing to
        Todoist.

        TODO: Currently updates the database.  This should not happen until AFTER tasks
        creation is a success. That is when an fav rd is "processed".

        Returns:
        -------
        raindrop_objects_for_todoist:  List of newly favourited rds as Raindrop objects
                                       ready to be sent to Todoist.
        """
        all_favs = self._extract_all_fav_rds()
        tracked_favs = self._fetch_tracked_favs()
        untracked_favs = self._extract_untracked_favs(all_favs, tracked_favs)
        rd_objects = self._convert_to_rd_objects(untracked_favs)
        logger.info(f"Found {len(rd_objects)} tasks to create.")
        return rd_objects

    def _extract_all_fav_rds(self) -> list[dict]:
        """
        Finds all favourited Raindrops in an Raindrop API response. Designed to work
        with collection_id endpoint, but likely to work with others.

        Favourite status is indicated by {"important": True}.

        BEWARE:  It seems rds do not to have an "important" key UNLESS favourited.

        Returns
        -------
        List[Dict]
            List of all Raindrop JSONs that are favorited.
        """
        fav_rds = []
        for raindrop in self.all_rds:
            if raindrop.get("important"):
                fav_rds.append(raindrop)
        logger.info(f"Includes {len(fav_rds)} favourites.")
        # logger.debug (f"Favourites: {fav_rds}")
        return fav_rds

    def _fetch_tracked_favs(self):
        db_manager = DatabaseManager()
        tracked_favs = db_manager.get_latest_database()["Processed Raindrops"]
        logger.info(f"db holds {len(tracked_favs)} favourited rds previously tracked")
        return tracked_favs

    def _extract_untracked_favs(self, all_favs: list[dict], tracked_favs: list[dict]):
        """
        Takes a list of favourited Raindrop objects and compares them to the list of
        previously processed favourites.

        Returns a list of newly favourited Raindrop objects, if any.

        Parameters:
            fav_rds         : List of all Raindrop JSONs that are favorited.

        Returns:
            unprocessed_rds : List of Raindrop JSONs that are newly favorited.
        """
        tracked_fav_ids = {rd["id"] for rd in tracked_favs}
        untracked_favs = [rd for rd in all_favs if rd["_id"] not in tracked_fav_ids]
        logger.info(f"Total untracked favourites found: {len(untracked_favs)}")
        logger.info(f"Untracked favourites found: {untracked_favs}")
        return untracked_favs

    def _convert_to_rd_objects(self, untracked_favs: list[dict]) -> list[Raindrop]:
        """
        Convert a list of newly favorited Raindrop JSONs to Raindrop objects ready for
        passing to Todoist.

        Parameters:
            unprocessed_rds : List of Raindrop JSONs that are newly favorited.

        Returns:
            rd_objects      : List of rd objects converted from the unprocessed rds.
        """
        rd_objects = []
        for raindrop_json in untracked_favs:
            rd_objects.append(Raindrop(raindrop_json))
        logger.info(f"{len(rd_objects)} Raindrop object(s) created.")
        return rd_objects
