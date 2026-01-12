import os
import pandas as pd
import yfinance as yf
from sqlalchemy import create_engine, text

USER = os.getenv('POSTGRES_USER')
PASSWORD = os.getenv('POSTGRES_PASSWORD')
DB = os.getenv('POSTGRES_DB')
HOST = 'db'
PORT = '5432'

url = f"postgresql://{USER}:{PASSWORD}@{HOST}:{PORT}/{DB}"
engine = create_engine(url)

def get_tickers():
    df = pd.read_sql("SELECT code_boursier FROM entreprise", engine)
    return df['code_boursier'].tolist()

def get_id(ticker):
    sql = f"SELECT id_entreprise FROM entreprise WHERE code_boursier = '{ticker}'"
    df = pd.read_sql(sql, engine)
    return df['id_entreprise'].iloc[0]

def last_date(company_id):
    sql = text(f"SELECT MAX(date_jour) FROM historique_bourse WHERE id_entreprise = {company_id}")
    with engine.connect() as conn:
        result = conn.execute(sql).scalar()
    return result

def transform(df):
    df = df.sort_index()
    df['rendement_jour'] = df['Close'].pct_change() * 100
    df['moyenne_mobile_50'] = df['Close'].rolling(window=50).mean()
    df['volatilite_30'] = df['rendement_jour'].rolling(window=30).std()
    df = df.dropna()
    return df

def run_etl(ticker):
    company_id = get_id(ticker)
    
    date_in_db = last_date(company_id)
    print(f"Traitement de: {ticker} (ID={company_id})")
    
    if date_in_db:
        print(f"    Dernière date: {date_in_db}")
    else:
        print("    Aucune donnée")

    stock = yf.Ticker(ticker)
    df = stock.history(period="5y")

    if df.empty:
        print(f"Pas de données pour: {ticker}")
        return
    
    df = transform(df)
    df = df.reset_index()
    
    if date_in_db:
        date_in_db = pd.to_datetime(date_in_db).tz_localize(df['Date'].dt.tz)
        new_rows = df[df['Date'] > date_in_db].copy()
        
        if new_rows.empty:
            print("    Base déjà à jour")
            return        
        df_final = new_rows.copy() 
        print(f"    Nouvelles lignes à ajouter : {len(df_final)}")
    else:
        df_final = df.copy()

    df_final['Date'] = df_final['Date'].dt.date

    df_final = df_final[['Date', 'Close', 'Volume', 'rendement_jour', 'volatilite_30', 'moyenne_mobile_50']]
    df_final.columns = [
        'date_jour', 
        'prix_fermeture', 
        'volume_echange', 
        'rendement_jour', 
        'volatilite_30', 
        'moyenne_mobile_50'
    ]
    df_final['id_entreprise'] = company_id

    df_final.to_sql('historique_bourse', engine, if_exists='append', index=False)
    print(f"Success: {len(df_final)} rows loaded.")

if __name__ == '__main__':
    try:
        tickers = get_tickers()
        for ticker in tickers:
            run_etl(ticker)
        print("Pipeline finished successfully.")

    except Exception as e:
        print("Critical Error:", e)