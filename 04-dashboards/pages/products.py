from dash import html, dcc, register_page
import dash_bootstrap_components as dbc

from components.cards import kpi_card
from components.product_chart import top_products_chart

from scripts.data_loader import (
    products,
    top_products,
    bottom_products
)

from scripts.utils import format_currency

register_page(
    __name__,
    path="/products",
    name="Products"
)

# METRICS

total_revenue = (
    products["Revenue"].sum()
)

total_profit = (
    products["Profit"].sum()
)

total_units = (
    products["UnitsSold"].sum()
)

avg_margin = (
    products["AvgMargin"].mean()
    * 100
)

# PRODUCT INTELLIGENCE

# Highest revenue product

top_revenue_product = (
    products.loc[
        products["Revenue"].idxmax()
    ]
)

# Highest profit product

top_profit_product = (
    products.loc[
        products["Profit"].idxmax()
    ]
)

# Highest margin product

top_margin_product = (
    products.loc[
        products["AvgMargin"].idxmax()
    ]
)

# Lowest margin product

lowest_margin_product = (
    products.loc[
        products["AvgMargin"].idxmin()
    ]
)

# Highest return-rate product

highest_return_product = (
    products.loc[
        products["ReturnRate"].idxmax()
    ]
)

# Highest units-sold product

top_units_product = (
    products.loc[
        products["UnitsSold"].idxmax()
    ]
)

# KPI COLOURS

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

# TABLE DATA

top_products_table = top_products[
    [
        "ProductName",
        "Category",
        "Revenue",
        "Profit"
    ]
].head(10).copy()

bottom_products_table = bottom_products[
    [
        "ProductName",
        "Category",
        "Revenue",
        "Profit"
    ]
].head(10).copy()

# FORMAT FINANCIAL VALUES

top_products_table["Revenue"] = (
    top_products_table["Revenue"].map(
        lambda x: f"R {x:,.2f}"
    )
)

top_products_table["Profit"] = (
    top_products_table["Profit"].map(
        lambda x: f"R {x:,.2f}"
    )
)

bottom_products_table["Revenue"] = (
    bottom_products_table["Revenue"].map(
        lambda x: f"R {x:,.2f}"
    )
)

bottom_products_table["Profit"] = (
    bottom_products_table["Profit"].map(
        lambda x: f"R {x:,.2f}"
    )
)


# RENAME TABLE COLUMNS

top_products_table = (
    top_products_table.rename(
        columns={
            "ProductName": "Product",
            "Category": "Category",
            "Revenue": "Revenue",
            "Profit": "Profit"
        }
    )
)

bottom_products_table = (
    bottom_products_table.rename(
        columns={
            "ProductName": "Product",
            "Category": "Category",
            "Revenue": "Revenue",
            "Profit": "Profit"
        }
    )
)


# LAYOUT

layout = dbc.Container(
    [
        # PAGE HEADER

        html.H1(
            "Product Analytics",
            className="mb-1"
        ),

        html.P(
            "Revenue, profitability and product-level performance across the portfolio.",
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
                        "Portfolio",
                        "#1479D2"
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
                        "Portfolio",
                        profit_colour
                    ),
                    xs=12,
                    sm=6,
                    lg=3
                ),

                dbc.Col(
                    kpi_card(
                        "Units Sold",
                        f"{total_units:,.0f}",
                        "Product Portfolio",
                        "#5B2C83"
                    ),
                    xs=12,
                    sm=6,
                    lg=3
                ),

                dbc.Col(
                    kpi_card(
                        "Average Margin",
                        f"{avg_margin:.2f}%",
                        "Product Portfolio",
                        margin_colour
                    ),
                    xs=12,
                    sm=6,
                    lg=3
                )

            ],
            className="g-4"
        ),

        html.Br(),

        # PRODUCT PERFORMANCE SNAPSHOT

        dbc.Card(
            dbc.CardBody(
                [
                    html.H5(
                        "Product Performance Snapshot",
                        className="mb-3",
                        style={
                            "color": "#061A35",
                            "fontWeight": "700"
                        }
                    ),

                    dbc.Row(
                        [
                            # HIGHEST REVENUE

                            dbc.Col(
                                [
                                    html.Small(
                                        "Highest Revenue",
                                        className="text-muted"
                                    ),

                                    html.Div(
                                        str(
                                            top_revenue_product[
                                                "ProductName"
                                            ]
                                        ),
                                        style={
                                            "fontSize": "1.05rem",
                                            "fontWeight": "700",
                                            "color": "#1479D2"
                                        }
                                    ),

                                    html.Div(
                                        format_currency(
                                            top_revenue_product[
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

                            # HIGHEST PROFIT

                            dbc.Col(
                                [
                                    html.Small(
                                        "Highest Profit",
                                        className="text-muted"
                                    ),

                                    html.Div(
                                        str(
                                            top_profit_product[
                                                "ProductName"
                                            ]
                                        ),
                                        style={
                                            "fontSize": "1.05rem",
                                            "fontWeight": "700",
                                            "color": "#2EAD76"
                                        }
                                    ),

                                    html.Div(
                                        format_currency(
                                            top_profit_product[
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

                            # HIGHEST MARGIN

                            dbc.Col(
                                [
                                    html.Small(
                                        "Highest Margin",
                                        className="text-muted"
                                    ),

                                    html.Div(
                                        str(
                                            top_margin_product[
                                                "ProductName"
                                            ]
                                        ),
                                        style={
                                            "fontSize": "1.05rem",
                                            "fontWeight": "700",
                                            "color": "#5B2C83"
                                        }
                                    ),

                                    html.Div(
                                        f"{top_margin_product['AvgMargin'] * 100:.2f}%",
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

        # TOP PRODUCTS REVENUE CHART

        dbc.Card(
            dbc.CardBody(
                [
                    html.H4(
                        "Product Revenue Performance",
                        className="mb-1",
                        style={
                            "color": "#000000"
                        }
                    ),

                    html.P(
                        "Top products ranked by revenue, with category shown for portfolio context.",
                        className="mb-3 fst-italic",
                        style={
                            "color": "#000000"
                        }
                    ),

                    dcc.Graph(
                        id="product-revenue-chart",

                        figure=top_products_chart(
                            products
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

        # PRODUCT OPERATIONAL POSITION

        dbc.Card(
            dbc.CardBody(
                [
                    html.H4(
                        "Product Operational Position",
                        className="mb-1",
                        style={
                            "color": "#061A35",
                            "fontWeight": "700"
                        }
                    ),

                    html.P(
                        "Product-level indicators highlighting margin strength, return exposure and sales concentration.",
                        className="mb-4 fst-italic"
                    ),

                    dbc.Row(
                        [
                            # HIGHEST MARGIN

                            dbc.Col(
                                dbc.Card(
                                    dbc.CardBody(
                                        [
                                            html.H6(
                                                "Highest Margin",
                                                style={
                                                    "color": "#061A35"
                                                }
                                            ),

                                            html.H3(
                                                f"{top_margin_product['AvgMargin'] * 100:.2f}%",
                                                style={
                                                    "color": "#2EAD76"
                                                }
                                            ),

                                            html.P(
                                                str(
                                                    top_margin_product[
                                                        "ProductName"
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
                                md=4
                            ),

                            # LOWEST MARGIN

                            dbc.Col(
                                dbc.Card(
                                    dbc.CardBody(
                                        [
                                            html.H6(
                                                "Lowest Margin",
                                                style={
                                                    "color": "#061A35"
                                                }
                                            ),

                                            html.H3(
                                                f"{lowest_margin_product['AvgMargin'] * 100:.2f}%",
                                                style={
                                                    "color": "#C0392B"
                                                }
                                            ),

                                            html.P(
                                                str(
                                                    lowest_margin_product[
                                                        "ProductName"
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
                                md=4
                            ),

                            # HIGHEST RETURNS

                            dbc.Col(
                                dbc.Card(
                                    dbc.CardBody(
                                        [
                                            html.H6(
                                                "Highest Return Rate",
                                                style={
                                                    "color": "#061A35"
                                                }
                                            ),

                                            html.H3(
                                                f"{highest_return_product['ReturnRate'] * 100:.2f}%",
                                                style={
                                                    "color": "#F39C12"
                                                }
                                            ),

                                            html.P(
                                                str(
                                                    highest_return_product[
                                                        "ProductName"
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
                                md=4
                            )
                        ],
                        className="g-3"
                    )
                ]
            ),
            className="shadow-sm"
        ),

        html.Br(),

        # TOP & BOTTOM PRODUCTS

        dbc.Row(
            [
                # TOP PRODUCTS

                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.H4(
                                    "Top Products",
                                    style={
                                        "color": "#061A35",
                                        "fontWeight": "700"
                                    }
                                ),

                                html.P(
                                    "Highest-revenue products by category.",
                                    className="mb-3 fst-italic",
                                    style={
                                        "color": "#000000"
                                    }
                                ),

                                html.Hr(),

                                dbc.Table.from_dataframe(
                                    top_products_table,
                                    striped=True,
                                    hover=True,
                                    bordered=False,
                                    size="sm",
                                    responsive=True
                                )
                            ]
                        ),
                        className="h-100 shadow-sm"
                    ),
                    lg=6
                ),

                # BOTTOM PRODUCTS

                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.H4(
                                    "Bottom Products",
                                    style={
                                        "color": "#061A35",
                                        "fontWeight": "700"
                                    }
                                ),

                                html.P(
                                    "Lowest-revenue products by category.",
                                    className="mb-3 fst-italic",
                                    style={
                                        "color": "#000000"
                                    }
                                ),

                                html.Hr(),

                                dbc.Table.from_dataframe(
                                    bottom_products_table,
                                    striped=True,
                                    hover=True,
                                    bordered=False,
                                    size="sm",
                                    responsive=True
                                )
                            ]
                        ),
                        className="h-100 shadow-sm"
                    ),
                    lg=6
                )
            ],
            className="g-4"
        )
    ],
    fluid=True
)