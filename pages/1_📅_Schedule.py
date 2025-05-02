# -*- coding: utf-8 -*-
"""
Created on Sun Apr 27 14:12:12 2025

@author: alann
"""


import streamlit as st

import pandas as pd
import random
from typing import Dict
from typing import List
import calendar


import networkx as nx
import itertools

import plotly.express as px
import plotly.graph_objects as go

import altair as alt



from datetime import datetime, timedelta
from collections import defaultdict

#pio.renderers.default = "browser"





#%% 
# 1. Setup basic parameters
random.seed(42)

num_suppliers = 250
num_products = 40


supplier_ids = [f'Supplier_{str(i).zfill(3)}' for i in range(1, num_suppliers + 1)]
products = [f'Product_{i}' for i in range(1, num_products + 1)]



# 2. Create supplier-product priority table
supplier_data = []
for supplier in supplier_ids:
    num_products_supplied = random.randint(5, 10)
    supplied_products = random.sample(products, num_products_supplied)
    row = {product: random.randint(1, 5) if product in supplied_products else 0 for product in products}
    row['Supplier ID'] = supplier
    supplier_data.append(row)

supplier_df = pd.DataFrame(supplier_data)
supplier_df = supplier_df[['Supplier ID'] + products]


# total priority across all suppliers for that product.
product_priority = supplier_df[products].sum(axis=0).to_dict()

# 3. Randomly assign products to slot types
slot_types = ["Cold Storage", "Perishable", "Dry Goods", "Bulk Items", "Hazardous Materials"]
product_slot = {product: random.choice(slot_types) for product in products}


# Random lead times for each product
lead_time_days = {product: random.randint(1, 5) for product in products}




#%%


def add_supplier_conflict_edges(G: nx.Graph, supplier_df: pd.DataFrame, supplier_ids: list[str]) -> None:
    """
    Adds weighted edges between products that are supplied by the same supplier.
    Each edge is weighted by the sum of their priority scores.
    A 'supplier' conflict label is attached to each such edge.

    Parameters:
    - G: networkx.Graph
        The graph to which edges will be added.
    - supplier_df: pd.DataFrame
        A DataFrame with 'Supplier ID' as a column and product names as columns.
        Each cell contains a priority (>0 if the supplier provides that product).
    - supplier_ids: list of Supplier IDs to iterate over.
    """
    new_supplier_df = supplier_df.set_index('Supplier ID').T

    for supplier in supplier_ids:
        if supplier not in new_supplier_df.columns:
            continue  # skip missing supplier
        
        priorities = new_supplier_df[supplier]
        supplied_products = priorities[priorities > 0].index.tolist()

        for u, v in itertools.combinations(supplied_products, 2):
            weight = int(priorities[u] + priorities[v])

            if G.has_edge(u, v):
                G[u][v]['weight'] += weight
                G[u][v]['conflicts'].add('supplier')
            else:
                G.add_edge(u, v, weight=weight, conflicts={'supplier'})

#%%




#               Function for DSatur Greedy Coloring
def dsatur_coloring(subgraph, product_priority):
    
    """
The D-Satur greedy algorithm is a graph coloring algorithm that extends the 
basic greedy algorithm by considering vertex degree and saturation degree to achieve 
better results in graph coloring problems. Here's a breakdown of its key concepts:


1. Vertex Degree: This refers to the number of edges connected to a vertex. In 
graph coloring, vertices with higher degrees (more connections) are generally 
harder to color because they tend to have more adjacent vertices to consider.

2. Saturation Degree (D-Saturation): The saturation degree of a vertex is the 
count of different colors used by its neighboring vertices. In D-Satur, vertices 
are selected based on their degree and the number of unique colors used by their neighbors.

3. Algorithm Steps:

Start with an uncolored vertex with the highest degree.
Choose a vertex that has the highest saturation degree (maximum number of different colors among its neighbors) 
if there are ties in the degrees.
Assign the smallest possible color to the selected vertex that is not already used by its neighbors.
Repeat until all vertices are colored.

Objective: The goal of D-Satur is to minimize the number of colors used while 
ensuring that no two adjacent vertices share the same color.


    
    
    """
    
    uncolored = set(subgraph.nodes())
    color_assignment = {}
    saturation = {node: set() for node in subgraph.nodes()}
    degrees = dict(subgraph.degree())

    while uncolored:
        # 1) Pick nodes with max saturation degree
        max_sat = max(len(saturation[n]) for n in uncolored)
        candidates = [n for n in uncolored if len(saturation[n]) == max_sat]
        
        # 2) Break ties by degree
        max_deg = max(degrees[n] for n in candidates)
        candidates = [n for n in candidates if degrees[n] == max_deg]
        
        # 3) Break ties by product priority (higher priority first)
        max_prio = max(product_priority[n] for n in candidates)
        candidates = [n for n in candidates if product_priority[n] == max_prio]

        
        # 4) Final tie-break: random if necessary
        node = random.choice(candidates)

        
        # 5) Assign smallest available color
        forbidden = {color_assignment[nb] for nb in subgraph[node] if nb in color_assignment}
        
        # color mapping: Easier for internal logic (fast), colors needs mapping afterward
        for color in range(1000):
            if color not in forbidden:
                color_assignment[node] = color
                break

        # 6) Update neighbor saturation
        for neighbor in subgraph[node]:
            if neighbor in uncolored:
                saturation[neighbor].add(color_assignment[node])

        uncolored.remove(node)

    return color_assignment








#%%
# year: int = 2021,
# month: int = 6,
# start_day: int = 14,
# end_day: int = 19,
# start_hour: int = 10,
# end_hour: int = 18,
# interval_hours: int = 2

def generate_replenishment_calendar(
    year,
    month,
    start_day,
    end_day,
    start_hour,
    end_hour,
    interval_hours
) -> list[datetime]:
    """
    Generate a list of datetime slots for replenishment scheduling.

    Parameters:
    - year: int, year of the calendar
    - month: int, month of the calendar
    - start_day: int, starting day (inclusive)
    - end_day: int, ending day (inclusive)
    - start_hour: int, start hour of each day (inclusive)
    - end_hour: int, end hour of each day (exclusive)
    - interval_hours: int, interval between time slots in hours

    Returns:
    - List of datetime objects representing time slots
    """
    dates = []
    for day in range(start_day, end_day + 1):
        for hour in range(start_hour, end_hour, interval_hours):
            dates.append(datetime(year, month, day, hour))
    
    return dates









#%%

def invert_product_slot_mapping(product_slot_dict):
    """
    Invert a product-to-slot mapping to a slot-to-products mapping.

    Parameters:
    - product_slot: dict mapping product -> slot

    Returns:
    - dict mapping slot -> list of products assigned to that slot
    """
    slot_to_products = defaultdict(list)
    for product, slot in product_slot.items():
        slot_to_products[slot].append(product)
    
    return slot_to_products



#%%



def plot_subgraph(subG, coloring, slot_type):
    # 1. Layout
    pos = nx.spring_layout(subG, seed=42)
    
    # 2. Build edge traces
    edge_x, edge_y = [], []
    for u, v in subG.edges():
        x0, y0 = pos[u]
        x1, y1 = pos[v]
        edge_x += [x0, x1, None]
        edge_y += [y0, y1, None]

    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=1, color='gray'),
        hoverinfo='none',
        mode='lines'
    )

    # 3. Build node traces
    node_x, node_y, node_text, node_color = [], [], [], []
    for node in subG.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        node_text.append(f"{node} (color={coloring.get(node)})")
        node_color.append(coloring.get(node, 0))

    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers+text',
        text=[n for n in subG.nodes()],
        textposition="top center",
        hovertext=node_text,
        marker=dict(
            showscale=True,
            colorscale='Viridis',
            color=node_color,
            size=20,
            colorbar=dict(title="Color Group"),
            line_width=2
        )
    )

    # 4. Create figure
    fig = go.Figure(data=[edge_trace, node_trace],
                    layout=go.Layout(
                        title=dict(
                            text=f"📦 Subgraph for Dock Room: {slot_type}",
                            font=dict(size=16)
                        ),
                        showlegend=False,
                        hovermode='closest',
                        margin=dict(b=20, l=5, r=5, t=40),
                        xaxis=dict(showgrid=False, zeroline=False),
                        yaxis=dict(showgrid=False, zeroline=False),
                        height=600
                    ))

    return fig


#%%

def build_dock_schedules(
    G,
    slot_to_products,
    product_priority,
    lead_time_days,
    dates,
    today,
    dsatur_coloring,
    plot_subgraph=None
) :
    """
    Build dock schedules using DSatur graph coloring per slot type.

    Parameters:
    - G: networkx.Graph: full product conflict graph
    - slot_to_products: dict mapping slot_type -> list of products
    - product_priority: dict mapping product -> priority
    - lead_time_days: dict mapping product -> lead time in days
    - dates: list of datetime objects (available replenishment slots)
    - today: current date as datetime object
    - dsatur_coloring: function that performs DSatur graph coloring
    - plot_subgraph: optional function to visualize subgraphs (can be None)

    Returns:
    - dock_schedules: nested dict mapping slot_type -> date -> list of products
    - graphs: list of visualized subgraphs (if plot_subgraph is provided)
    """
    dock_schedules = defaultdict(lambda: defaultdict(list))
    graphs = []

    for slot_type, products_in_slot in slot_to_products.items():
        # Step 1: Build subgraph
        subG = G.subgraph(products_in_slot)

        # Step 2: DSatur coloring
        coloring = dsatur_coloring(subG, product_priority)

        # Optional: visualize the subgraph
        if plot_subgraph:
            graphs.append(plot_subgraph(subG, coloring, slot_type))

        # Step 3: Assign each color (batch) to an available date
        color_to_date = {}
        used_dates = set()

        for color in sorted(set(coloring.values())):
            products_color = [p for p, c in coloring.items() if c == color]
            max_lead = max(lead_time_days[p] for p in products_color)
            earliest = today + timedelta(days=max_lead)

            assigned_date = None
            for d in dates:
                if d < earliest:
                    continue
                if d not in used_dates:
                    assigned_date = d
                    break

            if assigned_date is not None:
                color_to_date[color] = assigned_date
                used_dates.add(assigned_date)
            else:
                print(f"⚠️ No available slot for color {color} in {slot_type}!")

        # Step 4: Populate dock_schedules
        for product, color in coloring.items():
            date = color_to_date.get(color)
            if date:
                dock_schedules[slot_type][date].append(product)

    return dock_schedules, graphs

#%%

def generate_schedule_dataframe(
    dock_schedules
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Converts a nested dock schedule into a flat DataFrame and a pivoted schedule view.

    Parameters:
    - dock_schedules: dict of slot_type -> date -> list of products

    Returns:
    - schedule_df: flat DataFrame with columns [Docking Station, Datetime, Product]
    - schedule_pivot: pivoted DataFrame with Datetime as index and Docking Stations as columns
    """
    final_schedule = []

    for slot_type, date_products in dock_schedules.items():
        for date, products in date_products.items():
            for product in products:
                final_schedule.append({
                    "Docking Station": slot_type,
                    "Datetime": date,
                    "Product": product
                })

    schedule_df = pd.DataFrame(final_schedule).sort_values(by=["Docking Station", "Datetime"])

    schedule_pivot = schedule_df.pivot(index='Datetime', columns='Docking Station', values='Product')

    # Sort docking stations alphabetically
    schedule_pivot = schedule_pivot.reindex(sorted(schedule_pivot.columns), axis=1)

    # Fill empty slots with placeholder
    schedule_pivot = schedule_pivot.fillna('None')

    return schedule_df, schedule_pivot


#%%




def plot_gantt_chart(
    schedule_pivot: pd.DataFrame,
    product_priority: dict,
    product_slot: dict
):
    """
    Generates a Gantt chart from a schedule pivot using Plotly Express.

    Parameters:
    - schedule_pivot: DataFrame (Datetime x Bin) with product names
    - product_priority: dict mapping Product -> Priority (int)
    - product_slot: dict mapping Product -> Slot Type (Docking Station)

    Returns:
    - Plotly Figure (Gantt Chart)
    """
    # 1. Flatten the pivot to long format
    schedule_long = schedule_pivot.stack().reset_index()
    schedule_long.columns = ['Datetime', 'Bin', 'Product']
    schedule_long = schedule_long.dropna()

    # 2. Add metadata
    schedule_long['Priority'] = schedule_long['Product'].map(product_priority)
    schedule_long['Docking Station'] = schedule_long['Product'].map(product_slot)
    schedule_long['End'] = schedule_long['Datetime'] + pd.Timedelta(hours=2)

    # 3. Plot Gantt chart
    fig = px.timeline(
        schedule_long,
        x_start='Datetime',
        x_end='End',
        y='Bin',
        color='Priority',
        text='Product',
        title='Product Replenishment Schedule',
        labels={'Bin': 'Docking Station'}
    )

    fig.update_yaxes(autorange="reversed")
    fig.update_traces(textposition='inside', insidetextanchor='middle')
    fig.update_layout(height=600)

    return fig, schedule_long

#%%


def annotate_schedule_with_priority(
    schedule_pivot: pd.DataFrame, 
    product_priority: Dict[str, int]
) -> pd.DataFrame:
    """
    Returns a copy of the schedule pivot DataFrame with product names
    annotated by their priority (e.g., "ProductA (P=2)").

    Parameters:
    - schedule_pivot: pd.DataFrame with datetime as index and docking stations as columns
    - product_priority: dict mapping product names to priority values

    Returns:
    - schedule_pivot_combined: Annotated copy of the original schedule_pivot
    """
    schedule_pivot_combined = schedule_pivot.copy()

    for col in schedule_pivot_combined.columns:
        schedule_pivot_combined[col] = schedule_pivot_combined[col].apply(
            lambda prod: f"{prod} (P={product_priority[prod]})"
            if pd.notna(prod) and prod in product_priority
            else "None"
        )

    return schedule_pivot_combined

#%%



def plot_dock_utilization(schedule_long: pd.DataFrame) -> alt.Chart:
    """
    Plot dock utilization as a bar chart showing the number of unique products
    scheduled per dock (Bin), using Altair.

    Parameters:
    - schedule_long: Long-form schedule DataFrame with 'Bin' and 'Product' columns

    Returns:
    - Altair Chart object
    """
    dock_counts = (
        schedule_long.groupby('Bin')['Product']
        .nunique()
        .reset_index(name='Num Products')
        .sort_values(by='Num Products', ascending=False)
    )

    chart = alt.Chart(dock_counts).mark_bar(color='royalblue').encode(
        x=alt.X('Bin:N', title='Docking Station (Bin)', sort='-y'),
        y=alt.Y('Num Products:Q', title='Number of Products Scheduled'),
        tooltip=['Bin', 'Num Products']
    ).properties(
        title="Docking Station Utilization (Number of Scheduled Products)",
        width=600,
        height=400
    )

    return chart

#%%




def annotate_schedule_with_lead_time(
    schedule_pivot: pd.DataFrame, 
    lead_time_days: Dict[str, int]
) -> pd.DataFrame:
    """
    Returns a copy of the schedule pivot DataFrame with product names
    annotated by their lead times (e.g., "ProductA (LT=3d)").

    Parameters:
    - schedule_pivot: pd.DataFrame with Datetime as index and docking stations as columns
    - lead_time_days: dict mapping product names to lead time in days

    Returns:
    - schedule_pivot_combined: Annotated copy of the schedule_pivot
    """
    schedule_pivot_combined = schedule_pivot.copy()

    for col in schedule_pivot_combined.columns:
        schedule_pivot_combined[col] = schedule_pivot_combined[col].apply(
            lambda prod: f"{prod} (LT={lead_time_days[prod]}d)"
            if pd.notna(prod) and prod in lead_time_days
            else "None"
        )

    return schedule_pivot_combined


#%%


def build_supplier_conflict_graph(
    products: List[str],
    supplier_df: pd.DataFrame,
    supplier_ids: List[str],
    add_supplier_conflict_edges_fn
) -> nx.Graph:
    """
    Builds a conflict graph of products based on shared suppliers.

    Parameters:
    - products: List of product names
    - supplier_df: DataFrame with supplier info (indexed by Supplier ID, products as columns)
    - supplier_ids: List of supplier IDs
    - add_supplier_conflict_edges_fn: Function to add supplier conflict edges to the graph

    Returns:
    - G: A NetworkX graph with product nodes and conflict edges
    """
    G = nx.Graph()
    G.add_nodes_from(products)  # Add product nodes

    # Add supplier conflict edges via provided helper function
    add_supplier_conflict_edges_fn(G, supplier_df, supplier_ids)

    return G

#%%




#%%
# =============================================================================
#                                   MAIN
# =============================================================================
# ---- Build the graph ----
G = nx.Graph()
G.add_nodes_from(products)# add all suppliers as nodes
add_supplier_conflict_edges(G, supplier_df, supplier_ids)
  


#%%
def main():
    
    
  

    # --- Streamlit Side Bar ---
    st.title("🗓️ Replenishment Calendar Scheduler")
    
    
    # 1) Today picker + button
    today_date = st.sidebar.date_input("Today", value=datetime.today().date())
    today = datetime(today_date.year, today_date.month, today_date.day)
    
    if st.sidebar.button("Select Today"):
        st.write("today")
        st.code(f"Out[8]: {repr(today)}")
        
    # 2) Compute the scheduling month/year:
    year = today.year
    month = today.month
    # How many days this month has
    _, this_month_max = calendar.monthrange(year, month)
    
    
    # 3) If today is the last day (or beyond), roll into next month
    if today.day >= this_month_max:
        month += 1
        if month > 12:
            month = 1
            year += 1
    
    
    # 4) Now compute min_day = either tomorrow or 1 (if we rolled)
    min_day = 1 if today.day >= this_month_max else today.day + 1
    
    
    
        
    
    st.sidebar.header("Calendar Parameters")
    
    
    # 5) Other calendar params
    start_day = st.sidebar.number_input(
        "Start Day", min_value=min_day, 
        max_value=this_month_max, 
        value=min_day, 
        step=1
    )
    
    default_end = min(start_day + 5, this_month_max)
    end_day = st.sidebar.number_input(
        "End Day", 
        min_value=start_day, 
        max_value=this_month_max, 
        value=default_end, 
        step=1
    )
    
    
    start_hour = st.sidebar.number_input("Start Hour", value=10, min_value=0, max_value=23, step=1)
    end_hour = st.sidebar.number_input("End Hour", value=18, min_value=1, max_value=24, step=1)
    interval_hours = st.sidebar.number_input("Interval (hrs)", value=2, min_value=1, max_value=24, step=1)
    
    # Optional: Show selected range
    st.sidebar.markdown(f"**Selected Date Range:** {year}-{month:02d}-{start_day} to {year}-{month:02d}-{end_day}")


    
    
    if st.sidebar.button("Generate Calendar"):
        slots = generate_replenishment_calendar(
            year=year,
            month=month,
            start_day=start_day,
            end_day=end_day,
            start_hour=start_hour,
            end_hour=end_hour,
            interval_hours=interval_hours
        )
        
        
        # DataFrame for slots
        df_slots = pd.DataFrame({"Datetime": slots})
        with st.expander("📋 Slots Table", expanded=False):
            st.dataframe(df_slots)
    
    
    
        #today = datetime(2021, 6, 10)
        #dates = generate_replenishment_calendar()
        
        # Group products by slot
        slot_to_products = invert_product_slot_mapping(product_slot)
        
        
        # Schedule within the slots based on priority and lead time
        dock_schedules, visualizations = build_dock_schedules(
            G,
            slot_to_products,
            product_priority,
            lead_time_days,
            slots,
            today,
            dsatur_coloring,
            plot_subgraph  # optional, can be None
        )
        
        
        # Build the Final Schedule
        schedule_df, schedule_pivot = generate_schedule_dataframe(dock_schedules)
        
        
        # Gantt chart
        grant_chart, schedule_long = plot_gantt_chart(schedule_pivot, product_priority, product_slot)
        
        
        
        # Table View of Schedule with Priority
        schedule_pivot_combined = annotate_schedule_with_priority(schedule_pivot, product_priority)
        with st.expander("📋 Schedule Table with Priority", expanded=False):
            st.dataframe(schedule_pivot_combined)
        
        
        
        # Table View of Schedule with lead Time
        schedule_pivot_lt = annotate_schedule_with_lead_time(schedule_pivot, lead_time_days)
        with st.expander("📋 Schedule Table with Lead Time", expanded=False):
            st.dataframe(schedule_pivot_lt)
          
    
    
    
        # --- Streamlit Main ---
        # Gantt chart
        with st.container(border=True):
            st.plotly_chart(grant_chart, use_container_width=True)
        
        
      
    
        # Compute scheduled vs. unscheduled
        scheduled = set(schedule_df['Product'])
        all_products = set(products)
        unscheduled = all_products - scheduled
        
        # Streamlit layout with containers
       
        st.subheader("📦 Scheduling Summary")
        
        col1, col2 = st.columns(2)
    
        with col1:
            with st.container(border=True):
                st.metric("✅ Scheduled Products", len(scheduled))
    
        with col2:
            with st.container(border=True):
                st.metric("⚠️ Unscheduled Products", len(unscheduled))
    
        if unscheduled:
            with st.expander("View Unscheduled Products"):
                st.write(sorted(list(unscheduled))[:20])  # show up to 20 products

        
        with st.expander("🕸️ Graph Network", expanded=False):    
            st.markdown("Each subgraph shows conflicts within a specific docking slot.")
            
            num_columns = 2
            for i in range(0, len(visualizations), 2):
                cols = st.columns(num_columns)
                
                # First column
                with cols[0]:
                    st.plotly_chart(visualizations[i], use_container_width=True)
                    
                # Second column (only if available)
                if i + 1 < len(visualizations):
                    with cols[1]:
                        st.plotly_chart(visualizations[i + 1], use_container_width=True)
                
        # Dock Utilization (Number of Products Scheduled per Dock)
        dock_chart = plot_dock_utilization(schedule_long)
        with st.expander("🎰 Dock Utilization (Number of Products Scheduled per Dock)", expanded=False):
            st.altair_chart(dock_chart, use_container_width=True)
        
        
        
       
#%%

if __name__ == "__main__":
     main()
















