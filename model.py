# -*- coding: utf-8 -*-
from __future__ import division, unicode_literals # boilerplate
from datetime import datetime
import random, string, json
from hashids import Hashids
import web
# from _sqlite3 import InterfaceError
# from itertools import groupby
# from fuzzywuzzy import fuzz
# from nltk.corpus import stopwords

# hashids encrypt with salt and min_length=6
hashids = Hashids(salt="This is tornado salt", min_length=6)

# webpy db
db = web.database(dbn="sqlite", db='data/main.sqlite')

def generate_unique_code(size=8, chars=string.ascii_uppercase + 
                    string.ascii_lowercase + string.digits):
    return ''.join(random.SystemRandom().choice(chars) for _ in range(size))

def encrypt_id(id):
    if isinstance(id, unicode):
        id = int(id)
    return hashids.encrypt(id)

def decrypt_id(test):
    try:
        ids = hashids.decrypt(test)
        return ids[0]
    except IndexError:
        return None

class InOut(object):
    
    ''' Handle I/O.'''
    
    def __init__(self, data):
        self.edit_time =  str(datetime.now())
        for key, value in data.iteritems():
            if key == 'task_id':
                setattr(self, key, decrypt_id(value))
            else:
                setattr(self, key, value)

    def tuple_to_list(self, records):
        '''
        Receive a tuple of db instance and return list of dist.
        
        For example, in the form of [{'id':1}, {'text':'xxx'}].
        The list is still editable.
        '''
        results = []
        for record in records:
            result = dict((key, value) for key, value in record.iteritems())
#             if 'edit_time' in result:
#                 result['edit_time'] = transfer_relative_time(result['edit_time'])
            results.append(result)
        return results


class ModifyData(InOut):
    
    def insert_message(self):
        if len(self.message) > 0:
            db.insert('message', text=self.message, worker_id=self.worker_id, \
                        task_id=self.task_id, edit_time=self.edit_time)


class FetchDataWithInput(InOut):
     
    def fetch_all_messages(self):
        records = tuple(db.select('message',
                                   where="task_id=$task_id",
                                   vars={"task_id":self.task_id}))
        messages = self.tuple_to_list(records)
        return messages

class FetchDataWithout(object):
    
    ''' Fetch data with no input or match condition. '''
    
    def fetch_random_task(self):
        tasks = tuple(db.query("SELECT * from task ORDER BY RANDOM() LIMIT 1"))
        records = []
        for task in tasks:
            task_id = task.id
            task_text = task.text
            requester_id = task.requester_id
            record = {
                      "task_id"       : encrypt_id(task_id),
                      "text"          : task_text,
                      "requester_id"  : requester_id,
                      "unique_code"   : generate_unique_code()
                      }
            records.append(record)
        return records
    
   