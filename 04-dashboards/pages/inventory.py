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


# ==========================================================
# METRICS
# ==========================================================

total_inventory = inventory["Avg_Inventory"].sum()

avg_stockout = inventory["StockOutRate"].mean()

total_revenue = inventory["Revenue"].sum()

total_profit = inventory["Profit"].sum()


# ==========================================================
# LAYOUT
# ==========================================================

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

        # ==================================================
        # KPI CARDS
        # ==================================================

        dbc.Row(

            [

                dbc.Col(

                    kpi_card(
                        "Average Inventory",
                        f"{total_inventory:,.0f}",
                        "Category Total",
                        "#0B6E4F"
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
                        "#C0392B"
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
                        "#2E86DE"
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
                        "#8E44AD"
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
        # INVENTORY LEVELS
        # ==================================================

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

        # ==================================================
        # REVENUE PERFORMANCE
        # ==================================================

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
        dbc.Card(dbc.CardBody([html.H4("Inventory Risk"), html.Hr(), dbc.Table.from_dataframe(inventory_summary[["Category", "StockOutRate", "Inventory_Risk", "Revenue"]].head(10), striped=True, hover=True, size="sm")]), className="shadow-sm")

    ],

    fluid=True

)
