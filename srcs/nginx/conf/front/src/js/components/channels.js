import { router } from "../main.js";

class Channels extends HTMLElement {
	constructor() {
		super();

		this.innerHTML = `
		`;

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
				else if (json.channels) {
					json.channels.forEach((channel) => {
						this.innerHTML += `
							<div>
								<a href="/channels/${channel.id}" data-link id="Channel_Id">
									${channel.name}
								</a>
							</div>
						`;
					});
					this.innerHTML += `
						<form>
							<p>
								<label for="id_name">name:</label>
								<input id="id_name" type=text name="name" required>
							</p>
							<button type="submit">create</button>
						</form>
					`;

					let form = this.querySelector("form");

					async function onSubmit() {
						const formData = new FormData(form);
						let request = {};
						request.name = formData.get("name");
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
						else {
							router();
						}
					}

					form.addEventListener("submit", (event) => {
						event.preventDefault();
						onSubmit();
					});
				}
			});
		});
	}
}
customElements.define("channel-list", Channels);
