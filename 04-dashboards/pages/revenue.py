from dash import html, dcc, register_page
import dash_bootstrap_components as dbc

from components.cards import kpi_card
from components.charts import revenue_chart

from scripts.data_loader import monthly, forecast
from scripts.utils import format_currency

register_page(
    __name__,
    path="/revenue",
    name="Revenue"
)

# KPIs

latest = monthly.iloc[-1]
forecast_next = forecast.iloc[0]

revenue = latest["Revenue"]
profit = latest["Profit"]
margin = latest["Avg_Margin"]

forecast_revenue = forecast_next["Revenue_Forecast"]

# MONTH-ON-MONTH GROWTH

previous_revenue = monthly.iloc[-2]["Revenue"]

growth = (
    (revenue - previous_revenue)
    / previous_revenue
) * 100

# DYNAMIC KPI COLORS

# Profit and growth: Green if positive and Red if negative
profit_color = (
    "#2ECC71"
    if profit >= 0
    else "#C0392B"
)

growth_color = (
    "#2ECC71"
    if growth >= 0
    else "#C0392B"
)

# LAYOUT

layout = dbc.Container(
    [
        # HEADER

        html.H1(
            "Revenue Intelligence",
            className="mb-1"
        ),

        html.P(
            "Revenue trends, growth and forecasting.",
            className="text-muted"
        ),

        html.Br(),

        # KPI CARDS

        dbc.Row(
            [
                # LATEST REVENUE

                dbc.Col(
                    kpi_card(
                        "Latest Revenue",
                        format_currency(revenue),
                        "Current Month",
                        "#3498DB"
                    ),

                    lg=3
                ),

                # PROFIT

                dbc.Col(
                    kpi_card(
                        "Profit",
                        format_currency(profit),
                        "Current Month",
                        profit_color
                    ),

                    lg=3
                ),

                # GROWTH

                dbc.Col(
                    kpi_card(
                        "Growth",
                        f"{growth:.1f}%",
                        "Month-on-Month",
                        growth_color
                    ),

                    lg=3
                ),

                # FORECAST

                dbc.Col(
                    kpi_card(
                        "Forecast",
                        format_currency(forecast_revenue),
                        "Next Month",
                        "#3498DB"
                    ),

                    lg=3
                )
            ],

            className="g-4"
        ),

        html.Br(),

        # REVENUE + FORECAST CHART

        dbc.Card(
            dbc.CardBody(
                dcc.Graph(
                    figure=revenue_chart(
                        monthly,
                        forecast
                    ),

                    config={
                        "displayModeBar": True,
                        "displaylogo": False,
                        "responsive": True
                    }
                )
            ),

            className="shadow-sm"
        )
    ],

    fluid=True
)