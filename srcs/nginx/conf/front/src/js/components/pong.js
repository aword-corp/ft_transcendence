import {initPongSocket, closePongSocket} from "./socket.js";

class PongGame extends HTMLElement {
	constructor() {
		super();

		this.innerHTML = `
			<canvas id="pongCanvas" class="pongCanvas"></canvas>
		`;

		let canvas = document.getElementById("pongCanvas");
		let ctx = canvas.getContext("2d");
		initPongSocket();

		// if (!canvas || !canvas.getContext) {
		// 	console.error('Error: Canva not initialized properly');
		// 	return ;
		// }

		document.addEventListener("keydown", function(event) {
			let message;
			switch (event.key) {
				case "w":
					message = JSON.stringify({ "action": "UP_PRESS_KEYDOWN"});
					break ;
				case "s":
					message = JSON.stringify({ "action": "DOWN_PRESS_KEYDOWN"});
					break ;
				case "ArrowUp":
					message = JSON.stringify({ "action": "UP_PRESS_KEYDOWN"});
					break ;
				case "ArrowDown":
					message = JSON.stringify({ "action": "DOWN_PRESS_KEYDOWN"});
					break ;
			}
			if (message) {
				pongSocket.send(message);
			}
		});

		document.addEventListener("keyup", function(event) {
			let message;
			switch (event.key) {
				case "w":
					message = JSON.stringify({ "action": "UP_PRESS_KEYUP"});
					break ;
				case "s":
					message = JSON.stringify({ "action": "DOWN_PRESS_KEYUP"});
					break ;
				case "ArrowUp":
					message = JSON.stringify({ "action": "UP_PRESS_KEYUP"});
					break ;
				case "ArrowDown":
					message = JSON.stringify({ "action": "DOWN_PRESS_KEYUP"});
					break ;
			}
			if (message) {
				pongSocket.send(message);
			}
		});

		// the rendering to adapt to the socket messages received
	}
}




customElements.define("pong-game", PongGame);
