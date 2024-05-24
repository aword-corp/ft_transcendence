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
