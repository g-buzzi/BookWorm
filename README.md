# BookWorm

Um projeto desenvolvido para a disciplina Tópicos Especiais em Gerência de Dados que realiza a extração de dados de livros das seguintes fontes:
* [Nobel](https://www.papelarianobel.com.br/produtos-categoria/livro/)
* [Submarino](https://www.submarino.com.br/)
* [Livrarias Curitiba](https://www.livrariascuritiba.com.br/)
* [Livrarias Cultura](https://www.livrariacultura.com.br/)

# Apresentação

A [apresentação do BookWorm](https://youtu.be/LfKt5BMcBLw) está disponibilizada no youtube pelo link: [https://youtu.be/LfKt5BMcBLw](https://youtu.be/LfKt5BMcBLw)


### 📋 Pré-requisitos

Para instalar os requirimentos, basta ir à pasta do repositório e executar o comando:

```
pip install -r ./requirements.txt
```

## ⚙️ Executando os crawlers

Para executar os crawlers, execute o arquivo [main.py](main.py) e aguarde o fim do processo da extração (isto pode levar algumas horas):

```
python main.py
```

### 🔩 Visualizar gráficos

Os gráficos dos dados extraídos podem ser encontrados na pasta [graphs](graphs/) e incluem gráficos relacionados as fontes extraídas, o total de livros e preço dos livros em cada categoria extraída.

### ⌨️ Visualizar o site

Para iniciar a hospedagem local do site desenvolvido em Flask, acesse a pasta [site](site/)

```
cd ./site
```

Execute o comando:

```
flask run
```

E verifique no terminal de comando em qual porta o site foi hospedado.

## 🛠️ Construído com

* [BeautifulSoup](https://beautiful-soup-4.readthedocs.io/en/latest/) - Trabalhar com páginas HTML
* [Flask](https://flask.palletsprojects.com/en/3.0.x/) - Servidor para sites HTML
* [ISBNLib](https://pypi.org/project/isbnlib/) - Verificação e padronização de ISBN
* [NLTK](https://www.nltk.org/) - Lista de StopWords

## ✒️ Autores

* [**Gabriel Momm Buzzi**](https://github.com/g-buzzi)
* [**Breno de Brida**](https://github.com/brenobrida)
* [**Leonardo de Brida**](https://github.com/LeoBrida)