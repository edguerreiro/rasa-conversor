import pandas as pd 
import streamlit as st
from datetime import datetime

if 'processed_df' not in st.session_state:
    st.session_state.processed_df = None
if 'total_royalty' not in st.session_state:
    st.session_state.total_royalty = 0
if 'total_royalty_gross' not in st.session_state:
    st.session_state.total_royalty_gross = 0

st.title('Altafonte Conversor')

tax_rate = st.number_input(
    'Taxa de imposto (%)',
    min_value=0.0,
    max_value=100.0,
    value=28.5,
    step=0.1
)

def calculate_total(df, column):
    return df[column].sum()

def clean_ean(ean):
    # Remove Excel formula formatting
    return ean.strip('=()""')

def process_altafonte_statement(file, tax_rate):
    try:
        df = pd.read_csv(file, sep=';', decimal=',', thousands='.', encoding='latin1')
        filtered_df = df[df['SELLO'].isin(['Elemess'])].copy()
        
        filtered_df['EAN'] = filtered_df['EAN'].apply(clean_ean)
        
        st.session_state.total_royalty_gross = calculate_total(filtered_df, 'NET')
        filtered_df['NET'] = filtered_df['NET'] * (1 - tax_rate / 100)
        st.session_state.total_royalty = calculate_total(filtered_df, 'NET')
        
        for col in ['BRUTO', 'NET', 'CPM']:
            filtered_df[col] = filtered_df[col].apply(lambda x: f"{x:,.6f}".replace(",", "@").replace(".", ",").replace("@", "."))
        
        return filtered_df
    except Exception as e:
        st.error(f'Erro ao processar arquivo: {str(e)}')
        return None

uploaded_file = st.file_uploader('Upload statement', type=['csv'])

if uploaded_file:
    try:
        st.session_state.processed_df = process_altafonte_statement(uploaded_file, tax_rate)
        
        if st.session_state.processed_df is not None:
            st.info(f'⚠️ Mostrando dados processados com desconto de {tax_rate}%')
            
            col1, col2 = st.columns([1, 1])
            with col1:
                st.metric(
                    label="Total de Royalties Gross",
                    value=f"R$ {st.session_state.total_royalty_gross:,.2f}"
                )
            with col2:
                st.metric(
                    label="Total de Royalties com desconto",
                    value=f"R$ {st.session_state.total_royalty:,.2f}"
                )
            
            st.dataframe(st.session_state.processed_df)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            csv = st.session_state.processed_df.to_csv(index=False, sep=',', encoding='latin1').encode('UTF-8')
            st.download_button(
                label="Download CSV processado",
                data=csv,
                file_name=f"processed_statement_{timestamp}.csv",
                mime="text/csv"
            )
    except Exception as e:
        st.error(f"Erro ao carregar o arquivo: {e}")