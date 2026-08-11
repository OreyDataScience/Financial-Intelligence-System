from dash import html, dcc, register_page
import dash_bootstrap_components as dbc

from components.cards import kpi_card

from components.channel_chart import (
    channel_revenue_chart,
    channel_share_chart,
    channel_margin_chart,
    channel_return_rate_chart,
    channel_performance_matrix
)

from scripts.data_loader import channels
from scripts.utils import format_currency

register_page(
    __name__,
    path="/channels",
    name="Channel Analysis"
)

OREY_NAVY = "#061A35"
OREY_BLUE = "#1479D2"
OREY_GREEN = "#2ECC71"
OREY_ORANGE = "#F39C12"
OREY_RED = "#C0392B"
OREY_PURPLE = "#8E44AD"
OREY_GREY = "#7F8C8D"

# DATA PREPARATION

data = channels.copy()

data["ProfitMargin"] = (
    data["Profit"] /
    data["Revenue"].replace(0, None)
    * 100
)

data["ReturnRatePercent"] = (
    data["ReturnRate"] * 100
)

# PORTFOLIO METRICS

total_revenue = data["Revenue"].sum()

total_profit = data["Profit"].sum()

portfolio_margin = (
    total_profit /
    total_revenue
    * 100

    if total_revenue != 0
    else 0
)

avg_margin = data["ProfitMargin"].mean()

avg_returns = data["ReturnRate"].mean()

# BEST / WEAKEST CHANNELS

best_revenue_channel = (
    data.loc[
        data["Revenue"].idxmax(),
        "SalesChannel"
    ]
)

best_margin_channel = (
    data.loc[
        data["ProfitMargin"].idxmax(),
        "SalesChannel"
    ]
)

highest_return_channel = (
    data.loc[
        data["ReturnRate"].idxmax(),
        "SalesChannel"
    ]
)


lowest_margin_channel = (
    data.loc[
        data["ProfitMargin"].idxmin(),
        "SalesChannel"
    ]
)

# CHANNEL PERFORMANCE TABLE

table_data = data[
    [
        "SalesChannel",
        "Revenue",
        "Profit",
        "ProfitMargin",
        "Revenue_Share",
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

    if value <= avg_returns * 100:

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

channel_rows = []

for _, row in table_data.iterrows():

    channel_rows.append(
        html.Tr(
            [
                html.Td(
                    row["SalesChannel"],
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
                    f"{row['Revenue_Share'] * 100:.1f}%"

                    if row["Revenue_Share"] <= 1

                    else

                    f"{row['Revenue_Share']:.1f}%"
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

if portfolio_margin >= avg_margin:

    profitability_message = (
        f"The overall portfolio margin is "
        f"{portfolio_margin:.1f}%, indicating that "
        f"the channel mix is currently generating "
        f"healthy profitability relative to the "
        f"average channel margin. "
        f"{best_margin_channel} is the strongest "
        f"channel on margin performance."
    )

else:

    profitability_message = (
        f"The overall portfolio margin is "
        f"{portfolio_margin:.1f}%, below the "
        f"average channel margin of "
        f"{avg_margin:.1f}%. "
        f"This suggests that profitability is "
        f"uneven across the channel mix, with "
        f"{best_margin_channel} currently providing "
        f"the strongest margin performance."
    )

return_message = (
    f"{highest_return_channel} has the highest "
    f"return rate at "
    f"{data['ReturnRatePercent'].max():.2f}%. "
    f"This should be monitored for potential "
    f"product mix, customer behaviour or "
    f"channel-specific fulfilment issues."
)

# LAYOUT

layout = dbc.Container(
    [
        # PAGE HEADER

        html.H1(
            "Channel Analysis",
            className="mb-1"
        ),

        html.P(
            "Understanding where revenue is generated, where profit is created and where channel-level risk is emerging.",

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

                        "All Channels",
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

                        "All Channels",
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
                        f"{avg_returns * 100:.1f}%",
                        "Channel Average",
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

        # EXECUTIVE CHANNEL INSIGHT

        dbc.Card(
            dbc.CardBody(
                [
                    html.H5(
                        "Channel Intelligence",
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
                                        "Largest Revenue Channel",
                                        className="text-muted"
                                    ),

                                    html.Div(
                                        best_revenue_channel,
                                        style={
                                            "fontWeight": "700",
                                            "fontSize": "18px",
                                            "color": OREY_BLUE
                                        }
                                    )
                                ],

                                xs=12,
                                md=4
                            ),

                            dbc.Col(
                                [
                                    html.Small(
                                        "Strongest Margin Channel",
                                        className="text-muted"
                                    ),

                                    html.Div(
                                        best_margin_channel,
                                        style={
                                            "fontWeight": "700",
                                            "fontSize": "18px",
                                            "color": OREY_GREEN
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
                                        className="text-muted"

                                    ),

                                    html.Div(
                                        highest_return_channel,
                                        style={
                                            "fontWeight": "700",
                                            "fontSize": "18px",
                                            "color": OREY_RED
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

        # REVENUE + SHARE

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

                    xs=12,
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

                    xs=12,
                    lg=5
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
                        "Channel Performance Matrix",
                        className="mb-1",
                        style={
                            "color": OREY_NAVY,
                            "fontWeight": "700"
                        }
                    ),

                    html.P(
                        "Revenue is compared with profit margin to identify channels that create scale, profitability or potential performance concerns.",
                        className="mb-3 fst-italic"
                    ),

                    dcc.Graph(
                        id="channel-performance-matrix",
                        figure=channel_performance_matrix(
                            channels
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

        # MARGIN + RETURN RATE

        dbc.Row(
            [
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            dcc.Graph(
                                id="channel-margin-chart",
                                figure=channel_margin_chart(
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

                    xs=12,
                    lg=6
                ),

                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            dcc.Graph(
                                id="channel-return-rate-chart",
                                figure=channel_return_rate_chart(
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

                    xs=12,
                    lg=6
                )
            ],

            className="g-4"
        ),

        html.Br(),

        # CHANNEL INTELLIGENCE TABLE

        dbc.Card(
            dbc.CardBody(
                [
                    html.H4(
                        "Channel Intelligence",
                        className="mb-1",
                        style={
                            "color": OREY_NAVY,
                            "fontWeight": "700"
                        }
                    ),

                    html.P(
                        "Channel-level performance indicators highlighting revenue contribution, profitability and customer return exposure.",
                        className="mb-3 fst-italic"

                    ),

                    dbc.Table(
                        [
                            html.Thead(
                                html.Tr(
                                    [
                                        html.Th(
                                            "Sales Channel"
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
                                channel_rows
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
                    html.Div(
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
                                "Management view of channel performance, profitability and emerging risk.",
                                className="mb-0 fst-italic",
                                style={
                                    "color": OREY_GREY
                                }
                            )
                        ]
                    ),

                    html.Hr(),

                    # PROFITABILITY INSIGHT

                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.Div(
                                    "PROFITABILITY",
                                    style={
                                        "fontSize": "12px",
                                        "fontWeight": "700",
                                        "letterSpacing": "1px",
                                        "color": OREY_GREEN
                                    }
                                ),

                                html.H5(
                                    "Channel margin position",
                                    className="mt-1 mb-2",
                                    style={
                                        "color": OREY_NAVY,
                                        "fontWeight": "700"
                                    }
                                ),

                                html.P(
                                    profitability_message,
                                    className="mb-0"
                                )
                            ]
                        ),

                        className="border-0 shadow-sm mb-3"
                    ),

                    # SCALE INSIGHT

                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.Div(
                                    "REVENUE CONCENTRATION",
                                    style={
                                        "fontSize": "12px",
                                        "fontWeight": "700",
                                        "letterSpacing": "1px",
                                        "color": OREY_BLUE
                                    }
                                ),

                                html.H5(
                                    "Where the business is most exposed",
                                    className="mt-1 mb-2",
                                    style={
                                        "color": OREY_NAVY,
                                        "fontWeight": "700"
                                    }
                                ),

                                html.P(
                                    (
                                        f"{best_revenue_channel} currently "
                                        f"represents the largest revenue "
                                        f"channel. Its performance therefore "
                                        f"has the greatest potential impact "
                                        f"on overall business results."
                                    ),

                                    className="mb-0"
                                )
                            ]
                        ),

                        className="border-0 shadow-sm mb-3"
                    ),

                    # RISK INSIGHT

                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.Div(
                                    "OPERATIONAL RISK",
                                    style={
                                        "fontSize": "12px",
                                        "fontWeight": "700",
                                        "letterSpacing": "1px",
                                        "color": OREY_RED
                                    }
                                ),

                                html.H5(
                                    "Return exposure requiring attention",
                                    className="mt-1 mb-2",
                                    style={
                                        "color": OREY_NAVY,
                                        "fontWeight": "700"
                                    }
                                ),

                                html.P(
                                    return_message,
                                    className="mb-0"
                                )
                            ]
                        ),

                        className="border-0 shadow-sm"
                    )
                ]
            ),

            className="shadow-sm"
        )
    ],

    fluid=True

)