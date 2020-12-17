import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc

import os
import glob
import flask

from datetime import datetime, timedelta

base_dir = f"{os.path.dirname(__file__)}/../data/pics/"
static_image_route = '/static/'

PARAM_DESCRIPTIONS = {
    "CAPE surface": [html.Strong("Convective available potential energy"),
                     """\nA measure of the amount of energy available for convection. CAPE is directly related to the maximum potential vertical speed within an updraft. Higher values indicate greater potential for severe weather. Observed values in thunderstorm environments often may exceed 1000 J/kg, and in extreme cases may exceed 5000 J/kg.
                     However, as with other indices or indicators, there are no threshold values above which severe weather becomes imminent """],

    "CIN surface": [html.Strong("Convective inhibition"),
                    """\nA measure of the amount of energy needed in order to initiate convection. Values of CIN typically reflect the strength of the cap. They are obtained on a sounding by computing the area enclosed between the environmental temperature profile and the path of a rising air parcel, over the layer within which the latter is cooler than the former."""],

    "Dew point 2m": [html.Strong("Dew point temperature"),
                     """\nA measure of atmospheric moisture. It is the temperature to which air must be cooled in order to reach saturation (assuming air pressure and moisture content are constant). A higher dew point indicates more moisture present in the air."""],

    "LI surface": [html.Strong("Lifted index"),
                   """\nA common measure of atmospheric instability. Its value is obtained by computing the temperature that air near the ground would have if it were lifted to some higher level (around 5500m, usually) and comparing that temperature to the actual temperature at that level. Negative values indicate instability - the more negative, the more unstable the air is, and the stronger the updrafts are likely to be with any developing thunderstorms. 
                   However there are no "magic numbers" or threshold LI values below which severe weather becomes imminent. """],

    "Precipitation ground 6h": [html.Strong("Precipitation"),
                                """\n    The process where water vapor condenses in the atmosphere to form water droplets that fall to the Earth as rain, sleet, snow, hail, etc."""],

    "Pressure sea lvl": [html.Strong("Pressure"),
                         """\nThe exertion of force upon a surface by a fluid (e.g., the atmosphere) in contact with it. Here, reduced to sea level."""],

    "Temperature 2m": [html.Strong("Temperature"),
                       """\nThe temperature is a measure of the internal energy that a substance contains. This is the most measured quantity in the atmosphere."""],

    "Wind 10m": [html.Strong("Wind"),
                 """\nThe horizontal motion of the air past a given point. Winds begin with differences in air pressures. Pressure that's higher at one place than another sets up a force pushing from the high toward the low pressure. The greater the difference in pressures, the stronger the force. The distance between the area of high pressure and the area of low pressure also determines how fast the moving air is accelerated."""],

    "Wind 250hPa": [html.Strong("Wind"),
                    """\nThe horizontal motion of the air past a given point. Winds begin with differences in air pressures. Pressure that's higher at one place than another sets up a force pushing from the high toward the low pressure. The greater the difference in pressures, the stronger the force. The distance between the area of high pressure and the area of low pressure also determines how fast the moving air is accelerated."""],

    "Wind gust ground": [html.Strong("Wind gust"),
                         """\nRapid fluctuations in the wind speed with a variation of 10 knots (5,14 m/s) or more between peaks and lulls. The speed of the gust will be the maximum instantaneous wind speed."""],
}


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
server = app.server

app.layout = html.Div([
    dbc.Modal(
        [
            dbc.ModalHeader("Hello!"),
            dbc.ModalBody("""This is a web application, which visualizes NOAA's GFS numerical weather forecast (some of major elements) for Poland teritory.
            
            Instructions:
            1. Choose from which date and hour you'd like to see forecast calculations (base date and hour).
            2. Choose which data you'd like to see (chart).
            3. Use slider on the top to choose exact date and hour of predicted weather data (forecast).
            
            Charts will appear automatically. You can press right button on image and copy direct link to it or save it.
            
            Data is being downloaded and prepared just when it appears on NOAA's servers, usually every 6 hours.
            
            Parameters' descriptions were found at NOAA's National Weather Service's Glossary.
            
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

    html.Br(),
    html.Div([
        html.Div(id='forecast-text', children='Forecast:',
                 style={
                     'margin-left': '20px',
                     'color': 'white',
                     # 'backgroundColor': '#181a3d'
                 }),
        html.Div([
            dcc.Slider(
                id='forecast-slider',
                step=None,
                min=0,
                updatemode='drag'
            ),
            html.Br()
        ],
            style={
                'width': '100%'
            }
        )
    ], style={'backgroundColor': '#003d66'}),

    html.Aside([
        html.Br(),

        html.Div(id='day-text', children='Base day:', style={'margin-left': '10px'}),
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

        html.Div(id='hour-text', children='Base hour:', style={'margin-left': '10px'}),
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

        html.Div(id='chart-text', children='Chart:', style={'margin-left': '10px'}),
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

        html.Div([
            dbc.Button("Info & instructions", id="info-button", className="mr-1")
        ], style={
            'textAlign': 'center'
        }),
        html.Br(),

        html.Div(id='description', children=" ", style={'margin-left': '10px', 'white-space': 'pre-line'})

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
            interval=5 * 60 * 1000,  # in milliseconds
            n_intervals=0
        )
    ], style={
        'width': '70%',
        'float': 'right'
    })

], style={'backgroundColor': '#181a3d'})


@app.callback(
    dash.dependencies.Output("description", "children"),
    [dash.dependencies.Input("chart-dropdown", "value")]
)
def update_description(chart):
    return PARAM_DESCRIPTIONS[chart[:-4]]


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
    base_datetime = datetime.strptime(f"{day}-{hour}", "%Y%m%d-%Hz")
    marks = {
        int(i): {'label': "{}".format((base_datetime + timedelta(hours=int(i))).strftime('%d.%m\n%H:00')
                                      if int(i) % 12 == 0 else ''),
                 'style': {'white-space': 'pre-line'}}
        for i in charts[day][hour].keys()
    } if all(v is not None for v in [day, hour]) else {None: "no data"}
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
