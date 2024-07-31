import time
import os
import dash
from dash import Dash, dcc, html, Input, Output
import plotly.graph_objects as go
import math

app = dash.Dash(requests_pathname_prefix="/dashboard/")

# Initialize variables
ratio, length, point0_x, point0_y, current_x, current_y = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
origin_x, origin_y, height, velocity = 0.0, 0.0, 0.0, 0.0
gravitational, distance, totaltime = [0.0], [0.0], [0.0]
gravitational0, kinetic = 0.0, 0.0
periodtime = 0.0
mass = 109 / 100
onetime, flag = True, 0
starttime, periodstarttime = time.time(), time.time()
file_path = "pendulum_values.txt"

app.layout = html.Div(
    html.Div(
        [
            html.Div(id="live-update-text"),
            dcc.Graph(id="graph"),
            dcc.Graph(id="gravitationalgraph"),
            dcc.Interval(
                id="interval-component",
                interval=1 * 100,  # in milliseconds
                n_intervals=1,
            ),
        ]
    )
)


def euclidean(p1, p2):
    """Calculate Euclidean distance between two points."""
    return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)


@app.callback(
    Output("live-update-text", "children"),
    Input("interval-component", "n_intervals"),
)
def update_metrics(n):
    global ratio, length, point0_x, point0_y, current_x, current_y, distance, starttime, periodstarttime, totaltime, origin_x, origin_y, gravitational0, kinetic, onetime, flag, periodtime

    if os.path.exists(file_path):
        with open(file_path, "r") as file:
            values = {
                line.split(":")[0].strip(): float(line.split(":")[1]) for line in file
            }

        ratio, length, point0_x, point0_y, current_x, current_y = (
            values.get("Ratio", 0.0),
            values.get("Length", 0.0),
            values.get("Point 0 X", 0.0),
            values.get("Point 0 Y", 0.0),
            values.get("Current Point X", 0.0),
            values.get("Current Point Y", 0.0),
        )
        flag, origin_x, origin_y = (
            values.get("Flag", 0),
            point0_x,
            point0_y - (length / ratio) if ratio > 0 else 0,
        )
        length = length / 100

        if flag == 0:
            gravitational0, starttime, periodstarttime = 0.0, time.time(), time.time()

        if current_x != point0_x:
            totaltime.append(round(time.time() - starttime, 2))
            periodtime = round(time.time() - periodstarttime, 2)

        if current_x > point0_x:
            distance.append(
                euclidean((current_x, current_y), (point0_x, point0_y)) * ratio
            )
        elif current_x < point0_x:
            distance.append(
                euclidean((current_x, current_y), (point0_x, point0_y)) * -ratio
            )

        T = 2 * math.pi * (math.sqrt(length / 9.83))
        angle = math.degrees(math.atan2(current_x - origin_x, current_y - origin_y))
        angleradians = math.radians(angle)
        height = length - (length * math.cos(angleradians))
        gravitational.append(mass * 9.83 * height)

        if (flag == 1 and onetime) or all(
            gravitational[i] > gravitational[-1] for i in range(-2, -6, -1)
        ):
            if onetime:
                gravitational0, onetime, periodtime, periodstarttime = (
                    mass * 9.83 * height,
                    False,
                    0.0,
                    time.time(),
                )
            else:
                now = (
                    gravitational[-2]
                    + gravitational[-3]
                    + gravitational[-4]
                    + gravitational[-5]
                ) / 4
                if now > gravitational[-1]:
                    gravitational0 = now
            periodtime = 0.0

        style = {"padding": "5px", "fontSize": "16px"}
        return [
            html.Span(f"{key}: {value:.2f}", style=style)
            for key, value in {
                "Ratio": ratio,
                "Length": length,
                "Point 0 X": point0_x,
                "Point 0 Y": point0_y,
                "Current X": current_x,
                "Current Y": current_y,
                "Origin X": origin_x,
                "Origin Y": origin_y,
                "Angle": angle,
                "ENERGIATOTAL": gravitational0,
                "FLAG": flag,
                "Distance from Center": distance[-1],
                "Total Time": totaltime[-1],
                "Total Period Time": periodtime,
            }.items()
        ]
    else:
        return "File not found"


@app.callback(Output("graph", "figure"), Input("interval-component", "n_intervals"))
def display_graph(n):
    global totaltime, distance
    fig = go.Figure(
        go.Scatter(
            x=totaltime,
            y=distance,
            mode="lines+markers",
            name="Pendulum",
            marker=dict(color="rgb(105, 219, 124)"),
        )
    )
    fig.update_layout(
        title="Pendulum Motion",
        xaxis_title="Total Time (s)",
        yaxis_title="Distance from Center (cm)",
        paper_bgcolor="rgb(13, 17, 23)",
        plot_bgcolor="rgb(22, 27, 34)",
        font=dict(color="rgb(230, 237, 243)"),
    )
    return fig


@app.callback(
    Output("gravitationalgraph", "figure"), Input("interval-component", "n_intervals")
)
def display_gravitationalgraph(n):
    global gravitational, gravitational0
    kinetic = max(0, gravitational0 - gravitational[-1])
    colors = ["rgb(255, 169, 77)", "rgb(121, 192, 255)", "rgb(174, 62, 201)"]

    fig = go.Figure(
        go.Bar(
            x=["Gravitational Energy", "Kinetic Energy", "Total Energy"],
            y=[gravitational[-1], kinetic, gravitational0],
            name="Energys",
            marker_color=colors,
        )
    )
    fig.update_layout(
        title="Energys",
        yaxis_title="Joules (J)",
        paper_bgcolor="rgb(13, 17, 23)",
        plot_bgcolor="rgb(22, 27, 34)",
        font=dict(color="rgb(230, 237, 243)"),
    )
    return fig


if __name__ == "__main__":
    app.run_server(debug=True)
