import { router } from '../main.js';

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

export var localStream = undefined;

export var peerConnection = undefined;

export var interval = undefined;

async function makeCall() {
	const configuration = {
		'iceServers': [{
			'urls': 'turn:dev.acorp.games:3478',
			username: 'anon',
			credential: 'anon-pass'
		}], iceTransportPolicy: 'relay', 'sdpSemantics': 'unified-plan',
	};
	peerConnection = new RTCPeerConnection(configuration);
	if (localStream) {
		localStream.getTracks().forEach(track => {
			peerConnection.addTrack(track, localStream);
		});
	}
	pongSocket.addEventListener('message', async event => {
		const message = JSON.parse(event.data);
		if (message.answer) {
			const remoteDesc = new RTCSessionDescription(message.answer);
			await peerConnection.setRemoteDescription(remoteDesc).catch(e => console.error("Failed to set remote description: ", e));
		}
		if (message.iceCandidate) {
			try {
				await peerConnection.addIceCandidate(message.iceCandidate);
			} catch (e) {
				console.error('Error adding received ice candidate', e);
			}
		}
	});
	const offer = await peerConnection.createOffer({
		'offerToReceiveAudio': true,
		'offerToReceiveVideo': false
	});
	await peerConnection.setLocalDescription(offer);
	peerConnection.addEventListener('icecandidate', event => {
		if (event.candidate) {
			if (event.candidate.candidate.indexOf("relay") < 0) {
				return;
			}
			pongSocket.send(JSON.stringify({ 'iceCandidate': event.candidate }));
		}
	});
	peerConnection.addEventListener('connectionstatechange', event => {
		if (peerConnection.connectionState === 'connected' && interval) {
			clearInterval(interval);
			interval = undefined;
		} else if (peerConnection.connectionState === 'failed') {
			peerConnection.createOffer({ iceRestart: true }).then((offer) => {
				peerConnection.setLocalDescription(offer).then(() => {
					pongSocket.send(JSON.stringify({ 'offer': offer }));
				});
			});
		} else if (peerConnection.connectionState === 'closed' && interval) {
			clearInterval(interval);
			interval = undefined;
		} else if (peerConnection.connectionState === 'disconnected' && !interval) {
			interval = setInterval(() => {
				pongSocket.send(JSON.stringify({ 'offer': offer }));
			}, 4000);
		}
	});
	peerConnection.addEventListener('track', async (event) => {
		const [remoteStream] = event.streams;
		document.getElementById("peer_stream").srcObject = remoteStream;
	});
	interval = setInterval(() => {
		pongSocket.send(JSON.stringify({ 'offer': offer }));
	}, 4000);
}

async function answerCall() {
	const configuration = {
		'iceServers': [{
			'urls': 'turn:dev.acorp.games:3478',
			username: 'anon',
			credential: 'anon-pass'
		}], iceTransportPolicy: 'relay', 'sdpSemantics': 'unified-plan',
	};
	peerConnection = new RTCPeerConnection(configuration);
	if (localStream) {
		localStream.getTracks().forEach(track => {
			peerConnection.addTrack(track, localStream);
		});
	}
	pongSocket.addEventListener('message', async event => {
		const message = JSON.parse(event.data);
		if (message.offer) {
			peerConnection.setRemoteDescription(new RTCSessionDescription(message.offer)).catch(e => console.error("Failed to set remote description: ", e));
			const answer = await peerConnection.createAnswer();
			await peerConnection.setLocalDescription(answer);
			pongSocket.send(JSON.stringify({ 'answer': answer }));
		}
		if (message.iceCandidate) {
			try {
				await peerConnection.addIceCandidate(message.iceCandidate);
			} catch (e) {
				console.error('Error adding received ice candidate', e);
			}
		}
	});
	peerConnection.addEventListener('icecandidate', event => {
		if (event.candidate) {
			if (event.candidate.candidate.indexOf("relay") < 0) {
				return;
			}
			pongSocket.send(JSON.stringify({ 'iceCandidate': event.candidate }));
		}
	});
	peerConnection.addEventListener('track', async (event) => {
		const [remoteStream] = event.streams;
		document.getElementById("peer_stream").srcObject = remoteStream;
	});
}

export function initPongSocket(params) {
	if (pongSocket)
		return;
	pongSocket = new WebSocket((location.protocol === 'https:' ? 'wss://' : 'ws://') + window.location.host + '/ws/pong/game/' + params.uuid);
	pongSocket.addEventListener("message", async event => {
		const message = JSON.parse(event.data);
		if (message.player_id && message.player_id === 1) {
			navigator.mediaDevices.getUserMedia({ audio: true, video: false })
				.then(function (stream) {
					localStream = stream;
					makeCall();
				})
				.catch(function (err) {
					console.error('getUserMedia error:', err);
					makeCall();
				});
		} else if (message.player_id && message.player_id === 2) {
			navigator.mediaDevices.getUserMedia({ audio: true, video: false })
				.then(function (stream) {
					localStream = stream;
					answerCall();
				})
				.catch(function (err) {
					console.error('getUserMedia error:', err);
					answerCall();
				});
		}
	}, { once: true });
	pongSocket.onclose = function (event) {
		pongSocket = undefined;
		history.pushState("", "", "/");
		router();
	};
}

export function closePongSocket() {
	if (pongSocket && pongSocket.readyState === WebSocket.OPEN) {
		pongSocket.onclose = null;
		pongSocket.close();
	}
	if (peerConnection) {
		peerConnection.close();
		peerConnection = undefined;
	}
	if (localStream) {
		localStream.getTracks().forEach(track => {
			track.stop();
		});
		localStream = undefined;
	}
	if (interval) {
		clearInterval(interval);
		interval = undefined;
	}
	pongSocket = undefined;
}
