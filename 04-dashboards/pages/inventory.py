from dash import html, dcc, register_page
import dash_bootstrap_components as dbc

from components.cards import kpi_card

from components.inventory_chart import (
    inventory_by_category_chart,
    inventory_revenue_chart
)

from scripts.data_loader import (
    inventory,
    inventory_summary
)

from scripts.utils import format_currency


register_page(
    __name__,
    path="/inventory",
    name="Inventory"
)


# ==========================================================
# OREY ANALYTICS COLOURS
# ==========================================================

OREY_NAVY = "#061A35"
OREY_BLUE = "#1479D2"
OREY_LIGHT_BLUE = "#48A7F8"
OREY_GREEN = "#2ECC71"
OREY_ORANGE = "#F39C12"
OREY_RED = "#C0392B"
OREY_PURPLE = "#8E44AD"
OREY_GREY = "#7F8C8D"


# ==========================================================
# DATA PREPARATION
# ==========================================================

data = inventory.copy()


data["StockOutRatePercent"] = (
    data["StockOutRate"]
    .astype(float)
    .round(4)
    .mul(100)
)


# ==========================================================
# PORTFOLIO METRICS
# ==========================================================

total_inventory = (
    data["Avg_Inventory"]
    .sum()
)

avg_inventory = (
    data["Avg_Inventory"]
    .mean()
)

avg_stockout = (
    data["StockOutRate"]
    .mean()
)

total_revenue = (
    data["Revenue"]
    .sum()
)

total_profit = (
    data["Profit"]
    .sum()
)


# ==========================================================
# INVENTORY RISK COLOUR
# ==========================================================

if avg_stockout >= 0.05:

    stockout_colour = OREY_RED

elif avg_stockout >= 0.03:

    stockout_colour = OREY_ORANGE

else:

    stockout_colour = OREY_GREEN


# ==========================================================
# PROFIT COLOUR
# ==========================================================

profit_colour = (

    OREY_GREEN

    if total_profit >= 0

    else OREY_RED

)


# ==========================================================
# CATEGORY INTELLIGENCE
# ==========================================================

highest_inventory_category = (

    data.loc[
        data["Avg_Inventory"].idxmax(),
        "Category"
    ]

)

highest_inventory_value = (

    data["Avg_Inventory"].max()

)


highest_stockout_category = (

    data.loc[
        data["StockOutRate"].idxmax(),
        "Category"
    ]

)

highest_stockout_value = (

    data["StockOutRatePercent"].max()

)


highest_revenue_category = (

    data.loc[
        data["Revenue"].idxmax(),
        "Category"
    ]

)

highest_revenue_value = (

    data["Revenue"].max()

)


highest_profit_category = (

    data.loc[
        data["Profit"].idxmax(),
        "Category"
    ]

)

highest_profit_value = (

    data["Profit"].max()

)


# ==========================================================
# INVENTORY RISK TABLE
# ==========================================================

risk_table = inventory_summary[

    [
        "Category",
        "StockOutRate",
        "Inventory_Risk",
        "Revenue"
    ]

].head(10).copy()


risk_table["StockOutRate"] = (

    risk_table["StockOutRate"]
    .astype(float)
    .round(4)
    .mul(100)
    .map(
        lambda x:
        f"{x:.2f}%"
    )

)


risk_table["Revenue"] = (

    risk_table["Revenue"]
    .astype(float)
    .map(
        lambda x:
        f"R {x:,.2f}"
    )

)


# ==========================================================
# RISK BADGE
# ==========================================================

def risk_badge(risk):

    value = str(risk).strip()

    lower = value.lower()

    if lower in [
        "high",
        "high risk",
        "critical"
    ]:

        return dbc.Badge(
            value,
            color="danger",
            className="px-3 py-2"
        )

    elif lower in [
        "moderate",
        "moderate risk",
        "medium"
    ]:

        return dbc.Badge(
            value,
            color="warning",
            text_color="dark",
            className="px-3 py-2"
        )

    else:

        return dbc.Badge(
            value,
            color="success",
            className="px-3 py-2"
        )


# ==========================================================
# BUILD RISK TABLE
# ==========================================================

risk_rows = []


for _, row in risk_table.iterrows():

    risk_rows.append(

        html.Tr(

            [

                html.Td(

                    row["Category"],

                    style={
                        "fontWeight": "600",
                        "color": OREY_NAVY
                    }

                ),

                html.Td(
                    row["StockOutRate"]
                ),

                html.Td(
                    risk_badge(
                        row["Inventory_Risk"]
                    )
                ),

                html.Td(
                    row["Revenue"]
                )

            ]

        )

    )


# ==========================================================
# EXECUTIVE INTERPRETATION
# ==========================================================

if avg_stockout >= 0.05:

    stockout_message = (

        f"Inventory availability requires attention, "
        f"with the portfolio averaging a stock-out rate "
        f"of {avg_stockout * 100:.2f}%. "
        f"{highest_stockout_category} currently records "
        f"the highest stock-out exposure at "
        f"{highest_stockout_value:.2f}%."

    )

elif avg_stockout >= 0.03:

    stockout_message = (

        f"Inventory availability is showing moderate "
        f"pressure, with an average stock-out rate of "
        f"{avg_stockout * 100:.2f}%. "
        f"{highest_stockout_category} has the highest "
        f"category-level exposure at "
        f"{highest_stockout_value:.2f}%."

    )

else:

    stockout_message = (

        f"Inventory availability is currently relatively "
        f"stable, with an average stock-out rate of "
        f"{avg_stockout * 100:.2f}%. "
        f"{highest_stockout_category} remains the category "
        f"with the highest stock-out exposure at "
        f"{highest_stockout_value:.2f}%."

    )


profitability_message = (

    f"{highest_profit_category} is the strongest profit "
    f"contributor, generating approximately "
    f"{format_currency(highest_profit_value)} in profit. "
    f"{highest_revenue_category} is the largest revenue "
    f"category, contributing approximately "
    f"{format_currency(highest_revenue_value)}."

)


inventory_message = (

    f"{highest_inventory_category} carries the highest "
    f"average inventory level at "
    f"{highest_inventory_value:,.0f} units. "
    f"This category should be monitored alongside its "
    f"revenue contribution and stock-out exposure to "
    f"ensure inventory levels remain commercially justified."

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

            "Inventory Intelligence",

            className="mb-1"

        ),

        html.P(

            "Monitoring inventory levels, availability risk "
            "and financial performance across product categories.",

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

                        OREY_BLUE

                    ),

                    xs=12,
                    sm=6,
                    lg=3

                ),

                dbc.Col(

                    kpi_card(

                        "Stock-Out Rate",

                        f"{avg_stockout * 100:.2f}%",

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

                        format_currency(
                            total_revenue
                        ),

                        "Inventory Categories",

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


        # ==================================================
        # INVENTORY INTELLIGENCE
        # ==================================================

        dbc.Card(

            dbc.CardBody(

                [

                    html.H5(

                        "Inventory Intelligence",

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

                                        "Highest Inventory Category",

                                        className="text-muted"

                                    ),

                                    html.Div(

                                        highest_inventory_category,

                                        style={

                                            "fontWeight": "700",

                                            "fontSize": "18px",

                                            "color": OREY_BLUE

                                        }

                                    ),

                                    html.Small(

                                        f"{highest_inventory_value:,.0f} "
                                        "average inventory",

                                        className="text-muted"

                                    )

                                ],

                                xs=12,
                                md=4

                            ),

                            dbc.Col(

                                [

                                    html.Small(

                                        "Highest Stock-Out Exposure",

                                        className="text-muted"

                                    ),

                                    html.Div(

                                        highest_stockout_category,

                                        style={

                                            "fontWeight": "700",

                                            "fontSize": "18px",

                                            "color": OREY_RED

                                        }

                                    ),

                                    html.Small(

                                        f"{highest_stockout_value:.2f}% "
                                        "stock-out rate",

                                        className="text-muted"

                                    )

                                ],

                                xs=12,
                                md=4

                            ),

                            dbc.Col(

                                [

                                    html.Small(

                                        "Strongest Profit Category",

                                        className="text-muted"

                                    ),

                                    html.Div(

                                        highest_profit_category,

                                        style={

                                            "fontWeight": "700",

                                            "fontSize": "18px",

                                            "color": OREY_GREEN

                                        }

                                    ),

                                    html.Small(

                                        format_currency(
                                            highest_profit_value
                                        )
                                        + " profit",

                                        className="text-muted"

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


        # ==================================================
        # INVENTORY + REVENUE CHARTS
        # ==================================================

        dbc.Row(

            [

                dbc.Col(

                    dbc.Card(

                        dbc.CardBody(

                            [

                                dcc.Graph(

                                    id="inventory-category-chart",

                                    figure=(
                                        inventory_by_category_chart(
                                            data
                                        )
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

                    xs=12,
                    lg=6

                ),

                dbc.Col(

                    dbc.Card(

                        dbc.CardBody(

                            [

                                dcc.Graph(

                                    id="inventory-revenue-chart",

                                    figure=(
                                        inventory_revenue_chart(
                                            data
                                        )
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

                    xs=12,
                    lg=6

                )

            ],

            className="g-4"

        ),

        html.Br(),


        # ==================================================
        # INVENTORY RISK POSITION
        # ==================================================

        dbc.Card(

            dbc.CardBody(

                [

                    html.H4(

                        "Inventory Risk Position",

                        className="mb-1",

                        style={

                            "color": OREY_NAVY,

                            "fontWeight": "700"

                        }

                    ),

                    html.P(

                        "Current inventory conditions and the categories requiring the closest management attention.",

                        className="mb-4 fst-italic",

                        style={

                            "color": "#000000"

                        }

                    ),

                    dbc.Row(

                        [

                            dbc.Col(

                                dbc.Card(

                                    dbc.CardBody(

                                        [

                                            html.H6(

                                                "Average Stock-Out Rate",

                                                style={
                                                    "color": OREY_NAVY
                                                }

                                            ),

                                            html.H3(

                                                f"{avg_stockout * 100:.2f}%",

                                                style={
                                                    "color": stockout_colour
                                                }

                                            ),

                                            html.P(

                                                f"Highest category: "
                                                f"{highest_stockout_category}",

                                                className="mb-0",

                                                style={
                                                    "color": "#000000"
                                                }

                                            )

                                        ]

                                    ),

                                    className="border-0 shadow-sm"

                                ),

                                xs=12,
                                md=4

                            ),

                            dbc.Col(

                                dbc.Card(

                                    dbc.CardBody(

                                        [

                                            html.H6(

                                                "Highest Inventory Level",

                                                style={
                                                    "color": OREY_NAVY
                                                }

                                            ),

                                            html.H3(

                                                f"{highest_inventory_value:,.0f}",

                                                style={
                                                    "color": OREY_BLUE
                                                }

                                            ),

                                            html.P(

                                                f"Category: "
                                                f"{highest_inventory_category}",

                                                className="mb-0",

                                                style={
                                                    "color": "#000000"
                                                }

                                            )

                                        ]

                                    ),

                                    className="border-0 shadow-sm"

                                ),

                                xs=12,
                                md=4

                            ),

                            dbc.Col(

                                dbc.Card(

                                    dbc.CardBody(

                                        [

                                            html.H6(

                                                "Strongest Profit Category",

                                                style={
                                                    "color": OREY_NAVY
                                                }

                                            ),

                                            html.H3(

                                                format_currency(
                                                    highest_profit_value
                                                ),

                                                style={
                                                    "color": OREY_GREEN
                                                }

                                            ),

                                            html.P(

                                                f"Category: "
                                                f"{highest_profit_category}",

                                                className="mb-0",

                                                style={
                                                    "color": "#000000"
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


        # ==================================================
        # INVENTORY RISK TABLE
        # ==================================================

        dbc.Card(

            dbc.CardBody(

                [

                    html.H4(

                        "Inventory Risk",

                        className="mb-1",

                        style={

                            "color": OREY_NAVY,

                            "fontWeight": "700"

                        }

                    ),

                    html.P(

                        "Category-level stock-out exposure and financial contribution.",

                        className="mb-3 fst-italic",

                        style={
                            "color": "#000000"
                        }

                    ),

                    dbc.Table(

                        [

                            html.Thead(

                                html.Tr(

                                    [

                                        html.Th(
                                            "Category"
                                        ),

                                        html.Th(
                                            "Stock-Out Rate"
                                        ),

                                        html.Th(
                                            "Inventory Risk"
                                        ),

                                        html.Th(
                                            "Revenue"
                                        )

                                    ]

                                )

                            ),

                            html.Tbody(
                                risk_rows
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


        # ==================================================
        # EXECUTIVE INTERPRETATION
        # ==================================================

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

                        "What the current inventory position suggests for management.",

                        className="mb-4 fst-italic",

                        style={
                            "color": "#000000"
                        }

                    ),

                    dbc.Row(

                        [

                            dbc.Col(

                                dbc.Card(

                                    dbc.CardBody(

                                        [

                                            html.Small(

                                                "INVENTORY AVAILABILITY",

                                                style={

                                                    "fontWeight": "700",

                                                    "color": OREY_RED

                                                }

                                            ),

                                            html.H5(

                                                highest_stockout_category,

                                                className="mt-2 mb-2",

                                                style={

                                                    "fontWeight": "700",

                                                    "color": OREY_NAVY

                                                }

                                            ),

                                            html.P(

                                                stockout_message,

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

                                                "FINANCIAL CONTRIBUTION",

                                                style={

                                                    "fontWeight": "700",

                                                    "color": OREY_GREEN

                                                }

                                            ),

                                            html.H5(

                                                highest_profit_category,

                                                className="mt-2 mb-2",

                                                style={

                                                    "fontWeight": "700",

                                                    "color": OREY_NAVY

                                                }

                                            ),

                                            html.P(

                                                profitability_message,

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

                                                "INVENTORY EFFICIENCY",

                                                style={

                                                    "fontWeight": "700",

                                                    "color": OREY_BLUE

                                                }

                                            ),

                                            html.H5(

                                                highest_inventory_category,

                                                className="mt-2 mb-2",

                                                style={

                                                    "fontWeight": "700",

                                                    "color": OREY_NAVY

                                                }

                                            ),

                                            html.P(

                                                inventory_message,

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

                        stockout_message,

                        className="mb-2",

                        style={
                            "color": "#000000"
                        }

                    ),

                    html.P(

                        profitability_message,

                        className="mb-2",

                        style={
                            "color": "#000000"
                        }

                    ),

                    html.P(

                        inventory_message,

                        className="mb-0",

                        style={
                            "color": "#000000"
                        }

                    )

                ]

            ),

            className="shadow-sm"

        )

    ],

    fluid=True

)