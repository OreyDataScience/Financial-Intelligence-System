from dash import html, dcc, register_page
import dash_bootstrap_components as dbc

from components.cards import kpi_card
from components.store_chart import (
    top_stores_chart,
    store_profit_chart
)

from scripts.data_loader import stores, high_risk_stores
from scripts.utils import format_currency


register_page(
    __name__,
    path="/stores",
    name="Stores"
)


# ==========================================================
# METRICS
# ==========================================================

total_revenue = stores["Revenue"].sum()
total_profit = stores["Profit"].sum()
avg_margin = stores["AvgMargin"].mean()
avg_stockout = stores["StockOutRate"].mean()


# ==========================================================
# LAYOUT
# ==========================================================

layout = dbc.Container(

    [

        html.H1(
            "Store Performance",
            className="mb-1"
        ),

        html.P(
            "Revenue, profitability and operational performance across stores.",
            className="text-muted"
        ),

        html.Br(),

        # ==================================================
        # KPI CARDS
        # ==================================================

        dbc.Row(

            [

                dbc.Col(

                    kpi_card(
                        "Revenue",
                        format_currency(total_revenue),
                        "All Stores",
                        "#0B6E4F"
                    ),

                    xs=12,
                    sm=6,
                    lg=3

                ),

                dbc.Col(

                    kpi_card(
                        "Profit",
                        format_currency(total_profit),
                        "All Stores",
                        "#2E86DE"
                    ),

                    xs=12,
                    sm=6,
                    lg=3

                ),

                dbc.Col(

                    kpi_card(
                        "Average Margin",
                        f"{avg_margin:.1f}%",
                        "Store Portfolio",
                        "#8E44AD"
                    ),

                    xs=12,
                    sm=6,
                    lg=3

                ),

                dbc.Col(

                    kpi_card(
                        "Stock-Out Rate",
                        f"{avg_stockout * 100:.1f}%",
                        "Store Average",
                        "#F39C12"
                    ),

                    xs=12,
                    sm=6,
                    lg=3

                )

            ],

            className="g-4"

        ),

        html.Br(),

        # ==================================================
        # REVENUE
        # ==================================================

        dbc.Card(

            dbc.CardBody(

                [

                    dcc.Graph(

                        id="store-revenue-chart",

                        figure=top_stores_chart(stores),

                        config={
                            "displayModeBar": True,
                            "displaylogo": False,
                            "responsive": True
                        }

                    )

                ]

            ),

            className="shadow-sm"

        ),

        html.Br(),

        # ==================================================
        # PROFIT
        # ==================================================

        dbc.Card(

            dbc.CardBody(

                [

                    dcc.Graph(

                        id="store-profit-chart",

                        figure=store_profit_chart(stores),

                        config={
                            "displayModeBar": True,
                            "displaylogo": False,
                            "responsive": True
                        }

                    )

                ]

            ),

            className="shadow-sm"

        ),

        html.Br(),
        dbc.Card(dbc.CardBody([html.H4("High-Risk Stores"), html.Hr(), dbc.Table.from_dataframe(high_risk_stores[["StoreID", "StoreLocation", "StockOutRate", "ReturnRate"]].head(10), striped=True, hover=True, size="sm")]), className="shadow-sm")

    ],

    fluid=True

)
