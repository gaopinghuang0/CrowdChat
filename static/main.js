/* (c) Copyright 2015 Purdue University - MIT License */
(function(){
	/* Some global variables */
	var g_num_seen = 0; 
	var g_answer_num = 0;
	var g_questioned_num = 0;  
	var g_rejected_num = 0;
	var g_worker_id;
	var g_id_seen = 0;
	var g_total_reward = 0;
	var req_id;
	var g_task_id;
	var unique_code;
	var g_url_prefix = '';  // "" means localhost, /03 means 03 port
	var MIN_INPUT = 5;


jQuery(document).ready(function() {
	initiate_chatroom(1);   // for test, task_id is set to 1
});


function initiate_chatroom(task_id) {
    $("#message_input").on("keypress", handle_new_message_event);
	$("#messages_display").perfectScrollbar();
	$("#candidates_container").perfectScrollbar();
	$("#message_input").select();
	g_worker_id = get_all_ids().worker_id;
	req_id = get_all_ids().req_id;
	g_task_id = task_id;
	unique_code = get_all_ids().unique_code;
	if (req_id == g_worker_id) {
		$("#roommode").text('(requester)');
	} else {
		var worknum = g_worker_id == 'BBB' ? 1:2;
		$("#roommode").text('(worker'+worknum+')');
	}
    count_user_handler();
    add_new_ids(); 
    console.log(g_worker_id);
	
    poll();  // Check for new messages
    answer_poll(); // Check for new answer messages
    // rating_poll();  // Check for new ratings
    marking_poll();  // Check for new marking question
    reject_poll();   // Check for new rejecting message
    reward_poll();   // check for new reward
}


function handle_new_message_event(evt) {
    if(evt.which == 13) {  // only respond to enter key
        // Tell browser (via jQuery) not to try to submit the form the normal way
        evt.preventDefault();

        // Prevent user from typing more messages until last one is processed
        var message_input = document.getElementById("message_input");
        message_input.disabled = true;   // Disable text box

        // Send new message to the server using AJAX
        if ($("#message_input").val().length > MIN_INPUT) {
            jQuery.ajax({
                url: url_for("/new"),
                data: { message   : message_input.value,
                		worker_id : g_worker_id,
                		task_id   : g_task_id },
                type: "POST",
                success: function(data, text_status, jq_xhr) {
                    message_input.value = "";
                    message_input.disabled = false;
                    message_input.select();
                },
                error: function(jq_xhr, text_status, error_thrown) {
                    console.log("ERROR POSTING NEW MESSAGE:", error_thrown);
                }
            });
        }
        else {
        	open_error_dialog();
        	message_input.disabled = false;
        	return false;
        }
    }
}

function poll() {
	jQuery.ajax({
		url: url_for("/update"),
		type: "POST",
		data: {num_seen: g_num_seen},
		success: function(data, text_status, jq_xhr) {
            // Display the messages in the DIV with id="messages_display"
			var new_parts = [];
			var prev_parts = $("#messages_display ul").html();  // string
			for(var i = 0; i < data.messages.length; i++) {
                var message = data.messages[i];
				var html = safe_text(message.text);
				var each_worker_id = message.worker_id;
				var each_time = message.edit_time;
				var each_id = message.id;
				
				if (each_worker_id == g_worker_id) {  // it's me
					html = '<li class="message mymess"><span messid="'+each_id+'">' + html + '</span>'+
					'<div class="head_img"><img src="./static/images/head.jpg" alt="worker"></div></li>';
				}
				else {  // others' message
					if (each_worker_id == req_id)  {  // requster's mess
						html = '<li class="message othersmess reqmess"><span messid="'+each_id+'">Requester: ' +
						       html + '</span></li>';
					}
					else {  // other workers' message
						html = '<li class="message othersmess">'+
							'<div class="head_img"><img src="./static/images/head.jpg"alt="worker"></div>' +
							'<span messid="'+each_id+'" title="click to show options">' +
							html + '</span></li>';
					}
				}
				if (messid_in_prev(each_id, prev_parts) == false) {
					new_parts.push(html);
				}
			}
			$("#messages_display ul").html(prev_parts + new_parts.join(""));
			scroll_to_view('left');
			
			// click message to show prompt 
			// for worker, just mark as question and cancel
			// for requester, it has answer and reject
			if (g_worker_id == req_id) {
				click_message_prompt('.pop2');
			} else {
				click_message_prompt('.pop1');
			}
			
            // Record the number of messages
			g_num_seen = data.messages.length;
			
            // Check for new messages (again)
            poll();
		},
		error: function(jq_xhr, text_status, error_thrown) {
            // There was an error.  Report it on the console and then retry in 1000 ms (1 second)
			console.log("ERROR FETCHING UPDATE:", error_thrown);
			setTimeout(poll, 1000);
		}
	});
	
	/* judge whether this messid is in prev string */
	function messid_in_prev(id, prev){
		var span = '<span messid="'+id+'"';  // pattern
		//console.log(prev.indexOf(span) > -1);
		return prev.indexOf(span) > -1 ? true : false;
	}
}

function answer_poll() {
	jQuery.ajax({
		url: url_for("/cast_answer"),
		type: "POST",
		data: {answer_number: g_answer_num},
		success: function(data, text_status, jq_xhr) {
			// for Q/A pairs
			if (1) {  // so far, requester mode and worker_mode are the same
				var answer_parts = [];
				for(var i = 0; i < data.answers.length; i++) {
	                var record = data.answers[i];
					var quest = safe_text(record.quest);
					var ans = safe_text(record.answer);
					var qa_id = 'questid=' + record.quest_id + " ansid="+record.ans_id;
					
	                html = '<li class="qa_pair quest" '+ qa_id +'"><span>Q: </span>' + quest + "</li>" +
	                		'<li class="qa_pair ans" ' + qa_id + '"><span>A: </span>' + ans + "</li>";
	                answer_parts.push(html);
				}
				$("#candidates_container ul").html(answer_parts.join(""));
				$("#message_input").removeClass('answering');
				$("#message_input").attr("placeholder","");
			}
			
			scroll_to_view('right');
			
            /* Record the number of messages */
			g_answer_num = data.answers.length;
			/* Update the number of total answer */
			$('.answered_count').text(g_answer_num);			
            // Check for new messages (again)
			answer_poll();
		},
		error: function(jq_xhr, text_status, error_thrown) {
            // There was an error.  Report it on the console and then retry in 1000 ms (1 second)
			console.log("ERROR FETCHING UPDATE:", error_thrown);
			setTimeout(answer_poll, 1000);
		}
	});
}

//
//function rating_poll() {
//	jQuery.ajax({
//		url: url_for("/cast_rate"),
//		type: "POST",
//		data: {agreed_num: g_agreed_num},
//		success: function(data, text_status, jq_xhr) {
//			var agreed_parts = [];
//			for (var i = 0; i < data.ratings.length; i++) {
//				var this_id = 'pmessid' + data.ratings[i].id;
//				agreed_parts.push(this_id);
//			}
//			$("#candidates_container ul").each(function(){
//				$(this).find('.pending').each(function(){
//					var curr = $(this);
//					curr_id = curr.attr("id");
//					if (agreed_parts.indexOf(curr_id) >= 0) {
//						curr.addClass('agreed');
//					} else {
//						curr.removeClass('agreed');
//					}
//				});
//			});
//            /* Record the number of total agreed */
//			g_agreed_num = data.ratings.length;
//			/* Update the number of agreed pending */
//			$('.answered_count').text(g_agreed_num);
//            /* Check for new ratings (again) */
//			rating_poll();
//		},
//		error: function(jq_xhr, text_status, error_thrown) {
//            /* There was an error.  Report it on the console and then retry in 1000 ms (1 second) */
//			console.log("ERROR FETCHING UPDATE:", error_thrown);
//			setTimeout(rating_poll, 1000);
//		}
//	});
//}

/*
 * Handler for popup mode
 * mark or unmark, reject or undo one message, answer question
 */ 
function popup_mess_handler(obj, condition) {
	var mess_id = obj.attr('messid');  // get messid
	var num = (obj.hasClass(condition)) ? 0 : 1; 
	$.ajax({
		url: url_for(condition),
		type: "POST",
		data: {
			mess_id    : mess_id,
			task_id    : g_task_id,
			num        : num,
			text       : $('#message_input').val(),
		}
	});
}

/*
 * Check for new marking question or rejecting
 */
function marking_poll() {
	jQuery.ajax({
		url: url_for("cast_mark"),
		type: "POST",
		data: {questioned_num: g_questioned_num},
		success: function(data, text_status, jq_xhr) {
			var agreed_parts = [];
			for (var i = 0; i < data.questions.length; i++) {
				var this_id = data.questions[i].id;
				agreed_parts.push(this_id);
			}
			$("#messages_display ul").each(function(){
				$(this).find('.message').each(function(){
					var curr = $(this).find('span').last();
					curr_id = parseInt(curr.attr("messid"));
					if (agreed_parts.indexOf(curr_id) >= 0) {
						curr.addClass('questioned');
						if (curr.prev('.quest_mark').length == 0) {
							curr.before("<span class='quest_mark'>&quest;</span>");
						}
					} else {
						curr.removeClass('questioned');
						if (curr.prev('.quest_mark').length > 0) {
							curr.prev('.quest_mark').remove();
						}
					}
				});
			});
			
            /* Record the number of total questions */
			g_questioned_num = data.questions.length;
			/* Update the number of agreed pending */
			$('.total_count').text(g_questioned_num);
            /* Check for new ratings (again) */
			marking_poll();
		},
		error: function(jq_xhr, text_status, error_thrown) {
            /* There was an error.  Report it on the console and then retry in 1000 ms (1 second) */
			console.log("ERROR FETCHING UPDATE:", error_thrown);
			setTimeout(marking_poll, 1000);
		}
	});
}

/*
 * Check for new marking question or rejecting
 */
function reject_poll() {
	jQuery.ajax({
		url: url_for("cast_reject"),
		type: "POST",
		data: {rejected_num: g_rejected_num},
		success: function(data, text_status, jq_xhr) {
			var parts = [];
			for (var i = 0; i < data.rejected.length; i++) {
				var this_id = data.rejected[i].id;
				parts.push(this_id);
			}
			$("#messages_display ul").each(function(){
				$(this).find('.message').each(function(){
					var curr = $(this).find('span').last();
					curr_id = parseInt(curr.attr("messid"));
					if (parts.indexOf(curr_id) >= 0) {
						curr.addClass('rejected');
					} else {
						curr.removeClass('rejected');
					}
				});
			});
			
            /* Record the number of total rejected */
			g_rejected_num = data.rejected.length;

            /* Check for new ratings (again) */
			reject_poll();
		},
		error: function(jq_xhr, text_status, error_thrown) {
            /* There was an error.  Report it on the console and then retry in 1000 ms (1 second) */
			console.log("ERROR FETCHING UPDATE:", error_thrown);
			setTimeout(reject_poll, 1000);
		}
	});
}



/* 
 * Click message to show prompt 
 * for worker, just has "mark as question" and "cancel"
 * for requester, it has answer and reject and give points
 */
function click_message_prompt(mode) {
	var mess = $(".message span");
	var prev = null;  // to store previous selected item
	var now = null;  // to store the current selected item
	mess.on('click',function(){
		now = list_index($(this));

		if (prev == null) {
			prev = now;
		} 
		if (prev == now) {			
			if ($(this).hasClass('selected')) {
				deselected($(this));
			} else {
				$(this).addClass('selected');
				$(mode).slideFadeToggle();
			}
		}
		else {
			find_span_by_index(prev).removeClass('selected');
			
			$(mode).css('display', 'block');
			prev = now;
		}
		stick_pop(mode, $(this), $('#messages_display'));
	});
	
	$('.close').on('click', function(){
		deselected($("messagepop"));
		$("#message_input").removeClass('answering');
		$("#message_input").attr("placeholder","");
		$(".reward_options").css("display",'none');
		return false;
	});

	/* mark message as question */
	$('.mark_question').on('click',function(){
		// use list index "now" to find the span that is selected
		var obj = find_span_by_index(now);
		// if not rejected and not a requester's message
		if (!obj.hasClass('rejected') && !obj.parent().hasClass("reqmess")) {  
			popup_mess_handler(obj, 'questioned');
			button_set_color(obj, 'questioned', '.mark_question', 1);
		}
	});
	
	/* give reward to one message */
	$(".give_reward").on('click',function(){
		// use list index "now" to find the span that is selected
		var obj = find_span_by_index(now);
		// show the options of reward
		$(".reward_options").css("display","block");
		stick_pop('.reward_options', $(this), $('#messages_display'));
		// reward click handler
		$(".reward_button").on('click',function(){
			var button_id = $(this).attr('id');
			console.log(button_id);
			var messid = obj.attr("messid");
			console.log(messid);
			var reward_point = parseInt(button_id.substr(5));
			reward_point = typeof reward_point == "number" ? reward_point : 10;
			//update_reward(messid, reward_point);
			//update_reputation(messid);
		});
	});
	
	
	/* mark message as rejected */
	$(".reject_mess").on('click', function(){
		// use list index "now" to find the span that is selected
		var obj = find_span_by_index(now);
		popup_mess_handler(obj, 'rejected');
		button_set_color(obj, 'rejected', '.reject_mess', 1);
	});
	
	/* answer question, after that, push question and answer to right panel */
	$('.answer_ques').on('click', function(){
		// use list index "now" to find the span that is selected
		var obj = find_span_by_index(now);
		if (!obj.hasClass('rejected')) {  // if not rejected
			// 0. if it has not been marked as question,
			// mark it as a question
			if (!obj.hasClass("questioned")) {
				popup_mess_handler(obj, 'questioned');
			}
			
			// 1. use the question as the placeholder in the textarea
			// and add class "answering"
			var text = "Answer Here: " + obj.text();
			if (text.length > 40) {  // trancate too long text
				text = text.slice(0, 40) + '...';
			}
			var input = $("#message_input");
			input.attr("placeholder", text);
			input.addClass("answering");
			input.select();
			
			button_set_color(obj, 'answered', '.answer_ques', 1);
			
			// 2. detect submit event
			input.on("keypress", function(evt){
				if (evt.which == 13) {
					evt.preventDefault();
					if (input.val().length > MIN_INPUT && input.hasClass('answering')) {
						// 3. check whether have in the input 
						popup_mess_handler(obj, 'answered');
					}
				}
			});	
		}
	});
	
	function deselected(e) {
		$(mode).slideFadeToggle(function(){
			e.removeClass("selected");
		});
	}
	
	/* return the index number of the clicked message in the ul */
	function list_index(obj) {
		return obj.parent().parent().children().index(obj.parent());
	}
	
	/* the parent is hard coded as #messages_display */
	function find_span_by_index(ind) {
		return $("#messages_display ul li").eq(ind).find("span").last();
	}
	
	// source, target and parent should be jQuery object or string
	function stick_pop(source, target, parent){  
		// change string into jQuery object
		if (typeof source == 'string') source = $(source);
		if (typeof target == 'string') target = $(target);
		if (typeof parent == 'string') parent = $(parent);
		
		var par = parent[0].getBoundingClientRect();
		var tar = target[0].getBoundingClientRect();
		var src = source[0].getBoundingClientRect();
		var wid = source.width();  
		var left = tar.left;
		
		// other scroll handlers are cleared
		parent.unbind("scroll"); // quite nice ^_^
		
		// prevent popup from going out of left/right
		if (left + wid >= par.right) { 
			left = tar.right - wid;
		}
		// set css, absolute position
		source.css({
			position : 'absolute',
			top: Math.min(tar.top - src.height, tar.top - tar.height),
			left: Math.max(left, src.left),
		});
		
		/* Add special color for clicked event */
		button_set_color(target, 'questioned', '.mark_question');
		button_set_color(target, 'rejected', '.reject_mess');
		button_set_color(target, 'answered', '.answer_ques');
		
		// if the chatroom is scrolling, keep the popup moving with message
		// if the message is out of view, clear the popup
		parent.on('scroll', function(e){
			var curr = target[0].getBoundingClientRect();
			var curr_src = source[0].getBoundingClientRect();
			if (par.top <= curr.top && curr.top <= par.bottom) {
				source.css({
					top: curr.top - curr_src.height
				});
			} 
			else {
				source.css('display', 'none');
			}
		});
	}
	
	$.fn.slideFadeToggle = function(easing, callback) {
		return this.animate({opacity: 'toggle', height:"toggle"}, 
				'fast', easing, callback);
	};

}

/* 
 * Change the color of button
 * target is jquery obj
 * condition and button are strings
 */
function button_set_color(target, condition, button, flag) {
	// flag is 0 when it is blank
	flag = typeof flag !==  'undefined' ? flag : 0;  // ^_^
	
	if (flag == 0) {  // set background color if has class
		if (target.hasClass(condition)) {
			$(button).css("background-color","#dcdcdc");
		} else {
			$(button).css("background-color","#fff");
		}
	}
	else if (flag == 1) {  // in opposite way, set if not has class
		if (target.hasClass(condition)) {
			$(button).css("background-color","#fff");
		} else {
			$(button).css("background-color","#dcdcdc");
		}
	}
}


function scroll_to_view(flag) {
	/***
	 * jQuery .scrollTo 
	 * Adapted from http://lions-mark.com/jquery/scrollTo/
	 */
	$.fn.scrollTo = function( target, options, callback ){
		  if(typeof options == 'function' && arguments.length == 2){ callback = options; options = target; }
		  var settings = $.extend({
		    scrollTarget  : target,
		    offsetTop     : 50,
		    duration      : 500,
		    easing        : 'swing'
		  }, options);
		  return this.each(function(){
		    var scrollPane = $(this);
		    var scrollTarget = (typeof settings.scrollTarget == "number") ? settings.scrollTarget : $(settings.scrollTarget);
		    var scrollY = (typeof scrollTarget == "number") ? scrollTarget : scrollTarget.offset().top + 
		    				scrollPane.scrollTop() - parseInt(settings.offsetTop);
		    scrollPane.animate({scrollTop : scrollY }, parseInt(settings.duration), settings.easing, function(){
		      if (typeof callback == 'function') { callback.call(this); }
		    });
		  });
		}
	
	/* Scroll to the bottom list item once there is a new message */
	if ($("#messages_display ul li").length > 0 && flag == 'left') {
		var left_last = $("#messages_display ul li:last");
		$("#messages_display").scrollTo(left_last);
	}
	/* Scroll to the bottom list item once there is a new Q/A pair */
	if ($("#candidates_container ul li").length > 0 && flag == 'right') {
		var right_last = $("#candidates_container ul li:last");
		$("#candidates_container").scrollTo(right_last);
	}
}


/*
 * requester rate_pending_handler
 */ 
//function rate_pending_handler() {
//	if (g_worker_id == req_id) {  /* only requester can rate */
//		$(".pending").on('click', function(){
//			var mess_id = $(this).attr('id').slice(7);
//			var rating = ($(this).hasClass('agreed')) ? 0 : 1;
//			$.ajax({
//				url:"/rate",
//				type: "POST",
//				data: {
//					mess_id    : mess_id,
//					task_id    : g_task_id,
//					rating     : rating,
//				}
//			});
//		});
//	}
//}

/**
 * Module to get all constant ids,
 * not for changable id
 */
function get_all_ids() {
	var ids = {
			worker_id   : get_id_by_name('workerId') || makeid(),
			req_id      : get_id_by_name("reqid"),
			unique_code : get_id_by_name("uniquecode"),
			task_id     : get_id_by_name("task_id"),
	}
	
	function randomChoice(){
		var arr = ['AAA', 'BBB', 'CCC'];
	    return arr[Math.floor(arr.length * Math.random())];
	}
	
	function get_id_by_attr(attr) {
		var obj = $('input[name=hidden_info]');
		return obj.attr(attr);
	}
	
	function get_id_by_name(name) {
		var name = 'input[name='+ name + ']';
		var obj = $(name);
		return obj.val();
	}
	
	function makeid(){
	    var text = "";
	    var possible = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";

	    for( var i=0; i < 5; i++ )
	        text += possible.charAt(Math.floor(Math.random() * possible.length));

	    return text;
	}

	return ids;
}

/*
 * Set all ids using data from ajax
 */
function set_all_ids(key, value){
	function set_id_by_name(name, value){
		var name = 'input[name=' + name + ']';
		var obj = $(name);
		// obj.val() will never be false
		return obj.length > 0 ? obj.val(value) : false;
	}
	
	function set_id_by_class(classname, value){
		var obj = $(classname);
		return obj.length > 0 ? obj.val(value) : false;
	}
	
	function set_id_by_id(id, value){
		var obj = $(id);
		return obj.length > 0 ? obj.val(value) : false;
	}
	
	// return false if not exists, return jQuery object if success
	// jQuery object won't equal to false
	return set_id_by_name(key, value);
}

function url_for(url) {
	return url.indexOf('/') == 0 ? (g_url_prefix + url) : (g_url_prefix + '/' + url);
}

function safe_text(text) {
	return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;");
}

/*******************************************************************************
 * Common dialog to prompt error
 */
function open_error_dialog() {
	$("#dialog_confirm").html('Your input is too short.');

	// Define the Dialog and its properties.
	$("#dialog_confirm").dialog({
		resizable : false,
		modal : true,
		title : "Tips",
		height : 200,
		width : 400,
		buttons : {
			"OK" : function() {
				$(this).dialog('close');
			}
		}
	});
}
//update current reward point
function update_reward(messid, point) {
	jQuery.ajax({
		url: url_for("/new_reward"),
		data: { mess_id: messid,
				reward_point: point,
				task_id: g_task_id
    	},
		type: "POST",
		success: function(data, text_status, jq_xhr) {
			$("reward_point").val(data.reward_point); //update the banner  
		},
		error: function(jq_xhr, text_status, error_thrown) {
			console.log("ERROR SENDING REWARD POINTS:", error_thrown);
		}
	});
}

function reward_poll(){
	jQuery.ajax({
		url: url_for("/update_reward"),
		type: "POST",
		data: { task_id: g_task_id,
				worker_id: g_worker_id,
				total_reward: g_total_reward
    	},
		success: function(data, text_status, jq_xhr) {

			g_total_reward = data.results.total_reward;
			
			if (data.results.worker_id == g_worker_id) {
				$("#reward_point").text(g_total_reward); //update the banner 
			}
			
            // Check for new reward updates (again)
			reward_poll();
		},
		error: function(jq_xhr, text_status, error_thrown) {
            // There was an error.  Report it on the console and then retry in 1000 ms (1 second)
			console.log("ERROR FETCHING REWARD UPDATE:", error_thrown);
			setTimeout(reward_poll, 1000);
		}
	});
}


/*******************************
 * For waiting room
 */
function count_user_handler(){
	
	// update user number from server using AJAX
	$.ajax({
		url:url_for("/update_user"),
		type:"POST",
		//Get worker ID from javascript and send it to server
		data: {ids: g_worker_id, num_seen: g_id_seen},
		//Ajax success, get data from server, this data contains existing ids so far.
		success:function(data){
			// document.getElementById("user_number_display").innerHTML = data.user_number;
			var html_parts = [];
			var id = data.data.g_ids;
			for(var i =0; i < id.length; i++){
				img = '<img src="/static/images/head.jpg" >';
                html = '<div class="user">' + img + '  ' + id[i] + '</div>';
				html_parts.push(html);
			}
			document.getElementById("user_number_display").innerHTML = html_parts.join("");
			//record the number of workers
			g_id_seen = id.length;
			console.log(g_id_seen, id.length);
			console.log(g_worker_id);
			//check for new users 
			count_user_handler();	
		},
		
	});
}

function add_new_ids(){
	
	$.ajax({
		url:url_for("/new_user"),
		type:"POST",
		data: {ids: g_worker_id},
		success:function(){
			setTimeout(add_new_ids,5000);
			},
	});
}

$("#").click(function(){
	var task_id = 
	var worker_id = g_worker_id; 
	var currentdate = new Date();
	var in_room = 1;
	var enter_time = "Enter time:" + currentdate.getDate() + "/"
					+ (currentdate.getMonth()+1) + "/"
					+currentdate.getFullYear() + "@"
					+currentdate.getHours() + ":"
					+currentdate.getMinutes() + ":"
					+currentdate.getSeconds();
	
	document.getElementById("waiting_room").style.display = "none";
	document.getElementById("chatroom_containter").style.display = "block";
	$.ajax({
		url:"/switch",
		type:"POST",
		data: {task_id:task_id, worker_id:worker_id,enter_time:enter_time },
		success: on_success_switch_chatroom
		
		
	});
	
})


function on_success_switch_chatroom(data){
	// data = results
	set_all_ids(data);
}



})(jQuery);
