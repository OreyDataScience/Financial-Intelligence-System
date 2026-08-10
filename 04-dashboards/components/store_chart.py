import plotly.express as px

# STORE RISK COLOURS

RISK_COLOURS = {
    "Reliable": "#2ECC71",
    "Moderate Risk": "#F39C12",
    "High Risk": "#C0392B",
    "Critical": "#C0392B"
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

    if value in ["low", "reliable"]:
        return "Reliable"

    elif value in ["medium", "moderate", "moderate risk"]:
        return "Moderate Risk"

    elif value in ["high", "critical", "high risk"]:
        return "High Risk"

    else:
        return "High Risk"

# DISPLAY RISK COLOURS

DISPLAY_RISK_COLOURS = {
    "Reliable": "#2ECC71",
    "Moderate Risk": "#F39C12",
    "High Risk": "#C0392B"
}

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

    top["Risk_Display"] = top["Store_Risk"].apply(
        normalise_risk
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
            "StoreLabel": top["StoreLabel"].tolist(),
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
            size=12
        )
    )

    fig.update_layout(
        title="Top 10 Stores by Revenue",
        height=430,
        xaxis_title="Store",
        yaxis_title="Revenue (R)",
        legend_title="Store Risk",
        margin=dict(
            l=60,
            r=40,
            t=70,
            b=110
        ),
        xaxis=dict(
            tickangle=0,
            tickmode="array",
            tickvals=top["StoreLabel"].tolist(),
            ticktext=top["StoreLabel"].tolist(),
            categoryorder="array",
            categoryarray=top["StoreLabel"].tolist()
        ),
        yaxis=dict(
            range=[0, 2500000],
            tickmode="array",
            tickvals=[
                0,
                250000,
                500000,
                750000,
                1000000,
                1250000,
                1500000,
                1750000,
                2000000,
                2250000,
                2500000
            ],
            ticktext=[
                "0",
                "250K",
                "500K",
                "750K",
                "1M",
                "1.25M",
                "1.5M",
                "1.75M",
                "2M",
                "2.25M",
                "2.5M"
            ],
            separatethousands=True
        )
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

    top["Risk_Display"] = top["Store_Risk"].apply(
        normalise_risk
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
            "StoreLabel": top["StoreLabel"].tolist(),
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
            size=12
        )
    )

    fig.update_layout(
        title="Top 10 Stores by Profit",
        height=430,
        xaxis_title="Store",
        yaxis_title="Profit (R)",
        legend_title="Store Risk",
        margin=dict(
            l=60,
            r=40,
            t=70,
            b=110
        ),
        xaxis=dict(
            tickangle=0,
            tickmode="array",
            tickvals=top["StoreLabel"].tolist(),
            ticktext=top["StoreLabel"].tolist(),
            categoryorder="array",
            categoryarray=top["StoreLabel"].tolist()
        ),
        yaxis=dict(
            range=[0, 700000],
            tickmode="array",
            tickvals=[
                0,
                100000,
                200000,
                300000,
                400000,
                500000,
                600000,
                700000
            ],
            ticktext=[
                "0",
                "100K",
                "200K",
                "300K",
                "400K",
                "500K",
                "600K",
                "700K"
            ],
            separatethousands=True
        )
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

    # OREY ANALYTICS LOCATION COLOURS

    LOCATION_COLOURS = [
        "#0B4F92",  # Dark Blue
        "#48A7F8",  # Light Blue
        "#5B6573"   # Grey
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

    # OUTSIDE PERCENTAGE LABELS

    fig.update_traces(
        textposition="outside",
        texttemplate="%{percent:.1%}",
        textfont=dict(
            size=11
        ),

        hovertemplate=(
            "<b>%{label}</b><br>"
            "Revenue: R %{value:,.0f}<br>"
            "Revenue Share: %{percent}"
            "<extra></extra>"
        )
    )

    # LAYOUT

    fig.update_layout(
        height=300,

        # Remove Plotly legend title
        legend_title_text="",

        # Legend underneath the chart
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

        # Separate heading above the legend
        annotations=[
            dict(
                text="<b>Store Location</b>",
                x=0.5,
                y=-0.05,
                xref="paper",
                yref="paper",
                showarrow=False,
                xanchor="center",
                yanchor="top",
                font=dict(
                    size=11
                )
            )
        ],

        uniformtext=dict(
            minsize=9,
            mode="hide"
        )
    )

    return fig