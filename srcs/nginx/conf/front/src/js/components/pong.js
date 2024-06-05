import { pongSocket, initPongSocket, closePongSocket } from "./socket.js";

class PongGame extends HTMLElement {
	constructor() {
		super();

		this.innerHTML = `
			<canvas id="pongCanvas" class="pongCanvas"></canvas>
		`;

		this.canvas = document.getElementById("pongCanvas");
		this.ctx = this.canvas.getContext("2d");
		initPongSocket(this.attributes.getNamedItem("uuid").value);


		this.handleKeyDown = this.handleKeyDown.bind(this);
        this.handleKeyUp = this.handleKeyUp.bind(this);
        this.handleSocketMessage = this.handleSocketMessage.bind(this);

		
		document.addEventListener("keydown", this.handleKeyDown);
		document.addEventListener("keyup", this.handleKeyUp);

		pongSocket.addEventListener("message", this.handleSocketMessage);
	}


	handleKeyDown(event) {
		let message;
		switch (event.key) {
			case "w":
				message = JSON.stringify({ "action": "UP_PRESS_KEYDOWN" });
				break;
			case "s":
				message = JSON.stringify({ "action": "DOWN_PRESS_KEYDOWN" });
				break;
			case "ArrowUp":
				message = JSON.stringify({ "action": "UP_PRESS_KEYDOWN" });
				break;
			case "ArrowDown":
				message = JSON.stringify({ "action": "DOWN_PRESS_KEYDOWN" });
				break;
		}
		if (message) {
			pongSocket.send(message);
		}
	}

	handleKeyUp(event) {
		let message;
		switch (event.key) {
			case "w":
				message = JSON.stringify({ "action": "UP_PRESS_KEYUP" });
				break;
			case "s":
				message = JSON.stringify({ "action": "DOWN_PRESS_KEYUP" });
				break;
			case "ArrowUp":
				message = JSON.stringify({ "action": "UP_PRESS_KEYUP" });
				break;
			case "ArrowDown":
				message = JSON.stringify({ "action": "DOWN_PRESS_KEYUP" });
				break;
		}
		if (message) {
			pongSocket.send(message);
		}
	}

	handleSocketMessage(event) {
		let data = JSON.parse(event.data);

		if (data.type == "broadcast.pos") {
			this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

			let player1 = data.position.player1;
			let player2 = data.position.player2;

			this.drawBall(data.position.ball);
			this.drawPaddle(player1);
			this.drawPaddle(player2);
			this.drawCentralLine();
			this.drawScores(player1, player2);
		}
	}

	drawBall(ball) {
		const ratio_x = this.canvas.width;
		const ratio_y = this.canvas.height;

		this.ctx.fillStyle = 'black';
		this.ctx.beginPath();
		this.ctx.arc(ball.x * ratio_x, ball.y * ratio_y, ball.radius * ratio_x, 0, Math.PI*2);
		this.ctx.fill();
		this.ctx.closePath();
	}

	drawPaddle(paddle) {
		const ratio_x = this.canvas.width;
		const ratio_y = this.canvas.height;

		this.ctx.save();

		this.ctx.shadowColor = 'rgba(50, 50, 50, 0.7)'; // Neon color (cyan)
		this.ctx.shadowBlur = 20;
		this.ctx.shadowOffsetX = 0;
		this.ctx.shadowOffsetY = 0;
		this.ctx.fillStyle = 'black';

		this.ctx.fillRect(paddle.x * ratio_x, paddle.y * ratio_y, paddle.width * ratio_x, paddle.height * ratio_y);

		this.ctx.restore();
	}

	drawCentralLine() {
		this.ctx.beginPath();
		this.ctx.moveTo(this.canvas.width / 2, 0);
		this.ctx.lineTo(this.canvas.width / 2, this.canvas.height);
		this.ctx.stroke();
	}

	drawScores(player_1, player_2) {
		this.ctx.fillStyle = 'black';
		this.ctx.fillText(player_1.score, this.canvas.width / 2 - 75, 50);
		this.ctx.fillText(player_2.score, this.canvas.width / 2 + 45, 50);
	}

}




customElements.define("pong-game", PongGame);
