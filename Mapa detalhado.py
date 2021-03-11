#------------------------------------------------------------------
#-------------------- Importações e definições --------------------
#------------------------------------------------------------------
import os
import folium
import json
import vincent
import pandas as pd
from math import floor, ceil
from matplotlib import pyplot as plt
from delaunay2D import Delaunay2D
from shapely.geometry import mapping, Polygon, Point
import locale
locale.setlocale(locale.LC_ALL, 'pt_BR')

#------------------------------------------------------------------
#-------------------- Polígonos de Thiessen -----------------------
#------------------------------------------------------------------
def GetDiagramaVoronoi(pontos, centro, raio):
    dt = Delaunay2D(centro, raio)
    # Insert all seeds one by one
    for s in pontos:
        dt.addPoint(s)
    # Build Voronoi diagram as a list of coordinates and regions
    vc, vr = dt.exportVoronoiRegions()
    return [[vc[i] for i in vr[r]] for r in vr]

def MostrarPoligonos(poligonos):
    fig, ax = plt.subplots()
    ax.margins(0.1)
    ax.set_aspect('equal')
    for polygon in poligonos:
        plt.plot(*polygon.exterior.xy, color="red")
    plt.show()

def MostrarPoligono(poligono):
    fig, ax = plt.subplots()
    ax.margins(0.1)
    ax.set_aspect('equal')
    plt.plot(*poligono.exterior.xy)
    plt.show()

#------------------------------------------------------------------
#-------------------- Mapa ----------------------------------------
#------------------------------------------------------------------
def CriarMapa(latitude, longitude):
    return folium.Map(
        location=[longitude, latitude],
        zoom_start=12,
        tiles='OpenStreetMap'
    )

def AdicionarPontoMapa(dados, latitude, longitude, titulo, risco, mapa):
    group = vincent.Bar(dados, width=800, height=200)
    group.axis_titles(x='Horário', y='Chuva acumulada')
    folium.Marker(
        location=[latitude, longitude],
        tooltip = titulo,
        icon = folium.Icon(color='red', icon='exclamation-sign') if risco else folium.Icon(color='green', icon='ok-sign'),
        popup = folium.Popup(max_width = 850).add_child(
            folium.Vega(group.to_json(), width=850, height=250))
    ).add_to(mapa)

def AdicionarMalhaDeDados(malha, dados, mapa, limites):
    folium.Choropleth(
        geo_data=malha,
        name='Pluviosidade',
        data=dados,
        columns=['nomeEstacao', 'valorMedida'],
        key_on='feature.id',
        fill_color='YlGnBu',
        fill_opacity=0.75,
        line_opacity=0.25,
        legend_name='Chuvas acumuladas',
        bins = limites
    ).add_to(mapa)

def SalvarMapaEExibir(mapa):
    mapa.save('index.html')
    os.startfile('index.html', 'open')
    
#------------------------------------------------------------------
#-------------------- Análise CEMADEN -----------------------------
#------------------------------------------------------------------
def Filtrar24Horas(dados, horario):
    return dados.loc[(dados['datahora'] > horario - pd.Timedelta(hours = 24)) & (dados['datahora'] <= horario)]

def AnalisePrecipitacaoAcumulada(dadosFiltrados):
    apenasMedicoes = dadosFiltrados.drop(columns = ['latitude', 'longitude', 'datahora'])
    tabelaChuvas = apenasMedicoes.groupby(by = apenasMedicoes['nomeEstacao'])
    return tabelaChuvas.sum()

def AnalisePrecipitacaoPorHora(dadosFiltrados, horario):
    apenasMedicoes = dadosFiltrados.drop(columns = ['latitude', 'longitude'])
    apenasMedicoes['diferencaHoras'] = apenasMedicoes.apply(DiferencaHoras, axis = 1, args = [horario])
    apenasMedicoes.drop(columns = ['datahora'], inplace = True)
    tabelaPrecipitacoes = apenasMedicoes.pivot_table(index = 'diferencaHoras', columns = 'nomeEstacao', aggfunc = sum)
    return tabelaPrecipitacoes

def AnaliseLatitude(dados):
    apenasLatitude = dados.drop(columns = ['valorMedida', 'longitude', 'datahora'])
    tabelaLatitude = apenasLatitude.groupby(by = [dados['nomeEstacao']])
    return round(tabelaLatitude.mean(), 3)

def AnaliseLongitude(dados):
    apenasLongitude = dados.drop(columns = ['valorMedida', 'latitude', 'datahora'])
    tabelaLongitude = apenasLongitude.groupby(by = [dados['nomeEstacao']])
    return round(tabelaLongitude.mean(), 3)

#------------------------------------------------------------------
#-------------------- Leitura -------------------------------------
#------------------------------------------------------------------
def LerDadosCEMADEN():
    #municipio;codEstacao;uf;nomeEstacao;latitude;longitude;datahora;valorMedida
    dados = pd.read_csv('CEMADEN Junho 2019.csv', sep = ';', header = None)
    dados.columns = ['municipio', 'codEstacao', 'uf', 'nomeEstacao', 'latitude', 'longitude', 'datahora', 'valorMedida', 'Vazio']
    dados = dados.drop(columns = ['municipio', 'codEstacao', 'uf', 'Vazio'])
    dados['latitude'] = pd.to_numeric(dados['latitude'])
    dados['longitude'] = pd.to_numeric(dados['longitude'])
    dados['datahora'] = pd.to_datetime(dados['datahora'], format = '%Y-%m-%d %H:%M:%S')
    dados['valorMedida'] = pd.to_numeric(dados['valorMedida'])
    return dados

#------------------------------------------------------------------
#-------------------- Processamento -------------------------------
#------------------------------------------------------------------
def PegarResposta(padrao, mensagem, limiteInferior, limiteSuperior):
    resposta = padrao
    while (True):
        digitado = input(mensagem)
        if (digitado == ""):
            break
        else:
            if (str.isdigit(digitado)):
                convertido = int(digitado)
                if (convertido >= limiteInferior and convertido <= limiteSuperior):
                    resposta = convertido
                    break
                else:
                    print("Resposta fora dos limites permitidos!")
            else:
                print("Formato errado de resposta!")
    return resposta

def DiferencaHoras(registro, horario):
    horas = (horario - registro['datahora']) / pd.Timedelta(hours=1)
    return floor(horas)

def DiferencaHorasToTimestamp(registro, horario):
    resultado = horario - pd.Timedelta(hours = registro['diferencaHoras'])
    return resultado.strftime('%H:%M')

#------------------------------------------------------------------
#-------------------- Principal -----------------------------------
#------------------------------------------------------------------
#Geração das regiões de influência dos pluviômetros
dadosCEMADEN = LerDadosCEMADEN()
latitudes = AnaliseLatitude(dadosCEMADEN)
longitudes= AnaliseLongitude(dadosCEMADEN)
latitudesArray = [i[0] for i in latitudes.values]
longitudesArray = [i[0] for i in longitudes.values]
coordenadas = list(zip(latitudesArray, longitudesArray))
latitudeMedia = latitudes.mean()[0]
longitudeMedia = longitudes.mean()[0]

mapaJampa = json.load(open('jampa.json'))
pontosJampa = mapaJampa['geometries'][0]['coordinates'][0][0]
poligonoJampa = Polygon(pontosJampa)
poligonos = GetDiagramaVoronoi(coordenadas, [latitudeMedia, longitudeMedia], 1)
interseccoes = [Polygon(poligonos[i]).intersection(Point(coordenadas[i]).buffer(0.04)).intersection(poligonoJampa) for i in range(len(poligonos))]
MostrarPoligonos(interseccoes)

#Filtrar e organizar dados do CEMADEN
print('Para analisar o funcionamento do mapa será simulado o que o usuário veria no mapa em determinados dias e horários do mês de Junho de 2019.')
dia = PegarResposta(14, 'Dia do mês de Junho que será analisado: ', 1, 30)
hora = input('Horário que será analisado: ')
horario = pd.Timestamp('2019/6/%d %s' % (dia, hora))
precDoHorario = Filtrar24Horas(dadosCEMADEN, horario)
precAcumulada = AnalisePrecipitacaoAcumulada(precDoHorario)
precPorHora = AnalisePrecipitacaoPorHora(precDoHorario, horario)

#Escolha da escala
chuvaMinima = round(precAcumulada.min()[0], 1)
chuvaMaxima = round(precAcumulada.max()[0], 1)
limitesAtuais = [0, 2.2, 8.4, 18.6, 55.3]
if (chuvaMaxima > 55.3):
    limitesAtuais.append(ceil(chuvaMaxima))
escala = limitesAtuais
if (chuvaMinima > 18.6 and chuvaMaxima > 55.3):
    print('Quantidade de chuva muito alta, deseja usar uma escala de cores relativa a estes dados? 1 para sim e 0 para não.')
    tipoEscala = PegarResposta(0, 'Escala escolhida: ', 0, 1)
    if (tipoEscala):
        escala = list(precAcumulada['valorMedida'].quantile([0, 0.25, 0.5, 0.75, 1]))
    
#Gerar mapa colorido
mapa = CriarMapa(latitudeMedia, longitudeMedia)
AdicionarMalhaDeDados({
    'type': 'FeatureCollection',
    'features': [
        {
            "type": "Feature",
            "id": latitudes.index[i],
            "geometry": mapping(interseccoes[i])
        } for i in range(len(poligonos))]
    }, precAcumulada.reset_index(), mapa, escala)

#Gerar gráficos para mostrar as chuvas por horário
for i in precPorHora:
    bairro = i[1]
    latitude = latitudes.loc[bairro, 'latitude']
    longitude = longitudes.loc[bairro, 'longitude']
    precipitacao = precPorHora[i].to_frame(name="Precipitacao").reset_index()
    precipitacao.sort_index(ascending = False, inplace = True)
    precipitacao['horario'] = precipitacao.apply(DiferencaHorasToTimestamp, axis = 1, args = [horario])
    precipitacao.set_index('horario', inplace = True)
    precipitacao.drop(columns = ['diferencaHoras'], inplace = True)
    precipitacao['Acumulado'] = precipitacao.cumsum()
    precipitacao['Acumulado'] = precipitacao.apply(lambda row: row['Acumulado'] - row['Precipitacao'], axis = 1)
    acumulado = precAcumulada.loc[bairro][0]
    AdicionarPontoMapa(precipitacao[['Acumulado', 'Precipitacao']], longitude, latitude, '%s: %.1f mm' % (bairro, acumulado), acumulado > 18.6,  mapa)
SalvarMapaEExibir(mapa)
