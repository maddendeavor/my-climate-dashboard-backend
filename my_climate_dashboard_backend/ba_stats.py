import logging
import datetime

VERSION = "0.0.0"

class BAStats:
    """
    Class that handles pulling data and calculating stats for a specific BA
    """

    def __init__(self, ):
        self.data = []
        self.logger = logging.getLogger(__name__)
        self.ba_name = "psei"


    def get_data(self):
        self.logger.info("Getting Data!")

    def calculate_stats(self):

        self.logger.info("calculating results")
        # perform calculation

        response = {
            "created": datetime.utcnow().isoformat(),
            "model_version": VERSION,
            "input_data": input_dict,
            "result": result,
        }

        self.logger.info(f"returning {response}")
        return response