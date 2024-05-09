var count = 0;
const countSocket = new WebSocket('ws://' + window.location.host + '/ws/pong/');

countSocket.onmessage = function(e) {
	const data = JSON.parse(e.data);
    const message = data['message'];
	document.getElementById('count').innerText = message.count;
};

countSocket.onclose = function(e) {
	console.error('Chat socket closed unexpectedly');
};

function onClickMe() {
	countSocket.send(JSON.stringify({
		'message': 1
	}));
}