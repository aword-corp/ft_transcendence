import { tmSocket } from "./socket.js";
import { router } from "../main.js"


class TournamentQueue extends HTMLElement {
	constructor() {
		super();

		this.innerHTML = `
			<div>
				<h1>Tournament</h1>
				<p id="status">Matchmaking for a tournament</p>
				<div id="game">
				</div>
			</div>
		`;
		tmSocket.onmessage = function (e) {
			let data = JSON.parse(e.data);
			if (data.type == "game.start") {
				console.log(data.game_id);
				console.log(`Pushed state = ${"/pong/" + data.game_id}`)

				let src = "/pong/" + data.game_id + "/iframe";
				document.getElementById("status").innerText = `In game with id ${data.game_id}`;
				document.getElementById("game").innerHTML = `
					<iframe src="${src}" width="900" height="700">
					</iframe>
				`;
			} else if (data.type == "game.waiting") {
				document.getElementById("status").innerText = `Currently waiting`;
				document.getElementById("game").innerHTML = `<img src="https://media4.giphy.com/media/QBd2kLB5qDmysEXre9/giphy.gif?cid=6c09b9524n5r3ou51c7v4t9fz23gm3qymowstl74ps138sxn&ep=v1_internal_gif_by_id&rid=giphy.gif&ct=g"/>`
			}
			else if (data.type == "update.message") {
				console.log(data.users);
			} else {
				history.pushState("", "", "/");
				router();
			}
		};
	}
}

customElements.define("tournament-queue", TournamentQueue);
