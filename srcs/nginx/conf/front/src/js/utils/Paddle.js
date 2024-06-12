

export class Paddle {
	constructor(x, y, up, down, speed, height, width, score) {
		this._x = x;
		this._y = y;
		this._up = up;
		this._down = down;
		this._speed = speed;
		this._height = height;
		this._width = width;
		this._score = score;
	}


	get x() {
		return this._x;
	}

	get y() {
		return this._y;
	}

	get up() {
		return this._up;
	}

	get down() {
		return this._down;
	}

	get speed() {
		return this._speed;
	}

	get height() {
		return this._height;
	}

	get width() {
		return this._width;
	}

	get score() {
		return this._score;
	}

	set y(newY) {
		this._y = newY;
	}

	set up(newUp) {
		this._up = newUp;
	}

	set down(newDown) {
		this._down = newDown;
	}

	set speed(newSpeed) {
		this._speed = newSpeed;
	}

	set score(newScore) {
		this._score = newScore;
	}

	update_y(offset) {
		this._y += offset;
	}

	draw(ctx) {
		ctx.save();

		ctx.shadowColor = 'rgba(50, 50, 50, 0.7)'; // Neon color (cyan)
		ctx.shadowBlur = 20;
		ctx.shadowOffsetX = 0;
		ctx.shadowOffsetY = 0;
		ctx.fillStyle = 'black';

		ctx.fillRect(this._x, this._y, this._width, this._height);

		ctx.restore();
	}

	update(c_height) {

		if (this._up && !this._down) {
			this._y -= this._speed;
		}

		if (this._down && !this._up) {
			this._y += this._speed;
		}

		if (this._y < 0) {
			this._y = 0;
		} else if (this._y + this._height > c_height) {
			this._y = c_height - this._height;
		}
	}
}
