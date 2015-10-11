__author__ = 'Shane'
# -*- coding: utf-8 -*-
from bottle import *
from operator import itemgetter
from collections import Counter

@route('/hello', method='GET')
def default():
    return '<strong>GET on /hello was called</strong>'

@route ('/', method='GET')
def search():
    #This is the default route
    #This will return
    return '''
        <form action ="/test" method="post">
            <input name="keywords" type = "text" />
            <input value = "Search" type="submit" />
        </form>

    '''




@route('/test', method='POST')
def do_search():
    search = request.forms.get('keywords')
    # password=request.forms.get('password')

    searchWords= search.split()
    wordFrequency =[]
    outputTableHTML =""


    t= """
        <table id="results"?
        </table>
    """


    print wordFrequency



    wordList = []
    for i in searchWords:
        if i not in wordList:
            wordList.append(i)
    counter =0
    print wordList

    #for word in searchWords:
    #    l= wordList[:][0]
    #    print l
    #    if word not in l :
    #        wordFrequency.append([word,0])
    #    else:
    #        wordFrequency[[i for i in range(wordList) if wordList[i] == word]][1]+=1
    for i in range(0,len(wordList)):
        for j in range(0,len(searchWords)):
            if wordList[i] == searchWords[j]:
                counter+=1
        wordFrequency.append([wordList[i],counter])
        counter=0

    print wordFrequency

    wordFrequency = sorted(wordFrequency,key=itemgetter(1),reverse=1)

    limit =20
    if len(wordFrequency)<=20:
        limit =len(wordFrequency)

    for i in range(0,limit):
        outputTableHTML += '<tr> <td>%s</td> <td>%d</td> </tr> ' %(wordFrequency[i][0],wordFrequency[i][1])


    print outputTableHTML
    return """
            <form action ="/" method="post">
            <input name="keywords" type = "text" />
            <input value = "Search" type="submit" />
            </form>
    """+ "<table id=\"results\">" + outputTableHTML

@error(404)
def error404(error):
    return 'What are you doing here? Try a different URL...'

run(host='localhost', port=8080)
