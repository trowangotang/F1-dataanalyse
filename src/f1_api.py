import json
from functools import lru_cache
from typing import Any, Dict
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen

import pandas as pd


BASE_URL = "https://api.jolpi.ca/ergast/f1"
DEFAULT_TIMEOUT = 20


def _result_position(result: Dict[str, Any]) -> int:
    position = result.get("positionOrder", result.get("position"))

    if position is None:
        raise RuntimeError(f"Race result is missing a position field: {result}")

    return int(position)


def _get_json(path: str, **params: Any) -> Dict[str, Any]:
    query = f"?{urlencode(params)}" if params else ""
    url = f"{BASE_URL}/{path.lstrip('/')}.json{query}"

    try:
        with urlopen(url, timeout=DEFAULT_TIMEOUT) as response:
            return json.load(response)
    except HTTPError as exc:
        raise RuntimeError(f"F1 API returned HTTP {exc.code} for {url}") from exc
    except URLError as exc:
        raise RuntimeError(f"Could not reach F1 API at {url}: {exc.reason}") from exc


def fetch_driver_standings(season: int = 2023) -> pd.DataFrame:
    data = _get_json(f"{season}/driverstandings", limit=100)
    standings_lists = data["MRData"]["StandingsTable"]["StandingsLists"]

    if not standings_lists:
        return pd.DataFrame(columns=["driver", "team", "points", "wins", "podiums"])

    rows = []
    for item in standings_lists[0]["DriverStandings"]:
        driver = item["Driver"]
        constructor = item["Constructors"][0]
        driver_name = f"{driver['givenName']} {driver['familyName']}"
        rows.append(
            {
                "driver": driver_name,
                "team": constructor["name"],
                "points": float(item["points"]),
                "wins": int(item["wins"]),
            }
        )

    standings = pd.DataFrame(rows)
    podiums = _podiums_by_driver(season)
    return standings.merge(podiums, on="driver", how="left").fillna({"podiums": 0})


def _podiums_by_driver(season: int) -> pd.DataFrame:
    results = fetch_race_results(season)

    if results.empty:
        return pd.DataFrame(columns=["driver", "podiums"])

    podiums = (
        results[results["position"] <= 3]
        .groupby("driver", as_index=False)
        .size()
        .rename(columns={"size": "podiums"})
    )
    return podiums


@lru_cache(maxsize=None)
def fetch_race_results(season: int = 2023) -> pd.DataFrame:
    data = _get_json(f"{season}/results", limit=1000)
    races = data["MRData"]["RaceTable"]["Races"]

    rows = []
    for race in races:
        for result in race["Results"]:
            driver = result["Driver"]
            constructor = result["Constructor"]
            rows.append(
                {
                    "round": int(race["round"]),
                    "race": race["raceName"],
                    "driver": f"{driver['givenName']} {driver['familyName']}",
                    "team": constructor["name"],
                    "grid": int(result["grid"]),
                    "position": _result_position(result),
                    "points": float(result["points"]),
                }
            )

    return pd.DataFrame(rows)
