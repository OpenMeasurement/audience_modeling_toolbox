import dash
import dash_core_components as dcc
import dash_html_components as html
#import plotly.express as px
import plotly.graph_objects as go
import numpy  as np

fig = go.Figure(data=go.Heatmap(
    z=np.random.random([3, 3])
    #x=['1', '2', '3m'],
    #y=['1', '2', '3m'],
))

fig.update_layout(
    xaxis = dict(
        tickmode = 'array',
        tickvals = [0, 1, 2],
        ticktext = ["1", "2", "3+"]
    )
)

app = dash.Dash(__name__)

app.layout = html.Div([
    html.P("Example"),
    dcc.Graph(id="graph", figure=fig),
])

app.run_server(debug=True)
