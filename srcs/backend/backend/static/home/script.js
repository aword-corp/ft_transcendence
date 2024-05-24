const countSocket = new WebSocket((location.protocol === 'https:' ? 'wss://' : 'ws://') + window.location.host + '/ws/click/');

countSocket.onmessage = function (e) {
	document.getElementById('count').innerText = e.data;
};

function onClickMe() {
	countSocket.send("");
}

const chatSocket = new WebSocket((location.protocol === 'https:' ? 'wss://' : 'ws://') + window.location.host + '/ws/chat/');

chatSocket.onmessage = function (e) {
	const data = JSON.parse(e.data);
	if (!data || !data.message || data.error) {
		console.log("Error: " + (data ? (data.error ? data.error : "No message") : "No data"));
		return;
	}
	let div = document.createElement("div");
	div.innerText = data.message;
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
