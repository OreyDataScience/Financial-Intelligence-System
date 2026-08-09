import plotly.express as px

OREY_SEQUENCE = ["#1479D2", "#48A7F8", "#0B4F92", "#8CC9FF", "#2467A5"]
RISK_COLOURS = {"Low": "#3AA981", "Medium": "#F2B84B", "High": "#E97A4A", "Critical": "#D84D5A"}


def executive_top_products_chart(products):

    data = (
        products
        .sort_values("Revenue", ascending=True)
        .head(10)
    )

    fig = px.bar(
        data,
        x="Revenue",
        y="ProductName",
        orientation="h",
        color="Category",
        text="Revenue",
        template="plotly_white",
        color_discrete_sequence=OREY_SEQUENCE
    )

    fig.update_traces(
        texttemplate="R %{text:,.0f}",
        textposition="outside"
    )

    fig.update_layout(
        title="Top Products",
        height=300,
        xaxis_title="Revenue (R)",
        yaxis_title="",
        margin=dict(
            l=20,
            r=70,
            t=52,
            b=20
        )
    )

    return fig


def executive_top_stores_chart(stores):

    data = (
        stores
        .sort_values("Revenue", ascending=True)
        .head(10)
    )

    fig = px.bar(
        data,
        x="Revenue",
        y="StoreLocation",
        orientation="h",
        color="Store_Risk",
        text="Revenue",
        template="plotly_white",
        color_discrete_map=RISK_COLOURS
    )

    fig.update_traces(
        texttemplate="R %{text:,.0f}",
        textposition="outside"
    )

    fig.update_layout(
        title="Top Stores",
        height=300,
        xaxis_title="Revenue (R)",
        yaxis_title="",
        margin=dict(
            l=20,
            r=70,
            t=52,
            b=20
        )
    )

    return fig


def executive_channel_chart(channels):

    data = channels.sort_values(
        "Revenue",
        ascending=True
    )

    fig = px.bar(
        data,
        x="Revenue",
        y="SalesChannel",
        orientation="h",
        text="Revenue",
        template="plotly_white",
        color_discrete_sequence=OREY_SEQUENCE
    )

    fig.update_traces(
        texttemplate="R %{text:,.0f}",
        textposition="outside"
    )

    fig.update_layout(
        title="Revenue by Sales Channel",
        height=280,
        xaxis_title="Revenue (R)",
        yaxis_title="",
        margin=dict(
            l=20,
            r=70,
            t=52,
            b=20
        )
    )

    return fig
