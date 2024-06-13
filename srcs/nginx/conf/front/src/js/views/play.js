export function play_title() {
	return ("Play");
}

export function play_view() {
	return (`
		<div class="play-container">
			<div class="top-buttons">
				<div class="left-play-buttons">
					<button class="play-button btn" id="Regular_Queue" onclick="location.href='/play/regular'">Regular queue</button>
					<button class="play-button btn" id="Tournament_Queue" onclick="location.href='/play/tournament'">Tournament queue</button>
				</div>
				<div class="right-play-buttons">
					<button class="play-button btn" id="Local_Pong_Game" onclick="location.href='/pong_local'">Local Pong Game</button>
					<button class="play-button btn" id="Local_Pong_Tournament" onclick="location.href='/pong_local_tournament'">Local Pong Tournament</button>
				</div>
			</div>
			<div class="center-play-button">
				<button class="play-button btn" id="Ai_Match" onclick="location.href='/pong/ai'">AI match</button>
			</div>
		</div>
	`);
}
