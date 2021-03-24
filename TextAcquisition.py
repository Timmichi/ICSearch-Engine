import json
import re
from bs4 import BeautifulSoup
import os
import sys
import math
from nltk.stem import PorterStemmer

# Index = Token : [(DocID, ((SearchWord*Priority)+(SearchWord*BasicWords)), [Positions in the text])]
# DocID = DocID : URL
# IndexMarkers = InitialLetter : (StartPosition,EndPosition)
# DocIDMarkers = lineNumber : (StartPosition,EndPosition)


def tokenize(token):
    tokens = []
    try:
        ps = PorterStemmer()
        tokens += [ps.stem(token.lower())
                   for token in re.findall('[a-zA-Z0-9]+', token)]
        return tokens
    except:
        print("ERROR: Tokenize Function Error")
        return tokens


def computeWordData(tokens):
    if not isinstance(tokens, list):
        return {}
    freq = {}
    positions = {}
    for i, t in enumerate(tokens):
        if t in freq.keys():
            freq[t] += 1
            positions[t].append(i)
        else:
            freq[t] = 1
            positions[t] = [i]
    return freq, positions


def updateIndex(index, tokenFrequency, totalPositions, importantFrequency, totalWordsInDoc, docID):
    for k, v in tokenFrequency.items():
        # calculate tf score
        tf = v
        if tf > 0 and k in importantFrequency:
            tf = 2 + math.log10(tf) + math.log(importantFrequency[k])
        elif tf > 0 and k not in importantFrequency:
            tf = 1 + math.log10(tf)
        # add tf score and DocID to posting
        if k in index.keys():
            index[k].append((docID, tf))
        else:
            index[k] = [(docID, tf)]
    return index


def writeIndex(index):
    for k, v in index.items():
        directory = ".\letters"
        fileName = k + ".txt"
        filePath = os.path.join(directory, fileName)

        if not os.path.exists(filePath):
            f = open(filePath, "w", encoding='utf-8')
            for key, value in sorted(v.items(), key=lambda posting: len(posting[1]), reverse=True):
                f.write(f"{key} {str(value)}\n")
            f.close()
            continue

        storedData = {}
        f = open(filePath, "r", encoding='utf-8')
        for txt in f:
            val = re.search("^([a-zA-Z0-9]+) (.+)", txt)
            token = val.group(1)
            posting = eval(val.group(2))
            storedData[token] = posting
        f.close()
        f = open(filePath, "w", encoding='utf-8')

        for token, posting in v.items():
            if token in storedData:
                storedData[token] = storedData[token] + posting
            else:
                storedData[token] = posting

        sortedTuple = sorted(storedData.items(),
                             key=lambda posting: len(posting[1]), reverse=True)
        for k, v in sortedTuple:
            f.write(f"{k} {str(v)}\n")
        f.close()


def writeDocID(docID, IDline):
    for k, v in docID.items():
        directory = "." + "\\" + "numbers"
        fileName = str(IDline) + ".txt"
        filePath = os.path.join(directory, fileName)
        f = open(filePath, "a", encoding='utf-8')
        f.write(f"{k} {v}\n")
        f.close()


def mwMarkers(marker, directory, mergeFile):
    endPos = 0
    for root, dirs, files in os.walk(directory, topdown=False):
        for file in files:
            filePath = os.path.join(directory, file)
            k = file[0:-4]
            with open(filePath, "r", encoding='utf-8', errors='ignore') as f, open(mergeFile, "a", encoding='utf-8') as f2:
                for line in f:
                    f2.write(line)
                f2.close()
                startPos = endPos
                f.seek(0, 2)
                endPos = f.tell() + startPos
                f.close()
                v = (startPos, endPos)
                marker[k] = v


def convertIndexToAlphaIndex(index):
    alphaIndex = {}
    for k, v in index.items():
        key = k[0]
        if key in alphaIndex.keys():
            alphaIndex[key][k] = v
        else:
            alphaIndex[key] = {}
            alphaIndex[key][k] = v
    return alphaIndex


def getTitleParagraph(soup):
    title = soup.find('title')
    if title:
        title = soup.find('title').getText()
    paragraph = soup.findAll('p')
    if paragraph:
        preParagraph = soup.findAll('p')
        paragraph = ''
        for p in preParagraph:
            for x in p.findAll(text=True):
                paragraph += x
    else:
        paragraph = soup.getText()
    paragraph = re.findall("[A-Z].*?[\.!?,]", paragraph,
                           re.MULTILINE | re.DOTALL)
    if title == None and paragraph:
        title = ''
        if len(paragraph) < 2:
            loop = len(paragraph)
        else:
            loop = 2
        for i in range(0, loop):
            title += paragraph[i]
    if title and len(title) > 65:
        l = title.split(" ")
        title = ''
        if len(l) < 5:
            loop = len(l)
        else:
            loop = 5
        for i in range(0, loop):
            title += ' ' + l[i]
        title += '...'
    if paragraph:
        tempParagraph = ''
        if len(paragraph) < 5:
            loop = len(paragraph)
        else:
            loop = 5
        for i in range(0, loop):
            tempParagraph += paragraph[i]
        paragraph = tempParagraph[0:250] + "..."
    return title, paragraph


def getCondensedUrl(preUrl):
    preUrl = preUrl.split("//")
    preUrl = preUrl[1]
    preUrl = preUrl.split("/")
    url = f'{preUrl[0]}'
    preUrl.pop(0)
    iters = 0
    while len(url) < 25 and iters < len(preUrl):
        segment = preUrl[iters]
        if len(segment) > 10:
            url += " > " + segment[0:10] + "..."
        else:
            url += " > " + segment
        iters += 1
    return url


filePaths = list()
index = dict()
docID = dict()

for root, dirs, files in os.walk(".\DEV", topdown=False):
    for name in files:
        filePaths.append(os.path.join(root, name))

fileNumber = 1
initIDLine = 1
currIDLine = initIDLine
total = len(filePaths)

count = 0
for filePath in filePaths:
    try:
        with open(filePath) as f:
            data = json.load(f)
        soup = BeautifulSoup(data["content"], "html.parser")
        # computes frequency of tokens that are "important"
        importantList = ["strong", "h1", "h2", "h3", "title", "b"]
        importantText = [words.text.strip()
                         for words in soup.findAll(importantList)]
        importantText = ' '.join([elem for elem in importantText])
        importantToken = tokenize(importantText)
        importantFrequency = computeWordData(importantToken)[0]
        url = data["url"]
        con = getCondensedUrl(url)
        title, paragraph = getTitleParagraph(soup)
        docID[fileNumber] = [url, con, title, paragraph]
        text = soup.getText()
        fileToken = tokenize(text)
        totalWordsInDoc = len(fileToken)
        tokenFrequency, totalPositions = computeWordData(fileToken)
        updateIndex(index, tokenFrequency, totalPositions,
                    importantFrequency, totalWordsInDoc, fileNumber)
        print(int(float(fileNumber)*100/float(total)), "%")
        fileNumber += 1
        count += 1
        currIDLine += 1

        # At 1000 iterations, store index/docID, clear index/docID and reset count
        if count == 1000:
            # key is sorted by alphanumeric characters, values are the postings for tokens that start with those characters
            aIndex = convertIndexToAlphaIndex(index)
            writeIndex(aIndex)
            writeDocID(docID, initIDLine)
            count = 0
            initIDLine = currIDLine
            docID.clear()
            index.clear()
            aIndex.clear()
    except:
        print("Error: Error opening JSON file and using BeautifulSoup")
        break

# writes remaining index (iteration that didn't make it to 1000)
if index:
    aIndex = convertIndexToAlphaIndex(index)
    writeIndex(aIndex)
    writeDocID(docID, initIDLine)
    docID.clear()
    index.clear()
    aIndex.clear()

print(len(filePaths))
print(len(index))
print(sys.getsizeof(index))

# creates indexMarker.txt and merges index files in index.txt
indexMarker = dict()
indexDirectory = ".\letters"
mergedIndexFile = "index.txt"
mwMarkers(indexMarker, indexDirectory, mergedIndexFile)

# creates docIDMarker.txt and merges docID files in docID.txt
docIDMarker = dict()
docIDDirectory = "." + "\\" + "numbers"
mergedDocIDFile = "docID.txt"
mwMarkers(docIDMarker, docIDDirectory, mergedDocIDFile)

# writes markers to files
f = open("indexMarkers.txt", "w", encoding='utf-8')
f2 = open("docIDMarkers.txt", "w", encoding='utf-8')
f.write(str(indexMarker))
f2.write(str(docIDMarker))
