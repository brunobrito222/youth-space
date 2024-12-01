import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import re
import io
from io import BytesIO
pd.options.mode.chained_assignment = None
from io import StringIO

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


st.title('Contas a Receber')
st.markdown('Utilizado para cobranças, lembretes de pagamento, ofertas de negociação etc.')
st.write("\n")
st.markdown('##### Configure a formatação do relatório nas opções abaixo:')


on_situacao = st.toggle('Filtrar alunos por Situação?')
if on_situacao:
    situacao = st.selectbox("Que alunos você gostaria de selecionar?", ("Ativos", "Não-Ativos"))
else: situacao = 'Não filtrar'

on_valores = st.toggle('Deseja remover valores pequenos?')
if on_valores:
    valor = st.number_input('Selecionar valores a partir de: ', step=1, value=50)
else: valor = 0

on_parcelas = st.toggle('Filtrar alunos pelo total de parcelas vencidas?')
if on_parcelas:
    parcelas = st.number_input('Alunos com total de parcelas a partir de: ', step=1, min_value=1)
else: parcelas = 1

on_mensalidades = st.toggle('Manter somente mensalidades?')
if on_mensalidades:
    mensalidades = 'Sim'
else: mensalidades = 'Não'

on_matricula = st.toggle('Remover taxas de matrícula? (Recomendado)', value=True)
if on_matricula:
    matricula = 'Remover'
else: matricula = 'Manter'

on_duplicados = st.toggle('Remover duplicados? (Recomendado)',
          help='Desmarcar opção somente se quiser enviar uma mensagem separada para cada parcela do aluno.', value=True)
if on_duplicados:
    duplicados = 'Remover'
else: duplicados = 'Manter'


try:
    tabela = st.session_state['df']

    # Filtra alunos por Situação
    if situacao == 'Ativos':
        tabela = tabela.loc[(tabela['SituacaoAluno'] == 'Ativo') | (tabela['SituacaoAluno'] == 'Ativo/Turma nova')].reset_index(drop=True)
    elif situacao == 'Não-Ativos':
        tabela = tabela.loc[tabela['SituacaoAluno'] != 'Ativo'].reset_index(drop=True)
        tabela = tabela.loc[tabela['SituacaoAluno'] != 'Ativo/Turma nova'].reset_index(drop=True)

    # Formata colunas de telefones e remove colunas desnecessárias
    colunas_a_formatar = ['Celular', 'Telefone', 'CelularResponsavel',	'FoneResponsavel',	'FoneComercialResponsavel']
    colunas_formatadas = []
    for coluna in colunas_a_formatar:
        tabela[coluna] = tabela[coluna].astype(str).apply(limpar_telefone)
        nome_coluna_formatado13 = f'{coluna}_D13'
        nome_coluna_formatado12 = f'{coluna}_D12'
        tabela[nome_coluna_formatado13] = tabela[coluna].apply(formatar_telefone)
        tabela[nome_coluna_formatado12] = tabela[nome_coluna_formatado13].apply(retirar_o_9)
        colunas_formatadas.append(nome_coluna_formatado12)

    colunas_a_manter = ['NumeroParcela','Sacado','Situacao', 'DataVencimento', 'Valor', 'EmailResponsavel',
                        'ValorComJuros', 'Categoria', 'SituacaoAluno']
    colunas_a_manter.extend(colunas_formatadas)
    colunas_validas = [coluna for coluna in colunas_a_manter if coluna in tabela.columns]
    tabela = tabela[colunas_validas]

    # Converter colunas para seu formato correto
    tabela['DataVencimento'] = tabela['DataVencimento'].apply(parse_date)
    tabela['DataVencimento'] = tabela['DataVencimento'].dt.strftime('%d/%m/%Y')
    colunas_valor = ['Valor', 'ValorComJuros']
    for coluna in colunas_valor:
        tabela[coluna] = tabela[coluna].apply(converter_para_float)
        tabela[coluna] = tabela[coluna].round(2)

    # Preenche os dados faltantes na coluna 'Celular_D12' com os valores das outras colunas
    tabela['Celular_D12'] = tabela['Celular_D12'].fillna(tabela['CelularResponsavel_D12'])
    tabela['Celular_D12'] = tabela['Celular_D12'].fillna(tabela['Telefone_D12'])
    tabela['Celular_D12'] = tabela['Celular_D12'].fillna(tabela['FoneResponsavel_D12'])
    tabela['Celular_D12'] = tabela['Celular_D12'].fillna(tabela['FoneComercialResponsavel_D12'])
    tabela.drop(columns={'Telefone_D12','FoneResponsavel_D12','CelularResponsavel_D12','FoneComercialResponsavel_D12'}, inplace=True)

    # Filtra valores muito pequenos
    if valor > 0:
        tabela = tabela[tabela['Valor'] >= valor]

    # Criar coluna com ValorComJuros total
    tabela['ValorComJurosTotal'] = tabela.groupby('Sacado')['ValorComJuros'].transform('sum').round(2)

    # Criar coluna com Valor total
    tabela['ValorSemJurosTotal'] = tabela.groupby('Sacado')['Valor'].transform('sum').round(2)

    # Manter somente mensalidades
    if mensalidades == 'Sim':
        categorias_para_manter = ['Yth Mensalidade Regular', 'Mensalidade Code' ]
        categorias_para_manter = ['Mensalidade Code']
        tabela = tabela[tabela['Categoria'].isin(categorias_para_manter)]

    # Remover parcelas Canceladas
    tabela = tabela[ tabela['Situacao'] != 'Cancelada' ]

    # Remover taxas de matrícula
    if matricula == 'Remover':
        categorias_para_remover = ['Matrícula Yth', 'Taxa Matrícula', 'Matrícula Code', 'Yth - Primeira Parcela']
        tabela = tabela[~tabela['Categoria'].isin(categorias_para_remover)]

    # Contar quantas parcelas tem cada 'Sacado'
    tabela['TotalDeParcelas'] = tabela.groupby('Sacado')['Valor'].transform('count')

    # Filtrar alunos com base na quantidade de parcelas
    if parcelas > 1:
        tabela = tabela[(tabela.TotalDeParcelas >= parcelas)]

    # Remover duplicados
    if duplicados == 'Remover':
        tabela = tabela.drop_duplicates(subset='Sacado', keep='first')



    st.divider()

    # Exibir informações básicas sobre o DataFrame
    st.markdown("## Análise Financeira de Alunos")

    # Cálculo do valor total quitado e pendente
    st.subheader("Totais Financeiros")
    st.write('Valor total Quitado: ', tabela[tabela['Situacao'] == 'Quitada'].Valor.sum().round(2))
    st.write('Valor total Pendente: ', tabela[tabela['Situacao'] == 'Pendente'].Valor.sum().round(2))


    # Descrição estatística das colunas Valor e ValorComJuros
    st.subheader("Descrição Estatística")
    col1, col2, col3 = st.columns(3)
    col1.write(tabela.Valor.describe())
    col2.write(tabela.ValorComJuros.describe())


    # Contagem de valores para categorias específicas
    col1, col2, col3 = st.columns(3)
    # Exibindo as informações em cada coluna
    col1.write("Situação dos Alunos")
    col1.write(tabela.SituacaoAluno.value_counts())

    col2.write("Situação das Parcelas")
    col2.write(tabela.Situacao.value_counts())

    col3.write("Categoria das Parcelas")
    col3.write(tabela.Categoria.value_counts())


    # Datas de vencimento
    st.subheader("Datas de Vencimento")
    st.write("Vencimento mais antigo: ", tabela.DataVencimento.max())
    st.write("Vencimento mais recente: ", tabela.DataVencimento.min())

    # Criando gráficos usando matplotlib e exibindo-os com st.pyplot()
    st.subheader("Distribuição dos Valores e Parcelas")

    fig, axs = plt.subplots(1, 2, figsize=(10, 4))

    # Primeiro gráfico: Histograma da coluna 'Valor'
    tabela['Valor'].plot(kind='hist', ax=axs[0], grid=False)
    axs[0].set_ylabel('Alunos')
    axs[0].set_xlabel('Valor Mensalidade')
    axs[0].set_title('Distribuição de Valores das Mensalidades')

    # Segundo gráfico: Barras horizontais da quantidade de parcelas
    value_counts_sorted = tabela['TotalDeParcelas'].value_counts().sort_index()
    value_counts_sorted.plot(kind='barh', ax=axs[1])
    axs[1].set_xlabel('Número de Alunos')
    axs[1].set_ylabel('Número de Parcelas')
    axs[1].set_title('Número de Parcelas por Aluno')

    # Ajustar espaçamento entre os gráficos
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])

    # Removendo bordas desnecessárias e simplificando o visual
    for ax in axs:
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_visible(False)
        ax.spines['left'].set_visible(False)

    # Exibir os gráficos no Streamlit
    st.pyplot(fig)


    # Verifica se a tabela existe
    if 'tabela' not in locals() or tabela is None:
        st.warning("Nenhuma tabela disponível para exportar.")
    else:
        try:
            # Cria o arquivo Excel em um objeto BytesIO
            xls_buffer = BytesIO()
            with pd.ExcelWriter(xls_buffer, engine='xlsxwriter') as writer:
                tabela.to_excel(writer, index=False, sheet_name='Dados')

            # Recupera o conteúdo do arquivo Excel como bytes
            excel_data = xls_buffer.getvalue()

            # Botão para download do Excel
            st.download_button(
                label="Download Excel",
                data=excel_data,
                file_name="Planilha.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        except Exception as e:
            st.error(f"Não foi possível gerar o arquivo Excel. Erro: {e}")


    # Verifica se a tabela existe
    if 'tabela' not in locals() or tabela is None:
        st.warning("Nenhuma tabela disponível para exportar.")
    else:
        try:
            # Cria o arquivo CSV em um objeto StringIO
            csv_buffer = StringIO()
            tabela.to_csv(csv_buffer, index=False)

            # Recupera o conteúdo do CSV como string
            csv_data = csv_buffer.getvalue()

            # Botão para download do CSV
            st.download_button(
                label="Download CSV",
                data=csv_data,
                file_name="Planilha.csv",
                mime="text/csv"
            )
        except Exception as e:
            st.error(f"Não foi possível gerar o arquivo CSV. Erro: {e}")



except Exception as e:
    st.error(f"Não foi possível ler o arquivo. Erro: {e}")
    st.markdown('\n')
    st.markdown('Faça o upload do arquivo em Home.')
    if st.button(label='Home', type='primary'):
        st.switch_page("Home.py")