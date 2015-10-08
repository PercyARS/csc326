__author__ = 'zhaopeix'
import urllib2
import urlparse
from BeautifulSoup import *
from collections import defaultdict
import re
import sqlite3


dict = {}
_db_conn = None
try:
    _db_conn = sqlite3.connect('backend.db')
except sqlite3.Error, e:
    print "Error %s:" % e.args[0]
with _db_conn:
    c = _db_conn.cursor()
    c.execute('SELECT * FROM InvertIndex ORDER BY WordId')
    rows = c.fetchall()
    last_WordId = 0
    for tuples in rows:
        _word_id = tuples[0]
        _doc_id = tuples[1]
        c.execute('SELECT words FROM Lexicon WHERE Id=?', (_word_id,))
        _word = c.fetchone()[0]
        #print "word id is: "
        print _word_id
        #print "word  is: " + _word
        c.execute('SELECT doc_url FROM Document WHERE Id=?', (_doc_id,))
        _url = c.fetchone()[0]
        #print "doc id is: "
        #print _doc_id
        #print "url  is: " + _url
        # if this word doesn't exist in the dictionary yet
        if _word_id != last_WordId:
            print "word is "+_word
            dict[_word] = set([_url])
        else:
            print "word is "+_word
            temp = dict[_word]
            temp.add(_url)
            dict[_word] = temp
        last_WordId = _word_id
    print dict