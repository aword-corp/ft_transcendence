import { router } from "../main.js";
import { updateSocket } from "./socket.js";

class UserProfile extends HTMLElement {
	constructor() {
		super();

		this.innerHTML = `
		`;

		this.refreshProfile(this.getAttribute("user"));

		updateSocket.onmessage = (e) => {
			var data = JSON.parse(e.data);
			if (data.type.includes("friend") || data.type.includes("dm") || data.type.includes("block")) {
				this.refreshProfile(this.getAttribute("user"));
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
					let social_html = `
						${(JSON.parse(atob(localStorage.getItem("access-token").split('.')[1]))).username == user.username ?
							``
							:
							(user.is_blocked ?
								`<button id="unblock_user">Unblock user</button>`
								:
								((user.is_friend ?
									`<button id="remove_friend">Remove friend</button>`
									:
									(user.sent_friend_request ?
										`<button id="cancel_friend_request">Cancel</button>`
										:
										user.has_friend_request ?
											`<button id="accept_friend">Accept</button><button id="reject_friend">Reject</button>`
											:
											`<button id="add_friend">Add friend</button>`
									)
								) + `<button id="block_user">Block user</button>`)
							)
						}
					`;
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
							${social_html}
							${user.can_dm ? `<button id="dm_user">Direct messages</button>` : ""}
							<p id="error"></p>
						</div>
					`;
					if (document.getElementById("accept_friend")) {
						document.getElementById("accept_friend").onclick = async function accept_friend() {
							this.disabled = true;
							const response = await fetch(
								`/api/user/requests/friends/accept/${user.username}`,
								{
									method: "POST",
									headers: {
										'Accept': 'application/json, text/plain',
										'Content-Type': 'application/json;charset=UTF-8',
										'Authorization': `Bearer ${localStorage.getItem("access-token")}`,
									},
								}
							);
							const friend_json = await response.json();
							this.disabled = false;
							if (friend_json.error)
								document.getElementById("error").innerText = friend_json.error;

						}
					}
					if (document.getElementById("cancel_friend_request")) {
						document.getElementById("cancel_friend_request").onclick = async function cancel_friend_request() {
							this.disabled = true;
							const response = await fetch(
								`/api/user/requests/friends/remove/${user.username}`,
								{
									method: "POST",
									headers: {
										'Accept': 'application/json, text/plain',
										'Content-Type': 'application/json;charset=UTF-8',
										'Authorization': `Bearer ${localStorage.getItem("access-token")}`,
									},
								}
							);
							const friend_json = await response.json();
							this.disabled = false;
							if (friend_json.error)
								document.getElementById("error").innerText = friend_json.error;

						}
					}
					if (document.getElementById("reject_friend")) {
						document.getElementById("reject_friend").onclick = async function reject_friend() {
							this.disabled = true;
							const response = await fetch(
								`/api/user/requests/friends/reject/${user.username}`,
								{
									method: "POST",
									headers: {
										'Accept': 'application/json, text/plain',
										'Content-Type': 'application/json;charset=UTF-8',
										'Authorization': `Bearer ${localStorage.getItem("access-token")}`,
									},
								}
							);
							const friend_json = await response.json();
							this.disabled = false;
							if (friend_json.error)
								document.getElementById("error").innerText = friend_json.error;

						}
					}
					if (document.getElementById("add_friend")) {
						document.getElementById("add_friend").onclick = async function add_friend() {
							this.disabled = true;
							const response = await fetch(
								`/api/user/friends/add/${user.username}`,
								{
									method: "POST",
									headers: {
										'Accept': 'application/json, text/plain',
										'Content-Type': 'application/json;charset=UTF-8',
										'Authorization': `Bearer ${localStorage.getItem("access-token")}`,
									},
								}
							);
							const friend_json = await response.json();
							this.disabled = false;
							if (friend_json.error)
								document.getElementById("error").innerText = friend_json.error;

						}
					}
					if (document.getElementById("remove_friend")) {
						document.getElementById("remove_friend").onclick = async function remove_friend() {
							this.disabled = true;
							const response = await fetch(
								`/api/user/friends/remove/${user.username}`,
								{
									method: "POST",
									headers: {
										'Accept': 'application/json, text/plain',
										'Content-Type': 'application/json;charset=UTF-8',
										'Authorization': `Bearer ${localStorage.getItem("access-token")}`,
									},
								}
							);
							const friend_json = await response.json();
							this.disabled = false;
							if (friend_json.error)
								document.getElementById("error").innerText = friend_json.error;

						}
					}
					if (document.getElementById("unblock_user")) {
						document.getElementById("unblock_user").onclick = async function unblock_user() {
							this.disabled = true;
							const response = await fetch(
								`/api/user/unblock/${user.username}`,
								{
									method: "POST",
									headers: {
										'Accept': 'application/json, text/plain',
										'Content-Type': 'application/json;charset=UTF-8',
										'Authorization': `Bearer ${localStorage.getItem("access-token")}`,
									},
								}
							);
							const block_json = await response.json();
							this.disabled = false;
							if (block_json.error)
								document.getElementById("error").innerText = block_json.error;

						}
					}
					if (document.getElementById("block_user")) {
						document.getElementById("block_user").onclick = async function block_user() {
							this.disabled = true;
							const response = await fetch(
								`/api/user/block/${user.username}`,
								{
									method: "POST",
									headers: {
										'Accept': 'application/json, text/plain',
										'Content-Type': 'application/json;charset=UTF-8',
										'Authorization': `Bearer ${localStorage.getItem("access-token")}`,
									},
								}
							);
							const block_json = await response.json();
							this.disabled = false;
							if (block_json.error)
								document.getElementById("error").innerText = block_json.error;

						}
					}

					if (document.getElementById("dm_user")) {
						document.getElementById("dm_user").onclick = async function dm_user() {
							this.disabled = true;
							const response = await fetch(
								`/api/user/profile/${user.username}/dm`,
								{
									method: "GET",
									headers: {
										'Accept': 'application/json, text/plain',
										'Content-Type': 'application/json;charset=UTF-8',
										'Authorization': `Bearer ${localStorage.getItem("access-token")}`,
									},
								}
							);
							const dm_json = await response.json();
							this.disabled = false;
							if (dm_json.error)
								document.getElementById("error").innerText = dm_json.error;
							else if (dm_json.channel_id) {
								history.pushState("", "", `/channels/${dm_json.channel_id}`);
								router();
							}
						}
					}

				}
			});
		});
	}
}
customElements.define("user-profile", UserProfile);
