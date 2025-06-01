import streamlit as st
import pandas as pd
import numpy as np
import folium
import random
from streamlit_folium import st_folium
import plotly.express as px
import plotly.graph_objects as go
import networkx as nx
from datetime import datetime, timedelta
import json
import geopandas as gpd
from shapely.geometry import Point, Polygon
from openai import AzureOpenAI
import os
from pathlib import Path
from io import BytesIO
import base64

# Page config
st.set_page_config(
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS with improved styling
def load_css():
    st.markdown("""
    <style>
    :root {
        --primary-green: #2E8B57;
        --coral-orange: #FF6B35;
        --alice-blue: #F0F8FF;
        --dark-slate: #2F4F4F;
        --success-green: #28A745;
        --warning-orange: #FFA500;
        --danger-red: #DC3545;
        --investigation-purple: #6A4C93;
    }
    
    .main-header {
        background: linear-gradient(90deg, var(--primary-green), #228B22);
        color: white;
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        text-align: center;
    }
    
    .hero-metrics {
        background: linear-gradient(135deg, #FF6B35, #2E8B57);
        padding: 2rem;
        border-radius: 15px;
        margin: 2rem 0;
        color: white;
        text-align: center;
    }
    
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
    
    .alert-info {
        background-color: #E3F2FD;
        border-left: 5px solid #2196F3;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    
    .investigation-panel {
        background: linear-gradient(135deg, var(--investigation-purple), #DC3545);
        color: white;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    
    .report-panel {
        background: linear-gradient(135deg, #4A90E2, #357ABD);
        color: white;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        border-left: 5px solid var(--primary-green);
        margin: 1rem 0;
    }
    
    .risk-high { color: var(--danger-red); font-weight: bold; }
    .risk-medium { color: var(--warning-orange); font-weight: bold; }
    .risk-low { color: var(--success-green); font-weight: bold; }
    
    .live-detection {
        animation: pulse 2s infinite;
        background: #FFE6E6;
        border: 2px solid #DC3545;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    .berkah-highlight {
        background: linear-gradient(135deg, #FF6B35, #DC3545);
        color: white;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        border: 2px solid #FF4444;
    }
    
    @keyframes pulse {
        0% { box-shadow: 0 0 0 0 rgba(220, 53, 69, 0.7); }
        70% { box-shadow: 0 0 0 10px rgba(220, 53, 69, 0); }
        100% { box-shadow: 0 0 0 0 rgba(220, 53, 69, 0); }
    }
    
    .nav-button {
        width: 100%;
        margin: 0.2rem 0;
        background: linear-gradient(45deg, #2E8B57, #228B22);
        color: white;
        border: none;
        padding: 0.8rem;
        border-radius: 8px;
        font-weight: bold;
    }
    
    .nav-button:hover {
        background: linear-gradient(45deg, #228B22, #2E8B57);
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
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
    if 'investigation_data' not in st.session_state:
        st.session_state.investigation_data = {}
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "🏠 Dashboard Overview"

# Data loading functions
@st.cache_data
def load_geospatial_data():
    """Load geospatial data with PT BERKAH focus"""
    try:
        forest_gdf = gpd.read_file("forest.shp")
        sawit_gdf = gpd.read_file("sawit.shp")
        overlap_gdf = gpd.read_file("overlap.shp")
        st.success("✅ Loaded actual shapefiles successfully!")
        return forest_gdf, sawit_gdf, overlap_gdf
    except Exception as e:
        #st.warning(f"⚠️ Shapefiles not found, using demo data. Error: {str(e)}")
        return generate_realistic_geodata_with_berkah()

@st.cache_data
def load_financial_data():
    """Load financial data with PT BERKAH case study"""
    data_dir = Path("data")
    
    if not data_dir.exists():
        st.warning("⚠️ Data directory not found. Run financial_data_generator.py first.")
        return generate_demo_financial_data()
    
    try:
        transactions_df = pd.read_csv(data_dir / "transactions.csv")
        high_risk_df = pd.read_csv(data_dir / "transactions_high_risk.csv")
        clusters_df = pd.read_csv(data_dir / "transactions_clusters.csv")
        bank_accounts_df = pd.read_csv(data_dir / "bank_accounts.csv")
        
        # Convert date columns
        transactions_df['transaction_date'] = pd.to_datetime(transactions_df['transaction_date'])
        high_risk_df['transaction_date'] = pd.to_datetime(high_risk_df['transaction_date'])
        
        # Load PT BERKAH case study if available
        berkah_case_df = None
        try:
            berkah_case_df = pd.read_csv(data_dir / "pt_berkah_case_study.csv")
            berkah_case_df['transaction_date'] = pd.to_datetime(berkah_case_df['transaction_date'])
            #st.success(f"✅ Loaded PT BERKAH case study: {len(berkah_case_df)} transactions")
        except:
            pass
        
        #st.success(f"✅ Loaded financial data: {len(transactions_df):,} transactions, {len(high_risk_df):,} high-risk")
        return transactions_df, high_risk_df, clusters_df, bank_accounts_df, berkah_case_df
        
    except Exception as e:
        st.warning(f"⚠️ Error loading financial data: {str(e)}")
        return generate_demo_financial_data()

@st.cache_data  
def load_company_data():
    """Load company data with PT BERKAH highlighted"""
    data_dir = Path("data")
    
    try:
        pt_df = pd.read_csv(data_dir / "pt_data.csv")
        #st.success(f"✅ Loaded {len(pt_df)} companies from generated data")
        return pt_df
    except:
        try:
            pt_df = pd.read_csv("pt_data.csv")
            st.success(f"✅ Loaded {len(pt_df)} companies from pt_data.csv")
            return pt_df
        except:
            st.warning("⚠️ No company data found, using demo data")
            return generate_demo_companies_with_berkah()

def generate_realistic_geodata_with_berkah():
    """Generate geospatial data highlighting PT BERKAH case"""
    regions = {
        'Riau': {'center': [0.5, 101.4], 'bbox': [(-1, 100), (2, 103)]},
        'Kalimantan Selatan': {'center': [-2.2, 115.0], 'bbox': [(-4, 113), (-1, 117)]},
    }
    
    forest_areas = []
    sawit_concessions = []
    overlap_areas = []
    
    # Create PT BERKAH specific case in Riau
    center_lat, center_lon = 0.5, 101.4
    
    # Protected forest area
    forest_lat, forest_lon = center_lat + 0.2, center_lon + 0.3
    forest_polygon = Point(forest_lon, forest_lat).buffer(0.15)
    
    forest_areas.append({
        'geometry': forest_polygon,
        'name': 'Hutan Lindung Riau Tengah',
        'region': 'Riau',
        'status': 'Protected',
        'area_ha': 16700,
        'center_lat': forest_lat,
        'center_lon': forest_lon
    })
    
    # PT BERKAH concession overlapping with forest
    berkah_lat, berkah_lon = forest_lat + 0.02, forest_lon - 0.01
    berkah_polygon = Point(berkah_lon, berkah_lat).buffer(0.12)
    
    sawit_concessions.append({
        'geometry': berkah_polygon,
        'company': 'PT SAWIT NUSANTARA',
        'region': 'Riau',
        'permit_status': 'Active',
        'area_ha': 14500,
        'center_lat': berkah_lat,
        'center_lon': berkah_lon,
        'overlap_percentage': 35.2,
        'is_overlapping': True,
        'risk_score': 95
    })
    
    # Overlap area
    overlap_polygon = Point(berkah_lon, berkah_lat).buffer(0.08)
    overlap_areas.append({
        'geometry': overlap_polygon,
        'company': 'PT SAWIT NUSANTARA',
        'forest_area': 'Hutan Lindung Riau Tengah',
        'overlap_ha': 5100,
        'overlap_percentage': 35.2,
        'severity': 'CRITICAL',
        'center_lat': berkah_lat,
        'center_lon': berkah_lon
    })
    
    # Add other normal concessions
    for region_name, region_data in regions.items():
        center_lat, center_lon = region_data['center']
        
        for i in range(8):
            lat = center_lat + np.random.uniform(-0.8, 0.8)
            lon = center_lon + np.random.uniform(-1.2, 1.2)
            size = np.random.uniform(0.05, 0.15)
            
            if i < 2:  # Some additional overlaps
                overlap_pct = np.random.uniform(0.1, 0.25)
                risk_score = np.random.randint(70, 85)
            else:
                overlap_pct = 0
                risk_score = np.random.randint(20, 40)
            
            company_id = f"PT SAWIT {region_name.upper()} {i+1:02d}"
            
            sawit_polygon = Point(lon, lat).buffer(size)
            sawit_concessions.append({
                'geometry': sawit_polygon,
                'company': company_id,
                'region': region_name,
                'permit_status': 'Active',
                'area_ha': int(size * 111000 * 111000),
                'center_lat': lat,
                'center_lon': lon,
                'overlap_percentage': overlap_pct * 100,
                'is_overlapping': overlap_pct > 0,
                'risk_score': risk_score
            })
    
    forest_gdf = gpd.GeoDataFrame(forest_areas)
    sawit_gdf = gpd.GeoDataFrame(sawit_concessions)
    overlap_gdf = gpd.GeoDataFrame(overlap_areas)
    
    return forest_gdf, sawit_gdf, overlap_gdf

def generate_demo_financial_data():
    """Generate demo financial data with PT BERKAH case"""
    # Return placeholder data structure
    transactions_df = pd.DataFrame()
    high_risk_df = pd.DataFrame()
    clusters_df = pd.DataFrame()
    bank_accounts_df = pd.DataFrame()
    berkah_case_df = pd.DataFrame()
    
    return transactions_df, high_risk_df, clusters_df, bank_accounts_df, berkah_case_df

def generate_demo_companies_with_berkah():
    """Generate demo company data with PT BERKAH highlighted"""
    companies = [
        {
            'company_id': 'PALM_001',
            'nama_perseroan': 'PT SAWIT NUSANTARA',
            'is_suspicious': True,
            'risk_score': 95,
            'direktur_utama': 'Ahmad Wijaya',
            'direktur_nik': '1471010101800001'
        }
    ]
    
    return pd.DataFrame(companies)

# OpenAI Integration
def setup_openai():
    """Setup Azure OpenAI client"""
    try:
        endpoint = os.getenv('AZURE_OPENAI_ENDPOINT') or st.secrets.get('AZURE_OPENAI_ENDPOINT')
        api_key = os.getenv('AZURE_OPENAI_API_KEY') or st.secrets.get('AZURE_OPENAI_API_KEY')
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
    """Generate AI-powered analysis"""
    if not client:
        return "AI Assistant tidak tersedia. Pastikan Azure OpenAI sudah dikonfigurasi dengan benar."
    
    try:
        prompt = f"""
        Anda adalah AI Assistant untuk sistem JALAK-HIJAU yang mendeteksi kejahatan lingkungan dan pencucian uang di Indonesia.
        
        Konteks data: {data_context}
        Pertanyaan user: {user_query}
        
        Berikan analisis yang spesifik, actionable, dan dalam bahasa Indonesia. 
        Fokus pada:
        1. Pola mencurigakan yang terdeteksi
        2. Rekomendasi investigasi konkret
        3. Risiko yang perlu ditindaklanjuti
        4. Langkah-langkah investigasi selanjutnya
        """
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
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

# Investigation Mode Functions
def start_investigation(alert_id, alert_data):
    """Initialize investigation mode"""
    st.session_state.investigation_mode = True
    st.session_state.selected_alert = alert_id
    
    investigation_data = {
        'alert_id': alert_id,
        'status': 'ACTIVE',
        'priority': 'CRITICAL' if 'BERKAH' in alert_data.get('company', '') else 'HIGH',
        'assigned_to': 'Tim Investigasi PPATK',
        'start_date': datetime.now(),
        'case_summary': alert_data,
        'evidence_collected': [],
        'next_actions': [],
        'timeline': []
    }
    
    # Special handling for PT BERKAH case
    if 'BERKAH' in alert_data.get('company', ''):
        investigation_data['evidence_collected'] = [
            '🛰️ Citra satelit: overlap 35.2% dengan Hutan Lindung Riau (5,100 ha)',
            '💰 Transfer Rp 45M ke PT KARYA UTAMA CONSULTING sehari setelah clearing',
            '🔗 Beneficial owner sama: Ahmad Wijaya (NIK: 1471010101800001)',
            '📊 Pola structuring: 5 transaksi @Rp 400-499M dalam 5 hari',
            '🏢 Shell company: modal disetor rendah, alamat berbeda'
        ]
        investigation_data['next_actions'] = [
            '🔍 Verifikasi lapangan koordinat overlap (0.52°S, 101.43°E)',
            '📞 Koordinasi dengan KLHK untuk status izin HGU',
            '🏦 Request rekening koran PT BERKAH dan PT KARYA UTAMA',
            '👤 Background check Ahmad Wijaya - kepemilikan multi-entity',
            '⚖️ Persiapan STR dan koordinasi dengan Kejaksaan'
        ]
    else:
        # General case evidence
        investigation_data['evidence_collected'] = [
            '💰 Transfer mencurigakan terdeteksi sistem',
            '📊 Pola transaksi tidak wajar',
            '🔗 Potensi jaringan shell company'
        ]
        investigation_data['next_actions'] = [
            '🔍 Analisis mendalam pola transaksi',
            '📋 Trace beneficial ownership',
            '🏦 Review rekening koran terkait'
        ]
    
    st.session_state.investigation_data = investigation_data

def create_investigation_dashboard():
    """Create investigation mode dashboard"""
    if not st.session_state.investigation_mode:
        st.error("Investigation mode not active!")
        return
    
    inv_data = st.session_state.investigation_data
    
    # Special header for PT BERKAH case
    if 'BERKAH' in inv_data.get('case_summary', {}).get('company', ''):
        st.markdown(f"""
        <div class="berkah-highlight">
            <h2>🔥 CRITICAL INVESTIGATION - {inv_data['alert_id']}</h2>
            <h3>PT SAWIT NUSANTARA - Environmental Crime + Money Laundering</h3>
            <p><strong>Status:</strong> {inv_data['status']} | <strong>Priority:</strong> CRITICAL | <strong>Assigned:</strong> {inv_data['assigned_to']}</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="investigation-panel">
            <h2>🔍 INVESTIGATION MODE - {inv_data['alert_id']}</h2>
            <p><strong>Status:</strong> {inv_data['status']} | <strong>Priority:</strong> {inv_data['priority']} | <strong>Assigned:</strong> {inv_data['assigned_to']}</p>
        </div>
        """, unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📋 Case Overview", "🔍 Evidence", "🎯 Actions", "📊 Analysis", "📄 Generate STR"])
    
    with tab1:
        st.subheader("Case Summary")
        case = inv_data['case_summary']
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"""
            **Alert ID:** {case['id']}  
            **Company:** {case['company']}  
            **Location:** {case['location']}  
            **Risk Level:** <span class="risk-high">{case['risk']}</span>  
            **Type:** {case['type']}
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            **Investigation Start:** {inv_data['start_date'].strftime('%Y-%m-%d %H:%M')}  
            **Days Active:** {(datetime.now() - inv_data['start_date']).days}  
            **Progress:** 65% Complete  
            **Est. Completion:** 3 days
            """)
        
        # PT BERKAH specific timeline
        if 'BERKAH' in case.get('company', ''):
            st.subheader("📅 Case Timeline")
            st.markdown("""
            - **Day -15:** Satellite imagery shows forest clearing activity
            - **Day -14:** PT BERKAH transfers Rp 45B to shell company
            - **Day -13 to -9:** Structuring pattern: 5 transactions under threshold
            - **Day -7 to -3:** Layering through multiple shell companies
            - **Day 0:** JALAK-HIJAU alert triggered
            - **Today:** Investigation initiated
            """)
    
    with tab2:
        st.subheader("🔍 Evidence Collected")
        for i, evidence in enumerate(inv_data['evidence_collected']):
            st.markdown(f"**{i+1}.** {evidence}")
        
        new_evidence = st.text_input("Add New Evidence:")
        if st.button("➕ Add Evidence") and new_evidence:
            inv_data['evidence_collected'].append(f"📝 {new_evidence}")
            st.session_state.investigation_data = inv_data
            st.rerun()
    
    with tab3:
        st.subheader("🎯 Next Actions")
        for i, action in enumerate(inv_data['next_actions']):
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(f"**{i+1}.** {action}")
            with col2:
                if st.button("✅", key=f"complete_{i}"):
                    st.success(f"Action {i+1} marked complete!")
        
        new_action = st.text_input("Add New Action:")
        if st.button("➕ Add Action") and new_action:
            inv_data['next_actions'].append(f"🎯 {new_action}")
            st.session_state.investigation_data = inv_data
            st.rerun()
    
    with tab4:
        # Enhanced network analysis for PT BERKAH
        st.subheader("📊 Investigation Network Analysis")
        
        G = nx.DiGraph()
        
        if 'BERKAH' in case.get('company', ''):
            # PT BERKAH specific network
            G.add_node("Ahmad Wijaya", type="beneficial_owner", risk=95, color="red")
            G.add_node("PT BERKAH SAWIT", type="front_company", risk=95, color="orange")
            G.add_node("PT KARYA UTAMA", type="shell_company", risk=90, color="darkred")
            G.add_node("Hutan Lindung Riau", type="protected_area", risk=100, color="green")
            G.add_node("Bank Account A", type="account", risk=85, color="lightblue")
            G.add_node("Bank Account B", type="account", risk=80, color="lightblue")
            
            G.add_edge("Ahmad Wijaya", "PT BERKAH SAWIT", weight=0.95, relation="100% owner")
            G.add_edge("Ahmad Wijaya", "PT KARYA UTAMA", weight=0.90, relation="hidden owner")
            G.add_edge("PT BERKAH SAWIT", "Hutan Lindung Riau", weight=0.85, relation="illegal overlap")
            G.add_edge("PT BERKAH SAWIT", "Bank Account A", weight=0.90, relation="Rp 45B transfer")
            G.add_edge("Bank Account A", "Bank Account B", weight=0.80, relation="layering")
        else:
            # Generic network
            G.add_node("Company A", type="company", risk=70, color="orange")
            G.add_node("Shell Company", type="shell", risk=85, color="red")
            G.add_node("Bank Account", type="account", risk=75, color="lightblue")
            
            G.add_edge("Company A", "Shell Company", weight=0.8, relation="transfer")
            G.add_edge("Shell Company", "Bank Account", weight=0.7, relation="placement")
        
        # Create network visualization
        pos = nx.spring_layout(G, k=2, iterations=50)
        
        edge_x, edge_y = [], []
        for edge in G.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])
        
        node_x, node_y, node_text, node_colors, node_sizes = [], [], [], [], []
        for node in G.nodes():
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)
            node_text.append(node)
            node_colors.append(G.nodes[node].get('color', 'lightblue'))
            node_sizes.append(max(20, G.nodes[node].get('risk', 50)/3))
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=edge_x, y=edge_y, line=dict(width=2, color='gray'), 
                                hoverinfo='none', mode='lines', showlegend=False))
        fig.add_trace(go.Scatter(x=node_x, y=node_y, mode='markers+text', hoverinfo='text',
                                text=node_text, textposition="bottom center",
                                marker=dict(size=node_sizes, color=node_colors, line=dict(width=2, color='white')),
                                hovertext=[f"{node}<br>Risk: {G.nodes[node].get('risk', 0)}/100" for node in G.nodes()],
                                showlegend=False))
        
        fig.update_layout(title="Suspicious Network - Investigation Focus", showlegend=False, hovermode='closest',
                         xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                         yaxis=dict(showgrid=False, zeroline=False, showticklabels=False), height=400)
        
        st.plotly_chart(fig, use_container_width=True)
    
    with tab5:
        st.subheader("📄 Generate STR Report")
        
        if st.button("🚀 Generate Automatic STR", type="primary"):
            str_content = generate_str_report(inv_data)
            st.markdown("### Generated STR Report:")
            st.text_area("STR Content", str_content, height=400)
            
            # Download button
            st.download_button(
                label="📥 Download STR Report",
                data=str_content,
                file_name=f"STR_{inv_data['alert_id']}_{datetime.now().strftime('%Y%m%d')}.txt",
                mime="text/plain"
            )

def generate_str_report(investigation_data):
    """Generate STR report content"""
    case = investigation_data['case_summary']
    
    if 'BERKAH' in case.get('company', ''):
        report = f"""
SUSPICIOUS TRANSACTION REPORT (STR)
=======================================

ALERT ID: {investigation_data['alert_id']}
DATE: {datetime.now().strftime('%Y-%m-%d')}
PRIORITY: CRITICAL
CASE TYPE: Environmental Crime + Money Laundering

I. EXECUTIVE SUMMARY
-------------------
PT SAWIT NUSANTARA telah melakukan clearing ilegal terhadap Hutan Lindung Riau 
seluas 5,100 ha (35.2% overlap) dan mencuci hasil kejahatan melalui jaringan shell company 
dengan total transaksi mencurigakan Rp 67+ miliar.

II. ENTITIES INVOLVED
--------------------
1. PT SAWIT NUSANTARA
   - NPWP: 73.590.760.9-174.110
   - Direktur: Ahmad Wijaya (NIK: 1471010101800001)
   - Alamat: Jalan Sawit Raya No. 10, Pekanbaru, Riau

2. PT KARYA UTAMA CONSULTING (Shell Company)
   - NPWP: 82.591.670.8-175.210
   - Direktur: Ahmad Wijaya (NIK: 1471010101800001)
   - Alamat: Jalan Sudirman No. 100, Jakarta Pusat

III. SUSPICIOUS TRANSACTIONS
----------------------------
1. TXN_BERKAH_001: Rp 45,000,000,000 (Placement)
   Tanggal: {(datetime.now() - timedelta(days=14)).strftime('%Y-%m-%d')}
   From: PT BERKAH SAWIT → PT KARYA UTAMA CONSULTING

2. Structuring Pattern (5 transactions):
   Total: Rp 2,200,000,000
   Pattern: Amounts just under Rp 500M threshold

IV. ENVIRONMENTAL EVIDENCE
--------------------------
- Satellite imagery confirms illegal forest clearing
- Coordinates: 0.52°S, 101.43°E
- Protected area: Hutan Lindung Riau Tengah
- Overlap area: 5,100 hectares

V. RECOMMENDATION
-----------------
1. Immediate account freeze PT BERKAH & PT KARYA UTAMA
2. Coordinate with KLHK for permit verification
3. Asset tracing for Ahmad Wijaya
4. Criminal investigation for environmental crimes

Prepared by: JALAK-HIJAU System
Investigation Team: PPATK Environmental Crime Unit
"""
    else:
        report = f"""
SUSPICIOUS TRANSACTION REPORT (STR)
=======================================

ALERT ID: {investigation_data['alert_id']}
DATE: {datetime.now().strftime('%Y-%m-%d')}
PRIORITY: {investigation_data['priority']}

SUMMARY: Suspicious transaction pattern detected requiring further investigation.

ENTITIES: {case.get('company', 'Unknown')}
RISK LEVEL: {case.get('risk', 'Unknown')}
TYPE: {case.get('type', 'Unknown')}

RECOMMENDATION: Further investigation recommended.
"""
    
    return report

# Enhanced Dashboard Functions
def create_overview_dashboard():
    """Enhanced overview dashboard with PT BERKAH focus"""
    
    # Load all data
    forest_gdf, sawit_gdf, overlap_gdf = load_geospatial_data()
    financial_data = load_financial_data()
    transactions_df, high_risk_df, clusters_df, bank_accounts_df, berkah_case_df = financial_data
    companies_df = load_company_data()
    
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        critical_overlaps = len(overlap_gdf[overlap_gdf.get('severity', '') == 'CRITICAL']) if len(overlap_gdf) > 0 else 1
        st.metric("🚨 Critical Cases", f"{critical_overlaps}", delta="Real-time Detection")
    
    with col2:
        berkah_amount = 67000000000 if berkah_case_df is not None and len(berkah_case_df) > 0 else 67000000000
        st.metric("💰 Suspicious Amount", f"Rp {berkah_amount/1e9:.0f}B", delta="+1 today")
    
    with col3:
        forest_damage = 5100 if len(overlap_gdf) > 0 else 5100
        st.metric("🌲 Forest Damage", f"{forest_damage:,} ha", delta="Illegal Clearing")
    
    with col4:
        st.metric("⏱️ Detection Time", "< 24 hours", delta="Real-time Alert", delta_color="inverse")
    
    # Full-width map with PT BERKAH focus
    st.subheader("🗺️ Environmental Risk Map")
    
    # Center map on Riau (PT BERKAH location)
    center_lat, center_lon = 0.5, 101.4
    m = folium.Map(location=[center_lat, center_lon], zoom_start=8)
    
    # Add forest areas
    if len(forest_gdf) > 0:
        for idx, forest in forest_gdf.iterrows():
            if hasattr(forest, 'center_lat') and hasattr(forest, 'center_lon'):
                folium.CircleMarker(
                    location=[forest.center_lat, forest.center_lon],
                    radius=12,
                    popup=f"🌲 {forest.get('name', 'Protected Forest')}<br>Status: {forest.get('status', 'Protected')}<br>Area: {forest.get('area_ha', 0):,} ha",
                    color='green', fill=True, fillColor='green', fillOpacity=0.6
                ).add_to(m)
    
    # Add palm concessions with PT BERKAH highlighted
    if len(sawit_gdf) > 0:
        for idx, sawit in sawit_gdf.iterrows():
            if hasattr(sawit, 'center_lat') and hasattr(sawit, 'center_lon'):
                is_berkah = 'BERKAH' in sawit.get('company', '')
                is_overlapping = sawit.get('is_overlapping', False)
                risk_score = sawit.get('risk_score', 30)
                
                if is_berkah:
                    color, risk_level, icon = 'red', 'CRITICAL', 'exclamation-triangle'
                    popup_extra = ""
                elif is_overlapping or risk_score > 70:
                    color, risk_level, icon = 'orange', 'HIGH', 'warning'
                    popup_extra = ""
                else:
                    color, risk_level, icon = 'blue', 'LOW', 'leaf'
                    popup_extra = ""
                
                folium.Marker(
                    location=[sawit.center_lat, sawit.center_lon],
                    popup=f"""<div style="width: 350px;">
                        <h4>🏭 {sawit.get('company', 'Palm Company')}</h4><hr>
                        <b>Region:</b> {sawit.get('region', 'Unknown')}<br>
                        <b>Area:</b> {sawit.get('area_ha', 0):,} ha<br>
                        <b>Risk Score:</b> {risk_score}/100<br>
                        <b>Risk Level:</b> <span style="color: {color}; font-weight: bold;">{risk_level}</span><br>
                        {"<b style='color: red;'>⚠️ OVERLAPS WITH PROTECTED FOREST</b><br>" if is_overlapping else ""}
                        <b>Overlap:</b> {sawit.get('overlap_percentage', 0):.1f}%{popup_extra}</div>""",
                    icon=folium.Icon(color=color, icon=icon)
                ).add_to(m)
    
    # Display map
    map_data = st_folium(m, width=None, height=500)
    
    
    # Enhanced alert feed
    st.subheader("🚨 Live Alert Feed")
    
    alerts = [
        {
            'id': 'ALT-CRIT-001', 'time': '14:23 WIB', 'location': 'Riau Province',
            'type': 'Forest-Concession Overlap + Money Laundering', 'risk': 'CRITICAL',
            'company': 'PT SAWIT NUSANTARA', 
            'details': 'Overlap: 35.2% (5,100 ha) + Rp 67B suspicious transfers',
            'alert_source': 'integrated'
        },
        {
            'id': 'ALT-FIN-002', 'time': '13:45 WIB', 'location': 'Financial Network',
            'type': 'Structuring Pattern', 'risk': 'HIGH',
            'company': 'PT HIJAU SAWIT KALIMANTAN', 
            'details': 'Pattern: 8 transactions < Rp 500M threshold',
            'alert_source': 'financial'
        }
    ]
    
    # Display alerts with PT BERKAH highlighted
    for alert in alerts:
        is_berkah = 'BERKAH' in alert['company']
        alert_class = "berkah-highlight" if is_berkah else ("alert-critical" if alert['risk'] == 'CRITICAL' else "alert-warning")
        risk_class = f"risk-{alert['risk'].lower()}"
        
        icon = '🔥' if is_berkah else ('🛰️' if alert['alert_source'] == 'geospatial' else '💰')
        
        st.markdown(f"""
        <div class="{alert_class}">
            <strong>{icon} Alert {alert['id']}</strong> - {alert['time']}<br>
            <strong>Company:</strong> {alert['company']}<br>
            <strong>Type:</strong> {alert['type']}<br>
            <strong>Details:</strong> {alert.get('details', 'N/A')}<br>
            <strong>Risk Level:</strong> <span class="{risk_class}">{alert['risk']}</span>
            {' <b>🔥 INVESTIGATION ACTIVE</b>' if is_berkah else ''}
        </div>
        """, unsafe_allow_html=True)
        
        if st.button(f"🔍 {'View Investigation' if is_berkah else 'Start Investigation'}", key=f"investigate_{alert['id']}"):
            start_investigation(alert['id'], alert)
            st.success(f"✅ Investigation {alert['id']} {'accessed' if is_berkah else 'started'}!")
            st.rerun()

def create_analysis_page():
    """Enhanced analysis page"""
    st.header("📊 Advanced Analysis Dashboard")
    
    # Load data
    forest_gdf, sawit_gdf, overlap_gdf = load_geospatial_data()
    financial_data = load_financial_data()
    transactions_df, high_risk_df, clusters_df, bank_accounts_df, berkah_case_df = financial_data
    companies_df = load_company_data()
    
    # PT BERKAH case highlight
    if berkah_case_df is not None and len(berkah_case_df) > 0:
        st.markdown("""
        <div class="berkah-highlight">
            <h3>🎯 PT SAWIT NUSANTARA - Featured Case Analysis</h3>
            <p>Complete timeline: Forest clearing → Money laundering → Investigation</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Analysis controls
    col1, col2, col3 = st.columns(3)
    
    with col1:
        analysis_mode = st.selectbox("Analysis Mode", 
                                   ["ALT-CRIT-001", "Comprehensive Overview", "Network Focus"])
    
    with col2:
        risk_filter = st.selectbox("Risk Level", ["All Levels", "Critical Only", "High+"])
    
    with col3:
        time_period = st.selectbox("Time Period", ["Last 30 days", "Last 90 days", "All Time"])
    
    if analysis_mode == "ALT-CRIT-001":
        create_berkah_analysis(berkah_case_df, forest_gdf, sawit_gdf, overlap_gdf)
    else:
        create_general_analysis(transactions_df, high_risk_df, clusters_df)

def create_berkah_analysis(berkah_case_df, forest_gdf, sawit_gdf, overlap_gdf):
    """Detailed PT BERKAH case analysis"""
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🛰️ Geospatial Evidence")
        
        # PT BERKAH specific metrics
        st.metric("🌲 Forest Area Damaged", "5,100 ha", delta="Illegal clearing")
        st.metric("📍 Overlap Percentage", "35.2%", delta="Protected forest")
        st.metric("🚨 Violation Severity", "CRITICAL", delta="Immediate action required")
        
        # Timeline
        st.markdown("#### 📅 Investigation Timeline")
        timeline_data = pd.DataFrame({
            'Date': pd.date_range(start=datetime.now().date() - timedelta(days=15), periods=16),
            'Event': ['Forest clearing detected'] + ['Suspicious transaction']*10 + ['Alert triggered']*5
        })
        
        fig_timeline = px.scatter(timeline_data, x='Date', y='Event', 
                                 title="PT BERKAH Activity Timeline")
        st.plotly_chart(fig_timeline, use_container_width=True)
    
    with col2:
        st.markdown("#### 💰 Financial Evidence")
        
        if berkah_case_df is not None and len(berkah_case_df) > 0:
            total_amount = berkah_case_df['amount_idr'].sum()
            transaction_count = len(berkah_case_df)
        else:
            total_amount = 67000000000
            transaction_count = 12
        
        st.metric("💰 Total Suspicious Amount", f"Rp {total_amount/1e9:.1f}B")
        st.metric("📊 Transaction Count", f"{transaction_count}")
        st.metric("🏢 Entities Involved", "5", delta="Shell companies")
        
        # Money flow diagram
        st.markdown("#### 🔄 Money Flow Pattern")
        flow_data = pd.DataFrame({
            'Stage': ['Placement', 'Layering', 'Integration'],
            'Amount_B': [45, 15, 7],
            'Description': ['Initial transfer to shell', 'Multiple entity transfers', 'Final placement']
        })
        
        fig_flow = px.bar(flow_data, x='Stage', y='Amount_B', 
                         title="Money Laundering Stages (Billion Rp)")
        st.plotly_chart(fig_flow, use_container_width=True)

def create_general_analysis(transactions_df, high_risk_df, clusters_df):
    """General analysis dashboard"""
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📈 Transaction Trends")
        if len(transactions_df) > 0:
            daily_stats = transactions_df.groupby(transactions_df['transaction_date'].dt.date)['amount_idr'].sum().reset_index()
            fig_trend = px.line(daily_stats.tail(30), x='transaction_date', y='amount_idr',
                               title="Daily Transaction Volume")
            st.plotly_chart(fig_trend, use_container_width=True)
        else:
            st.info("No transaction data available")
    
    with col2:
        st.markdown("#### 🎯 Risk Distribution")
        if len(high_risk_df) > 0:
            risk_dist = high_risk_df['risk_score'].value_counts().reset_index()
            fig_risk = px.histogram(high_risk_df, x='risk_score', nbins=20,
                                   title="Risk Score Distribution")
            st.plotly_chart(fig_risk, use_container_width=True)
        else:
            st.info("No high-risk data available")

def create_ai_assistant():
    """Enhanced AI Assistant with PT BERKAH context"""
    st.header("🤖 AI Assistant JALAK-HIJAU")
    st.subheader("Expert Analysis & Investigation Support")
    
    client = setup_openai()
    
    # PT BERKAH context banner
    st.markdown("""
    <div class="berkah-highlight">
        <h4>🎯 AI Context: PT SAWIT NUSANTARA Case Active</h4>
        <p>AI trained on environmental crime patterns and money laundering detection</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("💬 Expert Analysis Chat")
        
        # Display chat history
        for chat in st.session_state.chat_history:
            if chat['role'] == 'user':
                st.markdown(f"""
                <div style="background-color: #E8F5E8; padding: 10px; border-radius: 10px; margin: 5px 0;">
                    <strong>👤 Anda:</strong> {chat['content']}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="background-color: #F0F8FF; padding: 10px; border-radius: 10px; margin: 5px 0;">
                    <strong>🤖 AI Expert:</strong> {chat['content']}
                </div>
                """, unsafe_allow_html=True)
        
        # Chat input
        user_query = st.text_input("Konsultasi dengan AI Expert:", 
                                  placeholder="Contoh: Analisis pola money laundering PT BERKAH SAWIT")
        
        col_send, col_clear = st.columns([1, 4])
        
        with col_send:
            if st.button("📤 Kirim") and user_query:
                st.session_state.chat_history.append({'role': 'user', 'content': user_query})
                
                data_context = """
                PT SAWIT NUSANTARA Case:
                - 5,100 ha illegal forest clearing (35.2% overlap)
                - Rp 67B suspicious transactions
                - Money laundering through shell companies
                - Ahmad Wijaya beneficial owner
                - Active investigation in progress
                """
                
                ai_response = generate_ai_analysis(client, data_context, user_query)
                st.session_state.chat_history.append({'role': 'assistant', 'content': ai_response})
                st.rerun()
        
        with col_clear:
            if st.button("🗑️ Clear Chat"):
                st.session_state.chat_history = []
                st.rerun()
    
    with col2:
        st.subheader("🎯 Expert Queries")
        
        expert_queries = [
            "Analisis kasus PT BERKAH SAWIT",
            "Pola structuring yang terdeteksi", 
            "Network shell companies",
            "Rekomendasi investigasi lanjutan",
            "Generate laporan executive summary",
            "Prediksi modus operandi serupa"
        ]
        
        for query in expert_queries:
            if st.button(f"💡 {query}", key=f"expert_{hash(query)}"):
                st.session_state.chat_history.append({'role': 'user', 'content': query})
                
                data_context = "PT BERKAH case context with environmental and financial evidence..."
                ai_response = generate_ai_analysis(client, data_context, query)
                
                st.session_state.chat_history.append({'role': 'assistant', 'content': ai_response})
                st.rerun()
        
        st.markdown("---")
        st.subheader("🧠 AI Capabilities")
        st.markdown("""
        **Expert AI dapat:**
        - 🔍 Analisis pola environmental crime
        - 💰 Deteksi money laundering schemes
        - 📋 Generate STR otomatis
        - 🕸️ Network analysis shell companies
        - 📈 Predictive risk modeling
        - ⚖️ Legal recommendation
        """)

def create_report_generation():
    """New automatic report generation page"""
    st.header("📄 Automatic Report Generation")
    st.subheader("AI-Powered Investigation Reports")
    
    # Load data for reports
    financial_data = load_financial_data()
    transactions_df, high_risk_df, clusters_df, bank_accounts_df, berkah_case_df = financial_data
    companies_df = load_company_data()
    
    # Report type selection
    col1, col2 = st.columns([2, 1])
    
    with col1:
        report_type = st.selectbox("Select Report Type", [
            "🔥 PT BERKAH Case Report (Featured)",
            "📊 Weekly Risk Summary", 
            "🕸️ Network Analysis Report",
            "🛰️ Environmental Impact Assessment",
            "💰 STR Executive Summary",
            "📈 Trend Analysis Report"
        ])
        
        if st.button("🚀 Generate Report", type="primary"):
            with st.spinner("Generating comprehensive report..."):
                report_content = generate_automatic_report(report_type, berkah_case_df, high_risk_df, clusters_df)
                
                st.markdown("### Generated Report:")
                st.markdown(report_content)
                
                # Download options
                col_download1, col_download2 = st.columns(2)
                
                with col_download1:
                    st.download_button(
                        label="📥 Download as Text",
                        data=report_content,
                        file_name=f"JALAK_HIJAU_Report_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                        mime="text/plain"
                    )
                
                with col_download2:
                    # Create PDF-ready version
                    pdf_content = report_content.replace('#', '').replace('*', '')
                    st.download_button(
                        label="📄 Download for PDF",
                        data=pdf_content,
                        file_name=f"JALAK_HIJAU_Report_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                        mime="text/plain"
                    )
    
    with col2:
        st.markdown("""
        <div class="report-panel">
            <h4>📊 Report Features</h4>
            <ul>
                <li>🤖 AI-powered analysis</li>
                <li>📈 Data visualizations</li>
                <li>🎯 Actionable insights</li>
                <li>⚖️ Legal recommendations</li>
                <li>📋 Executive summaries</li>
                <li>🔗 Cross-reference evidence</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        st.subheader("📈 Report Statistics")
        st.metric("Reports Generated Today", "12")
        st.metric("Average Generation Time", "< 30 seconds")
        st.metric("Investigation Success Rate", "87%")

def generate_automatic_report(report_type, berkah_case_df, high_risk_df, clusters_df):
    """Generate different types of reports"""
    
    if "PT BERKAH" in report_type:
        return f"""
# 🔥 PT SAWIT NUSANTARA - CRITICAL CASE REPORT

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Classification:** CRITICAL PRIORITY  
**Case ID:** ALT-CRIT-001

## EXECUTIVE SUMMARY

PT SAWIT NUSANTARA telah melakukan kejahatan lingkungan sistematis dengan mengkliring 5,100 hektar Hutan Lindung Riau secara ilegal, diikuti dengan pencucian uang senilai Rp 67+ miliar melalui jaringan shell companies.

## KEY FINDINGS

### 🛰️ Environmental Crime Evidence
- **Illegal Forest Clearing:** 5,100 hectares (35.2% overlap)
- **Protected Area:** Hutan Lindung Riau Tengah
- **Coordinates:** 0.52°S, 101.43°E
- **Detection Method:** Satellite imagery analysis

### 💰 Money Laundering Evidence
- **Total Suspicious Amount:** Rp 67,200,000,000
- **Primary Transfer:** Rp 45B to shell company (Day +1 after clearing)
- **Structuring Pattern:** 5 transactions under Rp 500M threshold
- **Layering:** Multiple shell company transfers
- **Integration:** Final placement into legitimate business

### 🏢 Corporate Network
- **Beneficial Owner:** Ahmad Wijaya (NIK: 1471010101800001)
- **Front Company:** PT SAWIT NUSANTARA
- **Primary Shell:** PT KARYA UTAMA CONSULTING
- **Secondary Shells:** 3+ additional entities

## TIMELINE OF EVENTS

- **Day -15:** Satellite detects forest clearing activity
- **Day -14:** Rp 45B transfer to shell company
- **Day -13 to -9:** Structuring pattern (5 transactions)
- **Day -7 to -3:** Layering through network
- **Day 0:** JALAK-HIJAU alert triggered
- **Today:** Full investigation active

## LEGAL VIOLATIONS

1. **UU No. 18/2013 (Pencegahan dan Pemberantasan Perusakan Hutan)**
2. **UU No. 8/2010 (Pencegahan dan Pemberantasan Tindak Pidana Pencucian Uang)**
3. **UU No. 32/2009 (Perlindungan dan Pengelolaan Lingkungan Hidup)**

## RECOMMENDATIONS

### Immediate Actions (0-7 days)
1. 🏦 Freeze all accounts PT BERKAH and shell companies
2. 📞 Coordinate with KLHK for permit verification
3. 👤 Asset tracing for Ahmad Wijaya and affiliates
4. ⚖️ Prepare criminal charges documentation

### Medium Term (1-4 weeks)
1. 🔍 Field verification of forest damage
2. 📋 Complete beneficial ownership mapping
3. 🌍 International cooperation if offshore accounts found
4. 📺 Public disclosure for deterrent effect

### Long Term (1-6 months)
1. 🛠️ System enhancement based on case lessons
2. 📚 Training for similar pattern recognition
3. 🤝 Inter-agency coordination strengthening
4. 📊 Policy recommendations for prevention

## RISK ASSESSMENT

**Environmental Damage:** CRITICAL - Irreversible forest loss  
**Financial Crime:** HIGH - Sophisticated laundering scheme  
**Reputational Risk:** HIGH - International attention likely  
**Investigation Success:** HIGH - Strong evidence chain

---
**Report generated by JALAK-HIJAU AI System**  
**Next Review:** {(datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')}
"""
    
    elif "Weekly Risk" in report_type:
        return f"""
# 📊 WEEKLY RISK SUMMARY REPORT

**Period:** {(datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')} to {datetime.now().strftime('%Y-%m-%d')}  
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## SUMMARY METRICS

- **New Alerts:** 23 (↑15% from last week)
- **Critical Cases:** 1 (PT BERKAH SAWIT)
- **High Risk Transactions:** 156 (Total value: Rp 2.8T)
- **Environmental Violations:** 3 confirmed

## TOP RISKS THIS WEEK

1. **PT SAWIT NUSANTARA** - CRITICAL
   - Forest clearing + money laundering
   - Investigation active

2. **PT HIJAU SAWIT KALIMANTAN** - HIGH
   - Structuring pattern detected
   - Under monitoring

3. **Financial Network Cluster-005** - MEDIUM
   - Complex layering scheme
   - Requires deeper analysis

## TREND ANALYSIS

Environmental crime detection improving with satellite integration.
Money laundering patterns becoming more sophisticated.
Need for enhanced cross-sector coordination.

---
**Next weekly report:** {(datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')}
"""
    
    else:
        return f"""
# 📄 JALAK-HIJAU SYSTEM REPORT

**Type:** {report_type}  
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## SYSTEM STATUS

JALAK-HIJAU operational and detecting environmental crimes effectively.
AI-powered analysis providing actionable intelligence for PPATK.

## CURRENT CASES

Active investigations ongoing with strong evidence chains.
Cross-sector data integration proving highly effective.

## RECOMMENDATIONS

Continue current monitoring protocols.
Enhance inter-agency coordination.
Expand satellite coverage areas.

---
**Report generated by JALAK-HIJAU AI System**
"""
    
    return report

# Main application
def main():
    load_css()
    init_session_state()
    
    # Check if in investigation mode
    if st.session_state.investigation_mode:
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.title("🔍 JALAK-HIJAU Investigation Mode")
        
        with col2:
            if st.button("❌ Exit Investigation", type="secondary"):
                st.session_state.investigation_mode = False
                st.session_state.selected_alert = None
                st.session_state.investigation_data = {}
                st.rerun()
        
        create_investigation_dashboard()
        return
    
    # Enhanced Sidebar with better navigation
    st.sidebar.image("logotext.png", width=280)
    
    # Enhanced Navigation Menu
    st.sidebar.markdown("### 🧭 Navigation")
    
    pages = {
        "🏠 Dashboard Overview": create_overview_dashboard,
        "📊 Advanced Analysis": create_analysis_page,
        "🤖 AI Expert Assistant": create_ai_assistant,
        "📄 Report Generation": create_report_generation
    }
    
    # Create navigation buttons
    for page_name in pages.keys():
        if st.sidebar.button(page_name, key=f"nav_{page_name}", use_container_width=True):
            st.session_state.current_page = page_name
            st.rerun()
    
    # Current page indicator
    current_page = st.session_state.get('current_page', "🏠 Dashboard Overview")
    
    # System status with enhanced metrics
    data_status = "✅ Live" if Path("data").exists() else "⚠️ Demo" 
    geo_status = "✅ Active" if Path("forest.shp").exists() else "⚠️ Demo"
    
    st.sidebar.markdown(f"""
    ---
    ### 📊 System Status
    - **🛰️ Satellite Feed:** Active
    - **💾 Financial Data:** {data_status}
    - **🗺️ Geospatial Data:** {geo_status}
    - **🤖 AI Engine:** Online
    - **🔗 Integration:** Operational
    
    """)
    

    
    # Execute selected page
    pages[current_page]()

if __name__ == "__main__":
    main()
