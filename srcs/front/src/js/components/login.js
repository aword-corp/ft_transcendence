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
				<p class="hidden" id="otp-input">
					<label for="id_otp">Validation code:</label>
					<input id="id_otp" type=text name="otp">
				</p>
				<button type="submit">Login</button>
				<p id="form-status"></p>
			</form>
	    `;

		let form = this.querySelector("form");

		async function onSubmit() {
			const formData = new FormData(form);
			let request = {};
			request.username = formData.get("username");
			request.password = formData.get("password");
			if (formData.get("otp"))
				request.otp = formData.get("otp");
			const response = await fetch(
				url,
				{
					method: "POST",
					headers: {
						'Accept': 'application/json, text/plain',
						'Content-Type': 'application/json;charset=UTF-8'
					},
					body: JSON.stringify(request),
				}
			);
			const json = await response.json();
			const status = response.status;
			if (status != 200) {
				if (json.detail.includes("validation")) {
					document.getElementById("otp-input").className = "";
					document.getElementById("id_otp").required = true;
					url = "https://localhost:8443/api/auth/login/verify";
				}
				document.getElementById("form-status").innerText = json.detail;
				return;
			}
			localStorage.setItem("access-token", json.access_token);
			localStorage.setItem("refresh-token", json.refresh_token);
			history.pushState("", "", "/");
			router();
		}

		form.addEventListener("submit", (event) => {
			event.preventDefault();
			onSubmit();
		});
	}
}

var url = "https://localhost:8443/api/auth/login";

customElements.define("login-form", Login);
