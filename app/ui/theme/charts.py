"""
Chart theming utilities for consistent light theme across all visualizations
"""
from .tokens import LIGHT

def apply_light_theme_to_plotly(fig):
    """Apply consistent light theme to any Plotly figure"""
    t = LIGHT
    
    fig.update_layout(
        plot_bgcolor=t['chart-bg'],
        paper_bgcolor=t['chart-bg'], 
        font_color=t['text'],
        title_font_color=t['text'],
        title_font_size=16,
        title_font_family="Inter, sans-serif",
        font_family="Inter, sans-serif",
        xaxis=dict(
            gridcolor=t['chart-grid'],
            linecolor=t['border'],
            tickcolor=t['border'],
            title_font_color=t['text-secondary'],
            tickfont_color=t['text-secondary'],
            zerolinecolor=t['border']
        ),
        yaxis=dict(
            gridcolor=t['chart-grid'], 
            linecolor=t['border'],
            tickcolor=t['border'],
            title_font_color=t['text-secondary'],
            tickfont_color=t['text-secondary'],
            zerolinecolor=t['border']
        ),
        margin=dict(l=20, r=20, t=40, b=20),
        # Use light theme color sequence
        colorway=t['chart-colors']
    )
    
    return fig

def get_chart_colors():
    """Get the standard chart color palette"""
    return LIGHT['chart-colors']

def get_status_color(status: str) -> str:
    """Get color for status indicators"""
    t = LIGHT
    colors = {
        'success': t['success'],
        'completed': t['success'], 
        'warning': t['warning'],
        'in_progress': t['warning'],
        'pending': t['warning'],
        'error': t['error'],
        'failed': t['error'],
        'info': t['info'],
        'default': t['text-muted']
    }
    return colors.get(status.lower(), colors['default'])