from dash import html, dcc, register_page
import dash_bootstrap_components as dbc

from components.cards import kpi_card
from components.channel_chart import (
    channel_revenue_chart,
    channel_share_chart
)

from scripts.data_loader import channels
from scripts.utils import format_currency


register_page(
    __name__,
    path="/channels",
    name="Channel Analysis"
)

# ==========================================================
# METRICS
# ==========================================================

total_revenue = channels["Revenue"].sum()

total_profit = channels["Profit"].sum()

avg_margin = channels["AvgMargin"].mean()

avg_returns = channels["ReturnRate"].mean()


# ==========================================================
# LAYOUT
# ==========================================================

layout = dbc.Container(

    [

        html.H1(
            "Channel Analysis",
            className="mb-1"
        ),

        html.P(
            "Revenue, profitability and customer returns across sales channels.",
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
                        "All Channels",
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
                        "All Channels",
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
                        "Channel Average",
                        "#8E44AD"
                    ),

                    xs=12,
                    sm=6,
                    lg=3

                ),

                dbc.Col(

                    kpi_card(
                        "Return Rate",
                        f"{avg_returns * 100:.1f}%",
                        "Channel Average",
                        "#C0392B"
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
        # CHARTS
        # ==================================================

        dbc.Row(

            [

                dbc.Col(

                    dbc.Card(

                        dbc.CardBody(

                            dcc.Graph(

                                id="channel-revenue-chart",

                                figure=channel_revenue_chart(
                                    channels
                                ),

                                config={
                                    "displayModeBar": True,
                                    "displaylogo": False,
                                    "responsive": True
                                }

                            )

                        ),

                        className="shadow-sm"

                    ),

                    lg=7

                ),

                dbc.Col(

                    dbc.Card(

                        dbc.CardBody(

                            dcc.Graph(

                                id="channel-share-chart",

                                figure=channel_share_chart(
                                    channels
                                ),

                                config={
                                    "displayModeBar": True,
                                    "displaylogo": False,
                                    "responsive": True
                                }

                            )

                        ),

                        className="shadow-sm"

                    ),

                    lg=5

                )

            ],

            className="g-4"

        )

    ],

    fluid=True

)