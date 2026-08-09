import plotly.express as px


def segment_revenue_chart(segments):

    fig = px.bar(
        segments.sort_values("Revenue", ascending=True),
        x="Revenue",
        y="CustomerSegment",
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
        title="Revenue by Customer Segment",
        height=360,
        xaxis_title="Revenue (R)",
        yaxis_title="",
        coloraxis_colorbar_title="Profit",
        margin=dict(
            l=20,
            r=50,
            t=70,
            b=20
        )
    )

    return fig


def segment_margin_chart(segments):

    fig = px.bar(
        segments.sort_values("AvgMargin", ascending=True),
        x="AvgMargin",
        y="CustomerSegment",
        orientation="h",
        text="AvgMargin",
        color="ReturnRate",
        template="plotly_white",
        color_continuous_scale="Blues"
    )

    fig.update_traces(
        texttemplate="%{text:.1f}%",
        textposition="outside"
    )

    fig.update_layout(
        title="Customer Segment Margin",
        height=360,
        xaxis_title="Average Margin (%)",
        yaxis_title="",
        coloraxis_colorbar_title="Return Rate",
        margin=dict(
            l=20,
            r=50,
            t=70,
            b=20
        )
    )

    fig.update_xaxes(
        ticksuffix="%"
    )

    return fig
