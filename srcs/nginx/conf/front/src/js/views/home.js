// import "../components/home.js"

export function home_title() {
	return ("Home");
}

export function home_view() {
	return (`
        <div class="container-home">
            <h1 class="main-title">PONG</h1>
            <div class="video-row">
                <video controls width=320>
                    <source src="https://cdn.acorp.games/assets/mushoku-s01-e21.webm" />
                    <track
                        label="French"
                        kind="subtitles"
                        srclang="fr"
                        src="https://cdn.acorp.games/assets/mushoku-s01-e21.vtt"
                        default />
                </video>
                <video controls width=320>
                    <source src="https://cdn.acorp.games/assets/oshi_no_ko-s01-e01.webm" />
                </video>
                <video controls width=320>
                    <source src="https://cdn.acorp.games/assets/nichijou-ed1.mp4" />
                </video>
            </div>
        </div>
    `);
}
