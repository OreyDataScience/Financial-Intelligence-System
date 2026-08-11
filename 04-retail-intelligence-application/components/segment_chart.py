import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


# ==========================================================
# OREY ANALYTICS COLOUR PALETTE
# ==========================================================

OREY_NAVY = "#061A35"
OREY_BLUE = "#1479D2"
OREY_LIGHT_BLUE = "#48A7F8"
OREY_GREEN = "#2ECC71"
OREY_ORANGE = "#F39C12"
OREY_RED = "#C0392B"
OREY_PURPLE = "#8E44AD"
OREY_GREY = "#7F8C8D"
OREY_LIGHT_GREY = "#E9EEF5"


# ==========================================================
# COMMON CHART LAYOUT
# ==========================================================

def apply_segment_layout(
    fig,
    height=360,
    title=None,
    xaxis_title=None,
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
            t=70,
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

        title=xaxis_title,

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


# ==========================================================
# SEGMENT COLOUR HELPER
# ==========================================================

def segment_colour_map(data):

    segments = list(
        data["CustomerSegment"].astype(str).unique()
    )

    palette = [
        OREY_BLUE,
        OREY_GREY,
        OREY_GREEN,
        OREY_ORANGE,
        OREY_PURPLE,
        OREY_LIGHT_BLUE
    ]

    return {
        segment: palette[i % len(palette)]
        for i, segment in enumerate(segments)
    }


# ==========================================================
# REVENUE BY CUSTOMER SEGMENT
# ==========================================================

def segment_revenue_chart(segments):

    data = segments.copy()

    data["Revenue"] = data["Revenue"].astype(float)

    data["ProfitMargin"] = (

        data["Profit"]
        /
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

    colour_map = segment_colour_map(data)

    fig = px.bar(

        data,

        x="CustomerSegment",

        y="Revenue",

        text="Revenue",

        color="CustomerSegment",

        color_discrete_map=colour_map,

        template="plotly_white",

        hover_data={

            "Revenue": ":,.0f",

            "Profit": ":,.0f",

            "ProfitMargin": ":.2f",

            "ReturnRatePercent": ":.2f"

        }

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

    apply_segment_layout(

        fig,

        height=380,

        title="Revenue by Customer Segment",

        xaxis_title="Customer Segment",

        yaxis_title="Revenue (R)"

    )

    fig.update_layout(

        showlegend=False

    )

    return fig


# ==========================================================
# PROFIT BY CUSTOMER SEGMENT
# ==========================================================

def segment_profit_chart(segments):

    data = segments.copy()

    data["Profit"] = data["Profit"].astype(float)

    data = data.sort_values(
        "Profit",
        ascending=True
    )

    colour_map = segment_colour_map(data)

    fig = px.bar(

        data,

        x="CustomerSegment",

        y="Profit",

        text="Profit",

        color="CustomerSegment",

        color_discrete_map=colour_map,

        template="plotly_white",

        hover_data={

            "Revenue": ":,.0f",

            "Profit": ":,.0f",

            "AvgMargin": ":.2f"

        }

    )

    fig.update_traces(

        texttemplate="R %{text:,.0f}",

        textposition="outside",

        marker_line_width=0,

        hovertemplate=(

            "<b>%{x}</b><br>"

            "Profit: R %{y:,.0f}<br>"

            "Revenue: R %{customdata[0]:,.0f}<br>"

            "Average Margin: %{customdata[2]:.2f}%"

            "<extra></extra>"

        )

    )

    apply_segment_layout(

        fig,

        height=360,

        title="Profit by Customer Segment",

        xaxis_title="Customer Segment",

        yaxis_title="Profit (R)"

    )

    fig.update_layout(

        showlegend=False

    )

    return fig


# ==========================================================
# CUSTOMER SEGMENT MARGIN
# ==========================================================

def segment_margin_chart(segments):

    data = segments.copy()

    # ------------------------------------------------------
    # CORRECT MARGIN CONVERSION
    #
    # AvgMargin is stored as a decimal.
    # Round to 4 decimal places first,
    # then multiply by 100 to obtain percentage.
    # ------------------------------------------------------

    data["AvgMarginPercent"] = (

        data["AvgMargin"]
        .round(4)
        * 100

    )

    data["ReturnRatePercent"] = (

        data["ReturnRate"] * 100

    )

    data = data.sort_values(

        "AvgMarginPercent",

        ascending=True

    )

    colour_map = segment_colour_map(data)

    fig = px.bar(

        data,

        x="CustomerSegment",

        y="AvgMarginPercent",

        text="AvgMarginPercent",

        color="CustomerSegment",

        color_discrete_map=colour_map,

        template="plotly_white",

        hover_data={

            "AvgMarginPercent": ":.2f",

            "ReturnRatePercent": ":.2f",

            "Revenue": ":,.0f",

            "Profit": ":,.0f"

        }

    )

    fig.update_traces(

        texttemplate="%{text:.2f}%",

        textposition="outside",

        marker_line_width=0,

        hovertemplate=(

            "<b>%{x}</b><br>"

            "Average Margin: %{y:.2f}%<br>"

            "Return Rate: %{customdata[1]:.2f}%<br>"

            "Revenue: R %{customdata[2]:,.0f}"

            "<extra></extra>"

        )

    )

    median_margin = (

        data["AvgMarginPercent"].median()

    )

    fig.add_hline(

        y=median_margin,

        line_dash="dash",

        line_width=1,

        line_color=OREY_GREY

    )

    apply_segment_layout(

        fig,

        height=360,

        title="Customer Segment Margin",

        xaxis_title="Customer Segment",

        yaxis_title="Average Margin (%)"

    )

    fig.update_yaxes(

        ticksuffix="%"

    )

    fig.update_layout(

        showlegend=False

    )

    return fig


# ==========================================================
# RETURN RATE BY CUSTOMER SEGMENT
# ==========================================================

def segment_return_rate_chart(segments):

    data = segments.copy()

    data["ReturnRatePercent"] = (

        data["ReturnRate"] * 100

    )

    data = data.sort_values(

        "ReturnRatePercent",

        ascending=True

    )

    median_return = data[

        "ReturnRatePercent"

    ].median()

    # ------------------------------------------------------
    # PERFORMANCE CLASSIFICATION
    # ------------------------------------------------------

    data["Return_Performance"] = data[
        "ReturnRatePercent"
    ].apply(

        lambda x:

        "Higher Return Exposure"

        if x > median_return

        else "Lower Return Exposure"

    )

    # ------------------------------------------------------
    # FIXED COLOURS
    # ------------------------------------------------------

    performance_colour_map = {

        "Lower Return Exposure":
            OREY_GREEN,

        "Higher Return Exposure":
            OREY_RED

    }

    fig = px.bar(

        data,

        x="CustomerSegment",

        y="ReturnRatePercent",

        text="ReturnRatePercent",

        color="Return_Performance",

        color_discrete_map=performance_colour_map,

        template="plotly_white"

    )

    fig.update_traces(

        texttemplate="%{text:.2f}%",

        textposition="outside",

        marker_line_width=0,

        hovertemplate=(

            "<b>%{x}</b><br>"

            "Return Rate: %{y:.2f}%"

            "<extra></extra>"

        )

    )

    fig.add_hline(

        y=median_return,

        line_dash="dash",

        line_width=1,

        line_color=OREY_GREY

    )

    apply_segment_layout(

        fig,

        height=360,

        title="Return Rate by Customer Segment",

        xaxis_title="Customer Segment",

        yaxis_title="Return Rate (%)"

    )

    fig.update_yaxes(

        ticksuffix="%"

    )

    # ------------------------------------------------------
    # LEGEND ON RIGHT
    # ------------------------------------------------------

    fig.update_layout(

        legend=dict(

            orientation="v",

            yanchor="middle",

            y=0.5,

            xanchor="left",

            x=1.02

        ),

        margin=dict(

            l=55,

            r=145,

            t=70,

            b=55

        )

    )

    return fig


# ==========================================================
# SEGMENT PERFORMANCE MATRIX
# ==========================================================

def segment_performance_matrix(segments):

    data = segments.copy()

    data["ProfitMargin"] = (

        data["Profit"]
        /
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

        text="CustomerSegment",

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

        line_color=OREY_GREY

    )

    fig.add_hline(

        y=median_margin,

        line_dash="dash",

        line_width=1,

        line_color=OREY_GREY

    )

    apply_segment_layout(

        fig,

        height=430,

        title="Customer Segment Performance Matrix",

        xaxis_title="Revenue (R)",

        yaxis_title="Profit Margin (%)"

    )

    fig.update_yaxes(

        ticksuffix="%"

    )

    # Legend at bottom

    fig.update_layout(

        legend=dict(

            orientation="h",

            yanchor="top",

            y=-0.18,

            xanchor="center",

            x=0.5

        ),

        margin=dict(

            l=55,

            r=30,

            t=70,

            b=100

        )

    )

    return fig