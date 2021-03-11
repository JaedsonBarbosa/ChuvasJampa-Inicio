#------------------------------------------------------------------
#-------------------- Importações e definições --------------------
#------------------------------------------------------------------
import requests
import pandas as pd
from matplotlib import pyplot as plt
import locale
locale.setlocale(locale.LC_ALL, 'pt_BR')
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
pd.set_option('display.max_colwidth', None)

#------------------------------------------------------------------
#-------------------- Gráfico -------------------------------------
#------------------------------------------------------------------
def CriarGraficoCompleto(dados, nomeEstacao):
    fig, ax = plt.subplots(nrows=1, ncols=1, figsize=(12,6))
    fig.canvas.set_window_title('Ultimas 24 horas CEMADEN')
    colunas = list(registros.columns)
    colunas.pop()
    dados[colunas].plot(rot = 0, kind = 'bar', ax = ax, legend = True)
    dados['Acumulado'].plot(secondary_y = True, legend = True, mark_right = False)
    ax.grid()
    ax.margins(0)
    ax.set_xlabel('Horário')
    ax.set_ylabel('Precipitação de cada hora (mm')
    ax.set_title('Precipitação das últimas 24 horas - ' + nomeEstacao)
    ax.right_ax.margins(0)
    ax.right_ax.set_ylabel('Precipitação acumulada (mm)')
    ax.right_ax.grid()
    plt.subplots_adjust(left = 0.06, bottom = 0.10, right = 0.94, top = 0.94)
    plt.show()

#------------------------------------------------------------------
#-------------------- Leitura -------------------------------------
#------------------------------------------------------------------
def EstacoesPB():
    estacoes = requests.get('http://sjc.salvar.cemaden.gov.br/resources/graficos/interativo/getJson2.php?uf=PB').text
    tabela = pd.read_json(estacoes)
    return tabela

def Ultimas24Horas(idEstacao):
    registros = requests.get(f'http://sjc.salvar.cemaden.gov.br/WebServiceSalvar-war/resources/horario/{idEstacao}/23').json()
    horarios = registros['horarios']
    datas = registros['datas']
    acumulados = registros['acumulados']
    registrosCorrigidos = ColunasParaLinhas(acumulados)
    tabela = pd.DataFrame(registrosCorrigidos, index = horarios, columns = datas)
    tabela['Acumulado'] = tabela.cumsum().sum(axis = 1)
    return tabela

#------------------------------------------------------------------
#-------------------- Análise -------------------------------------
#------------------------------------------------------------------
def MostrarTabelaOriginal(estacoes):
    print(estacoes)

def MostrarMunicipios(estacoes):
    municipios = estacoes[['codibge', 'cidade']]
    municipios.set_index('codibge', inplace = True)
    municipios = municipios.drop_duplicates()
    print(municipios)

def MostrarEstacoesMunicipio(estacoes, codMunicipio):
    estacoesMunicipio = estacoes.loc[estacoes['codibge'] == codMunicipio, ['idestacao', 'nomeestacao']]
    estacoesMunicipio.set_index('idestacao', inplace = True)
    print(estacoesMunicipio)

def MostrarResumoEstacao(estacoes, codEstacao):
    estacao = estacoes.loc[estacoes['idestacao'] == codEstacao]
    print(f"Cidade: {estacao['cidade'].iloc[0]}\nNome: {estacao['nomeestacao'].iloc[0]}\nUltimo valor: {estacao['ultimovalor'].iloc[0]} ({estacao['datahoraUltimovalor'].iloc[0]})\nAcumulado na última hora: {estacao['acc1hr'].iloc[0]}")
    horas = [3,6,12,24,48,72,96]
    for i in horas:
        print(f"Acumulado nas últimas {i} horas: {estacao[f'acc{i}hr'].iloc[0]}")

def PegarNomeEstacao(estacoes, codEstacao):
    estacao = estacoes.loc[estacoes['idestacao'] == codEstacao]
    return estacao['nomeestacao'].iloc[0]

def ColunasParaLinhas(dados):
    colunas = len(dados)
    linhas = len(dados[0])
    return [[dados[j][i] for j in range(colunas)] for i in range(linhas)]

def PegarResposta(padrao, mensagem, respostasPossiveis):
    resposta = padrao
    while (True):
        digitado = input(mensagem)
        if (digitado == ""):
            break
        else:
            if (str.isdigit(digitado)):
                convertido = int(digitado)
                if (convertido in respostasPossiveis):
                    resposta = convertido
                    break
                else:
                    print("Resposta fora das opções fornecidas!")
            else:
                print("Formato errado de resposta!")
    return resposta

#------------------------------------------------------------------
#-------------------- Principal -----------------------------------
#------------------------------------------------------------------
print('Observação: todos os horários estão no UTC\nPara converter para o horário de João Pessoa basta subtrair 3 horas')
estacoesPB = EstacoesPB()
while (True):
    print('\n1 - Mostrar tabela de estações completa\n' +
          '2 - Mostrar tabela de municípios e códigos\n' +
          '3 - Mostrar tabela de estações e códigos\n' +
          '4 - Mostrar resumo da estação\n' +
          '5 - Mostrar registros da últimas 24 horas\n'
          '9 - Sair (Padrão)')
    opcao = PegarResposta(9, 'Opção escolhida: ', [1,2,3,4,5,9])
    if (opcao == 1):
        MostrarTabelaOriginal(estacoesPB)
    elif (opcao == 2):
        MostrarMunicipios(estacoesPB)
    elif (opcao == 3):
        opcoes = list(estacoesPB['codibge'])
        opcoes.append(0)
        codMunicipio = PegarResposta(0, 'Código do município (0 para voltar - padrão): ', opcoes)
        if (codMunicipio != 0):
            MostrarEstacoesMunicipio(estacoesPB, codMunicipio)
    elif (opcao == 4 or opcao == 5):
        opcoes = list(estacoesPB['idestacao'])
        opcoes.append(0)
        codEstacao = PegarResposta(0, 'Código da estação (0 para voltar - padrão): ', opcoes)
        if (codEstacao != 0 and opcao == 4):
            MostrarResumoEstacao(estacoesPB, codEstacao)
        elif (codEstacao != 0 and opcao == 5):
            registros = Ultimas24Horas(codEstacao)
            print(registros)
            CriarGraficoCompleto(registros, PegarNomeEstacao(estacoesPB, codEstacao))
    else:
        break
