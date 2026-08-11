import plotly.express as px


def channel_revenue_chart(channels):

    fig = px.bar(
        channels.sort_values("Revenue", ascending=True),
        x="Revenue",
        y="SalesChannel",
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
        title="Revenue by Sales Channel",
        height=360,
        xaxis_title="Revenue (R)",
        yaxis_title="",
        coloraxis_colorbar_title="Profit",
        margin=dict(
            l=20,
            r=60,
            t=70,
            b=20
        )
    )

    return fig


def channel_share_chart(channels):

    fig = px.pie(
        channels,
        names="SalesChannel",
        values="Revenue_Share",
        hole=0.55,
        template="plotly_white",
        color_discrete_sequence=["#1479D2", "#48A7F8", "#0B4F92", "#8CC9FF", "#2467A5"]
    )

    fig.update_traces(
        textposition="inside",
        texttemplate="%{percent}"
    )

    fig.update_layout(
        title="Revenue Share by Sales Channel",
        height=360,
        margin=dict(
            l=20,
            r=20,
            t=70,
            b=20
        )
    )

    return fig