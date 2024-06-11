export function home_title() {
	return ("Home");
}

export function home_view() {
	return (`
		<h1>Bonjour</h1>
		<video controls width=640>
			<source src="/static/assets/mushoku-s01-e21.webm" />
			<track
				label="French"
				kind="subtitles"
				srclang="fr"
				src="/static/assets/mushoku-s01-e21.vtt"
				default />
		</video>
		<video controls width=640>
			<source src="/static/assets/oshi_no_ko-s01-e01.webm" />
		</video>
		<video controls width=640>
			<source src="/static/assets/nichijou-ed1.mp4" />
		</video>
		`
	);
}
