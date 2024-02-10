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

    # app.config.from_mapping(
    #     SECRET_KEY='dev',
    #     DATABASE=os.path.join(app.instance_path, 'my-climate-dashboard.sqlite'),
    # )
    #
    # if test_config is None:
    #     # load the instance config, if it exists, when not testing
    #     app.config.from_pyfile('config.py', silent=True)
    # else:
    #     # load the test config if passed in
    #     app.config.from_mapping(test_config)
    #
    # # ensure the instance folder exists
    # try:
    #     os.makedirs(app.instance_path)
    # except OSError:
    #     pass

    # a simple page that says hello
    @app.route('/my-climate-dashboard/hello')
    def hello():
        return 'Hello, World!'

    # Post for climate stats
    class ClimateStats(Resource):
        def __init__(self):
            self._required_features = ["ba_name"]
            self.inputs = reqparse.RequestParser()

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
            response = BAStats().calculate_stats(args["ba_name"])
            return response

    api.add_resource(ClimateStats, "/my-climate-dashboard/green-energy-stats")

    return app



