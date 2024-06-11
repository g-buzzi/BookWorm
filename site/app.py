from flask import request, Flask, render_template
from search_engine import SearchEngine

#flask --app viewer_site run

search_engine = SearchEngine()
app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True

@app.route("/")
def search():
    query = request.args.get('query')
    by = request.args.get('by')
    print(query)
    print(by)
    results = []
    if query is not None and by is not None:
        results = search_engine.search(query, by)
        print(results)
    return render_template('index.html', results=results, query=query, by=by)

@app.route("/<isbn>")
def book_viewer(isbn):
    book_data = {}
    if isbn is not None:
        book_data = search_engine.get(isbn)
    return render_template('book.html', book_data=book_data)
