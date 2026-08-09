import plotly.express as px

RISK_COLOURS = {"Low": "#3AA981", "Medium": "#F2B84B", "High": "#E97A4A", "Critical": "#D84D5A"}


def top_stores_chart(stores):

    top = (
        stores
        .sort_values("Revenue", ascending=False)
        .head(10)
    )

    fig = px.bar(
        top,
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
        title="Top 10 Stores by Revenue",
        height=360,
        xaxis_title="Revenue (R)",
        yaxis_title="",
        legend_title="Store Risk",
        margin=dict(
            l=20,
            r=80,
            t=70,
            b=20
        )
    )

    fig.update_yaxes(
        categoryorder="total ascending"
    )

    return fig


def store_profit_chart(stores):

    top = (
        stores
        .sort_values("Profit", ascending=False)
        .head(10)
    )

    fig = px.bar(
        top,
        x="Profit",
        y="StoreLocation",
        orientation="h",
        color="Store_Risk",
        text="Profit",
        template="plotly_white",
        color_discrete_map=RISK_COLOURS
    )

    fig.update_traces(
        texttemplate="R %{text:,.0f}",
        textposition="outside"
    )

    fig.update_layout(
        title="Top 10 Stores by Profit",
        height=360,
        xaxis_title="Profit (R)",
        yaxis_title="",
        legend_title="Store Risk",
        margin=dict(
            l=20,
            r=80,
            t=70,
            b=20
        )
    )

    fig.update_yaxes(
        categoryorder="total ascending"
    )

    return fig
