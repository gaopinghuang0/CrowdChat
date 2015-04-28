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
			try:
				value = int(value)
			except:
				value = value
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
#			  if 'edit_time' in result:
#				  result['edit_time'] = transfer_relative_time(result['edit_time'])
			results.append(result)
		return results


class ModifyData(InOut):
	
	# insert new message
	def insert_message(self):
		if isinstance(self.message, int) or len(self.message) > 0:
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
	# insert info of worker when enter chatrooom
	def insert_switch_chatroom_data(self):
		
		db.insert('chatroom_record', task_id = self.task_id, worker_id = self.worker_id, \
				  enter_time = self.edit_time, in_room = self.in_room )
		
	# insert into table rating_record
	# and update the rating column in table message			 
	def update_reward(self):
		# first check whether this messid has been rewarded
		# if yes, prevent inserting twice
		inserted = tuple(db.select("reward_record", where="mess_id=$mess_id",
										vars={'mess_id':self.mess_id}))
		if len(inserted) > 0:
			my_warning("duplicate insert reward")
			# return worker_id and False as well
			return inserted[0].worker_id, False  
		# fetch old points based on the mess_id
		# add old points and new point
		records = tuple(db.query('''SELECT worker.total_reward as total_reward, 
					worker.worker_id as worker_id from worker, message where 
					worker.worker_id=message.worker_id and
					message.id=%d'''%(self.mess_id)))[0]
		old_reward, worker_id = records.total_reward, records.worker_id
		db.insert('reward_record', worker_id=worker_id, mess_id=self.mess_id, \
				  record=self.reward_point, edit_time=self.edit_time)
		db.update('worker', where="worker_id=$worker_id", vars={'worker_id':worker_id},\
				total_reward=old_reward+self.reward_point)
		return worker_id, True   # return worker.worker_id
	
	# insert into table reputation_record
	# and update the reputation column in table message			 
	def update_reputation(self):
		# fetch old points based on the mess_id
		# add old points and new point
		records = tuple(db.query('''SELECT worker.reputation as reputation, worker.worker_id as worker_id from worker, message where worker.worker_id=message.worker_id and
					message.id=%d'''%(int(self.mess_id))))[0]
		old_reputation, worker_id = records.reputation, records.worker_id
		db.insert('reputation_record', worker_id=worker_id, mess_id=self.mess_id, \
				  record=self.reputation_change, edit_time=self.edit_time)
		db.update('worker', where="worker_id=$worker_id", vars={'worker_id':worker_id}, reputation=old_reputation+self.reputation_change)
		
		#set status of worker to be 0 if he or she has a reputation of -10
		if (old_reputation + self.reputation_change) == -10:
			dp.update('worker', where="worker_id=$worker_id", vars={'worker_id':worker_id}, status=0)

		return worker_id  # return worker.id, not worker.worker_id

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
		
	def initiate_worker_record(self):
		# try to update if exists
		db.query("INSERT OR IGNORE INTO worker(worker_id, edit_time) VALUES('%s', '%s')" %(self.worker_id, self.edit_time))

class FetchDataWithInput(InOut):
	
	''' Fetch data with input, like task_id or worker_id. ''' 
	
	def fetch_all_messages(self):
		records = tuple(db.select('message',
								   where="task_id=$task_id",
								   vars={"task_id":self.task_id}))
		return self.tuple_to_list(records)
	
	def fetch_all_qa(self):
		assert isinstance(self.task_id, int)
		# select Q/A id pairs	  ^_^
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
	
	# fetch all_worker_reward based on worker_id
	def fetch_all_worker_reward(self):
		print 'in fetch_all_worker_reward',self.task_id
		records = tuple(db.query('''SELECT worker.total_reward as total_reward, 
					worker.worker_id as worker_id from worker, chatroom_record where worker.worker_id = chatroom_record.worker_id and 
					chatroom_record.task_id=%d group by worker.worker_id'''%(self.task_id)))
		return self.tuple_to_list(records)
	
	# fetch all_worker_reputation based on worker_id
	def fetch_all_worker_reputation(self):
		records = tuple(db.query('''SELECT worker.reputation as reputation, 
					worker.worker_id as worker_id from worker, chatroom_record where worker.worker_id = chatroom_record.worker_id and 
					chatroom_record.task_id=%d'''%(self.task_id)))
		return self.tuple_to_list(records) 
	
	
class FetchDataWithout(object):
	
	''' Fetch data with no input or match condition. '''
	
	def fetch_task_by_id(self, task_id):
		tasks = tuple(db.select('task',
								where="id=$task_id",
								vars={"task_id":decrypt_id(task_id)}
								  ))
		return self.append_task_info(tasks)
	
	def fetch_all_task(self):
		tasks = tuple(db.query('''SELECT id, text from task '''  ))
		records = []
		for task in tasks:
			task_id = task.id
			task_text = task.text
			record = {
					  "task_id"		  : encrypt_id(task_id),
					  "text"		  : task_text,
					  "unique_code"   : generate_unique_code()
					  }
			records.append(record)
		return InOut({}).tuple_to_list(records)
	
	def append_task_info(self, tasks):
		records = []
		for task in tasks:
			task_id = task.id
			task_text = task.text
			requester_id = task.requester_id
			record = {
					  "task_id"		  : encrypt_id(task_id),
					  "text"		  : task_text,
					  "requester_id"  : requester_id,
					  "unique_code"   : generate_unique_code()
					  }
			records.append(record)
		return InOut({}).tuple_to_list(records)

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

def my_warning(mess):
	print "\nWarning: %s\n"%mess
