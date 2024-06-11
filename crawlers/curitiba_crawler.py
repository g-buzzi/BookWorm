#coding: utf-8
import requests
import time
import json
from bs4 import BeautifulSoup
import isbnlib
import re

def get_attributes(site: BeautifulSoup):
    attributes = {}
    linhas = site.select("table.group.CARACTERISTICAS tr")
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

def price_cleaner(value:str) -> float:
    if(value is not None):
        value = re.sub("[^0-9,]", "", value)
        value = re.sub(",", ".", value)
        if(len(value) > 0):
            return float(value)
    return None

def run():
    global log
   
    print("=========================== Iniciado extração na Curitiba =========================")

    log = open("./log/curitiba-log.txt", "w")
    log.write('====================================== Link Extraction =========================================\n')

    linksLivros = []
    page_count = 0
    step = 15
    while page_count < 30:
        log.write(f'===================== Processando a página {page_count}...\n')

        next_link = f'https://www.livrariascuritiba.com.br/api/catalog_system/pub/products/search/?_from={page_count*step}&_to={((page_count + 1)*step) - 1}'

        log.write(f'Processando página {page_count + 1}....\n')
        log.write(f'- Link: {next_link}\n')
        log.write('\n')

        requisicao = requests.get(next_link)
        livros = requisicao.json()
        for livro in livros:
            if('link' in livro):
                link = livro['link']
                linksLivros.append(link)
        page_count += 1
    links = list(set(linksLivros))

    log.write(f'====================================== Total de livro a serem processados: {len(links)}\n')

    log.write('====================================== Data Extraction =========================================\n')

    dictsList = []
    book_count = 0
    for link in links:
        log.write('\n')
        log.write(f'===================== Livro {book_count}\n')
        log.write(f'- Link: {link}\n')
        log.write('\n')
        requisicaoLivro = requests.get(link)
        siteLivro = BeautifulSoup(requisicaoLivro.text, "html.parser")

        # URL
        url = link

        # Título
        tituloBruto = siteLivro.find("div", class_="title-product")
        tagTitulo = tituloBruto.div.extract()
        titulo = tagTitulo.string.extract()

        # Edição
        edicaoBruta = siteLivro.find("td", class_="value-field Edicao")
        if edicaoBruta == None:
            edicao = None
        else:
            edicao = edicaoBruta.string.extract()
        
        # ISBN
        isbnBruto = siteLivro.find("td", class_="value-field ISBN")
        if isbnBruto == None:
            isbn = None
        else:
            valorIsbn = isbnBruto.string.extract()
            isbn = valorIsbn
            if isbnlib.is_isbn10(isbn):
                isbn = isbnlib.to_isbn13(isbn)
            else:
                isbn = isbn
    
        # Número de Páginas
        numPaginasBruto = siteLivro.find("td", class_="value-field Numero-de-Paginas")
        if numPaginasBruto == None:
            numPaginas = None
        else:
            numPaginas = numPaginasBruto.string.extract()

        # Editora
        editoraBruto = siteLivro.find("td", class_="value-field Editora")
        if editoraBruto == None:
            editora = None
        else:
            editora = editoraBruto.string.extract()

        # Ano da Edição
        anoEdicaoBruto = siteLivro.find("td", class_="value-field Ano-da-Edicao")
        if anoEdicaoBruto == None:
            anoEdicao = None
        else:
            anoEdicao = anoEdicaoBruto.string.extract()

        # Autor
        autorBruto = siteLivro.find("td", class_="value-field Autor")
        if autorBruto == None:
            autor = None
        else:
            autor = [autorBruto.string.extract()]

        # Formato
        formatoBruto = siteLivro.find("td", class_="value-field Formato")
        if formatoBruto == None:
            formato = None
        else:
            formato = formatoBruto.string.extract()

        # Tags (posso usar a categoria do livro como tag)
        tagBruto = siteLivro.find("li", class_ = "last")
        tag = ((tagBruto.a.extract()).span.extract()).string.extract()

        # Preço
        precoBruto = siteLivro.find("strong", class_="skuBestPrice")
        preco = precoBruto.string.extract()
        preco = price_cleaner(preco)
    
        # Nota
        # Nota final
        notaBruto = siteLivro.find("meta", itemprop = "ratingValue")
        if notaBruto == None:
            nota =  None
        else:
            nota = notaBruto['content']
    

        # Qtd votos
        qtdVotosBruto = siteLivro.find("strong", itemprop="ratingCount")
        if qtdVotosBruto == None:
            qtdVotos = None
        else:
            qtdVotos = qtdVotosBruto.string.extract()
        
        dados = dict(url = url, titulo = titulo, edicao = edicao, serie = None, isbn = isbn, numPaginas = numPaginas, editora = editora, ano = anoEdicao, autores = autor, tags = [tag], preco = preco, nota = {'notaFinal': nota, 'qtdVotos': qtdVotos})

        dictsList.append(dados)
        missing_notifier(dados, siteLivro)
        book_count += 1
        time.sleep(3)

    with open("./docs/curitiba-data.json", "w") as f:
        json.dump(dictsList, f, indent=2)
        f.flush()
    log.flush()
    log.close()

    print(f'=========================== Finalizada extração da Curitiba =========================\n=========================== Total de livros: {len(dictsList)}')
