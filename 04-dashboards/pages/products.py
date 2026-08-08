from dash import html, dcc, register_page
import dash_bootstrap_components as dbc

from components.cards import kpi_card
from components.product_chart import top_products_chart

from scripts.data_loader import products
from scripts.utils import format_currency

register_page(

    __name__,

    path="/products",

    name="Products"

)

# ==========================================================
# KPIs
# ==========================================================

total_revenue = products["Revenue"].sum()

total_profit = products["Profit"].sum()

total_units = products["UnitsSold"].sum()

avg_margin = products["AvgMargin"].mean()

# ==========================================================
# Layout
# ==========================================================

layout = dbc.Container(

    [

        html.H1(

            "Product Analytics",

            className="mb-1"

        ),

        html.P(

            "Revenue and profitability by product.",

            className="text-muted"

        ),

        html.Br(),

        dbc.Row(

            [

                dbc.Col(

                    kpi_card(

                        "Revenue",

                        format_currency(total_revenue),

                        "Portfolio",

                        "#0B6E4F"

                    ),

                    lg=3

                ),

                dbc.Col(

                    kpi_card(

                        "Profit",

                        format_currency(total_profit),

                        "Portfolio",

                        "#2E86DE"

                    ),

                    lg=3

                ),

                dbc.Col(

                    kpi_card(

                        "Units Sold",

                        f"{total_units:,.0f}",

                        "Products",

                        "#8E44AD"

                    ),

                    lg=3

                ),

                dbc.Col(

                    kpi_card(

                        "Average Margin",

                        f"{avg_margin:.1f}%",

                        "Portfolio",

                        "#F39C12"

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

                    figure=top_products_chart(

                        products

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