import pandas as pd
import streamlit as st
import io
from typing import Optional, Dict, Any



class StatementProcessor:
    def __init__(self):
        self.initialize_session_state()
        
    @staticmethod
    def initialize_session_state():
        if 'processed_df' not in st.session_state:
            st.session_state.processed_df = None
        if 'total_royalty' not in st.session_state:
            st.session_state.total_royalty = 0
        if 'total_royalty_gross' not in st.session_state:
            st.session_state.total_royalty_gross = 0
    
    def process_tax(self, df: pd.DataFrame, royalty_column: str) -> float:
        return df[royalty_column].sum()
    
    def format_date(self, series, is_start_date=False):  # Adicione self como primeiro parâmetro
        if pd.isna(series).all():
            return series
        dates = pd.to_datetime(series)
        if is_start_date:
            return dates.dt.strftime('01/%m/%Y')
        return dates.dt.strftime('%d/%m/%Y')
    
    def transform_to_template(self, df: pd.DataFrame) -> pd.DataFrame:
        
        template_columns = [
            'Start Date', 'End Date', 'Country', 'UPC', 'ISRC', 'Title',
            'Net. PPD', 'Total Net. PPD', 'Gross PPD', 'Total Gross PPD',
            'Gross Royalty', 'Net. Revenue', 'Consumer Price', 'Total Consumer Price',
            'Net. Royalty', 'Currency', 'Quantity', 'Sale Type', 'User Type',
            'Artist', 'Release Name', 'Store Name', 'Device', 'Label', 'DSP Asset',
            'DSP Product', 'DSP Vendor'
        ]
        
        mapping = {
            'Start Date': ('Transaction Month', True),
            'End Date': ('Accounted Date', False),
            'Country': 'Territory',
            'UPC': 'Parent ID',
            'ISRC': 'ID',
            'Title': 'Title',
            'Net. Revenue': 'Gross',
            'Net. Royalty': 'Net',
            'Currency': 'Currency',
            'Quantity': 'Quantity',
            'Sale Type': 'Sales Type',
            'Artist': 'Artists',
            'Release Name': 'Album/Channel',
            'Store Name': 'Store',
            'Label': 'Label'
        }
        
        new_df = pd.DataFrame(columns=template_columns)
        for new_col, value in mapping.items():
            if isinstance(value, tuple):
                old_col, is_start_date = value
                if old_col in df.columns:
                    new_df[new_col] = self.format_date(df[old_col], is_start_date)
            elif value in df.columns:
                new_df[new_col] = df[value]
        
        return new_df

    def process_onerpm(self, file: Any, tax_rate: float) -> Optional[pd.DataFrame]:
        try:
            df = pd.read_excel(file, sheet_name='Sales', engine='openpyxl')
            st.session_state.total_royalty_gross = self.process_tax(df, 'Net')
            df['Net'] = df['Net'] * (1 - tax_rate / 100)
            st.session_state.total_royalty = df['Net'].sum()
            return self.transform_to_template(df)
        except Exception as e:
            st.error(f'Error processing file: {str(e)}')
            return None

    def process_onerpm_sharein(self, file: Any, tax_rate: float) -> Optional[pd.DataFrame]:
        try:
            df = pd.read_excel(file, sheet_name='Shares In & Out', engine='openpyxl')
            if 'Share Type' not in df.columns:
                raise ValueError("Column 'Share Type' not found")
                
            filtered_df = df[df['Share Type'].str.contains('In', na=False)]
            st.session_state.total_royalty_gross = self.process_tax(filtered_df, 'Net')
            filtered_df['Net'] = filtered_df['Net'] * (1 - tax_rate / 100)
            st.session_state.total_royalty = filtered_df['Net'].sum()
            return self.transform_to_template(filtered_df)
        except Exception as e:
            st.error(f'Error processing file: {str(e)}')
            return None

def main():
    st.title('Onerpm Conversor')
    
    processor = StatementProcessor()
    
    distributor = st.selectbox(
        'Select report',
        ['ONErpm', 'ONErpm Share-In']
    )
    
    service_name = 'Onerpm'
    
    tax_rate = st.number_input(
        'Tax rate (%)',
        min_value=0.0,
        max_value=100.0,
        value=18.5,
        step=0.1
    )
    
    uploaded_file = st.file_uploader('Upload statement', type=['xlsx'])
    
    if uploaded_file:
        try:
            if distributor == 'ONErpm':
                st.session_state.processed_df = processor.process_onerpm(uploaded_file, tax_rate)
            else:
                st.session_state.processed_df = processor.process_onerpm_sharein(uploaded_file, tax_rate)
                st.warning('⚠️ Considerando apenas Share-In')
            
            if st.session_state.processed_df is not None:
                st.info(f'⚠️ Processado para {distributor} com desconto de {tax_rate}%')
                
                col1, col2 = st.columns([1, 1])
                with col1:
                    st.metric("Total Gross Royalties", f"{st.session_state.total_royalty_gross:,.2f}")
                with col2:
                    st.metric("Total Royalties with discount", f"{st.session_state.total_royalty:,.2f}")
                    
                st.dataframe(st.session_state.processed_df)
                
                # Excel download with service name
                service_df = pd.DataFrame({'ServiceName': [service_name]})
                final_df = pd.concat([service_df, st.session_state.processed_df], ignore_index=True)
                
                # CSV download
                csv = final_df.to_csv(index=False).encode('utf-8')

                if distributor == 'ONErpm':
                    file_name = uploaded_file.name.rsplit('.', 1)[0] + '_rasa-template.csv'

                elif distributor == 'ONErpm Share-In':
                    file_name = uploaded_file.name.rsplit('.', 1)[0] + '_rasa-template-sharein.csv'
                
                # Criar o cabeçalho correto
                header = 'ServiceName,ONERPM,,,,,,,,,,,,,,,,,,,,,,,,,,,\n'

                # Gerar CSV do DataFrame sem cabeçalho e começando da primeira linha de dados
                df_csv = st.session_state.processed_df.to_csv(index=False)
                df_lines = df_csv.split('\n')
                data_lines = df_lines[1:]  # Pegar todas as linhas exceto o cabeçalho
                data_csv = '\n'.join(data_lines)

                # Combinar cabeçalho customizado com dados
                final_csv = header + df_csv

                st.download_button(
                    "Download processed CSV",
                    final_csv.encode('utf-8'),
                    file_name,
                    "text/csv"
                )
                
        except Exception as e:
            st.error(f"Error loading file: {e}")

if __name__ == "__main__":
    main()