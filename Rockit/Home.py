import streamlit as st
import pandas as pd

st.set_page_config(page_title='ETL de contatos para whatsapp', page_icon=':telephone_receiver:')


st.title('Gerador de listas de disparo')
st.markdown('Faça aqui o upload do seu arquivo caso seja um relatório gerado pelo Sponte.\n\n'
            'Para arquivos gerados de outras fontes, entre em **Lista Avulsa**.')

st.sidebar.markdown('Desenvolvido por Bruno Brito.')

st.divider()
st.markdown('''
### Faça o upload do seu arquivo
''')

@st.cache_data
def load_data(file):
    if file is not None:
        df = pd.read_excel(file, skiprows=3)  # ou pd.read_excel(file) dependendo do tipo de arquivo
        return df
    return None

uploaded_file = st.file_uploader(
    label='Selecione a planilha',
    help='Somente relatórios tipo Contas a Receber ou Dados do Cadastro',
    type=['xls', 'xlsx']
)
if uploaded_file is not None:
    df = load_data(uploaded_file)
    st.session_state['df'] = df

st.divider()


st.markdown('Selecione o tipo de relatório:\n')
if st.button(label='Contar a Receber', type='primary'):
    st.switch_page("pages/2_Contas_a_Receber.py")
if st.button(label='Dados do Cadastro', type='primary'):
    st.switch_page("pages/3_Dados_do_Cadastro.py")






