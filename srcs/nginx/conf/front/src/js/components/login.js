import { router } from "../main.js";

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
			<a href="https://api.intra.42.fr/oauth/authorize?client_id=u-s4t2ud-964220b361e4429a890ad7ddd8d75900b65510f26557e6796e31ed2b14a754c4&redirect_uri=https%3A%2F%2Flocalhost%3A8443%2Fauth%2Fft%2Fcallback&response_type=code"><button class="w-fit flex flex-row group justify-center items-center bg-black hover:bg-slate-200 dark:hover:bg-white hover:text-black transition-all dark:border-0 border-black border-2 border-transparent text-white py-2 px-8 rounded uppercase mb-4"><span>Sign in with</span><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 57 40" height="18" class="ml-2 transition-all fill-white group-hover:fill-black"><path d="M31.627.205H21.084L0 21.097v8.457h21.084V40h10.543V21.097H10.542L31.627.205M35.349 10.233 45.58 0H35.35v10.233M56.744 10.542V0H46.512v10.542L36.279 21.085v10.543h10.233V21.085l10.232-10.543M56.744 21.395 46.512 31.628h10.232V21.395"></path></svg></button></a>
	    `;
		let form = this.querySelector("form");

		async function onSubmit() {
			const formData = new FormData(form);
			let request = {};
			request.username = formData.get("username");
			request.password = formData.get("password");
			if (formData.get("otp")) request.otp = formData.get("otp");
			const response = await fetch(url, {
				method: "POST",
				headers: {
					Accept: "application/json, text/plain",
					"Content-Type": "application/json;charset=UTF-8",
				},
				body: JSON.stringify(request),
			});
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
