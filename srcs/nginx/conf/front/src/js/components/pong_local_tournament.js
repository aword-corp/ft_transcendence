class LocalTournament extends HTMLElement {
	constructor() {
		super();

		this.players = [];

		this.innerHTML = `
            <div>
                <label for="playerName">Player Name: </label>
                <input type="text" id="playerName" />
                <button id="addPlayer">Add Player</button>
            </div>
            <p id="playerList"></p>
            <p id="count">Number of Players: 0</p>
            <button id="launchTournament">Launch Tournament</button>
            <p id="message"></p>
			<div id="game_div"></div>
        `;

		this.playerNameInput = this.querySelector('#playerName');
		this.addPlayerButton = this.querySelector('#addPlayer');
		this.playerListElement = this.querySelector('#playerList');
		this.countElement = this.querySelector('#count');
		this.launchTournamentButton = this.querySelector('#launchTournament');
		this.messageElement = this.querySelector('#message');

		this.addPlayerButton.addEventListener('click', () => this.addPlayer());
		this.launchTournamentButton.addEventListener('click', () => this.launchTournament());
	}

	addPlayer() {
		const playerName = this.playerNameInput.value.trim();
		if (playerName && this.players.length < 64) {
			this.players.push(playerName);
			this.updatePlayerList();
			this.playerNameInput.value = '';
		} else if (this.players.length >= 64) {
			this.messageElement.textContent = "Cannot add more than 64 players.";
		}
	}

	updatePlayerList() {
		document.getElementById("playerList").innerHTML = "";
		this.players.forEach(function (player) {
			const player_el = document.createElement('p');
			player_el.innerText = player;
			document.getElementById("playerList").append(player_el);
		});
		this.countElement.textContent = `Number of Players: ${this.players.length}`;
	}

	getPromiseFromEvent(item, event) {
		console.log("item", item);
		console.log("event", event);
		return new Promise((resolve) => {
			const listener = (e) => {
				item.removeEventListener(event, listener);
				console.log("trigger");
				resolve({ winner: e.winner, score: e.score });
			};
			item.addEventListener(event, listener);
		});
	}

	async launchTournament() {
		if (this.players.length < 4) {
			this.messageElement.textContent = "A minimum of 4 players is required to start the tournament.";
		} else {
			let n_round = Math.ceil(Math.log2(this.players.length));
			let current_round = 0;

			while (current_round < n_round) {
				let tree = [];
				console.log("round", current_round);
				for (var i = 0; i < this.players.length; i += 2) {
					if (i + 1 < this.players.length) {
						console.log("match", this.players[i], this.players[i + 1]);
						tree.push(await this.launchGame(this.players[i], this.players[i + 1]));
					}
					else {
						tree.push(this.players[i]);
					}
				}

				this.players = tree;
				++current_round;
			}
		}
	}

	async launchGame(player_1, player_2) {
		const game_div = document.getElementById("game_div");
		game_div.innerHTML = `<pong-local-game id="game"></pong-local-game>`;
		const game = document.getElementById("game");
		const result = await this.getPromiseFromEvent(game, "game_ended");
		console.log("winner", result.winner ? player_1 : player_2);
		game_div.innerHTML = "";
		return (result.winner ? player_1 : player_2);
	}
}

customElements.define("pong-local-tournament-game", LocalTournament);
