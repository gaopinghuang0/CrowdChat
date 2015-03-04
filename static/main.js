/* (c) Copyright 2015 Purdue University - MIT License */

var g_num_seen = 0;  // global variable:  number of messages seen so far
var g_pending_num = 0;
var worker_id;
var req_id;
var task_id;
var unique_code;

jQuery(document).ready(function() {
    $("#message_input").on("keypress", handle_new_message_event);
	$("#messages_display").perfectScrollbar();
	$("#candidates_container").perfectScrollbar();
	$("#message_input").select();
	worker_id = get_all_ids().worker_id;
	req_id = get_all_ids().req_id;
	task_id = get_all_ids().task_id;
	unique_code = get_all_ids().unique_code;
	console.log(req_id, worker_id);
	if (req_id == worker_id) {
		$("#roommode").text('(requester)');
	} else {
		var worknum = worker_id == 'BBB' ? 1:2;
		$("#roommode").text('(worker'+worknum+')');
	}
    poll();  // Check for new messages
    pending_poll(); // Check for new pending
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
                		worker_id : worker_id,
                		task_id   : task_id },
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
				if (each_worker_id == worker_id) {  // it's me
					html = '<li class="message mymess"><span>' + html + '</span>'+
					'<div class="head_img"><img src="./static/images/head.jpg" alt="worker"></div></li>';
				}
				else {  // others' message
					if (each_worker_id == req_id)  {  // requster's mess
						html = '<li class="message othersmess reqmess"><span>Requester: ' +
						       html + '</span></li>';
					}
					else {
						html = '<li class="message othersmess">'+
							'<div class="head_img"><img src="./static/images/head.jpg"alt="worker"></div>' +
							'<span>' + html + '</span></li>';
					}
				}
				html_parts.push(html);
			}
			$("#messages_display ul").html(html_parts.join(""));
			scroll_to_view('left');
			click_to_pending();
            // Record the number of messages
			g_num_seen = data.messages.length;
			
            // Check for new messages (again)
            poll();
		},
		error: function(jq_xhr, text_status, error_thrown) {
            // There was an error.  Report it on the console and then retry in 1000 ms (1 second)
			console.log("ERROR FETCHING UPDATE:", error_thrown);
			window.setTimeout(poll, 1000);
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
			if ($(".requester").length > 0) {  // requester mode
				var pending_parts = [];
				for(var i = 0; i < data.pendings.length; i++) {
	                var text2 = data.pendings[i];
					var html2 = text2.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;");
	                html2 = '<li class="pending">' + html2 + 
	                		"<span class='prompt'>(Click to agree/disagree)</span>"
	                		+'</li>';
	                pending_parts.push(html2);
				}
				$("#candidates_container ul").html(pending_parts.join(""));
			}
			else {  // worker mode
				
			}
			scroll_to_view('right');
            // Record the number of messages
			g_pending_num = data.pendings.length;
			
			$(".pending").on('click', function(){
				$(this).toggleClass("agreed");
			});
			
            // Check for new messages (again)
			pending_poll();
		},
		error: function(jq_xhr, text_status, error_thrown) {
            // There was an error.  Report it on the console and then retry in 1000 ms (1 second)
			console.log("ERROR FETCHING UPDATE:", error_thrown);
			window.setTimeout(poll, 1000);
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
		    var scrollY = (typeof scrollTarget == "number") ? scrollTarget : scrollTarget.offset().top + scrollPane.scrollTop() - parseInt(settings.offsetTop);
		    scrollPane.animate({scrollTop : scrollY }, parseInt(settings.duration), settings.easing, function(){
		      if (typeof callback == 'function') { callback.call(this); }
		    });
		  });
		}
	
	if ($("#messages_display ul li").length > 0 && flag == 'left') {
		var left_last = $("#messages_display ul li:last");
		$("#messages_display").scrollTo(left_last);
	}
	if ($("#candidates_container ul li").length > 0 && flag == 'right') {
		var right_last = $("#candidates_container ul li:last");
		$("#candidates_container").scrollTo(right_last);
	}
}

function click_to_pending() {
	$("#messages_display ul li span").click(function(){
		var pending_message = $(this).html();
		$.ajax({
			url:"/append",
			data:{pending_message:pending_message,
				worker_id:worker_id,
				pending_num:g_pending_num},
			type: "POST"
		});
	});
}


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


