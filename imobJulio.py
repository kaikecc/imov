import requests
from bs4 import BeautifulSoup
import pandas as pd
import matplotlib.pyplot as plt
from sqlalchemy import create_engine

# Faz a requisição da página
url_template = 'https://www.julioimoveis.com.br/busca?estado=1&cidade=7&valor-min=&valor-max=&operacao=venda&dormitorios%5B%5D=&area-min=&area-max=&page={}'

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


# criar a conexão com o banco de dados
# substitua 'sqlite:///meu_banco_de_dados.db' pelo seu endereço de banco de dados
engine = create_engine('sqlite:///imoveis.db')

# salvar o dataframe no banco de dados
# Se você quiser anexar o DataFrame a uma tabela existente
df_julio.to_sql('julio', engine, if_exists='append')