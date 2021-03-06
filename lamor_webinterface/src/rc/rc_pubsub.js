RC.PubSub = new (function() {
	var that = this;

	var ros;

	var picture_ready_listener;

	var dialog_feedback_publisher;

	var picture_ready_callback = function (msg) {
		// display picture
		disp = document.getElementById('imgdisplay');
		disp.setAttribute('src', msg.data);
		yes_button = document.getElementById('yes_button');
		no_button = document.getElementById('no_button');
		yes_button.style.display = 'inline';
		no_button.style.display = 'inline';
	}
	


	this.initialize = function(_ros) {
		ros = _ros;


		// Subscriber

		picture_ready_listener = new ROSLIB.Topic({ 
			ros : ros,
			name : '/webinterface/display_picture',
			messageType : 'std_msgs/String'
		});
		picture_ready_listener.subscribe(picture_ready_callback);


		// Publisher

		dialog_feedback_publisher = new ROSLIB.Topic({ 
			ros: ros,
			name: '/webinterface/dialog_feedback',
			messageType: 'std_msgs/String'
		});

	}

	

	this.shutdown = function() {
		picture_ready_listener.unsubscribe();

		dialog_feedback_publisher.unadvertise();

		ros = undefined;
	}

	this.sendDialogYes = function() {
		dialog_feedback_publisher.publish({data: 'yes'});
		yes_button.style.display = 'none';
		no_button.style.display = 'none';
		disp.setAttribute('src', '');
	}

	this.sendDialogNo = function() {
		dialog_feedback_publisher.publish({data: 'no'});
		yes_button.style.display = 'none';
		no_button.style.display = 'none';
		disp.setAttribute('src', '');
	}

}) ();