reputation = function(worker_id) {
	this.worker_id = worker_id;
	this.mess_id = -1; //message id
	this.score = 0; //current reputation score i.e. record
	this.datetime = new Date(); //edit datetime	
}

reputation.prototype = {
	set_worker_id: function(c_worker_id) {
		this.worker_id = c_worker_id;
	},

	get_worker_id: function() {
		return this.worker_id;
	},

	set_mess_id: function(c_mess_id) {
		this.mess_id = c_mess_id;
	},
	
	get_mess_id: function() {
		return this.mess_id;
	},

	inc_score: function() {
		this.score += 1;
	},
	
	dec_score: function() {
		this.score -= 1;
	},

	set_score: function(c_score) {
		this.score = c_score;
	},

	get_score: function() {
		return this.score;
	},

	set_datetime: function(c_datetime) {
		this.datetime = c_datetime;
	},

	get_datetime: function() {
		return this.datetime;
	},
}