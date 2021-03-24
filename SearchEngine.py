import json
import timeit
import re
import math
from nltk import PorterStemmer
from utils.download import download

# Index = Token : [(DocID, ((SearchWord*Priority)+(SearchWord*BasicWords)), [Positions in the text])]
# DocID = DocID : URL
# IndexMarkers = InitialLetter : (StartPosition,EndPosition)
# DocIDMarkers = lineNumber : (StartPosition,EndPosition)

# Load our marker indexes


def loadMarkers():
    indexMarkers = {}
    docIDMarkers = {}
    with open("indexMarkers.txt", 'r', encoding="utf-8") as f:
        indexMarkers = eval(f.read())
    with open("docIDMarkers.txt", 'r', encoding="utf-8") as f:
        docIDMarkers = eval(f.read())
    return (indexMarkers, docIDMarkers)

# Returns only intersecting posts. This function goes from the back to front instead of front to back
# Input -> [(token, [posting info]), ...] Output -> [(token, [posting info]), ...]


def intersectingPostings(postings):
    # If only one posting, return
    if len(postings) == 1:
        return postings

    # Declare Variables
    cursor = 0
    currentDoc = -1
    currentInfo = []
    resultInfo = []

    # Sort Postings to shortest first
    temp = []
    postings = sorted(postings, key=lambda posting: len(posting[1]))
    for p in postings:
        resultInfo.append((p[0], []))
        temp.append(p[1])
    postings = temp

    # While the first posting still has values
    while postings:

        if cursor == 0:
            currentInfo = []
            # If we are looking at the first posting, set the docID and append the post tuple to the currentInfo
            if len(postings[cursor]) == 0:
                break
            currentDoc = postings[cursor][-1][0]
            currentInfo.append(postings[cursor].pop())
            cursor += 1

        else:
            # check if this posting is empty
            if len(postings[cursor]) == 0:
                break
            # While the current doc searching is greater than the id we are looking at now, skip
            while currentDoc < postings[cursor][-1][0]:
                postings[cursor].pop()
                if len(postings[cursor]) == 0:
                    break
            if len(postings[cursor]) == 0:
                break
            # If it is the right id, move the cursor
            if currentDoc == postings[cursor][-1][0]:
                currentInfo.append(postings[cursor].pop())
                cursor += 1
                # If we are at the end, add all the info to the resultInfo
                if cursor == len(postings):
                    for i in range(len(currentInfo)):
                        resultInfo[i][1].append(currentInfo[i])
                    cursor = 0

            # If that id is not intersecting from all the postings, reset the cursor and info
            else:
                currentInfo = []
                cursor = 0

    # Return the result info
    return resultInfo

# Get the postings from the index.txt file
# Output -> [(token, [posting info]), ...]


def getPosting(words, indexMarkers):
    results = []
    i = 100
    with open("index.txt", 'r', encoding="utf-8") as f:
        for word in words:
            if word[0] not in indexMarkers:
                results.append([])
                break
            f.seek(indexMarkers[word[0]][0])
            line = f.readline()
            while line:
                val = re.search("^([a-zA-Z0-9]+) (.+)", line)
                if val == None:
                    continue
                if word == val.group(1):
                    results.append([word, eval(val.group(2))])
                    break
                if i <= 0:
                    if (f.tell() > indexMarkers[word[0]][1]):
                        results.append([])
                        break
                    i = 100
                i -= 1
                line = f.readline()
    if results == []:
        return [[]]
    else:
        return results

# Sort the postings based on doc id in increasing order


def sortPostings(postings):
    for i in range(len(postings)):
        postings[i][1] = sorted(postings[i][1], key=lambda p: p[0])
    return postings

# Get the URL from the DocID.txt file


def getURL(rankedPages, docIDMarkers):
    results = []
    with open("docID.txt", 'r', encoding="utf-8") as f:
        for page in rankedPages:
            docID = page[0]
            seekValue = str((math.floor(docID/1000)*1000)+1)
            f.seek(docIDMarkers[seekValue][0])
            line = f.readline()
            i = 100
            while line:
                val = re.search("^([a-zA-Z0-9]+) (.+)", line)
                if docID == int(val.group(1)):
                    # [(url, header, paragraph), (url, header, paragraph)]
                    results.append(eval(val.group(2)))
                    # here we can also append
                    break
                if i <= 0:
                    if (f.tell() > docIDMarkers[seekValue][1]):
                        results.append("No URL Found for docID")
                        break
                    i = 100
                i -= 1
                line = f.readline()
    return results

# Returns # of pages in all postings


def getTotalPages(postings):
    total = 0
    for posting in postings:
        total += len(posting[1])
    return total

# Sum all the scores together to form a list of tuples
# Output Value = [(DocID, Summed-Scores), ...]


def sumScores(tfidfPostings):
    if len(tfidfPostings) == 1:
        return tfidfPostings[0]
    result = []
    for p in tfidfPostings[0]:
        result.append([p[0], p[1]])
    for posting in tfidfPostings[1:]:
        for i, p in enumerate(posting):
            result[i][1] += p[1]
    return result

# Adds a Tf-Idf score to the posting
# Output Value = [(DocID, Tf-Idf), ...]


def addTfIdfScore(posting, N):
    result = []
    df = len(posting)
    for p in posting:
        TfIdfScore = p[1]*(N/df)
        result.append((p[0], TfIdfScore))
    return result

# Return posting that are sorted and ranked
# Output Value = [(DocID, Score), ...]


def getRankedPages(postings):
    tfidfPostings = []
    N = getTotalPages(postings)
    for posting in postings:
        tfidfPostings.append(addTfIdfScore(posting[1], N))
    summedPostings = sumScores(tfidfPostings)
    return sorted(summedPostings, key=lambda posting: posting[1], reverse=True)

# Print the ranked pages


# def printURLs(rankedPages, results, docIDMarkers):

#         urlList.append(r)
#     return urlList
#     # TODO


def preliminary():
    # Load the markers
    indexMarkers, docIDMarkers = loadMarkers()
    stemmer = PorterStemmer()
    stopWords = []
    with open("StopWords.txt", "r") as file:
        stopWords = [stemmer.stem(line.rstrip('\n').lower()) for line in file]
    return indexMarkers, docIDMarkers, stopWords, stemmer


def searchEngine(query, results, indexMarkers, docIDMarkers, stopWords, stemmer):
    # Ask the user for the query and result amount
    if query == "":
        return []
    query = query.lower()
    # if results == "":
    #     return []
    # results = int(results)

    # Start Timer For Query
    start = timeit.default_timer()

    # Split the query and find the postings associated with each query. If one query has nothing, continue
    query = list(set([stemmer.stem(t.lower()) for t in query.split(' ')]))
    if query == []:
        return []
    sCount = 0
    last = ""
    for i in range(len(query)-1, -1, -1):
        if query[i] in stopWords:
            sCount += 1
            last = query.pop(i)
        elif query[i] == '' or query[i] == ' ':
            query.pop(i)
    if query == []:
        query.append(last)

    queryPostings = getPosting(query, indexMarkers)
    if [] in queryPostings or len(queryPostings) < len(query):
        stop = timeit.default_timer()
        return []

    # Trim the query down so that only intersecting queries exist
        # --QueryPostings look like ->[(Token, [Postings]), ...]
    queryPostings = intersectingPostings(queryPostings)

    # Find the tf-idf of each document and rank it accordingly
    allRankedPages = getRankedPages(queryPostings)
    rankedPages = allRankedPages[:results]
    # Return the [URL, Title, Paragraph] according to score
    if rankedPages == []:
        print("No URL's found for your query")
        return
    infoList = getURL(rankedPages, docIDMarkers)
    # Stop time for the query.
    stop = timeit.default_timer()
    totalTime = stop - start
    return [totalTime, infoList, len(allRankedPages)]
