import json
import re
import nltk
import math
from nltk.corpus import stopwords


nltk.download('stopwords')


class SearchEngine:
    def __init__(self):
        with open('../docs/merged-data.json', 'r') as f:
            merge_data = json.load(f)
        self.data = merge_data
        self.create_indexes()
        self.stopwords = nltk.corpus.stopwords.words('portuguese')


    def create_indexes(self):
        self.indexes = {'autores': {}, 'titulo': {}, 'tags': {}, 'todos': {}}
        partial_indexes = ['autores', 'titulo', 'tags']
        for book in self.data.values():
            isbn = book['isbn']
            for index in partial_indexes:
                if index not in book or book[index] is None:
                    continue
                for word in book[index].split():
                    if word in self.indexes[index]:
                        self.indexes[index][word].add(isbn)
                    else:
                        self.indexes[index][word] = set([isbn])
                    if word in self.indexes['todos']:
                        self.indexes['todos'][word].add(isbn)
                    else:
                        self.indexes['todos'][word] = set([isbn])
                    
    def search(self, query: str, index: str='autor'):
        query = self.string_cleaner(query)
        query_words = query.split()
        results = {}
        for word in query_words:
            if word in self.indexes[index]:
                for isbn in self.indexes[index][word]:
                    if isbn in results:
                        results[isbn] += 1
                    else:
                        results[isbn] = 1
        sorted_results = sorted(results.items(), key=lambda x:x[1], reverse=True)
        sorted_results = [x[0] for x in sorted_results]
        final_results = []
        for isbn in sorted_results:
            final_results.append(self.get_result(isbn))
        return final_results
    
    def get_result(self, isbn):
        book = self.data[isbn]
        result = {'isbn': isbn}
        for fonte in book['fontes']:
            if 'titulo' not in result and 'titulo' in fonte and fonte['titulo'] is not None:
                result['titulo'] = fonte['titulo']
            if 'autores' not in result and 'autores' in fonte and fonte['autores'] is not None and len(fonte['autores']) > 0:
                result['autores'] = fonte['autores']
            if 'preco' in fonte and fonte['preco'] is not None and ('preco' not in result or fonte['preco'] < result['preco']):
                result['preco'] = fonte['preco']
        if 'titulo' not in result:
            result['titulo'] = "Título não encontrado"
        if 'autores' not in result:
            result['autores'] = ["Autores não encontrados"]
        if 'preco' not in result:
            result['preco'] = 0
        return result
            
                

    
    def get(self, isbn: str):
        if isbn in self.data:
            result = self.get_result(isbn)
            book = self.data[isbn]
            result['fontes'] = book['fontes']
            result['tags'] = book['tags']
            return result
        return None


    def normalize_word(self, word:str) -> str:
        word = word.lower()
        word = re.sub(r'[^\w\s\d]','', word) 
        word = word.strip()
        return word

    def string_cleaner(self, string:str) -> str:
        words = string.split()
        new_string = ""
        for word in words:
            normalized_word = self.normalize_word(word)
            if(normalized_word not in self.stopwords):
                new_string += normalized_word + " "
        return new_string.strip()
