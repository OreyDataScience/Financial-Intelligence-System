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

# ==========================================================
# METRICS
# ==========================================================

total_revenue = stores["Revenue"].sum()

total_profit = stores["Profit"].sum()

avg_margin = stores["AvgMargin"].mean()

avg_stockout = stores["StockOutRate"].mean()

# ==========================================================
# HIGH-RISK STORE TABLE
# ==========================================================

risk_table = high_risk_stores[
    [
        "StoreID",
        "StoreLocation",
        "StockOutRate",
        "ReturnRate"
    ]
].head(10).copy()

# Convert Stock-Out Rate to percentage
risk_table["StockOutRate"] = (
    risk_table["StockOutRate"]
    .round(4)
    .mul(100)
    .map(
        lambda x: f"{x:.2f}%"
    )
)

# Convert Return Rate to percentage
risk_table["ReturnRate"] = (
    risk_table["ReturnRate"]
    .round(4)
    .mul(100)
    .map(
        lambda x: f"{x:.2f}%"
    )
)

# Rename columns for presentation
risk_table = risk_table.rename(

    columns={
        "StoreID": "Store",

        "StoreLocation": "Location",

        "StockOutRate": "Stock-Out Rate",

        "ReturnRate": "Return Rate"
    }
)

# ==========================================================
# LAYOUT
# ==========================================================

layout = dbc.Container(
    [
        # ==================================================
        # PAGE HEADER
        # ==================================================

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
                        "#3498DB"
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
                        "#2ECC71"
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
                        (
                            "#2ECC71"
                            if avg_margin >= 0
                            else "#C0392B"
                        )
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
                        (
                            "#F39C12"
                            if avg_stockout * 100 < 5
                            else "#C0392B"
                        )
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
        # REVENUE CHART
        # ==================================================

        dbc.Card(
            dbc.CardBody(
                [
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

        # ==================================================
        # PROFIT CHART
        # ==================================================

        dbc.Card(
            dbc.CardBody(
                [
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

        # ==================================================
        # HIGH-RISK STORES + REVENUE SHARE
        # ==========================================================

        dbc.Row(
            [
                # ==========================================
                # HIGH-RISK STORES
                # ==========================================

                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.H5(
                                    "High-Risk Stores",
                                    className="mb-1"
                                ),

                                html.P(
                                    "Stores requiring operational attention.",
                                    className="mb-2",
                                    style={
                                        "fontStyle": "italic",
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

                                    className="mb-0"
                                )
                            ]
                        ),

                        className="shadow-sm h-100"
                    ),

                    lg=7
                ),

                # ==========================================
                # REVENUE SHARE PIE CHART
                # ==========================================

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