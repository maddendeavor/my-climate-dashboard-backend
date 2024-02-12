import logging
import os
import time
import datetime
import requests
import json
import pandas as pd

VERSION = "0.0.0"
EIA_API_KEY = os.environ.get("EIA_API_KEY")
DUMMY_RESPONSE = {
    "created": datetime.date.today().isoformat(),
    "sw_version": VERSION,
    "ba_name": "IMAGINARY_BA",
    "source_ratio_current": {"nuclear": 0.2, "solar": 0.1, "coal": 0.7},
    "green_ratio_current": 0.3,  # this case would be bad
    "green_ratio_mean": 0.5,  # this should be center point of dial
    "green_threshold_low": 0.4,  # below this dashboard popup says “shed loads”
    "green_threshold_high": 0.55,  # above this dashboard popup says “plug in loads”
    "alert_text": "Dirtier Energy Than Normal:  Shed Loads!",
}

LOCAL_LOGGER = logging.getLogger(__name__)

class BAStats:
    """
    Class that handles pulling data and calculating stats for a specific BA
    """

    def __init__(self, ba_name, logger=LOCAL_LOGGER ):
        self.data = pd.DataFrame()
        self.data_datetime = datetime.date.today().isoformat()
        self.ba_name = ba_name
        self.logger = logger


    def get_data(self):
        self.data = get_eia_grid_mix_timeseries_hourly(
            [self.ba_name],
            # Get last 5 days of data
            start_date=(datetime.date.today() - datetime.timedelta(days=5)).isoformat(),
            end_date=datetime.date.today().isoformat(),
            frequency="hourly"
        )
        self.data_datetime = datetime.date.today()
        self.logger.info("Got Data!")

    def return_stats(self):

        self.logger.info("calculating results")
        # perform calculation

        # response = DUMMY_RESPONSE.copy()
        # response["ba_name"] = ba_name
        response = {
            "created": datetime.datetime.now().isoformat(),
            "sw_version": VERSION,
            "ba_name": self.ba_name,
            "source_ratio_current": {"nuclear": 0.2, "solar": 0.1, "coal": 0.7},
            "green_ratio_current": 0.0,  # this case would be bad
            "green_ratio_mean": 0.0,  # this should be center point of dial
            "green_threshold_low": 0.0,  # below this dashboard popup says “shed loads”
            "green_threshold_high": 0.0,  # above this dashboard popup says “plug in loads”
            "alert_text": "Dirtier Energy Than Normal:  Shed Loads!",
        }

        self.logger.info(f"returning {response}")
        return response


# methods from Software Stack from Climate Tech class at Terra.do

def get_api_data():
    """
    Returns available data from the api
    """
    api_url = f"https://api.eia.gov/v2/electricity/rto?api_key={EIA_API_KEY}"
    print(api_url)

    response_content = requests.get(
        api_url,
    ).json()

    return response_content

# Time series get functions
def get_eia_timeseries(
        url_segment,
        facets,
        value_column_name="value",
        start_date=(datetime.date.today() - datetime.timedelta(days=365)).isoformat(),
        end_date=datetime.date.today().isoformat(),
        frequency="daily",
        timezone="Pacific",
):
    """
    A generalized helper function to fetch data from the EIA API
    """
    print("frequency:", frequency)
    api_url = f"https://api.eia.gov/v2/electricity/rto/{url_segment}/data/?api_key={EIA_API_KEY}"

    if timezone is not None:
        facet_dict = dict(**{"timezone": ["Pacific"]}, **facets)
    else:
        facet_dict = dict(**facets)

    response_content = requests.get(
        api_url,
        headers={
            "X-Params": json.dumps(
                {
                    "frequency": frequency,
                    "data": ["value"],
                    "facets": facet_dict,
                    "start": start_date,
                    "end": end_date,
                    "sort": [{"column": "period", "direction": "desc"}],
                    "offset": 0,
                    "length": 5000,  # This is the maximum allowed
                }
            )
        },
    ).json()

    # Sometimes EIA API responses are nested under a "response" key. Sometimes not 🤷
    if "error" in response_content:
        print(response_content)
        return None

    if "response" in response_content:
        response_content = response_content["response"]

    # Handle warnings by displaying them to the user
    if "warnings" in response_content:
        print(f"Warning(s) returned from EIA API:", response_content["warnings"])
    if "data" in response_content:
        print(f"{len(response_content['data'])} rows returned")
    else:
        print(str(response_content))
        return None

    # Convert the data to a Pandas DataFrame and clean it up for plotting
    dataframe = pd.DataFrame(response_content["data"])
    dataframe["timestamp"] = dataframe["period"].apply(
        pd.to_datetime,
        # format="%Y/%m/%dT%H"
        format="ISO8601"
    )
    # Clean up the "value" column-
    # EIA always sends the value we asked for in a column called "value"
    # Oddly, this is sometimes sent as a string though it should always be a number.
    # We convert its dtype and set the name to a more useful one
    eia_value_column_name = "value"
    return dataframe.astype({eia_value_column_name: float}).rename(columns={eia_value_column_name: value_column_name})


def get_eia_interchange_timeseries(balancing_authorities, **kwargs):
    """
    Fetch electricity interchange data (imports & exports from other utilities)
    """
    return get_eia_timeseries(
        url_segment="daily-interchange-data",
        facets={"toba": balancing_authorities},
        value_column_name=f"Interchange to local BA (MWh)",
        **kwargs,
    )


def get_eia_net_demand_and_generation_timeseries(balancing_authorities, **kwargs):
    """
    Fetch electricity demand data
    """
    return get_eia_timeseries(
        url_segment="daily-region-data",
        facets={
            "respondent": balancing_authorities,
            "type": ["D", "NG", "TI"],  # Filter out the "Demand forecast" (DF) type
        },
        value_column_name="Demand (MWh)",
        **kwargs,
    )

def get_eia_grid_mix_timeseries(balancing_authorities, **kwargs):
    """
    Fetch electricity generation data by fuel type
    """
    return get_eia_timeseries(
        url_segment="daily-fuel-type-data",
        facets={"respondent": balancing_authorities},
        value_column_name="Generation (MWh)",
        **kwargs,
    )

def get_eia_grid_mix_timeseries_hourly(balancing_authorities, frequency="hourly", **kwargs):
    """
    Fetch electricity generation data by fuel type
    """
    return get_eia_timeseries(
        url_segment="fuel-type-data",
        facets={"respondent": balancing_authorities},
        value_column_name="Generation (MWh)",
        frequency=frequency,
        timezone=None,
        **kwargs,
    )


# Dataframe cleaning and processing functions
def get_energy_generated_and_consumed_locally(df):
    demand_stats = df.groupby("type-name")["Demand (MWh)"].sum()
    # If local demand is smaller than net (local) generation, that means: amount generated and used locally == Demand (net export)
    # If local generation is smaller than local demand, that means: amount generated and used locally == Net generation (net import)
    # Therefore, the amount generated and used locally is the minimum of these two
    return min(demand_stats["Demand"], demand_stats["Net generation"])


def energy_consumed_locally_by_source_ba(local_ba):
    interchange_df = get_eia_interchange_timeseries([local_ba])
    demand_df = get_eia_net_demand_and_generation_timeseries([local_ba])

    energy_generated_and_used_locally = demand_df.groupby("timestamp").apply(
        get_energy_generated_and_consumed_locally
    )

    consumed_locally_column_name = "Power consumed locally (MWh)"

    # How much energy is imported and then used locally, grouped by the source BA (i.e. the BA which generated the energy)
    energy_imported_then_consumed_locally_by_source_ba = (
        interchange_df.groupby(["timestamp", "fromba"])[
            "Interchange to local BA (MWh)"
        ].sum().astype(int)
        # We're only interested in data points where energy is coming *in* to the local BA, i.e. where net export is negative
        # Therefore, ignore positive net exports
        .apply(lambda interchange: max(interchange, 0))
    )

    # Combine these two together to get all energy used locally, grouped by the source BA (both local and connected)
    energy_consumed_locally_by_source_ba = pd.concat(
        [
            energy_imported_then_consumed_locally_by_source_ba.rename(
                consumed_locally_column_name
            ).reset_index("fromba"),
            pd.DataFrame(
                {
                    "fromba": local_ba,
                    consumed_locally_column_name: energy_generated_and_used_locally,
                }
            ),
        ]
    ).reset_index()

    return energy_consumed_locally_by_source_ba


def get_usage_by_ba_and_generation_type(energy_consumed_locally_by_source_ba):
    """
    The goal is to get a DataFrame of energy used at the local BA (in MWh), broken down by both
    * the BA that the energy came from, and
    * the fuel type of that energy.
    So we'll end up with one row for each combination of source BA and fuel type.

    To get there, we need to combine the amount of imported energy from each source ba with grid mix for that source BA.
    The general formula is:
    Power consumed locally from a (BA, fuel type) combination =
      total power consumed locally from this source BA * (fuel type as a % of source BA's generation)
    fuel type as a % of source BA's generation =
       (total generation at source BA) / (total generation for this fuel type at this BA)
    """
    # First, get a list of all source BAs: our local BA plus the ones we're importing from
    all_source_bas = energy_consumed_locally_by_source_ba["fromba"].unique().tolist()

    # Then, fetch the fuel type breakdowns for each of those BAs
    generation_types_by_ba = get_eia_grid_mix_timeseries(all_source_bas).rename(
        {"respondent": "fromba", "type-name": "generation_type"}, axis="columns"
    )

    total_generation_by_source_ba = generation_types_by_ba.groupby(["timestamp", "fromba"])[
        "Generation (MWh)"
    ].sum()

    generation_types_by_ba_with_totals = generation_types_by_ba.join(
        total_generation_by_source_ba,
        how="left",
        on=["timestamp", "fromba"],
        rsuffix=" Total",
    )
    generation_types_by_ba_with_totals["Generation (% of BA generation)"] = (
        generation_types_by_ba_with_totals["Generation (MWh)"]
        / generation_types_by_ba_with_totals["Generation (MWh) Total"]
    )
    generation_types_by_ba_with_totals_and_source_ba_breakdown = generation_types_by_ba_with_totals.merge(
        energy_consumed_locally_by_source_ba.rename(
            {"Power consumed locally (MWh)": "Power consumed locally from source BA (MWh)"},
            axis="columns",
        ),
        on=["timestamp", "fromba"],
    )
    full_df_reindexed = (
        generation_types_by_ba_with_totals_and_source_ba_breakdown.set_index(
            ["timestamp", "fromba", "generation_type"]
        )
    )
    usage_by_ba_and_generation_type = (
        (
            full_df_reindexed["Power consumed locally from source BA (MWh)"]
            * full_df_reindexed["Generation (% of BA generation)"]
        )
        .rename("Usage (MWh)")
        .reset_index()
    )

    return usage_by_ba_and_generation_type


if __name__ == "__main__":
    import matplotlib.pyplot as plt

    ba_authority = "PSEI"

    t0=time.time()
    ba_stats = BAStats(ba_authority)
    ba_stats.get_data()

    # local_generation_grid_mix_hourly = get_eia_grid_mix_timeseries_hourly(
    #     [ba_authority],
    #     # Optional: uncomment the lines below to try looking at a different time range to get data from other seasons.
    #     start_date=(datetime.date.today() - datetime.timedelta(days=5)).isoformat(),
    #     end_date=datetime.date.today().isoformat(),
    #     frequency="hourly"
    # )
    print("data_datetime", ba_stats.data_datetime)
    print("data\n", ba_stats.data)
    print(ba_stats.return_stats())
    print("Process time:", time.time()-t0)

    # Plot results
    fig, ax = plt.subplots()
    for fuel_type in ba_stats.data["fueltype"].unique():
        df = ba_stats.data[ba_stats.data["fueltype"] == fuel_type]
        ax.plot(df["timestamp"], df["Generation (MWh)"], label=fuel_type)
    plt.legend()
    plt.grid(True)
    plt.title(f"{ba_authority} Power Generation")
    plt.xlabel("Timestamp")
    plt.ylabel("Generation (MWh)")
    plt.show()