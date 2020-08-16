import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.express as px
import pandas as pd
import base64

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
encoded_image = base64.b64encode(open('test8.png', 'rb').read())

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

df = pd.DataFrame({
    "Fruit": ["Apples", "Oranges", "Bananas", "Apples", "Oranges", "Bananas"],
    "Amount": [4, 1, 2, 2, 4, 5],
    "City": ["SF", "SF", "SF", "Montreal", "Montreal", "Montreal"]
})

fig = px.bar(df, x="Fruit", y="Amount", color="City", barmode="group")

app.layout = html.Div(children=[
    html.H1(children='Testowy nagłówek. ęśąćż'),

    html.Div(children='''
        Wykres CAPE surface based dla 15.08.2020r. 12:00 +0h.
    '''),

    html.Div(children=[html.Img(src='data:image/png;base64,{}'.format(encoded_image.decode()), style={'height':'70%', 'width':'70%'})], style={'textAlign': 'center'}),

    dcc.Graph(
        id='example-graph',
        figure=fig
    )
])

if __name__ == '__main__':
    app.run_server(debug=True)
