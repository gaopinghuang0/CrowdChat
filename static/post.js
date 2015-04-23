(function(){

$(document).ready(function(){


var assignment_id = (location.search.match(/assignmentId=(\w+)/)||[])[1];
var test_action = "";
var action = (location.search.match(/turkSubmitTo=([^=&]+)/)||[])[1]+"/mturk/externalSubmit";
alert("asdf");
alert (assignment_id);
if(assignment_id == "ASSIGNMENT_ID_NOT_AVAILABLE"){
	document.getElementById("submit").disabled = true;
	document.getElementById("click_accept_warning").style.display = "block";
	$(".enter_chat").prop("disabled",true);
	}
else if ( assignment_id == "undefined" || assignment_id == ""){
	document.getElementById("myfrom").method = "post";
	document.getElementById("myform").action = test_action;
	document.getElementsByClassName("enter_chat").disabled = true;
	}
else{
	document.getElementById("myform").method = "post";
	document.getElementById("myform").action = action;

	}	

})

})();
