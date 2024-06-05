import "../components/pong.js";

export function pong_title() {
	return ("Pong");
}

export function pong_view(params) {
	// console.log(params.uuid);
	return (`<pong-game uuid="${params.uuid}"></pong-game>`);
}
