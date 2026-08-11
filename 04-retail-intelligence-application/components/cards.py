from dash import html
import dash_bootstrap_components as dbc

def kpi_card(title, value, subtitle, colour):
    return dbc.Card(dbc.CardBody([
        html.P(title, className="kpi-label"),
        html.H2(value, className="kpi-value", style={"color": colour}),
        html.Small(subtitle, className="kpi-subtitle"),
    ]), className="orey-kpi h-100", style={"borderTopColor": colour})
