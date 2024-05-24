import { initSocketClick } from "./socket.js";

class Clicker extends HTMLElement {
	constructor() {
		super();

		const countSocket = new WebSocket((location.protocol === 'https:' ? 'wss://' : 'ws://') + window.location.host + '/ws/click/');

		countSocket.onmessage = function (e) {
			document.getElementById('count').innerText = e.data;
		};

		function onClickMe() {
			countSocket.send("");
		}


		fetch("https://localhost:8443/api/clicks", {
			method: "GET",
			headers: {
				Accept: "application/json, text/plain",
				"Content-Type": "application/json;charset=UTF-8",
			},
		}).then((response) =>
			response.json().then((json) => document.getElementById("count").innerText = json.count));

		this.onclick = initSocketClick();
	}
}
customElements.define("click-counter", Clicker);
