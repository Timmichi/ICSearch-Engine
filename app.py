from flask import Flask, render_template, url_for, request
import SearchEngine

app = Flask(__name__)
indexMarkers, docIDMarkers, stopWords, stemmer = SearchEngine.preliminary()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/result', methods=['POST', 'GET'])
def result():
    page = request.args.get('page', 1, type=int)
    if page > 0:
        page -= 1
    if request.method == 'POST':
        result = request.form
        query = result['query']
        if 'resultAmount' not in result.keys():
            resultAmount = 15
        else:
            resultAmount = int(result['resultAmount'])
    else:
        query = request.args.get('query', '', type=str)
        resultAmount = request.args.get('resultAmount', 0, type=int)
    # search engine!
    search = SearchEngine.searchEngine(
        query, 200, indexMarkers, docIDMarkers, stopWords, stemmer)
    if search == []:
        return render_template("result.html", valid=False)
    else:
        time = round(search[0], 2)
        infoList = search[1]
        totalResultAmount = search[2]
        if totalResultAmount < resultAmount:
            resultAmount = totalResultAmount
        # pagination (we are starting from page 1)
        offset = page * resultAmount
        infoList = infoList[offset:offset+resultAmount]
        page += 1
    return render_template("result.html", valid=True, page=page, query=query, resultAmount=resultAmount, totalResultAmount=totalResultAmount, infoList=infoList, time=time)


if __name__ == "__main__":
    app.run(debug=True)
