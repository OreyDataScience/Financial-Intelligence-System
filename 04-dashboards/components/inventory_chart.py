import pandas as pd
import plotly.express as px

# OREY ANALYTICS COLOUR PALETTE

OREY_NAVY = "#061A35"
OREY_BLUE = "#1479D2"
OREY_LIGHT_BLUE = "#48A7F8"
OREY_GREEN = "#2ECC71"
OREY_ORANGE = "#F39C12"
OREY_RED = "#C0392B"
OREY_PURPLE = "#8E44AD"
OREY_GREY = "#7F8C8D"
OREY_LIGHT_GREY = "#E9EEF5"

# COMMON CHART LAYOUT

def apply_inventory_layout(
    fig,
    height=360,
    title=None,
    xaxis_title=None,
    yaxis_title=None
):

    fig.update_layout(
        template="plotly_white",
        height=height,
        title=dict(
            text=title if title else "",
            font=dict(
                size=20,
                color=OREY_NAVY
            ),
            x=0
        ),

        font=dict(
            family="Arial",
            color=OREY_NAVY
        ),

        paper_bgcolor="white",
        plot_bgcolor="white",
        margin=dict(
            l=55,
            r=30,
            t=70,
            b=60
        ),

        hovermode="closest",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0
        )
    )

    fig.update_xaxes(
        title=xaxis_title,
        showgrid=False,
        linecolor="#D9E1EA",
        tickfont=dict(
            size=11
        )
    )

    fig.update_yaxes(
        title=yaxis_title,
        gridcolor=OREY_LIGHT_GREY,
        zeroline=False,
        title_font=dict(
            size=12
        ),

        tickfont=dict(
            size=11
        )
    )

    return fig

# AVERAGE INVENTORY BY CATEGORY

def inventory_by_category_chart(inventory):

    data = (
        inventory
        .groupby(
            "Category",
            as_index=False
        )

        .agg(
            Avg_Inventory=(
                "Avg_Inventory",
                "mean"
            ),

            StockOutRate=(
                "StockOutRate",
                "mean"
            ),

            Revenue=(
                "Revenue",
                "sum"
            ),

            Profit=(
                "Profit",
                "sum"
            )
        )

        .sort_values(
            "Avg_Inventory",
            ascending=True
        )
    )

    data["StockOutRatePercent"] = (
        data["StockOutRate"] * 100
    )

    fig = px.bar(
        data,
        x="Category",
        y="Avg_Inventory",
        text="Avg_Inventory",
        color="Category",
        template="plotly_white",

        color_discrete_sequence=[
            OREY_BLUE,
            OREY_LIGHT_BLUE,
            OREY_PURPLE,
            OREY_GREY,
            OREY_GREEN
        ],

        hover_data={
            "Avg_Inventory": ":,.0f",
            "StockOutRatePercent": ":.2f",
            "Revenue": ":,.0f",
            "Profit": ":,.0f"
        }
    )

    fig.update_traces(
        texttemplate="%{text:,.0f}",
        textposition="outside",
        textfont=dict(
            size=12
        ),

        marker_line_width=0,
        hovertemplate=(
            "<b>%{x}</b><br>"

            "Average Inventory: %{y:,.0f}<br>"

            "Stock-Out Rate: "
            "%{customdata[1]:.2f}%<br>"

            "Revenue: R %{customdata[2]:,.0f}<br>"

            "Profit: R %{customdata[3]:,.0f}"

            "<extra></extra>"
        )
    )

    apply_inventory_layout(
        fig,
        height=390,
        title="Average Inventory by Category",
        xaxis_title="Category",
        yaxis_title="Average Inventory"
    )

    fig.update_layout(
        showlegend=False
    )

    return fig

# REVENUE BY CATEGORY — RANKED BY PROFIT

def inventory_revenue_chart(inventory):

    data = (
        inventory

        .groupby(
            "Category",
            as_index=False
        )

        .agg(
            Revenue=(
                "Revenue",
                "sum"
            ),

            Profit=(
                "Profit",
                "sum"
            ),

            Avg_Inventory=(
                "Avg_Inventory",
                "mean"
            ),

            StockOutRate=(
                "StockOutRate",
                "mean"
            )

        )

        .sort_values(
            "Profit",
            ascending=True
        )
    )

    data["StockOutRatePercent"] = (
        data["StockOutRate"] * 100
    )

    fig = px.bar(
        data,
        x="Category",
        y="Revenue",
        color="Category",
        text="Revenue",
        template="plotly_white",

        color_discrete_sequence=[
            OREY_BLUE,
            OREY_LIGHT_BLUE,
            OREY_PURPLE,
            OREY_GREY,
            OREY_GREEN
        ],

        hover_data={
            "Revenue": ":,.0f",
            "Profit": ":,.0f",
            "Avg_Inventory": ":,.0f",
            "StockOutRatePercent": ":.2f"
        }
    )

    fig.update_traces(
        texttemplate="R %{text:,.0f}",
        textposition="outside",
        textfont=dict(
            size=12
        ),

        marker_line_width=0,
        hovertemplate=(
            "<b>%{x}</b><br>"

            "Revenue: R %{y:,.0f}<br>"

            "Profit: R %{customdata[1]:,.0f}<br>"

            "Average Inventory: "
            "%{customdata[2]:,.0f}<br>"

            "Stock-Out Rate: "
            "%{customdata[3]:.2f}%"

            "<extra></extra>"
        )
    )

    apply_inventory_layout(
        fig,
        height=390,
        title="Revenue by Category — Ranked by Profit",
        xaxis_title="Category",
        yaxis_title="Revenue (R)"
    )

    fig.update_layout(
        showlegend=False
    )

    return fig