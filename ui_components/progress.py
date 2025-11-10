"""
Progress bars and donut charts with glassmorphism styling.
"""

import streamlit as st
import plotly.graph_objects as go

def render_progress_bar(label, current, target, kind="neutral"):
    """
    Render a glassmorphic progress bar.
    
    Args:
        label: Progress bar label
        current: Current value
        target: Target value
        kind: Style type - "gain", "risk", "analytics", "goal", or "neutral"
    """
    percentage = min((current / target * 100) if target > 0 else 0, 100)
    
    # Color mapping
    color_map = {
        "gain": "#10b981",
        "risk": "#ef4444",
        "analytics": "#3b82f6",
        "goal": "#f59e0b",
        "neutral": "#8b5cf6"
    }
    color = color_map.get(kind, color_map["neutral"])
    
    progress_html = f"""
    <div style="margin: 16px 0;">
        <div style="
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
        ">
            <span style="
                font-weight: 600;
                color: rgba(255, 255, 255, 0.9);
                font-size: 0.95rem;
            ">{label}</span>
            <span style="
                font-weight: 700;
                color: {color};
                font-size: 0.95rem;
            ">{percentage:.1f}%</span>
        </div>
        <div style="
            width: 100%;
            height: 24px;
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 12px;
            overflow: hidden;
            border: 1px solid rgba(255, 255, 255, 0.2);
            box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.1);
        ">
            <div style="
                width: {percentage}%;
                height: 100%;
                background: linear-gradient(90deg, {color}, {color}dd);
                border-radius: 12px;
                transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1);
                box-shadow: 0 0 12px {color}66;
                position: relative;
                overflow: hidden;
            ">
                <div style="
                    position: absolute;
                    inset: 0;
                    background: linear-gradient(
                        90deg,
                        transparent,
                        rgba(255, 255, 255, 0.3),
                        transparent
                    );
                    animation: shimmer 2s infinite;
                "></div>
            </div>
        </div>
        <div style="
            display: flex;
            justify-content: space-between;
            margin-top: 6px;
            font-size: 0.8rem;
            color: rgba(255, 255, 255, 0.6);
        ">
            <span>${current:,.0f}</span>
            <span>${target:,.0f}</span>
        </div>
    </div>
    
    <style>
        @keyframes shimmer {{
            0% {{ transform: translateX(-100%); }}
            100% {{ transform: translateX(100%); }}
        }}
    </style>
    """
    
    st.markdown(progress_html, unsafe_allow_html=True)

def render_donut_chart(title, data_dict, kind="neutral"):
    """
    Render an animated donut chart for category breakdowns.
    
    Args:
        title: Chart title
        data_dict: Dictionary of {label: value}
        kind: Color scheme - "gain", "risk", "analytics", "goal", or "neutral"
    
    Example:
        render_donut_chart("Budget Allocation", {
            "Savings": 5000,
            "Expenses": 3000,
            "Investments": 2000
        }, kind="goal")
    """
    if not data_dict:
        st.warning("No data available for chart")
        return
    
    labels = list(data_dict.keys())
    values = list(data_dict.values())
    
    # Color schemes
    color_schemes = {
        "gain": ['#10b981', '#059669', '#047857', '#065f46'],
        "risk": ['#ef4444', '#dc2626', '#b91c1c', '#991b1b'],
        "analytics": ['#3b82f6', '#2563eb', '#1d4ed8', '#1e40af'],
        "goal": ['#f59e0b', '#d97706', '#b45309', '#92400e'],
        "neutral": ['#8b5cf6', '#7c3aed', '#6d28d9', '#5b21b6']
    }
    colors = color_schemes.get(kind, color_schemes["neutral"])
    
    # Extend colors if needed
    while len(colors) < len(labels):
        colors.extend(colors)
    
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.6,
        marker=dict(
            colors=colors[:len(labels)],
            line=dict(color='rgba(255, 255, 255, 0.3)', width=2)
        ),
        textinfo='label+percent',
        textfont=dict(size=12, color='white'),
        hovertemplate='<b>%{label}</b><br>$%{value:,.0f}<br>%{percent}<extra></extra>'
    )])
    
    # Calculate total
    total = sum(values)
    
    fig.update_layout(
        title=dict(
            text=title,
            font=dict(size=18, color='white', family='Inter'),
            x=0.5,
            xanchor='center'
        ),
        annotations=[dict(
            text=f'<b>Total</b><br>${total:,.0f}',
            x=0.5, y=0.5,
            font=dict(size=16, color='white', family='Inter'),
            showarrow=False
        )],
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        height=400,
        showlegend=True,
        legend=dict(
            font=dict(color='white'),
            bgcolor='rgba(255, 255, 255, 0.1)',
            bordercolor='rgba(255, 255, 255, 0.2)',
            borderwidth=1
        ),
        transition=dict(duration=500, easing='cubic-in-out')
    )
    
    st.plotly_chart(fig, use_container_width=True, key=f"donut_{title}_{hash(str(data_dict))}")

def render_gauge_chart(title, value, max_value, thresholds=None, kind="neutral"):
    """
    Render a gauge chart for single metrics.
    
    Args:
        title: Gauge title
        value: Current value
        max_value: Maximum value
        thresholds: Dict with 'low', 'medium', 'high' values (optional)
        kind: Color scheme
    """
    color_map = {
        "gain": "#10b981",
        "risk": "#ef4444",
        "analytics": "#3b82f6",
        "goal": "#f59e0b",
        "neutral": "#8b5cf6"
    }
    color = color_map.get(kind, color_map["neutral"])
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=value,
        title={'text': title, 'font': {'color': 'white', 'size': 18}},
        delta={'reference': max_value * 0.7},
        gauge={
            'axis': {'range': [0, max_value], 'tickcolor': 'white'},
            'bar': {'color': color},
            'bgcolor': 'rgba(255, 255, 255, 0.1)',
            'borderwidth': 2,
            'bordercolor': 'rgba(255, 255, 255, 0.3)',
            'steps': [
                {'range': [0, max_value * 0.33], 'color': 'rgba(239, 68, 68, 0.2)'},
                {'range': [max_value * 0.33, max_value * 0.66], 'color': 'rgba(245, 158, 11, 0.2)'},
                {'range': [max_value * 0.66, max_value], 'color': 'rgba(16, 185, 129, 0.2)'}
            ],
            'threshold': {
                'line': {'color': 'white', 'width': 4},
                'thickness': 0.75,
                'value': max_value * 0.9
            }
        },
        number={'font': {'color': 'white', 'size': 32}}
    ))
    
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        height=300,
        font={'color': 'white'},
        transition=dict(duration=500)
    )
    
    st.plotly_chart(fig, use_container_width=True, key=f"gauge_{title}_{value}")
