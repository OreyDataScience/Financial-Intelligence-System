import plotly.express as px

RISK_COLOURS = {"Low": "#3AA981", "Medium": "#F2B84B", "High": "#E97A4A", "Critical": "#D84D5A"}


def supplier_risk_chart(suppliers):

    risk_order = ["Low", "Medium", "High", "Critical"]

    suppliers = suppliers.copy()

    if "Supplier_Risk" in suppliers.columns:
        suppliers["Supplier_Risk"] = suppliers["Supplier_Risk"].astype(str)

    fig = px.bar(
        suppliers.sort_values("StockOutRate", ascending=True),
        x="StockOutRate",
        y="SupplierID",
        orientation="h",
        color="Supplier_Risk",
        text="StockOutRate",
        category_orders={
            "Supplier_Risk": risk_order
        },
        template="plotly_white",
        color_discrete_map=RISK_COLOURS
    )

    fig.update_traces(
        texttemplate="%{text:.1%}",
        textposition="outside"
    )

    fig.update_layout(
        title="Supplier Stock-Out Risk",
        height=360,
        xaxis_title="Stock-Out Rate",
        yaxis_title="Supplier",
        legend_title="Supplier Risk",
        margin=dict(
            l=20,
            r=80,
            t=70,
            b=20
        )
    )

    fig.update_xaxes(
        tickformat=".0%"
    )

    return fig


def supplier_lead_time_chart(suppliers):

    fig = px.bar(
        suppliers.sort_values("Avg_LeadTime", ascending=True),
        x="Avg_LeadTime",
        y="SupplierID",
        orientation="h",
        color="Supplier_Risk",
        text="Avg_LeadTime",
        template="plotly_white",
        color_discrete_map=RISK_COLOURS
    )

    fig.update_traces(
        texttemplate="%{text:.1f}",
        textposition="outside"
    )

    fig.update_layout(
        title="Supplier Average Lead Time",
        height=360,
        xaxis_title="Average Lead Time",
        yaxis_title="Supplier",
        legend_title="Supplier Risk",
        margin=dict(
            l=20,
            r=80,
            t=70,
            b=20
        )
    )

    return fig
