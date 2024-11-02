import streamlit as st
import pandas as pd
import re

st.set_page_config(page_icon=':telephone_receiver:')

# Função para limpar os números de telefone
def limpar_telefone(telefone):
    if pd.isna(telefone):
        return telefone
    return re.sub(r'\D', '', str(telefone))

# Função para formatar os números de telefone
def formatar_telefone(telefone):
    if pd.isna(telefone):
        return telefone
    # Remove os zeros à esquerda
    telefone = telefone.lstrip('0')
    # Formata para o padrão de 13 dígitos
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
    else:
        return pd.NA

# Função para retirar o dígito 9 adicional
def retirar_o_9(telefone):
    if pd.isna(telefone):
        return telefone
    if len(telefone) == 13 and telefone[4] == '9':
        return telefone[:4] + telefone[5:]
    return telefone

# Interface do Streamlit
st.title('Preparar Lista para disparo')

# Upload do arquivo
uploaded_file = st.file_uploader("Faça o upload de um arquivo Excel (.xls ou .xlsx)", type=["xls", "xlsx"])

if uploaded_file is not None:
    # Carregar o arquivo em um DataFrame
    df = pd.read_excel(uploaded_file)

    # Opção para excluir linhas superiores
    remove_rows = st.checkbox("Deseja excluir linhas superiores?")
    if remove_rows:
        num_rows_to_remove = st.number_input("Quantas linhas devem ser excluídas?", min_value=0, max_value=len(df)-1, value=2)
        df = df.iloc[num_rows_to_remove:]
        df.reset_index(drop=True, inplace=True)
        if len(df) > 0:
            df.columns = df.iloc[0]  # Define a nova primeira linha como os nomes das colunas
            df = df[1:]  # Remove a linha que agora é o cabeçalho
        else:
            st.error("Erro: Não há linhas suficientes para definir um cabeçalho válido após a exclusão.")

    # Mostrar ao usuário as primeiras linhas do arquivo para que ele possa identificar as colunas
    if len(df) > 0:
        st.write("Visualize as primeiras linhas da sua planilha:")
        st.write(df.head())

        # Deixar o usuário escolher qual coluna contém os números de telefone
        phone_column = st.selectbox("Selecione a coluna que contém os números de telefone:", df.columns)

        if st.button('Processar Contatos'):
            # Aplica a limpeza e formatação aos números de telefone
            df['whatsapp_number'] = df[phone_column].apply(limpar_telefone).apply(formatar_telefone).apply(retirar_o_9)

            # Mostrar o DataFrame atualizado
            st.write("Contatos formatados:")
            st.write(df[['whatsapp_number']].head())

            # Botão para download do arquivo CSV
            csv = df.to_csv(index=False)
            st.download_button(label="Baixar CSV com contatos formatados", data=csv, file_name='contatos_formatados.csv', mime='text/csv')
    else:
        st.error("Erro: O DataFrame está vazio após a exclusão das linhas.")
