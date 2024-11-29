import streamlit as st
import pandas as pd
import os
from io import BytesIO
import warnings

warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")
pd.set_option('display.max_colwidth', None)

# Column mapping dictionary
MUMA_MAPPING = {
    'BO_PayeesID': 'Member Reference',
    'Payee_Name': 'Member Name',
    'Publisher': 'PUBLISHER',
    'Country_Of_Sale': 'Territory',
    'StartDate': 'Date From (MM/YYYY)',
    'EndDate': 'Date To (MM/YYYY)',
    'BO_SongCode': 'BO_SONGCODE',
    'Publishers_SongCode': 'PUBLISHERS_SONGCODE',
    'Song_Title': 'Song Title',
    'Song_Owners': 'Song Composer(s)',
    'Performer': 'Artist',
    'Customer': 'CUSTOMER',
    'ISWC': 'ISWC',
    'ISRC': 'ISRC',
    'Currency': 'CURRENCY',
    'Format': 'Instrumental or Vocal Use',
    'Total_Units': 'Units',
    'ROYATIES_GROSS_$': 'ROYATIES_GROSS_$',
    'ADMIN_FEE_$': 'ADMIN_FEE_$',
    'ROYALTIES_TO_BE_PAID_$': 'Amount',
    'Source': 'Source of Income',
    'Statement_Period_#': 'STATEMENT_PERIOD_#',
    'Statement_Period': 'STATEMENT_PERIOD',
    'Payee_Statement_#': 'PAYEE_STATEMENT_#'
}

#----------------------------------
# Concat & Totalize Files
#----------------------------------
st.title("Concat Backoffice")
st.caption("Concatena e totaliza os arquivos Backoffice para conferência e inclusão no Reprtoir.")
    
# Upload dos arquivos
uploaded_files = st.file_uploader("Faça o upload dos arquivos Excel", 
                                type=['xlsx', 'xls'], 
                                accept_multiple_files=True,
                                key="concat_files",
                               )

if uploaded_files:
    # Botões para escolher a ação
    col1, col2, col3 = st.columns(3)
    
    with col1:
        concat_button = st.button('Concatenar arquivos', type='secondary')
    with col2:
        totals_button = st.button('Calcular totais', type='primary')
    with col3:
        muma_button = st.button('Gerar planilha MuMa', type='secondary')
    
    if concat_button:
        try:
            # Lista para armazenar os DataFrames
            dataframes = []
            
            # Processamento com barra de progresso
            progress_bar = st.progress(0)
            for i, file in enumerate(uploaded_files):
                progress = (i + 1) / len(uploaded_files)
                progress_bar.progress(progress)
                
                # Lê o arquivo e adiciona ao DataFrame
                df = pd.read_excel(file)
                dataframes.append(df)
                            
            # Concatena todos os DataFrames
            concatenated_df = pd.concat(dataframes, ignore_index=True)
            
            # Informações sobre o resultado
            st.success(f"""
            Concatenação concluída com sucesso!
            - Total de arquivos: {len(dataframes)}
            - Total de linhas: {len(concatenated_df)}
            - Total de colunas: {len(concatenated_df.columns)}
            """)
            
            # Prepara o arquivo para download
            buffer = BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                concatenated_df.to_excel(writer, index=False)
            
            # Botão de download
            st.download_button(
                label="📥 Baixar arquivo concatenado",
                data=buffer.getvalue(),
                file_name="arquivos_concatenados.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
        except Exception as e:
            st.error(f"Erro ao concatenar os arquivos: {str(e)}")
    
    if totals_button:
        try:
            # Lista para armazenar os resultados
            results = []
            
            # Processamento com barra de progresso
            progress_bar = st.progress(0)
            for i, file in enumerate(uploaded_files):
                progress = (i + 1) / len(uploaded_files)
                progress_bar.progress(progress)
                
                # Leitura do arquivo Excel
                if "ST" in file.name.upper():
                    df = pd.read_excel(file)
                    
                    if "ROYALTIES_TO_BE_PAID_$" in df.columns:
                        total_royalties = df["ROYALTIES_TO_BE_PAID_$"].sum()
                        results.append((file.name, total_royalties))
                    else:
                        st.warning(f"A coluna 'ROYALTIES_TO_BE_PAID_$' não foi encontrada em {file.name}")

            if results:
                # Cria o DataFrame com os resultados
                df_results = pd.DataFrame(results, columns=["Arquivo", "Soma de ROYALTIES_TO_BE_PAID_$"])

                # Arredonda os valores para duas casas decimais
                df_results["Soma de ROYALTIES_TO_BE_PAID_$"] = df_results["Soma de ROYALTIES_TO_BE_PAID_$"].round(2)

                # Adiciona uma linha com a soma total
                total_royalties_sum = df_results["Soma de ROYALTIES_TO_BE_PAID_$"].sum().round(2)
                df_results.loc[len(df_results.index)] = ["Total", total_royalties_sum]

                # Formata como moeda brasileira
                df_results["Soma de ROYALTIES_TO_BE_PAID_$"] = df_results["Soma de ROYALTIES_TO_BE_PAID_$"].apply(
                    lambda x: f"R${x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                )

                # Exibe o DataFrame
                st.dataframe(df_results)

                st.write(f'Total: **{total_royalties_sum}**')
                
            else:
                st.warning("Nenhum arquivo válido para totalização encontrado.")

        except Exception as e:
            st.error(f"Erro ao processar os totais: {str(e)}")
            
    if muma_button:
        try:
            # Lista para armazenar os DataFrames
            dataframes = []
            
            # Processamento com barra de progresso
            progress_bar = st.progress(0)
            for i, file in enumerate(uploaded_files):
                progress = (i + 1) / len(uploaded_files)
                progress_bar.progress(progress)
                
                # Lê o arquivo e adiciona ao DataFrame
                df = pd.read_excel(file)
                dataframes.append(df)
                            
            # Concatena todos os DataFrames
            df = pd.concat(dataframes, ignore_index=True)
            
            # Converte as datas para o formato MM/YYYY
            df['StartDate'] = pd.to_datetime(df['StartDate'], dayfirst=True).dt.strftime('%m/%Y')
            df['EndDate'] = pd.to_datetime(df['EndDate'], dayfirst=True).dt.strftime('%m/%Y')
            
            # Renomeia as colunas conforme o mapping
            df_muma = df.rename(columns=MUMA_MAPPING)
            
            # Prepara o arquivo para download
            buffer = BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                df_muma.to_excel(writer, index=False)
            
            # Informações sobre o resultado
            st.success(f"""
            Planilha MuMa gerada com sucesso!
            - Total de linhas: {len(df_muma)}
            - Total de colunas: {len(df_muma.columns)}
            """)
            
            # Botão de download
            st.download_button(
                label="📥 Baixar planilha MuMa",
                data=buffer.getvalue(),
                file_name="planilha_muma.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
        except Exception as e:
            st.error(f"Erro ao gerar planilha MuMa: {str(e)}")

else:
    st.info("Aguardando upload dos arquivos...")
