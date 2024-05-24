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


		fetch("/api/clicks", {
			method: "GET",
			headers: {
				Accept: "application/json, text/plain",
				"Content-Type": "application/json;charset=UTF-8",
			},
		}).then((response) => {
			response.json().then((json) => {
				document.getElementById("count").innerText = json.count;
			});
		});

		this.innerHTML = `
			<p id="count"></p>
		`;

		this.onclick = onClickMe;
	}
}

customElements.define("click-counter", Clicker);
