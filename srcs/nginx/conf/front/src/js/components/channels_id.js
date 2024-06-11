import { updateSocket } from "./socket.js";
import { router } from "../main.js";

class Channel extends HTMLElement {
	constructor() {
		super();

		this.innerHTML = `
		`;

		this.refreshChannel(this.getAttribute("id"));

		updateSocket.onmessage = (e) => {
			var data = JSON.parse(e.data);
			if (data.type.includes("channel") || data.type.includes("dm") || data.type.includes("block")) {
				this.refreshChannel(this.getAttribute("id"));
			}
		};
	}

	refreshChannel(channel_id) {
		fetch(
			`/api/channels/${channel_id}`,
			{
				method: "GET",
				headers: {
					'Accept': 'application/json, text/plain',
					'Content-Type': 'application/json;charset=UTF-8',
					'Authorization': `Bearer ${localStorage.getItem("access-token")}`,
				},
			}
		).then((response) => {
			let new_html = "";
			if (response.status != 200) {
				history.pushState("", "", "/");
				router();
			}
			response.json().then((channel_json) => {
				if (channel_json.error) {
					new_html = `
						<div>
							<h1>Error</h1>
							<p>${channel_json.error}</p>
						</div>
						`;
				}
				else if (channel_json.channel) {
					new_html += `
						<div>
							<h1>Channel name: ${channel_json.channel.name}</h1>
							<p>Channel description: ${channel_json.channel.description}</p>
							<p>Channel created at: ${channel_json.channel.created_at}</p>
							<p>Channel topic: ${channel_json.channel.topic}</p>
							<div id="user_list">
								<p>Users:</p>
					`;
					channel_json.channel.users.forEach((user) => {
						new_html += `
							<a href="/profile/${user}" data-link id="Channel_Id">
								${user}
							</a>
						`;
					});
					new_html += `</div></div>`;
					fetch(
						`/api/channels/${channel_id}/messages`,
						{
							method: "GET",
							headers: {
								'Accept': 'application/json, text/plain',
								'Content-Type': 'application/json;charset=UTF-8',
								'Authorization': `Bearer ${localStorage.getItem("access-token")}`,
							},
						}
					).then((response) => {
						response.json().then((messages_json) => {
							if (messages_json.error) {
								new_html = `
										<div>
											<h1>Error</h1>
											<p>${messages_json.error}</p>
										</div>
									`;
							}
							else if (messages_json.messages) {
								messages_json.messages.forEach((message) => {
									new_html += `
										<div>
											<p>author: ${message.author}</p>
											<p>content: ${message.content}</p>
											<p>edited: ${message.edited}</p>
											<p>created at: ${message.created_at}</p>
											<p>is pin: ${message.is_pin}</p>
											<div id="seen_users">
												<p>Seen by:</p>
									`;
									message.seen_by.forEach((seen) => {
										new_html += `<a href="/profile/${seen}" data-link id="Channel_Id">
														${seen}
													</a>`;
									});
									new_html += `</div></div>`;
								});

								new_html += `
									<form id="send_message">
										<p>
											<label for="id_message">message:</label>
											<input id="id_message" type=text name="message" required>
										</p>
										<button id="send_message_button" type="submit">send</button>
									</form>
									<form id="add_user">
										<p>
											<label for="id_user">user:</label>
											<input id="id_user" type=text name="user" required>
										</p>
										<button id="add_user_button" type="submit">add user</button>
									</form>
								`;

								this.innerHTML = new_html;

								document.getElementById("send_message").addEventListener("submit", (event) => {
									event.preventDefault();
									document.getElementById("send_message_button").disabled = true;
									this.sendMessage(channel_id);
									document.getElementById("send_message_button").disabled = false;
								});

								document.getElementById("add_user").addEventListener("submit", (event) => {
									event.preventDefault();
									document.getElementById("add_user_button").disabled = true;
									this.addUser(channel_id);
									document.getElementById("add_user_button").disabled = false;
								});

								if (channel_json.channel.cant_send) {
									document.getElementById("send_message").remove();
								}

								if (channel_json.channel.channel_type === 1) {
									document.getElementById("add_user").remove();
								}
							}
						});
					});
				}
			});
		});
	}

	async sendMessage(id) {
		const formData = new FormData(document.getElementById("send_message"));
		let request = {};
		request.content = formData.get("message");
		const response = await fetch(`/api/channels/${id}/messages`, {
			method: "POST",
			headers: {
				Accept: "application/json, text/plain",
				"Content-Type": "application/json;charset=UTF-8",
				'Authorization': `Bearer ${localStorage.getItem("access-token")}`,
			},
			body: JSON.stringify(request),
		});
		const json = await response.json();
		const status = response.status;
		if (status !== 201) {
			this.innerHTML = `
				<div>
					<h1>Error</h1>
					<p>${json.error}</p>
				</div>
			`;
		}
	}

	async addUser(id) {
		const formData = new FormData(document.getElementById("add_user"));
		let request = {};
		request.users = [formData.get("user")];
		const response = await fetch(`/api/channels/${id}`, {
			method: "PATCH",
			headers: {
				Accept: "application/json, text/plain",
				"Content-Type": "application/json;charset=UTF-8",
				'Authorization': `Bearer ${localStorage.getItem("access-token")}`,
			},
			body: JSON.stringify(request),
		});
		const json = await response.json();
		const status = response.status;
		if (status !== 200) {
			this.innerHTML = `
			<div>
				<h1>Error</h1>
				<p>${json.error}</p>
			</div>
		`;
		}
	}
}
customElements.define("channel-id", Channel);
