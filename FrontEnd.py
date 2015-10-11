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
        <h1>3PP</h1>
        <form action ="/results" method="post">
            <input name="keywords" type = "text" />
            <input value = "Search" type="submit" />
        </form>

    '''




@route('/results', method='POST')
def do_search():
    #search contains the string of words from the browser
    search = request.forms.get('keywords')

    #searchWords will now be a List of all the words from the browser input
    searchWords= search.split()

    wordFrequency =[]
    histogram = []

    #Declare the string variable for the HTML output string
    outputTableHTML =""

    #histogram is a Dict that contains the number of occurances
    histogram = Counter(searchWords)

    #Convert the Dictionary into a List so i can sort the words
    for key, value in histogram.iteritems():
        temp = [key,value]
        wordFrequency.append(temp)





    #print wordFrequency

    #for i in searchWords:
    #    if i not in wordList:
    #        wordList.append(i)
    #counter =0
    #print wordList

    #for word in searchWords:
    #    l= wordList[:][0]
    #    print l
    #    if word not in l :
    #        wordFrequency.append([word,0])
    #    else:
    #        wordFrequency[[i for i in range(wordList) if wordList[i] == word]][1]+=1


    #for i in range(0,len(wordList)):
    #    for j in range(0,len(searchWords)):
    #        if wordList[i] == searchWords[j]:
    #            counter+=1
    #    wordFrequency.append([wordList[i],counter])
    #    counter=0

    #print wordFrequency

    wordFrequency = sorted(wordFrequency,key=itemgetter(1),reverse=1)


    # Set the limit of words displayed in the HTML Table
    limit =20 # Set the default limit to 20 so if there are 40 words the limit will always be 20
    if len(wordFrequency)<=20: #If the number of words in wordFrequency is less than 20, just output whatever is there
        limit =len(wordFrequency)

    # Loop from i to the limit
    for i in range(limit):
        outputTableHTML += '<tr> <td>%s</td> <td>%d</td> </tr> ' %(wordFrequency[i][0],wordFrequency[i][1]) #This adds the words from list wordFrequency to the outputHTML string


    #print outputTableHTML
    # Output the search input box along with the HTML table of the previous search words.


    t= """
        <table id="results"?
        </table>
    """

    return """
            <h1>3PP</h1>
            <form action ="/results" method="post">
            <input name="keywords" type = "text" />
            <input value = "Search" type="submit" />
            </form>
    """+ "<table id=\"results\">" + outputTableHTML

#This displays the error page when an invalid URL is typed into the browser
@error(404)
def error404(error):
    return 'What are you doing here? Try a different URL...'

#This runs the webserer on host 'localhost' and port 8080. Can be accessed using http://localhost:8080/
run(host='localhost', port=8080)
