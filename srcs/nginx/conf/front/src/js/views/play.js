export function play_title() {
	return ("Play");
}

export function play_view() {
	return (`<div>
				<a href="/play/regular" data-link id="Regular_Queue">Regular queue</a>
				<a href="/play/tournament" data-link id="Tournament_Queue">Tournament queue</a>
				<a href="/pong_local" data-link id="Local_Pong_Game">Local Pong Game</a>
				<a href="/pong_local_tournament" data-link id="Local_Pong_Tournament">Local Pong Tournament</a>
				<a href="/pong/ai" data-link id="Ai_Match">AI match</a>
			</div>`);
}
