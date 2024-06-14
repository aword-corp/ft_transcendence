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

export var update_interval = undefined;

const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));

export function initSocketUpdate() {
	if (updateSocket)
		return;
	updateSocket = new WebSocket((location.protocol === 'https:' ? 'wss://' : 'ws://') + window.location.host + '/api/ws/update/');
	updateSocket.addEventListener("message", defaultSocketUpdateOnMessage);
	update_interval = setInterval(async () => {
		let notifications = notification_queue.slice();
		let message = "";
		for (const notification of notifications) {
			document.getElementById("notification-system").style.visibility = "visible";
			switch (notification.type) {
				case "friend.request.received":
					message = `You received a friend request from ${notification.from}.`;
					break;
				case "friend.accepted.received":
					message = `${notification.from} is now your friend.`;
					break;
				case "channel.message.received":
					message = notification.channel ? `${notification.from} sent a message in ${notification.channel}.` : `${notification.from} sent you a message.`;
					break;
				case "user.connected.received":
					message = `${notification.from} is now online.`;
					break;
				case "user.disconnected.received":
					message = `${notification.from} is now offline.`;
					break;
				case "duel.request.received":
					message = `${notification.from} sent you a duel request.`;
					break;
				case "duel.start.received":
					message = `A duel agains ${notification.from} started.`;
					break;
			}
			notification_queue.shift();
			document.getElementById("notification-system").innerHTML = message;
			await sleep(3000);
			document.getElementById("notification-system").innerHTML = "";
			document.getElementById("notification-system").style.visibility = "hidden";
			await sleep(500);
		}
	}, 5000);
}

export function closeSocketUpdate() {
	if (updateSocket && updateSocket.readyState === WebSocket.OPEN)
		updateSocket.close();
	if (update_interval) {
		clearInterval(update_interval);
		update_interval = undefined;
	}
	if (updateSocket)
		updateSocket.removeEventListener("message", defaultSocketUpdateOnMessage);
	updateSocket = undefined;
}

export var notification_queue = [];

export function defaultSocketUpdateOnMessage(e) {
	var data = JSON.parse(e.data);
	if (data && data.type) {
		if (data.type.includes("received") &&
			(
				data.type.includes("friend.request.received")
				|| data.type.includes("friend.accepted")
				|| data.type.includes("channel.message")
				|| data.type.includes("connected")
				|| data.type.includes("duel")
			))
			notification_queue.push(data);
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

async function onAnswer(event) {
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
	if (message.error) {
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
		pongSocket.removeEventListener('message', onAnswer);
	}
}

async function onIceCandidate(event) {
	if (event.candidate) {
		if (event.candidate.candidate.indexOf("relay") < 0) {
			return;
		}
		pongSocket.send(JSON.stringify({ 'iceCandidate': event.candidate }));
	}
}

async function onConnectionStateChange(event, offer) {
	if (peerConnection.connectionState === 'connected' && interval) {
		clearInterval(interval);
		interval = undefined;
	} else if (peerConnection.connectionState === 'failed') {
		peerConnection.createOffer({
			'offerToReceiveAudio': true,
			'offerToReceiveVideo': false,
			'iceRestart': true,
		}).then((offer) => {
			peerConnection.setLocalDescription(offer).then(() => {
				pongSocket.send(JSON.stringify({ 'offer': offer }));
			});
		});
	} else if (peerConnection.connectionState === 'closed' && interval) {
		clearInterval(interval);
		interval = undefined;
	} else if (peerConnection.connectionState === 'disconnected' && !interval) {
		peerConnection.createOffer({
			'offerToReceiveAudio': true,
			'offerToReceiveVideo': false,
			'iceRestart': true,
		}).then((offer) => {
			peerConnection.setLocalDescription(offer).then(() => {
				interval = setInterval(() => {
					pongSocket.send(JSON.stringify({ 'offer': offer }));
				}, 4000);
			});
		});
	}
}

async function onTrack(event) {
	const [remoteStream] = event.streams;
	document.getElementById("peer_stream").srcObject = remoteStream;
}

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
	pongSocket.addEventListener('message', onAnswer);
	const offer = await peerConnection.createOffer({
		'offerToReceiveAudio': true,
		'offerToReceiveVideo': false
	});
	await peerConnection.setLocalDescription(offer);
	peerConnection.addEventListener('icecandidate', onIceCandidate);
	peerConnection.addEventListener('connectionstatechange', onConnectionStateChange);
	peerConnection.addEventListener('track', onTrack);
	interval = setInterval(() => {
		pongSocket.send(JSON.stringify({ 'offer': offer }));
	}, 4000);
}

async function onCall(event) {
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
	if (message.error) {
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
		pongSocket.removeEventListener('message', onCall);
	}
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
	pongSocket.addEventListener('message', onCall);
	peerConnection.addEventListener('icecandidate', onIceCandidate);
	peerConnection.addEventListener('track', onTrack);
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
