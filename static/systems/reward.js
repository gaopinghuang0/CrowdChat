var MAX_WAITING_POINT

reward = function(worker_id) {
	this.worker_id = worker_id;
	this.point = 0; //current reward point i.e. record
	// this.datetime = new Date(); //edit datetime
	// this.mess_id = -1; //message id
	this.waiting_point = 0; //waiting point
}

reward.prototype = {
	set_worker_id: function(c_worker_id) {
		this.worker_id = c_worker_id;
	},

	get_worker_id: function() {
		return this.worker_id;
	},

	inc_point: function() {
		this.point += 1;
	},
	
	inc_point_by_reward: function(c_reward_level) {
		switch(c_reward_level) {
			case 0: this.point += 10; //good
			case 1: this.point += 30; //great
			case 2: this.point += 50; //splendid
		}
	},

	inc_point_redemption: function() { //in case of waiting point redemption
		this.point += this.waiting_point;
		this.waiting_point = 0; //reset waiting point
	},

	dec_point: function() {
		this.point -= 1;
	},

	set_point: function(c_point) {
		this.point = c_point;
	},

	get_point: function() {
		return this.point;
	},

	set_datetime: function(c_datetime) {
		this.datetime = c_datetime;
	},

	get_datetime: function() {
		return this.datetime;
	},

	set_mess_id: function(c_mess_id) {
		this.mess_id = c_mess_id;
	},

	get_mess_id: function() {
		return this.mess_id;
	},

	inc_waiting_point: function() {
		if(this.waiting_point < MAX_WAITING_POINT) this.waiting_point += 1;
	},

	get_waiting_point: function() {
		return this.waiting_point;
	},

	get_monetary_val: function() {
		return parseFloat(this.point / 10);
	},
}