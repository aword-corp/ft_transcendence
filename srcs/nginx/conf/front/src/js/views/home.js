import "../components/home.js"

export function home_title() {
	return ("Home");
}

export function home_view() {
	return (`
		<h1>Bonjour</h1>
		<video controls width=640>
			<source src="https://cdn.acorp.games/assets/mushoku-s01-e21.webm" />
			<track
				label="French"
				kind="subtitles"
				srclang="fr"
				src="https://cdn.acorp.games/assets/mushoku-s01-e21.vtt"
				default />
		</video>
		<video controls width=640>
			<source src="https://cdn.acorp.games/assets/oshi_no_ko-s01-e01.webm" />
		</video>
		<video controls width=640>
			<source src="https://cdn.acorp.games/assets/nichijou-ed1.mp4" />
		</video>
		`
	);
}
