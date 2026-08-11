import plotly.express as px

# OREY ANALYTICS CATEGORY COLOURS

CATEGORY_COLORS = {
    "Food": "#173B63",
    "Beauty": "#5DADE2",
    "Clothing": "#6C3483",
    "Electronics": "#4A5568",
    "Home": "#1E8449"
}

# TOP PRODUCTS CHART

def top_products_chart(products):

    # TOP 10 PRODUCTS BY REVENUE

    top = (
        products
        .sort_values(
            "Revenue",
            ascending=False
        )
        .head(10)
        .copy()
    )

    # PRODUCT LABEL

    top["Product_Category"] = (
        top["ProductName"]
        + "<br>— "
        + top["Category"]
    )

    # CHART

    fig = px.bar(
        top,
        x="Product_Category",
        y="Revenue",
        color="Category",
        text="Revenue",
        color_discrete_map=CATEGORY_COLORS,
        template="plotly_white"
    )

    # DATA LABELS

    fig.update_traces(
        texttemplate="R %{text:,.0f}",
        textposition="outside",
        cliponaxis=False,

        textfont=dict(
            size=11,
            family="Arial",
            color="#173B63"
        ),

        marker_line_width=0,

        hovertemplate=(
            "<b>%{x}</b><br>"
            "Revenue: R %{y:,.2f}"
            "<extra></extra>"
        )
    )

    # LAYOUT

    fig.update_layout(

        title=dict(
            text="Top 10 Products by Revenue",
            font=dict(
                size=20,
                color="#061A35"
            ),
            x=0
        ),

        height=480,
        autosize=True,
        xaxis_title="Product",
        yaxis_title="Revenue (R)",
        legend_title="Category",
        bargap=0.35,
        bargroupgap=0.15,
        margin=dict(
            l=60,
            r=40,
            t=75,
            b=125
        ),

        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(
            family="Arial",
            color="#061A35"
        ),

        hovermode="x unified"
    )

    # X AXIS

    fig.update_xaxes(
        tickangle=0,
        showgrid=False,
        automargin=True,
        tickfont=dict(
            size=10
        ),

        fixedrange=False,
        linecolor="#D9E1EA"
    )

    # Y AXIS

    fig.update_yaxes(
        showgrid=True,
        gridcolor="#E6EEF7",
        zeroline=False,
        automargin=True,
        separatethousands=True,
        tickformat="~s"
    )

    return fig