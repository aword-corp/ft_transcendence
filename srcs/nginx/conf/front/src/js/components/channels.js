import { updateSocket } from "./socket.js";

class Channels extends HTMLElement {
	constructor() {
		super();

		this.innerHTML = `
		`;

		this.refreshChannels();

		this.is_creating = false;

		updateSocket.onmessage = (e) => {
			var data = JSON.parse(e.data);
			if (data.type.includes("channel") || data.type.includes("dm") || data.type.includes("block")) {
				this.refreshChannels();
			}
		};
	}

	refreshChannels() {
		fetch(
			`/api/channels`,
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
				this.innerText = "";
			}
			response.json().then((json) => {
				if (json.error) {
					new_html = `
						<div>
							<h1>Error</h1>
							<p>${json.error}</p>
						</div>
						`;
				}
				else if (json.channels) {
					json.channels.forEach((channel) => {
						new_html += `
							<div id="channel_list">
								<a href="/channels/${channel.id}" data-link id="Channel_Id">
									${channel.name}
								</a>
							</div>
						`;
					});
					new_html += `
						<form>
							<p>
								<label for="id_name">name:</label>
								<input id="id_name" type=text name="name" required>
							</p>
							<button id="create_channel_button" type="submit">create</button>
						</form>
						`;

					this.innerHTML = new_html;

					let form = this.querySelector("form");

					form.addEventListener("submit", (event) => {
						event.preventDefault();
						if (this.is_creating)
							return;
						this.is_creating = true;
						document.getElementById("create_channel_button").disabled = true;
						this.onSubmit(form).then(() => {
							document.getElementById("create_channel_button").disabled = false;
							this.is_creating = false;
						});
					});

				}

			});
		});
	}

	async onSubmit(form) {
		const formData = new FormData(form);
		let request = {};
		request.name = formData.get("name");
		form.reset();
		const response = await fetch(`/api/channels`, {
			method: "PUT",
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
}

customElements.define("channel-list", Channels);
