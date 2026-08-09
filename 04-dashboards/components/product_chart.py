import plotly.express as px

# ==========================================================
# OREY ANALYTICS CATEGORY COLORS
# ==========================================================

CATEGORY_COLORS = {
    "Food": "#173B63",          # Dark Blue
    "Beauty": "#5DADE2",        # Light Blue
    "Clothing": "#6C3483",      # Deep Purple
    "Electronics": "#4A5568",   # Dark Grey
    "Home": "#1E8449"           # Dark Green
}

# ==========================================================
# TOP PRODUCTS CHART
# ==========================================================

def top_products_chart(products):

    # ------------------------------------------------------
    # Select top 10 products by revenue
    # ------------------------------------------------------

    top = (
        products
        .sort_values(
            "Revenue",
            ascending=False
        )
        .head(10)
        .copy()
    )

    # ------------------------------------------------------
    # Create unique Product + Category labels
    # ------------------------------------------------------

    top["Product_Category"] = (
        top["ProductName"]
        + "<br>— "
        + top["Category"]
    )

    # ------------------------------------------------------
    # Create vertical bar chart
    # ------------------------------------------------------

    fig = px.bar(
        top,

        x="Product_Category",

        y="Revenue",

        color="Category",

        text="Revenue",

        color_discrete_map=CATEGORY_COLORS,

        template="plotly_white"
    )

    # ------------------------------------------------------
    # Revenue data labels
    # ------------------------------------------------------

    fig.update_traces(
        texttemplate="R %{text:,.0f}",

        textposition="outside",

        cliponaxis=False,

        marker_line_width=0,

        textfont=dict(

            size=11,

            family="Arial",

            color="#173B63"
        )
    )

    # ------------------------------------------------------
    # Chart layout
    # ------------------------------------------------------

    fig.update_layout(
        title="Top 10 Products by Revenue",

        height=560,

        autosize=True,

        xaxis_title="Product",

        yaxis_title="Revenue (R)",

        legend_title="Category",

        bargap=0.50,

        bargroupgap=0.20,

        margin=dict(
            l=60,

            r=40,

            t=80,

            b=130

        ),

        plot_bgcolor="white",

        paper_bgcolor="white",

        font=dict(
            family="Arial",

            color="#173B63"
        )
    )

    # ------------------------------------------------------
    # X-axis
    # ------------------------------------------------------

    fig.update_xaxes(
        tickangle=0,

        showgrid=False,

        automargin=True,

        tickfont=dict(

            size=11
        ),

        fixedrange=False
    )

    # ------------------------------------------------------
    # Y-axis
    # ------------------------------------------------------

    fig.update_yaxes(
        showgrid=True,

        gridcolor="#E6EEF7",

        zeroline=False,

        automargin=True
    )

    return fig