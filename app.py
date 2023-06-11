import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html, Input, Output, dash_table
import dash_bootstrap_components as dbc
from datetime import date
from datetime import datetime

app = Dash(__name__, external_stylesheets=[dbc.themes.SLATE])

# -- Import and clean data (importing csv into pandas)
df = pd.read_csv("output.csv")

# ------------------------------------------------------------------------------
# App layout
app.layout = dbc.Container(html.Div([

    # Dashboard Title
    dbc.Row([
        dbc.Col([
            html.H1("Twitter Sentiment Dashboard")
        ], width=5)
    ], justify="center"),

    # Dashboard Filters
    dbc.Row([
        dbc.Col([
            html.Label('Symbol'),
            dcc.Dropdown(
                id="slct_symbol",
                options=[{"label": symbol, "value": symbol} for symbol in df["symbol"].unique()],
                multi=False,
                value="TSLA"
            ),
            html.Br()
        ], width=4),
        dbc.Col([
            html.Label('Date'),
            html.Br(),
            dcc.Input(
                id="my-date", 
                type="text", 
                placeholder="Y/M/D/H/MIN", 
                debounce=True
            )
        ], width=4)
    ]),
    html.Br(),
    dbc.Row([
        dbc.Col([
            html.H4('Total Records', className="card-title"),
            html.P(id='total_container', children=[], className="card-text")
        ]),
        dbc.Col([
            html.H4('Positive Records', className="card-title"),
            html.P(id='positive_container', children=[], className="card-text"),
        ]),
        dbc.Col([
            html.H4('Neutral Records', className="card-title"),
            html.P(id='neutral_container', children=[], className="card-text")
        ]),
        dbc.Col([
            html.H4('Negative Records', className="card-title"),
            html.P(id='negative_container', children=[], className="card-text")
        ]),
    ]),
    html.Br(),
    html.Div(id='output_container', children=[]),
    html.Div(id='my_df', children=[]),
    html.Br(),
    dcc.Graph(id='my_ternary_plot', figure={})
]))

# ------------------------------------------------------------------------------
# Connect the Plotly graphs with Dash Components
@app.callback(
    [Output(component_id='total_container', component_property='children'),
     Output(component_id='positive_container', component_property='children'),
     Output(component_id='neutral_container', component_property='children'),
     Output(component_id='negative_container', component_property='children'),
     Output(component_id='output_container', component_property='children'),
     Output(component_id='my_ternary_plot', component_property='figure'),
     Output(component_id='my_df', component_property='children')],
    [Input(component_id='slct_symbol', component_property='value'),
     Input('my_ternary_plot', 'selectedData'),
     Input('my-date','value')
    ]
)
def update_graph(option_slctd, selected_data, date_selected):
    DESIRED_COLUMNS = ["impression_count", "text", "created_at", "sentiment"]

    container = "The company chosen by the user was: {} {}".format(option_slctd, str(date_selected))

    dff = df.copy()
    dff = dff[dff["symbol"] == option_slctd]
    # print(type(dff["created_at"][0]))
    # date_str = dff["created_at"][0]
    # print(datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S%z").strftime("%d"))
    if date_selected:
        print(date_selected)
        print("Date was selected")
        user_date_list = date_selected.split("/")
        date_map = {
                0: "%Y",
                1: "%m", 
                2: "%d",
                3: "%H",
                4: "%M"
            }
        boolean_lists = []
        for i in range(len(user_date_list)):
            boolean_list_interval = dff["created_at"].apply(lambda x:datetime.strptime(x, "%Y-%m-%d %H:%M:%S%z").strftime(date_map[i]) == user_date_list[i])
            boolean_lists.append(boolean_list_interval)
        dff = dff.apply(lambda x: x[[all(series) for series in pd.concat(boolean_lists, axis=1).values]])
        print(dff)

    # total records
    total = len(dff)

    # positive records
    num_positive = str(round(100*(len(dff[dff["sentiment"] == "Positive"]) / total), 1)) + "%" if total != 0 else 0

    # neutral records
    num_neutral = str(round(100*(len(dff[dff["sentiment"] == "Neutral"]) / total), 1)) + "%" if total != 0 else 0

    # negative records
    num_negative = str(round(100*(len(dff[dff["sentiment"] == "Negative"]) / total), 1)) + "%" if total != 0 else 0

    # Graphs
    fig = px.scatter_ternary(dff, a="positive_score", b="neutral_score", c="negative_score", hover_name="sentiment")

    # Style data conditional based on sentiment column
    sentiment_colors = {
        'Positive': 'green',
        'Negative': 'red',
        'Neutral': 'blue'
    }
    
    style_data_conditional = [
        {
            'if': {'filter_query': '{sentiment} eq "Positive"'},
            'backgroundColor': sentiment_colors['Positive'],
            'color': 'white'
        },
        {
            'if': {'filter_query': '{sentiment} eq "Negative"'},
            'backgroundColor': sentiment_colors['Negative'],
            'color': 'white'
        },
        {
            'if': {'filter_query': '{sentiment} eq "Neutral"'},
            'backgroundColor': sentiment_colors['Neutral'],
            'color': 'white'
        }
    ]

    table = dash_table.DataTable(
        data=dff.to_dict('records'),
        columns=[{"name": i, "id": i} for i in dff[DESIRED_COLUMNS].columns],
        page_current=0,
        page_size=5,
        style_data_conditional=style_data_conditional,
        style_cell={
            'textAlign': 'left',
            'whiteSpace': 'pre-line'
            },
        sort_action="native"
    )

    # Update table with selected data
    if selected_data:
        selected_points = selected_data['points']
        selected_indices = [point['pointIndex'] for point in selected_points]
        selected_df = dff[DESIRED_COLUMNS].iloc[selected_indices]
        table.data = selected_df.to_dict('records')
        total = len(selected_df)

        # positive records
        num_positive = str(round(100*(len(selected_df[selected_df["sentiment"] == "Positive"]) / total), 1)) + "%" if total != 0 else 0

        # neutral records
        num_neutral = str(round(100*(len(selected_df[selected_df["sentiment"] == "Neutral"]) / total), 1)) + "%" if total != 0 else 0

        # negative records
        num_negative = str(round(100*(len(selected_df[selected_df["sentiment"] == "Negative"]) / total), 1)) + "%" if total != 0 else 0

    return total, num_positive, num_neutral, num_negative, container, fig, table


if __name__ == '__main__':
    app.run_server(debug=True) # LOCAL
    # app.run_server(debug=False, host="0.0.0.0", port=8080)