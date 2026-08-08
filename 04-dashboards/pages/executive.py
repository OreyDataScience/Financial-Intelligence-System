from dash import html, dcc, register_page
import dash_bootstrap_components as dbc

from components.cards import kpi_card
from components.charts import revenue_chart
from components.executive_insights import executive_insights

from scripts.data_loader import monthly, forecast
from scripts.utils import format_currency

register_page(
    __name__,
    path="/",
    name="Executive"
)

# ==========================================================
# DATA
# ==========================================================

latest = monthly.iloc[-1]
latest_forecast = forecast.iloc[0]

revenue = latest["Revenue"]
profit = latest["Profit"]
margin = latest["Avg_Margin"]
inventory = latest["Inventory_Risk"]
returns = latest["ReturnRate"]

forecast_revenue = latest_forecast["Revenue_Forecast"]

# ==========================================================
# LAYOUT
# ==========================================================

layout = dbc.Container(

    [

        html.H1(
            "Executive Dashboard",
            className="mb-1"
        ),

        html.P(
            "Retail Intelligence System",
            className="text-muted"
        ),

        html.Br(),

        dbc.Row(

            [

                dbc.Col(
                    kpi_card(
                        "Revenue",
                        format_currency(revenue),
                        "Latest Month",
                        "#0B6E4F"
                    ),
                    xs=12,
                    sm=6,
                    lg=2
                ),

                dbc.Col(
                    kpi_card(
                        "Profit",
                        format_currency(profit),
                        "Latest Month",
                        "#2E86DE"
                    ),
                    xs=12,
                    sm=6,
                    lg=2
                ),

                dbc.Col(
                    kpi_card(
                        "Average Margin",
                        f"{margin:.1f}%",
                        "Portfolio Average",
                        "#8E44AD"
                    ),
                    xs=12,
                    sm=6,
                    lg=2
                ),

                dbc.Col(
                    kpi_card(
                        "Revenue Forecast",
                        format_currency(forecast_revenue),
                        "Next Month",
                        "#3498DB"
                    ),
                    xs=12,
                    sm=6,
                    lg=2
                ),

                dbc.Col(
                    kpi_card(
                        "Inventory",
                        inventory,
                        "Current Status",
                        "#F39C12"
                    ),
                    xs=12,
                    sm=6,
                    lg=2
                ),

                dbc.Col(
                    kpi_card(
                        "Return Rate",
                        f"{returns*100:.1f}%",
                        "Current Month",
                        "#C0392B"
                    ),
                    xs=12,
                    sm=6,
                    lg=2
                ),

            ],

            className="g-4"

        ),

        html.Br(),

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
                        "responsive": True,
                        "toImageButtonOptions": {
                            "filename": "orey_analytics_revenue_dashboard"
                        }
                    }

                )

            ),

            className="shadow-sm"

        ),

        html.Br(),

        dbc.Row(

            [

                dbc.Col(

                    executive_insights(

                        revenue,

                        forecast_revenue,

                        margin,

                        inventory,

                        returns

                    ),

                    lg=4

                ),

                dbc.Col(

                    dbc.Card(

                        dbc.CardBody(

                            [

                                html.H4("Orey Analytics"),

                                html.Hr(),

                                html.P(
                                    "Retail Intelligence System"
                                ),

                                html.P(
                                    "Built with Python, Dash, Plotly and R."
                                ),

                                html.P(
                                    "Financial analytics powered by statistical forecasting."
                                )

                            ]

                        ),

                        className="shadow-sm h-100"

                    ),

                    lg=8

                )

            ],

            className="g-4"

        )

    ],

    fluid=True

)