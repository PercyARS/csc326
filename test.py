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
        # if this word id doesn't exist in the dictionary yet
        if _word_id != last_WordId:
            dict[_word_id] = set([_doc_id])
            #print dict[_word_id]
        else:
            temp = dict[_word_id]
            temp.add(_doc_id)
            dict[_word_id] = temp
            #print "duplicate wordid:!" + _word_id
            #tempSet = dict[_word_id].add(_doc_id)
            #dict[_word_id] = tempSet
        last_WordId = _word_id
    print dict