import dash
import dash_core_components as dcc
import dash_html_components as html
# import plotly.express as px
# import pandas as pd
# import base64

import os
import glob
import flask


# list_of_images = [os.path.abspath(x) for x in glob.glob('{}*.png'.format(IMG_DIR))]
# print(IMG_DIR)
# static_img_route = '/static/'
#
# external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
#
# app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
#
# app.layout = html.Div(children=[
#     html.H1(children='Testowy nagłówek. ęśąćż', style={'textAlign': 'center'}),
#
#     dcc.Dropdown(
#         id='image-dropdown',
#         options=[{'label': i, 'value': i} for i in list_of_images],
#         value=list_of_images[0]
#     ),
#     html.Img(id='image')
#     # html.Div(children=[html.Img(src='data:image/png;base64,{}'.format(encoded_image.decode()), style={'height':'70%', 'width':'70%'})], style={'textAlign': 'center'}),
# ])
#
#
# @app.callback(
#     dash.dependencies.Output('image', 'src'),
#     [dash.dependencies.Input('image-dropdown', 'value')]
# )
# def update_image_src(value):
#     return static_img_route + value
#
#
# @app.server.route("{}<IMG_DIR>.png".format(static_img_route))
# def serve_image(image_path):
#     image_name = '{}.png'.format(image_path)
#     if image_name not in list_of_images:
#         raise Exception('"{}" is excluded from the allowed static files'.format(image_path))
#     return flask.send_from_directory(IMG_DIR, image_name)


base_dir = "../data/pics/"
static_image_route = '/static/'


def helper_path(path):
    return os.path.basename(os.path.normpath(path))


charts = {helper_path(day):
              {helper_path(forecast):
                   [helper_path(pic) for pic in glob.glob(f"{base_dir}{helper_path(day)}/12z/{helper_path(forecast)}/*.png")]
               for forecast in glob.glob(f"{base_dir}{helper_path(day)}/12z/*/")}
          for day in glob.glob(f"{base_dir}*/")}

# print(charts.values())

app = dash.Dash()

app.layout = html.Div([
    html.Div([
        dcc.Dropdown(
            id='day-dropdown',
            options=[{'label': i, 'value': i} for i in charts.keys()],
            value=list(charts.keys())[0]
        )
    ]),
    html.Div([
        dcc.Dropdown(
            id='forecasts-dropdown',
            options=[{'label': i, 'value': i} for i in charts[list(charts.keys())[0]]],
            value=list(charts[list(charts.keys())[0]])[0]
        )
    ]),
    html.Div([
        dcc.Dropdown(
            id='chart-dropdown'
        )
    ]),
    html.Div(id='display-selected-values'),

    html.Img(id='image', style={'height':'70%', 'width':'70%'})
])


@app.callback(
    dash.dependencies.Output('forecasts-dropdown', 'options'),
    [dash.dependencies.Input('day-dropdown', 'value')]
)
def update_forecast_dropdown(name):
    return [{'label': i, 'value': i} for i in charts[name].keys()]


@app.callback(
    dash.dependencies.Output('chart-dropdown', 'options'),
    [dash.dependencies.Input('forecasts-dropdown', 'value'), dash.dependencies.Input('day-dropdown', 'value')]
)
def update_chart_dropdown(name, day):
    return [{'label': i, 'value': i} for i in charts[day][name][::]]


@app.callback(
    dash.dependencies.Output('display-selected-values', 'children'),
    [dash.dependencies.Input('day-dropdown', 'value'), dash.dependencies.Input('forecasts-dropdown', 'value'),
     dash.dependencies.Input('chart-dropdown', 'value')])
def set_display_children(day, forecast, chart):
    return f'you have selected path: {base_dir}{day}/12z/{forecast}/{chart}' if chart != None else 'Path is not selected yet.'

@app.callback(
    dash.dependencies.Output('image', 'src'),
    [dash.dependencies.Input('day-dropdown', 'value'), dash.dependencies.Input('forecasts-dropdown', 'value'),
     dash.dependencies.Input('chart-dropdown', 'value')])
def update_image_src(day, forecast, chart):
    return f"{static_image_route}{day}/12z/{forecast}/{chart}"


# Add a static image route that serves images from desktop
# Be *very* careful here - you don't want to serve arbitrary files
# from your computer or server
@app.server.route('{}<image_path>'.format(static_image_route))
def serve_image(image_path):
    return flask.send_from_directory("C:/Users/Kuba/Desktop/Projekt_GFS/GFS-forecast-web-app/data/pics/20200818/12z/000", "CAPEsurface.png")
    # return flask.send_from_directory(f"{base_dir}{image_path}", f"{image_path}")

if __name__ == '__main__':
    app.run_server(debug=True)
