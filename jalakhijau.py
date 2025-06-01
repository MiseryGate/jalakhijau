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
    
    .sawit-highlight {
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

# Enhanced data loading functions with fixed paths
@st.cache_data
def load_geospatial_data():
    """Load geospatial data with PT SAWIT NUSANTARA focus"""
    try:
        # Try current directory first
        forest_gdf = gpd.read_file("forest.shp")
        sawit_gdf = gpd.read_file("sawit.shp")
        overlap_gdf = gpd.read_file("overlap.shp")
        st.success("✅ Loaded actual shapefiles successfully!")
        return forest_gdf, sawit_gdf, overlap_gdf
    except Exception as e:
        return generate_realistic_geodata_with_sawit_nusantara()

@st.cache_data
def load_financial_data():
    """Load financial data with PT SAWIT NUSANTARA case study"""
    # Try multiple path locations for Streamlit Cloud compatibility
    file_locations = [
        # Current directory
        "transactions.csv",
        "transactions_high_risk.csv", 
        "transactions_clusters.csv",
        "bank_accounts.csv",
        # Data subdirectory
        "data/transactions.csv",
        "data/transactions_high_risk.csv",
        "data/transactions_clusters.csv", 
        "data/bank_accounts.csv"
    ]
    
    try:
        # Try current directory first (Streamlit Cloud compatible)
        transactions_df = pd.read_csv("transactions.csv") if Path("transactions.csv").exists() else None
        high_risk_df = pd.read_csv("transactions_high_risk.csv") if Path("transactions_high_risk.csv").exists() else None
        clusters_df = pd.read_csv("transactions_clusters.csv") if Path("transactions_clusters.csv").exists() else None
        bank_accounts_df = pd.read_csv("bank_accounts.csv") if Path("bank_accounts.csv").exists() else None
        
        # Try data subdirectory as fallback
        if transactions_df is None and Path("data/transactions.csv").exists():
            transactions_df = pd.read_csv("data/transactions.csv")
            high_risk_df = pd.read_csv("data/transactions_high_risk.csv") if Path("data/transactions_high_risk.csv").exists() else None
            clusters_df = pd.read_csv("data/transactions_clusters.csv") if Path("data/transactions_clusters.csv").exists() else None
            bank_accounts_df = pd.read_csv("data/bank_accounts.csv") if Path("data/bank_accounts.csv").exists() else None
        
        if transactions_df is not None:
            # Convert date columns
            transactions_df['transaction_date'] = pd.to_datetime(transactions_df['transaction_date'])
            if high_risk_df is not None:
                high_risk_df['transaction_date'] = pd.to_datetime(high_risk_df['transaction_date'])
            
            # Create PT SAWIT NUSANTARA case study from existing data
            sawit_case_df = None
            if high_risk_df is not None and len(high_risk_df) > 0:
                sawit_case_df = create_sawit_nusantara_case_study(high_risk_df)
            
            return transactions_df, high_risk_df, clusters_df, bank_accounts_df, sawit_case_df
        else:
            return generate_demo_financial_data()
        
    except Exception as e:
        st.warning(f"⚠️ Error loading financial data: {str(e)}")
        return generate_demo_financial_data()

@st.cache_data  
def load_company_data():
    """Load company data with PT SAWIT NUSANTARA highlighted"""
    try:
        # Try current directory first
        if Path("pt_data.csv").exists():
            pt_df = pd.read_csv("pt_data.csv")
        elif Path("data/pt_data.csv").exists():
            pt_df = pd.read_csv("data/pt_data.csv")
        else:
            return generate_demo_companies_with_sawit_nusantara()
        
        # Update any existing BERKAH references to SAWIT NUSANTARA
        pt_df.loc[pt_df['nama_perseroan'].str.contains('BERKAH', na=False), 'nama_perseroan'] = 'PT SAWIT NUSANTARA'
        
        return pt_df
    except:
        return generate_demo_companies_with_sawit_nusantara()

def create_sawit_nusantara_case_study(high_risk_df):
    """Create specific PT SAWIT NUSANTARA case study from existing data"""
    # Filter for PT SAWIT NUSANTARA or create synthetic case
    sawit_transactions = high_risk_df[
        (high_risk_df['sender_company'].str.contains('SAWIT NUSANTARA', na=False)) |
        (high_risk_df['receiver_company'].str.contains('SAWIT NUSANTARA', na=False)) |
        (high_risk_df['sender_company'].str.contains('BERKAH', na=False)) |
        (high_risk_df['receiver_company'].str.contains('BERKAH', na=False))
    ].copy()
    
    # Update company names to PT SAWIT NUSANTARA
    sawit_transactions.loc[sawit_transactions['sender_company'].str.contains('BERKAH', na=False), 'sender_company'] = 'PT SAWIT NUSANTARA'
    sawit_transactions.loc[sawit_transactions['receiver_company'].str.contains('BERKAH', na=False), 'receiver_company'] = 'PT SAWIT NUSANTARA'
    
    if len(sawit_transactions) == 0:
        # Create synthetic case study
        base_date = datetime.now() - timedelta(days=30)
        case_data = []
        
        # Main placement transaction
        case_data.append({
            'transaction_id': 'TXN_SAWIT_001',
            'transaction_date': base_date + timedelta(days=1),
            'sender_company': 'PT SAWIT NUSANTARA',
            'receiver_company': 'PT KARYA UTAMA CONSULTING',
            'amount_idr': 45000000000,  # 45 billion
            'risk_score': 95,
            'transaction_type': 'placement',
            'is_flagged': True,
            'case_related': True
        })
        
        # Structuring pattern
        for i in range(5):
            case_data.append({
                'transaction_id': f'TXN_SAWIT_{i+2:03d}',
                'transaction_date': base_date + timedelta(days=i+2),
                'sender_company': 'PT SAWIT NUSANTARA',
                'receiver_company': f'PT SHELL COMPANY {i+1}',
                'amount_idr': random.randint(400000000, 499000000),
                'risk_score': random.randint(80, 90),
                'transaction_type': 'structuring',
                'is_flagged': True,
                'case_related': True
            })
        
        sawit_transactions = pd.DataFrame(case_data)
        sawit_transactions['transaction_date'] = pd.to_datetime(sawit_transactions['transaction_date'])
    
    return sawit_transactions

def generate_realistic_geodata_with_sawit_nusantara():
    """Generate geospatial data highlighting PT SAWIT NUSANTARA case"""
    regions = {
        'Riau': {'center': [0.5, 101.4], 'bbox': [(-1, 100), (2, 103)]},
        'Kalimantan Selatan': {'center': [-2.2, 115.0], 'bbox': [(-4, 113), (-1, 117)]},
    }
    
    forest_areas = []
    sawit_concessions = []
    overlap_areas = []
    
    # Create PT SAWIT NUSANTARA specific case in Riau
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
    
    # PT SAWIT NUSANTARA concession overlapping with forest
    sawit_lat, sawit_lon = forest_lat + 0.02, forest_lon - 0.01
    sawit_polygon = Point(sawit_lon, sawit_lat).buffer(0.12)
    
    sawit_concessions.append({
        'geometry': sawit_polygon,
        'company': 'PT SAWIT NUSANTARA',
        'region': 'Riau',
        'permit_status': 'Active',
        'area_ha': 14500,
        'center_lat': sawit_lat,
        'center_lon': sawit_lon,
        'overlap_percentage': 35.2,
        'is_overlapping': True,
        'risk_score': 95
    })
    
    # Overlap area
    overlap_polygon = Point(sawit_lon, sawit_lat).buffer(0.08)
    overlap_areas.append({
        'geometry': overlap_polygon,
        'company': 'PT SAWIT NUSANTARA',
        'forest_area': 'Hutan Lindung Riau Tengah',
        'overlap_ha': 5100,
        'overlap_percentage': 35.2,
        'severity': 'CRITICAL',
        'center_lat': sawit_lat,
        'center_lon': sawit_lon
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
    """Generate demo financial data with PT SAWIT NUSANTARA case"""
    # Create minimal demo data structure
    base_date = datetime.now() - timedelta(days=30)
    
    demo_transactions = []
    for i in range(100):
        demo_transactions.append({
            'transaction_id': f'TXN_DEMO_{i:03d}',
            'transaction_date': base_date + timedelta(days=random.randint(0, 30)),
            'sender_company': 'PT SAWIT NUSANTARA' if i < 10 else f'PT DEMO COMPANY {i}',
            'receiver_company': 'PT KARYA UTAMA CONSULTING' if i < 5 else f'PT RECEIVER {i}',
            'amount_idr': random.randint(100000000, 5000000000),
            'risk_score': random.randint(60, 95) if i < 20 else random.randint(10, 50),
            'is_flagged': i < 20
        })
    
    transactions_df = pd.DataFrame(demo_transactions)
    transactions_df['transaction_date'] = pd.to_datetime(transactions_df['transaction_date'])
    
    high_risk_df = transactions_df[transactions_df['is_flagged']].copy()
    clusters_df = pd.DataFrame()
    bank_accounts_df = pd.DataFrame()
    sawit_case_df = high_risk_df[high_risk_df['sender_company'] == 'PT SAWIT NUSANTARA'].copy()
    
    return transactions_df, high_risk_df, clusters_df, bank_accounts_df, sawit_case_df

def generate_demo_companies_with_sawit_nusantara():
    """Generate demo company data with PT SAWIT NUSANTARA highlighted"""
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

# Pre-computed AI insights for PT SAWIT NUSANTARA
def get_sawit_nusantara_ai_insights(query_type="general"):
    """Get pre-computed AI insights for PT SAWIT NUSANTARA case"""
    insights = {
        "general": """
**ANALISIS KASUS PT SAWIT NUSANTARA - STATUS CRITICAL**

Berdasarkan analisis komprehensif sistem JALAK-HIJAU:

🚨 **TEMUAN UTAMA:**
- Clearing ilegal 5,100 ha Hutan Lindung Riau (overlap 35.2%)
- Money laundering Rp 67+ miliar melalui jaringan shell companies
- Ahmad Wijaya sebagai beneficial owner tersembunyi
- Pola structuring sistematis untuk hindari pelaporan

📊 **POLA KEUANGAN MENCURIGAKAN:**
1. **Placement:** Transfer Rp 45M ke PT Karya Utama sehari setelah clearing
2. **Structuring:** 5 transaksi @Rp 400-499M (di bawah threshold Rp 500M)
3. **Layering:** Aliran dana melalui 4+ shell companies
4. **Integration:** Penempatan akhir ke rekening bisnis legitimate

⚖️ **PELANGGARAN HUKUM:**
- UU No. 18/2013 (Pencegahan Perusakan Hutan)
- UU No. 8/2010 (Anti Money Laundering)
- UU No. 32/2009 (Perlindungan Lingkungan Hidup)

🎯 **REKOMENDASI SEGERA:**
1. Pembekuan semua rekening PT Sawit Nusantara & shell companies
2. Koordinasi KLHK untuk verifikasi izin dan damage assessment
3. Background check Ahmad Wijaya - asset tracing lengkap
4. Persiapan STR dan koordinasi Kejaksaan untuk tindak pidana
""",
        
        "structuring": """
**ANALISIS POLA STRUCTURING - PT SAWIT NUSANTARA**

🔍 **POLA TERDETEKSI:**
- 5 transaksi dalam periode 5 hari berturut-turut
- Nominal: Rp 400-499 juta (tepat di bawah threshold Rp 500 juta)
- Penerima: Shell companies berbeda dengan beneficial owner sama

📈 **RISK INDICATORS:**
- Timing: Segera setelah forest clearing operation
- Frequency: Daily consecutive transactions
- Amounts: Consistently under reporting threshold (classic structuring)
- Recipients: Multiple entities, single controller

⚖️ **REGULASI TERKAIT:**
- POJK No. 12/POJK.01/2017 tentang Penerapan Program Anti Pencucian Uang
- Threshold pelaporan transaksi: Rp 500 juta (Pasal 23 UU TPPU)

🎯 **INVESTIGASI LANJUTAN:**
1. Trace beneficial ownership semua penerima
2. Analisis timing correlation dengan satellite imagery
3. Cross-check dengan laporan transaksi bank periode sama
4. Identifikasi pola serupa di perusahaan Ahmad Wijaya lainnya
""",
        
        "network": """
**NETWORK ANALYSIS - JARINGAN PT SAWIT NUSANTARA**

🕸️ **STRUKTUR JARINGAN:**
- **Central Node:** Ahmad Wijaya (NIK: 1471010101800001)
- **Front Company:** PT Sawit Nusantara (operasional)
- **Primary Shell:** PT Karya Utama Consulting (receiver utama)
- **Secondary Shells:** 3+ entities untuk layering

🔗 **RELASI KUNCI:**
1. Ahmad Wijaya → 100% owner PT Sawit Nusantara
2. Ahmad Wijaya → Hidden beneficial owner shell companies
3. PT Sawit Nusantara → Transfer Rp 45M → PT Karya Utama
4. Shell companies → Cross-transfers untuk obscure money trail

📊 **RISK SCORING:**
- Ahmad Wijaya: 95/100 (central coordinator)
- PT Sawit Nusantara: 95/100 (primary violator)
- PT Karya Utama: 90/100 (main money receiver)
- Secondary shells: 80-85/100 (laundering vehicles)

🎯 **INVESTIGASI PRIORITAS:**
1. Map complete beneficial ownership network
2. Identify all bank accounts under Ahmad Wijaya control
3. Search for international connections (offshore accounts)
4. Look for similar patterns in other palm oil companies
""",
        
        "legal": """
**REKOMENDASI LEGAL - KASUS PT SAWIT NUSANTARA**

⚖️ **TINDAK PIDANA YANG DAPAT DIBUKTIKAN:**

**1. DEFORESTASI ILEGAL**
- Pasal 82 UU No. 18/2013: Pidana penjara 10-15 tahun + denda Rp 5-15 miliar
- Evidence: Satellite imagery overlap 35.2% dengan kawasan lindung

**2. PENCUCIAN UANG**
- Pasal 3 UU No. 8/2010: Pidana penjara 5-20 tahun + denda Rp 1-10 miliar
- Evidence: Placement, layering, integration pattern terdokumentasi

**3. PERUSAKAN LINGKUNGAN**
- Pasal 98 UU No. 32/2009: Pidana penjara 3-10 tahun + denda Rp 3-10 miliar
- Evidence: Kerusakan 5,100 ha hutan lindung

📋 **TAHAPAN PROSECUTORIAL:**
1. **Immediate (0-7 hari):** Asset freezing, STR filing
2. **Short-term (1-4 minggu):** Penyidikan, pengumpulan bukti
3. **Medium-term (1-3 bulan):** Penuntutan, persidangan
4. **Long-term (6-12 bulan):** Eksekusi putusan, asset recovery

🎯 **STRATEGI PENUNTUTAN:**
- Gunakan environmental crime sebagai predicate offense
- Leverage satellite evidence untuk strengthen case
- Coordinate dengan KLHK, KPK untuk comprehensive approach
- Consider civil asset forfeiture untuk environmental restoration
"""
    }
    
    return insights.get(query_type, insights["general"])

# OpenAI Integration with enhanced PT SAWIT NUSANTARA context
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
    """Generate AI-powered analysis with PT SAWIT NUSANTARA focus"""
    
    # Check if query is about PT SAWIT NUSANTARA case - use pre-computed insights
    query_lower = user_query.lower()
    if any(term in query_lower for term in ['sawit nusantara', 'structuring', 'network', 'legal', 'ahmad wijaya']):
        if 'structuring' in query_lower:
            return get_sawit_nusantara_ai_insights("structuring")
        elif 'network' in query_lower:
            return get_sawit_nusantara_ai_insights("network")
        elif 'legal' in query_lower or 'rekomendasi' in query_lower:
            return get_sawit_nusantara_ai_insights("legal")
        else:
            return get_sawit_nusantara_ai_insights("general")
    
    # For other queries, use OpenAI if available
    if not client:
        return "AI Assistant tidak tersedia. Menggunakan analisis pre-computed untuk kasus PT SAWIT NUSANTARA."
    
    try:
        enhanced_context = f"""
        {data_context}
        
        KASUS UNGGULAN: PT SAWIT NUSANTARA
        - Environmental crime: 5,100 ha illegal forest clearing
        - Money laundering: Rp 67+ miliar through shell companies
        - Beneficial owner: Ahmad Wijaya (NIK: 1471010101800001)
        - Pattern: Placement → Structuring → Layering → Integration
        - Legal violations: UU 18/2013, UU 8/2010, UU 32/2009
        """
        
        prompt = f"""
        Anda adalah AI Assistant untuk sistem JALAK-HIJAU yang mendeteksi kejahatan lingkungan dan pencucian uang di Indonesia.
        
        Konteks data: {enhanced_context}
        Pertanyaan user: {user_query}
        
        Berikan analisis yang spesifik, actionable, dan dalam bahasa Indonesia. 
        Fokus pada:
        1. Pola mencurigakan yang terdeteksi
        2. Rekomendasi investigasi konkret
        3. Risiko yang perlu ditindaklanjuti
        4. Langkah-langkah investigasi selanjutnya
        5. Referensi hukum yang relevan
        """
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Anda adalah expert analyst untuk PPATK Indonesia yang spesialis dalam mendeteksi environmental crime dan money laundering, dengan fokus khusus pada kasus PT SAWIT NUSANTARA."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=800,
            temperature=0.7
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        return f"Error dalam analisis AI: {str(e)}. Menggunakan analisis pre-computed untuk kasus PT SAWIT NUSANTARA."

# Enhanced Investigation Mode Functions
def start_investigation(alert_id, alert_data):
    """Initialize investigation mode"""
    st.session_state.investigation_mode = True
    st.session_state.selected_alert = alert_id
    
    investigation_data = {
        'alert_id': alert_id,
        'status': 'ACTIVE',
        'priority': 'CRITICAL' if 'SAWIT NUSANTARA' in alert_data.get('company', '') else 'HIGH',
        'assigned_to': 'Tim Investigasi PPATK',
        'start_date': datetime.now(),
        'case_summary': alert_data,
        'evidence_collected': [],
        'next_actions': [],
        'timeline': []
    }
    
    # Special handling for PT SAWIT NUSANTARA case
    if 'SAWIT NUSANTARA' in alert_data.get('company', ''):
        investigation_data['evidence_collected'] = [
            '🛰️ Citra satelit: overlap 35.2% dengan Hutan Lindung Riau (5,100 ha)',
            '💰 Transfer Rp 45M ke PT KARYA UTAMA CONSULTING sehari setelah clearing',
            '🔗 Beneficial owner sama: Ahmad Wijaya (NIK: 1471010101800001)',
            '📊 Pola structuring: 5 transaksi @Rp 400-499M dalam 5 hari',
            '🏢 Shell company: modal disetor rendah, alamat berbeda',
            '📍 Koordinat pelanggaran: 0.52°S, 101.43°E (Riau)',
            '⚖️ Violation: UU 18/2013, UU 8/2010, UU 32/2009'
        ]
        investigation_data['next_actions'] = [
            '🔍 Verifikasi lapangan koordinat overlap (0.52°S, 101.43°E)',
            '📞 Koordinasi dengan KLHK untuk status izin HGU',
            '🏦 Request rekening koran PT SAWIT NUSANTARA dan PT KARYA UTAMA',
            '👤 Background check Ahmad Wijaya - kepemilikan multi-entity',
            '⚖️ Persiapan STR dan koordinasi dengan Kejaksaan',
            '🌍 Trace international connections (offshore accounts)',
            '📊 Analisis pola serupa di perusahaan sawit lainnya'
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

def create_enhanced_network_visualization(case_data):
    """Create sophisticated network visualization for PT SAWIT NUSANTARA"""
    
    # Create enhanced network graph
    G = nx.DiGraph()
    
    # Define node attributes with enhanced styling
    nodes = {
        "Ahmad Wijaya": {
            "type": "beneficial_owner", 
            "risk": 95, 
            "color": "#DC3545", 
            "size": 60,
            "details": "NIK: 1471010101800001<br>Central Controller<br>Risk: 95/100"
        },
        "PT SAWIT NUSANTARA": {
            "type": "front_company", 
            "risk": 95, 
            "color": "#FF6B35", 
            "size": 50,
            "details": "Front Company<br>Palm Oil Operations<br>Risk: 95/100"
        },
        "PT KARYA UTAMA": {
            "type": "shell_company", 
            "risk": 90, 
            "color": "#8B0000", 
            "size": 45,
            "details": "Shell Company<br>Rp 45B Receiver<br>Risk: 90/100"
        },
        "Shell Company 1": {
            "type": "shell_company", 
            "risk": 85, 
            "color": "#CD5C5C", 
            "size": 35,
            "details": "Secondary Shell<br>Layering Vehicle<br>Risk: 85/100"
        },
        "Shell Company 2": {
            "type": "shell_company", 
            "risk": 83, 
            "color": "#CD5C5C", 
            "size": 35,
            "details": "Secondary Shell<br>Layering Vehicle<br>Risk: 83/100"
        },
        "Bank Account A": {
            "type": "account", 
            "risk": 88, 
            "color": "#4682B4", 
            "size": 30,
            "details": "Primary Account<br>PT SAWIT NUSANTARA<br>Risk: 88/100"
        },
        "Bank Account B": {
            "type": "account", 
            "risk": 85, 
            "color": "#87CEEB", 
            "size": 25,
            "details": "Shell Account<br>PT KARYA UTAMA<br>Risk: 85/100"
        },
        "Hutan Lindung Riau": {
            "type": "protected_area", 
            "risk": 100, 
            "color": "#228B22", 
            "size": 40,
            "details": "Protected Forest<br>5,100 ha damaged<br>Critical Violation"
        }
    }
    
    # Add nodes with attributes
    for node_id, attrs in nodes.items():
        G.add_node(node_id, **attrs)
    
    # Define edges with enhanced attributes
    edges = [
        ("Ahmad Wijaya", "PT SAWIT NUSANTARA", {"weight": 0.95, "relation": "100% Owner", "amount": "", "color": "#DC3545", "width": 4}),
        ("Ahmad Wijaya", "PT KARYA UTAMA", {"weight": 0.90, "relation": "Hidden Owner", "amount": "", "color": "#8B0000", "width": 3}),
        ("Ahmad Wijaya", "Shell Company 1", {"weight": 0.85, "relation": "Controller", "amount": "", "color": "#CD5C5C", "width": 2}),
        ("Ahmad Wijaya", "Shell Company 2", {"weight": 0.83, "relation": "Controller", "amount": "", "color": "#CD5C5C", "width": 2}),
        ("PT SAWIT NUSANTARA", "Hutan Lindung Riau", {"weight": 0.95, "relation": "Illegal Clearing", "amount": "5,100 ha", "color": "#FF4500", "width": 5}),
        ("PT SAWIT NUSANTARA", "Bank Account A", {"weight": 0.90, "relation": "Primary Account", "amount": "", "color": "#4682B4", "width": 3}),
        ("Bank Account A", "Bank Account B", {"weight": 0.88, "relation": "Transfer", "amount": "Rp 45B", "color": "#FF6B35", "width": 6}),
        ("Bank Account B", "Shell Company 1", {"weight": 0.80, "relation": "Layering", "amount": "Rp 15B", "color": "#FFA500", "width": 3}),
        ("Shell Company 1", "Shell Company 2", {"weight": 0.75, "relation": "Layering", "amount": "Rp 8B", "color": "#FFA500", "width": 2}),
    ]
    
    # Add edges with attributes
    for source, target, attrs in edges:
        G.add_edge(source, target, **attrs)
    
    # Create sophisticated layout
    pos = nx.spring_layout(G, k=3, iterations=50, seed=42)
    
    # Position Ahmad Wijaya at center
    pos["Ahmad Wijaya"] = (0, 0)
    
    # Create plotly figure
    fig = go.Figure()
    
    # Draw edges with varying widths and colors
    for edge in G.edges(data=True):
        source, target, attrs = edge
        x0, y0 = pos[source]
        x1, y1 = pos[target]
        
        fig.add_trace(go.Scatter(
            x=[x0, x1, None], 
            y=[y0, y1, None],
            mode='lines',
            line=dict(width=attrs['width'], color=attrs['color']),
            hoverinfo='text',
            hovertext=f"{source} → {target}<br>{attrs['relation']}<br>{attrs.get('amount', '')}",
            showlegend=False,
            opacity=0.8
        ))
    
    # Draw nodes with varying sizes and colors
    for node in G.nodes(data=True):
        node_id, attrs = node
        x, y = pos[node_id]
        
        fig.add_trace(go.Scatter(
            x=[x], 
            y=[y],
            mode='markers+text',
            marker=dict(
                size=attrs['size'],
                color=attrs['color'],
                line=dict(width=3, color='white'),
                opacity=0.9
            ),
            text=node_id,
            textposition="bottom center",
            textfont=dict(size=10, color='black'),
            hoverinfo='text',
            hovertext=attrs['details'],
            showlegend=False
        ))
    
    # Update layout for better visualization
    fig.update_layout(
        showlegend=False,
        hovermode='closest',
        margin=dict(b=20,l=5,r=5,t=40),
        annotations=[ 
            dict(
                text="Ahmad Wijaya: Central Controller | PT SAWIT NUSANTARA: Environmental Crime | Money Flow: Rp 67B+",
                showarrow=False,
                xref="paper", yref="paper",
                x=0.005, y=-0.002,
                xanchor='left', yanchor='bottom',
                font=dict(color='darkred', size=12)
            )
        ],
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        plot_bgcolor='rgba(248,248,255,0.8)',
        height=600
    )
    
    return fig

def create_investigation_dashboard():
    """Create enhanced investigation mode dashboard"""
    if not st.session_state.investigation_mode:
        st.error("Investigation mode not active!")
        return
    
    inv_data = st.session_state.investigation_data
    
    # Special header for PT SAWIT NUSANTARA case
    if 'SAWIT NUSANTARA' in inv_data.get('case_summary', {}).get('company', ''):
        st.markdown(f"""
        <div class="sawit-highlight">
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
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📋 Case Overview", "🔍 Evidence", "🎯 Actions", "📊 Network Analysis", "📄 Generate STR"])
    
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
            **Progress:** 75% Complete  
            **Est. Completion:** 2 days
            """)
        
        # PT SAWIT NUSANTARA specific timeline
        if 'SAWIT NUSANTARA' in case.get('company', ''):
            st.subheader("📅 Case Timeline")
            st.markdown("""
            - **Day -15:** Satellite imagery shows forest clearing activity (5,100 ha)
            - **Day -14:** PT SAWIT NUSANTARA transfers Rp 45B to PT KARYA UTAMA
            - **Day -13 to -9:** Structuring pattern: 5 transactions under threshold
            - **Day -7 to -3:** Layering through multiple shell companies
            - **Day -1:** Integration into legitimate business accounts
            - **Day 0:** JALAK-HIJAU alert triggered (ALT-CRIT-001)
            - **Today:** Full investigation active with 7 evidence points
            """)
            
            # Key metrics for PT SAWIT NUSANTARA
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("🌲 Forest Damaged", "5,100 ha", delta="35.2% overlap")
            with col2:
                st.metric("💰 Money Laundered", "Rp 67B+", delta="Multi-stage")
            with col3:
                st.metric("🏢 Entities Involved", "6", delta="Shell network")
            with col4:
                st.metric("⚖️ Legal Violations", "3", delta="Major laws")
    
    with tab2:
        st.subheader("🔍 Evidence Collected")
        for i, evidence in enumerate(inv_data['evidence_collected']):
            st.markdown(f"**{i+1}.** {evidence}")
        
        new_evidence = st.text_input("Add New Evidence:")
        if st.button("➕ Add Evidence") and new_evidence:
            inv_data['evidence_collected'].append(f"📝 {new_evidence}")
            st.session_state.investigation_data = inv_data
            st.rerun()
        
        # Evidence strength meter
        if 'SAWIT NUSANTARA' in inv_data.get('case_summary', {}).get('company', ''):
            st.subheader("📊 Evidence Strength Analysis")
            evidence_strength = {
                'Satellite Evidence': 95,
                'Financial Evidence': 92,
                'Corporate Network': 88,
                'Legal Documentation': 85
            }
            
            for evidence_type, strength in evidence_strength.items():
                st.progress(strength/100, text=f"{evidence_type}: {strength}%")
    
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
        
        # Priority matrix for PT SAWIT NUSANTARA
        if 'SAWIT NUSANTARA' in inv_data.get('case_summary', {}).get('company', ''):
            st.subheader("🎯 Action Priority Matrix")
            
            priority_actions = {
                'URGENT (0-24h)': ['Asset freezing', 'STR filing', 'Coordinate with KLHK'],
                'HIGH (1-7 days)': ['Field verification', 'Background check Ahmad Wijaya', 'Bank records request'],
                'MEDIUM (1-4 weeks)': ['International trace', 'Pattern analysis', 'Legal preparation']
            }
            
            for priority, actions in priority_actions.items():
                with st.expander(f"📋 {priority}"):
                    for action in actions:
                        st.markdown(f"- {action}")
    
    with tab4:
        st.subheader("📊 Enhanced Network Analysis")
        
        # Create sophisticated network visualization
        network_fig = create_enhanced_network_visualization(inv_data)
        st.plotly_chart(network_fig, use_container_width=True)
        
        # Network statistics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("🕸️ Network Nodes", "8", delta="Key entities")
        with col2:
            st.metric("🔗 Connections", "9", delta="Money flows")
        with col3:
            st.metric("🎯 Central Risk", "95%", delta="Ahmad Wijaya")
        
        # Money flow analysis
        if 'SAWIT NUSANTARA' in inv_data.get('case_summary', {}).get('company', ''):
            st.subheader("💰 Money Flow Analysis")
            
            flow_data = pd.DataFrame({
                'Stage': ['Placement', 'Layering 1', 'Layering 2', 'Integration'],
                'Amount_B': [45, 22, 12, 8],
                'Entities': ['PT KARYA UTAMA', 'Shell Company 1', 'Shell Company 2', 'Final Accounts'],
                'Risk_Level': [95, 85, 80, 75]
            })
            
            fig_flow = px.bar(flow_data, x='Stage', y='Amount_B', color='Risk_Level',
                            color_continuous_scale='Reds',
                            title="💰 Money Laundering Flow (Billion Rp)",
                            hover_data=['Entities'])
            st.plotly_chart(fig_flow, use_container_width=True)
    
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
            
        # STR preview for PT SAWIT NUSANTARA
        if 'SAWIT NUSANTARA' in inv_data.get('case_summary', {}).get('company', ''):
            st.subheader("📋 STR Preview - Key Elements")
            st.markdown("""
            **🔥 EXECUTIVE SUMMARY:**
            - Environmental crime: 5,100 ha illegal forest clearing
            - Money laundering: Rp 67+ billion systematic scheme
            - Criminal network: Ahmad Wijaya + 5 shell companies
            
            **⚖️ LEGAL VIOLATIONS:**
            - UU No. 18/2013 (Forest Protection): 10-15 years prison
            - UU No. 8/2010 (Money Laundering): 5-20 years prison  
            - UU No. 32/2009 (Environmental Protection): 3-10 years prison
            
            **🎯 IMMEDIATE ACTIONS:**
            - Asset freezing PT SAWIT NUSANTARA & network
            - Criminal investigation coordination
            - Environmental damage assessment
            """)

def generate_str_report(investigation_data):
    """Generate enhanced STR report content"""
    case = investigation_data['case_summary']
    
    if 'SAWIT NUSANTARA' in case.get('company', ''):
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
1. PT SAWIT NUSANTARA (Front Company)
   - NPWP: 73.590.760.9-174.110
   - Direktur: Ahmad Wijaya (NIK: 1471010101800001)
   - Alamat: Jalan Sawit Raya No. 10, Pekanbaru, Riau
   - Risk Score: 95/100

2. PT KARYA UTAMA CONSULTING (Primary Shell)
   - NPWP: 82.591.670.8-175.210
   - Direktur: Ahmad Wijaya (NIK: 1471010101800001)
   - Alamat: Jalan Sudirman No. 100, Jakarta Pusat
   - Risk Score: 90/100

3. Ahmad Wijaya (Beneficial Owner)
   - NIK: 1471010101800001
   - Central controller of criminal network
   - Multiple entity ownership (6+ companies)

III. ENVIRONMENTAL CRIME EVIDENCE
--------------------------------
- Satellite imagery confirms illegal forest clearing
- Location: Hutan Lindung Riau Tengah
- Coordinates: 0.52°S, 101.43°E
- Overlap area: 5,100 hectares (35.2% of concession)
- Violation date: {(datetime.now() - timedelta(days=15)).strftime('%Y-%m-%d')}

IV. MONEY LAUNDERING PATTERN
----------------------------
1. PLACEMENT PHASE
   - TXN_SAWIT_001: Rp 45,000,000,000
   - Date: {(datetime.now() - timedelta(days=14)).strftime('%Y-%m-%d')}
   - From: PT SAWIT NUSANTARA → PT KARYA UTAMA CONSULTING
   - Timing: 1 day after forest clearing detected

2. STRUCTURING PHASE (5 transactions)
   - Total: Rp 2,200,000,000
   - Pattern: Amounts Rp 400-499M (under threshold)
   - Period: 5 consecutive days
   - Recipients: Different shell companies, same beneficial owner

3. LAYERING PHASE
   - Complex transfers through shell company network
   - Multiple bank accounts across different institutions
   - Obscured ownership through nominee arrangements

4. INTEGRATION PHASE
   - Final placement into legitimate business accounts
   - Estimated amount: Rp 8,000,000,000

V. LEGAL VIOLATIONS
------------------
1. UU No. 18/2013 (Pencegahan dan Pemberantasan Perusakan Hutan)
   - Pasal 82: Pidana 10-15 tahun + denda Rp 5-15 miliar
   
2. UU No. 8/2010 (Pencegahan dan Pemberantasan TPPU)
   - Pasal 3: Pidana 5-20 tahun + denda Rp 1-10 miliar
   
3. UU No. 32/2009 (Perlindungan dan Pengelolaan Lingkungan Hidup)
   - Pasal 98: Pidana 3-10 tahun + denda Rp 3-10 miliar

VI. INVESTIGATION STATUS
-----------------------
- Evidence collected: {len(investigation_data['evidence_collected'])} items
- Network entities identified: 8
- Money flow tracking: Complete
- Legal documentation: In progress
- Coordination: KLHK, Kejaksaan, PPATK

VII. RECOMMENDATIONS
-------------------
IMMEDIATE (0-7 days):
1. Freeze all accounts PT SAWIT NUSANTARA and shell companies
2. Asset seizure Ahmad Wijaya and affiliated entities
3. Coordinate with KLHK for environmental damage assessment
4. Criminal investigation initiation

MEDIUM TERM (1-4 weeks):
1. Field verification of forest damage coordinates
2. Complete beneficial ownership mapping
3. International cooperation for offshore account tracing
4. Prepare criminal charges documentation

LONG TERM (1-6 months):
1. Environmental restoration enforcement
2. Asset recovery for environmental compensation
3. Systemic improvements in palm oil sector monitoring
4. Policy recommendations for prevention

VIII. RISK ASSESSMENT
--------------------
Environmental Damage: CRITICAL - Irreversible forest loss
Financial Crime: HIGH - Sophisticated laundering scheme  
Prosecution Success: HIGH - Strong evidence chain
Reputational Impact: HIGH - International attention expected

---
Report prepared by: JALAK-HIJAU AI System
Investigation Team: PPATK Environmental Crime Unit
Next review: {(datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')}
Classification: RESTRICTED - Law Enforcement Only
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
    """Enhanced overview dashboard with PT SAWIT NUSANTARA focus"""
    
    # Load all data
    forest_gdf, sawit_gdf, overlap_gdf = load_geospatial_data()
    financial_data = load_financial_data()
    transactions_df, high_risk_df, clusters_df, bank_accounts_df, sawit_case_df = financial_data
    companies_df = load_company_data()
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        critical_overlaps = len(overlap_gdf[overlap_gdf.get('severity', '') == 'CRITICAL']) if len(overlap_gdf) > 0 else 1
        st.metric("🚨 Critical Cases", f"{critical_overlaps}", delta="Real-time Detection")
    
    with col2:
        sawit_amount = 67000000000 if sawit_case_df is not None and len(sawit_case_df) > 0 else 67000000000
        st.metric("💰 Suspicious Amount", f"Rp {sawit_amount/1e9:.0f}B", delta="+1 today")
    
    with col3:
        forest_damage = 5100 if len(overlap_gdf) > 0 else 5100
        st.metric("🌲 Forest Damage", f"{forest_damage:,} ha", delta="Illegal Clearing")
    
    with col4:
        st.metric("⏱️ Detection Time", "< 24 hours", delta="Real-time Alert", delta_color="inverse")
    
    # Full-width map with PT SAWIT NUSANTARA focus
    st.subheader("🗺️ Environmental Risk Map - PT SAWIT NUSANTARA Highlighted")
    
    # Center map on Riau (PT SAWIT NUSANTARA location)
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
    
    # Add palm concessions with PT SAWIT NUSANTARA highlighted
    if len(sawit_gdf) > 0:
        for idx, sawit in sawit_gdf.iterrows():
            if hasattr(sawit, 'center_lat') and hasattr(sawit, 'center_lon'):
                is_sawit_nusantara = 'SAWIT NUSANTARA' in sawit.get('company', '')
                is_overlapping = sawit.get('is_overlapping', False)
                risk_score = sawit.get('risk_score', 30)
                
                if is_sawit_nusantara:
                    color, risk_level, icon = 'red', 'CRITICAL', 'exclamation-triangle'
                    popup_extra = "<br><b style='color: red;'>🔥 UNDER INVESTIGATION</b>"
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
    st.subheader("🚨 Live Alert Feed - PT SAWIT NUSANTARA Case Active")
    
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
        },
        {
            'id': 'ALT-GEO-003', 'time': '12:30 WIB', 'location': 'Kalimantan Selatan',
            'type': 'Unauthorized Land Clearing', 'risk': 'MEDIUM',
            'company': 'PT AGRO SEJAHTERA', 
            'details': 'Satellite detected: 800 ha clearing without permit',
            'alert_source': 'geospatial'
        }
    ]
    
    # Display alerts with PT SAWIT NUSANTARA highlighted
    for alert in alerts:
        is_sawit_nusantara = 'SAWIT NUSANTARA' in alert['company']
        alert_class = "sawit-highlight" if is_sawit_nusantara else ("alert-critical" if alert['risk'] == 'CRITICAL' else "alert-warning")
        risk_class = f"risk-{alert['risk'].lower()}"
        
        icon = '🔥' if is_sawit_nusantara else ('🛰️' if alert['alert_source'] == 'geospatial' else '💰')
        
        st.markdown(f"""
        <div class="{alert_class}">
            <strong>{icon} Alert {alert['id']}</strong> - {alert['time']}<br>
            <strong>Company:</strong> {alert['company']}<br>
            <strong>Type:</strong> {alert['type']}<br>
            <strong>Details:</strong> {alert.get('details', 'N/A')}<br>
            <strong>Risk Level:</strong> <span class="{risk_class}">{alert['risk']}</span>
            {' <b>🔥 INVESTIGATION ACTIVE</b>' if is_sawit_nusantara else ''}
        </div>
        """, unsafe_allow_html=True)
        
        if st.button(f"🔍 {'View Investigation' if is_sawit_nusantara else 'Start Investigation'}", key=f"investigate_{alert['id']}"):
            start_investigation(alert['id'], alert)
            st.success(f"✅ Investigation {alert['id']} {'accessed' if is_sawit_nusantara else 'started'}!")
            st.rerun()

def create_analysis_page():
    """Enhanced analysis page with conditional controls"""
    st.header("📊 Advanced Analysis Dashboard")
    
    # Load data
    forest_gdf, sawit_gdf, overlap_gdf = load_geospatial_data()
    financial_data = load_financial_data()
    transactions_df, high_risk_df, clusters_df, bank_accounts_df, sawit_case_df = financial_data
    companies_df = load_company_data()
    
    
    # Enhanced analysis controls with conditional visibility
    col1, col2, col3 = st.columns(3)
    
    with col1:
        analysis_mode = st.selectbox("Analysis Mode", 
                                   ["ALT-CRIT-001 (PT SAWIT NUSANTARA)", "Comprehensive Overview", "Network Focus"])
    
    # Conditional controls - only show for non-case-specific modes
    is_case_specific = "ALT-CRIT-001" in analysis_mode
    
    with col2:
        if not is_case_specific:
            risk_filter = st.selectbox("Risk Level", ["All Levels", "Critical Only", "High+"])
        else:
            st.markdown("**Risk Level:** *CRITICAL (Case-specific)*")
            risk_filter = "Critical Only"
    
    with col3:
        if not is_case_specific:
            time_period = st.selectbox("Time Period", ["Last 30 days", "Last 90 days", "All Time"])
        else:
            st.markdown("**Time Period:** *Case Timeline (15 days)*")
            time_period = "Case Timeline"
    
    # Analysis based on mode
    if is_case_specific:
        create_sawit_nusantara_analysis(sawit_case_df, forest_gdf, sawit_gdf, overlap_gdf)
    else:
        create_general_analysis(transactions_df, high_risk_df, clusters_df, risk_filter, time_period)

def create_sawit_nusantara_analysis(sawit_case_df, forest_gdf, sawit_gdf, overlap_gdf):
    """Detailed PT SAWIT NUSANTARA case analysis"""
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🛰️ Geospatial Evidence")
        
        # PT SAWIT NUSANTARA specific metrics
        st.metric("🌲 Forest Area Damaged", "5,100 ha")
        st.metric("📍 Overlap Percentage", "35.2%")
        st.metric("🚨 Violation Severity", "CRITICAL")
        st.metric("📍 Coordinates", "0.52°S, 101.43°E")
    
    with col2:
        st.markdown("#### 💰 Financial Evidence")
        
        if sawit_case_df is not None and len(sawit_case_df) > 0:
            total_amount = sawit_case_df['amount_idr'].sum()
            transaction_count = len(sawit_case_df)
        else:
            total_amount = 67000000000
            transaction_count = 12
        
        st.metric("💰 Total Suspicious Amount", f"Rp {total_amount/1e9:.1f}B")
        st.metric("📊 Transaction Count", f"{transaction_count}")
        st.metric("🏢 Entities Involved", "6")
        st.metric("👤 Beneficial Owner", "Ahmad Wijaya")
    
    # Single column layout for charts
    # Money flow diagram
    st.markdown("#### 🔄 Money Flow Pattern")
    flow_data = pd.DataFrame({
        'Stage': ['Placement', 'Structuring', 'Layering', 'Integration'],
        'Amount_B': [45, 22, 15, 8],
        'Description': ['Initial transfer to shell', 'Under-threshold splits', 'Multi-entity transfers', 'Final placement'],
        'Risk_Score': [95, 88, 82, 75]
    })
    
    fig_flow = px.bar(flow_data, x='Stage', y='Amount_B', 
                     color='Risk_Score', color_continuous_scale='Reds',
                     title="💰 Money Laundering Stages (Billion Rp)",
                     hover_data=['Description'])
    fig_flow.update_layout(height=400)
    st.plotly_chart(fig_flow, use_container_width=True)
    
    # Enhanced timeline visualization replacing Complete Case Timeline Analysis
    st.markdown("#### 📊 Chronological Case Timeline - Interactive")
    
    # Create comprehensive timeline data for PT SAWIT NUSANTARA
    base_date = datetime.now() - timedelta(days=15)
    timeline_events = []
    
    # Environmental track events
    timeline_events.extend([
        {
            'date': base_date,
            'event_type': 'Environmental',
            'track': 'Environmental Crime',
            'event': 'Forest clearing initiation detected',
            'details': '🛰️ Satellite imagery shows initial clearing activity in Hutan Lindung Riau',
            'amount': 0,
            'risk_level': 85,
            'color': '#228B22',
            'size': 15,
            'y_position': 3
        },
        {
            'date': base_date + timedelta(days=3),
            'event_type': 'Environmental',
            'track': 'Environmental Crime', 
            'event': 'Major clearing expansion',
            'details': '🌲 5,100 hectares cleared - 35.2% overlap with protected area confirmed',
            'amount': 0,
            'risk_level': 95,
            'color': '#DC3545',
            'size': 25,
            'y_position': 3
        }
    ])
    
    # Financial track events - overlapping with environmental
    timeline_events.extend([
        {
            'date': base_date + timedelta(days=1),
            'event_type': 'Financial',
            'track': 'Money Laundering',
            'event': 'Placement: Rp 45B transfer',
            'details': '💰 PT SAWIT NUSANTARA → PT KARYA UTAMA CONSULTING (Rp 45,000,000,000)',
            'amount': 45000000000,
            'risk_level': 95,
            'color': '#FF6B35',
            'size': 30,
            'y_position': 2
        },
        {
            'date': base_date + timedelta(days=2),
            'event_type': 'Financial',
            'track': 'Money Laundering',
            'event': 'Structuring begins',
            'details': '📊 First transaction Rp 450M - under threshold pattern starts',
            'amount': 450000000,
            'risk_level': 88,
            'color': '#FFA500',
            'size': 18,
            'y_position': 2
        },
        {
            'date': base_date + timedelta(days=3),
            'event_type': 'Financial',
            'track': 'Money Laundering',
            'event': 'Structuring continues',
            'details': '📊 Transaction 2: Rp 485M to Shell Company 1',
            'amount': 485000000,
            'risk_level': 85,
            'color': '#FFA500',
            'size': 16,
            'y_position': 2
        },
        {
            'date': base_date + timedelta(days=4),
            'event_type': 'Financial',
            'track': 'Money Laundering',
            'event': 'Peak structuring activity',
            'details': '📊 Transactions 3-5: Multiple Rp 400-499M transfers (same day as major clearing)',
            'amount': 1350000000,
            'risk_level': 92,
            'color': '#FF6B35',
            'size': 22,
            'y_position': 2
        },
        {
            'date': base_date + timedelta(days=7),
            'event_type': 'Financial',
            'track': 'Money Laundering',
            'event': 'Layering phase',
            'details': '🔄 Complex transfers through shell company network - obscuring trail',
            'amount': 15000000000,
            'risk_level': 80,
            'color': '#CD5C5C',
            'size': 20,
            'y_position': 2
        },
        {
            'date': base_date + timedelta(days=10),
            'event_type': 'Financial',
            'track': 'Money Laundering',
            'event': 'Integration phase',
            'details': '🏢 Final placement into legitimate business accounts',
            'amount': 8000000000,
            'risk_level': 75,
            'color': '#4682B4',
            'size': 18,
            'y_position': 2
        }
    ])
    
    # Investigation track events
    timeline_events.extend([
        {
            'date': base_date + timedelta(days=15),
            'event_type': 'Investigation',
            'track': 'JALAK-HIJAU System',
            'event': 'Alert ALT-CRIT-001 triggered',
            'details': '🚨 AI correlation: Environmental + Financial patterns detected',
            'amount': 0,
            'risk_level': 100,
            'color': '#6A4C93',
            'size': 25,
            'y_position': 1
        },
        {
            'date': datetime.now().date(),
            'event_type': 'Investigation',
            'track': 'JALAK-HIJAU System',
            'event': 'Investigation active (75% complete)',
            'details': '🔍 Evidence collection, STR preparation, coordination with KLHK',
            'amount': 0,
            'risk_level': 90,
            'color': '#8B0000',
            'size': 20,
            'y_position': 1
        }
    ])
    
    # Convert to DataFrame
    timeline_df = pd.DataFrame(timeline_events)
    timeline_df['date'] = pd.to_datetime(timeline_df['date'])
    
    # Create interactive timeline with multiple tracks
    fig_timeline = go.Figure()
    
    # Add events by track with different y-positions
    tracks = {
        'JALAK-HIJAU System': 1,
        'Money Laundering': 2, 
        'Environmental Crime': 3
    }
    
    for track_name, y_pos in tracks.items():
        track_data = timeline_df[timeline_df['track'] == track_name]
        
        fig_timeline.add_trace(go.Scatter(
            x=track_data['date'],
            y=[y_pos] * len(track_data),
            mode='markers+text',
            marker=dict(
                size=track_data['size'],
                color=track_data['color'],
                line=dict(width=2, color='white'),
                opacity=0.8
            ),
            text=track_data['event'],
            textposition="top center",
            textfont=dict(size=10),
            hovertemplate='<b>%{text}</b><br>' +
                         'Date: %{x}<br>' +
                         'Track: ' + track_name + '<br>' +
                         'Details: %{customdata}<br>' +
                         '<extra></extra>',
            customdata=track_data['details'],
            name=track_name,
            showlegend=True
        ))
    
    # Add connecting lines to show causality
    # Environmental → Financial correlation
    env_major = timeline_df[(timeline_df['event'] == 'Major clearing expansion')]['date'].iloc[0]
    fin_peak = timeline_df[(timeline_df['event'] == 'Peak structuring activity')]['date'].iloc[0]
    
    fig_timeline.add_shape(
        type="line",
        x0=env_major, y0=3,
        x1=fin_peak, y1=2,
        line=dict(color="red", width=2, dash="dash"),
        opacity=0.6
    )
    
    # Add annotation for correlation
    fig_timeline.add_annotation(
        x=fin_peak,
        y=2.5,
        text="🔗 Correlation:<br>Same-day activity",
        showarrow=True,
        arrowhead=2,
        arrowsize=1,
        arrowwidth=2,
        arrowcolor="red",
        font=dict(size=10, color="red"),
        bgcolor="rgba(255,255,255,0.8)",
        bordercolor="red",
        borderwidth=1
    )
    
    # Update layout
    fig_timeline.update_layout(

        xaxis=dict(
            title="Date",
            showgrid=True,
            gridwidth=1,
            gridcolor='lightgray'
        ),
        yaxis=dict(
            title="Activity Track",
            tickvals=[1, 2, 3],
            ticktext=['Investigation', 'Financial Crime', 'Environmental Crime'],
            range=[0.5, 3.5],
            showgrid=True,
            gridwidth=1,
            gridcolor='lightgray'
        ),
        height=500,
        hovermode='closest',
        plot_bgcolor='rgba(248,248,255,0.9)',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    st.plotly_chart(fig_timeline, use_container_width=True)
    
    # Network visualization for case-specific analysis
    st.markdown("#### 🕸️ Case-Specific Network Analysis")
    network_fig = create_enhanced_network_visualization({})
    st.plotly_chart(network_fig, use_container_width=True)

def create_general_analysis(transactions_df, high_risk_df, clusters_df, risk_filter, time_period):
    """General analysis dashboard with filters"""
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📈 Transaction Trends")
        if len(transactions_df) > 0:
            # Apply time filter
            if time_period == "Last 30 days":
                cutoff_date = datetime.now() - timedelta(days=30)
                filtered_df = transactions_df[transactions_df['transaction_date'] >= cutoff_date]
            elif time_period == "Last 90 days":
                cutoff_date = datetime.now() - timedelta(days=90)
                filtered_df = transactions_df[transactions_df['transaction_date'] >= cutoff_date]
            else:
                filtered_df = transactions_df
            
            daily_stats = filtered_df.groupby(filtered_df['transaction_date'].dt.date)['amount_idr'].sum().reset_index()
            fig_trend = px.line(daily_stats.tail(30), x='transaction_date', y='amount_idr',
                               title=f"Daily Transaction Volume - {time_period}")
            st.plotly_chart(fig_trend, use_container_width=True)
        else:
            st.info("No transaction data available")
    
    with col2:
        st.markdown("#### 🎯 Risk Distribution")
        if len(high_risk_df) > 0:
            # Apply risk filter
            if risk_filter == "Critical Only":
                filtered_risk_df = high_risk_df[high_risk_df['risk_score'] >= 90]
            elif risk_filter == "High+":
                filtered_risk_df = high_risk_df[high_risk_df['risk_score'] >= 70]
            else:
                filtered_risk_df = high_risk_df
            
            fig_risk = px.histogram(filtered_risk_df, x='risk_score', nbins=20,
                                   title=f"Risk Score Distribution - {risk_filter}")
            st.plotly_chart(fig_risk, use_container_width=True)
        else:
            st.info("No high-risk data available")
    
    # Cluster analysis for general mode
    if len(clusters_df) > 0:
        st.markdown("#### 🕸️ Detected Transaction Clusters")
        
        cluster_summary = clusters_df.groupby('risk_level').agg({
            'cluster_id': 'count',
            'total_amount': 'sum',
            'transaction_count': 'sum'
        }).reset_index()
        
        fig_clusters = px.bar(cluster_summary, x='risk_level', y='cluster_id',
                             title="Transaction Clusters by Risk Level")
        st.plotly_chart(fig_clusters, use_container_width=True)

def create_ai_assistant():
    """Enhanced AI Assistant with PT SAWIT NUSANTARA context"""
    st.header("🤖 AI Assistant JALAK-HIJAU")
    st.subheader("Expert Analysis & Investigation Support")
    
    client = setup_openai()
    
    
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
                                  placeholder="Contoh: Analisis pola money laundering PT SAWIT NUSANTARA")
        
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
            "Analisis kasus PT SAWIT NUSANTARA",
            "Pola structuring yang terdeteksi", 
            "Network shell companies",
            "Rekomendasi investigasi lanjutan",
            "Generate laporan executive summary",
            "Prediksi modus operandi serupa",
            "Legal violations analysis",
            "Environmental impact assessment"
        ]
        
        for query in expert_queries:
            if st.button(f"💡 {query}", key=f"expert_{hash(query)}"):
                st.session_state.chat_history.append({'role': 'user', 'content': query})
                
                data_context = "PT SAWIT NUSANTARA case context with environmental and financial evidence..."
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
        - 🛰️ Satellite imagery analysis
        - 🎯 Investigation prioritization
        """)

def create_report_generation():
    """Enhanced automatic report generation page"""
    st.header("📄 Automatic Report Generation")
    st.subheader("AI-Powered Investigation Reports")
    
    # Load data for reports
    financial_data = load_financial_data()
    transactions_df, high_risk_df, clusters_df, bank_accounts_df, sawit_case_df = financial_data
    companies_df = load_company_data()
    
    # Report type selection
    col1, col2 = st.columns([2, 1])
    
    with col1:
        report_type = st.selectbox("Select Report Type", [
            "ALT-CRIT-001 (PT SAWIT NUSANTARA)",
            "📊 Weekly Risk Summary", 
            "🕸️ Network Analysis Report",
            "🛰️ Environmental Impact Assessment",
            "💰 STR Executive Summary",
            "📈 Trend Analysis Report",
            "⚖️ Legal Violation Analysis",
            "🎯 Investigation Progress Report"
        ])
        
        if st.button("🚀 Generate Report", type="primary"):
            with st.spinner("Generating comprehensive report..."):
                report_content = generate_automatic_report(report_type, sawit_case_df, high_risk_df, clusters_df)
                
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
                <li>🛰️ Satellite evidence</li>
                <li>💰 Financial flow analysis</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        

def generate_automatic_report(report_type, sawit_case_df, high_risk_df, clusters_df):
    """Generate different types of reports"""
    
    if "PT SAWIT NUSANTARA" in report_type:
        return f"""
# PT SAWIT NUSANTARA - CRITICAL CASE REPORT

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Classification:** CRITICAL PRIORITY  
**Case ID:** ALT-CRIT-001

## EXECUTIVE SUMMARY

PT SAWIT NUSANTARA telah melakukan kejahatan lingkungan sistematis dengan mengkliring 5,100 hektar Hutan Lindung Riau secara ilegal, diikuti dengan pencucian uang senilai Rp 67+ miliar melalui jaringan shell companies yang dipimpin oleh Ahmad Wijaya.

## KEY FINDINGS

### 🛰️ Environmental Crime Evidence
- **Illegal Forest Clearing:** 5,100 hectares (35.2% overlap)
- **Protected Area:** Hutan Lindung Riau Tengah
- **Coordinates:** 0.52°S, 101.43°E
- **Detection Method:** Satellite imagery analysis (Landsat/Sentinel-2)
- **Environmental Damage:** Carbon emissions, biodiversity loss, water system impact

### 💰 Money Laundering Evidence
- **Total Suspicious Amount:** Rp 67,200,000,000
- **Primary Transfer:** Rp 45B to PT KARYA UTAMA CONSULTING (Day +1 after clearing)
- **Structuring Pattern:** 5 transactions under Rp 500M threshold
- **Layering:** Multiple shell company transfers across 6 entities
- **Integration:** Final placement into legitimate business accounts

### 🏢 Corporate Network Analysis
- **Beneficial Owner:** Ahmad Wijaya (NIK: 1471010101800001)
- **Front Company:** PT SAWIT NUSANTARA (operational entity)
- **Primary Shell:** PT KARYA UTAMA CONSULTING (main receiver)
- **Secondary Shells:** 4+ additional layering entities
- **Bank Accounts:** 8+ accounts across multiple institutions

## DETAILED TIMELINE OF EVENTS

- **Day -15:** Satellite detects forest clearing activity initiation
- **Day -14:** Rp 45B transfer to PT KARYA UTAMA CONSULTING
- **Day -13 to -9:** Structuring pattern (5 transactions @Rp 400-499M)
- **Day -7 to -3:** Complex layering through shell company network
- **Day -1:** Integration phase into legitimate accounts
- **Day 0:** JALAK-HIJAU alert triggered (ALT-CRIT-001)
- **Today:** Full investigation active with 75% completion

## LEGAL VIOLATIONS ANALYSIS

### Primary Violations
1. **UU No. 18/2013 (Pencegahan dan Pemberantasan Perusakan Hutan)**
   - Pasal 82: Pidana penjara 10-15 tahun + denda Rp 5-15 miliar
   - Evidence: Satellite imagery, field verification pending

2. **UU No. 8/2010 (Pencegahan dan Pemberantasan Tindak Pidana Pencucian Uang)**
   - Pasal 3: Pidana penjara 5-20 tahun + denda Rp 1-10 miliar
   - Evidence: Complete money flow documentation

3. **UU No. 32/2009 (Perlindungan dan Pengelolaan Lingkungan Hidup)**
   - Pasal 98: Pidana penjara 3-10 tahun + denda Rp 3-10 miliar
   - Evidence: Environmental damage assessment

### Aggravating Factors
- Systematic and organized nature of crimes
- Significant environmental damage (5,100 ha)
- Large financial amounts (Rp 67B+)
- Multiple entity involvement
- Sophisticated money laundering scheme

## INVESTIGATION PROGRESS

### Evidence Collected (7/10 items)
1. ✅ Satellite imagery showing forest clearing
2. ✅ Financial transaction records (Rp 67B+)
3. ✅ Corporate ownership mapping
4. ✅ Bank account identification
5. ✅ Structuring pattern analysis
6. ✅ Shell company network mapping
7. ✅ Beneficial ownership documentation
8. 🔄 Field verification (in progress)
9. 🔄 International account tracing (pending)
10. 🔄 Asset valuation (pending)

### Coordination Status
- **PPATK:** Investigation lead, STR preparation
- **KLHK:** Environmental assessment, permit verification
- **Kejaksaan:** Criminal charges preparation
- **POLRI:** Field investigation support
- **BI/OJK:** Banking sector coordination

## RECOMMENDATIONS

### Immediate Actions (0-7 days)
1. 🏦 **Asset Freezing:** All PT SAWIT NUSANTARA and shell company accounts
2. 📞 **KLHK Coordination:** Environmental damage verification
3. 👤 **Subject Monitoring:** Ahmad Wijaya and associates
4. ⚖️ **STR Filing:** Formal suspicious transaction report
5. 🌍 **International Alerts:** Potential offshore account tracing

### Medium Term Actions (1-4 weeks)
1. 🔍 **Field Verification:** Physical inspection of forest damage
2. 📋 **Complete Network Mapping:** All related entities and individuals
3. 🏛️ **Legal Proceedings:** Criminal charge preparation
4. 📺 **Public Disclosure:** Deterrent effect consideration
5. 🤝 **Inter-agency Coordination:** Enhanced information sharing

### Long Term Actions (1-6 months)
1. 🛠️ **System Enhancement:** Based on case lessons learned
2. 📚 **Training Programs:** Pattern recognition for similar cases
3. 📊 **Policy Recommendations:** Prevention mechanism improvements
4. 🌱 **Environmental Restoration:** Forest rehabilitation planning
5. 💰 **Asset Recovery:** Environmental damage compensation

## RISK ASSESSMENT

| Risk Category | Level | Impact | Mitigation |
|---------------|-------|---------|------------|
| Environmental Damage | CRITICAL | Irreversible forest loss | Immediate restoration planning |
| Financial Crime | HIGH | Sophisticated laundering | Complete asset tracing |
| Reputational Risk | HIGH | International attention | Proactive public communication |
| Investigation Success | HIGH | Strong evidence chain | Continued evidence collection |
| Legal Prosecution | MEDIUM | Complex multi-jurisdiction | Enhanced coordination |

## SUCCESS METRICS

- **Investigation Completion:** 75% (Target: 100% in 2 days)
- **Evidence Quality:** HIGH (7/10 items collected)
- **Prosecution Readiness:** 65% (Target: 90% in 1 week)
- **Asset Recovery Potential:** 80% (Accounts identified)
- **Environmental Impact Documentation:** 90% (Satellite evidence complete)

---
**Report Classification:** RESTRICTED - Law Enforcement Only  
**Generated by:** JALAK-HIJAU AI System v2.0  
**Next Review:** {(datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d')}  
**Investigation Team:** PPATK Environmental Crime Unit  
**Contact:** jalak-hijau-investigations@ppatk.go.id
"""
    
    elif "Weekly Risk" in report_type:
        return f"""
# 📊 WEEKLY RISK SUMMARY REPORT

**Period:** {(datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')} to {datetime.now().strftime('%Y-%m-%d')}  
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## SUMMARY METRICS

- **New Alerts:** 25 (↑18% from last week)
- **Critical Cases:** 1 (PT SAWIT NUSANTARA - ACTIVE INVESTIGATION)
- **High Risk Transactions:** 167 (Total value: Rp 3.2T)
- **Environmental Violations:** 4 confirmed, 2 under verification
- **Money Laundering Networks:** 3 major networks identified

## TOP RISKS THIS WEEK

### 1. PT SAWIT NUSANTARA - CRITICAL 🔥
   - **Status:** Active investigation (75% complete)
   - **Issues:** Forest clearing + money laundering
   - **Amount:** Rp 67B+ suspicious transfers
   - **Action:** STR prepared, asset freezing recommended

### 2. PT HIJAU SAWIT KALIMANTAN - HIGH ⚠️
   - **Status:** Under monitoring
   - **Issues:** Structuring pattern detected
   - **Amount:** Rp 4.2B across 8 transactions
   - **Action:** Enhanced surveillance initiated

### 3. Financial Network Cluster-007 - MEDIUM 📊
   - **Status:** Analysis phase
   - **Issues:** Complex layering scheme
   - **Amount:** Rp 2.8B cross-border flows
   - **Action:** International cooperation requested

## TREND ANALYSIS

### Positive Developments
- ✅ Environmental crime detection accuracy improved 25%
- ✅ Satellite integration reducing false positives
- ✅ Cross-sector data sharing enhanced
- ✅ Average detection time reduced to <24 hours

### Concerning Trends
- ⚠️ Money laundering schemes becoming more sophisticated
- ⚠️ Increased use of cryptocurrency mixing services
- ⚠️ Shell company networks expanding internationally
- ⚠️ Environmental damage accelerating in remote areas

## RECOMMENDATIONS

### Immediate Actions
1. Continue PT SAWIT NUSANTARA investigation priority
2. Enhance monitoring of Kalimantan region
3. Strengthen international cooperation protocols
4. Deploy additional satellite coverage

### Medium-term Improvements
1. AI model retraining with new patterns
2. Enhanced shell company detection algorithms
3. Real-time environmental monitoring expansion
4. Cross-border information sharing agreements

---
**Next weekly report:** {(datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')}
**Distribution:** PPATK Leadership, Investigation Teams, Partner Agencies
"""
    
    else:
        return f"""
# 📄 JALAK-HIJAU SYSTEM REPORT

**Type:** {report_type}  
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## SYSTEM STATUS

JALAK-HIJAU operational and detecting environmental crimes effectively.
AI-powered analysis providing actionable intelligence for PPATK.

### Current Capabilities
- **Real-time satellite monitoring:** Active across Indonesia
- **Financial transaction analysis:** 24/7 processing
- **AI-powered risk scoring:** 89% accuracy rate
- **Cross-sector data integration:** 5 major agencies connected

## CURRENT CASES

### Active Investigations
1. **PT SAWIT NUSANTARA (ALT-CRIT-001):** Critical priority, 75% complete
2. **Network Cluster-007:** Medium priority, analysis phase
3. **Regional Monitoring:** 15 entities under surveillance

### Key Performance Indicators
- **Detection Speed:** <24 hours (target: <12 hours)
- **Investigation Success Rate:** 89% (target: 90%)
- **False Positive Rate:** 12% (target: <10%)
- **Environmental Coverage:** 85% (target: 95%)

## RECOMMENDATIONS

### System Enhancements
1. Continue satellite coverage expansion
2. Enhance AI model training with new patterns
3. Strengthen inter-agency data sharing
4. Develop predictive analytics capabilities

### Operational Improvements
1. Increase investigation team capacity
2. Enhance field verification protocols
3. Strengthen international cooperation
4. Develop public-private partnerships

---
**Report generated by JALAK-HIJAU AI System**
**Contact:** system-admin@jalak-hijau.ppatk.go.id
"""

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
    try:
        st.sidebar.image("logotext.png", width=280)
    except:
        st.sidebar.markdown("# 🛰️ JALAK-HIJAU")
    
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
    try:
        data_status = "✅ Live" if (Path("transactions.csv").exists() or Path("data/transactions.csv").exists()) else "⚠️ Demo" 
    except:
        data_status = "⚠️ Demo"
    
    try:
        geo_status = "✅ Active" if Path("forest.shp").exists() else "⚠️ Demo"
    except:
        geo_status = "⚠️ Demo"
    
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
