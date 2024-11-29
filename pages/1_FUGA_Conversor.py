import pandas as pd
import streamlit as st

# Inicialização do estado da sessão
if 'processed_df' not in st.session_state:
    st.session_state.processed_df = None
if 'total_royalty' not in st.session_state:
    st.session_state.total_royalty = 0
if 'total_royalty_gross' not in st.session_state:
    st.session_state.total_royalty_gross = 0

st.title('FUGA Conversor')

tax_rate = st.number_input(
    'Taxa de imposto (%)',
    min_value=0.0,
    max_value=100.0,
    value=18.5,
    step=0.1
)

def process_fuga_statement(file, tax_rate):
    try:
        df = pd.read_csv(file, sep=',', decimal='.')
        filtered_df = df[df['Product Label'].isin(['Elemess', 'Elemess Label Services'])]
        
        st.session_state.total_royalty_gross = filtered_df['Reported Royalty'].sum()
        filtered_df['Reported Royalty'] = filtered_df['Reported Royalty'] * (1 - tax_rate / 100)
        st.session_state.total_royalty = filtered_df['Reported Royalty'].sum()
        
        return filtered_df
    except Exception as e:
        st.error(f'Erro ao processar arquivo: {str(e)}')
        return None

uploaded_file = st.file_uploader('Upload statement', type=['csv'])

if uploaded_file:
    try:
        st.session_state.processed_df = process_fuga_statement(uploaded_file, tax_rate)
        
        if st.session_state.processed_df is not None:
            st.info(f'⚠️ Mostrando dados processados com desconto de {tax_rate}%')
            
            col1, col2 = st.columns([1, 1])
            with col1:
                st.metric(
                    label="Total de Royalties Calculados",
                    value=f"{st.session_state.total_royalty_gross:,.2f}"
                )
            with col2:
                st.metric(
                    label="Total de Royalties com desconto",
                    value=f"{st.session_state.total_royalty:,.2f}"
                )
            
            st.dataframe(st.session_state.processed_df)
            
            csv = st.session_state.processed_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Download CSV processado",
                data=csv,
                file_name="processed_statement.csv",
                mime="text/csv"
            )
    except Exception as e:
        st.error(f"Erro ao carregar o arquivo: {e}")