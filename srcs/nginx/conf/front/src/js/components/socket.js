export var countSocket = undefined;

export function initSocketClick() {
	if (countSocket)
		return;
	countSocket = new WebSocket((location.protocol === 'https:' ? 'wss://' : 'ws://') + window.location.host + '/ws/click/');
}

export function closeSocketClick() {
	if (countSocket && countSocket.readyState === WebSocket.OPEN)
		countSocket.close();
	countSocket = undefined;
}

export var updateSocket = undefined;

export function initSocketUpdate() {
	if (updateSocket)
		return;
	updateSocket = new WebSocket((location.protocol === 'https:' ? 'wss://' : 'ws://') + window.location.host + '/api/ws/update/');
}

export function closeSocketUpdate() {
	if (updateSocket && updateSocket.readyState === WebSocket.OPEN)
		updateSocket.close();
	updateSocket = undefined;
}

export function defaultSocketUpdateOnMessage(e) {
	var data = JSON.parse(e.data);
	if (data) {
		console.log(data);
	}
}

export var mmSocket = undefined;

export function initMMSocket() {
	if (mmSocket)
		return;
	mmSocket = new WebSocket((location.protocol === 'https:' ? 'wss://' : 'ws://') + window.location.host + '/ws/pong/matchmaking');
}

export function closeMMSocket() {
	if (mmSocket && mmSocket.readyState === WebSocket.OPEN)
		mmSocket.close();
	mmSocket = undefined;
}


export var tmSocket = undefined;

export function initTMSocket() {
	if (tmSocket)
		return;
	tmSocket = new WebSocket((location.protocol === 'https:' ? 'wss://' : 'ws://') + window.location.host + '/ws/pong/tournament');
}

export function closeTMSocket() {
	if (tmSocket && tmSocket.readyState === WebSocket.OPEN)
		tmSocket.close();
	tmSocket = undefined;
}

export var pongSocket = undefined;

export function initPongSocket(params) {
	if (pongSocket)
		return;
	pongSocket = new WebSocket((location.protocol === 'https:' ? 'wss://' : 'ws://') + window.location.host + '/ws/pong/game/' + params.uuid);
}

export function closePongSocket() {
	if (pongSocket && pongSocket.readyState === WebSocket.OPEN)
		pongSocket.close();
	pongSocket = undefined;
}