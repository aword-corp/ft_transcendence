import { Ball } from "../utils/Ball.js"
import { Paddle } from "../utils/Paddle.js"
import { Particle } from "../utils/Particle.js"

class Local extends HTMLElement {
	constructor() {
		super();

		this.innerHTML = `
			<canvas tabindex='1' id="pongCanvas" class="pongCanvas"></canvas>
			<h1 style="text-align: center">Player 1: W/Z and S</h1>
			<h1 style="text-align: center">Player 2: 5 and 2</h1>
			<h1 style="text-align: center" id="winner"></h1>
		`;

		this.canvas = document.getElementById("pongCanvas");

		this.canvas.width = 600;
		this.canvas.height = 400;

		this.ctx = this.canvas.getContext("2d");


		this.wall_offset = 25;
		this.paddleWidth = 10;
		this.paddleHeight = 100;
		this.maxScore = 3;
		this.acceleration = 1.05;
		this.rectWidth = 200;
		this.rectLength = 80;
		this.gameFinished = false;
		this.particles = [];
		this.ball;
		this.player_1;
		this.player_2;

		this.setCanvasSize();
		this.handleKeyDown = this.handleKeyDown.bind(this);
		this.handleKeyUp = this.handleKeyUp.bind(this);
		this.handleClick = this.handleClick.bind(this);
		this.handleHover = this.handleHover.bind(this);


		this.canvas.addEventListener("keydown", this.handleKeyDown);
		this.canvas.addEventListener("keyup", this.handleKeyUp);
		this.canvas.addEventListener("click", this.handleClick);
		this.canvas.addEventListener("mousemove", this.handleHover);
		this.initGame();
	}

	setCanvasSize() {
		this.canvas.width = window.innerWidth;
		this.canvas.height = window.innerHeight;

		if (this.canvas.width > 800) {
			this.canvas.width = 800;
		}
		if (this.canvas.height > 600) {
			this.canvas.height = 600;
		}

	}

	async initGame() {
		this.ball = new Ball(
			this.canvas.width / 2,
			this.canvas.height / 2,
			9,
			-5,
			5
		); // init this.ball

		this.player_1 = new Paddle(
			this.wall_offset,
			(this.canvas.height - this.paddleHeight) / 2,
			false,
			false,
			10,
			this.paddleHeight,
			this.paddleWidth,
			0,
		); // init player1

		this.player_2 = new Paddle(
			this.canvas.width - this.wall_offset - this.paddleWidth,
			(this.canvas.height - this.paddleHeight) / 2,
			false,
			false,
			10,
			this.paddleHeight,
			this.paddleWidth,
			0,
		); // init player2

		this.gameFinished = false;

		this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

		this.drawCentralLine();
		this.drawScores();

		this.ball.draw(this.ctx);
		this.player_1.draw(this.ctx);
		this.player_2.draw(this.ctx);

		this.player_1.update(this.canvas.height);
		this.player_2.update(this.canvas.height);
		await this.sleep(2000);
		this.gameLoop();

	}

	drawCentralLine() {
		this.ctx.beginPath();
		this.ctx.moveTo(this.canvas.width / 2, 0);
		this.ctx.lineTo(this.canvas.width / 2, this.canvas.height);
		this.ctx.stroke();
	}

	drawScores() {
		this.ctx.fillStyle = 'black';
		this.ctx.fillText(this.player_1.score, this.canvas.width / 2 - 75, 50);
		this.ctx.fillText(this.player_2.score, this.canvas.width / 2 + 45, 50);
	}

	drawRoundedRect(x, y, width, height, radius) {
		if (width < 2 * radius) radius = width / 2;
		if (height < 2 * radius) radius = height / 2;

		this.ctx.beginPath();
		this.ctx.moveTo(x + radius, y);
		this.ctx.arcTo(x + width, y, x + width, y + height, radius);
		this.ctx.arcTo(x + width, y + height, x, y + height, radius);
		this.ctx.arcTo(x, y + height, x, y, radius);
		this.ctx.arcTo(x, y, x + width, y, radius);
		this.ctx.closePath();
		this.ctx.fill();
		this.ctx.stroke();
	}

	drawWinner(can_replay) {
		if (this.player_1.score >= this.player_2.score) {
			document.getElementById("winner").innerText = "Player 1 has won";
		}
		else {
			document.getElementById("winner").innerText = "Player 2 has won";
		}

		this.gameFinished = true;
	}

	async gameLoop() {
		this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

		this.drawCentralLine();
		this.drawScores();

		this.ball.draw(this.ctx);
		this.player_1.draw(this.ctx);
		this.player_2.draw(this.ctx);

		this.player_1.update(this.canvas.height);
		this.player_2.update(this.canvas.height);
		switch (this.updateBallPosition(this.ball, this.player_1, this.player_2)) {
			case 1:
				this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
				this.drawCentralLine();
				this.drawScores();
				this.ball.colorTemperature = 0;
				this.ball.draw(this.ctx);
				this.player_1.draw(this.ctx);
				this.player_2.draw(this.ctx);
				await this.sleep(1000);
				break;
			case 2:
				this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
				this.drawCentralLine();
				this.drawScores();
				this.drawWinner(this.getAttribute("can_replay"));
				await this.sleep(3000);
				this.dispatchEvent(new CustomEvent("game_ended", {
					winner: this.player_1.score > this.player_2.score,
					score: [this.player_1.score, this.player_2.score],
				}
				));
				return;
		}

		this.updateParticles();
		this.drawParticles();

		requestAnimationFrame(() => this.gameLoop());
	}


	updateBallPosition() {
		let oldX = this.ball.x;

		this.ball.update();
		// console.log("Ball is at %d, %d", this.ball.x, this.ball.y);


		// check for up and down wall collision
		if (this.ball.y - this.ball.radius < 0) {
			this.ball.y = this.ball.radius;
			this.ball.dy *= -1;
		} else if (this.ball.y + this.ball.radius > this.canvas.height) {
			this.ball.y = this.canvas.height - this.ball.radius;
			this.ball.dy *= -1;
		}

		if (this.ball.x - this.ball.radius < 0) {
			this.reset_ball(1);
			this.reset_paddles();
			this.player_2.score += 1;
			return this.checkScore() ? 2 : 1;
		} else if (this.ball.x + this.ball.radius > this.canvas.width) {
			this.reset_ball(2);
			this.reset_paddles();
			this.player_1.score += 1;
			return this.checkScore() ? 2 : 1;
		}

		// players paddles collisions
		this.checkPlayerCollision(oldX);
		return 0;
	}

	checkPlayerCollision(oldX) {
		const maxAngle = Math.PI / 4;


		let wentThrough1 = oldX - this.ball.radius > this.player_1.width + this.player_1.x && this.ball.x - this.ball.radius <= this.player_1.width + this.player_1.x;

		if (wentThrough1 && this.player_1.y <= this.ball.y + this.ball.radius && this.ball.y - this.ball.radius <= this.player_1.y + this.player_1.height) {
			// console.log("Ball is at %d, %d", this.ball.x, this.ball.y);
			this.createParticules(this.ball.x, this.ball.y, 'red', 1);
			this.ball.colorTemperature += 0.05;
			let ballPosPaddle = (this.player_1.y + this.player_1.height / 2) - this.ball.y;
			let relPos = ballPosPaddle / (this.player_1.height / 2);
			let bounceAngle = relPos * maxAngle;

			let speed = Math.sqrt(this.ball.dx * this.ball.dx + this.ball.dy * this.ball.dy) * this.acceleration;
			this.ball.dx = speed * Math.cos(bounceAngle);
			this.ball.dy = speed * -Math.sin(bounceAngle);
		}



		let wentThrough2 = oldX + this.ball.radius < this.player_2.x && this.ball.x + this.ball.radius >= this.player_2.x;

		if (wentThrough2 && this.player_2.y <= this.ball.y + this.ball.radius && this.ball.y - this.ball.radius <= this.player_2.y + this.player_2.height) {
			this.createParticules(this.ball.x, this.ball.y, 'red', 2);
			this.ball.colorTemperature += 0.05;
			let ballPosPaddle = (this.player_2.y + this.player_2.height / 2) - this.ball.y;
			let relPos = ballPosPaddle / (this.player_2.height / 2);
			let bounceAngle = relPos * maxAngle;


			let speed = Math.sqrt(this.ball.dx * this.ball.dx + this.ball.dy * this.ball.dy) * this.acceleration;
			this.ball.dx = -speed * Math.cos(bounceAngle);
			this.ball.dy = speed * -Math.sin(bounceAngle);
		}
	}

	sleep(ms) {
		return new Promise(resolve => setTimeout(resolve, ms));
	}

	reset_ball(player) {
		this.ball.x = this.canvas.width / 2;
		this.ball.y = this.canvas.height / 2;
		this.ball.dx = player == 1 ? 5 : -5;
		this.ball.dy = 5;
	}

	reset_paddles() {
		// this.player_1.x = this.wall_offset;
		this.player_1.y = (this.canvas.height - this.paddleHeight) / 2;
		// this.player_2.x = this.canvas.width - this.wall_offset - this.paddleWidth;
		this.player_2.y = (this.canvas.height - this.paddleHeight) / 2;
	}

	checkScore() {
		return (this.player_1.score >= this.maxScore || this.player_2.score >= this.maxScore);
	}

	handleKeyDown(event) {
		switch (event.key) {
			case 'w':
			case 'z':
				this.player_1.up = true;
				break;
			case 's':
				this.player_1.down = true;
				break;
			case '5':
				this.player_2.up = true;
				break;
			case '2':
				this.player_2.down = true;
				break;
		}
	};

	handleKeyUp(event) {
		switch (event.key) {
			case 'w':
			case 'z':
				this.player_1.up = false;
				break;
			case 's':
				this.player_1.down = false;
				break;
			case '5':
				this.player_2.up = false;
				break;
			case '2':
				this.player_2.down = false;
				break;
		}
	};

	getMousePos(event) {
		var rect = this.canvas.getBoundingClientRect();

		return {
			x: event.clientX - rect.left,
			y: event.clientY - rect.top,
		}
	}

	clickedOnButton(mousePos, rect) {
		return mousePos.x > rect.x && mousePos.x < rect.x + this.rectWidth
			&& mousePos.y > rect.y && mousePos.y < rect.y + this.rectLength;
	}

	handleClick(event) {
		var mousePos = this.getMousePos(event);
		var rect = {
			x: (this.canvas.width - this.rectWidth) / 2,
			y: this.canvas.height / 2 + 20
		}

		if (this.clickedOnButton(mousePos, rect) && this.gameFinished) {
			this.initGame();
		}
	};

	handleHover(event) {
		const mousePos = this.getMousePos(event);
		const buttonRect = {
			x: (this.canvas.width - this.rectWidth) / 2,
			y: this.canvas.height / 2 + 20,
		};
		if (this.clickedOnButton(mousePos, buttonRect)) {
			this.canvas.style.cursor = 'pointer';
		} else {
			this.canvas.style.cursor = 'default';
		}
	};



	createParticules(x, y, color, player) {
		for (let i = 0; i < 20; i++) {
			let dx = player == 1 ? Math.abs((Math.random() - 0.5) * 4) : -Math.abs((Math.random() - 0.5) * 4);
			let dy = (Math.random() - 0.5) * 4;
			let part = new Particle(x, y, dx, dy, 20, color);
			this.particles.push(part);
		}
	}

	updateParticles() {
		this.particles = this.particles.filter(particle => particle.life > 0);
		this.particles.forEach(particle => particle.update());
	}

	drawParticles() {
		this.particles.forEach(particle => particle.draw(this.ctx));
	}


}
customElements.define("pong-local-game", Local);
