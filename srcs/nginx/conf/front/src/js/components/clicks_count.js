import { countSocket } from "./socket.js";

class Clicker extends HTMLElement {
	constructor() {
		super();

		this.innerHTML = `
			<p id="count"></p>
		`;
		fetch("/api/clicks", {
			method: "GET",
			headers: {
				Accept: "application/json, text/plain",
				"Content-Type": "application/json;charset=UTF-8",
			},
		}).then((response) =>
			response.json().then((json) => document.getElementById("count").innerText = json.count));

		this.onclick = function (e) {
			countSocket.send("");
		};

		countSocket.onmessage = function (e) {
			document.getElementById("count").innerText = e.data;
		}
	}
}
customElements.define("click-counter", Clicker);
