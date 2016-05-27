from flask import Flask, render_template, redirect, url_for
from flask_bootstrap import Bootstrap

from logic.metadata import INDICES_DIR
from search_app.forms import SearchForm
from searcher import Searcher

app = Flask(__name__)
Bootstrap(app=app)
searcher = Searcher(INDICES_DIR)


@app.route('/', methods=['GET', 'POST'])
def index():
    form = SearchForm()

    if form.validate():
        return redirect(url_for('search_results'), query=form.query.data)
    return render_template('index.html', form=form)


@app.route('/search_results/<query>')
def search_results(query):
    id_pos = searcher.find_document(query.split())
    urls = [searcher.get_url(doc_id) for doc_id, pos in id_pos]
    return render_template('results.html', query=query, urls=urls)

if __name__ == '__main__':
    app.run(debug=True, port=8000)

