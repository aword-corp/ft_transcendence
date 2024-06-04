import {pongSocket, initPongSocket, closePongSocket} from "./socket.js";

class PongGame extends HTMLElement {
	static get observedAttributes() {
		return ['uuid'];
	}

	constructor() {
		super();

		this.innerHTML = `
			<canvas id="pongCanvas" class="pongCanvas"></canvas>
		`;

		let canvas = document.getElementById("pongCanvas");
		let ctx = canvas.getContext("2d");
		initPongSocket(this.uuid);

		document.addEventListener("keydown", this.handleKeyDown);
		document.addEventListener("keyup", this.handleKeyUp);

		pongSocket.addEventListener("message", this.handleSocketMessage);
	}


	handleKeyDown(event) {
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
	}

	handleKeyUp(event) {
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
	}

	handleSocketMessage(event) {
		//implement rendering of the game here
	}

}




customElements.define("pong-game", PongGame);
