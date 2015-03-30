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
import logging, sys, os, json
import model

# Settings
PORT             = 8003
DEBUG            = False

# Global data structures
g_events =  ['messages', 'answers', 'questions', 'rejected']  # all the events that we are handling
# thus, g_messages[0] is used to store global messages, i.e., g_events[0]
# g_messages[1] is to store global answers, etc
g_messages = [[] for x in g_events]  
# similarly, g_waiters[0] is used to store set of Future objects for 'messages', corresponding to g_events[0]
g_waiters = [set() for x in g_events]


class MainHandler(web.RequestHandler):
    def get(self):
        # fetch random task
        records = model.FetchDataWithout().fetch_random_task()
        # records[0] means the only one task
        messages = model.FetchDataWithInput(records[0]).fetch_all_messages()
        atomic_id_append(messages, 'id', g_messages[g_events.index('messages')])
        
        answers = model.FetchDataWithInput(records[0]).fetch_all_qa()
        atomic_id_append(answers, 'quest_id', g_messages[g_events.index('answers')])
        
        # Since g_messages[2] and [3] may decrease its length, we cannot use append. Instead,
        # we have to assign a new value to it
        # global g_messages
        g_messages[g_events.index('questions')] = model.FetchDataWithInput(records[0]).fetch_all_questions() 
        g_messages[g_events.index('rejected')] = model.FetchDataWithInput(records[0]).fetch_all_rejected()

        # Serve index.html blank.  It will fetch new messages upon loading.
        self.render("index.html", records=records)

class NewHandler(web.RequestHandler):
    def post(self):
        index = g_events.index('messages')  # Get the index in the g_events, 0
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
        global g_messages
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
        global g_messages
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
          (r"/cast_reject", CastRejectHandler)],
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
