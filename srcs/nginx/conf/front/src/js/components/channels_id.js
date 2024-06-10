import { router } from "../main.js";

class Channel extends HTMLElement {
	constructor() {
		super();

		this.innerHTML = `
		`;

		fetch(
			`/api/channels/${this.getAttribute("id")}`,
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
				else if (json.channel) {
					this.innerHTML += `
						<div>
							<h1>${json.channel.name}</h1>
							<p>${json.channel.description}</p>
							<p>${json.channel.created_at}</p>
							<p>${json.channel.topic}</p>
					`;
					json.channel.users.forEach((user) => {
						this.innerHTML += `
							<p>${user}</p>
						`;
					});
					this.innerHTML += `</div>`;
					fetch(
						`/api/channels/${this.getAttribute("id")}/messages`,
						{
							method: "GET",
							headers: {
								'Accept': 'application/json, text/plain',
								'Content-Type': 'application/json;charset=UTF-8',
								'Authorization': `Bearer ${localStorage.getItem("access-token")}`,
							},
						}
					).then((response) => {
						response.json().then((json) => {
							if (json.error) {
								this.innerHTML = `
										<div>
											<h1>Error</h1>
											<p>${json.error}</p>
										</div>
									`;
							}
							else if (json.messages) {
								json.messages.forEach((message) => {
									this.innerHTML += `
										<div>
											<p>${message.author}</p>
											<p>${message.content}</p>
											<p>${message.edited}</p>
											<p>${message.created_at}</p>
											<p>${message.is_pin}</p>
									`;
									message.seen_by.forEach((seen) => {
										this.innerHTML += `<p>${seen}</p>`;
									});
									this.innerHTML += `</div>`;
								});

								this.innerHTML += `
									<form id="send_message">
										<p>
											<label for="id_message">message:</label>
											<input id="id_message" type=text name="message" required>
										</p>
										<button type="submit">send</button>
									</form>
									<form id="add_user">
										<p>
											<label for="id_user">user:</label>
											<input id="id_user" type=text name="user" required>
										</p>
										<button type="submit">send</button>
									</form>
								`;

								let send_message_form = document.getElementById("send_message");

								async function sendMessage(id) {
									const formData = new FormData(send_message_form);
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
									else {
										router();
									}
								}

								send_message_form.addEventListener("submit", (event) => {
									event.preventDefault();
									sendMessage(this.getAttribute("id"));
								});

								let add_user_form = document.getElementById("add_user");

								async function addUser(id) {
									const formData = new FormData(add_user_form);
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
									else {
										router();
									}
								}

								add_user_form.addEventListener("submit", (event) => {
									event.preventDefault();
									addUser(this.getAttribute("id"));
								});
							}
						});
					});
				}
			});
		});
	}
}
customElements.define("channel-id", Channel);
