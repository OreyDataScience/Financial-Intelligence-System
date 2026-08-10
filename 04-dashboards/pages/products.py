from dash import html, dcc, register_page
import dash_bootstrap_components as dbc

from components.cards import kpi_card
from components.product_chart import top_products_chart

from scripts.data_loader import products, top_products, bottom_products
from scripts.utils import format_currency

register_page(
    __name__,
    path="/products",
    name="Products"
)

# KPIs

total_revenue = products["Revenue"].sum()

total_profit = products["Profit"].sum()

total_units = products["UnitsSold"].sum()

avg_margin = products["AvgMargin"].mean()

# TABLE DATA

top_products_table = top_products[
    ["ProductName", "Category", "Revenue", "Profit"]
].head(10).copy()

bottom_products_table = bottom_products[
    ["ProductName", "Category", "Revenue", "Profit"]
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

top_products_table = top_products_table.rename(
    columns={
        "ProductName": "Product",
        "Category": "Category",
        "Revenue": "Revenue",
        "Profit": "Profit"
    }
)

bottom_products_table = bottom_products_table.rename(
    columns={
        "ProductName": "Product",
        "Category": "Category",
        "Revenue": "Revenue",
        "Profit": "Profit"
    }
)

# LAYOUT

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

        # KPI CARDS

        dbc.Row(
            [
                dbc.Col(
                    kpi_card(
                        "Revenue",
                        format_currency(total_revenue),
                        "Portfolio",
                        "#3498DB"
                    ),
                    lg=3
                ),

                dbc.Col(
                    kpi_card(
                        "Profit",
                        format_currency(total_profit),
                        "Portfolio",
                        "#2ECC71"
                        if total_profit >= 0
                        else "#C0392B"
                    ),
                    lg=3
                ),

                dbc.Col(
                    kpi_card(
                        "Units Sold",
                        f"{total_units:,.0f}",
                        "Products",
                        "#6C3483"
                    ),
                    lg=3
                ),

                dbc.Col(
                    kpi_card(
                        "Average Margin",
                        f"{avg_margin:.1f}%",
                        "Portfolio",
                        "#2ECC71"
                        if avg_margin >= 0
                        else "#C0392B"
                    ),
                    lg=3
                )
            ],

            className="g-4"
        ),

        html.Br(),

        # PRODUCT REVENUE CHART

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
                                    "Top Products"
                                ),

                                html.P(
                                    "Highest-revenue products by category.",
                                    className="mb-3",
                                    style={
                                        "fontStyle": "italic",
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

                        className="h-100"
                    ),

                    lg=6
                ),

                # BOTTOM PRODUCTS

                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.H4(
                                    "Bottom Products"
                                ),

                                html.P(
                                    "Lowest-revenue products by category.",
                                    className="mb-3",
                                    style={
                                        "fontStyle": "italic",
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

                        className="h-100"
                    ),

                    lg=6
                )
            ],

            className="g-4"
        )
    ],

    fluid=True
)