# ICSearch Engine

Created By Timothy Simanhadi, Jody Jamin

### Description
Inverted index and search engine implementation. Search included subdomains from uci.edu. The search engine will search words from an input and parse through the indexed websites. It returns websites based on relevance to the words inputted. Stop words are removed from the search query and the query is porter stemmed. The search engine will take words from the query and look through the index.txt and indexMarkers.txt file that contains postings (docID, tf score, title, information) and docID/URL pairings respectively to match. We rank the highest scoring documents using our tf/idf and important word scoring heuristic. Finally we return the most relevant websites to our flask app.

### How To Run
Download the repository. Unzip index.txt and run app.py.
### Implementation
- tf-idf and important word scoring heuristic
- inverted index
- fingerprint (duplicate removal)
- inverted index creation
- word stemming
- web interface (flask)
- fast response time (< 300ms)
  
![searchEngineDemo](https://media.giphy.com/media/H4YBD1XwDzTLlaXenc/giphy.gif)
