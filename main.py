#!/usr/local/bin/python2.7 
# -*- coding: utf-8 -*-
# (c) Copyright 2015 Purdue University
#
# Author: Gaoping Huang - http://web.ics.purdue.edu/~huang679
# Adapted from:  Alexander J. Quinn - http://alexquinn.org
# License: MIT License - http://opensource.org/licenses/MIT
# Credit:  Loosely based on Tornado "chat_demo" (Apache License by Facebook)
#          https://github.com/tornadoweb/tornado/tree/master/demos/chat
# Version: 0.1

from tornado import ioloop, web, gen, concurrent
import logging, sys, os, json, time
import model

# Settings
PORT             = 8003
DEBUG            = False

# Global data structures
g_events =  ['messages', 'answers', 'questions', 'rejected', 'reward', 'reputation']  # all the events that we are handling
# thus, g_messages[0] is used to store global messages, i.e., g_events[0]
# g_messages[1] is to store global answers, etc
g_messages = [[] for x in g_events]  
# similarly, g_waiters[0] is used to store set of Future objects for 'messages', corresponding to g_events[0]
g_waiters = [set() for x in g_events]
# g_waitroom['g_worker'] stores old list
# g_waitroom['g_worker_compare'] stores recent worker_id lisst
g_waitroom = {"g_worker":list(),"g_worker_compare":list()}
# g_waitroom_set 
g_waitroom_set = set()
g_worker_id = 0
g_time = time.time()

class MainHandler(web.RequestHandler):
    def get(self):
        infos = {
                 'worker_id': self.get_argument('workerId', 'AAA'),
                 'assign_id': self.get_argument('assignmentId','bbb'),
                 'hit_id': self.get_argument('hitId','vvv'),
                 'turkSubmitTo': self.get_argument('turkSubmitTo','ddd'),
                 }

        # Serve index.html blank.  It will fetch new messages upon loading.
        self.render("index.html", infos=infos)

class FetchAllTaskHandler(web.RequestHandler):
    # fetch all tasks and send back to brower
    def post(self):
        tasks = model.FetchDataWithout().fetch_all_task()
        self.write({"tasks":tasks})

class SwitchHandler(web.RequestHandler):
    def post(self):
        #Data from ajax: when trigger,
        data = {
                'task_id'       :   self.get_argument("task_id"),
                'worker_id'     :   self.get_argument("worker_id"),
                'in_room'       :   self.get_argument("in_room"),
                }
        model.ModifyData(data).initiate_worker_record()
        model.ModifyData(data).insert_switch_chatroom_data()
        ##
        
        records = self.initiate_g_records(data["task_id"])
        
        self.write({"records":records})
        
    def initiate_g_records(self, task_id):
        records = model.FetchDataWithout().fetch_task_by_id(task_id)
        fetches = model.FetchDataWithInput(records[0])
        # records[0] means the only one task
        messages = fetches.fetch_all_messages()
        atomic_id_append(messages, 'id', g_messages[g_events.index('messages')])
        
        answers = fetches.fetch_all_qa()
        atomic_id_append(answers, 'quest_id', g_messages[g_events.index('answers')])
        
        # Since g_messages[2] and [3] may decrease its length, we cannot use append. Instead,
        # we have to assign a new value to it
        # global g_messages
        g_messages[g_events.index('questions')] = fetches.fetch_all_questions() 
        g_messages[g_events.index('rejected')] = fetches.fetch_all_rejected()
        g_messages[g_events.index('reward')] = fetches.fetch_all_worker_reward()
        return records


class NewHandler(web.RequestHandler):
    def post(self):
        index = g_events.index('messages')  # Get the index in the g_events, 0
        print "in newhandler"
        # Get new message sent by browser and append it to the global message list
        posts = {
                 'message'     : self.get_argument("message"),
                 'worker_id'   : self.get_argument("worker_id"),
                 'task_id'     : self.get_argument("task_id")
                 }
        # insert into database
        model.ModifyData(posts).insert_message()
        # fetch all messages with task_id
        messages = model.FetchDataWithInput(posts).fetch_all_messages()
        atomic_id_append(messages, 'id', g_messages[index])
                
        # Print a message to the log so we can see what is going on
        logging.info("Sending new message to %r listeners", len(g_waiters[index]))
        # Notify all waiting /update requests
        for future in g_waiters[index]:

            # Set the result of the Future object yielded by the request's coroutine
            future.set_result(g_messages[index])
        # Clear the waiters list
        g_waiters[index].clear()

class UpdateHandler(web.RequestHandler):
    @gen.coroutine
    def post(self):
        index = g_events.index('messages')  # Get the index in the g_events, 0
        # Browser sends the number of messages it has seen so far.
        num_seen = int(self.get_argument("num_seen", 0))
        
        # If there are no new messages (other than what browser has already seen), then wait.
        if num_seen == len(g_messages[index]):
            self._future = concurrent.Future() # Create an empty Future object
            g_waiters[index].add(self._future)                # Add it to the global set of waiters
            yield self._future                         # WAIT until future.set_result(..) is called

        # If browser is still connected, then send the entire list of messages as JSON
        if not self.request.connection.stream.closed():
            self.write({"messages": g_messages[index]})  # This sets Content-Type header automatically

    def on_connection_close(self):     # override tornado.web.RequestHandler.on_connection_close(..)
        # Remove this Future object from the global set of waiters
        g_waiters[g_events.index('messages')].remove(self._future)
        self._future.set_result([])    # Set an empty result to unblock the waiting coroutine(s)


class AnswerHandler(web.RequestHandler):
    def post(self):
        index = g_events.index('answers')  # Get the index in the g_events, 1
        # Get new message sent by browser and append it to the global answer_message list
        answer_posts = {
                 'task_id'     : self.get_argument("task_id"),
                 'mess_id'     : self.get_argument("mess_id"),
                 'answered'    : self.get_argument("num"),
                 'text'        : self.get_argument("text"),
                 }
        # insert into table  answer_record
        model.ModifyData(answer_posts).insert_answer_message()
        # fetch all question/answer pairs with task_id
        answers = model.FetchDataWithInput(answer_posts).fetch_all_qa()
        atomic_id_append(answers, 'quest_id', g_messages[index])
        
        print g_messages[index]
        # Notify all waiting /update requests
        for future in g_waiters[index]:
    
            # Set the result of the Future object yielded by the request's coroutine
            future.set_result(g_messages[index])
    
        # Clear the waiters list
        g_waiters[index].clear()

class CastAnswerHandler(web.RequestHandler):
    @gen.coroutine
    def post(self):
        index = g_events.index('answers')  # Get the index in the g_events, 1
        # Browser sends the number of messages it has seen so far.
        answer_num = int(self.get_argument("answer_number", 0))
        # If there are no new messages (other than what browser has already seen), then wait.
        if answer_num == len(g_messages[index]):
            self._future = concurrent.Future() # Create an empty Future object
            g_waiters[index].add(self._future)                # Add it to the global set of waiters
            yield self._future                         # WAIT until future.set_result(..) is called

        # If browser is still connected, then send the entire list of messages as JSON
        if not self.request.connection.stream.closed():
            # print 'I am in answerhandler, g_messages[1]=', g_messages[1]
            self.write({"answers": g_messages[index]})  # This sets Content-Type header automatically

    def on_connection_close(self):     # override tornado.web.RequestHandler.on_connection_close(..)
        # Remove this Future object from the global set of waiters
        g_waiters[g_events.index('answers')].remove(self._future)
        self._future.set_result([])    # Set an empty result to unblock the waiting coroutine(s)


class QuestionHandler(web.RequestHandler):
    def post(self):
        index = g_events.index('questions')  # Get the index in the g_events, 2
        # Get new message sent by browser
        mark_posts = {
                 'task_id'     : self.get_argument("task_id"),
                 'mess_id'     : self.get_argument("mess_id"),
                 'questioned'  : self.get_argument("num")
                 }
        
        # update the rating column in table message
        model.ModifyData(mark_posts).update_questioned()
        
        # fetch all of the agreed messages'id with task_id to a list
        g_messages[index] = model.FetchDataWithInput(mark_posts).fetch_all_questions()
        
        # Notify all waiting /update requests
        for future in g_waiters[index]:
    
            # Set the result of the Future object yielded by the request's coroutine
            future.set_result(g_messages[index])
    
        # Clear the waiters list
        g_waiters[index].clear()

class CastMarkHandler(web.RequestHandler):
    @gen.coroutine
    def post(self):
        curr_num = int(self.get_argument("questioned_num", 0))
        index = g_events.index('questions')  # Get the index in the g_events, 2
        
        if curr_num == len(g_messages[index]):
            self._future = concurrent.Future() # Create an empty Future object
            g_waiters[index].add(self._future)                # Add it to the global set of waiters
            yield self._future                         # WAIT until future.set_result(..) is called

        # If browser is still connected, then send the entire list of messages as JSON
        if not self.request.connection.stream.closed():
            self.write({"questions": g_messages[index]})  # This sets Content-Type header automatically

    def on_connection_close(self):     # override tornado.web.RequestHandler.on_connection_close(..)
        g_waiters[g_events.index('questions')].remove(self._future)
        self._future.set_result([])    # Set an empty result to unblock the waiting coroutine(s)    


class RejectHandler(web.RequestHandler):
    def post(self):
        # Get new message sent by browser and append it to the global pending_message list
        index = g_events.index('rejected')  # Get the index in the g_events, 3
        mark_posts = {
                 'task_id'     : self.get_argument("task_id"),
                 'mess_id'     : self.get_argument("mess_id"),
                 'rejected'    : self.get_argument("num")
                 }
        
        # update the rating column in table message
        model.ModifyData(mark_posts).update_rejected()
        
        # fetch all of the agreed messages'id with task_id to a list
        g_messages[index] = model.FetchDataWithInput(mark_posts).fetch_all_rejected()

        # Notify all waiting /update requests
        for future in g_waiters[index]:
    
            # Set the result of the Future object yielded by the request's coroutine
            future.set_result(g_messages[index])
    
        # Clear the waiters list
        g_waiters[index].clear()

class CastRejectHandler(web.RequestHandler):
    @gen.coroutine
    def post(self):
        curr_num = int(self.get_argument("rejected_num", 0))
        index = g_events.index('rejected')  # Get the index in the g_events, 3
        if curr_num == len(g_messages[index]):
            self._future = concurrent.Future() # Create an empty Future object
            g_waiters[index].add(self._future)                # Add it to the global set of waiters
            yield self._future                         # WAIT until future.set_result(..) is called

        # If browser is still connected, then send the entire list of messages as JSON
        if not self.request.connection.stream.closed():
            self.write({"rejected": g_messages[index]})  # This sets Content-Type header automatically

    def on_connection_close(self):     # override tornado.web.RequestHandler.on_connection_close(..)
        g_waiters[g_events.index('rejected')].remove(self._future)
        self._future.set_result([])    # Set an empty result to unblock the waiting coroutine(s) 

class NewRewardHandler(web.RequestHandler):
    def post(self):
        # Get new message sent by browser and append it to the global pending_message list
        index = g_events.index('reward')  # Get the index in the g_events, 4
        mark_posts = {
                 'task_id'     : self.get_argument("task_id"),
                 'mess_id'     : self.get_argument("mess_id"),
                 'reward_point': self.get_argument("reward_point")
                 }
        
        # update the reward column in table message, and get id
        worker_id = model.ModifyData(mark_posts).update_reward()

        #fetch reward point of current worker
        g_messages[index] = model.FetchDataWithInput(mark_posts).fetch_all_worker_reward()
        
        # Notify all waiting /update requests
        for future in g_waiters[index]:
    
            # Set the result of the Future object yielded by the request's coroutine
            future.set_result(g_messages[index])
    
        # Clear the waiters list
        g_waiters[index].clear()


class UpdateRewardHandler(web.RequestHandler):
    @gen.coroutine
    def post(self):
        index = g_events.index('reward')  # Get the index in the g_events, 4
        total_reward = int(self.get_argument("total_reward", 0))
        worker_id = self.get_argument("worker_id", 0)
        worker_reward = self.fetch_one_reward(worker_id)
        print g_messages[index], worker_reward
        if total_reward == worker_reward['total_reward']:
            self._future = concurrent.Future() # Create an empty Future object
            g_waiters[index].add(self._future)                # Add it to the global set of waiters
            yield self._future                         # WAIT until future.set_result(..) is called

        # If browser is still connected, then send the entire list of messages as JSON
        if not self.request.connection.stream.closed():
            self.write({"results": worker_reward})  # This sets Content-Type header automatically
    
    # return {'worker_id':'xadf', 'total_reward': 120} based on g_worker_id
    def fetch_one_reward(self, worker_id):
        index = g_events.index('reward')  # Get the index in the g_events, 4
        mark_posts = {}
        for record in g_messages[index]:
            if record['worker_id'] == worker_id:
                mark_posts = record
                break
        if len(mark_posts) == 0:
            mark_posts = {'worker_id': "None", "total_reward": 0}
        return mark_posts
    
    def on_connection_close(self):     # override tornado.web.RequestHandler.on_connection_close(..)
        g_waiters[g_events.index('reward')].remove(self._future)
        self._future.set_result([])    # Set an empty result to unblock the waiting coroutine(s) 

class NewReputationHandler(web.RequestHandler):
    def post(self):
        # Get new message sent by browser and append it to the global pending_message list
        index = g_events.index('reputation')  # Get the index in the g_events, 5
        mark_posts = {
                 'task_id'          : self.get_argument("task_id"),
                 'mess_id'          : self.get_argument("mess_id"),
                 'reputation_change': self.get_argument("reputation_change")
                 }
        
        # update the reputation column in table message, and get id
        worker_id = model.ModifyData(mark_posts).update_reputation()
        
        #fetch reputation score of current worker
        g_messages[index] = model.FetchDataWithInput(mark_posts).fetch_all_worker_reputation()
        
        # Notify all waiting /update requests
        for future in g_waiters[index]:
    
            # Set the result of the Future object yielded by the request's coroutine
            future.set_result(g_messages[index])
    
        # Clear the waiters list
        g_waiters[index].clear()

class UpdateReputationHandler(web.RequestHandler):
    @gen.coroutine
    def post(self):
        index = g_events.index('reputation')  # Get the index in the g_events, 5
        reputation = int(self.get_argument("reputation", 0))
        worker_id = self.get_argument("worker_id", 0)
        worker_reputation = self.fetch_one_reputation(worker_id)

        if reputation == worker_reputation['reputation']:
            self._future = concurrent.Future() # Create an empty Future object
            g_waiters[index].add(self._future)                # Add it to the global set of waiters
            yield self._future                         # WAIT until future.set_result(..) is called

        # If browser is still connected, then send the entire list of messages as JSON
        if not self.request.connection.stream.closed():
            self.write({"results": worker_reputation})  # This sets Content-Type header automatically
    
    # return {'worker_id':'xadf', 'total_reward': 120} based on g_worker_id
    def fetch_one_reputation(self, worker_id):
        index = g_events.index('reputation')  # Get the index in the g_events, 5
        mark_posts = {}
        for record in g_messages[index]:
            if record['worker_id'] == worker_id:
                mark_posts = record
                break

        if len(mark_posts) == 0:
            mark_posts = {'worker_id': "None", "reputation": 0}
        return mark_posts
    
    def on_connection_close(self):     # override tornado.web.RequestHandler.on_connection_close(..)
        g_waiters[g_events.index('reputation')].remove(self._future)
        self._future.set_result([])    # Set an empty result to unblock the waiting coroutine(s) 

class NewUserHandler(web.RequestHandler):
    def post(self):
        # add id to compare list 
        worker_id = self.get_argument("ids")
        if worker_id not in g_waitroom["g_worker_compare"]:
            g_waitroom['g_worker_compare'].append(worker_id)
        # compare list with real g_worker
        # if g_waitroom["g_worker"] != g_waitroom["g_worker_compare"]:
        current_time = time.time()
        global g_time
        print g_time, worker_id
        #print current_time
        if current_time - g_time > 5:
            g_time = current_time
            #for future in g_waiters[index]:
            #    future.set_result(g_ids)
            g_waitroom["g_worker"] = g_waitroom["g_worker_compare"]
        
        if g_waitroom["g_worker"] == g_waitroom["g_worker_compare"]:
            for future in g_waitroom_set:
                future.set_result(g_waitroom["g_worker"])
            g_waitroom["g_worker_compare"]= []
            #Clear the waiters list
            g_waitroom_set.clear()

        
class UpdateUserHandler(web.RequestHandler):
    @gen.coroutine
    def post(self):
        #Get num_seen so far
        num_seen = int(self.get_argument("num_seen"))

        if num_seen == len(g_waitroom["g_worker"]):
            self._future = concurrent.Future()
            g_waitroom_set.add(self._future)
            yield self._future

        data = {"worker_number":len(g_waitroom["g_worker"]),"g_ids":g_waitroom["g_worker"]}
        
        if not self.request.connection.stream.closed():
            self.write({"data":data})
        
    
    def on_connection_close(self):
        g_waitroom_set.remove(self._future) 
        self._future.set_result([])
 

        
def atomic_id_append(results, key, g_results):
    ids = []  # ids that are already in g_results
    for g_result in g_results:
        ids.append(g_result[key])
    # print ids
    for result in results:
        if result[key] not in ids:
            g_results.append(result)


def main():
    # Create the Application object
    app = web.Application(
        [ (r"/",            MainHandler),
          (r"/new",         NewHandler),
          (r"/update",      UpdateHandler),
          (r"/answered",    AnswerHandler),
          (r"/cast_answer", CastAnswerHandler),
          (r"/questioned",  QuestionHandler),
          (r"/cast_mark",   CastMarkHandler),
          (r"/rejected",    RejectHandler),
          (r"/cast_reject", CastRejectHandler),
          (r"/new_reward",  NewRewardHandler),
          (r"/update_reward", UpdateRewardHandler),
          (r"/new_reputation", NewReputationHandler),
          (r"/update_reputation", UpdateReputationHandler),
          (r"/new_user",    NewUserHandler),
          (r"/switch",      SwitchHandler),
          (r"/task",       FetchAllTaskHandler),
          (r"/update_user", UpdateUserHandler),],
        template_path = os.path.join(os.path.dirname(__file__), "templates"),
        static_path   = os.path.join(os.path.dirname(__file__), "static"),
        debug         = DEBUG,
    )
    # Start the HTTP server and the IOLoop.  (These work together.)
    app.listen(port=PORT)
    sys.stderr.write("Starting server at http://localhost:%d\n"%PORT)
    ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    main()
