from dash import html, dcc, register_page
import dash_bootstrap_components as dbc

from components.cards import kpi_card

from components.supplier_chart import (
    supplier_risk_matrix_chart,
    supplier_lowest_lead_time_chart,
    supplier_highest_lead_time_chart,
    supplier_risk_distribution_chart,
    supplier_lead_time_by_risk_chart,
    top_attention_suppliers
)

from scripts.data_loader import suppliers
from scripts.utils import format_currency

register_page(
    __name__,
    path="/suppliers",
    name="Suppliers"
)

# METRICS

total_revenue = suppliers["Revenue"].sum()

avg_lead_time = suppliers["Avg_LeadTime"].mean()

avg_stockout = suppliers["StockOutRate"].mean()

high_risk_count = suppliers[
    suppliers["Supplier_Risk"].astype(str).str.lower().isin(
        [
            "high risk",
            "critical",
            "high"
        ]
    )
].shape[0]

# TOP 10 SUPPLIERS REQUIRING MOST ATTENTION

attention_suppliers = top_attention_suppliers(
    suppliers,
    n=10
)

# LAYOUT

layout = dbc.Container(
    [
        # PAGE HEADER

        html.H1(
            "Supplier Risk",
            className="mb-1"
        ),

        html.P(
            "Supplier reliability, lead times and operational risk.",
            className="text-muted"
        ),

        html.Br(),

        # KPI CARDS

        dbc.Row(
            [
                dbc.Col(
                    kpi_card(
                        "Supplier Revenue",
                        format_currency(total_revenue),
                        "Portfolio",
                        "#0B6E4F"
                    ),

                    xs=12,
                    sm=6,
                    lg=3

                ),

                dbc.Col(
                    kpi_card(
                        "Avg Lead Time",
                        f"{avg_lead_time:.2f} days",
                        "Supplier Average",
                        "#2E86DE"
                    ),

                    xs=12,
                    sm=6,
                    lg=3

                ),

                dbc.Col(
                    kpi_card(
                        "Stock-Out Rate",
                        f"{avg_stockout * 100:.2f}%",
                        "Supplier Average",
                        "#F39C12"
                    ),

                    xs=12,
                    sm=6,
                    lg=3
                ),

                dbc.Col(
                    kpi_card(
                        "High-Risk Suppliers",
                        f"{high_risk_count}",
                        "High Risk / Critical",
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

        # SUPPLIER LEAD TIMES

        dbc.Row(
            [
                # LOWEST LEAD TIMES

                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.H5(
                                    "Supplier Lead Time",
                                    className="mb-0",
                                    style={
                                        "color": "#000000"
                                    }
                                ),

                                html.P(
                                    "Lowest lead times",
                                    className="mb-2 fst-italic",
                                    style={
                                        "color": "#000000"
                                    }
                                ),

                                dcc.Graph(

                                    id="supplier-lowest-lead-time-chart",
                                    figure=supplier_lowest_lead_time_chart(
                                        suppliers
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

                # HIGHEST LEAD TIMES

                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.H5(
                                    "Supplier Lead Time",
                                    className="mb-0",
                                    style={
                                        "color": "#000000"
                                    }
                                ),

                                html.P(
                                    "Highest lead times",
                                    className="mb-2 fst-italic",
                                    style={
                                        "color": "#000000"
                                    }
                                ),

                                dcc.Graph(

                                    id="supplier-highest-lead-time-chart",
                                    figure=supplier_highest_lead_time_chart(
                                        suppliers
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

        # SUPPLIER RISK MATRIX

        dbc.Card(
            dbc.CardBody(
                dcc.Graph(
                    id="supplier-risk-matrix-chart",
                    figure=supplier_risk_matrix_chart(
                        suppliers
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

        # SUPPLIER RISK SUMMARY

        dbc.Card(
            dbc.CardBody(
                [
                    html.H4(
                        "Supplier Risk Summary",
                        className="mb-1",
                        style={
                            "color": "#000000"
                        }
                    ),

                    html.P(
                        "Current supplier portfolio indicators",
                        className="mb-4",
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
                                                "High-Risk Suppliers",
                                                style={
                                                    "color": "#000000"
                                                }
                                            ),

                                            html.H3(
                                                f"{high_risk_count}",
                                                style={
                                                    "color": "#C0392B"
                                                }
                                            ),

                                            html.P(
                                                "Suppliers classified as High Risk or Critical.",
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
                                                "Average Lead Time",
                                                style={
                                                    "color": "#000000"
                                                }
                                            ),

                                            html.H3(
                                                f"{avg_lead_time:.2f} days",
                                                style={
                                                    "color": "#0B4F92"
                                                }
                                            ),

                                            html.P(
                                                "Average number of days suppliers take to deliver.",
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
                                                "Average Stock-Out Rate",
                                                style={
                                                    "color": "#000000"
                                                }
                                            ),

                                            html.H3(
                                                f"{avg_stockout * 100:.2f}%",
                                                style={
                                                    "color": "#F39C12"
                                                }
                                            ),

                                            html.P(
                                                "Average supplier stock-out rate across the portfolio.",
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

        # TOP 10 SUPPLIERS REQUIRING MOST ATTENTION

        dbc.Card(
            dbc.CardBody(
                [
                    html.H4(
                        "Supplier Attention Intelligence",
                        className="mb-1",
                        style={
                            "color": "#000000"
                        }
                    ),

                    html.P(
                        "Top 10 suppliers requiring the most operational attention based on risk, stock-out exposure, lead time and operational concern.",
                        className="mb-3 fst-italic",
                        style={
                            "color": "#000000"
                        }
                    ),

                    dbc.Table.from_dataframe(
                        attention_suppliers[
                            [
                                "SupplierID",
                                "Attention_Score",
                                "Operational_Concern",
                                "Avg_LeadTime",
                                "StockOutRate",
                                "Supplier_Risk"
                            ]
                        ]
                        .assign(
                            Attention_Score=lambda df:
                                df["Attention_Score"].map(
                                    lambda x: f"{x:.1f}/100"
                                ),

                            Avg_LeadTime=lambda df:
                                df["Avg_LeadTime"]
                                .round(2)
                                .map(
                                    lambda x:
                                    f"{x:.2f} days"
                                ),

                            StockOutRate=lambda df:
                                df["StockOutRate"]
                                .round(4)
                                .mul(100)
                                .map(
                                    lambda x:
                                    f"{x:.2f}%"
                                )
                        ),

                        striped=True,
                        hover=True,
                        bordered=False,
                        size="sm",
                        responsive=True
                    )
                ]
            ),

            className="shadow-sm"
        ),

        html.Br(),

        # BOTTOM RISK INTELLIGENCE

        dbc.Row(
            [
                # SUPPLIER RISK DISTRIBUTION

                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            dcc.Graph(
                                id="supplier-risk-distribution-chart",
                                figure=supplier_risk_distribution_chart(
                                    suppliers
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

                # AVERAGE LEAD TIME BY RISK

                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            dcc.Graph(
                                id="supplier-lead-time-by-risk-chart",

                                figure=supplier_lead_time_by_risk_chart(
                                    suppliers
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
        )
    ],

    fluid=True
)