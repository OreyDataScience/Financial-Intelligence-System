import plotly.express as px

# OREY ANALYTICS COLOURS

OREY_NAVY = "#061A35"
OREY_BLUE = "#1479D2"
OREY_LIGHT_BLUE = "#48A7F8"
OREY_GREEN = "#2ECC71"
OREY_ORANGE = "#F39C12"
OREY_RED = "#C0392B"
OREY_PURPLE = "#8E44AD"
OREY_GREY = "#7F8C8D"

# STORE RISK COLOURS

DISPLAY_RISK_COLOURS = {
    "Reliable": OREY_GREEN,
    "Moderate Risk": OREY_ORANGE,
    "High Risk": OREY_RED
}

# STORE LABEL

def create_store_label(row):

    return (
        f"{row['StoreID']}<br>"
        f"{row['StoreLocation']}"
    )

# NORMALISE RISK VALUES

def normalise_risk(value):

    value = str(value).strip().lower()

    if value in [
        "low",
        "reliable"
    ]:
        return "Reliable"

    elif value in [
        "medium",
        "moderate",
        "moderate risk"
    ]:
        return "Moderate Risk"

    elif value in [
        "high",
        "critical",
        "high risk"
    ]:
        return "High Risk"

    return "High Risk"

# TOP STORES BY REVENUE

def top_stores_chart(stores):

    top = (
        stores
        .sort_values(
            "Revenue",
            ascending=False
        )
        .head(10)
        .copy()
    )

    top["StoreLabel"] = top.apply(
        create_store_label,
        axis=1
    )

    top["Risk_Display"] = (
        top["Store_Risk"]
        .apply(normalise_risk)
    )

    fig = px.bar(
        top,
        x="StoreLabel",
        y="Revenue",
        color="Risk_Display",
        text="Revenue",
        template="plotly_white",
        color_discrete_map=DISPLAY_RISK_COLOURS,
        category_orders={
            "StoreLabel": top[
                "StoreLabel"
            ].tolist(),
            "Risk_Display": [
                "Reliable",
                "Moderate Risk",
                "High Risk"
            ]
        }
    )

    fig.update_traces(
        texttemplate="R %{text:,.0f}",
        textposition="outside",
        textfont=dict(
            size=11
        ),
        hovertemplate=(
            "<b>%{x}</b><br>"
            "Revenue: R %{y:,.2f}"
            "<extra></extra>"
        )
    )

    fig.update_layout(
        title=dict(
            text="Top 10 Stores by Revenue",
            font=dict(
                size=20,
                color=OREY_NAVY
            ),
            x=0
        ),

        height=400,

        font=dict(
            family="Arial",
            color=OREY_NAVY
        ),

        paper_bgcolor="white",
        plot_bgcolor="white",

        xaxis_title="Store",
        yaxis_title="Revenue (R)",

        legend_title="Store Risk",

        margin=dict(
            l=60,
            r=30,
            t=65,
            b=105
        ),

        hovermode="x unified"
    )

    fig.update_xaxes(
        showgrid=False,
        linecolor="#D9E1EA",
        tickangle=0
    )

    fig.update_yaxes(
        gridcolor="#E9EEF5",
        zeroline=False,
        separatethousands=True,
        tickformat="~s"
    )

    return fig

# TOP STORES BY PROFIT

def store_profit_chart(stores):

    top = (
        stores
        .sort_values(
            "Profit",
            ascending=False
        )
        .head(10)
        .copy()
    )

    top["StoreLabel"] = top.apply(
        create_store_label,
        axis=1
    )

    top["Risk_Display"] = (
        top["Store_Risk"]
        .apply(normalise_risk)
    )

    fig = px.bar(
        top,
        x="StoreLabel",
        y="Profit",
        color="Risk_Display",
        text="Profit",
        template="plotly_white",
        color_discrete_map=DISPLAY_RISK_COLOURS,
        category_orders={
            "StoreLabel": top[
                "StoreLabel"
            ].tolist(),
            "Risk_Display": [
                "Reliable",
                "Moderate Risk",
                "High Risk"
            ]
        }
    )

    fig.update_traces(
        texttemplate="R %{text:,.0f}",
        textposition="outside",
        textfont=dict(
            size=11
        ),
        hovertemplate=(
            "<b>%{x}</b><br>"
            "Profit: R %{y:,.2f}"
            "<extra></extra>"
        )
    )

    fig.update_layout(
        title=dict(
            text="Top 10 Stores by Profit",
            font=dict(
                size=20,
                color=OREY_NAVY
            ),
            x=0
        ),

        height=400,
        font=dict(
            family="Arial",
            color=OREY_NAVY
        ),

        paper_bgcolor="white",
        plot_bgcolor="white",
        xaxis_title="Store",
        yaxis_title="Profit (R)",
        legend_title="Store Risk",
        margin=dict(
            l=60,
            r=30,
            t=65,
            b=105
        ),

        hovermode="x unified"
    )

    fig.update_xaxes(
        showgrid=False,
        linecolor="#D9E1EA",
        tickangle=0
    )

    fig.update_yaxes(
        gridcolor="#E9EEF5",
        zeroline=False,
        separatethousands=True,
        tickformat="~s"
    )

    return fig

# REVENUE SHARE BY STORE LOCATION

def store_revenue_share_chart(stores):

    revenue_by_location = (
        stores
        .groupby(
            "StoreLocation",
            as_index=False
        )["Revenue"]
        .sum()
        .sort_values(
            "Revenue",
            ascending=False
        )
    )

    LOCATION_COLOURS = [
        OREY_NAVY,
        OREY_LIGHT_BLUE,
        "#5B6573"
    ]

    fig = px.pie(
        revenue_by_location,
        names="StoreLocation",
        values="Revenue",
        title="Revenue Share by Store Location",
        hole=0.45,
        template="plotly_white",
        color_discrete_sequence=LOCATION_COLOURS
    )

    fig.update_traces(
        textposition="outside",
        texttemplate="%{percent:.1%}",
        textfont=dict(
            size=11
        ),

        hovertemplate=(
            "<b>%{label}</b><br>"
            "Revenue: R %{value:,.2f}<br>"
            "Revenue Share: %{percent:.1%}"
            "<extra></extra>"
        )
    )

    fig.update_layout(
        height=320,

        font=dict(
            family="Arial",
            color=OREY_NAVY
        ),

        paper_bgcolor="white",
        plot_bgcolor="white",

        title=dict(
            text="Revenue Share by Store Location",
            font=dict(
                size=20,
                color=OREY_NAVY
            ),
            x=0
        ),

        legend_title_text="",

        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.12,
            xanchor="center",
            x=0.5,
            font=dict(
                size=10
            )
        ),

        margin=dict(
            l=20,
            r=20,
            t=70,
            b=75
        ),

        uniformtext=dict(
            minsize=9,
            mode="hide"
        )
    )

    return fig