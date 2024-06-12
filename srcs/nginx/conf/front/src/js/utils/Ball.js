export class Ball {
	constructor(x, y, radius, dx, dy) {
		this._x = x;
		this._y = y;
		this._radius = radius;
		this._dx = dx;
		this._dy = dy;
		this._colorTemperature = 0;
	}

	get x() {
		return this._x;
	}

	get y() {
		return this._y;
	}

	get dx() {
		return this._dx;
	}

	get dy() {
		return this._dy;
	}

	get radius() {
		return this._radius;
	}

	get colorTemperature() {
		return this._colorTemperature;
	}

	set x(newX) {
		this._x = newX;
	}

	set y(newY) {
		this._y = newY;
	}

	set dx(newDX) {
		this._dx = newDX;
	}

	set dy(newDY) {
		this._dy = newDY;
	}

	set radius(newRadius) {
		this._radius = newRadius;
	}

	set colorTemperature(newColorTemperature) {
		this._colorTemperature = newColorTemperature;
	}

	update_x(offset) {
		this._x = this._x + offset;
	}

	update_y(offset) {
		this._y += offset;
	}

	update() {
		this._x += this._dx;
		this._y += this._dy;
	
		// this._colorTemperature += 0.01;
		// if (this._colorTemperature > 1) {
		// 	this._colorTemperature = 1;
		// }
	}

	getColor() {
		let r = Math.min(255, this._colorTemperature * 510);
		let g = Math.min(100, (this.colorTemperature - 0.5) * 200);
        let b = Math.min(100, (this.colorTemperature - 0.5) * 200);
		return `rgb(${r}, ${g}, ${b})`;
	}

	draw(ctx) {
		ctx.fillStyle = this.getColor();
		ctx.beginPath();
		ctx.arc(this._x, this._y, this._radius, 0, Math.PI*2);
		ctx.fill();
		ctx.closePath();
	}
}