import streamlit as st

from analysis import save_processed_data, top_comebacks
from f1_api import fetch_driver_standings, fetch_race_results


DEFAULT_SEASON = 2023


st.set_page_config(
    page_title="F1 Data Analysis",
    layout="wide",
)


@st.cache_data(show_spinner=False)
def load_season_data(season):
    driver_standings = fetch_driver_standings(season)
    race_results = fetch_race_results(season)
    return driver_standings, race_results


def team_points(driver_standings):
    return (
        driver_standings.groupby("team", as_index=False)["points"]
        .sum()
        .sort_values("points", ascending=False)
    )


def average_grid_delta(race_results):
    df = race_results[race_results["grid"] > 0].copy()
    df["places_gained"] = df["grid"] - df["position"]
    return (
        df.groupby("driver", as_index=False)["places_gained"]
        .mean()
        .sort_values("places_gained", ascending=False)
    )


def points_by_race(race_results, selected_driver):
    df = race_results[race_results["driver"] == selected_driver].copy()
    df = df.sort_values("round")
    return df[["round", "race", "points"]]


def display_metric_row(driver_standings, race_results):
    champion = driver_standings.sort_values("points", ascending=False).iloc[0]
    best_team = team_points(driver_standings).iloc[0]
    races = race_results["race"].nunique()
    drivers = driver_standings["driver"].nunique()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Champion", champion["driver"], f"{champion['points']:.0f} pts")
    col2.metric("Top Team", best_team["team"], f"{best_team['points']:.0f} pts")
    col3.metric("Races", races)
    col4.metric("Drivers", drivers)


def main():
    st.title("F1 Data Analysis")

    with st.sidebar:
        st.header("Controls")
        season = st.number_input("Season", min_value=1950, max_value=2030, value=DEFAULT_SEASON, step=1)
        save_data = st.checkbox("Save processed CSV files", value=True)
        st.caption("Data source: Jolpica F1 API")

    try:
        with st.spinner(f"Fetching {season} season data..."):
            driver_standings, race_results = load_season_data(int(season))
    except RuntimeError as exc:
        st.error(f"Could not fetch F1 data: {exc}")
        st.stop()

    if driver_standings.empty or race_results.empty:
        st.warning("No data found for this season.")
        st.stop()

    if save_data:
        driver_path, race_path = save_processed_data(driver_standings, race_results, int(season))
        st.sidebar.success("CSV files saved")
        st.sidebar.caption(str(driver_path))
        st.sidebar.caption(str(race_path))

    display_metric_row(driver_standings, race_results)

    standings_tab, teams_tab, race_tab, data_tab = st.tabs(
        ["Drivers", "Teams", "Race Analysis", "Data"]
    )

    with standings_tab:
        st.subheader("Driver Championship")
        standings = driver_standings.sort_values("points", ascending=False)
        st.bar_chart(standings, x="driver", y="points", color="#d71920")
        st.dataframe(
            standings[["driver", "team", "points", "wins", "podiums"]],
            use_container_width=True,
            hide_index=True,
        )

    with teams_tab:
        st.subheader("Team Points")
        teams = team_points(driver_standings)
        st.bar_chart(teams, x="team", y="points", color="#1f77b4")
        st.dataframe(teams, use_container_width=True, hide_index=True)

    with race_tab:
        col1, col2 = st.columns([1, 1])

        with col1:
            st.subheader("Average Places Gained")
            grid_delta = average_grid_delta(race_results)
            st.bar_chart(grid_delta, x="driver", y="places_gained", color="#2ca02c")

        with col2:
            st.subheader("Top Race Comebacks")
            st.dataframe(top_comebacks(race_results), use_container_width=True, hide_index=True)

        st.subheader("Driver Points by Race")
        selected_driver = st.selectbox(
            "Driver",
            driver_standings.sort_values("driver")["driver"].tolist(),
        )
        st.line_chart(points_by_race(race_results, selected_driver), x="race", y="points")

    with data_tab:
        st.subheader("Raw API Tables")
        st.dataframe(race_results, use_container_width=True, hide_index=True)
        st.dataframe(driver_standings, use_container_width=True, hide_index=True)


if __name__ == "__main__":
    main()
