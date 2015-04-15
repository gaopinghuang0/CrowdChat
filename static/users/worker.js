worker = function(worker_id) {
	this.worker_id = worker_id; //text
	this.status = 1; //0 - blocked; 1 - normal
	this.reward = new reward(worker_id);
	this.reputation = new reputation(worker_id);
}

worker.prototype = {
	set_worker_id: function(c_worker_id) {
		this.worker_id = c_worker_id;
	},

	get_worker_id: function() {
		return this.worker_id;
	},

	set_status: function(c_status) {
		this.status = c_status;
	},

	get_status: function() {
		return this.status;
	}
}