from dash import html, dcc, register_page
import dash_bootstrap_components as dbc

from components.cards import kpi_card

from components.store_chart import (
    top_stores_chart,
    store_profit_chart,
    store_revenue_share_chart
)

from scripts.data_loader import (
    stores,
    high_risk_stores
)

from scripts.utils import format_currency


register_page(
    __name__,
    path="/stores",
    name="Stores"
)


# ============================================================
# METRICS
# ============================================================

total_revenue = stores["Revenue"].sum()

total_profit = stores["Profit"].sum()

# IMPORTANT:
# Calculate from full-precision CSV values.
# Only round when displaying the KPI.
avg_margin = (
    stores["AvgMargin"].mean()
    * 100
)

avg_stockout = (
    stores["StockOutRate"].mean()
)


# ============================================================
# ADDITIONAL STORE INTELLIGENCE
# ============================================================

# Highest revenue store
top_revenue_store = (
    stores.loc[
        stores["Revenue"].idxmax()
    ]
)

# Highest profit store
top_profit_store = (
    stores.loc[
        stores["Profit"].idxmax()
    ]
)

# Highest margin store
top_margin_store = (
    stores.loc[
        stores["AvgMargin"].idxmax()
    ]
)

# Highest stock-out store
top_stockout_store = (
    stores.loc[
        stores["StockOutRate"].idxmax()
    ]
)

# Lowest stock-out store
lowest_stockout_store = (
    stores.loc[
        stores["StockOutRate"].idxmin()
    ]
)


# ============================================================
# KPI COLOURS
# ============================================================

profit_colour = (
    "#2ECC71"
    if total_profit >= 0
    else "#C0392B"
)

margin_colour = (
    "#2ECC71"
    if avg_margin >= 0
    else "#C0392B"
)

stockout_colour = (
    "#F39C12"
    if avg_stockout * 100 < 5
    else "#C0392B"
)


# ============================================================
# HIGH-RISK STORE TABLE
# ============================================================

risk_table = high_risk_stores[
    [
        "StoreID",
        "StoreLocation",
        "StockOutRate",
        "ReturnRate"
    ]
].head(10).copy()


risk_table["StockOutRate"] = (
    risk_table["StockOutRate"]
    .mul(100)
    .map(
        lambda x: f"{x:.2f}%"
    )
)


risk_table["ReturnRate"] = (
    risk_table["ReturnRate"]
    .mul(100)
    .map(
        lambda x: f"{x:.2f}%"
    )
)


risk_table = risk_table.rename(
    columns={
        "StoreID": "Store",
        "StoreLocation": "Location",
        "StockOutRate": "Stock-Out Rate",
        "ReturnRate": "Return Rate"
    }
)


# ============================================================
# LAYOUT
# ============================================================

layout = dbc.Container(
    [

        # ====================================================
        # PAGE HEADER
        # ====================================================

        html.H1(
            "Store Performance",
            className="mb-1"
        ),

        html.P(
            "Revenue, profitability and operational performance across stores.",
            className="text-muted"
        ),

        html.Br(),


        # ====================================================
        # KPI CARDS
        # ====================================================

        dbc.Row(
            [

                dbc.Col(
                    kpi_card(
                        "Revenue",
                        format_currency(total_revenue),
                        "All Stores",
                        "#1479D2"
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
                        profit_colour
                    ),
                    xs=12,
                    sm=6,
                    lg=3
                ),

                dbc.Col(
                    kpi_card(
                        "Average Margin",
                        f"{avg_margin:.2f}%",
                        "Store Portfolio",
                        margin_colour
                    ),
                    xs=12,
                    sm=6,
                    lg=3
                ),

                dbc.Col(
                    kpi_card(
                        "Stock-Out Rate",
                        f"{avg_stockout * 100:.2f}%",
                        "Store Average",
                        stockout_colour
                    ),
                    xs=12,
                    sm=6,
                    lg=3
                )

            ],
            className="g-4"
        ),

        html.Br(),


        # ====================================================
        # STORE PERFORMANCE SNAPSHOT
        # ====================================================

        dbc.Card(
            dbc.CardBody(
                [

                    html.H5(
                        "Store Performance Snapshot",
                        className="mb-3",
                        style={
                            "color": "#061A35",
                            "fontWeight": "700"
                        }
                    ),

                    dbc.Row(
                        [

                            dbc.Col(
                                [

                                    html.Small(
                                        "Highest Revenue",
                                        className="text-muted"
                                    ),

                                    html.Div(
                                        str(
                                            top_revenue_store[
                                                "StoreID"
                                            ]
                                        ),
                                        style={
                                            "fontSize": "1.15rem",
                                            "fontWeight": "700",
                                            "color": "#1479D2"
                                        }
                                    ),

                                    html.Div(
                                        format_currency(
                                            top_revenue_store[
                                                "Revenue"
                                            ]
                                        ),
                                        style={
                                            "fontSize": "0.85rem",
                                            "color": "#061A35"
                                        }
                                    )

                                ],
                                xs=12,
                                md=4
                            ),

                            dbc.Col(
                                [

                                    html.Small(
                                        "Highest Profit",
                                        className="text-muted"
                                    ),

                                    html.Div(
                                        str(
                                            top_profit_store[
                                                "StoreID"
                                            ]
                                        ),
                                        style={
                                            "fontSize": "1.15rem",
                                            "fontWeight": "700",
                                            "color": "#2EAD76"
                                        }
                                    ),

                                    html.Div(
                                        format_currency(
                                            top_profit_store[
                                                "Profit"
                                            ]
                                        ),
                                        style={
                                            "fontSize": "0.85rem",
                                            "color": "#061A35"
                                        }
                                    )

                                ],
                                xs=12,
                                md=4
                            ),

                            dbc.Col(
                                [

                                    html.Small(
                                        "Highest Margin",
                                        className="text-muted"
                                    ),

                                    html.Div(
                                        str(
                                            top_margin_store[
                                                "StoreID"
                                            ]
                                        ),
                                        style={
                                            "fontSize": "1.15rem",
                                            "fontWeight": "700",
                                            "color": "#5B2C83"
                                        }
                                    ),

                                    html.Div(
                                        f"{top_margin_store['AvgMargin'] * 100:.2f}%",
                                        style={
                                            "fontSize": "0.85rem",
                                            "color": "#061A35"
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


        # ====================================================
        # REVENUE PERFORMANCE
        # ====================================================

        dbc.Card(
            dbc.CardBody(
                [

                    html.H4(
                        "Store Revenue Performance",
                        className="mb-1",
                        style={
                            "color": "#000000"
                        }
                    ),

                    html.P(
                        "Top stores ranked by revenue, with store risk shown for context.",
                        className="mb-3 fst-italic",
                        style={
                            "color": "#000000"
                        }
                    ),

                    dcc.Graph(
                        id="store-revenue-chart",

                        figure=top_stores_chart(
                            stores
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


        # ====================================================
        # PROFIT PERFORMANCE
        # ====================================================

        dbc.Card(
            dbc.CardBody(
                [

                    html.H4(
                        "Store Profit Performance",
                        className="mb-1",
                        style={
                            "color": "#000000"
                        }
                    ),

                    html.P(
                        "Top stores ranked by profit, with operational risk shown alongside financial performance.",
                        className="mb-3 fst-italic",
                        style={
                            "color": "#000000"
                        }
                    ),

                    dcc.Graph(
                        id="store-profit-chart",

                        figure=store_profit_chart(
                            stores
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


        # ====================================================
        # OPERATIONAL POSITION
        # ====================================================

        dbc.Card(
            dbc.CardBody(
                [

                    html.H4(
                        "Store Operational Position",
                        className="mb-1",
                        style={
                            "color": "#061A35",
                            "fontWeight": "700"
                        }
                    ),

                    html.P(
                        "Store-level operational indicators highlighting where availability risk is concentrated.",
                        className="mb-4 fst-italic"
                    ),

                    dbc.Row(
                        [

                            dbc.Col(
                                dbc.Card(
                                    dbc.CardBody(
                                        [

                                            html.H6(
                                                "Highest Stock-Out Rate",
                                                style={
                                                    "color": "#061A35"
                                                }
                                            ),

                                            html.H3(
                                                f"{top_stockout_store['StockOutRate'] * 100:.2f}%",
                                                style={
                                                    "color": "#C0392B"
                                                }
                                            ),

                                            html.P(
                                                str(
                                                    top_stockout_store[
                                                        "StoreID"
                                                    ]
                                                ),
                                                className="mb-0",
                                                style={
                                                    "color": "#000000",
                                                    "fontWeight": "600"
                                                }
                                            )

                                        ]
                                    ),
                                    className="border-0 shadow-sm"
                                ),
                                xs=12,
                                md=6
                            ),

                            dbc.Col(
                                dbc.Card(
                                    dbc.CardBody(
                                        [

                                            html.H6(
                                                "Lowest Stock-Out Rate",
                                                style={
                                                    "color": "#061A35"
                                                }
                                            ),

                                            html.H3(
                                                f"{lowest_stockout_store['StockOutRate'] * 100:.2f}%",
                                                style={
                                                    "color": "#2EAD76"
                                                }
                                            ),

                                            html.P(
                                                str(
                                                    lowest_stockout_store[
                                                        "StoreID"
                                                    ]
                                                ),
                                                className="mb-0",
                                                style={
                                                    "color": "#000000",
                                                    "fontWeight": "600"
                                                }
                                            )

                                        ]
                                    ),
                                    className="border-0 shadow-sm"
                                ),
                                xs=12,
                                md=6
                            )

                        ],
                        className="g-3"
                    )

                ]
            ),
            className="shadow-sm"
        ),

        html.Br(),


        # ====================================================
        # HIGH-RISK STORES + REVENUE SHARE
        # ====================================================

        dbc.Row(
            [

                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            [

                                html.H4(
                                    "High-Risk Stores",
                                    className="mb-1",
                                    style={
                                        "color": "#061A35",
                                        "fontWeight": "700"
                                    }
                                ),

                                html.P(
                                    "Stores requiring operational attention based on elevated risk indicators.",
                                    className="mb-3 fst-italic",
                                    style={
                                        "color": "#000000"
                                    }
                                ),

                                html.Hr(),

                                dbc.Table.from_dataframe(
                                    risk_table,
                                    striped=True,
                                    bordered=False,
                                    hover=True,
                                    size="sm",
                                    responsive=True,
                                    className="mb-0"
                                )

                            ]
                        ),
                        className="shadow-sm h-100"
                    ),
                    lg=7
                ),

                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            [

                                dcc.Graph(
                                    id="store-revenue-share-chart",

                                    figure=store_revenue_share_chart(
                                        stores
                                    ),

                                    config={
                                        "displayModeBar": True,
                                        "displaylogo": False,
                                        "responsive": True
                                    }
                                )

                            ]
                        ),
                        className="shadow-sm h-100"
                    ),
                    lg=5
                )

            ],
            className="g-4"
        )

    ],
    fluid=True
)