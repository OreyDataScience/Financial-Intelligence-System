from dash import html, dcc, register_page
import dash_bootstrap_components as dbc

from components.cards import kpi_card
from components.inventory_chart import (
    inventory_by_category_chart,
    inventory_revenue_chart
)

from scripts.data_loader import inventory, inventory_summary
from scripts.utils import format_currency


register_page(
    __name__,
    path="/inventory",
    name="Inventory"
)

# METRICS

total_inventory = inventory["Avg_Inventory"].sum()

avg_stockout = inventory["StockOutRate"].mean()

total_revenue = inventory["Revenue"].sum()

total_profit = inventory["Profit"].sum()

# CONDITIONAL KPI COLOURS
# Stock-Out Rate, Below 5% = Orange & 5% or higher = Red

stockout_colour = (
    "#F39C12"
    if avg_stockout < 0.05
    else "#C0392B"
)

# Profit, Positive = Green & Negative = Red

profit_colour = (
    "#2ECC71"
    if total_profit >= 0
    else "#C0392B"
)

# PREPARE INVENTORY RISK TABLE

risk_table = inventory_summary[
    [
        "Category",
        "StockOutRate",
        "Inventory_Risk",
        "Revenue"
    ]
].head(10).copy()

# Format Revenue with R and 2 decimal places
risk_table["Revenue"] = risk_table["Revenue"].apply(
    lambda x: f"R {x:,.2f}"
)

# Convert Stock-Out Rate to percentage

risk_table["StockOutRate"] = (
    risk_table["StockOutRate"]
    .round(4)
    .mul(100)
    .map(lambda x: f"{x:.2f}%")
)

# LAYOUT

layout = dbc.Container(
    [
        html.H1(
            "Inventory Intelligence",
            className="mb-1"
        ),

        html.P(
            "Inventory levels, stock-out risk and financial performance by category.",
            className="text-muted"
        ),

        html.Br(),

        # KPI CARDS

        dbc.Row(
            [
                dbc.Col(
                    kpi_card(
                        "Average Inventory",
                        f"{total_inventory:,.0f}",
                        "Category Total",
                        "#3498DB"
                    ),

                    xs=12,
                    sm=6,
                    lg=3
                ),

                dbc.Col(
                    kpi_card(
                        "Stock-Out Rate",
                        f"{avg_stockout * 100:.1f}%",
                        "Category Average",
                        stockout_colour
                    ),

                    xs=12,
                    sm=6,
                    lg=3
                ),

                dbc.Col(
                    kpi_card(
                        "Revenue",
                        format_currency(total_revenue),
                        "Inventory Categories",
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
                        "Inventory Categories",
                        profit_colour
                    ),

                    xs=12,
                    sm=6,
                    lg=3
                )
            ],

            className="g-4"
        ),

        html.Br(),

        # INVENTORY LEVELS

        dbc.Card(
            dbc.CardBody(
                dcc.Graph(
                    id="inventory-category-chart",
                    figure=inventory_by_category_chart(
                        inventory
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

        # REVENUE PERFORMANCE

        dbc.Card(
            dbc.CardBody(
                dcc.Graph(
                    id="inventory-revenue-chart",
                    figure=inventory_revenue_chart(
                        inventory
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

        # INVENTORY RISK

        dbc.Card(
            dbc.CardBody(
                [
                    html.H4(
                        "Inventory Risk"
                    ),
                    html.Hr(),
                    dbc.Table.from_dataframe(
                        risk_table,
                        striped=True,
                        hover=True,
                        size="sm",
                        style={
                            "textAlign": "left"
                        }
                    )
                ]
            ),

            className="shadow-sm"
        )
    ],

    fluid=True
)