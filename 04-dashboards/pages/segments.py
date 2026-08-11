from dash import html, dcc, register_page
import dash_bootstrap_components as dbc

from components.cards import kpi_card
from components.segment_chart import (
    segment_revenue_chart,
    segment_margin_chart
)

from scripts.data_loader import segments
from scripts.utils import format_currency


register_page(
    __name__,
    path="/segments",
    name="Customer Segments"
)

# ==========================================================
# METRICS
# ==========================================================

total_revenue = segments["Revenue"].sum()

total_profit = segments["Profit"].sum()

avg_margin = segments["AvgMargin"].mean()

avg_return_rate = segments["ReturnRate"].mean()


# ==========================================================
# LAYOUT
# ==========================================================

layout = dbc.Container(

    [

        html.H1(
            "Customer Segments",
            className="mb-1"
        ),

        html.P(
            "Revenue, profitability and customer behaviour across segments.",
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
                        "All Segments",
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
                        "All Segments",
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
                        "Segment Average",
                        "#8E44AD"
                    ),

                    xs=12,
                    sm=6,
                    lg=3

                ),

                dbc.Col(

                    kpi_card(
                        "Return Rate",
                        f"{avg_return_rate * 100:.1f}%",
                        "Segment Average",
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
        # REVENUE BY SEGMENT
        # ==================================================

        dbc.Card(

            dbc.CardBody(

                dcc.Graph(

                    id="segment-revenue-chart",

                    figure=segment_revenue_chart(
                        segments
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

        html.Br(),

        # ==================================================
        # MARGIN BY SEGMENT
        # ==================================================

        dbc.Card(

            dbc.CardBody(

                dcc.Graph(

                    id="segment-margin-chart",

                    figure=segment_margin_chart(
                        segments
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