export function play_title() {
	return ("Play");
}

export function play_view() {
	return (`
		<div class="play-container">
			<div class="top-buttons">
				<div class="left-play-buttons">
					<a class="play-button btn" id="Regular_Queue" data-link href="/play/regular">Regular queue</a>
					<a class="play-button btn" id="Tournament_Queue" data-link href="/play/tournament">Tournament queue</a>
				</div>
				<div class="right-play-buttons">
					<a class="play-button btn" id="Local_Pong_Game" data-link href="/pong_local">Local Pong Game</a>
					<a class="play-button btn" id="Local_Pong_Tournament" data-link href="/pong_local_tournament">Local Pong Tournament</a>
				</div>
			</div>
			<div class="center-play-button">
				<a class="play-button btn" id="Ai_Match" data-link href="/pong/ai">AI match</a>
			</div>
		</div>
	`);
}
