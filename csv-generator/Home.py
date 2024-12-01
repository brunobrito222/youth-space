import streamlit as st
import pandas as pd

st.set_page_config(page_title='ETL de contatos para whatsapp', page_icon=':telephone_receiver:')


st.title('Gerador de listas de disparo')
st.markdown('Faça aqui o upload do seu arquivo caso seja um **relatório gerado pelo Sponte**.\n\n'
            'Para arquivos gerados de outras fontes, entre em **Lista Avulsa** no menu lateral.')

st.sidebar.markdown('Desenvolvido por Bruno Brito.')

st.divider()
st.markdown('''
### 1º) Faça o upload do seu relatório Sponte
''')

uploaded_file = st.file_uploader(
    label='Selecione a planilha',
    help='Somente relatórios tipo Contas a Receber ou Dados do Cadastro',
    type=['xls', 'xlsx']
)

st.divider()
st.markdown('''
### 2º) Selecione o tipo de relatório:\n
''')

if uploaded_file is not None:
    dataframe = pd.read_excel(uploaded_file, skiprows=3)
    st.session_state['df'] = dataframe

if st.button(label='Contar a Receber', type='primary'):
    st.switch_page("pages/2_Contas_a_Receber.py")
if st.button(label='Dados do Cadastro', type='primary'):
    st.switch_page("pages/3_Dados_do_Cadastro.py")






