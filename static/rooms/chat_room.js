var MAX_OCCUPANCY = 5;

chat_room = function(crid) {
	this.crid = crid; //chat room ID
	this.occupancy = MAX_OCCUPANCY; //default room occupancy is max occupancy
	this.instruction = ""; //task instruction (in string)
	this.occupants = new Set(); //a list of occupants
	this.mess_list = new Set(); //a list of messages
	this.qa_pairs = []; //a list of question-answer pairs
}

chat_room.prototype = {
	get_crid: function() {
		return this.crid;
	},

	set_occupancy: function(c_occupancy) {
		this.occupancy = c_occupancy;
	},

	get_occupancy: function() {
		return this.occupancy;
	},
	
	set_instruction: function(c_instruction) {
		this.instruction = c_instruction;
	},

	get_instruction: function() {
		return this.instruction;
	},

	add_occupant: function(c_occupant) {
		if(this.occupants.length == this.occupancy) {
			alert("ERROR: The room has maximum number of occupants!"); 
			return;
		}

		this.occupants.add(c_occupant);
	},

	delete_occupant: function(c_uid) {
		if(!this.occupants.has(c_uid)) {
			alert("ERROR: The user is not in the room!"); 
			return;
		}

		this.occupants.delete(c_uid);
	},

	get_occupants: function() {
		return this.occupants;
	},

	clear_occupants: function() {
		this.occupants = new Set();
	},

	add_message: function(c_mess) {
		this.mess_list.add(c_mess);
	},

	delete_message: function(c_mess) {
		if(!this.mess_list.has(c_mess)) {
			alert("ERROR: The message cannot be found!"); 
			return;
		}

		this.mess_list.delete(c_mess);
	},

	get_messages: function() {
		return this.mess_list;
	},

	clear_messages: function() {
		this.mess_list = new Set();
	},

	add_qa_pair: function(c_q, c_a) {
		this.qa_pairs[c_q] = c_a;
	},

	delete_qa_pair: function(c_q) { //delete a question-answer pair by question
		if(this.qa_pairs[c_q] == "") {
			alert("ERROR: The question/answer pair cannot be found!"); 
			return;
		}

		delete this.qa_pairs[c_q];
	},

	get_qa_pairs: function() {
		return this.qa_pairs;
	},

	clear_qa_pairs: function() {
		this.qa_pairs = new Set();
	},
}