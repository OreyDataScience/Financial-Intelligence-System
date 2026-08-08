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

# ==========================================================
# KPIs
# ==========================================================

latest = monthly.iloc[-1]
forecast_next = forecast.iloc[0]

revenue = latest["Revenue"]
profit = latest["Profit"]
margin = latest["Avg_Margin"]

forecast_revenue = forecast_next["Revenue_Forecast"]

growth = (
    (monthly.iloc[-1]["Revenue"] - monthly.iloc[-2]["Revenue"])
    / monthly.iloc[-2]["Revenue"]
) * 100

# ==========================================================
# Layout
# ==========================================================

layout = dbc.Container(

    [

        html.H1(
            "Revenue Intelligence",
            className="mb-1"
        ),

        html.P(
            "Revenue trends, growth and forecasting.",
            className="text-muted"
        ),

        html.Br(),

        dbc.Row(

            [

                dbc.Col(

                    kpi_card(

                        "Latest Revenue",

                        format_currency(revenue),

                        "Current Month",

                        "#0B6E4F"

                    ),

                    lg=3

                ),

                dbc.Col(

                    kpi_card(

                        "Profit",

                        format_currency(profit),

                        "Current Month",

                        "#2E86DE"

                    ),

                    lg=3

                ),

                dbc.Col(

                    kpi_card(

                        "Growth",

                        f"{growth:.1f}%",

                        "Month-on-Month",

                        "#8E44AD"

                    ),

                    lg=3

                ),

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