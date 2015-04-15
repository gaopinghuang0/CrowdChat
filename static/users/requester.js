requester = function(ID) {
	this.ID = ID; //primary integer key; assumed immutable
	this.requester_id = ID % 1 == 0 ? ID.toString() : ID; //text
}

requester.prototype = {
	set_requester_id: function(c_requester_id) {
		this.requester_id = c_requester_id;
	},

	get_requester_id: function() {
		return this.requester_id;
	},
}