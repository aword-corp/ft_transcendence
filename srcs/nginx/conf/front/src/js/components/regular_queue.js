import { mmSocket } from "./socket.js";
import { router } from "../main.js"


class RegularQueue extends HTMLElement {
	constructor() {
		super();

		this.innerHTML = `
			<div>
				<h1>Regular Match</h1>
				<p>Matchmaking for a regular match</p>
			</div>
		`;
		mmSocket.onmessage = function (e) {
			let data = JSON.parse(e.data);
			if (data.type == "game.start") {
				console.log(data.game_id);
				console.log(`Pushed state = ${"/pong/" + data.game_id}`)
				history.pushState("", "", "/pong/" + data.game_id);
				router();
			} else if (data.type == "update.message") {
				console.log(data.users);
			} else {
				history.pushState("", "", "/");
				router();
			}
		};
	}
}

customElements.define("regular-queue", RegularQueue);
