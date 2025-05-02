# -*- coding: utf-8 -*-
"""
Created on Tue Apr 29 15:26:52 2025

@author: alann
"""
import networkx as nx
import plotly.graph_objects as go
import streamlit as st

import importlib.util
import sys
from pathlib import Path

# Path to your module file
file_path = Path("pages/1_📅_Schedule.py")

# Create module spec
spec = importlib.util.spec_from_file_location("schedule_module", file_path)
module = importlib.util.module_from_spec(spec)
sys.modules["schedule_module"] = module
spec.loader.exec_module(module)



#%%

#compute_visualizations, slot_to_products, product_priority, lead_time_days, slots, today = module.main()
G = module.G




#%%



def plot_network_graph_plotly(G, title="Network Graph"):
    pos = nx.spring_layout(G, seed=42)
    
    # Create edge traces
    edge_x = []
    edge_y = []
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x += [x0, x1, None]
        edge_y += [y0, y1, None]

    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=0.5, color='#888'),
        hoverinfo='none',
        mode='lines'
    )

    # Create node traces
    node_x = []
    node_y = []
    node_text = []
    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        node_text.append(str(node))

    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers+text',
        text=node_text,
        textposition="top center",
        hoverinfo='text',
        marker=dict(
            showscale=False,
            color='blue',
            size=10,
            line_width=2
        )
    )

    fig = go.Figure(data=[edge_trace, node_trace],
                    layout=go.Layout(
                        title=title,
                        title_x=0.5,
                        showlegend=False,
                        hovermode='closest',
                        margin=dict(b=20,l=5,r=5,t=40),
                        xaxis=dict(showgrid=False, zeroline=False),
                        yaxis=dict(showgrid=False, zeroline=False)
                    ))
    
    return fig

#%%



fig = plot_network_graph_plotly(G, title="Product Conflict Graph")

st.title("🗓️ Graph Network")
st.plotly_chart(fig, use_container_width=True)




#%%
# st.title("📊 Subgraph Visualizations")

# if graphs:
#     for i, fig in enumerate(graphs, start=1):
#         st.subheader(f"Graph {i}")
#         st.plotly_chart(fig, use_container_width=True)
# else:
#     st.write("No visualizations returned.")
        
#%%