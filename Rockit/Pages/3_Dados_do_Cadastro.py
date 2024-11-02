import streamlit as st
import pandas as pd
from io import StringIO
import matplotlib.pyplot as plt
import re
import io
from io import BytesIO
pd.options.mode.chained_assignment = None

st.set_page_config(page_icon=':telephone_receiver:')

def limpar_telefone(telefone):
    if pd.isna(telefone):
        return telefone
    return re.sub(r'\D', '', str(telefone))

def formatar_telefone(telefone):
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

def retirar_o_9(telefone):
    if pd.isna(telefone):
        return telefone
    if len(telefone) == 13 and telefone[4] == '9':
        return telefone[:4] + telefone[5:]
    return telefone

def parse_date(date):
    if pd.isna(date):
        return pd.NaT
    for fmt in ('%d/%m/%Y %H:%M:%S', '%Y-%m-%d %H:%M:%S', '%Y/%m/%d %H:%M:%S'):
        try:
            return pd.to_datetime(date, format=fmt)
        except ValueError:
            continue
    return pd.NaT  # Se nenhum formato corresponder

def converter_para_float(valor):
    if pd.isna(valor):
        return valor
    return float(str(valor).replace(',', '.'))


st.title('Dados do Cadastro')
st.markdown('Utilizado para avisos pedagógicos, ofertas comeciais, lembrete aos alunos etc.')
st.write("\n")
st.markdown('##### Configure a formatação do relatório nas opções abaixo:')


on_situacao = st.toggle('Filtrar alunos por Situação?')
if on_situacao:
    situacao = st.selectbox("Que alunos você gostaria de selecionar?", ("Ativos", "Não-Ativos"))
else: situacao = 'Não filtrar'

on_adimplencia = st.toggle('Filtrar alunos por Adimplência?', help='Inadimplência considera atraso a partir de 60 dias.')
if on_adimplencia:
    adimplencia = st.selectbox("Que alunos você gostaria de selecionar?", ("Adimplentes", "Inadimplentes"))
else: adimplencia = 'Não filtrar'

on_duplicados = st.toggle('Remover duplicados? (Recomendado)',
          help='Desmarcar opção somente se quiser enviar uma mensagem separada para cada parcela do aluno.', value=True)
if on_duplicados:
    duplicados = 'Remover'
else: duplicados = 'Manter'

try:
    tabela = st.session_state['df']

    # Filtrar alunos por situação
    if situacao == 'Ativos':
        tabela = tabela.loc[(tabela['Situacao'] == 'Ativo') | (tabela['Situacao'] == 'Ativo/Turma nova')].reset_index(drop=True)
    elif situacao == 'Não-Ativos':
        tabela = tabela.loc[tabela['Situacao'] != 'Ativo'].reset_index(drop=True)
        tabela = tabela.loc[tabela['Situacao'] != 'Ativo/Turma nova'].reset_index(drop=True)

    # Filtrar alunos por Adimplência
    if adimplencia == 'Adimplentes':
        tabela = tabela.loc[(tabela['Inadimplente'] == 'Ativo') | (tabela['SituacaoAluno'] == 'Ativo')].reset_index(drop=True)
    elif adimplencia == 'Não-Ativos':
        tabela = tabela.loc[tabela['Inadimplente'] != 'Ativo'].reset_index(drop=True)
        tabela = tabela.loc[tabela['Inadimplente'] != 'Ativo/Turma nova'].reset_index(drop=True)

    # Formata colunas de telefones e remove colunas desnecessárias
    colunas_a_formatar = ['FoneResidencial', 'FoneCelular']
    colunas_formatadas = []
    for coluna in colunas_a_formatar:
        tabela[coluna] = tabela[coluna].astype(str).apply(limpar_telefone)
        nome_coluna_formatado13 = f'{coluna}_D13'
        nome_coluna_formatado12 = f'{coluna}_D12'
        tabela[nome_coluna_formatado13] = tabela[coluna].apply(formatar_telefone)
        tabela[nome_coluna_formatado12] = tabela[nome_coluna_formatado13].apply(retirar_o_9)
        colunas_formatadas.append(nome_coluna_formatado12)

    colunas_a_manter = ['Nome','FoneCelular','FoneComercial','FoneResidencial','Email',
                        'Sexo','DataNascimento','Situacao', 'Inadimplente']
    colunas_a_manter.extend(colunas_formatadas)
    colunas_validas = [coluna for coluna in colunas_a_manter if coluna in tabela.columns]
    tabela = tabela[colunas_validas]

    # Preenche os dados faltantes na coluna 'FoneCelular_D12' com os valores das outras colunas
    tabela['FoneCelular_D12'] = tabela['FoneCelular_D12'].fillna(tabela['FoneResidencial_D12'])
    tabela['FoneResidencial_D12'] = tabela['FoneResidencial_D12'].fillna(tabela['FoneCelular_D12'])
    tabela.drop(columns={'FoneCelular','FoneResidencial'}, inplace=True)

    # Converte data para formato correto
    tabela['DataNascimento'] = tabela['DataNascimento'].apply(parse_date)
    tabela['DataNascimento'] = tabela['DataNascimento'].dt.strftime('%d/%m/%Y')

    # Remover duplicados
    if duplicados == 'Remover':
        tabela = tabela.drop_duplicates(subset='Nome', keep='first')

    # Organiza por ordem alfabética
    tabela.sort_values(by='Nome', inplace=True )

except:
    st.markdown('\n')
    st.markdown('Faça o upload do arquivo em Home.')
    if st.button(label='Home', type='primary'):
        st.switch_page("Home.py")



