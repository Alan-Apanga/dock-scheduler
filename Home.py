# -*- coding: utf-8 -*-
"""
Created on Tue Apr 29 01:08:41 2025

@author: alann
"""

import streamlit as st



#%%

st.set_page_config(
    page_title="Dashboard for Replenishment Schedule",
    page_icon="🔃",
    layout="wide",
    initial_sidebar_state="expanded")


#%%


# Table View


st.sidebar.markdown("Click the pages ☝️ to navigate between Interface.")


st.markdown(""" 
            
# 📦 Inventory Replenishment Scheduling Dashboard

Welcome to the **Inventory Replenishment Scheduling Dashboard** — a data-driven solution designed to optimize product delivery planning across multiple docking stations.

---

## 🚀 Project Overview

This tool solves the **Replenishment Slot Allocation** problem for a warehouse or retail supply chain. It schedules **products** for delivery into **5 distinct docking stations**, based on:

- 🧊 **Slot Type Requirements** (e.g., Cold Storage, Perishable, Dry Goods, etc.)
- ⏱️ **Lead Times** (minimum days required before product arrival)
- 🧑‍🤝‍🧑 **Supplier Conflicts** (products from the same supplier can't arrive at the same time)
- 📊 **Product Priority** (high-priority items scheduled earlier when possible)

Each product is assigned:
- A **slot type** → determines the **dock/station** it belongs to
- A **priority score** → influences scheduling order
- A **lead time** → ensures realistic delivery windows

---

## 🧠 Theory & Method

This dashboard uses a combination of **graph theory** and **greedy optimization** to allocate time slots efficiently:

- ✅ A **conflict graph** is built where edges represent clashes (e.g., same supplier or slot type).
- ✅ Within each docking station (slot group), a **DSatur greedy coloring algorithm** is applied to prevent overlapping deliveries.
- ✅ Each product is then assigned to the **earliest available time slot** that:
  - Meets its **lead time requirement**
  - Avoids conflicts with already scheduled products
  - Respects **priority-based scheduling**

---

## 📊 Features of this Dashboard

- ✅ **Gantt Chart View**  
  Interactive timeline showing exactly when and where each product is scheduled.

- ✅ **Schedule Table**  
  See which products are assigned to which time slots and docking stations, alongside priority.

- ✅ **Dock Utilization Report**  
  Quickly visualize how busy each dock is (number of scheduled products per station).

- ✅ **Priority Mapping**  
  Combined product + priority labeling for easy tracking of high-impact items.

---

## 📌 Assumptions

- The system supports **5 fixed slot types**, each tied to a unique docking station.
- Each product can be **scheduled once**, and **no overbooking** is allowed.
- All deliveries take **2 hours per slot**, within a **6-day horizon (24 time slots)**.
- The product-priority mapping is based on **aggregated supplier-level importance**.

---

## 💼 Use Case

This tool is ideal for:
- Supply Chain Managers needing conflict-free dock scheduling
- Warehouse teams managing **multi-slot**, **multi-supplier** delivery planning
- Analysts needing visibility into **priority-driven logistics**

---

🔄 Data is generated artificially for simulation purposes, but structure mirrors real-world warehouse operations.

            
            
            
            
            
""") 