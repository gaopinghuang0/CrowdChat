/* (c) Copyright 2015 Purdue University - MIT License */
(function(){
	/* Some global variables */
	var g_num_seen = 0; 
	var g_pending_num = 0;
	var g_agreed_num = 0;  
	var g_worker_id;
	var req_id;
	var g_task_id;
	var unique_code;

jQuery(document).ready(function() {
    $("#message_input").on("keypress", handle_new_message_event);
	$("#messages_display").perfectScrollbar();
	$("#candidates_container").perfectScrollbar();
	$("#message_input").select();
	g_worker_id = get_all_ids().worker_id;
	req_id = get_all_ids().req_id;
	g_task_id = get_all_ids().task_id;
	unique_code = get_all_ids().unique_code;
	if (req_id == g_worker_id) {
		$("#roommode").text('(requester)');
	} else {
		var worknum = g_worker_id == 'BBB' ? 1:2;
		$("#roommode").text('(worker'+worknum+')');
	}
	
	// 1. click on the message to show mark (question and cancel)
	
	// Opt1. automatically mark the input with ? as question
	
	// 2. click on the question button, change its color
	
	// 3. click on the answer button, it is related to this question
	
	// 4. after answer it, push the Q/A pair to the right
	
	// 5. for requester, it has some buttons to answer it and reject it
	
	// 6. for requester, he/she can only answer the meaningful question, and approve it atomitically
	
	
    poll();  // Check for new messages
    pending_poll(); // Check for new pending messages
    rating_poll();  // Check for new ratings
});

function handle_new_message_event(evt) {
    if(evt.which == 13) {  // only respond to enter key
        // Tell browser (via jQuery) not to try to submit the form the normal way
        evt.preventDefault();

        // Prevent user from typing more messages until last one is processed
        var message_input = document.getElementById("message_input");
        message_input.disabled = true;   // Disable text box

        // Send new message to the server using AJAX
        if ($("#message_input").val().length > 0) {
            jQuery.ajax({
                url: "/new",
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
        	// empty enter
        }
    }
}

function poll() {
	jQuery.ajax({
		url: "/update",
		type: "POST",
		data: {num_seen: g_num_seen},
		success: function(data, text_status, jq_xhr) {
            // Display the messages in the DIV with id="messages_display"
			var html_parts = [];
			for(var i = 0; i < data.messages.length; i++) {
                var message = data.messages[i];
				var html = message.text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;");
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
					else {
						html = '<li class="message othersmess">'+
							'<div class="head_img"><img src="./static/images/head.jpg"alt="worker"></div>' +
							'<span messid="'+each_id+'">' + html + '</span></li>';
					}
				}
				html_parts.push(html);
			}
			$("#messages_display ul").html(html_parts.join(""));
			scroll_to_view('left');
			
			// click message to show prompt 
			// for worker, just mark as question and cancel
			// for requester, it has answer and reject
			click_message_prompt('.pop1');
			
			push_to_pending_handler();
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
}

function pending_poll() {
	jQuery.ajax({
		url: "/pending",
		type: "POST",
		data: {pending_number: g_pending_num},
		success: function(data, text_status, jq_xhr) {
			// for Pending
			if (g_worker_id == req_id) {  // requester mode
				var pending_parts = [];
				for(var i = 0; i < data.pendings.length; i++) {
	                var text2 = data.pendings[i];
					var html2 = text2.text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;");
					var pmess_id = 'pmessid' + text2.id; /* pending message id */

	                html2 = '<li class="pending" id="'+ pmess_id +'">' + html2 + 
	                		"<span class='prompt_content'><span class='prompt'>(Click to agree/disagree)" +
	                		"</span></span></li>";
	                pending_parts.push(html2);
				}
				$("#candidates_container ul").html(pending_parts.join(""));
			}
			else {  // worker mode
				var pending_parts = [];
				for(var i = 0; i < data.pendings.length; i++) {
	                var text2 = data.pendings[i];
					var html2 = text2.text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;");
					var pmess_id = 'pmessid' + text2.id; /* pending message id */

	                html2 = '<li class="pending" style="cursor:auto;" id="'+ pmess_id +'">' + html2 
	                		+'</li>';
	                pending_parts.push(html2);
				}
				$("#candidates_container ul").html(pending_parts.join(""));
			}
			scroll_to_view('right');
			
			/* requester rate_pending_handler */
			rate_pending_handler();
			
            /* Record the number of messages */
			g_pending_num = data.pendings.length;
			/* Update the number of total pending */
			$('.total_count').text(g_pending_num);			
            // Check for new messages (again)
			pending_poll();
		},
		error: function(jq_xhr, text_status, error_thrown) {
            // There was an error.  Report it on the console and then retry in 1000 ms (1 second)
			console.log("ERROR FETCHING UPDATE:", error_thrown);
			setTimeout(pending_poll, 1000);
		}
	});
}


function rating_poll() {
	jQuery.ajax({
		url: "/cast_rate",
		type: "POST",
		data: {agreed_num: g_agreed_num},
		success: function(data, text_status, jq_xhr) {
			var agreed_parts = [];
			for (var i = 0; i < data.ratings.length; i++) {
				var this_id = 'pmessid' + data.ratings[i].id;
				agreed_parts.push(this_id);
			}
			$("#candidates_container ul").each(function(){
				$(this).find('.pending').each(function(){
					var curr = $(this);
					curr_id = curr.attr("id");
					if (agreed_parts.indexOf(curr_id) >= 0) {
						curr.addClass('agreed');
					} else {
						curr.removeClass('agreed');
					}
				});
			});
            /* Record the number of total agreed */
			g_agreed_num = data.ratings.length;
			/* Update the number of agreed pending */
			$('.agreed_count').text(g_agreed_num);
            /* Check for new ratings (again) */
			rating_poll();
		},
		error: function(jq_xhr, text_status, error_thrown) {
            /* There was an error.  Report it on the console and then retry in 1000 ms (1 second) */
			console.log("ERROR FETCHING UPDATE:", error_thrown);
			setTimeout(rating_poll, 1000);
		}
	});
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
	
	/* Scroll to the bottom list item once there is new message */
	if ($("#messages_display ul li").length > 0 && flag == 'left') {
		var left_last = $("#messages_display ul li:last");
		$("#messages_display").scrollTo(left_last);
	}
	if ($("#candidates_container ul li").length > 0 && flag == 'right') {
		var right_last = $("#candidates_container ul li:last");
		$("#candidates_container").scrollTo(right_last);
	}
}

/*
 * Click on the message (<span>), get the message_id and
 * send to the server
 */
function push_to_pending_handler() {
	
	/* need to modify */
	
//	$("#messages_display ul li span").click(function(){
//		var pending_message = $(this).html();
//		var this_id = parseInt($(this).attr("messid"));
//		$.ajax({
//			url:"/append",
//			data:{
//				worker_id       : g_worker_id,
//				mess_id         : this_id,
//				task_id         : g_task_id,
//				},
//			type: "POST"
//		});
//	});
}


/* 
 * Click message to show prompt 
 * for worker, just mark as question and cancel
 * for requester, it has answer and reject
 */
function click_message_prompt(mode) {
	var mess = $(".message span");
	var prev = null;  // to store previous selected item
	mess.on('click',function(){
		var now = list_index($(this));
		
		if (prev == null) {
			prev = now;
		} 
		if (prev == now) {
			var pos = $(this)[0].getBoundingClientRect();

			pop_here(pos);  // change pop's position
			
			if ($(this).hasClass('selected')) {
				deselected($(this));
			} else {
				$(this).addClass('selected');
				$(mode).slideFadeToggle();
			}
			//return false;
		}
		else {
			$("#messages_display ul li").eq(prev).find("span").removeClass('selected');
			var pos = $(this)[0].getBoundingClientRect();
			pop_here(pos);  // change pop's position
			$(mode).css('display', 'block');
			prev = now;
		}
	});
	
	$('.close').on('click', function(){
		deselected($("messagepop"));
		return false;
	});

	$('.mark_question').on('click',function(){
		
	});
	function deselected(e) {
		$(mode).slideFadeToggle(function(){
			e.removeClass("selected");
		});
	}
	
	function list_index(obj) {
		return obj.parent().parent().children().index(obj.parent());
	}
	
	function pop_here(pos){
		var chat = $('.left')[0].getBoundingClientRect();
		var popup = $(mode).width();  
		var left = pos.left;
		if (pos.left + popup >= chat.right) {
			left = pos.right - popup;
		}
		$(mode).css({
			position : 'absolute',
			top: pos.top - pos.height,
			left: left,
		});
	}
	
	$.fn.slideFadeToggle = function(easing, callback) {
		return this.animate({opacity: 'toggle', height:"toggle"}, 
				'fast', easing, callback);
	};

}



/*
 * requester rate_pending_handler
 */ 
function rate_pending_handler() {
	if (g_worker_id == req_id) {  /* only requester can rate */
		$(".pending").on('click', function(){
			var mess_id = $(this).attr('id').slice(7);
			var rating = ($(this).hasClass('agreed')) ? 0 : 1;
			$.ajax({
				url:"/rate",
				type: "POST",
				data: {
					mess_id    : mess_id,
					task_id    : g_task_id,
					rating     : rating,
				}
			});
		});
	}
}

/**
 * Module to get all useful ids
 */
function get_all_ids() {
	var setting = $("#some_setting");
	var worker_array = ['AAA', 'BBB', 'CCC'];
	var ids = {
			worker_id   : randomChoice(worker_array),
			hit_id      : makeid(),
			req_id      : setting.attr("reqid"),
			task_id     : setting.attr("taskid"),
			unique_code : setting.attr("uniquecode")
	}
	
	function randomChoice(arr){
	    return arr[Math.floor(arr.length * Math.random())];
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

})(jQuery);
