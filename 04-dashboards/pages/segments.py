from dash import html, dcc, register_page
import dash_bootstrap_components as dbc

from components.cards import kpi_card

from components.segment_chart import (
    segment_revenue_chart,
    segment_profit_chart,
    segment_margin_chart,
    segment_return_rate_chart,
    segment_performance_matrix
)

from scripts.data_loader import segments
from scripts.utils import format_currency

register_page(
    __name__,
    path="/segments",
    name="Customer Segments"
)

# OREY ANALYTICS COLOURS

OREY_NAVY = "#061A35"
OREY_BLUE = "#1479D2"
OREY_GREEN = "#2ECC71"
OREY_ORANGE = "#F39C12"
OREY_RED = "#C0392B"
OREY_PURPLE = "#8E44AD"
OREY_GREY = "#7F8C8D"

# DATA PREPARATION

data = segments.copy()

data["ProfitMargin"] = (
    data["Profit"]
    /
    data["Revenue"].replace(0, None)
    * 100
)

data["ReturnRatePercent"] = (
    data["ReturnRate"] * 100
)

data["RevenueSharePercent"] = (
    data["Revenue"]
    /
    data["Revenue"].sum()
    * 100
)

# PORTFOLIO METRICS

total_revenue = data["Revenue"].sum()

total_profit = data["Profit"].sum()

portfolio_margin = (
    total_profit
    /
    total_revenue
    * 100

    if total_revenue != 0
    else 0
)

avg_margin = data["ProfitMargin"].mean()

avg_return_rate = data["ReturnRate"].mean()

# BEST / WEAKEST SEGMENTS

largest_segment = (
    data.loc[
        data["Revenue"].idxmax(),
        "CustomerSegment"
    ]
)

strongest_margin_segment = (
    data.loc[
        data["ProfitMargin"].idxmax(),
        "CustomerSegment"
    ]
)

highest_return_segment = (
    data.loc[
        data["ReturnRate"].idxmax(),
        "CustomerSegment"
    ]
)

lowest_margin_segment = (
    data.loc[
        data["ProfitMargin"].idxmin(),
        "CustomerSegment"
    ]
)

# SEGMENT INTELLIGENCE TABLE

table_data = data[
    [
        "CustomerSegment",
        "Revenue",
        "Profit",
        "ProfitMargin",
        "RevenueSharePercent",
        "ReturnRatePercent"
    ]
].copy()

table_data = table_data.sort_values(
    "Revenue",
    ascending=False
)

def margin_badge(value):

    if value >= avg_margin:

        return dbc.Badge(
            f"{value:.1f}%",
            color="success",
            className="px-2 py-1"
        )

    return dbc.Badge(
        f"{value:.1f}%",
        color="warning",
        text_color="dark",
        className="px-2 py-1"
    )

def return_badge(value):

    if value <= avg_return_rate * 100:

        return dbc.Badge(
            f"{value:.2f}%",
            color="success",
            className="px-2 py-1"
        )

    return dbc.Badge(
        f"{value:.2f}%",
        color="danger",
        className="px-2 py-1"
    )

segment_rows = []

for _, row in table_data.iterrows():

    segment_rows.append(
        html.Tr(
            [
                html.Td(
                    row["CustomerSegment"],
                    style={
                        "fontWeight": "600",
                        "color": OREY_NAVY
                    }
                ),

                html.Td(
                    format_currency(
                        row["Revenue"]
                    )
                ),

                html.Td(
                    format_currency(
                        row["Profit"]
                    )
                ),

                html.Td(
                    margin_badge(
                        row["ProfitMargin"]
                    )
                ),

                html.Td(
                    f"{row['RevenueSharePercent']:.1f}%"
                ),

                html.Td(
                    return_badge(
                        row["ReturnRatePercent"]
                    )
                )
            ]
        )
    )

# EXECUTIVE INTERPRETATION

largest_revenue_share = (
    data.loc[
        data["Revenue"].idxmax(),
        "RevenueSharePercent"
    ]
)

if portfolio_margin >= avg_margin:

    profitability_message = (
        f"The customer portfolio is generating an overall "
        f"margin of {portfolio_margin:.1f}%, which is above "
        f"the average segment margin of {avg_margin:.1f}%. "
        f"{strongest_margin_segment} currently produces "
        f"the strongest segment-level margin."
    )

else:

    profitability_message = (
        f"The customer portfolio is generating an overall "
        f"margin of {portfolio_margin:.1f}%, below the "
        f"average segment margin of {avg_margin:.1f}%. "
        f"{strongest_margin_segment} remains the strongest "
        f"segment by margin."
    )

return_message = (
    f"{highest_return_segment} has the highest return "
    f"rate at {data['ReturnRatePercent'].max():.2f}%. "
    f"This may indicate greater exposure to product mix, "
    f"customer behaviour or fulfilment-related issues."
)

# LAYOUT

layout = dbc.Container(
    [
        # PAGE HEADER

        html.H1(
            "Customer Segments",
            className="mb-1"
        ),

        html.P(
            "Understanding where customer value is generated, "
            "where profitability is strongest and where behavioural "
            "risk is emerging.",
            className="text-muted"
        ),

        html.Br(),

        # KPI CARDS

        dbc.Row(
            [
                dbc.Col(
                    kpi_card(
                        "Revenue",
                        format_currency(
                            total_revenue
                        ),
                        "All Segments",
                        OREY_BLUE
                    ),

                    xs=12,
                    sm=6,
                    lg=3
                ),

                dbc.Col(
                    kpi_card(
                        "Profit",
                        format_currency(
                            total_profit
                        ),
                        "All Segments",
                        OREY_GREEN
                    ),

                    xs=12,
                    sm=6,
                    lg=3
                ),

                dbc.Col(
                    kpi_card(
                        "Portfolio Margin",
                        f"{portfolio_margin:.1f}%",
                        "Revenue-weighted",
                        OREY_PURPLE
                    ),

                    xs=12,
                    sm=6,
                    lg=3
                ),

                dbc.Col(
                    kpi_card(
                        "Average Return Rate",
                        f"{avg_return_rate * 100:.1f}%",
                        "Segment Average",
                        OREY_RED
                    ),

                    xs=12,
                    sm=6,
                    lg=3
                )
            ],

            className="g-4"
        ),

        html.Br(),

        # SEGMENT INTELLIGENCE

        dbc.Card(
            dbc.CardBody(
                [
                    html.H5(
                        "Customer Segment Intelligence",
                        className="mb-3",
                        style={
                            "color": OREY_NAVY,
                            "fontWeight": "700"
                        }
                    ),

                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.Small(
                                        "Largest Revenue Segment",
                                        style={
                                            "color": "#000000"
                                        }
                                    ),

                                    html.Div(
                                        largest_segment,
                                        style={
                                            "fontWeight": "700",
                                            "fontSize": "18px",
                                            "color": OREY_BLUE
                                        }
                                    ),

                                    html.Small(
                                        f"{largest_revenue_share:.1f}% "
                                        "of portfolio revenue",
                                        style={
                                            "color": "#000000"
                                        }
                                    )
                                ],

                                xs=12,
                                md=4
                            ),

                            dbc.Col(
                                [
                                    html.Small(
                                        "Strongest Margin Segment",
                                        style={
                                            "color": "#000000"
                                        }
                                    ),

                                    html.Div(
                                        strongest_margin_segment,
                                        style={
                                            "fontWeight": "700",
                                            "fontSize": "18px",
                                            "color": OREY_GREEN
                                        }
                                    ),

                                    html.Small(
                                        f"{data['ProfitMargin'].max():.1f}% "
                                        "segment margin",
                                        style={
                                            "color": "#000000"
                                        }
                                    )
                                ],

                                xs=12,
                                md=4
                            ),

                            dbc.Col(
                                [
                                    html.Small(
                                        "Highest Return Exposure",
                                        style={
                                            "color": "#000000"
                                        }
                                    ),

                                    html.Div(
                                        highest_return_segment,
                                        style={
                                            "fontWeight": "700",
                                            "fontSize": "18px",
                                            "color": OREY_RED
                                        }
                                    ),

                                    html.Small(
                                        f"{data['ReturnRatePercent'].max():.2f}% "
                                        "return rate",
                                        style={
                                            "color": "#000000"
                                        }
                                    )
                                ],

                                xs=12,
                                md=4
                            )
                        ],

                        className="g-4"
                    )
                ]
            ),

            className="shadow-sm"
        ),

        html.Br(),

        # REVENUE + PROFIT

        dbc.Row(
            [
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            dcc.Graph(
                                id="segment-revenue-chart",
                                figure=segment_revenue_chart(
                                    data
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

                    xs=12,
                    lg=6
                ),

                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            dcc.Graph(
                                id="segment-profit-chart",
                                figure=segment_profit_chart(
                                    data
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

                    xs=12,
                    lg=6
                )
            ],

            className="g-4"
        ),

        html.Br(),

        # MARGIN + RETURN RATE

        dbc.Row(
            [
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            dcc.Graph(
                                id="segment-margin-chart",
                                figure=segment_margin_chart(
                                    data
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

                    xs=12,
                    lg=6
                ),

                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            dcc.Graph(
                                id="segment-return-rate-chart",
                                figure=segment_return_rate_chart(
                                    data
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

                    xs=12,
                    lg=6
                )
            ],

            className="g-4"
        ),

        html.Br(),

        # PERFORMANCE MATRIX

        dbc.Card(
            dbc.CardBody(
                [
                    html.H4(
                        "Customer Segment Performance Matrix",
                        className="mb-1",
                        style={
                            "color": OREY_NAVY,
                            "fontWeight": "700"
                        }
                    ),

                    html.P(
                        "Revenue scale is compared with profitability to identify high-value segments and areas requiring management attention.",
                        className="mb-3 fst-italic"
                    ),

                    dcc.Graph(
                        id="segment-performance-matrix",
                        figure=segment_performance_matrix(
                            data
                        ),

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

        # SEGMENT INTELLIGENCE TABLE

        dbc.Card(
            dbc.CardBody(
                [
                    html.H4(
                        "Segment Intelligence",
                        className="mb-1",
                        style={
                            "color": OREY_NAVY,
                            "fontWeight": "700"
                        }
                    ),

                    html.P(
                        "Segment-level indicators highlighting financial contribution, profitability and customer return exposure.",
                        className="mb-3 fst-italic"
                    ),

                    dbc.Table(
                        [
                            html.Thead(
                                html.Tr(
                                    [
                                        html.Th(
                                            "Customer Segment"
                                        ),

                                        html.Th(
                                            "Revenue"
                                        ),

                                        html.Th(
                                            "Profit"
                                        ),

                                        html.Th(
                                            "Profit Margin"
                                        ),

                                        html.Th(
                                            "Revenue Share"
                                        ),

                                        html.Th(
                                            "Return Rate"
                                        )
                                    ]
                                )
                            ),

                            html.Tbody(
                                segment_rows
                            )
                        ],

                        striped=True,
                        hover=True,
                        bordered=False,
                        responsive=True,
                        size="sm",
                        className="align-middle"
                    )
                ]
            ),

            className="shadow-sm"
        ),

        html.Br(),

        # EXECUTIVE INTERPRETATION

        dbc.Card(
            dbc.CardBody(
                [
                    html.H4(
                        "Executive Interpretation",
                        className="mb-1",
                        style={
                            "color": OREY_NAVY,
                            "fontWeight": "700"
                        }
                    ),

                    html.P(
                        "What the current customer mix suggests for management.",
                        className="mb-4 fst-italic"
                    ),

                    dbc.Row(
                        [
                            dbc.Col(
                                dbc.Card(
                                    dbc.CardBody(
                                        [
                                            html.Small(
                                                "VALUE CONCENTRATION",
                                                style={
                                                    "fontWeight": "700",
                                                    "color": OREY_BLUE
                                                }
                                            ),

                                            html.H5(
                                                largest_segment,
                                                className="mt-2 mb-2",
                                                style={
                                                    "fontWeight": "700",
                                                    "color": OREY_NAVY
                                                }
                                            ),

                                            html.P(
                                                (
                                                    f"{largest_segment} "
                                                    f"contributes "
                                                    f"{largest_revenue_share:.1f}% "
                                                    "of total revenue, making "
                                                    "its performance important "
                                                    "to overall business results."
                                                ),
                                                className="mb-0",
                                                style={
                                                    "color": "#000000"
                                                }
                                            )
                                        ]
                                    ),

                                    className="border-0 shadow-sm h-100"
                                ),

                                xs=12,
                                lg=4
                            ),

                            dbc.Col(
                                dbc.Card(
                                    dbc.CardBody(
                                        [
                                            html.Small(
                                                "PROFITABILITY",
                                                style={
                                                    "fontWeight": "700",
                                                    "color": OREY_GREEN
                                                }
                                            ),

                                            html.H5(
                                                strongest_margin_segment,
                                                className="mt-2 mb-2",
                                                style={
                                                    "fontWeight": "700",
                                                    "color": OREY_NAVY
                                                }
                                            ),

                                            html.P(
                                                (
                                                    f"This segment records "
                                                    f"the strongest margin at "
                                                    f"{data['ProfitMargin'].max():.1f}%. "
                                                    f"{lowest_margin_segment} "
                                                    "may require closer review "
                                                    "of pricing, costs or "
                                                    "customer economics."
                                                ),
                                                className="mb-0",
                                                style={
                                                    "color": "#000000"
                                                }
                                            )
                                        ]
                                    ),

                                    className="border-0 shadow-sm h-100"
                                ),

                                xs=12,
                                lg=4
                            ),

                            dbc.Col(
                                dbc.Card(
                                    dbc.CardBody(
                                        [
                                            html.Small(
                                                "CUSTOMER RISK",
                                                style={
                                                    "fontWeight": "700",
                                                    "color": OREY_RED
                                                }
                                            ),

                                            html.H5(
                                                highest_return_segment,
                                                className="mt-2 mb-2",
                                                style={
                                                    "fontWeight": "700",
                                                    "color": OREY_NAVY
                                                }
                                            ),

                                            html.P(
                                                return_message,
                                                className="mb-0",
                                                style={
                                                    "color": "#000000"
                                                }
                                            )

                                        ]

                                    ),

                                    className="border-0 shadow-sm h-100"
                                ),

                                xs=12,
                                lg=4
                            )
                        ],

                        className="g-3"
                    ),

                    html.Hr(
                        className="my-4"
                    ),

                    html.P(
                        profitability_message,
                        className="mb-2"
                    ),

                    html.P(
                        (
                            f"The concentration of revenue in "
                            f"{largest_segment} means changes in this "
                            "segment could have a material effect on "
                            "overall performance. Management should "
                            "therefore balance growth opportunities with "
                            "segment-level profitability and return risk."
                        ),
                        className="mb-0"
                    )
                ]
            ),

            className="shadow-sm"
        )
    ],

    fluid=True
)