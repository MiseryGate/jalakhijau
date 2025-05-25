import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import time
import matplotlib.pyplot as plt
from streamlit_option_menu import option_menu
from folium.plugins import MarkerCluster
from datetime import date
import plotly.express as px
import base64
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import silhouette_score
from sklearn.cluster import DBSCAN, KMeans
import time
import osmnx as ox
import networkx as nx
import folium
import requests
from folium.plugins import MarkerCluster
import geopandas as gpd
import folium
from geopy.geocoders import Nominatim
import requests
from shapely.geometry import Polygon
from streamlit_folium import st_folium

# Read The Data

# Set Streamlit layout to wide
st.set_page_config(layout="wide", page_title="StrataXcel15", page_icon="./building.ico")
#Menu
menu = option_menu(None, ["Home","Dashboard","Descriptive Statistic","Clustering", "Mapping"], 
    icons=['house', 'bar-chart-steps','buildings',"globe"], 
    menu_icon="cast", default_index=0, orientation="horizontal",
    styles={
        "container": {"padding": "0!important"},
        "icon": {"color": "white", "font-size": "15px"}, 
        "nav-link": {"font-size": "15   px", "text-align": "left", "margin":"0px", "--hover-color": "#eee"},
        "nav-link-selected": {"background-color": "blue"},
    })