import requests
from bs4 import BeautifulSoup
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from io import BytesIO
from datetime import datetime
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

arquivo = open("token.txt")
token = arquivo.read()

def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Olá, Estou processando o gráfico!')
    imoveis()

def echo(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(update.message.text)


def sendImage(image_stream):
    # Configurar o URL e os dados para enviar a imagem via Telegram
    url = "https://api.telegram.org/bot" + token + "/sendPhoto"
    files = {'photo': ('image.png', image_stream, 'image/png')}
    data = {'chat_id': "1222662328"}

    # Enviar a imagem via Telegram
    r = requests.post(url, files=files, data=data)
    return r.status_code, r.reason, r.content


def extract_imoveis_info(url_template):
        
    url = url_template.format(1)

    response = requests.get(url)

    # Cria o objeto BeautifulSoup
    soup = BeautifulSoup(response.text, 'html.parser')

    qnt_imoveis = soup.find_all('span', {'class': 'resultado-numeros'})
    paginas = qnt_imoveis[0].text.strip().split()[2]



    url = url_template.format(paginas)
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Encontra todas as informações de imóveis na página
    imoveis = soup.find_all('a', {'class': 'imovel'})

    # Cria listas vazias para armazenar as informações extraídas
    titulos = []
    localizacoes = []
    dormitorios = []
    banheiros = []
    garagens = []
    referencias = []
    valores = []

    # Extrai as informações de cada imóvel
    for imovel in imoveis:
        # Extrai o título do imóvel
        titulo = imovel.find('h3').get_text().strip()
        titulos.append(titulo)
        
        # Extrai a localização do imóvel
        localizacao = imovel.find('span', {'class': 'light'}).get_text().strip()
        localizacoes.append(localizacao)
        
        # Extrai os detalhes do imóvel
        detalhes = imovel.find('div', {'class': 'box-itens'}).find_all('div', {'class': 'objeto'})
        dormitorio = detalhes[0].find('span', {'class': 'numero'}).get_text().strip()
        dormitorios.append(dormitorio)
        banheiro = detalhes[1].find('span', {'class': 'numero'}).get_text().strip()
        banheiros.append(banheiro)
        garagem = detalhes[2].find('span', {'class': 'numero'}).get_text().strip()
        garagens.append(garagem)
        
        # Extrai a referência do imóvel
        referencia = imovel.find('div', {'class': 'objeto-referencia'}).get_text().strip()
        referencias.append(referencia)
        
        # Extrai o valor do imóvel
        valor = imovel.find('div', {'class': 'objeto-valor'}).find('strong').get_text().strip()
        valores.append(valor)

        
        
    # Cria o DataFrame com as informações extraídas
    dados = {'Título': titulos,
            'Localização': localizacoes,
            'Dormitórios': dormitorios,
            'Banheiros': banheiros,
            'Garagens': garagens,
            'Referência': referencias,
            'Valor': valores
            }
    df_julio = pd.DataFrame(dados)

    # convertendo a coluna 'Valor' para float
    
    df_julio['Valor'] = df_julio['Valor'].str.replace('R\$', '').str.replace(',', '').str.replace('[^0-9]', '', regex=True).str.replace(' ', '')
    df_julio['Valor'] = df_julio['Valor'].replace('', '0').astype(float) / 100
    
    return df_julio


def plot_imoveis(df):

    df_apartamento = df[df['Título'].str.contains('Apartamento')]

    df_grouped = df_apartamento.groupby('Localização')['Valor'].agg(['min', 'max']).sort_values('max', ascending=False)
    df_count = df_apartamento.groupby('Localização')['Valor'].agg(['mean', 'count']).sort_values('count', ascending=False)
    df_mean = df_apartamento.groupby('Localização')['Valor'].mean().sort_values(ascending=False)


    fig, ax = plt.subplots(figsize=(10, 8))
    bars1 = ax.bar(df_grouped.index, df_grouped['min'], color='red', alpha=0.5, label = 'Mín. Valor')
    bars2 = ax.bar(df_grouped.index, df_grouped['max']-df_grouped['min'], bottom=df_grouped['min'], color='blue', alpha=0.5, label = 'Máx. Valor')

    data_hora_atual = datetime.now()
    ax.set_xlabel('Bairros de Brusque-SC')
    ax.set_ylabel('Valor (R$)')
    ax.set_title('Apartamentos em Brusque-SC (Julio Imóveis) / ' + str(data_hora_atual))

    # Adiciona as informações de quantidade de apartamentos acima de cada barra
    for i, bar in enumerate(bars2):        
        height = df_grouped['max'][i]#bar.get_height() + 7*1e5
        ax.text(bar.get_x() + bar.get_width() / 2., height, str(df_count['count'][i]), ha='center', va='bottom')

    # Adiciona a linha com a média de valores
    line = ax.plot(df_grouped.index, df_mean.values, color='green', marker='o',label = 'Média Valor')
    ax.legend()

   
    box = ax.get_position()
    new_width = box.width 
    new_height = box.height * 0.75
    new_x = (1 - new_width) / 2
    new_y = (1 - new_height) * 0.75
    ax.set_position([new_x, new_y, new_width, new_height])

   
    # Mostra o gráfico
    plt.xticks(rotation=90)
    plt.legend()
    plt.grid()
    

    # Salvar a imagem gerada em memória
    image_stream = BytesIO()
    plt.savefig(image_stream, format='png')
    #plt.close()
    image_stream.seek(0)

    sendImage(image_stream)
    #plt.show()


def imoveis():
    url_template = 'https://www.julioimoveis.com.br/busca?estado=1&cidade=7&valor-min=&valor-max=&operacao=venda&dormitorios%5B%5D=&area-min=&area-max=&page={}'
    df_julio = extract_imoveis_info(url_template)
    plot_imoveis(df_julio)


def main() -> None:
    updater = Updater(token, use_context=True)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
