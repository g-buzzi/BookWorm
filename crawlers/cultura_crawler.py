import requests
from bs4 import BeautifulSoup
import random
import time
import json
import isbnlib

# Constants
BASE_URL = "https://www.livrariacultura.com.br/"
HEADERS = {'User-Agent': 'Mozilla/5.0'}
RESULTS_PER_PAGE = 10


# Lista de User-Agents para rotacionar
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36',
]

def get_attributes(site: BeautifulSoup):
    attributes = {}
    linhas = site.select("table.group.Especificacoes tr")
    for linha in linhas:
        identificador = linha.select_one('th.name-field')
        if(identificador):
            id = identificador.text
            value = linha.select_one('td.value-field')
            if(value):
                value = value.text
                attributes[id] = value
    return attributes
    

def missing_notifier(book_data, site: BeautifulSoup):
    check_attributes = ['edicao', 'isbn', 'numPaginas', 'editora', 'ano', 'preco']
    missing = []
    for check_attribute in check_attributes:
        if(not book_data[check_attribute]):
            missing.append(check_attribute)
    if('autores' not in book_data or (book_data['autores'] is not None and len(book_data['autores'])) == 0):
        missing.append('autores')
    if('tags' not in book_data or (book_data['tags'] is not None and len(book_data['tags'])) == 0):
        missing.append('tags')
    if(len(missing) > 0):
        attributes = get_attributes(site)
        log.write('\n')
        log.write('=============================== Missing attributes\n')
        log.write('Missing attributes:' + ','.join(missing) + '\n')
        log.write('\n')
        log.write('======== Available attributes\n')
        for id, value in attributes.items():
            log.write(f'{id} -> {value}\n')
        log.write('\n')

# Função para fazer requisição com cabeçalhos rotacionados
def fetch_url(url):
    headers = {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Referer': 'https://www.google.com/'
    }
    response = requests.get(url, headers=headers)
    return response

# Função para extrair dados do livro
def extract_book_data(book_soup, book_url):
    book_data = {
        "URL": book_url,
        "titulo": "",
        "edicao": "",
        "isbn": "",
        "numPaginas": 0,
        "editora": "",
        "ano": 0,
        "autores": [],
        "preco": 0.0
    }

    title = None
    title_h1 = book_soup.find('h1', class_="title_product")
    if title_h1:
        title = title_h1.get_text(strip=True)
    else:
        title_div = book_soup.find('div', class_="fn productName")
        if title_div:
            title = title_div.get_text(strip=True)

    if title:
        book_data["titulo"] = title
    else:
        book_data["titulo"] = "Title not found"

    # Extrair outras informações
    especificacoes = book_soup.find('div', class_="vtex-productSpecification")
    if especificacoes:
        table = especificacoes.find('table')
        if table:
            for tr in table.find_all('tr'):
                th = tr.find('th')
                td = tr.find('td')
                if th and td:
                    key = th.get_text(strip=True).lower().replace(" ", "_")
                    value = td.get_text(strip=True)
                    if key == "isbn":
                        isbn_10 = value
                        if isbnlib.is_isbn10(isbn_10):
                            book_data["isbn"] = isbnlib.to_isbn13(isbn_10)
                        else:
                            book_data["isbn"] = isbn_10
                    elif key == "ano_de_edicao" or key == "ano":
                        book_data["ano"] = int(value) if value.isdigit() else 0
                    elif key == "colaborador":
                        autores = [author.split(":")[-1].strip() for author in value.split('|') if 'Autor:' in author]
                        book_data["autores"].extend(autores)
                    elif key == "páginas":
                        book_data["numPaginas"] = int(value) if value.isdigit() else 0
                    elif key == "editora":
                        book_data["editora"] = value
                    elif key == "edição":
                        book_data["edicao"] = value

    # Extrair o preço
    preco_div = book_soup.find('strong', class_="skuBestPrice")
    if preco_div:
        preco_text = preco_div.get_text(strip=True).replace('R$', '').replace(',', '.').split()
        preco_reais = float(preco_text[0]) if preco_text else 0
        preco_centavos = float(preco_div.find('span', class_='super-cents').get_text(strip=True)) / 100 if preco_div.find('span', 'super-cents') else 0
        book_data["preco"] = preco_reais + preco_centavos

    return book_data

# Lista de categorias para buscar livros
categories = [
    "romance",
    "ficcao",
    "biografias",
    "historia",
    "infantil",
    "autoajuda",
    "ciencias",
    "fantasia",
    "misterio",
    "religiao",
    "tecnologia",
    "negocios",
    "gastronomia",
    "aventura",
    "poesia",
    "quadrinhos",
    "saude",
    "psicologia",
    "filosofia",
    "educacao",
    "esportes",
    "viagens",
    "arte",
    "fotografia"
]


def run():
    global log
    
    print("=========================== Iniciado extração na Cultura =========================")

    log = open("./log/cultura-log.txt", "w")
    # Contador de resultados
    result_counter = 0
    all_books = []

    for category in categories:
        log.write(f'====================================== Category "{category}" =========================================\n')
        SEARCH_URL = f"{BASE_URL}{category}?PS={RESULTS_PER_PAGE}"
        log.write(f'- Link: {SEARCH_URL}\n')
        log.write('\n')

        response = fetch_url(SEARCH_URL)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find all book divs on the current page
        book_divs = soup.find_all('div', class_="prateleiraProduto__foto")

        for div in book_divs:
            a_tag = div.find('a')
            if a_tag and 'href' in a_tag.attrs:
                book_url = a_tag['href']
                log.write('\n')
                log.write(f'===================== Livro {result_counter}\n')
                log.write(f'- Link: {book_url}\n')
                log.write('\n')
                # Fetch the book details page
                book_response = fetch_url(book_url)
                book_soup = BeautifulSoup(book_response.text, 'html.parser')

                # Extrair dados do livro
                book_data = extract_book_data(book_soup, book_url)
                missing_notifier(book_data, book_soup)
                all_books.append(book_data)
                result_counter += 1

    # Salvar todos os dados em um arquivo JSON
    with open('./docs/cultura-data.json', 'w', encoding='utf-8') as f:
        json.dump(all_books, f, indent=2)
        f.flush()
    log.flush()
    log.close()

    print(f'=========================== Finalizada extração da Cultura =========================\n=========================== Total de livros: {result_counter}')