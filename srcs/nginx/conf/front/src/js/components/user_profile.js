import { router } from "../main.js";

class UserProfile extends HTMLElement {
	constructor() {
		super();

		this.innerHTML = `
		`;

		fetch(
			`/api/user/profile/${this.getAttribute("user")}`,
			{
				method: "GET",
				headers: {
					'Accept': 'application/json, text/plain',
					'Content-Type': 'application/json;charset=UTF-8',
					'Authorization': `Bearer ${localStorage.getItem("access-token")}`,
				},
			}
		).then((response) => {
			if (response.status != 200) {
				this.innerText = "";
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
							<img src=${user.avatar_url ? user.avatar_url : ""} />
							<img src=${user.banner_url ? user.banner_url : ""} />
							<p>${user.display_name}</p>
							<p>${user.username}</p>
							<p>${user.bio}</p>
							<p>${user.region}</p>
							<p>${user.country_code}</p>
							<p>${user.language}</p>
							<p>${user.grade}</p>
							<p>${user.created_at}</p>
							<p>${user.xp}</p>
							<p>${user.elo}</p>
							<p>${user.status}</p>
							${social_html}
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
							else
								router();
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
							else
								router();
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
							else
								router();
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
							else
								router();
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
							else
								router();
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
							else
								router();
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
							else
								router();
						}
					}

				}
			});
		});
	}
}
customElements.define("user-profile", UserProfile);
