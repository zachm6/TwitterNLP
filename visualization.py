import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output, dash_table

app = Dash(__name__)

# -- Import and clean data (importing csv into pandas)
df = pd.read_csv("output.csv")
print(df.head())

# ------------------------------------------------------------------------------
# App layout
app.layout = html.Div([
    html.H1("Twitter Sentiment Dashboard", style={'text-align': 'center'}),
    dcc.Dropdown(
        id="slct_symbol",
        options=[
            {"label": "TSLA", "value": "TSLA"},
            {"label": "AMZN", "value": "AMZN"},
            {"label": "AAPL", "value": "AAPL"}
        ],
        multi=False,
        value="TSLA",
        style={'width': "40%"}
    ),
    html.Div(id='output_container', children=[]),
    html.Br(),
    html.Div(id='my_df', children=[]),
    html.Br(),
    dcc.Graph(id='my_ternary_plot', figure={})
])

# ------------------------------------------------------------------------------
# Connect the Plotly graphs with Dash Components
@app.callback(
    [Output(component_id='output_container', component_property='children'),
     Output(component_id='my_ternary_plot', component_property='figure'),
     Output(component_id='my_df', component_property='children')],
    [Input(component_id='slct_symbol', component_property='value'),
     Input('my_ternary_plot', 'selectedData')]
)
def update_graph(option_slctd, selected_data):
    print(option_slctd)
    print(type(option_slctd))

    container = "The company chosen by the user was: {}".format(option_slctd)

    dff = df.copy()
    dff = dff[dff["symbol"] == option_slctd]

    # Graphs
    fig = px.scatter_ternary(dff, a="positive_score", b="neutral_score", c="negative_score", hover_name="sentiment")

    table = dash_table.DataTable(
        editable=True,
        data=dff.to_dict('records'),
        columns=[{"name": i, "id": i} for i in dff.columns]
    )

    # Update table with selected data
    if selected_data:
        selected_points = selected_data['points']
        selected_indices = [point['pointIndex'] for point in selected_points]
        selected_df = dff.iloc[selected_indices]
        table.data = selected_df.to_dict('records')

    return container, fig, table


if __name__ == '__main__':
    app.run_server(debug=True)