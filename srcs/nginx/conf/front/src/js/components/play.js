import { mmSocket, initMMSocket, closeMMSocket } from "./socket.js";
import { router } from "../main.js"


class PlayMenu extends HTMLElement {
	constructor() {
		super();

		this.innerHTML = `
			<div>
				<button class="play button" id="regular-match" type="button">Regular Match</button>
				<button class="play button" id="tournament" type="button">Tournament</button>
			</div>
		`;

		this.querySelector('#regular-match').addEventListener('click', this.handleRegularMatchClick.bind(this));
		this.querySelector('#tournament').addEventListener('click', this.handleTournamentClick.bind(this));

	}

	handleRegularMatchClick() {
		this.innerHTML = `
		<div>
			<h1>Regular Match</h1>
			<p>Matchmaking for a regular match</p>
		</div>
		`;

		initMMSocket();

		mmSocket.addEventListener("message", function(e) {
			let data = JSON.parse(e.data);
			if (data.type == "game.start") {
				console.log(data.game_id);
				console.log(`Pushed state = ${"/pong/" + data.game_id}`)
				history.pushState("", "", "/pong/" + data.game_id);
				router();
			} else if (data.type == "update.message") {
				console.log(data.users);
			} else {
				console.log("whatever");
			}
		});
	}

	handleTournamentClick() {
		this.innerHTML = `
		<div>
			<h1>Tournament</h1>
			<p>Matchmaking for a tournament</p>
		</div>
		`;

		initMMSocket();

		mmSocket.addEventListener("message", function(e) {
			console.log(e.data);
		});
	}


}

customElements.define("play-menu", PlayMenu);