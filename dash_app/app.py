import numpy as np
np.seterr(divide='ignore')
import pandas as pd

import itertools
from itertools import product
#from open_measurement.model import NormalExponentialADF, MixtureOfExponentials

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.graph_objects as go
from plotly.subplots import make_subplots


### Required stuff from openmeasuremet modeling ###

import warnings
from abc import ABC, abstractmethod

class AbstractADF(ABC):

    def f_reach(self, grs, freqs) :
        return np.prod(
            self._f_reach(
                np.reshape(grs,   [-1, 1, self.n_dims]),
                np.reshape(freqs, [1, -1, self.n_dims])
            ), axis=2 )

    def fplus_reach(self, grs, freqs) :
        return np.prod(
            self._fplus_reach(
                np.reshape(grs,   [-1, 1, self.n_dims]),
                np.reshape(freqs, [1, -1, self.n_dims])
            ), axis=2 )

class NormalExponentialADF(AbstractADF) :

    def __init__(self, gammas, bounds=(1.0e-10, np.inf)) :
        self.n_dims     = len(gammas)
        self.parameters = gammas

        self.bounds     = {
            "lower" : [bounds[0] for i in range(self.n_dims)],
            "upper" : [bounds[1] for i in range(self.n_dims)]
        }

    @property
    def parameters(self) :
        return self._gammas

    @parameters.setter
    def parameters(self, gammas) :
        self._gammas = gammas

    def _f_reach(self, grs, freqs) :
        return np.power(self._gammas*grs, freqs) / np.power(1 + self._gammas*grs, freqs + 1)

    def _fplus_reach(self, grs, freqs) :
        return np.power((self._gammas*grs) / (1+ self._gammas*grs), freqs)

    def ftrunc_reach(self, grs, max_freq) :
        freqs = np.array(list(
            itertools.product(*[range(max_freq+1) for i in range(self.n_dims)])
            ))
        R = self._f_reach(np.reshape(grs, [-1, 1, self.n_dims]),
                          np.reshape(freqs, [1, -1, self.n_dims]))

        R_truncate = self._fplus_reach(np.reshape(grs, [-1, 1, self.n_dims]),
                                       max_freq * np.ones([1, 1, self.n_dims]))
        for n_freq, n_dim in itertools.product(range((max_freq+1)**self.n_dims), range(self.n_dims)) :
            if freqs[n_freq, n_dim] == max_freq :
                for n_gr in range(R.shape[0]) :
                    R[n_gr, n_freq, n_dim] = R_truncate[n_gr, 0, n_dim]

        return np.prod(R, axis=2)

class MixtureADF(AbstractADF) :

    def __init__(self, amplitudes, simple_adfs, normalize=True) :
        n_dims = simple_adfs[0].n_dims
        adf_n_dims = [adf.n_dims == n_dims for adf in simple_adfs]
        self.n_dims = n_dims
        self.n_simples   = len(amplitudes)
        self.amplitudes  = amplitudes
        self.simple_adfs = simple_adfs

        if not np.isclose(np.sum(amplitudes), 1.0) and normalize :
            warnings.warn("The amplitudes are not normalized, normalizing them ...")
            self.normalize()

    @property
    def amplitudes(self):
        return self._amplitudes

    @amplitudes.setter
    def amplitudes(self, amplitudes) :
        self._amplitudes = amplitudes

    @property
    def parameters(self) :
        return np.hstack([
            simple_adf.parameters for simple_adf in self.simple_adfs
        ]).flatten()

    @parameters.setter
    def parameters(self, parameters) :
        index = 0
        for simple_adf in self.simple_adfs :
            n = len(simple_adf.parameters)
            simple_adf.parameters = parameters[index: index+n]
            index += n

    def normalize(self) :
        self.amplitudes = self.amplitudes/np.sum(self.amplitudes)

    def _f_reach(self, grs, freqs) :
        return np.tensordot(
            self.amplitudes,
            np.array([simple_adf._f_reach(grs, freqs) for simple_adf in self.simple_adfs]),
            axes = ([0], [0])
            )

    def _fplus_reach(self, grs, freqs) :
        return np.tensordot(
            self.amplitudes,
            np.array([simple_adf._fplus_reach(grs, freqs) for simple_adf in self.simple_adfs]),
            axes = ([0], [0])
            )

    def ftrunc_reach(self, grs, max_freq) :
        return np.tensordot(
            self.amplitudes,
            np.array([simple_adf.ftrunc_reach(grs, max_freq) for simple_adf in self.simple_adfs]),
            axes = ([0], [0])
            )

class MixtureOfExponentials(MixtureADF) :
    def __init__(self, amplitudes, simple_adfs) :
        super().__init__(amplitudes, simple_adfs)

population_size = int(12.0e6)
adf = MixtureOfExponentials(
    amplitudes  = np.array([0.09151325, 0.86611876, 0.07544663]),
    simple_adfs = [
        NormalExponentialADF(np.array([1.06266947,  0.01997136])),
        NormalExponentialADF(np.array([1.06252994,  0.01346685])),
        NormalExponentialADF(np.array([0.89667383, 11.25955419])),
    ]
)

### App stuff

# working_dir = ".."
max_freq = 20

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
#print(report.gr_values)

report_gr_values = [0.92322892, 0.148324]

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

def center3(s) :
    if len(s) == 2 :
        return s + " "
    else :
        return str.center(s, 3)

freq_label_jump = 1
tickrange = range(0, max_freq+1, freq_label_jump)
ticklabels = [str(i) for i in range(0, max_freq+1, freq_label_jump)]
ticklabels[-1] = ticklabels[-1] + "+"
ticklabels = [center3(label) for label in ticklabels]

report_rfdata = np.loadtxt("report_rfdata.dat")

colorscales = ["viridis", "cividis", "solar", "inferno", "plasma", "thermal"]

def format_number(n):
    letters = ['', 'K', 'M', 'B', 'T']
    index = int(np.log10(n) / 3)
    power = 10**(3*index)
    number = n / power
    if number.is_integer() :
        return str(n//power) + letters[index]
    else :
        return str(n/power) + letters[index]
tickvals = np.hstack([10**l*np.arange(1, 10) for l in range(0, 10)])
tickvals = tickvals[tickvals < 3.5e7]
ticktext = np.array([format_number(a) for a in tickvals])
ticktext[np.mod(np.log10(tickvals), 1) != 0] = ''
tickvals = np.log10(tickvals)


def plot_2d_rf (data, colorscale, dim_cols=['Digital', 'Facebook']) :
    fig = make_subplots(
        rows=3, cols=3,
        specs=[
            [{"colspan": 2},               None, None          ],
            [{"rowspan": 2, "colspan": 2}, None, {"rowspan": 2}],
            [None,                         None, None          ]
        ],
        vertical_spacing = 0.01,
        horizontal_spacing = 0.01
    )

    fig.add_trace(
        go.Heatmap(
            z = np.log10(data),
            zmin = 0,
            zmax = np.log10(np.max(data)),
            zauto = False,
            x = ticklabels,
            y = ticklabels,
            customdata = np.around(data, decimals=2),
            hovertemplate='Facebook: %{x}<br>Digital: %{y}<br>n-reach: %{customdata}<extra></extra>',
            colorscale=colorscale,
            colorbar = {
                'title'    : 'n-reach',
                'ticks'    : 'outside',
                'ticklen'  : 5,
                'tickvals' : tickvals,
                'ticktext' : ticktext,
                'ypad'     : 0,
                'xpad'     : 10,
                'x'        : 1.0
            },
            xgap=.2,
            ygap=.2
        ),
        row = 2, col=1
    )

    data_0 = np.log10(np.sum(data, axis=0))
    data_0[data_0 < 0] = 0
    fig.add_trace(
        go.Bar(
            x=ticklabels,
            y=data_0,
            customdata=np.round(np.sum(data, axis=0), decimals=2),
            hovertemplate='{0}: %{{x}}<br>n-reach: %{{customdata}}<extra></extra>'.format(dim_cols[1]),
            orientation='v',
            marker={'color': data_0,'colorscale': colorscale}
        ),
        row=1, col=1
    )

    data_1 = np.log10(np.sum(data, axis=1))
    data_1[data_1 < 0] = 0

    fig.add_trace(
        go.Bar(
            x=data_1,
            y=ticklabels,
            customdata=np.round(np.sum(data, axis=1), decimals=2),
            hovertemplate='{0}: %{{y}}<br>n-reach: %{{customdata}}<extra></extra>'.format(dim_cols[0]),
            orientation='h',
            marker={'color': data_1,'colorscale': colorscale}
        ),
        row=2, col=3
    )

    fig.update_layout(
        dict(
            bargap=0,
            plot_bgcolor='rgba(255,255,255,255)',
            xaxis = {
                'type' : 'category',
                'scaleanchor' : 'x2',
                'ticks' : '',
                'showticklabels' : False
            },
            yaxis = {'ticks' : '', 'showticklabels' : False},
            xaxis2 = {
                'title'     : dim_cols[1],
                'type'      : 'category',
                'constrain' : 'domain',
            },
            yaxis2 = {
                'title'     : dim_cols[0],
                'type'        : 'category',
                'constrain'   : 'domain',
                'scaleanchor' : 'x2',
                'ticks'       : 'outside',
                'tickcolor'   : 'rgba(255,255,255,255)',
                'ticklen'     : 6
            },
            xaxis3 = {'ticks' : '', 'showticklabels' : False},
            yaxis3 = {
                'type' : 'category',
                'scaleanchor' : 'y2',
                'ticks' : '',
                'showticklabels' : False
            },
            autosize=False,
            width=1000,
            height=1000,
            showlegend=False
        )
    )
    return fig

def main_figure(colorscale) :
    return plot_2d_rf(report_rfdata, colorscale)

def model_figure(gr_0, gr_1, colorscale) :
    gr_values = [gr_0, gr_1]
    model_data = adf.ftrunc_reach(gr_values, max_freq=max_freq).reshape([max_freq+1, max_freq+1]) * population_size
    return plot_2d_rf(model_data, colorscale)

app.layout = html.Div(children=[
    html.H1(children='Interactive Facebook-Digital-Linear'),
    dcc.RadioItems(
        id='colorscale',
        options=[{'label' : x, 'value' : x} for x in colorscales],
        value='viridis',
        labelStyle={'display': 'inline-block'}
    ),
    html.P(children='''
        The StateFarm data
    '''),
    html.Div([
        dcc.Graph(
            id='main-figure',
            figure=main_figure('viridis')
        )], style={'display': 'flex', 'align-items' : 'center', 'justify-content' : 'center'}),
    html.Div([
        dcc.Graph(
            id='model-figure',
            figure=model_figure(*report_gr_values, 'viridis')
            )], style={'display': 'flex', 'align-items' : 'center', 'justify-content' : 'center'}),
    html.Div([
        html.Div([
            "Gross rating Digital : ",
            dcc.Slider(
                id='gr_0_slider',
                min=0.1,
                max=5.0,
                step=0.01,
                value=np.around(report_gr_values[0], decimals=2),
            ),
            dcc.Input(id="gr_0_box", type='text', value=np.around(report_gr_values[0], decimals=2), style={'textAlign' : 'center'})
        ], style={"display": "grid", "grid-template-columns": "10% 65% 5%"}),
        html.Div([
            "Gross rating Facebook : ",
            dcc.Slider(
                id='gr_1_slider',
                min=0.1,
                max=5.0,
                step=0.01,
                value=np.around(report_gr_values[1], decimals=2),
            ),
            dcc.Input(id="gr_1_box", type='text', value=np.around(report_gr_values[1], decimals=2), style={'textAlign' : 'center'})
        ], style={"display": "grid", "grid-template-columns": "10% 65% 5%"}),
        html.Div(id='slider-output-container')
    ])
])

@app.callback(
    Output("main-figure", "figure"),
    [Input("colorscale", "value")])
def change_colorscale(colorscale):
    return main_figure(colorscale)

@app.callback(
    Output("model-figure", "figure"),
    [Input("colorscale", "value"), Input("gr_0_slider", "value"), Input("gr_1_slider", "value")])
def change_colorscale(colorscale, gr_0, gr_1):
    return model_figure(gr_0, gr_1, colorscale)

@app.callback(
    Output("gr_0_box", "value"),
    [Input("gr_0_slider", "value")])
def change_gr_0(value):
    return value

@app.callback(
    Output("gr_1_box", "value"),
    [Input("gr_1_slider", "value")])
def change_gr_1(value):
    return value


if __name__ == '__main__':
    app.run_server(debug=True)
