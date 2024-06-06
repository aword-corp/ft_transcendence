import { router } from "../main.js";

class FT_Auth extends HTMLElement {
	constructor() {
		super();

		this.innerHTML = ``;

		const urlParams = new URLSearchParams(window.location.search);
		const code = urlParams.get('code');

		fetch(`https://localhost:8443/api/auth/ft/callback?code=${code}`).then((response) => response.json().then((json) => {
			if (json["access_token"]) {
				localStorage.setItem("access-token", json.access_token);
				localStorage.setItem("refresh-token", json.refresh_token);
				history.pushState("", "", "/");
				router();
				return;
			}
			history.pushState("", "", "/register");
			router();
			return;
		}));
	}
}

customElements.define("ft-auth", FT_Auth);
