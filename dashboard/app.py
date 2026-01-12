import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
import plotly.graph_objects as go
import os

st.set_page_config(page_title="Risk Monitor", layout="wide", initial_sidebar_state="expanded")


st.markdown("""
    <style>
    .block-container {padding-top: 1rem; padding-bottom: 0rem;}
    h1 {font-size: 2rem;}
    </style>
    """, unsafe_allow_html=True)


USER = os.getenv('POSTGRES_USER')
PASSWORD = os.getenv('POSTGRES_PASSWORD')
DB = os.getenv('POSTGRES_DB')
HOST = 'db'
PORT = '5432'

@st.cache_resource
def get_db_engine():
    url = f"postgresql://{USER}:{PASSWORD}@{HOST}:{PORT}/{DB}"
    return create_engine(url)

engine = get_db_engine()

@st.cache_data
def get_companies():
    return pd.read_sql("SELECT * FROM entreprise ORDER BY code_boursier", engine)

@st.cache_data
def get_history(company_id):
    query = text(f"""
        SELECT date_jour, prix_fermeture, moyenne_mobile_50, volatilite_30 
        FROM historique_bourse 
        WHERE id_entreprise = {company_id} 
        ORDER BY date_jour ASC
    """)
    return pd.read_sql(query, engine)

st.sidebar.title("Configuration")

try:
    df_companies = get_companies()
    

    company_name = st.sidebar.selectbox(
        "Actif",
        df_companies['nom'].tolist()
    )
    

    selected_company = df_companies[df_companies['nom'] == company_name].iloc[0]
    company_id = selected_company['id_entreprise']
    ticker = selected_company['code_boursier']
    sector = selected_company['secteur']

    st.sidebar.divider()
    st.sidebar.info(f"Ticker: {ticker}\n\nSecteur: {sector}")

except Exception:
    st.error("Erreur connexion BDD.")
    st.stop()

col_title, col_logo = st.columns([3, 1])
with col_title:
    st.title(f"{company_name} ({ticker})")
    st.caption(f"Secteur : {sector} | Devise : EUR")

# Chargement données
df_history = get_history(company_id)

if not df_history.empty:
    last_row = df_history.iloc[-1]
    prev_row = df_history.iloc[-2] if len(df_history) > 1 else last_row

    # Calcul variation journalière
    var_day = ((last_row['prix_fermeture'] - prev_row['prix_fermeture']) / prev_row['prix_fermeture']) * 100

    #  SECTION KPI 
    st.divider()
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)

    kpi1.metric(
        label="Dernier Prix", 
        value=f"{last_row['prix_fermeture']:.2f} €", 
        delta=f"{var_day:.2f} %"
    )
    kpi2.metric(
        label="Moyenne Mobile (50j)", 
        value=f"{last_row['moyenne_mobile_50']:.2f} €"
    )
    kpi3.metric(
        label="Volatilité (30j)", 
        value=f"{last_row['volatilite_30']:.2f} %",
        delta_color="inverse" 
    )
    kpi4.metric(
        label="Points de données",
        value=len(df_history)
    )
    st.divider()

    st.subheader("Analyse Technique")
    
    fig_price = go.Figure()
    
    fig_price.add_trace(go.Scatter(
        x=df_history['date_jour'], 
        y=df_history['prix_fermeture'],
        mode='lines',
        name='Close',
        line=dict(color='#0052cc', width=1.5) 
    ))

    fig_price.add_trace(go.Scatter(
        x=df_history['date_jour'], 
        y=df_history['moyenne_mobile_50'],
        mode='lines',
        name='MA 50',
        line=dict(color='#ff9900', width=1.5, dash='dash')
    ))

    fig_price.update_layout(
        height=450,
        margin=dict(l=20, r=20, t=20, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig_price, use_container_width=True)

    st.subheader("Métriques de Risque")

    fig_vol = go.Figure()

    fig_vol.add_trace(go.Scatter(
        x=df_history['date_jour'], 
        y=df_history['volatilite_30'],
        mode='lines',
        name='Volatilité',
        fill='tozeroy',
        line=dict(color='#dc3545', width=1) 
    ))

    fig_vol.update_layout(
        height=250,
        margin=dict(l=20, r=20, t=20, b=20),
        yaxis_title="Volatilité (%)"
    )
    st.plotly_chart(fig_vol, use_container_width=True)

else:
    st.warning("Données insuffisantes.")