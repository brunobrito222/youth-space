import streamlit as st
import pandas as pd
import re
from io import StringIO

# Configuração da página
st.set_page_config(page_icon=':telephone_receiver:', layout="centered", page_title="Preparar Lista para Disparo")

# Função para limpar os números de telefone
def limpar_telefone(telefone):
    if pd.isna(telefone):
        return telefone
    return re.sub(r'\D', '', str(telefone))

# Função para formatar os números de telefone
def formatar_telefone(telefone):
    if pd.isna(telefone):
        return telefone
    telefone = telefone.lstrip('0')  # Remove os zeros à esquerda
    if len(telefone) == 12:
        return telefone[:4] + '9' + telefone[4:]
    elif len(telefone) == 11:
        return '55' + telefone
    elif len(telefone) == 10:
        return '55' + telefone[:2] + '9' + telefone[2:]
    elif len(telefone) == 9:
        return '5585' + telefone
    elif len(telefone) == 8:
        return '55859' + telefone
    return pd.NA

# Função para retirar o dígito 9 adicional
def retirar_o_9(telefone):
    if pd.isna(telefone):
        return telefone
    if len(telefone) == 13 and telefone[4] == '9':
        return telefone[:4] + telefone[5:]
    return telefone

# Interface do Streamlit
st.title('Preparar Lista para Disparo')

# Upload do arquivo
uploaded_file = st.file_uploader("Faça o upload de um arquivo Excel (.xls ou .xlsx)", type=["xls", "xlsx"])

if uploaded_file is not None:
    try:
        # Carregar o arquivo em um DataFrame
        df = pd.read_excel(uploaded_file)

        # Verifica se o DataFrame está vazio
        if df.empty:
            st.error("O arquivo carregado está vazio. Por favor, carregue um arquivo válido.")
        else:
            # Opção para excluir linhas superiores
            remove_rows = st.checkbox("Deseja excluir linhas superiores?")
            if remove_rows:
                num_rows_to_remove = st.number_input(
                    "Quantas linhas devem ser excluídas?", 
                    min_value=0, 
                    max_value=len(df)-1, 
                    value=2
                )
                df = df.iloc[num_rows_to_remove:].reset_index(drop=True)

                # Redefine os cabeçalhos, se necessário
                if len(df) > 0:
                    df.columns = df.iloc[0]  # Define a nova primeira linha como nomes das colunas
                    df = df[1:]  # Remove a linha que virou cabeçalho
                else:
                    st.error("Erro: Não há linhas suficientes para redefinir o cabeçalho.")
            
            if len(df) > 0:
                # Mostrar ao usuário as primeiras linhas para identificação
                st.write("Visualize as primeiras linhas da sua planilha:")
                st.write(df.head())

                # Seleção da coluna de números de telefone
                phone_column = st.selectbox("Selecione a coluna que contém os números de telefone:", df.columns)

                if st.button('Processar Contatos'):
                    # Aplica as transformações nos números de telefone
                    df['whatsapp_number'] = (
                        df[phone_column]
                        .apply(limpar_telefone)
                        .apply(formatar_telefone)
                        .apply(retirar_o_9)
                    )

                    # Mostra o DataFrame atualizado
                    st.write("Números formatados:")
                    st.write(df[['whatsapp_number']].head())

                    # Botão para download do CSV
                    csv_buffer = StringIO()
                    df.to_csv(csv_buffer, index=False)
                    csv_data = csv_buffer.getvalue()

                    st.download_button(
                        label="Baixar CSV com números formatados",
                        data=csv_data,
                        file_name='contatos_formatados.csv',
                        mime='text/csv'
                    )
            else:
                st.error("Erro: O DataFrame está vazio após a exclusão das linhas.")
    except Exception as e:
        st.error(f"Ocorreu um erro ao processar o arquivo: {e}")
