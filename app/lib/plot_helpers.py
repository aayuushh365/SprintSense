import plotly.graph_objects as go

def tidy(fig: go.Figure, *, title: str | None = None):
    if title:
        fig.update_layout(title=title)
    fig.update_layout(
        template="plotly_white",
        margin=dict(l=10, r=10, t=50, b=10),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        xaxis=dict(categoryorder="array"),  # we feed ordered categoricals already
    )
    fig.update_traces(hovertemplate="%{x}<br>%{y}<extra></extra>")
    return fig
