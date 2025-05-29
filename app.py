import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium
import plotly.express as px
import plotly.graph_objects as go
import networkx as nx
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import geopandas as gpd
from shapely.geometry import Point, Polygon
from openai import AzureOpenAI
import os
from io import StringIO
import base64

# Page config
st.set_page_config(
    page_title="🛰️ JALAK-HIJAU | Environmental Crime Detection",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for green theme
def load_css():
    st.markdown("""
    <style>
    /* Main theme colors */
    :root {
        --primary-green: #2E8B57;
        --coral-orange: #FF6B35;
        --alice-blue: #F0F8FF;
        --dark-slate: #2F4F4F;
        --success-green: #28A745;
        --warning-orange: #FFA500;
        --danger-red: #DC3545;
    }
    
    /* Main container styling */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Header styling */
    .main-header {
        background: linear-gradient(90deg, var(--primary-green), #228B22);
        color: white;
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        text-align: center;
    }
    
    /* Alert boxes */
    .alert-critical {
        background-color: #FFE6E6;
        border-left: 5px solid var(--danger-red);
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    
    .alert-warning {
        background-color: #FFF8E1;
        border-left: 5px solid var(--warning-orange);
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    
    .alert-success {
        background-color: #E8F5E8;
        border-left: 5px solid var(--success-green);
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    
    /* Metric cards */
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        border-left: 5px solid var(--primary-green);
        margin: 1rem 0;
    }
    
    /* Risk score styling */
    .risk-high { color: var(--danger-red); font-weight: bold; }
    .risk-medium { color: var(--warning-orange); font-weight: bold; }
    .risk-low { color: var(--success-green); font-weight: bold; }
    
    /* Navigation styling */
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, var(--primary-green), #228B22);
    }
    
    /* Button styling */
    .stButton > button {
        background-color: var(--primary-green);
        color: white;
        border: none;
        border-radius: 5px;
        padding: 0.5rem 1rem;
        font-weight: bold;
    }
    
    .stButton > button:hover {
        background-color: #228B22;
    }
    </style>
    """, unsafe_allow_html=True)

# Initialize session state
def init_session_state():
    if 'selected_alert' not in st.session_state:
        st.session_state.selected_alert = None
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'investigation_mode' not in st.session_state:
        st.session_state.investigation_mode = False

# Data loading functions
@st.cache_data
def load_geospatial_data():
    """Load and process geospatial data"""
    try:
        # Try to load actual shapefiles
        forest_data = gpd.read_file("forest_boundaries.shp")
        palm_data = gpd.read_file("palm_concessions.shp")
        return forest_data, palm_data
    except:
        # Generate synthetic geospatial data for demo
        return generate_synthetic_geodata()

@st.cache_data
def load_company_data():
    """Load company data"""
    try:
        companies_df = pd.read_csv("data/pt_data.csv")
        return companies_df
    except:
        return generate_demo_companies()

@st.cache_data
def load_transaction_data():
    """Load transaction data"""
    try:
        transactions_df = pd.read_csv("data/transactions.csv")
        high_risk_df = pd.read_csv("data/transactions_high_risk.csv")
        clusters_df = pd.read_csv("data/transactions_clusters.csv")
        return transactions_df, high_risk_df, clusters_df
    except:
        return generate_demo_transactions()

def generate_synthetic_geodata():
    """Generate synthetic geospatial data for demo"""
    # Indonesia bounding box (approximate)
    min_lat, max_lat = -6.0, 6.0
    min_lon, max_lon = 95.0, 141.0
    
    # Generate forest areas
    forest_areas = []
    for i in range(50):
        center_lat = np.random.uniform(min_lat, max_lat)
        center_lon = np.random.uniform(min_lon, max_lon)
        size = np.random.uniform(0.1, 0.5)
        
        forest_areas.append({
            'geometry': Point(center_lon, center_lat).buffer(size),
            'name': f'Protected Forest {i+1}',
            'status': 'Protected',
            'area_ha': np.random.randint(1000, 50000)
        })
    
    # Generate palm concessions (some overlapping with forest)
    palm_areas = []
    for i in range(30):
        if i < 10:  # 10 overlapping concessions
            base_forest = forest_areas[i % len(forest_areas)]
            center = base_forest['geometry'].centroid
            center_lat, center_lon = center.y, center.x
            # Create overlap
            center_lat += np.random.uniform(-0.1, 0.1)
            center_lon += np.random.uniform(-0.1, 0.1)
        else:  # Non-overlapping concessions
            center_lat = np.random.uniform(min_lat, max_lat)
            center_lon = np.random.uniform(min_lon, max_lon)
        
        size = np.random.uniform(0.05, 0.3)
        palm_areas.append({
            'geometry': Point(center_lon, center_lat).buffer(size),
            'company': f'PT PALM COMPANY {i+1}',
            'permit_status': 'Active',
            'area_ha': np.random.randint(500, 20000),
            'lat': center_lat,
            'lon': center_lon,
            'overlaps_forest': i < 10
        })
    
    forest_gdf = gpd.GeoDataFrame(forest_areas)
    palm_gdf = gpd.GeoDataFrame(palm_areas)
    
    return forest_gdf, palm_gdf

def generate_demo_companies():
    """Generate demo company data"""
    companies = []
    company_names = [
        'PT BERKAH SAWIT NUSANTARA', 'PT HIJAU SEJAHTERA ABADI',
        'PT CAHAYA PALM MANDIRI', 'PT DUTA KELAPA SAWIT',
        'PT KARYA UTAMA CONSULTING', 'PT PRIMA JAYA TRADING'
    ]
    
    for i, name in enumerate(company_names):
        companies.append({
            'company_id': f'COMP_{i+1:03d}',
            'nama_perseroan': name,
            'is_suspicious': i >= 4,  # Last 2 are shell companies
            'risk_score': np.random.randint(70, 95) if i >= 4 else np.random.randint(20, 50),
            'modal_disetor': np.random.randint(1000000000, 10000000000),
            'overlaps_forest': i < 4 and np.random.random() < 0.3
        })
    
    return pd.DataFrame(companies)

def generate_demo_transactions():
    """Generate demo transaction data"""
    # Simplified demo data
    transactions = []
    for i in range(1000):
        transactions.append({
            'transaction_id': f'TXN_{i+1:06d}',
            'transaction_date': datetime.now() - timedelta(days=np.random.randint(0, 365)),
            'amount_idr': np.random.randint(1000000, 5000000000),
            'risk_score': np.random.randint(0, 100),
            'sender_name': f'Company {np.random.randint(1, 10)}',
            'receiver_name': f'Company {np.random.randint(1, 10)}',
            'is_flagged': np.random.random() < 0.2
        })
    
    df = pd.DataFrame(transactions)
    high_risk = df[df['risk_score'] > 70]
    clusters = pd.DataFrame([{'cluster_id': f'CLUSTER_{i}', 'risk_level': 'High'} for i in range(5)])
    
    return df, high_risk, clusters

# OpenAI Integration
def setup_openai():
    """Setup Azure OpenAI client"""
    try:
        # Azure OpenAI Configuration
        endpoint = os.getenv('AZURE_OPENAI_ENDPOINT') or st.secrets.get('AZURE_OPENAI_ENDPOINT', 'https://pbjai.openai.azure.com/')
        api_key = os.getenv('AZURE_OPENAI_API_KEY') or st.secrets.get('AZURE_OPENAI_API_KEY', '41JZvwVKYSZpbfhPX3dteutRygJc0PtiL5VdirvyQqDQ9XpF7521JQQJ99BBACHYHv6XJ3w3AAABACOGn6E')
        api_version = os.getenv('AZURE_OPENAI_API_VERSION') or st.secrets.get('AZURE_OPENAI_API_VERSION', '2024-08-01-preview')
        
        if api_key and endpoint:
            client = AzureOpenAI(
                api_key=api_key,
                api_version=api_version,
                azure_endpoint=endpoint
            )
            return client
        else:
            return None
    except Exception as e:
        st.error(f"Error setting up Azure OpenAI: {str(e)}")
        return None

def generate_ai_analysis(client, data_context, user_query):
    """Generate AI-powered analysis using Azure OpenAI"""
    if not client:
        return "AI Assistant tidak tersedia. Pastikan Azure OpenAI sudah dikonfigurasi dengan benar."
    
    try:
        prompt = f"""
        Anda adalah AI Assistant untuk sistem JALAK-HIJAU yang mendeteksi kejahatan lingkungan dan pencucian uang di Indonesia.
        
        Konteks data:
        {data_context}
        
        Pertanyaan user: {user_query}
        
        Berikan analisis yang spesifik, actionable, dan dalam bahasa Indonesia. 
        Fokus pada:
        1. Pola mencurigakan yang terdeteksi
        2. Rekomendasi investigasi konkret
        3. Risiko yang perlu ditindaklanjuti
        4. Langkah-langkah investigasi selanjutnya
        
        Berikan respons dalam format yang mudah dibaca dengan bullet points dan struktur yang jelas.
        """
        
        # Use Azure OpenAI with the specific deployment
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # This should match your deployment name
            messages=[
                {"role": "system", "content": "Anda adalah expert analyst untuk PPATK Indonesia yang spesialis dalam mendeteksi environmental crime dan money laundering."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=800,
            temperature=0.7
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        return f"Error dalam analisis AI: {str(e)}. Periksa konfigurasi Azure OpenAI."

# Dashboard components
def create_overview_dashboard():
    """Main overview dashboard"""
    st.markdown("""
    <div class="main-header">
        <h1>🛰️ JALAK-HIJAU</h1>
        <h3>Environmental Crime Detection System</h3>
        <p>Sistem Deteksi Kejahatan Lingkungan & Pencucian Uang Terintegrasi</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Load data
    forest_gdf, palm_gdf = load_geospatial_data()
    companies_df = load_company_data()
    transactions_df, high_risk_df, clusters_df = load_transaction_data()
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        overlapping_areas = len([p for p in palm_gdf.to_dict('records') if p.get('overlaps_forest', False)])
        st.metric(
            label="🚨 Area Overlap Terdeteksi",
            value=f"{overlapping_areas}",
            delta="Kritis"
        )
    
    with col2:
        high_risk_companies = len(companies_df[companies_df.get('risk_score', 0) > 70])
        st.metric(
            label="🏢 Perusahaan Berisiko Tinggi",
            value=f"{high_risk_companies}",
            delta="+2 hari ini"
        )
    
    with col3:
        flagged_transactions = len(high_risk_df) if isinstance(high_risk_df, pd.DataFrame) else 0
        st.metric(
            label="💰 Transaksi Mencurigakan",
            value=f"{flagged_transactions}",
            delta="Minggu ini"
        )
    
    with col4:
        avg_detection_time = "6 hari"
        st.metric(
            label="⏱️ Rata-rata Waktu Deteksi",
            value=avg_detection_time,
            delta="-8 hari vs sebelumnya",
            delta_color="inverse"
        )
    
    # Main map
    st.subheader("🗺️ Peta Risiko Lingkungan Real-time")
    
    # Create folium map
    center_lat, center_lon = -2.5, 118.0  # Indonesia center
    m = folium.Map(location=[center_lat, center_lon], zoom_start=5, tiles='OpenStreetMap')
    
    # Add forest boundaries (green)
    for idx, forest in forest_gdf.iterrows():
        if hasattr(forest.geometry, 'centroid'):
            center = forest.geometry.centroid
            folium.CircleMarker(
                location=[center.y, center.x],
                radius=8,
                popup=f"Hutan Lindung: {forest.get('name', 'Unknown')}",
                color='green',
                fill=True,
                fillColor='green',
                fillOpacity=0.3
            ).add_to(m)
    
    # Add palm concessions with risk coloring
    for idx, palm in palm_gdf.iterrows():
        if 'lat' in palm and 'lon' in palm:
            color = 'red' if palm.get('overlaps_forest', False) else 'orange'
            risk_level = 'TINGGI - Overlap dengan hutan lindung' if palm.get('overlaps_forest', False) else 'SEDANG'
            
            folium.CircleMarker(
                location=[palm['lat'], palm['lon']],
                radius=12,
                popup=f"""
                <b>{palm.get('company', 'Unknown Company')}</b><br>
                Luas: {palm.get('area_ha', 0):,} ha<br>
                Status Risiko: {risk_level}<br>
                Permit: {palm.get('permit_status', 'Unknown')}
                """,
                color=color,
                fill=True,
                fillColor=color,
                fillOpacity=0.7
            ).add_to(m)
    
    # Display map
    map_data = st_folium(m, width=700, height=500)
    
    # Alert feed
    st.subheader("🚨 Feed Alert Terkini")
    
    alerts = [
        {
            'id': 'ALT-2024-0156',
            'time': '14:23 WIB',
            'location': 'Riau Province',
            'type': 'Overlap Konsesi-Hutan Lindung',
            'risk': 'CRITICAL',
            'company': 'PT BERKAH SAWIT NUSANTARA'
        },
        {
            'id': 'ALT-2024-0157',
            'time': '13:45 WIB',
            'location': 'Kalimantan Selatan',
            'type': 'Transaksi Mencurigakan',
            'risk': 'HIGH',
            'company': 'PT HIJAU SEJAHTERA ABADI'
        },
        {
            'id': 'ALT-2024-0158',
            'time': '12:30 WIB',
            'location': 'Sumatera Utara',
            'type': 'Pembukaan Lahan Baru',
            'risk': 'MEDIUM',
            'company': 'PT CAHAYA PALM MANDIRI'
        }
    ]
    
    for alert in alerts:
        risk_class = f"risk-{alert['risk'].lower()}"
        alert_class = "alert-critical" if alert['risk'] == 'CRITICAL' else "alert-warning"
        
        st.markdown(f"""
        <div class="{alert_class}">
            <strong>🚨 Alert {alert['id']}</strong> - {alert['time']}<br>
            <strong>Lokasi:</strong> {alert['location']}<br>
            <strong>Jenis:</strong> {alert['type']}<br>
            <strong>Perusahaan:</strong> {alert['company']}<br>
            <strong>Risk Level:</strong> <span class="{risk_class}">{alert['risk']}</span>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button(f"🔍 Investigasi Alert {alert['id']}", key=f"investigate_{alert['id']}"):
            st.session_state.selected_alert = alert['id']
            st.session_state.investigation_mode = True
            st.rerun()

def create_geospatial_analysis():
    """Geospatial analysis page"""
    st.header("🗺️ Analisis Geospasial")
    st.subheader("Deteksi Overlap Konsesi Sawit vs Hutan Lindung")
    
    # Load data
    forest_gdf, palm_gdf = load_geospatial_data()
    
    # Analysis options
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Filter & Kontrol")
        
        # Province filter
        provinces = ['Semua Provinsi', 'Riau', 'Kalimantan Selatan', 'Sumatera Utara', 'Kalimantan Tengah']
        selected_province = st.selectbox("Pilih Provinsi", provinces)
        
        # Risk level filter
        risk_levels = ['Semua Level', 'Critical', 'High', 'Medium', 'Low']
        selected_risk = st.selectbox("Level Risiko", risk_levels)
        
        # Date range
        date_range = st.date_input(
            "Periode Analisis",
            value=[datetime.now() - timedelta(days=30), datetime.now()],
            max_value=datetime.now()
        )
        
        # Overlap threshold
        overlap_threshold = st.slider("Minimum Overlap (%)", 0, 100, 10)
        
        st.markdown("### 📊 Statistik Overlap")
        
        # Calculate statistics
        total_palm_areas = len(palm_gdf)
        overlapping_areas = len([p for p in palm_gdf.to_dict('records') if p.get('overlaps_forest', False)])
        overlap_percentage = (overlapping_areas / total_palm_areas) * 100 if total_palm_areas > 0 else 0
        
        st.metric("Total Konsesi Sawit", total_palm_areas)
        st.metric("Konsesi Overlap", overlapping_areas)
        st.metric("Persentase Overlap", f"{overlap_percentage:.1f}%")
        
    with col2:
        st.subheader("Peta Analisis Overlap")
        
        # Create detailed analysis map
        center_lat, center_lon = -2.5, 118.0
        m = folium.Map(location=[center_lat, center_lon], zoom_start=6)
        
        # Add forest areas (green overlay)
        for idx, forest in forest_gdf.iterrows():
            if hasattr(forest.geometry, 'centroid'):
                center = forest.geometry.centroid
                folium.Circle(
                    location=[center.y, center.x],
                    radius=50000,  # 50km radius for visualization
                    popup=f"Hutan Lindung: {forest.get('name', 'Protected Forest')}",
                    color='green',
                    fill=True,
                    fillColor='green',
                    fillOpacity=0.2,
                    weight=2
                ).add_to(m)
        
        # Add palm concessions with detailed info
        for idx, palm in palm_gdf.iterrows():
            if 'lat' in palm and 'lon' in palm:
                overlaps = palm.get('overlaps_forest', False)
                
                if overlaps:
                    color = 'red'
                    risk_status = 'CRITICAL - Overlap Terdeteksi'
                    icon_color = 'red'
                else:
                    color = 'blue'
                    risk_status = 'Normal'
                    icon_color = 'blue'
                
                # Create detailed popup
                popup_html = f"""
                <div style="width: 300px;">
                    <h4>{palm.get('company', 'Unknown Company')}</h4>
                    <hr>
                    <b>Luas Konsesi:</b> {palm.get('area_ha', 0):,} ha<br>
                    <b>Status Permit:</b> {palm.get('permit_status', 'Unknown')}<br>
                    <b>Risk Level:</b> <span style="color: {color}; font-weight: bold;">{risk_status}</span><br>
                    <b>Koordinat:</b> {palm['lat']:.4f}, {palm['lon']:.4f}<br>
                    {"<b style='color: red;'>⚠️ OVERLAP DENGAN HUTAN LINDUNG</b>" if overlaps else ""}
                </div>
                """
                
                folium.Marker(
                    location=[palm['lat'], palm['lon']],
                    popup=folium.Popup(popup_html, max_width=300),
                    icon=folium.Icon(color=icon_color, icon='tree' if overlaps else 'leaf')
                ).add_to(m)
        
        # Display map
        map_data = st_folium(m, width=700, height=600)
        
        # Analysis results table
        st.subheader("📋 Detail Konsesi Berisiko")
        
        # Create analysis DataFrame
        analysis_data = []
        for idx, palm in palm_gdf.iterrows():
            if palm.get('overlaps_forest', False):
                analysis_data.append({
                    'Perusahaan': palm.get('company', 'Unknown'),
                    'Luas (ha)': f"{palm.get('area_ha', 0):,}",
                    'Status': 'OVERLAP DETECTED',
                    'Risk Score': np.random.randint(85, 98),
                    'Koordinat': f"{palm.get('lat', 0):.4f}, {palm.get('lon', 0):.4f}",
                    'Tindakan': 'Investigasi Prioritas'
                })
        
        if analysis_data:
            df_analysis = pd.DataFrame(analysis_data)
            st.dataframe(df_analysis, use_container_width=True)
            
            # Export options
            csv = df_analysis.to_csv(index=False)
            st.download_button(
                label="📥 Download Laporan CSV",
                data=csv,
                file_name=f"overlap_analysis_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        else:
            st.info("Tidak ada overlap yang terdeteksi dengan filter saat ini.")

def create_company_network():
    """Company network analysis page"""
    st.header("🏢 Analisis Jaringan Perusahaan")
    st.subheader("Deteksi Shell Company & Beneficial Ownership")
    
    # Load company data
    companies_df = load_company_data()
    transactions_df, high_risk_df, clusters_df = load_transaction_data()
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("🎯 Perusahaan Target")
        
        # Company selector
        company_list = companies_df['nama_perseroan'].tolist() if 'nama_perseroan' in companies_df.columns else []
        selected_company = st.selectbox("Pilih Perusahaan untuk Analisis", company_list)
        
        if selected_company:
            # Get company details
            company_info = companies_df[companies_df['nama_perseroan'] == selected_company].iloc[0]
            
            st.markdown("### 📊 Profile Perusahaan")
            
            risk_score = company_info.get('risk_score', 0)
            risk_color = 'red' if risk_score > 70 else 'orange' if risk_score > 40 else 'green'
            
            st.markdown(f"""
            <div class="metric-card">
                <h4>{selected_company}</h4>
                <p><strong>Risk Score:</strong> <span style="color: {risk_color}; font-weight: bold;">{risk_score}/100</span></p>
                <p><strong>Modal Disetor:</strong> Rp {company_info.get('modal_disetor', 0):,}</p>
                <p><strong>Status:</strong> {'Suspicious' if company_info.get('is_suspicious', False) else 'Normal'}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Risk factors
            st.markdown("### ⚠️ Faktor Risiko")
            
            if company_info.get('is_suspicious', False):
                st.markdown("""
                - 🔴 **Perusahaan baru** (< 6 bulan)
                - 🔴 **Modal disetor rendah** (< 30% dari ditempatkan)
                - 🔴 **Pemilik saham kompleks** (nominee structure)
                - 🔴 **Aktivitas tidak sesuai KBLI**
                """)
            else:
                st.markdown("""
                - 🟢 **Perusahaan established** (> 2 tahun)
                - 🟢 **Modal disetor memadai**
                - 🟢 **Struktur kepemilikan transparan**
                - 🟢 **Aktivitas sesuai izin**
                """)
    
    with col2:
        st.subheader("🕸️ Network Graph")
        
        # Create network graph
        G = nx.Graph()
        
        # Add nodes for companies
        for idx, company in companies_df.iterrows():
            node_color = 'red' if company.get('is_suspicious', False) else 'lightblue'
            G.add_node(
                company['nama_perseroan'], 
                color=node_color,
                size=company.get('risk_score', 30),
                type='company'
            )
        
        # Add some relationships (demo)
        suspicious_companies = companies_df[companies_df.get('is_suspicious', False) == True]['nama_perseroan'].tolist()
        if len(suspicious_companies) > 1:
            for i in range(len(suspicious_companies) - 1):
                G.add_edge(suspicious_companies[i], suspicious_companies[i + 1], weight=0.8)
        
        # Create plotly network visualization
        pos = nx.spring_layout(G, k=3, iterations=50)
        
        # Extract edges
        edge_x = []
        edge_y = []
        for edge in G.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])
        
        # Extract nodes
        node_x = []
        node_y = []
        node_text = []
        node_colors = []
        node_sizes = []
        
        for node in G.nodes():
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)
            node_text.append(node)
            
            # Get node attributes
            node_data = companies_df[companies_df['nama_perseroan'] == node]
            if len(node_data) > 0:
                is_suspicious = node_data.iloc[0].get('is_suspicious', False)
                risk_score = node_data.iloc[0].get('risk_score', 30)
                node_colors.append('red' if is_suspicious else 'lightblue')
                node_sizes.append(max(15, risk_score / 3))
            else:
                node_colors.append('lightblue')
                node_sizes.append(15)
        
        # Create plotly figure
        fig = go.Figure()
        
        # Add edges
        fig.add_trace(go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(width=2, color='gray'),
            hoverinfo='none',
            mode='lines'
        ))
        
        # Add nodes
        fig.add_trace(go.Scatter(
            x=node_x, y=node_y,
            mode='markers+text',
            hoverinfo='text',
            text=node_text,
            textposition="middle center",
            marker=dict(
                size=node_sizes,
                color=node_colors,
                line=dict(width=2, color='white')
            ),
            hovertext=[f"{node}<br>Risk Score: {companies_df[companies_df['nama_perseroan']==node].iloc[0].get('risk_score', 0) if len(companies_df[companies_df['nama_perseroan']==node]) > 0 else 0}" for node in G.nodes()]
        ))
        
        fig.update_layout(
            title="Network Analysis - Hubungan Antar Perusahaan",
            showlegend=False,
            hovermode='closest',
            margin=dict(b=20,l=5,r=5,t=40),
            annotations=[ dict(
                text="Red nodes = Suspicious companies, Blue nodes = Normal companies",
                showarrow=False,
                xref="paper", yref="paper",
                x=0.005, y=-0.002,
                xanchor='left', yanchor='bottom'
            )],
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Company analysis table
        st.subheader("📋 Analisis Perusahaan Berisiko")
        
        high_risk_companies = companies_df[companies_df.get('risk_score', 0) > 70]
        if len(high_risk_companies) > 0:
            display_df = high_risk_companies[['nama_perseroan', 'risk_score', 'is_suspicious']].copy()
            display_df.columns = ['Nama Perusahaan', 'Risk Score', 'Status Suspicious']
            display_df['Tindakan'] = 'Investigasi Prioritas'
            
            st.dataframe(display_df, use_container_width=True)

def create_financial_analysis():
    """Financial transaction analysis page"""
    st.header("💰 Analisis Transaksi Keuangan")
    st.subheader("Deteksi Pola Mencurigakan & Money Laundering")
    
    # Load transaction data
    transactions_df, high_risk_df, clusters_df = load_transaction_data()
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    total_transactions = len(transactions_df) if isinstance(transactions_df, pd.DataFrame) else 0
    high_risk_count = len(high_risk_df) if isinstance(high_risk_df, pd.DataFrame) else 0
    
    with col1:
        st.metric("Total Transaksi", f"{total_transactions:,}")
    
    with col2:
        st.metric("Transaksi Berisiko Tinggi", f"{high_risk_count:,}")
    
    with col3:
        if isinstance(transactions_df, pd.DataFrame) and 'amount_idr' in transactions_df.columns:
            total_amount = transactions_df['amount_idr'].sum()
            st.metric("Total Nilai", f"Rp {total_amount/1e12:.1f}T")
        else:
            st.metric("Total Nilai", "Rp 125.5T")
    
    with col4:
        suspicious_rate = (high_risk_count / total_transactions * 100) if total_transactions > 0 else 15.3
        st.metric("Tingkat Kecurigaan", f"{suspicious_rate:.1f}%")
    
    # Time series analysis
    st.subheader("📈 Tren Transaksi Mencurigakan")
    
    # Generate demo time series data
    dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='D')
    suspicious_counts = np.random.poisson(12, len(dates))
    
    # Create spikes during palm harvest seasons
    for i, date in enumerate(dates):
        if date.month in [3, 4, 9, 10]:  # Harvest months
            suspicious_counts[i] += np.random.poisson(8)
    
    time_series_df = pd.DataFrame({
        'Tanggal': dates,
        'Transaksi_Mencurigakan': suspicious_counts,
        'Bulan': dates.month
    })
    
    fig_time = px.line(
        time_series_df, 
        x='Tanggal', 
        y='Transaksi_Mencurigakan',
        title='Transaksi Mencurigakan per Hari (2024)',
        color_discrete_sequence=['#FF6B35']
    )
    
    fig_time.update_layout(
        xaxis_title="Tanggal",
        yaxis_title="Jumlah Transaksi Mencurigakan",
        hovermode='x unified'
    )
    
    st.plotly_chart(fig_time, use_container_width=True)
    
    # Risk distribution
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🎯 Distribusi Risk Score")
        
        # Generate risk score data
        risk_scores = np.random.normal(45, 25, 1000)
        risk_scores = np.clip(risk_scores, 0, 100)
        
        fig_hist = px.histogram(
            x=risk_scores,
            nbins=20,
            title="Distribusi Risk Score Transaksi",
            color_discrete_sequence=['#2E8B57']
        )
        
        fig_hist.update_layout(
            xaxis_title="Risk Score",
            yaxis_title="Jumlah Transaksi",
            showlegend=False
        )
        
        st.plotly_chart(fig_hist, use_container_width=True)
    
    with col2:
        st.subheader("💸 Transaksi per Kategori")
        
        categories = ['Normal', 'Structuring', 'Large Suspicious', 'Layering']
        values = [70, 15, 10, 5]
        colors = ['#2E8B57', '#FFA500', '#FF6B35', '#DC3545']
        
        fig_pie = px.pie(
            values=values,
            names=categories,
            title="Kategori Transaksi (%)",
            color_discrete_sequence=colors
        )
        
        st.plotly_chart(fig_pie, use_container_width=True)
    
    # High-risk transactions table
    st.subheader("🚨 Transaksi Berisiko Tinggi")
    
    # Generate demo high-risk transactions
    demo_high_risk = pd.DataFrame({
        'Transaction ID': [f'TXN_{i:06d}' for i in range(1, 11)],
        'Tanggal': pd.date_range('2024-12-01', periods=10, freq='D'),
        'Pengirim': [f'PT Company {i}' for i in range(1, 11)],
        'Penerima': [f'PT Shell {i}' for i in range(1, 11)],
        'Jumlah (IDR)': np.random.randint(45000000, 2000000000, 10),
        'Risk Score': np.random.randint(75, 98, 10),
        'Pattern': np.random.choice(['Structuring', 'Large Transfer', 'Layering'], 10)
    })
    
    # Format currency
    demo_high_risk['Jumlah_Formatted'] = demo_high_risk['Jumlah (IDR)'].apply(lambda x: f"Rp {x:,}")
    demo_high_risk['Risk_Color'] = demo_high_risk['Risk Score'].apply(
        lambda x: '🔴' if x > 90 else '🟠' if x > 80 else '🟡'
    )
    
    display_cols = ['Transaction ID', 'Tanggal', 'Pengirim', 'Penerima', 'Jumlah_Formatted', 'Risk Score', 'Risk_Color', 'Pattern']
    st.dataframe(demo_high_risk[display_cols], use_container_width=True)
    
    # Investigation buttons
    st.subheader("🔍 Tools Investigasi")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📊 Generate Laporan STR"):
            st.success("Laporan STR berhasil digenerate untuk 5 transaksi teratas!")
    
    with col2:
        if st.button("🕸️ Analisis Network"):
            st.info("Menampilkan network analysis untuk entitas terkait...")
    
    with col3:
        if st.button("📈 Prediksi Trend"):
            st.warning("Prediksi: Peningkatan aktivitas mencurigakan bulan depan (+15%)")

def create_ai_assistant():
    """AI-powered assistant page"""
    st.header("🤖 AI Assistant JALAK-HIJAU")
    st.subheader("Analisis Cerdas & Rekomendasi Investigasi")
    
    # Setup OpenAI client
    client = setup_openai()
    
    # AI Assistant interface
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("💬 Chat dengan AI Assistant")
        
        # Chat history display
        chat_container = st.container()
        
        with chat_container:
            for i, chat in enumerate(st.session_state.chat_history):
                if chat['role'] == 'user':
                    st.markdown(f"""
                    <div style="background-color: #E8F5E8; padding: 10px; border-radius: 10px; margin: 5px 0;">
                        <strong>👤 Anda:</strong> {chat['content']}
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div style="background-color: #F0F8FF; padding: 10px; border-radius: 10px; margin: 5px 0;">
                        <strong>🤖 AI Assistant:</strong> {chat['content']}
                    </div>
                    """, unsafe_allow_html=True)
        
        # Chat input
        user_query = st.text_input("Tanya AI Assistant:", placeholder="Contoh: Analisis PT BERKAH SAWIT NUSANTARA")
        
        col_send, col_clear = st.columns([1, 4])
        
        with col_send:
            if st.button("📤 Kirim"):
                if user_query:
                    # Add user message to history
                    st.session_state.chat_history.append({'role': 'user', 'content': user_query})
                    
                    # Generate AI response
                    data_context = """
                    Data context: JALAK-HIJAU memiliki data transaksi mencurigakan, 
                    perusahaan berisiko tinggi, dan area overlap konsesi sawit dengan hutan lindung.
                    Sistem mendeteksi 15% perusahaan dengan pola shell company dan 
                    transaksi strukturing senilai Rp 125T.
                    """
                    
                    ai_response = generate_ai_analysis(client, data_context, user_query)
                    
                    # Add AI response to history
                    st.session_state.chat_history.append({'role': 'assistant', 'content': ai_response})
                    
                    st.rerun()
        
        with col_clear:
            if st.button("🗑️ Clear Chat"):
                st.session_state.chat_history = []
                st.rerun()
    
    with col2:
        st.subheader("🎯 Quick Actions")
        
        # Pre-defined queries
        quick_queries = [
            "Jelaskan pola mencurigakan PT BERKAH SAWIT",
            "Analisis transaksi strukturing hari ini",
            "Perusahaan mana yang paling berisiko?",
            "Generate laporan investigasi",
            "Prediksi tren pencucian uang",
            "Rekomendasi prioritas investigasi"
        ]
        
        for query in quick_queries:
            if st.button(f"💡 {query}", key=f"quick_{hash(query)}"):
                # Add to chat and process
                st.session_state.chat_history.append({'role': 'user', 'content': query})
                
                data_context = "Konteks sistem JALAK-HIJAU dengan data kasus aktual..."
                ai_response = generate_ai_analysis(client, data_context, query)
                
                st.session_state.chat_history.append({'role': 'assistant', 'content': ai_response})
                st.rerun()
        
        st.markdown("---")
        
        # AI capabilities info
        st.subheader("🧠 Kemampuan AI")
        st.markdown("""
        **AI Assistant dapat:**
        - 🔍 Menganalisis pola transaksi mencurigakan
        - 📋 Generate laporan investigasi otomatis
        - 🎯 Memberikan rekomendasi prioritas
        - 🕸️ Mengidentifikasi jaringan shell company
        - 📈 Memprediksi tren kejahatan
        - ⚡ Jawab pertanyaan natural language
        """)
        
        if not client:
            st.warning("⚠️ OpenAI API belum dikonfigurasi. Beberapa fitur AI mungkin tidak tersedia.")
    
    # Auto-generated reports section
    st.subheader("📋 Laporan AI Otomatis")
    
    tab1, tab2, tab3 = st.tabs(["🚨 Alert Analysis", "📊 Risk Assessment", "🎯 Investigation Plan"])
    
    with tab1:
        st.markdown("""
        ### 🚨 Analisis Alert Terkini
        
        **Alert ID:** ALT-2024-0156  
        **Status:** CRITICAL
        
        **AI Analysis:**
        Terdeteksi overlap konsesi PT BERKAH SAWIT NUSANTARA dengan hutan lindung seluas 127 ha. 
        Perusahaan ini menunjukkan pola suspicious:
        
        - ✅ **Incorporated baru:** 2 bulan lalu
        - ✅ **Modal disetor rendah:** Hanya 15% dari modal ditempatkan  
        - ✅ **Transaksi besar:** Rp 45B deposit 1 hari setelah clearing
        - ✅ **Network connection:** Terhubung dengan 4 shell companies
        
        **Rekomendasi:** Investigasi prioritas tinggi, focus pada beneficial owner Ahmad Wijaya.
        """)
    
    with tab2:
        st.markdown("""
        ### 📊 Risk Assessment Komprehensif
        
        **Overall Risk Level:** HIGH (Score: 87/100)
        
        **Risk Breakdown:**
        - **Geospatial Risk:** 95/100 (Overlap critical)
        - **Corporate Risk:** 85/100 (Shell company network)  
        - **Financial Risk:** 82/100 (Structuring patterns)
        - **Temporal Risk:** 78/100 (Timing correlation)
        
        **Predicted Impact:** Kerugian negara estimated Rp 15-25 miliar
        """)
    
    with tab3:
        st.markdown("""
        ### 🎯 Investigation Action Plan
        
        **Phase 1: Data Collection (1-2 hari)**
        1. Kumpulkan semua transaksi PT BERKAH SAWIT (3 bulan terakhir)
        2. Trace beneficial ownership Ahmad Wijaya 
        3. Analisis 4 perusahaan terkait dalam network
        
        **Phase 2: Field Verification (3-5 hari)**  
        1. Verifikasi lokasi overlap via satellite/drone
        2. Cek status izin di KLHK
        3. Koordinasi dengan Pemda setempat
        
        **Phase 3: Financial Investigation (5-7 hari)**
        1. Request bank records semua entitas
        2. Analisis cash flow dan transfer patterns
        3. Identifikasi aset tersembunyi/nominee accounts
        
        **Expected Outcome:** Case ready untuk penyidikan dalam 10 hari
        """)

def create_reports():
    """Reports and export page"""
    st.header("📋 Laporan & Export")
    st.subheader("Generate Laporan Investigasi Otomatis")
    
    # Report types
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Jenis Laporan")
        
        report_types = {
            "STR - Suspicious Transaction Report": "Laporan transaksi mencurigakan untuk PPATK",
            "Environmental Impact Report": "Laporan dampak lingkungan dari overlap konsesi", 
            "Corporate Network Analysis": "Analisis jaringan perusahaan dan beneficial ownership",
            "Financial Flow Investigation": "Pelacakan aliran dana dan money laundering",
            "Executive Summary": "Ringkasan eksekutif untuk pimpinan",
            "Court-Ready Evidence Package": "Paket bukti untuk persidangan"
        }
        
        selected_report = st.selectbox("Pilih Jenis Laporan", list(report_types.keys()))
        st.info(report_types[selected_report])
        
        # Date range
        date_range = st.date_input(
            "Periode Laporan",
            value=[datetime.now() - timedelta(days=30), datetime.now()]
        )
        
        # Case selection
        cases = ["ALT-2024-0156 (PT BERKAH SAWIT)", "ALT-2024-0157 (PT HIJAU SEJAHTERA)", "Semua Kasus Aktif"]
        selected_case = st.selectbox("Pilih Kasus", cases)
        
        # Report format
        formats = ["PDF", "Word Document", "Excel Workbook", "PowerPoint Presentation"]
        selected_format = st.selectbox("Format Output", formats)
        
        # Generate report button
        if st.button("🚀 Generate Laporan", type="primary"):
            with st.spinner("Generating laporan..."):
                import time
                time.sleep(3)  # Simulate processing
                st.success(f"✅ Laporan {selected_report} berhasil digenerate!")
                
                # Show download link
                st.markdown(f"""
                📥 **Download Ready:**
                - Filename: `JALAK_HIJAU_{selected_report.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.{selected_format.split()[0].lower()}`
                - Size: 2.5 MB
                - Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                """)
                
                # Fake download button (for demo)
                st.download_button(
                    label=f"📥 Download {selected_format}",
                    data="Sample report content...",
                    file_name=f"JALAK_HIJAU_Report_{datetime.now().strftime('%Y%m%d')}.txt",
                    mime="text/plain"
                )
    
    with col2:
        st.subheader("📈 Report Preview")
        
        # Sample report preview
        st.markdown("""
        ### 🚨 SUSPICIOUS TRANSACTION REPORT (STR)
        **Report ID:** STR-2024-1205-001  
        **Generated:** 2024-12-05 14:30 WIB  
        **Case:** ALT-2024-0156
        
        ---
        
        #### EXECUTIVE SUMMARY
        Teridentifikasi skema pencucian uang melalui ekspansi ilegal perkebunan kelapa sawit 
        dengan total estimated value **Rp 125 miliar**.
        
        #### KEY FINDINGS
        
        **🏢 Entities Involved:**
        - PT BERKAH SAWIT NUSANTARA (Front Company)
        - PT KARYA UTAMA CONSULTING (Shell Company)  
        - Ahmad Wijaya (Beneficial Owner)
        - 4 Related Corporate Entities
        
        **💰 Financial Pattern:**
        - Total Suspicious Transactions: Rp 125,5 miliar
        - Number of Transactions: 47
        - Time Period: Mar 2024 - Nov 2024
        - Primary Method: Structuring + Layering
        
        **🛰️ Environmental Evidence:**
        - Illegal Expansion: 127 hectares
        - Overlap with Protected Forest: 98%
        - Estimated Timber Value: Rp 15-25 miliar
        
        #### RECOMMENDATIONS
        1. **Immediate freezing** of all accounts
        2. **Criminal investigation** coordination with Polri
        3. **Asset recovery** proceedings
        4. **Environmental restoration** order
        
        ---
        *Report generated by JALAK-HIJAU AI System*
        """)
        
        # Export options
        st.subheader("📤 Export Options")
        
        export_formats = {
            "CSV Data Export": "Raw data dalam format CSV untuk analisis lanjutan",
            "JSON API Export": "Structured data untuk integrasi sistem lain", 
            "GeoJSON Spatial Data": "Data geospasial untuk GIS analysis",
            "Excel Dashboard": "Interactive Excel dengan charts dan pivot tables"
        }
        
        for format_name, description in export_formats.items():
            with st.expander(f"📁 {format_name}"):
                st.write(description)
                
                if st.button(f"Export {format_name}", key=f"export_{format_name}"):
                    st.success(f"✅ {format_name} exported successfully!")

# Main application
def main():
    # Load CSS
    load_css()
    
    # Initialize session state
    init_session_state()
    
    # Sidebar navigation
    st.sidebar.markdown("""
    <div style="text-align: center; padding: 20px;">
        <h2 style="color: white;">🛰️ JALAK-HIJAU</h2>
        <p style="color: white;">Environmental Crime Detection</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Navigation menu
    pages = {
        "🏠 Dashboard Utama": create_overview_dashboard,
        "🗺️ Analisis Geospasial": create_geospatial_analysis,
        "🏢 Network Perusahaan": create_company_network,
        "💰 Analisis Transaksi": create_financial_analysis,
        "🤖 AI Assistant": create_ai_assistant,
        "📋 Laporan & Export": create_reports
    }
    
    selected_page = st.sidebar.selectbox("Pilih Halaman", list(pages.keys()))
    
    # System status
    st.sidebar.markdown("""
    ---
    ### 📊 System Status
    - **🟢 Satellite Feed:** Active
    - **🟢 Transaction Monitor:** Running  
    - **🟢 AI Engine:** Online
    - **🟢 Database:** Connected
    
    ### 📈 Today's Stats
    - **New Alerts:** 3
    - **High Risk Cases:** 12
    - **AI Recommendations:** 8
    """)
    
    # Investigation mode indicator
    if st.session_state.investigation_mode:
        st.sidebar.markdown("""
        ---
        ### 🔍 INVESTIGATION MODE
        **Active Case:** {}
        
        **Status:** In Progress
        """.format(st.session_state.selected_alert or "N/A"))
        
        if st.sidebar.button("❌ Exit Investigation"):
            st.session_state.investigation_mode = False
            st.session_state.selected_alert = None
            st.rerun()
    
    # Credits
    st.sidebar.markdown("""
    ---
    ### 👥 Treasury Data Lab
    **Hackathon PPATK 2024**
    
    Built with ❤️ for Indonesia
    """)
    
    # Execute selected page
    pages[selected_page]()

if __name__ == "__main__":
    main()