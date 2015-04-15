var MAX_OCCUPANCY = 500;
var MAX_TASK_CAPACITY = 100;

waiting_room = function(wrid) {
	this.wrid = wrid; //waiting room ID
	this.occupancy = MAX_OCCUPANCY; //default room occupancy is max occupancy
	this.task_cap = MAX_TASK_CAPACITY; //default task capacity is max task capacity 
	this.occupants = new Set(); //a list of occupants
	this.chat_rooms = new Set(); //a list of existing chat rooms; each chat room corresponds to a task
}

waiting_room.prototype = {
	get_wrid: function() {
		return this.wrid;
	},
	
	set_occupancy: function(c_occupancy) {
		this.occupancy = c_occupancy;
	},
	
	get_occupancy: function() {
		return this.occupancy;
	},
	
	set_task_cap: function(c_task_cap) {
		this.task_cap = c_task_cap;
	},
	
	get_task_cap: function() {
		return this.task_cap;
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
	
	add_chat_room: function(c_cr) {
		if(this.chat_rooms.length == this.task_cap) {
			alert("ERROR: The room has reached its maximum task capacity!"); 
			return;
		}

		this.chat_rooms.add(c_cr);
	},
	
	delete_chat_room: function(c_crid) {
		if(!this.chat_rooms.has(c_crid)) {
			alert("ERROR: The room does not have the task!"); 
			return;
		}

		this.chat_rooms.delete(c_crid);
	},
	
	get_chat_rooms: function() {
		return this.chat_rooms;
	},
	
	clear_chat_rooms: function() {
		this.chat_rooms = new Set();
	},
}