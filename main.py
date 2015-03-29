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

g_messages = []     # list of messages, each as plain text
g_waiters  = set()  # set of Future objects, one for each waiting /update request
g_pendings = []
g_pending_waiters = set()
g_questions  = []
g_question_waiters = set()

class MainHandler(web.RequestHandler):
    def get(self):
        # fetch random task
        records = model.FetchDataWithout().fetch_random_task()
        # records[0] means the only one task
        messages = model.FetchDataWithInput(records[0]).fetch_all_messages()
        atomic_id_append(messages, g_messages)
        
        pendings = model.FetchDataWithInput(records[0]).fetch_all_pendings()
        atomic_id_append(pendings, g_pendings)
        
        # Since g_questions may decrease its length, we cannot use append. Instead,
        # we have to assign a new value to it
        global g_questions
        g_questions = model.FetchDataWithInput(records[0]).fetch_all_questions()

        # Serve index.html blank.  It will fetch new messages upon loading.
        self.render("index.html", records=records)

class NewHandler(web.RequestHandler):
    def post(self):
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
        for message in messages:
            if message not in g_messages:
                g_messages.append(message)
        # Print a message to the log so we can see what is going on
        print g_messages
        logging.info("Sending new message to %r listeners", len(g_waiters))
        # Notify all waiting /update requests
        for future in g_waiters:

            # Set the result of the Future object yielded by the request's coroutine
            future.set_result(g_messages)

        # Clear the waiters list
        g_waiters.clear()

class UpdateHandler(web.RequestHandler):
    @gen.coroutine
    def post(self):
        # Browser sends the number of messages it has seen so far.
        num_seen = int(self.get_argument("num_seen", 0))
        
        # If there are no new messages (other than what browser has already seen), then wait.
        if num_seen == len(g_messages):
            self._future = concurrent.Future() # Create an empty Future object
            g_waiters.add(self._future)                # Add it to the global set of waiters
            yield self._future                         # WAIT until future.set_result(..) is called

        # If browser is still connected, then send the entire list of messages as JSON
        if not self.request.connection.stream.closed():
            self.write({"messages": g_messages})  # This sets Content-Type header automatically

    def on_connection_close(self):     # override tornado.web.RequestHandler.on_connection_close(..)
        g_waiters.remove(self._future) # Remove this Future object from the global set of waiters
        self._future.set_result([])    # Set an empty result to unblock the waiting coroutine(s)


class AppendHandler(web.RequestHandler):
    def post(self):
        # Get new message sent by browser and append it to the global pending_message list
        pending_posts = {
                 'worker_id'   : self.get_argument("worker_id"),
                 'task_id'     : self.get_argument("task_id"),
                 'mess_id'     : self.get_argument("mess_id")
                 }
        # insert into table  pending_record
        model.ModifyData(pending_posts).insert_pending_message()
        # fetch all pending messages with task_id
        pendings = model.FetchDataWithInput(pending_posts).fetch_all_pendings()
        for pending in pendings:
            if pending not in g_pendings:
                g_pendings.append(pending)
        # Print a message to the log so we can see what is going on
        logging.info("Sending new message to %r listeners", len(g_waiters))
    
        # Notify all waiting /update requests
        for future in g_pending_waiters:
    
            # Set the result of the Future object yielded by the request's coroutine
            future.set_result(g_pendings)
    
        # Clear the waiters list
        g_pending_waiters.clear()

class PendingHandler(web.RequestHandler):
    @gen.coroutine
    def post(self):
        # Browser sends the number of messages it has seen so far.
        pending_num = int(self.get_argument("pending_number", 0))
        
        # If there are no new messages (other than what browser has already seen), then wait.
        if pending_num == len(g_pendings):
            self._future = concurrent.Future() # Create an empty Future object
            g_pending_waiters.add(self._future)                # Add it to the global set of waiters
            yield self._future                         # WAIT until future.set_result(..) is called

        # If browser is still connected, then send the entire list of messages as JSON
        if not self.request.connection.stream.closed():
            # print 'I am in pendinghandler, g_pendings=', g_pendings
            self.write({"pendings": g_pendings})  # This sets Content-Type header automatically

    def on_connection_close(self):     # override tornado.web.RequestHandler.on_connection_close(..)
        g_pending_waiters.remove(self._future) # Remove this Future object from the global set of waiters
        self._future.set_result([])    # Set an empty result to unblock the waiting coroutine(s)


class QuestionHandler(web.RequestHandler):
    def post(self):
        # Get new message sent by browser and append it to the global pending_message list
        mark_posts = {
                 'task_id'     : self.get_argument("task_id"),
                 'mess_id'     : self.get_argument("mess_id"),
                 'questioned'  : self.get_argument("num")
                 }
        
        # update the rating column in table message
        model.ModifyData(mark_posts).update_questioned()
        
        # fetch all of the agreed messages'id with task_id to a list
        global g_questions
        g_questions = model.FetchDataWithInput(mark_posts).fetch_all_questions()

        # Print a message to the log so we can see what is going on
        logging.info("Sending new message to %r listeners", len(g_question_waiters))
        # Notify all waiting /update requests
        for future in g_question_waiters:
    
            # Set the result of the Future object yielded by the request's coroutine
            future.set_result(g_questions)
    
        # Clear the waiters list
        g_question_waiters.clear()

class CastMarkHandler(web.RequestHandler):
    @gen.coroutine
    def post(self):
        curr_num = int(self.get_argument("questioned_num", 0))
        if curr_num == len(g_questions):
            self._future = concurrent.Future() # Create an empty Future object
            g_question_waiters.add(self._future)                # Add it to the global set of waiters
            yield self._future                         # WAIT until future.set_result(..) is called

        # If browser is still connected, then send the entire list of messages as JSON
        if not self.request.connection.stream.closed():
            self.write({"questions": g_questions})  # This sets Content-Type header automatically

    def on_connection_close(self):     # override tornado.web.RequestHandler.on_connection_close(..)
        g_question_waiters.remove(self._future) # Remove this Future object from the global set of waiters
        self._future.set_result([])    # Set an empty result to unblock the waiting coroutine(s)    

def atomic_id_append(results, g_results):
    ids = []  # ids that are already in g_results
    for g_result in g_results:
        ids.append(g_result['id'])
    # print ids
    for result in results:
        if result['id'] not in ids:
            g_results.append(result)


def main():
    # Create the Application object
    app = web.Application(
        [ (r"/",            MainHandler),
          (r"/new",         NewHandler),
          (r"/update",      UpdateHandler),
          (r"/append",      AppendHandler),
          (r"/pending",     PendingHandler),
          (r"/questioned",  QuestionHandler),
          (r"/rejected",    RejectHandler),
          (r"/cast_mark",   CastMarkHandler),
          (r"/cast_answer", CastAnswerHandler) ],
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
