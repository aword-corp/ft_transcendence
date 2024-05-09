const countSocket = new WebSocket((location.protocol === 'https:' ? 'wss://' : 'ws://') + window.location.host + '/ws/pong/');

countSocket.onmessage = function (e) {
	const data = JSON.parse(e.data);
	const message = data['message'];
	document.getElementById('count').innerText = message.count;
};

function onClickMe() {
	countSocket.send(JSON.stringify({
		'message': 'clicked'
	}));
}

const chatSocket = new WebSocket((location.protocol === 'https:' ? 'wss://' : 'ws://') + window.location.host + '/ws/chat/');

chatSocket.onmessage = function (e) {
	const data = JSON.parse(e.data);
	let div = document.createElement("div");
	div.innerHTML = data.message;
	document.getElementById('chat-log').append(div);
};

function onKeyUp(event) {
	if (event.key === 'Enter') {  // enter, return
		document.getElementById('chat-message-submit').click();
	}
};

function onClick(event) {
	const messageInputDom = document.getElementById('chat-message-input');
	const message = messageInputDom.value;
	chatSocket.send(JSON.stringify({
		'message': message
	}));
	messageInputDom.value = '';
};
