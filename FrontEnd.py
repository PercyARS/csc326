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
        <form action ="/" method="post">
            <input name="keywords" type = "text" />
            <input value = "Search" type="submit" />
        </form>

    '''


wordFrequency =[]
histogram=[]
@route('/', method='POST')
def do_search():
    #search contains the string of words from the browser
    search = request.forms.get('keywords')

    #searchWords will now be a List of all the words from the browser input
    searchWords= search.split()

    #wordFrequency will contain the final results of the input from the user broken down to the number of occurances in the search text.
    global wordFrequency
    global histogram
    #This for loop will go and take previously entered data and add it back into the search words list so that it may be re-entered in the histogram
    for i in range(len(wordFrequency)):
        for j in range(wordFrequency[i][1]):
            searchWords.append(wordFrequency[i][0])




    #reset wordFrequency so it can be used again.
    wordFrequency = []
    #Declare the string variable for the HTML output string
    outputTableHTML ="<table id=\"results\"> <tr> <td>Word</td> <td>Count</td> </tr>"
    outputTableHTML2 ="<table id=\"results\"> <tr> <td>Word History</td></tr>"
    #histogram is a Dict that contains the number of occurances
    histogram = Counter(searchWords)

    #Convert the Dictionary into a List so i can sort the words
    for key, value in histogram.iteritems():
        temp = [key,value]
        wordFrequency.append(temp)

    #Sort the List using the function sorted using itemgetter on index 1 and then sort in reverse.
    wordFrequency = sorted(wordFrequency,key=itemgetter(1),reverse=1)


    # Set the limit of words displayed in the HTML Table
    limit =20 # Set the default limit to 20 so if there are 40 words the limit will always be 20
    if len(wordFrequency)<=20: #If the number of words in wordFrequency is less than 20, just output whatever is there
        limit =len(wordFrequency)

    # Loop from i to the limit
    for i in range(limit):
        outputTableHTML += '<tr> <td>%s</td> <td>%d</td> </tr> ' %(wordFrequency[i][0],wordFrequency[i][1]) #This adds the words from list wordFrequency to the outputHTML string

    for i in range(len(wordFrequency)):
        outputTableHTML2 += '<tr> <td>%s</td> </tr> ' %(wordFrequency[i][0]) #This adds the words from lis

    # Output the search input box along with the HTML table of the previous search words
    return """
            <h1>3PP</h1>
            <form action ="/" method="post">
            <input name="keywords" type = "text" />
            <input value = "Search" type="submit" />
            </form>
    """ + outputTableHTML #+ outputTableHTML2

#This displays the error page when an invalid URL is typed into the browser
@error(404)
def error404(error):
    return 'What are you doing here?!?! Go away and try a different URL...'

#This runs the webserer on host 'localhost' and port 8080. Can be accessed using http://localhost:8080/
run(host='localhost', port=8080)
