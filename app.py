import json
import os
from pathlib import Path
from collections import defaultdict

import networkx as nx
from dash import Dash, html, dcc, ctx
from dash.dependencies import Input, Output, State
import dash_cytoscape as cyto


APP_BG = "#07090D"
PANEL_BG = "#11151C"
SURFACE_BG = "#171E27"
GRAPH_CANVAS_BG = "#E8EEF2"
BOUNDARY_BG = "#DDE6EC"
BOUNDARY_BORDER = "#9BAAB8"

TEXT_PRIMARY = "#F7FAFC"
TEXT_MUTED = "#A9B4C0"
TEXT_DARK = "#0F172A"
ACCENT_BLUE = "#21A9FF"

NORMAL_SWC_COLOR = "#2B8CBE"
NORMAL_SWC_BORDER = "#67C7F3"
IMPACTED_SWC_COLOR = "#FF8A4A"
IMPACTED_SWC_BORDER = "#FFC39F"
SELECTED_SIGNAL_COLOR = "#FF9F45"
SELECTED_SIGNAL_BORDER = "#FFE2C3"
HIGHLIGHT_SIGNAL_COLOR = "#FFE5C4"
HIGHLIGHT_SIGNAL_BORDER = "#FFD09A"

SIGNAL_IN_BG = "#DCEAF3"
SIGNAL_OUT_BG = "#CFE4D6"
SIGNAL_BORDER = "#7E93A7"

EDGE_COLOR = "#6D7F90"
EDGE_HIGHLIGHT = "#2296F3"
BOUNDARY_EDGE = "#8AA0B2"

# -----------------------------
# Load data
# -----------------------------
BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "swc_data.json"

with DATA_FILE.open("r", encoding="utf-8") as f:
    data = json.load(f)

swcs = data["swcs"]


# -----------------------------
# Initial scattered SWC positions
# -----------------------------
SWC_POSITIONS = {
    "SWC_INPUT": {"x": 220, "y": 320},
    "SWC1": {"x": 560, "y": 130},
    "SWC2": {"x": 900, "y": 150},
    "SWC3": {"x": 540, "y": 560},
    "SWC4": {"x": 940, "y": 470},
    "SWC5": {"x": 1300, "y": 310},
    "SWC6": {"x": 1520, "y": 150},
    "SWC_OUTPUT": {"x": 1460, "y": 560}
}

PORT_GAP_Y = 34
PORT_X_OFFSET = 85

DEFAULT_INFO = (
    "Click a signal port inside an SWC block, or search/select a signal. "
    "Default trace mode is Upstream."
)

SYSTEM_BOUNDARY_ID = "SYSTEM_BOUNDARY"


# -----------------------------
# Build graph and elements
# -----------------------------
G = nx.DiGraph()
elements = []

output_signal_producer = {}
signal_nodes_by_label = defaultdict(list)
node_meta = {}


# -----------------------------
# Add system boundary container
# -----------------------------
elements.append({
    "data": {
        "id": SYSTEM_BOUNDARY_ID,
        "label": "System Boundary",
        "type": "boundary_box"
    },
    "position": {"x": 930, "y": 350},
    "grabbable": False,
    "selectable": False,
    "locked": True,
    "pannable": False
})

G.add_node(SYSTEM_BOUNDARY_ID, type="boundary_box", label="System Boundary")
node_meta[SYSTEM_BOUNDARY_ID] = {
    "type": "boundary_box",
    "label": "System Boundary",
    "swc_id": None,
    "signal_name": None,
    "port_kind": None
}


# -----------------------------
# Create SWC parent nodes
# -----------------------------
for swc in swcs:
    swc_id = swc["id"]
    swc_name = swc["name"]
    pos = SWC_POSITIONS[swc_id]

    G.add_node(swc_id, type="swc", label=swc_name)

    node_meta[swc_id] = {
        "type": "swc",
        "label": swc_name,
        "swc_id": swc_id,
        "signal_name": None,
        "port_kind": None
    }

    elements.append({
        "data": {
            "id": swc_id,
            "label": swc_name,
            "type": "swc",
            "parent": SYSTEM_BOUNDARY_ID
        },
        "position": {"x": pos["x"], "y": pos["y"]},
        "grabbable": True
    })


# -----------------------------
# Create signal nodes inside SWCs
# -----------------------------
for swc in swcs:
    swc_id = swc["id"]
    pos = SWC_POSITIONS[swc_id]
    col_x = pos["x"]
    col_y = pos["y"]

    inputs = swc.get("inputs", [])
    outputs = swc.get("outputs", [])

    input_start_y = col_y - ((len(inputs) - 1) * PORT_GAP_Y / 2) if inputs else col_y
    output_start_y = col_y - ((len(outputs) - 1) * PORT_GAP_Y / 2) if outputs else col_y

    for i, signal_name in enumerate(inputs):
        node_id = f"{swc_id}__IN__{signal_name}"
        pos_y = input_start_y + i * PORT_GAP_Y

        G.add_node(
            node_id,
            type="signal",
            port_kind="in",
            label=signal_name,
            swc_id=swc_id,
            signal_name=signal_name
        )

        node_meta[node_id] = {
            "type": "signal",
            "label": signal_name,
            "swc_id": swc_id,
            "signal_name": signal_name,
            "port_kind": "in"
        }

        signal_nodes_by_label[signal_name.lower()].append(node_id)

        elements.append({
            "data": {
                "id": node_id,
                "label": signal_name,
                "type": "signal",
                "port_kind": "in",
                "parent": swc_id,
                "swc_id": swc_id,
                "signal_name": signal_name
            },
            "position": {"x": col_x - PORT_X_OFFSET, "y": pos_y},
            "grabbable": False,
            "locked": False
        })

    for i, signal_name in enumerate(outputs):
        node_id = f"{swc_id}__OUT__{signal_name}"
        pos_y = output_start_y + i * PORT_GAP_Y

        G.add_node(
            node_id,
            type="signal",
            port_kind="out",
            label=signal_name,
            swc_id=swc_id,
            signal_name=signal_name
        )

        node_meta[node_id] = {
            "type": "signal",
            "label": signal_name,
            "swc_id": swc_id,
            "signal_name": signal_name,
            "port_kind": "out"
        }

        signal_nodes_by_label[signal_name.lower()].append(node_id)
        output_signal_producer[signal_name] = node_id

        elements.append({
            "data": {
                "id": node_id,
                "label": signal_name,
                "type": "signal",
                "port_kind": "out",
                "parent": swc_id,
                "swc_id": swc_id,
                "signal_name": signal_name
            },
            "position": {"x": col_x + PORT_X_OFFSET, "y": pos_y},
            "grabbable": False,
            "locked": False
        })


# -----------------------------
# Internal dependency edges
# -----------------------------
for swc in swcs:
    swc_id = swc["id"]
    dependencies = swc.get("dependencies", {})

    for output_signal, input_signals in dependencies.items():
        out_id = f"{swc_id}__OUT__{output_signal}"

        for input_signal in input_signals:
            in_id = f"{swc_id}__IN__{input_signal}"

            if G.has_node(in_id) and G.has_node(out_id):
                G.add_edge(in_id, out_id, edge_type="internal")
                elements.append({
                    "data": {
                        "id": f"EDGE__{in_id}__{out_id}",
                        "source": in_id,
                        "target": out_id,
                        "edge_type": "internal"
                    }
                })


# -----------------------------
# Interface edges across SWCs
# -----------------------------
for swc in swcs:
    swc_id = swc["id"]

    for input_signal in swc.get("inputs", []):
        consumer_in_id = f"{swc_id}__IN__{input_signal}"
        producer_out_id = output_signal_producer.get(input_signal)

        if producer_out_id:
            producer_swc = node_meta[producer_out_id]["swc_id"]

            if producer_swc != swc_id:
                G.add_edge(producer_out_id, consumer_in_id, edge_type="interface")
                elements.append({
                    "data": {
                        "id": f"EDGE__{producer_out_id}__{consumer_in_id}",
                        "source": producer_out_id,
                        "target": consumer_in_id,
                        "edge_type": "interface"
                    }
                })


# -----------------------------
# Boundary arrows to show system scope
# External inputs -> InGateway
# OutDispatch -> External outputs
# -----------------------------
boundary_input_signals = [
    "AccelPedal",
    "BrakePedal",
    "WheelSpeedFL",
    "SteeringAngle",
    "BatterySOC"
]

boundary_output_signals = [
    "MotorTorqueCommand",
    "BrakeCommand"
]

left_stub_x = 40
for idx, sig in enumerate(boundary_input_signals):
    stub_id = f"EXT_IN__{sig}"
    target_id = f"SWC_INPUT__OUT__{sig}"
    stub_y = SWC_POSITIONS["SWC_INPUT"]["y"] - 68 + idx * 34

    G.add_node(stub_id, type="boundary", label="")
    node_meta[stub_id] = {
        "type": "boundary",
        "label": sig,
        "swc_id": None,
        "signal_name": sig,
        "port_kind": "external_in"
    }

    elements.append({
        "data": {
            "id": stub_id,
            "label": "",
            "type": "boundary"
        },
        "position": {"x": left_stub_x, "y": stub_y},
        "grabbable": False
    })

    if G.has_node(target_id):
        G.add_edge(stub_id, target_id, edge_type="boundary_in")
        elements.append({
            "data": {
                "id": f"EDGE__{stub_id}__{target_id}",
                "source": stub_id,
                "target": target_id,
                "edge_type": "boundary_in"
            }
        })

right_stub_x = 1880
for idx, sig in enumerate(boundary_output_signals):
    source_id = f"SWC_OUTPUT__OUT__{sig}"
    stub_id = f"EXT_OUT__{sig}"
    stub_y = SWC_POSITIONS["SWC_OUTPUT"]["y"] - 17 + idx * 34

    G.add_node(stub_id, type="boundary", label="")
    node_meta[stub_id] = {
        "type": "boundary",
        "label": sig,
        "swc_id": None,
        "signal_name": sig,
        "port_kind": "external_out"
    }

    elements.append({
        "data": {
            "id": stub_id,
            "label": "",
            "type": "boundary"
        },
        "position": {"x": right_stub_x, "y": stub_y},
        "grabbable": False
    })

    if G.has_node(source_id):
        G.add_edge(source_id, stub_id, edge_type="boundary_out")
        elements.append({
            "data": {
                "id": f"EDGE__{source_id}__{stub_id}",
                "source": source_id,
                "target": stub_id,
                "edge_type": "boundary_out"
            }
        })


# -----------------------------
# Search helpers
# -----------------------------
all_unique_signal_names = sorted(
    {meta["signal_name"] for meta in node_meta.values() if meta.get("type") == "signal"}
)


def dropdown_options_from_search(search_value):
    if not search_value:
        names = all_unique_signal_names[:25]
    else:
        text = search_value.strip().lower()
        exact = [n for n in all_unique_signal_names if n.lower() == text]
        starts = [n for n in all_unique_signal_names if n.lower().startswith(text) and n not in exact]
        contains = [n for n in all_unique_signal_names if text in n.lower() and n not in exact and n not in starts]
        names = (exact + starts + contains)[:25]

    return [{"label": name, "value": name} for name in names]


def find_best_node_for_signal_name(signal_name):
    if not signal_name:
        return None, "Select a signal."

    matches = signal_nodes_by_label.get(signal_name.strip().lower(), [])
    if not matches:
        return None, f'No signal found for "{signal_name}".'

    matches = sorted(
        matches,
        key=lambda n: (
            0 if node_meta[n].get("port_kind") == "out" else 1,
            node_meta[n]["swc_id"]
        )
    )
    chosen = matches[0]
    return chosen, f'Found signal "{signal_name}".'


# -----------------------------
# View helpers
# -----------------------------
def base_stylesheet():
    return [
        {
            "selector": 'node[type="boundary_box"]',
            "style": {
                "shape": "round-rectangle",
                "background-color": BOUNDARY_BG,
                "background-opacity": 0.35,
                "border-color": BOUNDARY_BORDER,
                "border-width": 2,
                "border-style": "dashed",
                "label": "data(label)",
                "color": "#4A5D70",
                "font-size": 14,
                "font-weight": "bold",
                "text-valign": "top",
                "text-halign": "center",
                "padding-top": "40px",
                "padding-left": "70px",
                "padding-right": "35px",
                "padding-bottom": "55px",
                "events": "no"
            }
        },
        {
            "selector": 'node[type="swc"]',
            "style": {
                "shape": "round-rectangle",
                "background-color": NORMAL_SWC_COLOR,
                "border-color": NORMAL_SWC_BORDER,
                "border-width": 2,
                "label": "data(label)",
                "color": TEXT_DARK,
                "font-size": 11,
                "font-weight": "bold",
                "text-valign": "bottom",
                "text-halign": "center",
                "text-margin-y": 18,
                "padding-top": "18px",
                "padding-left": "18px",
                "padding-right": "18px",
                "padding-bottom": "18px",
                "text-wrap": "wrap",
                "text-max-width": "120px"
            }
        },
        {
            "selector": 'node[type="signal"]',
            "style": {
                "shape": "round-rectangle",
                "width": 120,
                "height": 22,
                "background-color": SIGNAL_IN_BG,
                "border-color": SIGNAL_BORDER,
                "border-width": 1,
                "label": "data(label)",
                "font-size": 8,
                "color": TEXT_DARK,
                "text-halign": "center",
                "text-valign": "center",
                "text-wrap": "wrap",
                "text-max-width": "108px"
            }
        },
        {
            "selector": 'node[port_kind="in"]',
            "style": {
                "background-color": SIGNAL_IN_BG
            }
        },
        {
            "selector": 'node[port_kind="out"]',
            "style": {
                "background-color": SIGNAL_OUT_BG
            }
        },
        {
            "selector": 'node[type="boundary"]',
            "style": {
                "shape": "rectangle",
                "width": 1,
                "height": 1,
                "background-opacity": 0,
                "border-width": 0,
                "label": ""
            }
        },
        {
            "selector": "edge",
            "style": {
                "width": 2,
                "line-color": EDGE_COLOR,
                "target-arrow-color": EDGE_COLOR,
                "target-arrow-shape": "triangle",
                "curve-style": "bezier"
            }
        },
        {
            "selector": 'edge[edge_type="internal"]',
            "style": {
                "line-style": "dashed"
            }
        },
        {
            "selector": 'edge[edge_type="interface"]',
            "style": {
                "line-style": "solid"
            }
        },
        {
            "selector": 'edge[edge_type="boundary_in"]',
            "style": {
                "line-style": "solid",
                "line-color": BOUNDARY_EDGE,
                "target-arrow-color": BOUNDARY_EDGE,
                "width": 2
            }
        },
        {
            "selector": 'edge[edge_type="boundary_out"]',
            "style": {
                "line-style": "solid",
                "line-color": BOUNDARY_EDGE,
                "target-arrow-color": BOUNDARY_EDGE,
                "width": 2
            }
        }
    ]


def impacted_swc_ids(node_ids):
    swc_ids = set()

    for node_id in node_ids:
        meta = node_meta.get(node_id)
        if not meta:
            continue

        if meta["type"] == "swc":
            swc_ids.add(node_id)
        elif meta["type"] == "signal":
            swc_ids.add(meta["swc_id"])

    return swc_ids


def edge_ids_for_subgraph(node_ids):
    node_ids = set(node_ids)
    edge_ids = set()

    for u, v in G.edges():
        if u in node_ids and v in node_ids:
            edge_ids.add(f"EDGE__{u}__{v}")

    return edge_ids


def build_highlight_styles(selected_node_id, direction):
    styles = base_stylesheet()

    if selected_node_id not in G.nodes:
        return styles

    if direction == "up":
        impacted_nodes = set(nx.ancestors(G, selected_node_id)) | {selected_node_id}
    elif direction == "down":
        impacted_nodes = {selected_node_id} | set(nx.descendants(G, selected_node_id))
    else:
        impacted_nodes = (
            set(nx.ancestors(G, selected_node_id))
            | {selected_node_id}
            | set(nx.descendants(G, selected_node_id))
        )

    swc_ids = impacted_swc_ids(impacted_nodes)
    highlight_edge_ids = edge_ids_for_subgraph(impacted_nodes)

    for swc_id in swc_ids:
        styles.append({
            "selector": f'node[id = "{swc_id}"]',
            "style": {
                "background-color": IMPACTED_SWC_COLOR,
                "border-color": IMPACTED_SWC_BORDER
            }
        })

    for node_id in impacted_nodes:
        meta = node_meta.get(node_id, {})
        if meta.get("type") == "signal" and node_id != selected_node_id:
            styles.append({
                "selector": f'node[id = "{node_id}"]',
                "style": {
                    "background-color": HIGHLIGHT_SIGNAL_COLOR,
                    "border-color": HIGHLIGHT_SIGNAL_BORDER,
                    "border-width": 2,
                    "color": TEXT_DARK
                }
            })

    selected_meta = node_meta.get(selected_node_id, {})
    if selected_meta.get("type") == "signal":
        styles.append({
            "selector": f'node[id = "{selected_node_id}"]',
            "style": {
                "background-color": SELECTED_SIGNAL_COLOR,
                "border-color": SELECTED_SIGNAL_BORDER,
                "border-width": 3,
                "color": TEXT_DARK
            }
        })
    else:
        styles.append({
            "selector": f'node[id = "{selected_node_id}"]',
            "style": {
                "background-color": IMPACTED_SWC_COLOR,
                "border-color": "#8E0000",
                "border-width": 3
            }
        })

    for edge_id in highlight_edge_ids:
        styles.append({
            "selector": f'edge[id = "{edge_id}"]',
            "style": {
                "line-color": "#FB8C00",
                "target-arrow-color": "#FB8C00",
                "width": 3
            }
        })

    return styles


# -----------------------------
# App layout
# -----------------------------
app = Dash(__name__)

legend_box_style = {
    "display": "flex",
    "alignItems": "center",
    "gap": "8px",
    "marginRight": "18px",
    "color": TEXT_PRIMARY
}

legend_color_style = lambda color: {
    "width": "14px",
    "height": "14px",
    "backgroundColor": color,
    "border": "1px solid rgba(255,255,255,0.35)",
    "borderRadius": "100%",
    "display": "inline-block"
}

app.layout = html.Div(
    style={
        "fontFamily": "Aptos, Inter, Segoe UI, Calibri, Arial, sans-serif",
        "padding": "20px",
        "backgroundColor": APP_BG,
        "minHeight": "100vh",
        "color": TEXT_PRIMARY,
        "boxSizing": "border-box"
    },
    children=[
        html.Div(
            style={
                "display": "flex",
                "gap": "18px",
                "alignItems": "stretch",
                "flexWrap": "wrap"
            },
            children=[
                html.Div(
                    style={
                        "flex": "0 1 460px",
                        "background": PANEL_BG,
                        "borderRadius": "14px",
                        "padding": "22px",
                        "border": "1px solid #222B36",
                        "boxShadow": "0 12px 32px rgba(0,0,0,0.35)"
                    },
                    children=[
                        html.Div(
                            "INTERACTION MATRIX",
                            style={
                                "color": ACCENT_BLUE,
                                "fontWeight": "700",
                                "fontSize": "20px",
                                "letterSpacing": "0.5px",
                                "marginBottom": "8px"
                            }
                        ),
                        html.H1(
                            "Accelerating ADAS Issue Triage",
                            style={
                                "margin": "0 0 14px 0",
                                "fontSize": "54px",
                                "lineHeight": "1.05",
                                "fontWeight": "700"
                            }
                        ),
                        html.P(
                            "Visualize cross-module signal dependencies, isolate impact paths, and"
                            " identify ownership boundaries faster.",
                            style={"color": TEXT_MUTED, "fontSize": "24px", "lineHeight": "1.35"}
                        ),
                        html.Div(
                            style={
                                "height": "4px",
                                "width": "70%",
                                "background": f"linear-gradient(90deg, {ACCENT_BLUE}, transparent)",
                                "margin": "18px 0 20px 0"
                            }
                        ),
                        html.Div(
                            style={"display": "flex", "gap": "10px", "flexWrap": "wrap", "marginBottom": "18px"},
                            children=[
                                html.Div("Connected Signal Graph", style={
                                    "padding": "8px 12px", "background": SURFACE_BG, "borderRadius": "999px",
                                    "border": "1px solid #293443", "fontWeight": "600"
                                }),
                                html.Div("Upstream / Downstream Trace", style={
                                    "padding": "8px 12px", "background": SURFACE_BG, "borderRadius": "999px",
                                    "border": "1px solid #293443", "fontWeight": "600"
                                }),
                                html.Div("Owner & Impact Context", style={
                                    "padding": "8px 12px", "background": SURFACE_BG, "borderRadius": "999px",
                                    "border": "1px solid #293443", "fontWeight": "600"
                                })
                            ]
                        ),
                        html.Div(
                            style={
                                "display": "flex",
                                "gap": "10px",
                                "alignItems": "center",
                                "flexWrap": "wrap",
                                "marginBottom": "12px"
                            },
                            children=[
                                html.Label("Trace direction", style={"fontWeight": "700", "color": TEXT_PRIMARY}),
                                dcc.RadioItems(
                                    id="direction",
                                    options=[
                                        {"label": "Upstream", "value": "up"},
                                        {"label": "Downstream", "value": "down"},
                                        {"label": "Both", "value": "both"}
                                    ],
                                    value="up",
                                    inline=True,
                                    style={"color": TEXT_PRIMARY},
                                    labelStyle={
                                        "color": TEXT_PRIMARY,
                                        "marginRight": "14px",
                                        "fontWeight": "600"
                                    },
                                    inputStyle={"marginRight": "6px"}
                                )
                            ]
                        ),
                        html.Div(
                            style={"display": "flex", "gap": "10px", "alignItems": "center", "flexWrap": "wrap"},
                            children=[
                                dcc.Dropdown(
                                    id="signal-search",
                                    options=dropdown_options_from_search(""),
                                    placeholder="Search/select signal...",
                                    searchable=True,
                                    clearable=True,
                                    style={
                                        "flex": "1 1 260px",
                                        "minWidth": "220px",
                                        "color": TEXT_DARK
                                    }
                                ),
                                html.Button(
                                    "Go",
                                    id="go-btn",
                                    n_clicks=0,
                                    style={
                                        "backgroundColor": ACCENT_BLUE,
                                        "color": "white",
                                        "border": "none",
                                        "padding": "10px 16px",
                                        "borderRadius": "10px",
                                        "cursor": "pointer",
                                        "fontWeight": "700"
                                    }
                                ),
                                html.Button(
                                    "Reset",
                                    id="reset-btn",
                                    n_clicks=0,
                                    style={
                                        "backgroundColor": SURFACE_BG,
                                        "color": "white",
                                        "border": "1px solid #314052",
                                        "padding": "10px 16px",
                                        "borderRadius": "10px",
                                        "cursor": "pointer",
                                        "fontWeight": "700"
                                    }
                                )
                            ]
                        ),
                        html.Div(
                            style={
                                "display": "flex",
                                "alignItems": "center",
                                "flexWrap": "wrap",
                                "gap": "4px 8px",
                                "marginTop": "14px",
                                "paddingTop": "10px",
                                "borderTop": "1px solid #273240"
                            },
                            children=[
                                html.Div(style=legend_box_style, children=[
                                    html.Span(style=legend_color_style(NORMAL_SWC_COLOR)),
                                    html.Span("Normal SWC")
                                ]),
                                html.Div(style=legend_box_style, children=[
                                    html.Span(style=legend_color_style(IMPACTED_SWC_COLOR)),
                                    html.Span("Impacted SWC")
                                ]),
                                html.Div(style=legend_box_style, children=[
                                    html.Span(style=legend_color_style(SELECTED_SIGNAL_COLOR)),
                                    html.Span("Selected signal")
                                ]),
                                html.Div(style=legend_box_style, children=[
                                    html.Span(style=legend_color_style(HIGHLIGHT_SIGNAL_COLOR)),
                                    html.Span("Impacted signal")
                                ])
                            ]
                        ),
                        html.Div(
                            id="status-text",
                            children=DEFAULT_INFO,
                            style={
                                "marginTop": "12px",
                                "padding": "12px",
                                "background": SURFACE_BG,
                                "border": "1px solid #2A3543",
                                "borderRadius": "10px",
                                "color": TEXT_MUTED
                            }
                        )
                    ]
                ),
                html.Div(
                    style={
                        "flex": "1 1 780px",
                        "minWidth": "520px",
                        "background": "#0F131B",
                        "borderRadius": "14px",
                        "padding": "14px",
                        "border": "1px solid #222B36",
                        "boxShadow": "0 12px 32px rgba(0,0,0,0.35)"
                    },
                    children=[
                        cyto.Cytoscape(
                            id="graph",
                            elements=elements,
                            layout={"name": "preset", "fit": True, "padding": 30},
                            style={
                                "width": "100%",
                                "height": "82vh",
                                "minHeight": "760px",
                                "border": "1px solid #334354",
                                "borderRadius": "10px",
                                "backgroundColor": GRAPH_CANVAS_BG
                            },
                            stylesheet=base_stylesheet(),
                            minZoom=0.3,
                            maxZoom=2.5,
                            userZoomingEnabled=True,
                            userPanningEnabled=True,
                            boxSelectionEnabled=False,
                            autoungrabify=False
                        )
                    ]
                )
            ]
        )
    ]
)


# -----------------------------
# Update dropdown suggestions
# -----------------------------
@app.callback(
    Output("signal-search", "options"),
    Input("signal-search", "search_value")
)
def update_dropdown_options(search_value):
    return dropdown_options_from_search(search_value)


# -----------------------------
# Main interaction callback
# -----------------------------
@app.callback(
    Output("graph", "stylesheet"),
    Output("status-text", "children"),
    Output("signal-search", "value"),
    Input("graph", "tapNodeData"),
    Input("go-btn", "n_clicks"),
    Input("reset-btn", "n_clicks"),
    State("direction", "value"),
    State("signal-search", "value"),
    prevent_initial_call=False
)
def update_view(tap_node_data, go_clicks, reset_clicks, direction, selected_signal_name):
    trigger = ctx.triggered_id

    if trigger is None:
        return base_stylesheet(), DEFAULT_INFO, None

    if trigger == "reset-btn":
        return base_stylesheet(), "View reset. Select a new signal to start again.", None

    if trigger == "go-btn":
        node_id, message = find_best_node_for_signal_name(selected_signal_name)
        if node_id:
            styles = build_highlight_styles(node_id, direction)
            return styles, message, selected_signal_name
        return base_stylesheet(), message, selected_signal_name

    if trigger == "graph":
        if not tap_node_data:
            return base_stylesheet(), DEFAULT_INFO, selected_signal_name

        node_id = tap_node_data["id"]
        label = tap_node_data.get("label", node_id)
        node_type = tap_node_data.get("type", "")

        styles = build_highlight_styles(node_id, direction)

        if node_type == "signal":
            msg = f'Selected signal "{label}" with trace mode "{direction}".'
            search_value = label
        else:
            msg = f'Selected SWC "{label}" with trace mode "{direction}".'
            search_value = selected_signal_name

        return styles, msg, search_value

    return base_stylesheet(), DEFAULT_INFO, selected_signal_name

server = app.server

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8050))
    app.run(host="0.0.0.0", port=port, debug=False)
