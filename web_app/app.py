import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output, ctx, State, ALL
import dash_bootstrap_components as dbc
import requests
from io import StringIO
import re
import os
import json
import logging

# --- App Initialization ---
app = Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.FONT_AWESOME],
    suppress_callback_exceptions=True,
)
server = app.server
APP_DIR = os.path.dirname(os.path.abspath(__file__))
df = pd.DataFrame()
CONFIG_FILE = os.path.join(APP_DIR, "..", "config.json")


# --- Data Loading ---
def load_config():
    if not os.path.exists(CONFIG_FILE):
        return None
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)


config = load_config()


def load_data(use_local=True):
    global df, config
    local_excel_path = os.path.join(APP_DIR, "local.xlsx")
    if config is None:
        logging.error("config.json not found. Please run setup.py in the root directory.")
        df = pd.DataFrame()
        return

    if use_local and os.path.exists(local_excel_path):
        try:
            df = pd.read_excel(local_excel_path, engine="openpyxl")
            logging.info(f"Loaded data from {local_excel_path}")
        except Exception as e:
            logging.error(f"Error loading local file: {e}", exc_info=True)
            df = pd.DataFrame()
    else:
        try:
            logging.info("Attempting to download new data from Google Sheet...")
            response = requests.get(config["sheet_csv_url"])
            response.raise_for_status()
            df = pd.read_csv(StringIO(response.text))
            df.to_excel(local_excel_path, index=False, engine="openpyxl")
            logging.info(f"Successfully downloaded and saved as {local_excel_path}!")
        except Exception as e:
            logging.error(f"Error downloading data: {e}", exc_info=True)
            if "df" not in globals() or df.empty:
                df = pd.DataFrame()

    if not df.empty:
        df.columns = df.columns.str.strip()
        if "Date" in df.columns:
            df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        if "Match ID" not in df.columns:
            df["Match ID"] = range(len(df), 0, -1)
        df.sort_values("Match ID", ascending=False, inplace=True)
        df.reset_index(drop=True, inplace=True)
        logging.info("DataFrame processed and sorted by Match ID (descending).")


load_data(use_local=True)

# --- Layout ---
app.layout = dbc.Container(
    [
        dcc.Store(id="history-display-count-store", data={"count": 10}),
        dbc.Row(
            [
                dbc.Col(
                    html.Img(
                        src="https://upload.wikimedia.org/wikipedia/commons/thumb/5/55/Overwatch_circle_logo.svg/1024px-Overwatch_circle_logo.svg.png",
                        height="50px",
                    ),
                    width="auto",
                ),
                dbc.Col(html.H1("Overwatch Statistics", className="my-4"), width=True),
                dbc.Col(
                    dbc.Button(
                        "Update Data from Cloud",
                        id="update-data-button",
                        color="primary",
                        className="mt-4",
                    ),
                    width="auto",
                ),
            ],
            align="center",
            className="mb-3",
        ),
        dbc.Row(
            [
                dbc.Col(
                    [
                        dbc.Card(
                            [
                                dbc.CardHeader(
                                    "Filters", className="bg-primary text-white"
                                ),
                                dbc.CardBody(
                                    [
                                        dbc.Label("Select Player:"),
                                        dcc.Dropdown(
                                            id="player-dropdown",
                                            options=[
                                                {"label": p, "value": p}
                                                for p in (
                                                    config["known_players"]
                                                    if config
                                                    else []
                                                )
                                            ],
                                            value=(
                                                config["known_players"][0]
                                                if config and config["known_players"]
                                                else None
                                            ),
                                            clearable=False,
                                            className="mb-3",
                                        ),
                                        dbc.Label(
                                            "Select Season (overrides Year/Month):"
                                        ),
                                        dcc.Dropdown(
                                            id="season-dropdown",
                                            placeholder="(no selection)",
                                            className="mb-3",
                                            clearable=True,
                                        ),
                                        dbc.Label("Select Year:"),
                                        dcc.Dropdown(
                                            id="year-dropdown",
                                            placeholder="(no selection)",
                                            className="mb-3",
                                            clearable=True,
                                        ),
                                        dbc.Label("Select Month:"),
                                        dcc.Dropdown(
                                            id="month-dropdown",
                                            placeholder="(no selection)",
                                            className="mb-3",
                                            clearable=True,
                                        ),
                                        dbc.Label("Minimum Games Played:"),
                                        dcc.Slider(
                                            id="min-games-slider",
                                            min=1,
                                            max=100,
                                            step=None,
                                            value=5,
                                            marks={
                                                1: "1", 5: "5", 10: "10", 25: "25",
                                                50: "50", 75: "75", 100: "100",
                                            },
                                            included=False,
                                            className="mb-1",
                                        ),
                                        html.Div(
                                            id="slider-hint",
                                            className="text-muted",
                                            style={"fontSize": "0.85em"},
                                        ),
                                        html.Hr(),
                                        dbc.Label("Compare with:"),
                                        dcc.Dropdown(
                                            id="compare-dropdown",
                                            multi=True,
                                            placeholder="Select up to 2 players...",
                                        ),
                                    ]
                                ),
                            ],
                            className="mb-4",
                        )
                    ],
                    width=3,
                ),
                dbc.Col(
                    [
                        dbc.Tabs(
                            [
                                dbc.Tab(
                                    label="Map & Mode Stats",
                                    tab_id="tab-map",
                                    children=[
                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    dcc.Dropdown(
                                                        id="map-stat-type",
                                                        value="winrate",
                                                        clearable=False,
                                                        style={"width": "100%", "marginBottom": "20px"},
                                                        options=[
                                                            {"label": "Winrate by Map", "value": "winrate"},
                                                            {"label": "Games per Map", "value": "plays"},
                                                            {"label": "Gamemode Stats", "value": "gamemode"},
                                                            {"label": "Attack/Defense Stats", "value": "attackdef"},
                                                        ],
                                                    ),
                                                    width=4,
                                                ),
                                                dbc.Col(
                                                    html.Div(
                                                        dbc.Switch(
                                                            id="map-view-type",
                                                            label="Detailed View",
                                                            value=False,
                                                            className="mt-1",
                                                        ),
                                                        id="map-view-type-container",
                                                        style={"marginBottom": "20px"},
                                                    ),
                                                    width=4,
                                                    className="d-flex align-items-center",
                                                ),
                                            ]
                                        ),
                                        html.Div(id="map-stat-container"),
                                    ],
                                ),
                                dbc.Tab(
                                    label="Hero Stats",
                                    tab_id="tab-hero",
                                    children=[
                                        dcc.Dropdown(
                                            id="hero-stat-type",
                                            value="winrate",
                                            clearable=False,
                                            style={"width": "300px", "marginBottom": "20px"},
                                            options=[
                                                {"label": "Winrate by Hero", "value": "winrate"},
                                                {"label": "Games per Hero", "value": "plays"},
                                            ],
                                        ),
                                        dcc.Graph(id="hero-stat-graph"),
                                    ],
                                ),
                                dbc.Tab(
                                    label="Role Stats",
                                    tab_id="tab-role",
                                    children=[
                                        dcc.Dropdown(
                                            id="role-stat-type",
                                            value="winrate",
                                            clearable=False,
                                            style={"width": "300px", "marginBottom": "20px"},
                                            options=[
                                                {"label": "Winrate by Role", "value": "winrate"},
                                                {"label": "Games per Role", "value": "plays"},
                                            ],
                                        ),
                                        dcc.Graph(id="role-stat-graph"),
                                    ],
                                ),
                                dbc.Tab(
                                    dcc.Graph(id="performance-heatmap"),
                                    label="Performance Heatmap",
                                    tab_id="tab-heatmap",
                                ),
                                dbc.Tab(
                                    label="Winrate Trend",
                                    tab_id="tab-trend",
                                    children=[
                                        dbc.Label("Filter by Hero (optional):"),
                                        dcc.Dropdown(
                                            id="hero-filter-dropdown",
                                            placeholder="No hero selected",
                                            className="mb-3",
                                        ),
                                        dcc.Graph(id="winrate-over-time"),
                                    ],
                                ),
                                dbc.Tab(
                                    label="Match History",
                                    tab_id="tab-history",
                                    children=[
                                        dbc.Row(
                                            [
                                                dbc.Col(width=6),
                                                dbc.Col(
                                                    dcc.Dropdown(
                                                        id="history-load-amount-dropdown",
                                                        options=[
                                                            {"label": "Load 10 more", "value": 10},
                                                            {"label": "Load 25 more", "value": 25},
                                                            {"label": "Load 50 more", "value": 50},
                                                        ],
                                                        value=10,
                                                        clearable=False,
                                                    ),
                                                    width=3,
                                                ),
                                                dbc.Col(
                                                    dbc.Button(
                                                        "Load More",
                                                        id="load-more-history-button",
                                                        color="secondary",
                                                        className="w-100",
                                                    ),
                                                    width=3,
                                                ),
                                            ],
                                            className="my-3",
                                        ),
                                        html.Div(
                                            id="history-list-container",
                                            style={"maxHeight": "1000px", "overflowY": "auto"},
                                        ),
                                    ],
                                ),
                            ],
                            id="tabs",
                            active_tab="tab-map",
                        )
                    ],
                    width=9,
                ),
            ]
        ),
        dbc.Row(
            dbc.Col(
                dbc.Card(
                    [
                        dbc.CardHeader(
                            id="stats-header", className="bg-primary text-white"
                        ),
                        dbc.CardBody([html.Div(id="stats-container")]),
                    ]
                ),
                width=12,
            ),
            className="mt-4",
        ),
        html.Div(id="dummy-output", style={"display": "none"}),
    ],
    fluid=True,
)


# --- Helper Functions ---
def get_map_image_url(map_name):
    if not isinstance(map_name, str):
        return f"{APP_DIR}/assets/maps/default.png"
    cleaned_name = map_name.lower().replace(" ", "_").replace("'", "")
    for ext in [".jpg", ".png"]:
        asset_path = f"/assets/maps/{cleaned_name}{ext}"
        if os.path.exists(os.path.join(APP_DIR, "assets", "maps", f"{cleaned_name}{ext}")):
            return asset_path
    return f"{APP_DIR}/assets/maps/default.png"


def get_hero_image_url(hero_name):
    if not isinstance(hero_name, str):
        return f"{APP_DIR}/assets/heroes/default_hero.png"
    base_name = hero_name.lower()
    potential_names = list(
        set(
            [
                base_name.replace(".", "").replace(":", "").replace("ú", "u").replace(" ", "_"),
                base_name.replace(".", "").replace(":", "").replace("ú", "u").replace(" ", ""),
                re.sub(r"[^a-z0-9]", "", base_name),
            ]
        )
    )
    for name in potential_names:
        if not name:
            continue
        for ext in [".png", ".jpg", ".jpeg"]:
            asset_path = f"/assets/heroes/{name}{ext}"
            if os.path.exists(os.path.join(APP_DIR, "assets", "heroes", f"{name}{ext}")):
                return asset_path
    return f"{APP_DIR}/assets/heroes/default_hero.png"


def filter_data(player, season=None, month=None, year=None):
    global df
    if df.empty:
        return pd.DataFrame()
    temp = df[df["Result"].isin(["VICTORY", "DEFEAT", "DRAW"])].copy() # Include DRAW
    if season:
        temp = temp[temp["Season"] == season]
    else:
        if year is not None:
            temp = temp[pd.to_numeric(temp["Year"], errors="coerce") == int(year)]
        if month is not None:
            temp = temp[temp["Month"] == month]
    hero_col, role_col = f"{player} Hero", f"{player} Role"
    if hero_col not in temp.columns or role_col not in temp.columns:
        return pd.DataFrame()
    temp = temp[temp[hero_col].notna() & (temp[hero_col] != "Not in game")]
    if temp.empty:
        return pd.DataFrame()
    temp["Hero"], temp["Role"] = temp[hero_col].str.strip(), temp[role_col].str.strip()
    return temp[temp["Hero"].notna() & (temp["Hero"] != "")]


def calculate_winrate(data, group_col):
    if data.empty or group_col not in data.columns:
        return pd.DataFrame(columns=[group_col, "Win", "Lose", "Draw", "Winrate", "Games"])
    data[group_col] = data[group_col].astype(str).str.strip()
    data = data[data[group_col].notna() & (data[group_col] != "")]
    if data.empty:
        return pd.DataFrame(columns=[group_col, "Win", "Lose", "Draw", "Winrate", "Games"])
    
    grouped = data.groupby([group_col, "Result"]).size().unstack(fill_value=0)
    if "VICTORY" not in grouped: grouped["VICTORY"] = 0
    if "DEFEAT" not in grouped: grouped["DEFEAT"] = 0
    if "DRAW" not in grouped: grouped["DRAW"] = 0
        
    grouped["Games"] = grouped["VICTORY"] + grouped["DEFEAT"] + grouped["DRAW"]
    # Winrate calculation can be defined in multiple ways, e.g., Wins / (Total - Draws)
    # Here we use a simple Wins / Total Games for consistency.
    grouped["Winrate"] = grouped["VICTORY"] / grouped["Games"]
    return grouped.reset_index().sort_values("Winrate", ascending=False)


def generate_summary_table(players_data, min_games):
    header = [html.Thead(html.Tr([html.Th("Statistic")] + [html.Th(p) for p in players_data.keys()]))]
    rows = []
    total_games_row, winrate_row = [html.Td("Total Games")], [html.Td("Winrate")]
    for player, data in players_data.items():
        if not data.empty:
            total = len(data)
            wins = len(data[data["Result"] == "VICTORY"])
            winrate = wins / total if total > 0 else 0
            total_games_row.append(html.Td(f"{total}"))
            winrate_row.append(html.Td(f"{winrate:.1%}"))
        else:
            total_games_row.append(html.Td("0"))
            winrate_row.append(html.Td("N/A"))
    rows.append(html.Tr(total_games_row))
    rows.append(html.Tr(winrate_row))

    most_played_hero_row = [html.Td("Most Played Hero")]
    for player, data in players_data.items():
        if not data.empty:
            try:
                hero = data["Hero"].mode()[0]
                count = data["Hero"].value_counts()[hero]
                most_played_hero_row.append(html.Td(f"{hero} ({count})"))
            except (KeyError, IndexError):
                most_played_hero_row.append(html.Td("N/A"))
        else:
            most_played_hero_row.append(html.Td("N/A"))
    rows.append(html.Tr(most_played_hero_row))

    best_wr_hero_row = [html.Td(f"Best Winrate Hero (>{min_games} games)")]
    for player, data in players_data.items():
        if not data.empty:
            try:
                hero_wr = calculate_winrate(data, "Hero")
                hero_wr_filtered = hero_wr[hero_wr["Games"] >= min_games]
                best_hero = hero_wr_filtered.loc[hero_wr_filtered["Winrate"].idxmax()]
                best_wr_hero_row.append(html.Td(f"{best_hero['Hero']} ({best_hero['Winrate']:.0%})"))
            except (KeyError, IndexError, ValueError):
                best_wr_hero_row.append(html.Td("N/A"))
        else:
            best_wr_hero_row.append(html.Td("N/A"))
    rows.append(html.Tr(best_wr_hero_row))

    return dbc.Table(header + [html.Tbody(rows)], bordered=True, striped=True, hover=True)


def generate_history_layout_simple(games_df):
    if games_df.empty:
        return [dbc.Alert("No match history available.", color="info")]
    history_items = []
    last_season = None
    for idx, game in games_df.iterrows():
        if pd.isna(game.get("Map")): continue
        current_season = game.get("Season")
        if pd.notna(current_season) and current_season != last_season:
            history_items.append(dbc.Alert(f"Season {current_season}", color="secondary", className="my-4 text-center fw-bold"))
            last_season = current_season
        
        map_name, gamemode = game.get("Map", "Unknown"), game.get("Gamemode", "")
        map_image_url = get_map_image_url(map_name)
        date_str = game["Date"].strftime("%Y-%m-%d") if pd.notna(game.get("Date")) else "N/A"
        
        result = game.get("Result")
        if result == "VICTORY": result_color, result_text = "success", "VICTORY"
        elif result == "DEFEAT": result_color, result_text = "danger", "DEFEAT"
        else: result_color, result_text = "warning", "DRAW"

        player_list_items = []
        if config and "known_players" in config:
            for p in config["known_players"]:
                hero = game.get(f"{p} Hero")
                if pd.notna(hero) and hero != "Not in game":
                    role = game.get(f"{p} Role", "N/A")
                    hero_image_url = get_hero_image_url(hero)
                    player_list_items.append(
                        dbc.ListGroupItem(
                            html.Div([
                                html.Img(src=hero_image_url, style={"width": "40px", "height": "40px", "borderRadius": "50%", "objectFit": "cover", "marginRight": "15px"}),
                                html.Div([
                                    html.Div([html.Span(p, className="fw-bold"), html.Span(f" ({role})", className="text-muted", style={"fontSize": "0.9em"})]),
                                    html.Div(hero),
                                ], className="d-flex justify-content-between align-items-center w-100"),
                            ], className="d-flex align-items-center")
                        )
                    )
        
        history_items.append(
            dbc.Card(
                dbc.Row([
                    dbc.Col(html.Img(src=map_image_url, className="img-fluid rounded-start h-100", style={"objectFit": "cover"}), md=3),
                    dbc.Col([
                        dbc.CardHeader(html.Div([
                            html.Div([html.H5(f"{map_name}", className="mb-0"), html.Small(f"{gamemode} • {date_str}", className="text-muted")]),
                            dbc.Badge(result_text, color=result_color, className="ms-auto", style={"height": "fit-content"}),
                        ], className="d-flex justify-content-between align-items-center")),
                        dbc.CardBody(dbc.ListGroup(player_list_items, flush=True), className="p-0"),
                    ], md=9),
                ], className="g-0"),
                className="mb-3",
            )
        )
    return history_items


# --- Callbacks ---
@app.callback(
    Output("dummy-output", "children"),
    Input("update-data-button", "n_clicks"),
    prevent_initial_call=True,
)
def update_data(n_clicks):
    if n_clicks > 0:
        logging.info("Update data button clicked. Fetching new data.")
        load_data(use_local=False)
    return f"Data updated at {pd.Timestamp.now()}"


@app.callback(
    Output("season-dropdown", "options"),
    Output("month-dropdown", "options"),
    Output("year-dropdown", "options"),
    Input("dummy-output", "children"),
)
def update_filter_options(_):
    if df.empty: return [], [], []
    seasons = [{"label": s, "value": s} for s in sorted(df["Season"].dropna().unique(), reverse=True)] if "Season" in df.columns else []
    months = [{"label": m, "value": m} for m in sorted(df["Month"].dropna().unique())] if "Month" in df.columns else []
    years = [{"label": str(int(y)), "value": int(y)} for y in sorted(df["Year"].dropna().unique())] if "Year" in df.columns else []
    return seasons, months, years


@app.callback(
    Output("compare-dropdown", "options"),
    Output("compare-dropdown", "value"),
    Input("player-dropdown", "value"),
)
def update_compare_options(selected_player):
    if not config or not selected_player: return [], []
    options = [{"label": p, "value": p} for p in config["known_players"] if p != selected_player]
    return options, []


@app.callback(
    Output("map-view-type-container", "style"), Input("map-stat-type", "value")
)
def toggle_view_type_visibility(map_stat_type):
    return {"display": "block"} if map_stat_type in ["winrate", "plays"] else {"display": "none"}


@app.callback(
    Output("min-games-slider", "disabled"),
    Output("slider-hint", "children"),
    [Input("tabs", "active_tab"), Input("hero-stat-type", "value"), Input("role-stat-type", "value"), Input("map-stat-type", "value")],
)
def toggle_slider(tab, hero_stat, role_stat, map_stat):
    if (tab == "tab-hero" and hero_stat == "winrate") or \
       (tab == "tab-role" and role_stat == "winrate") or \
       (tab == "tab-map" and map_stat in ["winrate", "gamemode", "attackdef"]):
        return False, ""
    return True, "Only relevant for winrate statistics"


@app.callback(
    Output("history-list-container", "children"),
    Output("history-display-count-store", "data"),
    [Input("load-more-history-button", "n_clicks"), Input("dummy-output", "children")],
    [State("history-display-count-store", "data"), State("history-load-amount-dropdown", "value")],
)
def update_history_display(n_clicks, _, current_store, load_amount):
    global df
    if df.empty:
        return [dbc.Alert("No match history available.", color="danger")], {"count": 10}
    new_count = (current_store.get("count", 10) + load_amount) if ctx.triggered_id == "load-more-history-button" else 10
    games_to_show = df.head(new_count)
    return generate_history_layout_simple(games_to_show), {"count": new_count}


@app.callback(
    [
        Output("map-stat-container", "children"), Output("hero-stat-graph", "figure"),
        Output("role-stat-graph", "figure"), Output("performance-heatmap", "figure"),
        Output("stats-header", "children"), Output("stats-container", "children"),
        Output("winrate-over-time", "figure"), Output("hero-filter-dropdown", "options"),
    ],
    [
        Input("player-dropdown", "value"), Input("min-games-slider", "value"),
        Input("season-dropdown", "value"), Input("month-dropdown", "value"), Input("year-dropdown", "value"),
        Input("hero-filter-dropdown", "value"), Input("hero-stat-type", "value"),
        Input("role-stat-type", "value"), Input("map-stat-type", "value"),
        Input("map-view-type", "value"), Input("compare-dropdown", "value"),
    ],
    [Input("dummy-output", "children")],
)
def update_all_graphs(player, min_games, season, month, year, hero_filter, hero_stat_type, role_stat_type, map_stat_type, map_view_type, compare_players, _):
    if not player:
        empty_fig = go.Figure(layout={"title": "Please select a player"})
        return [html.Div()], empty_fig, empty_fig, empty_fig, "Statistics", html.Div("Please select a player."), empty_fig, []

    if compare_players and len(compare_players) > 2:
        compare_players = compare_players[:2]

    all_players_to_load = [player] + (compare_players if compare_players else [])
    dataframes = {p: filter_data(p, season, month, year) for p in all_players_to_load}
    main_df = dataframes[player]
    
    title_suffix = f"({player}{' vs ' + ', '.join(compare_players) if compare_players else ''})"
    empty_fig = go.Figure(layout={"title": "No data available for this selection"})
    stats_header = f"Overall Statistics"
    
    all_player_data = {p: filter_data(p, season, month, year) for p in config["known_players"]} if config else {}
    stats_container = generate_summary_table(all_player_data, min_games)

    map_stat_output, bar_fig = None, go.Figure()
    attack_def_modes = ["Attack", "Defense", "Symmetric"]
    if map_view_type and not compare_players and map_stat_type in ["winrate", "plays"]:
        pass # Detailed map view logic would go here
    else:
        group_col = {"winrate": "Map", "plays": "Map", "gamemode": "Gamemode", "attackdef": "Team 1 Side"}.get(map_stat_type)
        y_col = "Winrate" if map_stat_type in ["winrate", "gamemode", "attackdef"] else "Games"
        for name, df_to_plot in dataframes.items():
            if not df_to_plot.empty and group_col and group_col in df_to_plot.columns:
                if y_col == "Winrate":
                    stats = calculate_winrate(df_to_plot, group_col)
                    stats = stats[stats["Games"] >= min_games]
                    if not stats.empty:
                        bar_fig.add_trace(go.Bar(x=stats[group_col], y=stats[y_col], name=name, customdata=stats[["Games"]], hovertemplate="<b>%{x}</b><br>Winrate: %{y:.1%}<br>Games: %{customdata[0]}<extra></extra>"))
                else:
                    stats = df_to_plot.groupby(group_col).size().reset_index(name="Games").sort_values("Games", ascending=False)
                    if not stats.empty:
                        bar_fig.add_trace(go.Bar(x=stats[group_col], y=stats[y_col], name=name, hovertemplate="<b>%{x}</b><br>Games: %{y}<extra></extra>"))
        bar_fig.update_layout(title=f"{map_stat_type.title().replace('def', 'Def')} by {group_col} {title_suffix}", barmode="group", yaxis_title=y_col, legend_title="Player")
        if y_col == "Winrate": bar_fig.update_layout(yaxis_tickformat=".0%")
        if not bar_fig.data: bar_fig = empty_fig

    if map_stat_type == "winrate":
        map_stat_output = dbc.Row(dbc.Col(dcc.Graph(figure=bar_fig), width=12))
    else:
        pie_fig = go.Figure()
        pie_data_col = "Gamemode" if map_stat_type == "gamemode" else "Team 1 Side" if map_stat_type == "attackdef" else None
        if pie_data_col:
            pie_data = main_df.copy()
            if pie_data_col == "Team 1 Side": pie_data = pie_data[pie_data["Team 1 Side"].isin(attack_def_modes)]
            pie_data = pie_data.groupby(pie_data_col).size().reset_index(name="Games")
            if not pie_data.empty:
                pie_fig = px.pie(pie_data, names=pie_data_col, values="Games", title=f"{pie_data_col} Distribution")
                pie_fig.update_traces(hovertemplate="<b>%{label}</b><br>Games: %{value}<br>Share: %{percent}<extra></extra>")
            else: pie_fig = empty_fig
        
        if map_stat_type == "plays":
            map_stat_output = dbc.Row([dbc.Col(dcc.Graph(figure=bar_fig), width=12)])
        else:
            map_stat_output = dbc.Row([dbc.Col(dcc.Graph(figure=bar_fig), width=7), dbc.Col(dcc.Graph(figure=pie_fig), width=5)])

    def create_comparison_fig(stat_type, group_col):
        fig = go.Figure()
        y_col = "Winrate" if stat_type == "winrate" else "Games"
        for name, df_to_plot in dataframes.items():
            if not df_to_plot.empty:
                if y_col == "Winrate":
                    stats = calculate_winrate(df_to_plot, group_col)
                    stats = stats[stats["Games"] >= min_games]
                    if not stats.empty:
                        fig.add_trace(go.Bar(x=stats[group_col], y=stats[y_col], name=name, customdata=stats[["Games"]], hovertemplate="<b>%{x}</b><br>Winrate: %{y:.1%}<br>Games: %{customdata[0]}<extra></extra>"))
                else:
                    stats = df_to_plot.groupby(group_col).size().reset_index(name="Games").sort_values("Games", ascending=False)
                    if not stats.empty:
                        fig.add_trace(go.Bar(x=stats[group_col], y=stats[y_col], name=name, hovertemplate="<b>%{x}</b><br>Games: %{y}<extra></extra>"))
        fig.update_layout(title=f"{stat_type.title()} by {group_col} {title_suffix}", barmode="group", yaxis_title=y_col, legend_title="Player")
        if y_col == "Winrate": fig.update_layout(yaxis_tickformat=".0%")
        return fig if fig.data else empty_fig

    hero_fig = create_comparison_fig(hero_stat_type, "Hero")
    role_fig = create_comparison_fig(role_stat_type, "Role")
    heatmap_fig = empty_fig
    if not main_df.empty:
        try:
            pivot = main_df.pivot_table(index="Role", columns="Map", values="Result", aggfunc=lambda x: (x == "VICTORY").sum() / len(x) if len(x) > 0 else 0)
            if not pivot.empty:
                heatmap_fig = px.imshow(pivot, text_auto=".0%", color_continuous_scale="RdYlGn", zmin=0, zmax=1, aspect="auto", title=f"Winrate Heatmap – {player}")
                heatmap_fig.update_traces(hovertemplate="<b>Map: %{x}</b><br><b>Role: %{y}</b><br><b>Winrate: %{z:.1%}</b><extra></extra>")
        except Exception: pass
    
    winrate_fig = go.Figure()
    for name, df_plot in dataframes.items():
        if not df_plot.empty and "Date" in df_plot.columns:
            time_data = df_plot.dropna(subset=["Date"]).copy()
            time_data.sort_values("Date", inplace=True)
            if hero_filter:
                time_data = time_data[time_data["Hero"] == hero_filter]
            if not time_data.empty:
                time_data["Win"] = (time_data["Result"] == "VICTORY").astype(int)
                time_data["GameNum"] = range(1, len(time_data) + 1)
                time_data["CumulativeWinrate"] = time_data["Win"].cumsum() / time_data["GameNum"]
                winrate_fig.add_trace(go.Scatter(x=time_data["GameNum"], y=time_data["CumulativeWinrate"], mode="lines", name=name))
    
    winrate_fig.update_layout(title=f"Winrate Trend {title_suffix}", yaxis_tickformat=".0%", yaxis_title="Winrate", xaxis_title="Game Number", legend_title="Player")
    winrate_fig.update_traces(hovertemplate="<b>Game Number: %{x}</b><br><b>Winrate: %{y:.1%}</b><extra></extra>")
    if not winrate_fig.data: winrate_fig = empty_fig
    
    hero_options = []
    if not main_df.empty:
        heroes = sorted(main_df["Hero"].dropna().unique())
        hero_options = [{"label": html.Div([html.Img(src=get_hero_image_url(h), style={"height": "25px", "marginRight": "10px"}), h]), "value": h} for h in heroes]
        
    return map_stat_output, hero_fig, role_fig, heatmap_fig, stats_header, stats_container, winrate_fig, hero_options


if __name__ == "__main__":
    if not config:
        print("FATAL: config.json not found. Please run the setup script in the root directory of the project first.")
    else:
        # Note: Dash's default logger can be quite verbose.
        # The logging level for the web server can be configured here if needed.
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.WARNING)
        app.run(debug=False)