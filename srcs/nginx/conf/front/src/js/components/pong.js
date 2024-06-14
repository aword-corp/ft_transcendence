import { pongSocket } from "./socket.js";

class PongGame extends HTMLElement {
	constructor() {
		super();

		this.innerHTML = `
			<h1 style="text-align: center">Controls: W/Z and S</h1>
			<div id="chat">
			<div class="scoreboard">
				<div id="player1-info" class="player-info">
					<span id="player1-name">Player 1</span>
					<span id="player1-score">0</span>
				</div>
				<div id="player2-info" class="player-info">
					<span id="player2-name">Player 2</span>
					<span id="player2-score">0</span>
				</div>
			</div>
            <canvas tabindex='1' id="pongCanvas" class="pongCanvas"></canvas>
            <div class="container">
                <div class="nav-bar">
                    <a>Chat</a>
                    <div class="close">
                        <div class="line one"></div>
                        <div class="line two"></div>
                    </div>
                </div>
                <div class="messages-area" id="chat"></div>
                <div class="sender-area">
                    <div class="input-place">
                        <input placeholder="Send a message." class="send-input" id="id_message" type="text" name="message" required>
                        <div class="send" id="send_message">
                            <svg class="send-icon" version="1.1" id="Capa_1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" x="0px" y="0px" viewBox="0 0 512 512" style="enable-background:new 0 0 512 512;" xml:space="preserve"><g><g><path fill="#16db65" d="M481.508,210.336L68.414,38.926c-17.403-7.222-37.064-4.045-51.309,8.287C2.86,59.547-3.098,78.551,1.558,96.808 L38.327,241h180.026c8.284,0,15.001,6.716,15.001,15.001c0,8.284-6.716,15.001-15.001,15.001H38.327L1.558,415.193 c-4.656,18.258,1.301,37.262,15.547,49.595c14.274,12.357,33.937,15.495,51.31,8.287l413.094-171.409 C500.317,293.862,512,276.364,512,256.001C512,235.638,500.317,218.139,481.508,210.336z"></path></g></g></svg>
                        </div>
                    </div>
                </div>
            </div>
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

		this.canvas.addEventListener("keydown", this.handleKeyDown);
		this.canvas.addEventListener("keyup", this.handleKeyUp);
		this.canvas.addEventListener("focusout", (event) => {
			pongSocket.send(JSON.stringify({ "action": "UP_PRESS_KEYUP" }));
			this.up = false;
			pongSocket.send(JSON.stringify({ "action": "DOWN_PRESS_KEYUP" }));
			this.down = false;
		});

		pongSocket.addEventListener("message", this.handleSocketMessage);

		let send_message_button = document.getElementById("send_message");

		send_message_button.addEventListener("click", (event) => {
			event.preventDefault();
			const messageInput = document.getElementById("id_message");
			const message = messageInput.value;
			if (message.trim()) {
				pongSocket.send(JSON.stringify({ "message": message }));
				messageInput.value = '';
			}
			// event.target.reset();
		});
	}

	handleKeyDown(event) {
		if (event.code === "KeyW" || event.code === "KeyZ" || event.code === "ArrowUp") {
			if (!this.up) {
				pongSocket.send(JSON.stringify({ "action": "UP_PRESS_KEYDOWN" }));
				this.up = true;
			}
		} else if (event.code === "KeyS" || event.code === "ArrowDown") {
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
		} else if (event.code === "KeyS" || event.code === "ArrowDown") {
			if (this.down) {
				pongSocket.send(JSON.stringify({ "action": "DOWN_PRESS_KEYUP" }));
				this.down = false;
			}
		}
	}

	handleSocketMessage(event) {
		let data = JSON.parse(event.data);

		if (data.type == "broadcast.pos") {
			this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height); // Clear the canvas

			let player1 = data.position.player1;
			let player2 = data.position.player2;
			let ball = data.position.ball;

			this.drawBall(ball);
			this.drawPaddle(player1);
			this.drawPaddle(player2);
			this.drawCentralLine();
			this.updateScores(player1, player2);
		} else if (data.type == "broadcast.result") {
			this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
		} else if (data.type == "broadcast.message") {
			this.addMessageToChat(data.message);
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

		this.ctx.shadowColor = 'rgba(6, 52, 25, 0.7)'; // Neon color (cyan)
		this.ctx.shadowBlur = 20;
		this.ctx.shadowOffsetX = 0;
		this.ctx.shadowOffsetY = 0;
		this.ctx.fillStyle = 'rgba(22, 219, 101, 1)';

		this.ctx.fillRect(paddle.x * ratio_x, paddle.y * ratio_y, paddle.width * ratio_x, paddle.height * ratio_y);

		this.ctx.restore();
	}

	drawCentralLine() {
		this.ctx.beginPath();
		this.ctx.moveTo((this.canvas.width >> 1), 0);
		this.ctx.lineTo((this.canvas.width >> 1), this.canvas.height);
		this.ctx.stroke();
	}

	updateScores(player1, player2) {
		document.getElementById("player1-score").innerText = player1.score;
		document.getElementById("player1-name").innerText = player1.name;
		document.getElementById("player2-score").innerText = player2.score;
		document.getElementById("player2-name").innerText = player2.name;
	}

	addMessageToChat(message) {
		const name = message.user.display_name != null ? message.user.display_name : message.user.name;
		const chat = document.getElementById("chat");
		const messageElement = document.createElement("div");
		messageElement.className = "message_u";

		const pfp = document.createElement("img");
		pfp.src = message.user.avatar_url;
		pfp.alt = "OI";
		pfp.className = "profile-image";

		const spectate = document.createElement("img");
		spectate.src = !message.is_player ? "/static/static/oeil.png" : "/static/static/escrime.png";
		spectate.className = "spectate-image";

		const textElement = document.createElement("span");
		textElement.textContent = name + " : " + message.message;

		const textContainer = document.createElement("div");
		textContainer.className = "text-container";
		textContainer.appendChild(textElement);

		messageElement.appendChild(spectate);
		messageElement.appendChild(pfp);
		messageElement.appendChild(textContainer);

		chat.appendChild(messageElement);
		chat.scrollTop = chat.scrollHeight; // Scroll to the bottom
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
