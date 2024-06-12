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

export var localPeerConnection = undefined;

async function makeCall() {
	let interval = undefined;
	const configuration = {
		'iceServers': [{
			'urls': 'turn:dev.acorp.games:3478',
			username: 'anon',
			credential: 'anon-pass'
		}], iceTransportPolicy: 'relay', 'sdpSemantics': 'unified-plan',
	};
	const peerConnection = new RTCPeerConnection(configuration);
	console.log("peerConnection", peerConnection);
	localStream.getTracks().forEach(track => {
		console.log("track", track);
		peerConnection.addTrack(track, localStream);
	});
	pongSocket.addEventListener('message', async event => {
		const message = JSON.parse(event.data);
		if (message.answer) {
			console.log("message_answer", message);
			const remoteDesc = new RTCSessionDescription(message.answer);
			await peerConnection.setRemoteDescription(remoteDesc);
		}
		if (message.iceCandidate) {
			console.log("message_iceCandidate", message);
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
	console.log("offer", offer);
	await peerConnection.setLocalDescription(offer);
	peerConnection.addEventListener('icecandidate', event => {
		console.log("icecandidate", event);
		if (event.candidate) {
			if (event.candidate.candidate.indexOf("relay") < 0) {
				return;
			}
			pongSocket.send(JSON.stringify({ 'iceCandidate': event.candidate }));
		}
	});
	peerConnection.addEventListener('connectionstatechange', event => {
		console.log("connectionstatechange", event);
		console.log("state", peerConnection.connectionState);
		if (peerConnection.connectionState === 'connected') {
			console.log("connected ?????? gg");
			if (interval) {
				clearInterval(interval);
				interval = undefined;
			}
		} else if (peerConnection.connectionState === 'failed') {
			peerConnection.createOffer({ iceRestart: true }).then((offer) => {
				peerConnection.setLocalDescription(offer).then(() => {
					pongSocket.send(JSON.stringify({ 'offer': offer }));
				});
			});
		}
	});
	peerConnection.addEventListener('track', async (event) => {
		const [remoteStream] = event.streams;
		console.log("track", event);
		document.getElementById("peer_stream").srcObject = remoteStream;
	});
	interval = setInterval(() => {
		pongSocket.send(JSON.stringify({ 'offer': offer }));
	}, 5000);
}

async function answerCall() {
	const configuration = {
		'iceServers': [{
			'urls': 'turn:dev.acorp.games:3478',
			username: 'anon',
			credential: 'anon-pass'
		}], iceTransportPolicy: 'relay', 'sdpSemantics': 'unified-plan',
	};
	const peerConnection = new RTCPeerConnection(configuration);
	console.log("peerConnection", peerConnection);
	localStream.getTracks().forEach(track => {
		console.log("track", track);
		peerConnection.addTrack(track, localStream);
	});
	pongSocket.addEventListener('message', async event => {
		const message = JSON.parse(event.data);
		if (message.offer) {
			console.log("message_offer", message);
			peerConnection.setRemoteDescription(new RTCSessionDescription(message.offer));
			const answer = await peerConnection.createAnswer();
			await peerConnection.setLocalDescription(answer);
			pongSocket.send(JSON.stringify({ 'answer': answer }));
		}
		if (message.iceCandidate) {
			console.log("message_iceCandidate", message);
			try {
				await peerConnection.addIceCandidate(message.iceCandidate);
			} catch (e) {
				console.error('Error adding received ice candidate', e);
			}
		}
	});
	peerConnection.addEventListener('icecandidate', event => {
		console.log("icecandidate", event);
		if (event.candidate) {
			if (event.candidate.candidate.indexOf("relay") < 0) {
				return;
			}
			pongSocket.send(JSON.stringify({ 'iceCandidate': event.candidate }));
		}
	});
	peerConnection.addEventListener('connectionstatechange', event => {
		console.log("connectionstatechange", event);
		console.log("state", peerConnection.connectionState);
		if (peerConnection.connectionState === 'connected') {
			console.log("connected ?????? gg");
		}
	});
	peerConnection.addEventListener('track', async (event) => {
		const [remoteStream] = event.streams;
		console.log("track", event);
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
			console.log("Trying to get user media")
			navigator.mediaDevices.getUserMedia({ audio: true, video: false })
				.then(function (stream) {
					localStream = stream;
					console.log("localStream", localStream);
					// document.getElementById("local_stream").srcObject = localStream;
					makeCall();
				})
				.catch(function (err) {
					console.error('getUserMedia error:', err);
				});
		} else if (message.player_id && message.player_id === 2) {
			console.log("Trying to get user media")
			navigator.mediaDevices.getUserMedia({ audio: true, video: false })
				.then(function (stream) {
					localStream = stream;
					console.log("localStream", localStream);
					// document.getElementById("local_stream").srcObject = localStream;
					answerCall();
				})
				.catch(function (err) {
					console.error('getUserMedia error:', err);
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
	pongSocket = undefined;
}
