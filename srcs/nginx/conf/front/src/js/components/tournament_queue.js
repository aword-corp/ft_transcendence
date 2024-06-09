import { tmSocket } from "./socket.js";
import { router } from "../main.js"


class TournamentQueue extends HTMLElement {
	constructor() {
		super();

		this.innerHTML = `
			<div>
				<h1>Tournament</h1>
				<p>Matchmaking for a tournament</p>
			</div>
		`;
		tmSocket.onmessage = function (e) {
			let data = JSON.parse(e.data);
			if (data.type == "game.start") {
				console.log(data.game_id);
				console.log(`Pushed state = ${"/pong/" + data.game_id}`)
				history.pushState("", "", "/pong/" + data.game_id);
				router();
			} else if (data.type == "update.message") {
				console.log(data.users, data.time_left);
			} else {
				console.log("whatever");
			}
		};
	}
}

customElements.define("tournament-queue", TournamentQueue);
