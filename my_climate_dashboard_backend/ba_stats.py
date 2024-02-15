import logging
import os
import time
import datetime
import requests
import json
import copy
import pandas as pd
import numpy as np

VERSION = "0.0.0"
EIA_API_KEY = os.environ.get("EIA_API_KEY")
DUMMY_RESPONSE = {
    "created": datetime.datetime.now().isoformat(),
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
LOW_THRESHOLD_PCT = 0.75
HIGH_THRESHOLD_PCT = 1.1

class BAStats:
    """
    Class that handles pulling data and calculating stats for a specific BA
    """

    def __init__(self, ba_name, logger=LOCAL_LOGGER ):
        self.data_mix = pd.DataFrame()
        self.data_demand = pd.DataFrame()
        self.data_mix_datetime = None
        self.data_demand_datetime = None
        self.ba_name = ba_name.upper()
        self.logger = logger
        self.logger.info(f"initialized with {self.ba_name}")

    def get_data_mix(self,
                     start_date_input=(datetime.date.today() - datetime.timedelta(days=5)).isoformat(),  # 5 days ago
                     end_date_input=(datetime.date.today() + datetime.timedelta(days=1)).isoformat(),  # tomorrow
                     ):

        self.logger.info("Getting data")
        # only get new data if it is more than an hour old
        if (self.data_mix_datetime is None) or (self.data_mix_datetime > (datetime.datetime.now() - datetime.timedelta(hours=1))):
            # This provides generation mix, but only goes up to 00 the day before, T08 = 00H PST
            self.data_mix = get_eia_grid_mix_timeseries(
                [self.ba_name],
                # Get last 5 days of data
                start_date=start_date_input,
                end_date=end_date_input,
                frequency="hourly"
            ).copy()

            self.data_mix_datetime = datetime.datetime.now().isoformat()
            print(f"Received mix data up to {max(self.data_mix['timestamp'])}!")

    def get_data_demand(self,
                        start_date_input=(datetime.date.today() - datetime.timedelta(days=5)).isoformat(),  # 5 days ago,
                        end_date_input=(datetime.date.today() + datetime.timedelta(days=3)).isoformat(),  # tomorrow
                        ):

        self.logger.info("Getting data")
        # only get new data if it is more than an hour old
        if (self.data_demand_datetime is None) or (self.data_demand_datetime > (datetime.datetime.now() - datetime.timedelta(hours=1))):
            # This provides most up to date demand and forecast data, but not mix
            self.data_demand = get_eia_demand_forecast_generation_interchange(
                [self.ba_name],  # needs to be in a list
                start_date=start_date_input,
                end_date=end_date_input
            ).copy()

            self.data_demand_datetime = datetime.datetime.now().isoformat()
            print(f"Received demand data up to {max(self.data_demand['timestamp'])}!")

    def create_green_df(self):
        # Filter rows with fuel types Solar and Wind
        green_df = self.data_mix[self.data_mix['fueltype'].isin(['SUN', 'WND', 'NUC', 'WAT'])]
        green_df = green_df.groupby('period')['Generation (MWh)'].sum().reset_index()

        # Calculate the total generation for each time period
        total_generation = self.data_mix.groupby('period')['Generation (MWh)'].sum().reset_index()
        # Merge the total generation back to the green_df
        green_df = pd.merge(green_df, total_generation, on='period', suffixes=('_green', '_total'))
        # Calculate the ratio (Solar+Wind) / total
        green_df['Green ratio'] = green_df['Generation (MWh)_green'] / green_df['Generation (MWh)_total']
        green_df[["Date"]] = green_df[["period"]].apply(pd.to_datetime)
        green_df = green_df.sort_values(by=['Date'], ascending=False)

        return green_df

    def create_demand_df(self):
        demand_df = self.data_demand[self.data_demand['type'] == 'D'].copy()
        demand_df = demand_df.rename(columns={"Generation (MWh)": "Demand"})
        demand_df = demand_df[['period', 'respondent', 'Demand', 'value-units']]

        forecast_df = self.data_demand[self.data_demand['type'] == 'DF']
        forecast_df = forecast_df.rename(columns={"Generation (MWh)": "Demand Forecast"})

        demand_df = pd.merge(demand_df, forecast_df[['period', 'Demand Forecast']], on='period')
        max_demand = demand_df['Demand'].max()
        demand_df['Demand_norm'] = demand_df['Demand'] / max_demand
        demand_df['Demand Forecast_norm'] = demand_df['Demand Forecast'] / max_demand

        demand_df['Demand ratio'] = demand_df['Demand'] / demand_df['Demand Forecast']
        demand_df['Demand diff'] = demand_df['Demand'] - demand_df['Demand Forecast']

        return demand_df

    def return_stats(self):

        self.logger.info("calculating results")
        # response = DUMMY_RESPONSE.copy()
        # response["ba_name"] = ba_name
        self.get_data_mix()
        self.get_data_demand()

        # Get source mix ratios for pie chart display
        latest_mix = self.data_mix[self.data_mix["timestamp"] == max(self.data_mix["timestamp"])]
        latest_mix["mix_ratio"] = latest_mix["Generation (MWh)"] / sum(latest_mix["Generation (MWh)"])
        source_ratio_current = latest_mix[["type-name", "mix_ratio"]].set_index("type-name").to_dict()
        source_ratio_current["timestamp"] = str(max(self.data_mix["timestamp"]))

        # Create time series, for time series display
        demand_data = {
                    "timestamp_demand": self.data_demand[self.data_demand["type"] == "D"]["timestamp"].astype(str).tolist(),
                    "demand": self.data_demand[self.data_demand["type"] == "D"]["Generation (MWh)"].tolist(),
                    "timestamp_forecast": self.data_demand[self.data_demand["type"] == "DF"]["timestamp"].astype(str).tolist(),
                    "forecast": self.data_demand[self.data_demand["type"] == "DF"]["Generation (MWh)"].tolist(),
                },
        mix_data = {}
        for fuel_type in self.data_mix["type-name"].unique():
            mix_data[fuel_type + "_timestamp"] = self.data_mix[self.data_mix["type-name"] == fuel_type]["timestamp"].astype(str).tolist()
            mix_data[fuel_type] = self.data_mix[self.data_mix["type-name"] == fuel_type]["Generation (MWh)"].tolist()


        demand_df = self.create_demand_df()
        green_df = self.create_green_df()

        # Merge the demand information from df_demand
        analysis_df = pd.merge(green_df, demand_df[
            ['period', 'Demand', 'Demand Forecast', 'Demand_norm', 'Demand Forecast_norm', 'Demand ratio',
             'Demand diff']], on='period')

        latest_row = analysis_df.head(1)
        latest_green_ratio = latest_row['Green ratio'].values[0]
        max_green = analysis_df['Green ratio'].max()
        min_green = analysis_df['Green ratio'].min()

        latest_demand_ratio = latest_row['Demand_norm'].values[0]
        max_demand = analysis_df['Demand_norm'].max()
        min_demand = analysis_df['Demand_norm'].min()

        green_ratio_mean = (min_green+max_green)/2
        green_threshold_low = green_ratio_mean * LOW_THRESHOLD_PCT
        green_threshold_high = green_ratio_mean * HIGH_THRESHOLD_PCT

        demand_ratio_mean = (min_demand+max_demand)/2
        demand_threshold_low = demand_ratio_mean * LOW_THRESHOLD_PCT
        demand_threshold_high = demand_ratio_mean * HIGH_THRESHOLD_PCT

        demand_alert_text = ""
        if latest_demand_ratio > demand_threshold_high:
            demand_alert_text = f"Demand Energy {int(HIGH_THRESHOLD_PCT*100)}% Higher Than Normal: Shed Loads!"
        elif latest_demand_ratio < demand_threshold_low:
            demand_alert_text = f"Demand Energy {int(LOW_THRESHOLD_PCT*100)}% Lower Than Normal: Plug in Loads!"

        green_alert_text = ""
        if latest_green_ratio > green_threshold_high:
            green_alert_text = f"Green Energy {int(HIGH_THRESHOLD_PCT * 100)}% Higher Than Normal: Plug in Loads!"
        elif latest_green_ratio < green_threshold_low:
            green_alert_text = f"Green Energy {int(LOW_THRESHOLD_PCT * 100)}% Lower Than Normal: Shed Loads!"

        response = {
            "created": datetime.datetime.now().isoformat(),
            "sw_version": VERSION,
            "ba_name": self.ba_name,
            "source_ratio_current": copy.copy(source_ratio_current),
            "green_ratio_current": latest_green_ratio,   # this case would be bad
            "green_ratio_mean": green_ratio_mean,  # this should be center point of dial
            "green_threshold_low": green_threshold_low,  # below this dashboard popup says “shed loads”
            "green_threshold_high": green_threshold_high,  # above this dashboard popup says “plug in loads”
            "demand_ratio_current": latest_demand_ratio,  # ratio of demand to max demand
            "demand_ratio_mean": demand_ratio_mean,  # this should be center point of dial
            "demand_threshold_low": demand_threshold_low,  # below this dashboard popup says "plug in loads"
            "demand_threshold_high": demand_threshold_high,  # above this dashboard popup says "shed loads"
            "alert_text": demand_alert_text,  # only doing demand since green energy calculations lag currently
            "demand_alert_text": demand_alert_text,
            "green_alert_text": green_alert_text,
            "data_timeseries": {
                "demand_data": copy.copy(demand_data),
                "mix_data": copy.copy(mix_data),

            }
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
    api_url = f"https://api.eia.gov/v2/electricity/rto/{url_segment}/data/?api_key={EIA_API_KEY}"

    if timezone is not None:
        facet_dict = dict(**{"timezone": ["Pacific"]}, **facets)
    else:
        facet_dict = dict(**facets)

    headers = {
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
        }

    response_content = requests.get(
        api_url,
        headers=headers,
    )
    response_content = response_content.json()

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
        format="ISO8601"
    )
    # Clean up the "value" column-
    # EIA always sends the value we asked for in a column called "value"
    # Oddly, this is sometimes sent as a string though it should always be a number.
    # We convert its dtype and set the name to a more useful one
    eia_value_column_name = "value"
    return dataframe.astype({eia_value_column_name: float}).rename(columns={eia_value_column_name: value_column_name})


def get_eia_interchange_timeseries_daily(balancing_authorities, **kwargs):
    """
    Fetch electricity interchange data (imports & exports from other utilities)
    """
    return get_eia_timeseries(
        url_segment="daily-interchange-data",
        facets={"toba": balancing_authorities},
        value_column_name=f"Interchange to local BA (MWh)",
        **kwargs,
    )


def get_eia_net_demand_and_generation_timeseries_daily(balancing_authorities, **kwargs):
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

def get_eia_grid_mix_timeseries_daily(balancing_authorities, **kwargs):
    """
    Fetch electricity generation data by fuel type
    """
    return get_eia_timeseries(
        url_segment="daily-fuel-type-data",
        facets={"respondent": balancing_authorities},
        value_column_name="Generation (MWh)",
        **kwargs,
    )

def get_eia_grid_mix_timeseries(balancing_authorities, frequency="hourly", **kwargs):
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


def get_eia_demand_forecast_generation_interchange(balancing_authorities, frequency="hourly", **kwargs):
    """
    Fetch hourly demand with demand "D", demand forecast "DF", generation as "NG" and interchange as "TI"
    """
    data = get_eia_timeseries(
        url_segment="region-data",
        facets={"respondent": balancing_authorities},  # for some reason this doesn't work on this
        value_column_name="Generation (MWh)",
        frequency=frequency,
        timezone=None,
        **kwargs,
    )
    return data


# Dataframe cleaning and processing functions
def get_energy_generated_and_consumed_locally(df):
    demand_stats = df.groupby("type-name")["Demand (MWh)"].sum()
    # If local demand is smaller than net (local) generation, that means: amount generated and used locally == Demand (net export)
    # If local generation is smaller than local demand, that means: amount generated and used locally == Net generation (net import)
    # Therefore, the amount generated and used locally is the minimum of these two
    return min(demand_stats["Demand"], demand_stats["Net generation"])


def energy_consumed_locally_by_source_ba(local_ba):
    interchange_df = get_eia_interchange_timeseries_daily([local_ba])
    demand_df = get_eia_net_demand_and_generation_timeseries_daily([local_ba])

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
    generation_types_by_ba = get_eia_grid_mix_timeseries_daily(all_source_bas).rename(
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
    results = ba_stats.return_stats()

    print("data_demand_datetime", ba_stats.data_demand_datetime)
    print("data_demand\n", ba_stats.data_demand)

    print("data_mix_datetime", ba_stats.data_mix_datetime)
    print("data_mix\n", ba_stats.data_mix)
    print("Process time:", time.time()-t0)

    print(results)

    # Plot results
    fig, ax = plt.subplots(figsize=(12, 8))
    for fuel_type in ba_stats.data_mix["type-name"].unique():
        df = ba_stats.data_mix[ba_stats.data_mix["type-name"] == fuel_type]
        ax.plot(df["timestamp"], df["Generation (MWh)"], label=fuel_type)
    plt.legend()
    plt.grid(True)
    plt.xticks(rotation=45)
    plt.title(f"{ba_authority} Power Generation")
    plt.xlabel("Timestamp")
    plt.ylabel("Generation (MWh)")
    plt.show()

    fig, ax = plt.subplots(figsize=(12, 8))
    for fuel_type in ba_stats.data_demand["type-name"].unique():
        df = ba_stats.data_demand[ba_stats.data_demand["type-name"] == fuel_type]
        ax.plot(df["timestamp"], df["Generation (MWh)"], label=fuel_type)

    plt.legend()
    plt.grid(True)
    plt.xticks(rotation=45)
    plt.title(f"{ba_authority} Power Generation")
    plt.xlabel("Timestamp")
    plt.ylabel("Generation (MWh)")
    plt.show()


    # plot green
    demand_df = ba_stats.create_demand_df()
    green_df = ba_stats.create_green_df()

    # Merge the demand information from df_demand
    analysis_df = pd.merge(green_df, demand_df[
        ['period', 'Demand', 'Demand Forecast', 'Demand_norm', 'Demand Forecast_norm', 'Demand ratio',
         'Demand diff']], on='period')

    # Plot Ratios
    fig, ax = plt.subplots(figsize=(12, 8))
    ax.plot(analysis_df['Date'], analysis_df['Green ratio'], "g", label="green_ratio")
    ax.plot(analysis_df['Date'], analysis_df['Demand ratio'], "b", label="demand2forecast_ratio")
    ax.plot(analysis_df['Date'], analysis_df['Demand_norm'], "c", label="demand2max_ratio")
    plt.legend()
    plt.grid(True)
    plt.xticks(rotation=45)
    # plt.tight_layout()
    plt.xlabel("Timestamp")
    plt.ylabel("Ratio")
    plt.title(f"{ba_authority} Green energy / Demand ratio vs time (latest: {max(analysis_df['Date'])})")

    # Plot correlation
    correlation = analysis_df["Green ratio"].corr(analysis_df["Demand ratio"])
    fig, ax = plt.subplots(figsize=(12, 8))
    ax.scatter(analysis_df["Green ratio"], analysis_df["Demand ratio"], label='')
    # ax.scatter(analysis_df["Green ratio"], analysis_df["Demand diff"], label='')
    ax.annotate(f'Correlation: {correlation:.2f}', xy=(0.5, 0.95), xycoords='axes fraction', ha='center', fontsize=12)
    plt.legend()
    plt.grid(True)
    plt.xticks(rotation=45)
    # plt.tight_layout()
    plt.title(f"{ba_authority} Green energy ratio vs Demand ratio")
    plt.xlabel("Green ratio")
    plt.ylabel("Demand ratio")
    plt.show()