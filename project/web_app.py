import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc

import os
import glob
import flask

base_dir = f"{os.path.dirname(__file__)}\\..\\data\\pics\\"
static_image_route = '/static/'


def helper_path(path):
    return os.path.basename(os.path.normpath(path))


charts = {helper_path(day):
            {helper_path(hour):
                {helper_path(forecast):
                    [helper_path(pic) for pic in
                     glob.glob(f"{base_dir}{helper_path(day)}/{helper_path(hour)}/{helper_path(forecast)}/*.png")]
                 for forecast in glob.glob(f"{base_dir}{helper_path(day)}/{helper_path(hour)}/*/")}
             for hour in glob.glob(f"{base_dir}{helper_path(day)}/*/")}
          for day in glob.glob(f"{base_dir}*/")}

app = dash.Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])
# print(charts[list(charts.keys())[0]])

app.layout = html.Div([
    html.Br(),
    dbc.Modal(
        [
            dbc.ModalHeader("Hello!"),
            dbc.ModalBody("""
            This is a simple web application, which visualizes GFS numerical weather forecast (some of major elements) for Poland teritory.
            \n
            Author: Jakub Poręba
            MIT License
            Github: https://github.com/Porbi96/GFS-forecast-web-app
            @2020
            """),
            dbc.ModalFooter(
                dbc.Button("Close", id="info-close", className="ml-auto")
            ),
        ],
        id="info-modal",
        # size="sm",
        style={
            'white-space': 'pre-line'
        }
    ),

    html.Div([
        dcc.Slider(
            id='forecast-slider',
            step=None,
            min=0,
            updatemode='drag'
        )],
        style={
            'width': '95%',
            'padding-left': '2%'
        }
    ),
    html.Aside([
        html.Br(),
        html.Div([
            dcc.Dropdown(
                id='day-dropdown',
                options=[{'label': i, 'value': i} for i in charts.keys()],
                value=list(charts.keys())[-1],
                clearable=False,
                style={
                    'width': '99%',
                    'margin-left': '5px'
                }
            )
        ]),
        html.Br(),

        html.Div([
            dcc.Dropdown(
                id='hour-dropdown',
                clearable=False,
                style={
                    'width': '99%',
                    'margin-left': '5px'
                }
            )
        ]),
        html.Br(),

        html.Div([
            dcc.Dropdown(
                id='chart-dropdown',
                clearable=False,
                style={
                    'width': '99%',
                    'margin-left': '5px'
                }

            )
        ]),
        html.Br(),

        html.Div(id='display-selected-values', style={'textAlign': 'center'}),
        html.Br(), html.Br(),

        html.Div([
            dbc.Button("Info", id="info-button", className="mr-1")
        ], style={
            'bottom': '10px'
        })

    ], style={
        'width': '30%',
        'float': 'left'
    }),

    html.Main([
        html.Img(id='image',
                 style={'height': '100%',
                        'width': '100%',
                        'textAlign': 'center'
                        }),

        dcc.Interval(
            id='day-interval',
            interval=10 * 60 * 1000,  # in milliseconds
            n_intervals=0
        )
    ], style={
        'width': '70%',
        'float': 'right'
    })

])


@app.callback(
    dash.dependencies.Output("info-modal", "is_open"),
    [dash.dependencies.Input("info-button", "n_clicks"), dash.dependencies.Input("info-close", "n_clicks")],
    [dash.dependencies.State("info-modal", "is_open")],
)
def toggle_modal(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open


@app.callback(
    [dash.dependencies.Output('day-dropdown', 'options'), dash.dependencies.Output('day-dropdown', 'value')],
    [dash.dependencies.Input('day-interval', 'n_intervals')],
    [dash.dependencies.State("day-dropdown", "value")]
)
def update_day_dropdown(n, current_val):
    global charts
    charts = {helper_path(day):
                  {helper_path(hour):
                       {helper_path(forecast):
                            [helper_path(pic) for pic in
                             glob.glob(
                                 f"{base_dir}{helper_path(day)}/{helper_path(hour)}/{helper_path(forecast)}/*.png")]
                        for forecast in glob.glob(f"{base_dir}{helper_path(day)}/{helper_path(hour)}/*/")}
                   for hour in glob.glob(f"{base_dir}{helper_path(day)}/*/")}
              for day in glob.glob(f"{base_dir}*/")}

    options = [{'label': f"{i[:4]}-{i[4:6]}-{i[6:]}", 'value': i} for i in charts.keys()]
    if current_val in [option['value'] for option in options]:
        value = current_val
    else:
        value = options[-1]['value']

    return options, value


@app.callback(
    [dash.dependencies.Output('hour-dropdown', 'options'), dash.dependencies.Output('hour-dropdown', 'value')],
    [dash.dependencies.Input('day-dropdown', 'value')],
    [dash.dependencies.State("hour-dropdown", "value")]
)
def update_hour_dropdown(day, current_val):
    options = [{'label': "{:02}:00 UTC".format(int(i[:-1])), 'value': i} for i in charts[day].keys()]
    if current_val in [option['value'] for option in options]:
        value = current_val
    else:
        value = options[0]['value']

    return options, value


@app.callback(
    [dash.dependencies.Output('forecast-slider', 'marks'), dash.dependencies.Output('forecast-slider', 'max'),
     dash.dependencies.Output('forecast-slider', 'value')],
    [dash.dependencies.Input('day-dropdown', 'value'), dash.dependencies.Input('hour-dropdown', 'value')],
    [dash.dependencies.State("forecast-slider", "value")]
)
def update_forecast_slider(day, hour, current_val):
    marks = {int(i): f"{int(i) if int(i)%12==0 else ''}" for i in charts[day][hour].keys()} if all(v is not None for v in [day, hour]) \
        else {None: "no data", None: "no data"}
    max = list(marks.keys())[-1]
    if current_val in list(marks.keys()):
        value = current_val
    else:
        value = list(marks.keys())[0]

    return marks, max, value


@app.callback(
    [dash.dependencies.Output('chart-dropdown', 'options'), dash.dependencies.Output('chart-dropdown', 'value')],
    [dash.dependencies.Input('day-dropdown', 'value'), dash.dependencies.Input('hour-dropdown', 'value'),
     dash.dependencies.Input('forecast-slider', 'value')],
    [dash.dependencies.State("chart-dropdown", "value")]
)
def update_chart_dropdown(day, hour, forecast, current_val):
    options = [{'label': i[:-4], 'value': i} for i in charts[day][hour][f'{forecast:03}'][::]] \
        if all(v not in [None, " "] for v in [day, hour, forecast]) else [{'label': " ", 'value': " "}]
    if current_val in [option['value'] for option in options]:
        value = current_val
    else:
        value = options[0]['value']

    return options, value


@app.callback(
    dash.dependencies.Output('display-selected-values', 'children'),
    [dash.dependencies.Input('day-dropdown', 'value'), dash.dependencies.Input('hour-dropdown', 'value'),
     dash.dependencies.Input('forecast-slider', 'value'), dash.dependencies.Input('chart-dropdown', 'value')])
def set_display_children(day, hour, forecast, chart):
    return 'Chart not selected.' if any(v is None for v in [chart, day, hour, forecast]) else f'{day} {hour[:-1]}:00 UTC +{forecast}h {chart[:-4]}'
    # return f'you have selected path: {base_dir}{day}/{hour}/{forecast}/{chart}' if chart is not None else 'Path is not selected yet.'


@app.callback(
    dash.dependencies.Output('image', 'src'),
    [dash.dependencies.Input('day-dropdown', 'value'), dash.dependencies.Input('hour-dropdown', 'value'),
     dash.dependencies.Input('forecast-slider', 'value'), dash.dependencies.Input('chart-dropdown', 'value')])
def update_image_src(day, hour, forecast, chart):
    return f"{static_image_route}{day}-{hour}-{forecast:03}-{chart}" if forecast is not None \
        else f"{static_image_route}{day}-{hour}-000-{chart}"


@app.server.route('{}<img_path>'.format(static_image_route))
def serve_image(img_path):
    if ".." in img_path:
        raise Exception('"{}" is excluded from the allowed static paths'.format(img_path))
    image_path = img_path.replace('-', '/')
    image_dir = base_dir + image_path[:17]
    image_name = image_path[17:]
    return flask.send_from_directory(image_dir, image_name)


if __name__ == '__main__':
    app.run_server(debug=True)
