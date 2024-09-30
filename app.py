import dash
from dash import dcc, html
from datetime import datetime as dt
import yfinance as yf
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import pandas as pd
import plotly.express as px

# Assuming you have a function called prediction in model.py
from model import prediction

def get_stock_price_fig(df):
    fig = px.line(df, x="Date", y=["Close", "Open"], title="Closing and Opening Price vs Date")
    return fig

def get_more(df):
    df['EWA_20'] = df['Close'].ewm(span=20, adjust=False).mean()
    fig = px.scatter(df, x="Date", y="EWA_20", title="Exponential Moving Average vs Date")
    fig.update_traces(mode='lines+markers')
    return fig

app = dash.Dash(__name__, external_stylesheets=[
    "https://fonts.googleapis.com/css2?family=Roboto&display=swap"
])
server = app.server
@server.route('/')
def serve_index():
    return send_from_directory('.', 'index.html')

# Predefined logos for specific stocks
stock_logos = {
    "GOOGL": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4a/Googlelogo.svg/1280px-Googlelogo.svg.png",
    "AMZN": "https://upload.wikimedia.org/wikipedia/commons/a/a9/Amazon_logo.svg",
    "NFLX": "https://logo.clearbit.com/netflix.com",
    "AAPL": "https://upload.wikimedia.org/wikipedia/commons/f/fa/Apple_logo_black.svg",
    "MSFT": "https://upload.wikimedia.org/wikipedia/commons/4/44/Microsoft_logo.svg",
    "FLIKART": "https://upload.wikimedia.org/wikipedia/commons/5/57/Flipkart_logo.svg",
    "IBM": "https://upload.wikimedia.org/wikipedia/commons/5/51/IBM_logo.svg"
}

# HTML layout of the site
app.layout = html.Div(
    [
        html.Div(
            [
                # Navigation
                html.P("Welcome to the Stock Dash App!", className="start"),
                html.Div([
                    html.P("Input stock code: "),
                    html.Div([
                        dcc.Input(id="dropdown_tickers", type="text", placeholder="e.g., AAPL"),
                        html.Button("Submit", id='submit'),
                    ], className="form")
                ], className="input-place"),
                html.Div([
                    dcc.DatePickerRange(
                        id='my-date-picker-range',
                        min_date_allowed=dt(1995, 8, 5),
                        max_date_allowed=dt.now(),
                        initial_visible_month=dt.now(),
                        end_date=dt.now().date()
                    ),
                ], className="date"),
                html.Div([
                    html.Button("Stock Price", className="stock-btn", id="stock"),
                    html.Button("Indicators", className="indicators-btn", id="indicators"),
                    dcc.Input(id="n_days", type="text", placeholder="number of days"),
                    html.Button("Forecast", className="forecast-btn", id="forecast")
                ], className="buttons"),
            ], className="nav"
        ),

        # Content
        html.Div(
            [
                html.Div(
                    [  # Header
                        html.Img(id="logo", style={"width": "100px", "height": "auto"}),
                        html.P(id="ticker", style={"fontSize": "24px", "fontWeight": "bold", "display": "inline"}),
                    ],
                    className="header"
                ),
                html.Div(id="description", className="description_ticker"),
                html.Div([], id="graphs-content"),
                html.Div([], id="main-content"),
                html.Div([], id="forecast-content")
            ],
            className="content"
        ),
    ],
    className="container"
)

# Callback for company info
@app.callback(
    [Output("description", "children"),
     Output("logo", "src"),
     Output("ticker", "children"),
     Output("stock", "n_clicks"),
     Output("indicators", "n_clicks"),
     Output("forecast", "n_clicks")],
    [Input("submit", "n_clicks")],
    [State("dropdown_tickers", "value")]
)
def update_data(n, val):
    if n is None:
        raise PreventUpdate
    if val is None or val.strip() == "":
        return "Please enter a valid stock code to get details.", "", "Invalid Code", None, None, None

    try:
        ticker = yf.Ticker(val.strip().upper())
        inf = ticker.info
        df = pd.DataFrame().from_dict(inf, orient="index").T
        description = df['longBusinessSummary'].values[0] if 'longBusinessSummary' in df.columns else "Description not available."
        
        logo_url = stock_logos.get(val.strip().upper(), "https://via.placeholder.com/100")
        short_name = df['shortName'].values[0] if 'shortName' in df.columns else val.strip().upper()

        return description, logo_url, short_name, None, None, None

    except Exception as e:
        return f"Error fetching data: {str(e)}", "", "Error", None, None, None

# Callback for stock price graphs
@app.callback([Output("graphs-content", "children")],
              [Input("stock", "n_clicks"),
               Input('my-date-picker-range', 'start_date'),
               Input('my-date-picker-range', 'end_date')],
              [State("dropdown_tickers", "value")])
def stock_price(n, start_date, end_date, val):
    if n is None:
        return [""]

    if val is None or val.strip() == "":
        raise PreventUpdate

    if start_date is not None and end_date is not None:
        df = yf.download(val.strip().upper(), start=start_date, end=end_date)
    else:
        df = yf.download(val.strip().upper())

    df.reset_index(inplace=True)
    fig = get_stock_price_fig(df)
    return [dcc.Graph(figure=fig)]

# Callback for indicators
@app.callback([Output("main-content", "children")],
              [Input("indicators", "n_clicks"),
               Input('my-date-picker-range', 'start_date'),
               Input('my-date-picker-range', 'end_date')],
              [State("dropdown_tickers", "value")])
def indicators(n, start_date, end_date, val):
    if n is None:
        return [""]

    if val is None or val.strip() == "":
        return [""]

    if start_date is None:
        df_more = yf.download(val.strip().upper())
    else:
        df_more = yf.download(val.strip().upper(), start=start_date, end=end_date)

    df_more.reset_index(inplace=True)
    fig = get_more(df_more)
    return [dcc.Graph(figure=fig)]

# Callback for forecast
@app.callback([Output("forecast-content", "children")],
              [Input("forecast", "n_clicks")],
              [State("n_days", "value"),
               State("dropdown_tickers", "value")])
def forecast(n, n_days, val):
    if n is None:
        return [""]

    if val is None or val.strip() == "":
        raise PreventUpdate

    try:
        n_days = int(n_days) + 1 if n_days.isdigit() else 1  # Default to 1 day if input is invalid
        fig = prediction(val.strip().upper(), n_days)
        return [dcc.Graph(figure=fig)]
    except Exception as e:
        return [f"Error in forecasting: {str(e)}"]

if __name__ == '__main__':
    app.run_server(debug=True)
    """app.run_server(debug=True, host='0.0.0.0', port=8050)"""

