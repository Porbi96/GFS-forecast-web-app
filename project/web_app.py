import dash
import dash_core_components as dcc
import dash_html_components as html

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

app = dash.Dash()
# print(charts[list(charts.keys())[0]])

app.layout = html.Div([
    # html.Div([
    #
    # ]),
    html.Aside([
        html.Br(),
        html.Div([
            dcc.Dropdown(
                id='day-dropdown',
                options=[{'label': i, 'value': i} for i in charts.keys()],
                value=list(charts.keys())[-1],
                style=dict(
                    width='99%'
                )
            )
        ]),
        html.Br(),

        html.Div([
            dcc.Dropdown(
                id='hour-dropdown',
                # options=[{'label': i, 'value': i} for i in charts[list(charts.keys())[0]]],
                # value=list(charts.keys())[0][0],
                style=dict(
                    width='99%'
                )
            )
        ]),
        html.Br(),

        html.Div([
            dcc.Dropdown(
                id='forecast-dropdown',
                # options=[{'label': i, 'value': i} for i in charts[list(charts.keys())[0]]],
                # value=list(charts[list(charts.keys())[0]])[0],
                style=dict(
                    width='99%'
                )
            )
        ]),
        html.Br(),

        html.Div([
            dcc.Dropdown(
                id='chart-dropdown',
                style=dict(
                    width='99%'
                )
            )
        ]),
        html.Br(),
    ], style={
        'width': '30%',
        # 'margin-right': '15px',
        'float': 'left'
    }),

    html.Main([
        html.Div(id='display-selected-values', style={'textAlign': 'center'}),

        dcc.Slider(
            id='forecast-slider',
            step=None,
            min=0
        ),

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
    [dash.dependencies.Output('forecast-dropdown', 'options'), dash.dependencies.Output('forecast-dropdown', 'value')],
    [dash.dependencies.Input('day-dropdown', 'value'), dash.dependencies.Input('hour-dropdown', 'value')],
    [dash.dependencies.State("forecast-dropdown", "value")]
)
def update_forecast_dropdown(day, hour, current_val):
    options = [{'label': "+{}h".format(int(i)), 'value': i} for i in charts[day][hour].keys()] \
        if hour is not None else [{'label': " ", 'value': " "}]
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
    marks = {int(i): "" for i in charts[day][hour].keys()} if hour is not None else {0: "no data", 6: "no data"}
    max = list(marks.keys())[-1]
    if current_val in list(marks.keys()):
        value = current_val
    else:
        value = list(marks.keys())[0]

    return marks, max, value


@app.callback(
    [dash.dependencies.Output('chart-dropdown', 'options'), dash.dependencies.Output('chart-dropdown', 'value')],
    [dash.dependencies.Input('day-dropdown', 'value'), dash.dependencies.Input('hour-dropdown', 'value'),
     dash.dependencies.Input('forecast-dropdown', 'value')],
    [dash.dependencies.State("chart-dropdown", "value")]
)
def update_chart_dropdown(day, hour, forecast, current_val):
    options = [{'label': i[:-4], 'value': i} for i in charts[day][hour][forecast][::]] \
        if (forecast is not None and forecast is not " ") else [{'label': " ", 'value': " "}]
    if current_val in [option['value'] for option in options]:
        value = current_val
    else:
        value = options[0]['value']

    return options, value


@app.callback(
    dash.dependencies.Output('display-selected-values', 'children'),
    [dash.dependencies.Input('day-dropdown', 'value'), dash.dependencies.Input('hour-dropdown', 'value'),
     dash.dependencies.Input('forecast-dropdown', 'value'), dash.dependencies.Input('chart-dropdown', 'value')])
def set_display_children(day, hour, forecast, chart):
    return f'{day} {hour}:00 UTC +{forecast}h {chart[:-4]}' if chart is not None else 'Chart not selected.'
    # return f'you have selected path: {base_dir}{day}/{hour}/{forecast}/{chart}' if chart is not None else 'Path is not selected yet.'


@app.callback(
    dash.dependencies.Output('image', 'src'),
    [dash.dependencies.Input('day-dropdown', 'value'), dash.dependencies.Input('hour-dropdown', 'value'),
     dash.dependencies.Input('forecast-dropdown', 'value'), dash.dependencies.Input('chart-dropdown', 'value')])
def update_image_src(day, hour, forecast, chart):
    return f"{static_image_route}{day}-{hour}-{forecast}-{chart}"


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
