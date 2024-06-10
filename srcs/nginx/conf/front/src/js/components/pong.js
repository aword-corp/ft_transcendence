import { pongSocket } from "./socket.js";

class PongGame extends HTMLElement {
	constructor() {
		super();

		this.innerHTML = `
			<canvas id="pongCanvas" class="pongCanvas"></canvas>
		`;

		this.canvas = document.getElementById("pongCanvas");

		this.canvas.width = 600;
		this.canvas.height = 400;

		this.ctx = this.canvas.getContext("2d");


		this.handleKeyDown = this.handleKeyDown.bind(this);
		this.handleKeyUp = this.handleKeyUp.bind(this);
		this.handleSocketMessage = this.handleSocketMessage.bind(this);

		this.name = (JSON.parse(atob(localStorage.getItem("access-token").split('.')[1]))).username;

		this.up = false;

		this.down = false;

		document.addEventListener("keydown", this.handleKeyDown);
		document.addEventListener("keyup", this.handleKeyUp);

		pongSocket.addEventListener("message", this.handleSocketMessage);

	}

	handleKeyDown(event) {
		if (event.code === "KeyW" || event.code === "KeyZ" || event.code === "ArrowUp") {
			if (!this.up) {
				pongSocket.send(JSON.stringify({ "action": "UP_PRESS_KEYDOWN" }));
				this.up = true;
			}
		}
		else if (event.code === "KeyS" || event.code === "ArrowDown") {
			if (!this.down) {
				pongSocket.send(JSON.stringify({ "action": "DOWN_PRESS_KEYDOWN" }));
				this.down = true;
			}
		}
	}

	handleKeyUp(event) {
		if (event.code === "KeyW" || event.code === "KeyZ" || event.code === "ArrowUp") {
			if (this.up) {
				pongSocket.send(JSON.stringify({ "action": "UP_PRESS_KEYUP" }));
				this.up = false;
			}
		}
		else if (event.code === "KeyS" || event.code === "ArrowDown") {
			if (this.down) {
				pongSocket.send(JSON.stringify({ "action": "DOWN_PRESS_KEYUP" }));
				this.down = false;
			}
		}
	}

	handleSocketMessage(event) {
		let data = JSON.parse(event.data);

		if (data.type == "broadcast.pos") {
			this.ctx.reset();

			let player1 = data.position.player1;
			let player2 = data.position.player2;
			let ball = data.position.ball;

			this.drawBall(ball);
			this.drawPaddle(player1);
			this.drawPaddle(player2);
			this.drawCentralLine();
			this.drawScores(player1, player2);
		}

		else if (data.type == "broadcast.result") {
			this.ctx.reset();
		}

		else if (data.type == "broadcast.message") {
			console.log(data.message);
		}
	}

	drawBall(ball) {
		const ratio_x = this.canvas.width;
		const ratio_y = this.canvas.height;
		const scale = Math.min(ratio_x, ratio_y);

		this.ctx.fillStyle = 'black';
		this.ctx.beginPath();
		this.ctx.arc(ball.x * ratio_x, ball.y * ratio_y, ball.radius * scale, 0, Math.PI * 2);
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
		this.ctx.moveTo((this.canvas.width >> 1), 0);
		this.ctx.lineTo((this.canvas.width >> 1), this.canvas.height);
		this.ctx.stroke();
	}

	drawScores(player_1, player_2) {
		this.ctx.fillStyle = 'black';
		this.ctx.fillText(player_1.score, (this.canvas.width >> 1) - 75, 50);
		this.ctx.fillText(player_2.score, (this.canvas.width >> 1) + 45, 50);
	}

	mirror(player1, player2, ball) {
		let tmp = player1.x;
		player1.x = player2.x;
		player2.x = tmp;

		ball.x = Math.abs(0.5 - ball.x);
		ball.y = Math.abs(0.5 - ball.y);
	}

}

customElements.define("pong-game", PongGame);
