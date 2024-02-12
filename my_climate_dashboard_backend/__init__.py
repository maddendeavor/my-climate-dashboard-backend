import os

from flask import (
    Flask,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)
from flask_restful import Resource, Api, reqparse
from .ba_stats import BAStats

VERSION = "0.0.0"
DIRNAME = os.path.dirname(__file__)

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    api = Api(app)

    # a simple page that says hello
    @app.route('/my-climate-dashboard/hello')
    def hello():
        return 'Hello, World!'

    # Post for climate stats
    class ClimateStats(Resource):
        def __init__(self, logger=app.logger):
            self._required_features = ["ba_name"]
            self.inputs = reqparse.RequestParser()
            self.logger=logger

            for feature in self._required_features:
                self.inputs.add_argument(
                    feature,
                    type=str,
                    required=True,
                    location="json",
                    help="No {} provided".format(feature),
                )
            super(ClimateStats, self).__init__()

        def post(self):
            args = self.inputs.parse_args()
            response = BAStats(args["ba_name"], logger=self.logger).return_stats()
            return response

    api.add_resource(ClimateStats, "/my-climate-dashboard/green-energy-stats")

    return app



