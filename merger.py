import json
import re
import nltk
nltk.download('stopwords')
 
# import nltk for stopwords
from nltk.corpus import stopwords
stopwords = nltk.corpus.stopwords.words('portuguese')

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

def create_entry(isbn: str):
    return {"isbn": isbn, "titulo": "", "autores": "", "tags": "", "fontes": []}

def update_entry(entry: dict, book_data: dict):
    entry['titulo'] = append_search_string(entry["titulo"], get_attribute(book_data, 'titulo'))
    autores = get_attribute(book_data, 'autores')
    if autores is not None:
        for autor in autores:
            entry['autores'] = append_search_string(entry["autores"], autor)
    tags = get_attribute(book_data, 'tags')
    if tags is not None:
        for tag in tags:
            entry['tags'] = append_search_string(entry["tags"], tag)
    entry['fontes'].append(book_data)
    return entry

def run():
    global log
    log = open("./log/merger-log.txt", "w")
    log.write('====================================== Merging =========================================\n')

    merged_data = {}
    sources = {'nobel': 'Nobel','submarino': 'Submarino', 'cultura': 'Livrarias Cultura', 'curitiba': "Livrarias Curitiba"}

    for key, name in sources.items():
        print(f"=========================== Unindo dados da {name} =========================")
        f = open(f'./docs/{key}-data.json')
        books_data = json.load(f)
        f.close()
        for book in books_data:
            isbn = get_attribute(book, 'isbn')
            if isbn is None:
                continue
            book['fonte'] = name
            entry = None
            if book['isbn'] in merged_data:
                entry = merged_data[book['isbn']]
            else:
                entry = create_entry(book['isbn'])
                merged_data[book['isbn']] = entry
            entry = update_entry(entry, book)
            merged_data[book['isbn']] = entry
        print(f"=========================== Finalizado dados da {name} =========================")

    with open('./docs/merged-data.json', 'w') as f:
        json.dump(merged_data, f, indent=2)
    log.close()
    print(f'=========================== Fim da do merging =========================\nTotal de livros únicos: {len(merged_data)}')
        


