import argparse
import sys
from pathlib import Path

from matplotlib import pyplot as plt

from f1_api import fetch_driver_standings, fetch_race_results


DEFAULT_SEASON = 2023
PLOTS_DIR = Path("plots")
PROCESSED_DIR = Path("data/processed")


def save_processed_data(driver_standings, race_results, season):
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    driver_path = PROCESSED_DIR / f"f1_{season}_driver_standings_api.csv"
    race_path = PROCESSED_DIR / f"f1_{season}_race_results_api.csv"

    driver_standings.to_csv(driver_path, index=False)
    race_results.to_csv(race_path, index=False)

    return driver_path, race_path


def plot_points_per_driver(driver_standings, season):
    df = driver_standings.sort_values("points", ascending=False)

    plt.figure(figsize=(11, 6))
    bars = plt.bar(df["driver"], df["points"], color="#d71920")
    plt.bar_label(bars, fmt="%.0f", padding=3, fontsize=8)
    plt.xticks(rotation=45, ha="right")
    plt.title(f"F1 {season} - Driver Championship Points")
    plt.ylabel("Points")
    plt.tight_layout()

    output_path = PLOTS_DIR / f"f1_{season}_points_per_driver.png"
    plt.savefig(output_path)
    return output_path


def plot_points_per_team(driver_standings, season):
    df = (
        driver_standings.groupby("team", as_index=False)["points"]
        .sum()
        .sort_values("points", ascending=True)
    )

    plt.figure(figsize=(10, 6))
    bars = plt.barh(df["team"], df["points"], color="#1f77b4")
    plt.bar_label(bars, fmt="%.0f", padding=4, fontsize=8)
    plt.title(f"F1 {season} - Points per Team")
    plt.xlabel("Points")
    plt.tight_layout()

    output_path = PLOTS_DIR / f"f1_{season}_points_per_team.png"
    plt.savefig(output_path)
    return output_path


def plot_grid_to_finish_delta(race_results, season):
    df = race_results[race_results["grid"] > 0].copy()
    df["delta"] = df["grid"] - df["position"]
    df = (
        df.groupby("driver", as_index=False)["delta"]
        .mean()
        .sort_values("delta", ascending=True)
    )

    colors = ["#d71920" if value < 0 else "#2ca02c" for value in df["delta"]]

    plt.figure(figsize=(10, 7))
    bars = plt.barh(df["driver"], df["delta"], color=colors)
    plt.axvline(0, color="black", linewidth=0.8)
    plt.bar_label(bars, fmt="%.1f", padding=3, fontsize=8)
    plt.title(f"F1 {season} - Average Grid to Finish Change")
    plt.xlabel("Average places gained")
    plt.tight_layout()

    output_path = PLOTS_DIR / f"f1_{season}_grid_to_finish_delta.png"
    plt.savefig(output_path)
    return output_path


def top_comebacks(race_results, limit=10):
    df = race_results[race_results["grid"] > 0].copy()
    df["places_gained"] = df["grid"] - df["position"]
    return (
        df.sort_values("places_gained", ascending=False)
        [["race", "driver", "team", "grid", "position", "places_gained"]]
        .head(limit)
    )


def print_summary(driver_standings, race_results, season):
    champion = driver_standings.sort_values("points", ascending=False).iloc[0]
    team_points = (
        driver_standings.groupby("team", as_index=False)["points"]
        .sum()
        .sort_values("points", ascending=False)
    )

    print(f"\nF1 {season} summary")
    print(f"Driver champion: {champion['driver']} ({champion['points']:.0f} points)")
    print(f"Top team by driver points: {team_points.iloc[0]['team']} ({team_points.iloc[0]['points']:.0f} points)")

    print("\nTop 10 race comebacks")
    print(top_comebacks(race_results).to_string(index=False))


def run_analysis(season, show_plots):
    PLOTS_DIR.mkdir(exist_ok=True)

    driver_standings = fetch_driver_standings(season)
    race_results = fetch_race_results(season)

    driver_path, race_path = save_processed_data(driver_standings, race_results, season)
    plot_paths = [
        plot_points_per_driver(driver_standings, season),
        plot_points_per_team(driver_standings, season),
        plot_grid_to_finish_delta(race_results, season),
    ]

    print_summary(driver_standings, race_results, season)

    print("\nSaved processed data")
    print(driver_path)
    print(race_path)

    print("\nSaved plots")
    for path in plot_paths:
        print(path)

    if show_plots:
        plt.show()
    else:
        plt.close("all")


def parse_args():
    parser = argparse.ArgumentParser(description="Analyze Formula 1 season data from the Jolpica F1 API.")
    parser.add_argument("--season", type=int, default=DEFAULT_SEASON, help="F1 season to analyze.")
    parser.add_argument("--no-show", action="store_true", help="Save plots without opening chart windows.")
    return parser.parse_args()


def main():
    args = parse_args()

    try:
        run_analysis(args.season, show_plots=not args.no_show)
    except RuntimeError as exc:
        print(f"Could not fetch F1 data: {exc}", file=sys.stderr)
        print("Check your internet connection and try again.", file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
