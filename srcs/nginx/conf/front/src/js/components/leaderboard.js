import { objIsEmpty } from "../utils/objects.js";

class Leaderboard extends HTMLElement {
	constructor() {
		super();

		this.innerHTML = `
			<div class="container mt-5">
				<div id="leaderboard" class="table-responsive"></div>
			</div>
		`;

		fetch("/api/leaderboard", {
			method: "GET",
			headers: {
				Accept: "application/json, text/plain",
				"Content-Type": "application/json;charset=UTF-8",
			},
		}).then((response) => {
			response.json().then((json) => {
				const leaderboardElement = document.getElementById("leaderboard");
				const leaderboardData = JSON.parse(json.leaderboard);

				if (objIsEmpty(leaderboardData)) {
					leaderboardElement.innerText = "No data";
					leaderboardElement.classList.add("text-center", "mt-3");
					return;
				}

				leaderboardElement.innerHTML = '';

				const table = document.createElement('table');
				table.classList.add('table', 'table-striped', 'table-bordered', 'table-hover');

				const thead = table.createTHead();
				const headerRow = thead.insertRow();
				const nameHeader = document.createElement('th');
				nameHeader.textContent = 'Name';
				const scoreHeader = document.createElement('th');
				scoreHeader.textContent = 'Score';

				headerRow.appendChild(nameHeader);
				headerRow.appendChild(scoreHeader);

				const tbody = table.createTBody();
				Object.entries(leaderboardData).forEach(([name, score]) => {
					if (!name || !name.length)
						return;
					const row = tbody.insertRow();
					const nameCell = row.insertCell();
					const scoreCell = row.insertCell();

					const profile = document.createElement('a');
					profile.textContent = name;
					profile.href = `/profile/${name}`;
					profile.classList.add('text-decoration-none');

					nameCell.appendChild(profile);
					nameCell.classList.add('text-center');
					scoreCell.textContent = Math.trunc(score);
					scoreCell.classList.add('text-center');
				});

				leaderboardElement.appendChild(table);
			});
		});
	}
}

customElements.define("leader-board", Leaderboard);
