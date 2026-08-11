import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

OREY_NAVY = "#061A35"
OREY_BLUE = "#1479D2"
OREY_LIGHT_BLUE = "#48A7F8"
OREY_GREEN = "#2ECC71"
OREY_ORANGE = "#F39C12"
OREY_RED = "#C0392B"
OREY_PURPLE = "#8E44AD"
OREY_GREY = "#7F8C8D"
OREY_LIGHT_GREY = "#E9EEF5"

CHANNEL_COLORS = {
    "Online": OREY_BLUE,
    "In-Store": OREY_GREY
}

# COMMON CHART LAYOUT

def apply_channel_layout(
    fig,
    height=340,
    title=None,
    yaxis_title=None
):

    fig.update_layout(
        template="plotly_white",
        height=height,
        title=dict(
            text=title if title else "",
            font=dict(
                size=20,
                color=OREY_NAVY
            ),
            x=0
        ),

        font=dict(
            family="Arial",
            color=OREY_NAVY
        ),
        paper_bgcolor="white",
        plot_bgcolor="white",
        margin=dict(
            l=55,
            r=30,
            t=65,
            b=55
        ),

        hovermode="closest",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0
        )
    )

    fig.update_xaxes(
        showgrid=False,
        linecolor="#D9E1EA",
        tickfont=dict(
            size=11
        )
    )

    fig.update_yaxes(
        title=yaxis_title,
        gridcolor=OREY_LIGHT_GREY,
        zeroline=False,
        title_font=dict(
            size=12
        ),

        tickfont=dict(
            size=11
        )
    )

    return fig

# REVENUE BY SALES CHANNEL

def channel_revenue_chart(channels):

    data = channels.copy()

    data["ProfitMargin"] = (
        data["Profit"] /
        data["Revenue"].replace(0, pd.NA)
        * 100
    )

    data["ReturnRatePercent"] = (
        data["ReturnRate"] * 100
    )

    data = data.sort_values(
        "Revenue",
        ascending=True
    )

    fig = px.bar(
        data,
        x="SalesChannel",
        y="Revenue",
        text="Revenue",
        color="SalesChannel",
        color_discrete_map=CHANNEL_COLORS,
        hover_data={
            "Revenue": ":,.0f",
            "Profit": ":,.0f",
            "ProfitMargin": ":.2f",
            "ReturnRatePercent": ":.2f"
        },

        template="plotly_white"
    )

    fig.update_traces(
        texttemplate="R %{text:,.0f}",
        textposition="outside",
        marker_line_width=0,
        hovertemplate=(
            "<b>%{x}</b><br>"

            "Revenue: R %{y:,.0f}<br>"

            "Profit: R %{customdata[1]:,.0f}<br>"

            "Profit Margin: %{customdata[2]:.2f}%<br>"

            "Return Rate: %{customdata[3]:.2f}%"

            "<extra></extra>"
        )
    )

    fig.update_layout(
        title="Revenue by Sales Channel",
        height=390,
        xaxis_title="Sales Channel",
        yaxis_title="Revenue (R)",
        margin=dict(
            l=60,
            r=135,
            t=70,
            b=55
        ),

        legend=dict(
            orientation="v",
            yanchor="middle",
            y=0.5,
            xanchor="left",
            x=1.02
        )
    )

    return fig

# REVENUE SHARE

def channel_share_chart(channels):

    data = channels.copy()

    fig = px.pie(
        data,
        names="SalesChannel",
        values="Revenue",
        hole=0.58,
        template="plotly_white",
        color="SalesChannel",
        color_discrete_map=CHANNEL_COLORS
    )

    fig.update_traces(
        textposition="inside",
        texttemplate="%{percent:.1%}",
        hovertemplate=(
            "<b>%{label}</b><br>"

            "Revenue: R %{value:,.0f}<br>"

            "Share: %{percent:.1%}"

            "<extra></extra>"
        ),

        marker=dict(
            line=dict(
                color="white",
                width=2
            )
        )
    )

    fig.update_layout(
        title="Revenue Share by Sales Channel",
        height=430,
        margin=dict(
            l=30,
            r=30,
            t=70,
            b=100
        ),

        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.08,
            xanchor="center",
            x=0.5
        )
    )

    return fig

# PROFIT MARGIN BY CHANNEL

def channel_margin_chart(channels):

    data = channels.copy()

    data["ProfitMargin"] = (
        data["Profit"] /
        data["Revenue"].replace(0, pd.NA)
        * 100
    )

    data = data.sort_values(
        "ProfitMargin",
        ascending=True
    )

    data["Performance"] = data["ProfitMargin"].apply(
        lambda x:

        "Strong"

        if x >= data["ProfitMargin"].median()

        else "Below Median"
    )

    fig = px.bar(
        data,
        x="SalesChannel",
        y="ProfitMargin",
        text="ProfitMargin",
        color="Performance",
        color_discrete_map={
            "Strong": OREY_GREEN,
            "Below Median": OREY_ORANGE
        },

        template="plotly_white"
    )

    fig.update_traces(
        texttemplate="%{text:.1f}%",
        textposition="outside",
        hovertemplate=(
            "<b>%{x}</b><br>"

            "Profit Margin: %{y:.2f}%"

            "<extra></extra>"
        )
    )

    median_margin = data["ProfitMargin"].median()

    fig.add_hline(
        y=median_margin,
        line_dash="dash",
        line_width=1,
        line_color=OREY_GREY
    )

    fig.update_layout(
        title="Profit Margin by Channel",
        height=350,
        xaxis_title="Sales Channel",
        yaxis_title="Profit Margin (%)",
        margin=dict(
            l=60,
            r=135,
            t=70,
            b=55
        ),

        legend=dict(
            orientation="v",
            yanchor="middle",
            y=0.5,
            xanchor="left",
            x=1.02
        )
    )

    fig.update_yaxes(
        ticksuffix="%"
    )

    return fig

# RETURN RATE BY CHANNEL

def channel_return_rate_chart(channels):

    data = channels.copy()

    data["ReturnRatePercent"] = (
        data["ReturnRate"] * 100
    )

    median_return = (
        data["ReturnRatePercent"].median()
    )

    data["Return_Performance"] = data[
        "ReturnRatePercent"

    ].apply(
        lambda x:

        "Higher Return Exposure"

        if x > median_return

        else "Lower Return Exposure"
    )

    data = data.sort_values(
        "ReturnRatePercent",
        ascending=True
    )

    fig = px.bar(
        data,
        x="SalesChannel",
        y="ReturnRatePercent",
        text="ReturnRatePercent",
        color="Return_Performance",
        color_discrete_map={
            "Lower Return Exposure": OREY_GREEN,
            "Higher Return Exposure": OREY_RED
        },

        template="plotly_white"
    )

    fig.update_traces(
        texttemplate="%{text:.2f}%",
        textposition="outside",
        hovertemplate=(
            "<b>%{x}</b><br>"

            "Return Rate: %{y:.2f}%"

            "<extra></extra>"
        )
    )

    # Median line retained, but WITHOUT a label

    fig.add_hline(
        y=median_return,
        line_dash="dash",
        line_width=1,
        line_color=OREY_GREY
    )

    fig.update_layout(
        title="Return Rate by Channel",
        height=350,
        xaxis_title="Sales Channel",
        yaxis_title="Return Rate (%)",
        margin=dict(
            l=60,
            r=135,
            t=70,
            b=55
        ),

        legend=dict(
            orientation="v",
            yanchor="middle",
            y=0.5,
            xanchor="left",
            x=1.02
        )
    )

    fig.update_yaxes(
        ticksuffix="%"
    )

    return fig

# CHANNEL PERFORMANCE MATRIX

def channel_performance_matrix(channels):

    data = channels.copy()

    data["ProfitMargin"] = (
        data["Profit"] /
        data["Revenue"].replace(0, pd.NA)
        * 100
    )

    data["ReturnRatePercent"] = (
        data["ReturnRate"] * 100
    )

    median_revenue = data["Revenue"].median()

    median_margin = data["ProfitMargin"].median()

    data["Performance"] = data.apply(
        lambda row:

        "High Value / High Margin"

        if (
            row["Revenue"] >= median_revenue
            and
            row["ProfitMargin"] >= median_margin
        )

        else

        "High Value / Lower Margin"

        if (
            row["Revenue"] >= median_revenue
            and
            row["ProfitMargin"] < median_margin
        )

        else

        "Lower Value / High Margin"

        if (
            row["Revenue"] < median_revenue
            and
            row["ProfitMargin"] >= median_margin
        )

        else

        "Lower Value / Lower Margin",

        axis=1
    )

    colour_map = {
        "High Value / High Margin":
            OREY_GREEN,
        "High Value / Lower Margin":
            OREY_ORANGE,
        "Lower Value / High Margin":
            OREY_BLUE,
        "Lower Value / Lower Margin":
            OREY_RED
    }

    fig = px.scatter(
        data,
        x="Revenue",
        y="ProfitMargin",
        size="Profit",
        color="Performance",
        text="SalesChannel",
        color_discrete_map=colour_map,
        hover_data={
            "Revenue": ":,.0f",
            "Profit": ":,.0f",
            "ProfitMargin": ":.2f",
            "ReturnRatePercent": ":.2f"
        },

        template="plotly_white"
    )

    fig.update_traces(
        textposition="top center",
        marker=dict(
            opacity=0.85,
            line=dict(
                width=1,
                color="white"
            )
        ),

        hovertemplate=(
            "<b>%{text}</b><br>"

            "Revenue: R %{x:,.0f}<br>"

            "Profit Margin: %{y:.2f}%<br>"

            "<extra></extra>"
        )
    )
    fig.add_vline(
        x=median_revenue,
        line_dash="dash",
        line_width=1,
        line_color=OREY_GREY,
        annotation_text="Median Revenue",
        annotation_position="top"
    )

    fig.add_hline(
        y=median_margin,
        line_dash="dash",
        line_width=1,
        line_color=OREY_GREY,
        annotation_text="Median Margin",
        annotation_position="top left"
    )

    fig.update_layout(
        template="plotly_white",
        height=450,
        title=dict(
            text="Channel Performance Matrix",
            font=dict(
                size=20,
                color=OREY_NAVY
            ),

            x=0
        ),

        font=dict(
            family="Arial",
            color=OREY_NAVY
        ),

        paper_bgcolor="white",
        plot_bgcolor="white",
        hovermode="closest",
        margin=dict(
            l=65,
            r=30,
            t=70,
            b=115
        ),

        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.18,
            xanchor="center",
            x=0.5,
            title="Performance Category"
        )
    )

    fig.update_xaxes(
        title="Revenue (R)",
        showgrid=False,
        linecolor="#D9E1EA"
    )

    fig.update_yaxes(
        title="Profit Margin (%)",
        ticksuffix="%%",
        gridcolor=OREY_LIGHT_GREY,
        zeroline=False
    )

    return fig