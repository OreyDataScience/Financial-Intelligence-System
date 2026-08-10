import plotly.express as px


# ==========================================================
# OREY ANALYTICS CATEGORY COLOURS
# ==========================================================

CATEGORY_COLOURS = [
    "#0B4F92",  # Dark Blue
    "#48A7F8",  # Light Blue
    "#5B2C83",  # Deep Purple
    "#5B6573",  # Dark Grey
    "#176B4D"   # Dark Green
]


# ==========================================================
# AVERAGE INVENTORY BY CATEGORY
# ==========================================================

def inventory_by_category_chart(inventory):

    category_inventory = (
        inventory
        .groupby(
            "Category",
            as_index=False
        )["Avg_Inventory"]
        .mean()
        .sort_values(
            "Avg_Inventory",
            ascending=False
        )
    )

    fig = px.bar(

        category_inventory,

        x="Category",

        y="Avg_Inventory",

        color="Category",

        text="Avg_Inventory",

        template="plotly_white",

        color_discrete_sequence=CATEGORY_COLOURS,

        category_orders={
            "Category": category_inventory["Category"].tolist()
        }

    )

    # ======================================================
    # DATA LABELS
    # ======================================================

    fig.update_traces(

        texttemplate="%{text:,.0f}",

        textposition="outside",

        textfont=dict(
            size=12
        )

    )

    # ======================================================
    # LAYOUT
    # ======================================================

    fig.update_layout(

        title="Average Inventory by Category",

        height=430,

        xaxis_title="Category",

        yaxis_title="Average Inventory",

        showlegend=False,

        margin=dict(

            l=60,

            r=40,

            t=70,

            b=80

        ),

        xaxis=dict(

            tickangle=0,

            categoryorder="array",

            categoryarray=category_inventory[
                "Category"
            ].tolist()

        ),

        yaxis=dict(

            range=[0, 1200],

            tickmode="linear",

            tick0=0,

            dtick=200,

            separatethousands=True

        )

    )

    return fig


# ==========================================================
# REVENUE BY CATEGORY
# RANKED BY PROFIT
# ==========================================================

def inventory_revenue_chart(inventory):

    category_performance = (
        inventory
        .groupby(
            "Category",
            as_index=False
        )
        .agg(
            Revenue=("Revenue", "sum"),
            Profit=("Profit", "sum")
        )
        .sort_values(
            "Profit",
            ascending=False
        )
    )

    fig = px.bar(

        category_performance,

        x="Category",

        y="Revenue",

        color="Category",

        text="Revenue",

        template="plotly_white",

        color_discrete_sequence=CATEGORY_COLOURS,

        category_orders={
            "Category": category_performance[
                "Category"
            ].tolist()
        },

        custom_data=["Profit"]

    )

    # ======================================================
    # DATA LABELS
    # ======================================================

    fig.update_traces(

        texttemplate="R %{text:,.0f}",

        textposition="outside",

        textfont=dict(
            size=12
        ),

        hovertemplate=(
            "<b>%{x}</b><br>"
            "Revenue: R %{y:,.2f}<br>"
            "Profit: R %{customdata[0]:,.2f}"
            "<extra></extra>"
        )

    )

    # ======================================================
    # LAYOUT
    # ======================================================

    fig.update_layout(

        title="Revenue by Category — Ranked by Profit",

        height=430,

        xaxis_title="Category",

        yaxis_title="Revenue (R)",

        showlegend=False,

        margin=dict(

            l=60,

            r=40,

            t=70,

            b=80

        ),

        xaxis=dict(

            tickangle=0,

            categoryorder="array",

            categoryarray=category_performance[
                "Category"
            ].tolist()

        ),

        yaxis=dict(

            separatethousands=True

        )

    )

    return fig