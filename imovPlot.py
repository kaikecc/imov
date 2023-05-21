from sqlalchemy import create_engine
import pandas as pd
import matplotlib.pyplot as plt
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

token = '6274563938:AAE_sZNggKL5le7Zlw3s-U-edOkNzNa-mnA'
updater = Updater(token=token, use_context=True)

def send_graph(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id

    # Cria a conexão com o banco de dados
    engine = create_engine('sqlite:///imoveis.db')

    # Carrega os dados da tabela 'julio' no DataFrame
    df_julio = pd.read_sql_table('julio', con=engine)

    # Filtra os dados que contêm 'Apartamento' no campo 'Título'
    df_apartamento = df_julio[df_julio['Título'].str.contains('Apartamento')]

    # Agrupa os imóveis por localização e calcula a média e quantidade de apartamentos de cada grupo
    df_grouped = df_apartamento.groupby('Localização')['Valor'].agg(['mean', 'count']).sort_values('count', ascending=False)

    # Cria o gráfico de barras
    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.bar(df_grouped.index, df_grouped['mean'], color='blue', alpha=0.5)

    # Define os rótulos dos eixos x e y
    ax.set_xlabel('Bairros de Brusque-SC')
    ax.set_ylabel('Valor médio (R$)')
    ax.set_title('Relação entre Localização, Valor e Quantidade de Apartamentos')

    # Adiciona as informações de quantidade de apartamentos acima de cada barra
    for i, bar in enumerate(bars):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2., height, str(df_grouped['count'][i]), ha='center', va='bottom')

    # Mostra o gráfico
    plt.xticks(rotation=90)
    plt.grid()

    # Salva a figura
    figname = 'grafico.png'
    plt.savefig(figname, dpi=300, bbox_inches='tight')
    plt.close()

    # Envia a imagem pelo Telegram
    context.bot.send_photo(chat_id=chat_id, photo=open(figname, 'rb'))

send_command_handler = CommandHandler('send', send_graph)
updater.dispatcher.add_handler(send_command_handler)

updater.start_polling()
updater.idle()
