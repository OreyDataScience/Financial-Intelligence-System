import plotly.graph_objects as go


def revenue_chart(monthly, forecast):

    fig = go.Figure()

    # Historical Revenue
    fig.add_trace(

        go.Scatter(

            x=monthly["Month"],
            y=monthly["Revenue"],

            mode="lines+markers",

            name="Revenue",

            line=dict(
                color="#0B6E4F",
                width=4
            ),

            marker=dict(size=8),

            hovertemplate="<b>%{x}</b><br>Revenue: R %{y:,.0f}<extra></extra>"

        )

    )

    # Forecast
    fig.add_trace(

        go.Scatter(

            x=forecast["Month"],
            y=forecast["Revenue_Forecast"],

            mode="lines",

            name="Forecast",

            line=dict(
                color="#3498DB",
                width=4,
                dash="dash"
            ),

            hovertemplate="<b>%{x}</b><br>Forecast: R %{y:,.0f}<extra></extra>"

        )

    )

    # Upper CI
    fig.add_trace(

        go.Scatter(

            x=forecast["Month"],
            y=forecast["Upper_95"],

            mode="lines",

            line=dict(width=0),

            showlegend=False,

            hoverinfo="skip"

        )

    )

    # Lower CI
    fig.add_trace(

        go.Scatter(

            x=forecast["Month"],
            y=forecast["Lower_95"],

            mode="lines",

            fill="tonexty",

            fillcolor="rgba(52,152,219,0.18)",

            line=dict(width=0),

            name="95% Confidence",

            hoverinfo="skip"

        )

    )

    fig.update_layout(

        template="plotly_white",

        height=550,

        title=dict(
            text="Revenue Trend & 6-Month Forecast",
            x=0.01,
            font=dict(size=22)
        ),

        hovermode="x unified",

        paper_bgcolor="white",

        plot_bgcolor="white",

        margin=dict(
            l=20,
            r=20,
            t=70,
            b=20
        ),

        legend=dict(
            orientation="h",
            y=1.08,
            x=0
        )

    )

    fig.update_xaxes(

        title="",

        showgrid=False,

        showline=False

    )

    fig.update_yaxes(

        title="Revenue (R)",

        separatethousands=True,

        gridcolor="#ECECEC",

        zeroline=False

    )

    return fig