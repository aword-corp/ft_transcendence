export class Particle {
	constructor (x, y, dx, dy, life, color) {
		this._x = x;
        this._y = y;
        this._dx = dx;
        this._dy = dy;
        this._life = life;
        this._color = color;
	}

	get x() {
		return this._x;
	}

	get y() {
		return this._y;
	}

	get life() {
		return this._life;
	}

	get color() {
		return this._color;
	}

	get dx() {
		return this._dx;
	}

	get dy() {
		return this._dy;
	}

	set x(x) {
		this._x = x;
	}

	set y(y) {
		this._y = y;
	}

	set life(life) {
		this._life = life;
	}

	set color(color) {
		this._color = color;
	}

	set dx(dx) {
		this._dx = dx;
	}

	set dy(dy) {
		this._dy = dy;
	}

	update() {
		this._x += this._dx;
		this._y += this._dy;
		this._life -= 1;
	}

	draw(ctx) {
		ctx.save();
		ctx.globalAlpha = this._life / 100;
		ctx.fillStyle = this._color;
		ctx.beginPath();
        ctx.arc(this.x, this.y, 3, 0, Math.PI * 2);
        ctx.fill();
        ctx.restore();
	}
}