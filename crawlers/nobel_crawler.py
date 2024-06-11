import re
import requests
from bs4 import BeautifulSoup
import time
import json
import re
import datetime
import traceback


def missing_notifier(book_data, attributes:dict):
    check_attributes = ['edicao', 'isbn', 'numPaginas', 'editora', 'ano', 'preco']
    missing = []
    for check_attribute in check_attributes:
        if(not book_data[check_attribute]):
            missing.append(check_attribute)
    if(len(book_data['autores']) == 0):
        missing.append('autores')
    if(len(book_data['tags']) == 0):
        missing.append('tags')
    if(len(missing) > 0):
        log.write('\n')
        log.write('=============================== Missing attributes\n')
        log.write('Missing attributes:' + ','.join(missing) + '\n')
        log.write('\n')
        log.write('======== Available attributes\n')
        for id, value in attributes.items():
            log.write(f'{id} -> {value}\n')
        log.write('\n')
    

def get_table_attributes(table: BeautifulSoup) -> dict:
    attributes = {}
    linhas = table.find_all("tr")
    for linha in linhas:
        identificador = linha.find('td')
        if(identificador):
            id = string_cleaner(identificador.text)
            value = identificador.find_next_sibling('td')
            if(value):
                value = value.text
                attributes[id] = value
    return attributes

def get_list_attributes(table: BeautifulSoup) -> dict:
    attributes = {}
    itens = table.find_all("li")
    for item in itens:
        identificador = item.select_one('span.txtDescricao')
        if(identificador):
            id = string_cleaner(identificador.text)
        dado = item.select_one('span:not(.txtDescricao)')
        if(dado):
            attributes[id] = dado.text
            continue
        id = string_cleaner(item.text.split(':')[0])
        dado = item.text.split(':')[-1]
        dado = re.sub(';$', '', dado)
        dado = re.sub('\.$', '', dado)
        attributes[id] = dado
    return attributes

def find_attribute(dados: dict, pattern: str):
    for id, value in dados.items():
        if(re.match(pattern + '(\s*:)?', id, flags=re.IGNORECASE)):
            return value
    return None

def find_table_attribute(tabela: BeautifulSoup, pattern: str) -> str:
    identificador = tabela.find(lambda tag: tag.name == "td" and re.match(pattern, tag.text, flags=re.IGNORECASE))
    if(identificador):
        return identificador.find_next_sibling('td').text
    return None

def find_list_attribute(lista, pattern: str) -> str:
    item = lista.find(lambda tag: tag.name == "li" and re.match(pattern + '\s*:', tag.text.upper()))
    if(item):
        dado = item.select('span:not(.txtDescricao)')
        if(dado):
            return dado.text
        dado = item.text.split(':')[-1]
        dado = re.sub(';$', '', dado)
        dado = re.sub('\.$', '', dado)
        return dado
    return None

def find_aditional_table_attribute(tabela: BeautifulSoup, pattern: str) -> str:
    identificador = tabela.find(lambda tag: tag.name == "th" and re.match(pattern, tag.text, flags=re.IGNORECASE))
    if(identificador):
        return identificador.find_next_sibling('td').text
    return None

#======================= Cleaners

def string_cleaner(value:str) -> str:
    if(value is not None):
        value = value.strip()
        if(value != ""):
            return value
    return None

def number_cleaner(value:str) -> int:
    value = string_cleaner(value)
    if(value is not None):
        value = re.sub("[^0-9]", "", value)
        if(len(value) > 0):
            return int(value)
    return None

def price_cleaner(value:str) -> float:
    if(value is not None):
        value = re.sub("[^0-9,]", "", value)
        value = re.sub(",", ".", value)
        if(len(value) > 0):
            return float(value)
    return None

#======================= Data formatters

def get_ISBN(dados: BeautifulSoup, find_attribute) -> str:
    isbn = string_cleaner(find_attribute(dados, "ISBN"))
    if(isbn):
        isbn = re.sub("[^0-9xX]", "", isbn)
        if(isbn != ""):
            if(len(isbn) == 13):
                return isbn
            elif(len(isbn) == 10):
                return isbn_10_to_13(isbn)
    return None

def isbn_10_to_13(isbn10: str):
    isbn_13 = '978' + isbn10
    check_digit = 0
    alternate = 0
    for digit in isbn_13[:12]:
        number = number_cleaner(digit)
        if(number is None):
            return None
        check_digit += number * (1 + (alternate * 2))
        alternate = (alternate + 1)%2
    if(check_digit%10 == 0):
        check_digit = 0
    else:
        check_digit = (10 - check_digit%10)
    return isbn_13[:12] + str(check_digit)


def get_year(dados: BeautifulSoup, find_attribute) -> str:
    ano = number_cleaner(find_attribute(dados, "ANO.*EDI[ÇC][AÃ]O")) #FIXME Alguns usam Data de publicação: 4 de outubro de 2006.
    if(not ano):
        ano = string_cleaner(find_attribute(dados, "Data.*Publica[çc][aã]o"))
        if(ano):
            search = re.search('[0-9]{4, 4}', ano)
            if search:
                ano = number_cleaner(search.group(1))
            else:
                ano = None
    return ano

def get_authors(dados: BeautifulSoup, find_attribute) -> list:
    nome_autores = string_cleaner(find_attribute(dados, "AUTOR"))
    autores = []
    if(nome_autores):
        for nome_autor in nome_autores.split(';'):
            nome_corrigido = ''
            for parte_nome in reversed(nome_autor.split(',')):
                nome_corrigido += string_cleaner(parte_nome) + ' '
            nome_corrigido = string_cleaner(nome_corrigido)
            autores.append(nome_corrigido)
    return autores


def run():

    #======================= Link Extraction
    next_link = "https://papelarianobel.com.br/produtos-categoria/livro/?orderby=menu_order"
    book_links = []

    print("=========================== Iniciado extração na Nobel =========================")

    global log
    log = open("./log/nobel-log.txt", "w")
    log.write('====================================== Link Extraction =========================================\n')

    page_count = 0
    while next_link != None and page_count < 30:
        page_count += 1
        log.write(f'===================== Processando a página {page_count}...\n')
        log.write(f'- Link: {next_link}\n')
        log.write('\n')
        page = requests.get(next_link)
        start_time = datetime.datetime.now()
        soup = BeautifulSoup(page.content, "html.parser")

        try:
            products_container = soup.find('div', class_='elementor-loop-container')
            products = products_container.find_all('div', {"data-elementor-type" : "loop-item"})
            for product in products:
                link = product.find(class_='elementor-widget-image').find('a')
                if(link):
                    book_links.append(link['href'])
        except Exception as err:
            log.write('\n')
            log.write('=================================\n')
            log.write(f'Error to find book links on page: {next_link}\n')
            log.write(str(err))
            log.write('\n')
            log.write('=================================\n')
        
        try:
            next_button = soup.find("a", class_='next')
            if next_button:
                next_link = next_button['href']
            else:
                next_link = None
        except Exception as err:
            log.write('\n')
            log.write('=================================\n')
            log.write(f'Error to find next link on page: {next_link}\n')
            log.write(str(err))
            log.write('\n')
            log.write('=================================\n')
        #next_link = None #TEST
        time_difference = datetime.datetime.now() - start_time
        if(time_difference.seconds < 5):
            sleep_time = 5 - (time_difference.microseconds/1000000)
            time.sleep(sleep_time)


    #======================= Data Extraction

    log.write(f'====================================== Total de livro a serem processados: {len(book_links)}\n')

    book_data = []
    total = 0

    log.write('====================================== Data Extraction =========================================\n')

    for link in book_links:
        try:
            total += 1
            book = {'url': link}
            book_data.append(book)
            page = requests.get(link)
            start_time = datetime.datetime.now()
            soup = BeautifulSoup(page.content, "html.parser")
            titulo = soup.find(class_='product_title')

            log.write('\n')
            log.write(f'===================== Livro {total}\n')
            log.write(f'- Link: {link}\n')
            log.write('\n')
            
            if titulo:
                titulo = titulo.text.strip()
                book['titulo'] = titulo
            else:
                book['titulo'] = None
            
            tabela = soup.find('div', {"data-widget_type": "woocommerce-product-content.default"})
            if not tabela:
                log.write('\n')
                log.write('=================================\n')
                log.write('Erro para encontrar tabela\n')
                log.write('\n')
                log.write('=================================\n')
                continue

            dados = tabela.find('table')
            get_attributes = get_table_attributes
            if not dados:
                dados = tabela.find('ul')
                if not dados:
                    log.write('\n')
                    log.write('=================================\n')
                    log.write('Erro para encontrar dados\n')
                    log.write('\n')
                    log.write('=================================\n')
                get_attributes = get_list_attributes
            dados = get_attributes(dados)
            
            # ===== Edição
            book['edicao'] = number_cleaner(find_attribute(dados, "(N[ÚU]MERO|Nº)?.*EDI[CÇ][AÃ]O"))
            
            # ===== Série #FIXME - Fazer Regex mais preciso para dividir esses dois ou desistir
            serie = find_attribute(dados, "COLE[ÇC][AÃ]O")
            book['serie'] = {"nome": serie, "numero": number_cleaner(serie)} 

            # ===== ISBN
            book['isbn'] = get_ISBN(dados, find_attribute)
            
            # ===== Páginas
            book['numPaginas'] = number_cleaner(find_attribute(dados, '.*P[ÁA]GINA'))

            # ===== Editora
            book['editora'] = string_cleaner(find_attribute(dados, "EDITORA"))

            # ===== Ano
            book['ano'] = get_year(dados, find_attribute)

            # ===== Autores
            book['autores'] = get_authors(dados, find_attribute)
            
            # ===== Tags
            tags = [] #Não vem da tabela
            tag = string_cleaner(find_attribute(dados, "CATEGORIA"))
            if(tag):
                tags.append(tag)
            posted_in = soup.find(class_='posted_in')
            if posted_in:
                categorias = posted_in.find_all('a')
                for categoria in categorias:
                    if(categoria.text != 'Livro'):
                        tag = string_cleaner(categoria.text)
                        tags.append(tag)
            book['tags'] = tags
            
            # ===== Preço
            formato = find_attribute(dados, 'ENCADERNA[CÇ][AÃ]O')
            if(not formato):
                formato = find_attribute(dados, 'CAPA')

            preco = soup.find('div', {'data-widget_type': 'woocommerce-product-price.default'})
            if(preco):
                bdi = preco.find('bdi')
                book['preco'] = price_cleaner(bdi.text)
            else:
                book['preco'] = None

            # ===== Campos faltantes
            missing_notifier(book, dados)

            # ===== BE POLITE
            log.flush()
            time_difference = datetime.datetime.now() - start_time
            if(time_difference.seconds < 5):
                sleep_time = 5 - (time_difference.microseconds/1000000)
                time.sleep(sleep_time)
        except Exception as err:
            log.write('\n')
            log.write('=================================\n')
            log.write(f'Error to process the book: {link}\n')
            log.write(traceback.format_exc())
            log.write(str(err))
            log.write('\n')
            log.write('=================================\n')

    with open('./docs/nobel-data.json', 'w') as f:
        json.dump(book_data, f, indent=2)
        f.flush()
    log.flush()
    log.close()
    print(f'=========================== Finalizada extração da Nobel =========================\n=========================== Total de livros: {len(book_data)}')