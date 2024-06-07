export function play_title() {
	return ("Play");
}

export function play_view(params) {
	return (`<div>
				<a href="/play/regular" data-link id="Regular_Queue">Regular queue</a>
				<a href="/play/tournament" data-link id="Tournament_Queue">Tournament queue</a>
				<a href="/play/ai" data-link id="Ai_Match">AI match</a>
			</div>`);
}
