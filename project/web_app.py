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
              {helper_path(forecast):
                   [helper_path(pic) for pic in glob.glob(f"{base_dir}{helper_path(day)}/12z/{helper_path(forecast)}/*.png")]
               for forecast in glob.glob(f"{base_dir}{helper_path(day)}/12z/*/")}
          for day in glob.glob(f"{base_dir}*/")}

app = dash.Dash()

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
                value=list(charts.keys())[0],
                style=dict(
                    width='99%'
                )
            )
        ]),
        html.Br(),

        html.Div([
            dcc.Dropdown(
                id='forecast-dropdown',
                options=[{'label': i, 'value': i} for i in charts[list(charts.keys())[0]]],
                value=list(charts[list(charts.keys())[0]])[0],
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

    html.Div(id='display-selected-values', style={'textAlign': 'center'}),

    html.Img(id='image',
             style={'height':'70%',
                    'width':'70%',
                    'textAlign': 'center'
                    })
])


@app.callback(
    dash.dependencies.Output('forecast-dropdown', 'options'),
    [dash.dependencies.Input('day-dropdown', 'value')]
)
def update_forecast_dropdown(name):
    return [{'label': i, 'value': i} for i in charts[name].keys()]


@app.callback(
    dash.dependencies.Output('chart-dropdown', 'options'),
    [dash.dependencies.Input('forecast-dropdown', 'value'), dash.dependencies.Input('day-dropdown', 'value')]
)
def update_chart_dropdown(name, day):
    return [{'label': i, 'value': i} for i in charts[day][name][::]]


@app.callback(
    dash.dependencies.Output('display-selected-values', 'children'),
    [dash.dependencies.Input('day-dropdown', 'value'), dash.dependencies.Input('forecast-dropdown', 'value'),
     dash.dependencies.Input('chart-dropdown', 'value')])
def set_display_children(day, forecast, chart):
    return f'you have selected path: {base_dir}{day}/12z/{forecast}/{chart}' if chart is not None else 'Path is not selected yet.'

@app.callback(
    dash.dependencies.Output('image', 'src'),
    [dash.dependencies.Input('day-dropdown', 'value'), dash.dependencies.Input('forecast-dropdown', 'value'),
     dash.dependencies.Input('chart-dropdown', 'value')])
def update_image_src(day, forecast, chart):
    return f"{static_image_route}{day}-12z-{forecast}-{chart}"

@app.server.route('{}<img_path>'.format(static_image_route))
def serve_image(img_path):
    if ".." in img_path:
        raise Exception('"{}" is excluded from the allowed static paths'.format(img_path))
    image_path = img_path.replace('-', '/')
    image_dir = base_dir + image_path[:17]
    image_name = image_path[17:]
    # return f"dir: {image_dir} name: {image_name}"
    return flask.send_from_directory(image_dir, image_name)
    # return flask.send_from_directory(f"{base_dir}{image_path}", f"{image_path}")

if __name__ == '__main__':
    app.run_server(debug=True)
