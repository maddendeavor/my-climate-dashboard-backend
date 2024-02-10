import logging
from datetime import datetime

VERSION = "0.0.0"

class BAStats:
    """
    Class that handles pulling data and calculating stats for a specific BA
    """

    def __init__(self, logger=logging.getLogger(__name__)):
        self.data = []
        self.logger = logger


    def get_data(self):
        self.logger.info("Getting Data!")

    def calculate_stats(self, ba_name):

        self.logger.info("calculating results")
        # perform calculation

        response = {
            "created": datetime.utcnow().isoformat(),
            "sw_version": VERSION,
            "ba_name": ba_name,
            "source_ratio_current": {"nuclear": 0.2, "solar": 0.1, "coal": 0.7},
            "green_ratio_current": 0.3,  # this case would be bad
            "green_ratio_mean": 0.5,  # this should be center point of dial
            "green_threshold_low": 0.4,  # below this dashboard popup says “shed loads”
            "green_threshold_high": 0.55, # above this dashboard popup says “plug in loads”
            "alert_text": "Dirtier Energy Than Normal:  Shed Loads!",
        }

        self.logger.info(f"returning {response}")
        return response