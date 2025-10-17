import plotly.graph_objects as go

def tidy(
    fig: go.Figure,
    *,
    title: str | None = None,
    x_title: str | None = None,
    y_title: str | None = None,
) -> go.Figure:
    """Apply a consistent Plotly layout, hover, and optional titles."""
    if title:
        fig.update_layout(title=title)
    if x_title:
        fig.update_xaxes(title_text=x_title)
    if y_title:
        fig.update_yaxes(title_text=y_title)

    fig.update_layout(
        template="plotly_white",
        margin=dict(l=10, r=10, t=50, b=10),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        xaxis=dict(categoryorder="array"),
    )
    # Uniform hover: show x then y with 2 decimals when numeric
    fig.update_traces(hovertemplate="%{x}<br>%{y}<extra></extra>")
    return fig
