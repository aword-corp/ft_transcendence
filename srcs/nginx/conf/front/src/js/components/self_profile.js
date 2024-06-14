import { router } from "../main.js";
import { updateSocket } from "./socket.js";

class SelfProfile extends HTMLElement {
	constructor() {
		super();

		this.innerHTML = `
		`;

		this.username = JSON.parse(atob(localStorage.getItem("access-token").split('.')[1])).username;

		this.refreshProfile(this.username);

		updateSocket.onmessage = (e) => {
			var data = JSON.parse(e.data);
			if (data.type && data.type.includes("friend") || data.type.includes("dm") || data.type.includes("block")) {
				this.refreshProfile(this.username);
			}
		};

	}

	refreshProfile(username) {
		fetch(
			`/api/user/profile/${username}`,
			{
				method: "GET",
				headers: {
					'Accept': 'application/json, text/plain',
					'Content-Type': 'application/json;charset=UTF-8',
					'Authorization': `Bearer ${localStorage.getItem("access-token")}`,
				},
			}
		).then((response) => {
			if (response.status === 404) {
				history.pushState("", "", "/");
				router();
			}
			response.json().then((json) => {
				if (json.error) {
					this.innerHTML = `
						<div>
							<h1>Error</h1>
							<p>${json.error}</p>
						</div>
						`;
				}
				else if (json.user) {
					let user = json.user;
					this.innerHTML = `
						<div>
							<h1>User profile of ${user.display_name ? `${user.display_name} (${user.username})` : user.username}</h1>
							<img src=${user.avatar_url ? user.avatar_url : ""} />
							<img src=${user.banner_url ? user.banner_url : ""} />
							<p>bio: ${user.bio}</p>
							<p>region: ${user.region}</p>
							<p>country: ${user.country_code}</p>
							<p>language: ${user.language}</p>
							<p>grade: ${user.grade}</p>
							<p>created at: ${user.created_at}</p>
							<p>xp: ${user.xp}</p>
							<p>elo: ${user.elo}</p>
							<p>online: ${user.is_online}</p>
							<p>focused: ${user.is_focused}</p>
							<p>spectating: ${user.is_spectating}</p>
							<p>in game: ${user.is_playing}</p>
							<p id="error"></p>
							<a href="/profile/settings" data-link id="Edit_Profile">Edit profile</a>
						</div>
					`;
				}
			});
		});
	}
}
customElements.define("self-profile", SelfProfile);
