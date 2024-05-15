import { router } from "../main.js"

class Login extends HTMLElement {
	constructor() {
		super();

		this.innerHTML = `
			<form class="auth-form">
				<p>
					<label for="id_username">Username/Email:</label>
					<input id="id_username" type=text name="username" required>
				</p>
				<p>
					<label for="id_password">Password:</label>
					<input id="id_password" type=password name="password" required>
				</p>
				<button type="submit">Login</button>
				<p id="form-status"></p>
			</form>
	    `;

		let form = this.querySelector("form");

		async function onSubmit() {
			const formData = new FormData(form);
			try {

				const response = await fetch(
					"https://localhost:8443/api/auth/login",
					{
						method: "POST",
						headers: {
							'Accept': 'application/json, text/plain',
							'Content-Type': 'application/json;charset=UTF-8'
						},
						body: JSON.stringify({ username: formData.get("username"), password: formData.get("password") }),
					}
				);
				const json = await response.json();
				const status = response.status;
				if (status != 200) {
					document.getElementById("form-status").innerText = json.detail;
					return;
				}
				localStorage.setItem("access-token", json.access);
				localStorage.setItem("refresh-token", json.refresh);
				history.pushState("", "", "/");
				router();
			}
			catch (e) { }
		}

		form.addEventListener("submit", (event) => {
			event.preventDefault();
			onSubmit();
		});
	}
}

customElements.define("login-form", Login);
