#!/usr/local/bin/python2.7
# -*- coding: utf-8 -*-
# (c) Copyright 2015 Purdue University
#
# Author: Gaoping Huang - https://github.com/gaopinghuang0
# License: MIT License - http://opensource.org/licenses/MIT
# Version: 0.1


from __future__ import division, unicode_literals # boilerplate
from datetime import datetime
import random, string, json
from hashids import Hashids
import web
import time
# from _sqlite3 import InterfaceError
# from itertools import groupby
# from fuzzywuzzy import fuzz
# from nltk.corpus import stopwords

# hashids encrypt with salt and min_length=6
hashids = Hashids(salt="This is tornado salt", min_length=6)

# webpy db
db = web.database(dbn="sqlite", db='data/crowdchat.sqlite')

class InOut(object):
    
    ''' Handle data in and out.'''
    
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
        
        For example, return a list with the form of [{'id':1}, {'text':'xxx'}].
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
    
    # insert new message
    def insert_message(self):
        if len(self.message) > 0:
            db.insert('message', text=self.message, worker_id=self.worker_id, \
                        task_id=self.task_id, edit_time=self.edit_time)

    # insert new question and answer pair
    def insert_answer_message(self):
        if isinstance(self.task_id, int):
            # find the mess id of answer
            ans_id = 0
            # since the new message is inserted by other function
            # we need a loop to wait until the message is actually inserted
            while ans_id == 0 :
                #time.sleep(0.1)
                records = tuple(db.select("message", 
                                          where="text=$text and task_id=$task_id",
                                          vars={'text':self.text, 'task_id':self.task_id}))
                if len(records) > 0:
                    ans_id = records[0].id
            # insert the ids of answer and question pairs
            db.insert('answer_record', ans_id=ans_id, quest_id=self.mess_id, \
                      task_id=self.task_id, edit_time=self.edit_time)
            # update the 'answered' column of question id
            db.update('message', where="id=$id", vars={'id':self.mess_id}, answered=self.answered)
            
    # insert into table rating_record
    # and update the rating column in table message          
    def update_ratings(self):
        db.insert('rating_record', task_id=self.task_id, mess_id=self.mess_id, \
                  temp_rating=self.rating, edit_time=self.edit_time)
        db.update('message', where="id=$id", vars={'id':self.mess_id}, rating=self.rating)
    
    # insert the question mark record to question_record table    
    # update the questioned column in table "message"
    def update_questioned(self):
        # db.insert(), add later
        db.update('message', where="id=$id", vars={'id':self.mess_id}, questioned=self.questioned)
    
    # insert the reject record to a table
    # update the rejected column in table "message"
    def update_rejected(self):
        # db.insert(), add later
        db.update('message', where="id=$id", vars={'id':self.mess_id}, rejected=self.rejected)

class FetchDataWithInput(InOut):
    
    ''' Fetch data with input, like task_id or worker_id. ''' 
    
    def fetch_all_messages(self):
        records = tuple(db.select('message',
                                   where="task_id=$task_id",
                                   vars={"task_id":self.task_id}))
        return self.tuple_to_list(records)
    
    def fetch_all_qa(self):
        assert isinstance(self.task_id, int)
        # select Q/A id pairs     ^_^
        records = tuple(db.query('''SELECT ans_rec.quest_id as quest_id, q.text as quest,
                                ans_rec.ans_id as ans_id, a.text as answer 
                                from answer_record as ans_rec, message as q, message as a
                                where ans_rec.quest_id=q.id and ans_rec.ans_id=a.id and ans_rec.task_id=%d;'''
                                 % (self.task_id)))
        return self.tuple_to_list(records)
    
    def fetch_all_ratings(self):
        records = tuple(db.query('''SELECT id from message where rating=1 and id in
                                (SELECT mess_id from pending_record where task_id=%d);'''
                                 % (self.task_id)))
        return self.tuple_to_list(records)
    
    # fetch all questioned messages' ids
    def fetch_all_questions(self):
        records = tuple(db.query('''SELECT id from message where questioned=1 and task_id=%d;'''
                                 % (self.task_id)))
        return self.tuple_to_list(records)
    
    # fetch all rejected messages' ids into a list
    def fetch_all_rejected(self):
        records = tuple(db.query('''SELECT id from message where rejected=1 and task_id=%d;'''
                                 % (self.task_id)))
        return self.tuple_to_list(records)
    
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
    
   