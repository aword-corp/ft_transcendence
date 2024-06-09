class TwoFa extends HTMLElement {
	constructor() {
		super();

		this.innerHTML =
			`
				<div>
					<p id="two-fa-status"></p>
				</div>
				<button>generate qr code</button>
			`
			;

		let div = this.querySelector("div");

		let button = this.querySelector("button");

		let fa_status = document.getElementById("two-fa-status");

		async function onSubmit() {

			try {

				const response = await fetch(
					"/api/auth/setup_2fa",
					{
						method: "POST",
						headers: {
							'Accept': 'application/json, text/plain',
							'Content-Type': 'application/json;charset=UTF-8',
							'Authorization': `Bearer ${localStorage.getItem("access-token")}`,
						},
					}
				);
				const json = await response.json();
				const status = response.status;
				if (status != 200) {
					fa_status.innerText = "error";
					return;
				}
				const qrcode = json.qr_code;
				const otp_secret = json.otp_secret;
				div.innerHTML = `<p>${otp_secret}</p>${qrcode}`;
				localStorage.removeItem("access-token");
				localStorage.removeItem("refresh-token");
			}
			catch (e) { }
		}

		button.addEventListener("click", (event) => {
			event.preventDefault();
			onSubmit();
		});
	}
}

customElements.define("two-fa", TwoFa);
