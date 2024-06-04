var countSocket = undefined;

export function onSocketClick() {
	countSocket.send("");
}

export function initSocketClick() {
	if (countSocket)
		return;
	countSocket = new WebSocket((location.protocol === 'https:' ? 'wss://' : 'ws://') + window.location.host + '/ws/click/');
	countSocket.onmessage = function (e) {
		document.getElementById('count').innerText = e.data;
	};
	return onSocketClick;
}

export function closeSocketClick() {
	if (countSocket && (countSocket.readyState === WebSocket.OPEN || countSocket.readyState === WebSocket.CONNECTING))
		countSocket.close();
	countSocket = undefined;
}

export var mmSocket = undefined;

export function initMMSocket() {
	if (mmSocket)
		return;
	mmSocket = new WebSocket((location.protocol === 'https:' ? 'wss://' : 'ws://') + window.location.host + '/ws/pong/matchmaking');
	mmSocket.onmessage = function (e) {
		// document.getElementById('count').innerText = e.data;
		// console.log(e.data);
	};
}

export function closeMMSocket() {
	if (mmSocket && (mmSocket.readyState === WebSocket.OPEN || mmSocket.readyState === WebSocket.CONNECTING))
		mmSocket.close();
	mmSocket = undefined;
}


export var pongSocket = undefined;

export function initPongSocket(uuid) {
	if (pongSocket)
		return;
	pongSocket = new WebSocket((location.protocol === 'https:' ? 'wss://' : 'ws://') + window.location.host + '/ws/pong/game/' + uuid);
	pongSocket.onmessage = function (e) {
		let data = JSON.parse(e.data);
		console.log(data);
	};
}

export function closePongSocket() {
	if (pongSocket && (pongSocket.readyState === WebSocket.OPEN || pongSocket.readyState === WebSocket.CONNECTING))
		pongSocket.close();
	pongSocket = undefined;
}