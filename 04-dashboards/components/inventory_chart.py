import plotly.express as px


def inventory_by_category_chart(inventory):

    fig = px.bar(
        inventory.sort_values("Avg_Inventory", ascending=True),
        x="Avg_Inventory",
        y="Category",
        orientation="h",
        text="Avg_Inventory",
        color="StockOutRate",
        color_continuous_scale="Blues",
        template="plotly_white"
    )

    fig.update_traces(
        texttemplate="%{text:,.0f}",
        textposition="outside"
    )

    fig.update_layout(
        title="Average Inventory by Category",
        height=360,
        xaxis_title="Average Inventory",
        yaxis_title="",
        coloraxis_colorbar_title="Stock-Out Rate",
        margin=dict(
            l=20,
            r=40,
            t=70,
            b=20
        )
    )

    return fig


def inventory_revenue_chart(inventory):

    fig = px.bar(
        inventory.sort_values("Revenue", ascending=True),
        x="Revenue",
        y="Category",
        orientation="h",
        text="Revenue",
        color="Profit",
        template="plotly_white",
        color_continuous_scale="Blues"
    )

    fig.update_traces(
        texttemplate="R %{text:,.0f}",
        textposition="outside"
    )

    fig.update_layout(
        title="Revenue by Inventory Category",
        height=360,
        xaxis_title="Revenue (R)",
        yaxis_title="",
        coloraxis_colorbar_title="Profit",
        margin=dict(
            l=20,
            r=40,
            t=70,
            b=20
        )
    )

    return fig
