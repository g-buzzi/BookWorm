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

def find_attribute(dados: dict, pattern: str):
    for id, value in dados.items():
        if(re.match(pattern + '(\s*:)?', id, flags=re.IGNORECASE)):
            return value
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
    else:
        isbn = string_cleaner(find_attribute(dados, "C(ó|o|Ó)digo (de)? barra(s)?"))
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
    ano = number_cleaner(find_attribute(dados, "ANO.*(Publica[çc][aã]o)?")) #FIXME Alguns usam Data de publicação: 4 de outubro de 2006.
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
        for nome_autor in nome_autores.split(','):
            autores.append(nome_autor)
    return autores



#======================= Link Extraction

def run():
    global log

    HEADERS = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:98.0) Gecko/20100101 Firefox/98.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "pt-BR,pt;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0",
    }

    next_link = "https://www.submarino.com.br/categoria/livros/g/tipo-de-produto-Livro?sortBy=topSelling"
    book_links = []

    print("=========================== Iniciado extração no Submarino =========================")

    log = open("./log/submarino-log.txt", "w")
    log.write('====================================== Link Extraction =========================================\n')

    page_count = 0
    books_per_page = 28

    while next_link != None and page_count < 50: 
        log.write(f'===================== Processando a página {page_count}...\n')
        log.write(f'- Link: {next_link}\n')
        log.write('\n')
        page_count += 1
        page = requests.get(next_link, headers=HEADERS)
        start_time = datetime.datetime.now()
        soup = BeautifulSoup(page.content, "html.parser")

        try:
            products = soup.select('.dpeJTS .dEPgPn .JOEpk')
            for product in products:
                link = product['href'].split('?')[0]
                book_links.append('https://www.submarino.com.br' + link)
        except Exception as err:
            log.write('\n')
            log.write('=================================\n')
            log.write(f'Error to find book links on page: {next_link}\n')
            log.write(str(err))
            log.write('\n')
            log.write('=================================\n')
        
        try:
            buttons = soup.select(".fDQwki li a")
            next_link = f'https://www.submarino.com.br/categoria/livros/g/tipo-de-produto-Livro?sortBy=topSelling&limit={books_per_page}&offset={books_per_page*page_count}'
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
            page = requests.get(link, headers=HEADERS)
            start_time = datetime.datetime.now()
            soup = BeautifulSoup(page.content, "html.parser")
            titulo = soup.find('h1', class_='src__Title-sc-1xq3hsd-0')

            log.write('\n')
            log.write(f'===================== Livro {total}\n')
            log.write(f'- Link: {link}\n')
            log.write('\n')
            
            if titulo:
                titulo = string_cleaner(re.sub('^\s*livro -\s*', '', titulo.text))
                if titulo is not None:
                    titulo = titulo.capitalize()
                book['titulo'] = titulo
            else:
                book['titulo'] = None
            
            dados = soup.select_one('.src__SpecsCell-sc-10qje1m-2.bqHqeR tbody')
            if not dados:
                log.write('\n')
                log.write('=================================\n')
                log.write('Erro para encontrar tabela\n')
                log.write('\n')
                log.write('=================================\n')
                continue
            dados = get_table_attributes(dados)
            
            # ===== Edição
            book['edicao'] = number_cleaner(find_attribute(dados, "(N[ÚU]MERO|Nº)?.*EDI[CÇ][AÃ]O"))
            
            # ===== Série #FIXME - Fazer Regex mais preciso para dividir esses dois ou desistir
            serie = find_attribute(dados, "COLE[ÇC][AÃ]O")
            if serie:
                patterns = re.match('(.*) (\(.*\))', serie) # espera estilo 'Nome da coleção (Vol. X)'
                if(patterns):
                    book['serie'] = {"nome": patterns[0], "numero": number_cleaner(patterns[1])} 
                else:
                    book['serie'] = {"nome": serie, "numero": None} 
            else:
                book['serie'] = None

            # ===== ISBN
            book['isbn'] = get_ISBN(dados, find_attribute)
            
            # ===== Páginas
            book['numPaginas'] = number_cleaner(find_attribute(dados, '.*P[ÁA]GINA'))

            # ===== Editora
            book['editora'] = string_cleaner(find_attribute(dados, "EDITORA"))
            if book['editora'] is None:
                book['editora'] = string_cleaner(find_attribute(dados, "MARCA"))
            if book['editora'] is None:
                book['editora'] = string_cleaner(find_attribute(dados, "FABRICANTE"))

            # ===== Ano
            book['ano'] = get_year(dados, find_attribute)

            # ===== Autores
            book['autores'] = get_authors(dados, find_attribute)
            
            # ===== Tags
            tags = [] #Não vem da tabela
            thema = string_cleaner(find_attribute(dados, "Thema"))
            if thema:
                for tag in thema.split(','):
                    if tag.find(':'):
                        tags.append(tag.split(':')[0])
                    else:
                        tags.append(tag)
            book['tags'] = tags
            
            # ===== Preço

            preco = soup.find(class_='priceSales')
            if(preco):
                formato = string_cleaner(find_attribute(dados, "CAPA"))      
                if formato is None:
                    formato = string_cleaner(find_attribute(dados, "COBERTURA"))
                else:
                    formato = "Capa " + formato

                book['preco'] = price_cleaner(preco.text)
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

    with open('./docs/submarino-data.json', 'w') as f:
        json.dump(book_data, f, indent=2)
        f.flush()
    log.flush()
    log.close()
    print(f'=========================== Finalizada extração do Submarino =========================\n=========================== Total de livros: {len(book_data)}')