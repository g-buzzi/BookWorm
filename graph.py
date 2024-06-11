import json
import re
import nltk
import pandas as pd
import matplotlib.pyplot as plt
nltk.download('stopwords')
 
# import nltk for stopwords
from nltk.corpus import stopwords
stopwords = nltk.corpus.stopwords.words('portuguese')


#Total de livros por fonte
#Variação de preço média para cada fonte

def get_attribute(book:dict, attr:str):
    if attr in book:
        return book[attr]
    return None

def normalize_word(word:str) -> str:
    word = word.lower()
    word = re.sub(r'[^\w\s\d]','', word) 
    word = word.strip()
    return word

def string_cleaner(string:str) -> str:
    words = string.split()
    new_string = ""
    for word in words:
        normalized_word = normalize_word(word)
        if(normalized_word not in stopwords):
            new_string += normalized_word + " "
    return new_string.strip()

def append_search_string(previous: str, new_string: str) -> str:
    if new_string is None:
        return previous
    new_string = string_cleaner(new_string)
    new_words = new_string.split()    
    for word in new_words:
        if(word not in previous):
            previous += ' ' + word
    return previous.strip()

def run():
    graph_data = {'nobel': {'variacao': 0, 'variacao_n': 0},'submarino': {'variacao': 0, 'variacao_n': 0}, 'cultura': {'variacao': 0, 'variacao_n': 0}, 'curitiba': {'variacao': 0, 'variacao_n': 0}, 'todos': {'total': 0, 'categorias': {}}}

    
    sources = {'nobel': 'Nobel','submarino': 'Submarino', 'cultura': 'Livrarias Cultura', 'curitiba': "Livrarias Curitiba"}
    inv_sources =  {v: k for k, v in sources.items()}

    for source, name in sources.items():
        print(f"=========================== Obtendo dados para gráficos {name} =========================")
        f = open(f'./docs/{source}-data.json')
        books_data = json.load(f)
        f.close()
        graph_data[source]['total'] = len(books_data)
        graph_data[source]['categorias'] = {}
        graph_data['todos']['total'] += len(books_data)
        graph_data[source]['preco_medio'] = 0
        graph_data[source]['preco_medio_n'] = 0
        
        for book in books_data:
            preco = get_attribute(book, 'preco')
            if preco is not None and preco != 0:
                graph_data[source]['preco_medio'] += preco
                graph_data[source]['preco_medio_n'] += 1


            tags_list = get_attribute(book, 'tags')
            tags = ""
            if tags_list is not None:
                for tag in tags_list:
                    tags = append_search_string(tags, tag)

            for tag in tags.split():
                if tag in graph_data[source]['categorias']:
                    categoria = graph_data[source]['categorias'][tag]
                    if preco is not None and preco != 0:
                        categoria['preco'] = ((categoria['preco']*categoria['total']) + preco)/(categoria['total'] + 1)
                    categoria['total'] += 1
                else:
                    if preco is None:
                        graph_data[source]['categorias'][tag] = {'total': 0, 'preco': 0}
                    else:
                        graph_data[source]['categorias'][tag] = {'total': 1, 'preco': preco}
        graph_data[source]['preco_medio'] = graph_data[source]['preco_medio'] / graph_data[source]['preco_medio_n']
            
        print(f"=========================== Finalizado dados da {name} =========================")

    print(f"=========================== Obtendo dados para gráficos Merged =========================")
    f = open(f'./docs/merged-data.json')
    merged_data = json.load(f)
    f.close()
    graph_data['todos']['unique'] = len(merged_data)
    graph_data['todos']['preco_medio'] = 0
    graph_data['todos']['preco_medio_n'] = 0

    for book_data in merged_data.values():
        tags = get_attribute(book_data, 'tags')
        preco_medio = 0
        preco_medio_n = 0
        for book in book_data['fontes']:
            preco = get_attribute(book, 'preco')
            if preco is not None and preco != 0:
                preco_medio += preco
                preco_medio_n += 1

        if preco_medio_n != 0:
            preco_medio = preco_medio/preco_medio_n
            graph_data['todos']['preco_medio'] += preco_medio
            graph_data['todos']['preco_medio_n'] += 1

        for tag in tags.split():
            if tag in graph_data['todos']['categorias']:
                categoria = graph_data['todos']['categorias'][tag]
                if preco_medio is not None and preco_medio != 0:
                    categoria['preco'] = ((categoria['preco']*categoria['total']) + preco_medio)/(categoria['total'] + 1)
                categoria['total'] += 1
            else:
                if preco is None:
                    graph_data['todos']['categorias'][tag] = {'total': 0, 'preco': 0}
                else:
                    graph_data['todos']['categorias'][tag] = {'total': 1, 'preco': preco_medio}
       
        for fonte in book_data['fontes']:
            source = inv_sources[get_attribute(fonte, 'fonte')]
            preco = get_attribute(fonte, 'preco')
            if preco is not None and preco != 0 and preco_medio != 0:
                graph_data[source]['variacao'] += preco - preco_medio
                graph_data[source]['variacao_n'] += 1


    print(f"=========================== Finalizado dados do Merged =========================")

    print(f"=========================== Criando gráficos =========================")

    variacoes = []
    total = []
    for source, name in sources.items():
        print(source)
        if graph_data[source]['variacao_n'] != 0:
            print(graph_data[source]['variacao'])
            graph_data[source]['variacao'] = graph_data[source]['variacao'] / graph_data[source]['variacao_n']
            
        variacoes.append([name, graph_data[source]['variacao']])
        total.append([name, graph_data[source]['total']])

        try:
            df_categorias = pd.DataFrame.from_dict(graph_data[source]['categorias'], orient = 'index')
            print(df_categorias)
            g = df_categorias.sort_values(by='total', ascending=False).head(15)
            plot = g.plot(kind='bar', figsize=(15, 10), y='total')
            fig = plot.get_figure()
            fig.savefig('graphs/categories_total_' + source + '.png')
            plt.cla()

            g = df_categorias.sort_values(by='preco', ascending=False).head(15)
            plot = g.plot(kind='bar', figsize=(15, 10), y='preco')
            fig = plot.get_figure()
            fig.savefig('graphs/categories_price_high_' + source + '.png')
            plt.cla()

            
            g = df_categorias.sort_values(by='preco', ascending=True).head(15)
            plot = g.plot(kind='bar', figsize=(15, 10), y='preco')
            fig = plot.get_figure()
            fig.savefig('graphs/categories_price_low_' + source + '.png')
            plt.cla()
        except:
            pass
    
    df_categorias = pd.DataFrame.from_dict(graph_data['todos']['categorias'], orient = 'index')


    g = df_categorias.sort_values(by='total', ascending=False).head(15)
    plot = g.plot(kind='bar', figsize=(15, 10), y='total')
    fig = plot.get_figure()
    fig.savefig('graphs/categories_total_todos.png')
    plt.cla()

    g = df_categorias.sort_values(by='preco', ascending=False).head(15)
    plot = g.plot(kind='bar', figsize=(15, 10), y='preco')
    fig = plot.get_figure()
    fig.savefig('graphs/categories_price_high_todos.png')
    plt.cla()

    
    g = df_categorias.sort_values(by='preco', ascending=True).head(15)
    plot = g.plot(kind='bar', figsize=(15, 10), y='preco')
    fig = plot.get_figure()
    fig.savefig('graphs/categories_price_low_todos.png')
    plt.cla()

    df_variacoes = pd.DataFrame(variacoes, columns=['fonte', 'variacao'])
    df_variacoes = df_variacoes.set_index('fonte')
    plot = df_variacoes.plot(kind='bar', figsize=(15, 10), y='variacao')
    fig = plot.get_figure()
    fig.savefig('graphs/variacao_por_fonte.png')
    plt.cla()



    df_total = pd.DataFrame(total, columns=['fonte', 'total'])
    df_total = df_total.set_index('fonte')
    plot = df_total.plot(kind='pie', figsize=(15, 10), y='total')

    fig = plot.get_figure()
    fig.savefig('graphs/livros_por_fontes.png')
    plt.cla()

    #print(f'Total de livros {graph_data['todos']['total']}')
    #print(f'Total de livros únicos {graph_data['todos']['unique']}')

run()
        

