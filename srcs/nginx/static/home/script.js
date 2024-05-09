const countSocket = new WebSocket((location.protocol === 'https:' ? 'wss://' : 'ws://') + window.location.host + '/ws/pong/');

countSocket.onmessage = function(e) {
	const data = JSON.parse(e.data);
    const message = data['message'];
	document.getElementById('count').innerText = message.count;
};

function onClickMe() {
	countSocket.send(JSON.stringify({
		'message': 'clicked'
	}));
}