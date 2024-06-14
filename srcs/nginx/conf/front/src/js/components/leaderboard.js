import { objIsEmpty } from "../utils/objects.js";

class Leaderboard extends HTMLElement {
	constructor() {
		super();

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
					leaderboardElement.classList.add("leaderboard-align-text");
					return;
				}

				leaderboardElement.innerHTML = '';

				const table = document.createElement('table');
				table.style.width = '100%';
				table.style.borderCollapse = 'collapse';

				const header = table.createTHead();
				const headerRow = header.insertRow();
				const nameHeader = document.createElement('th');
				nameHeader.textContent = 'Name';
				nameHeader.style.border = '1px solid black';
				nameHeader.style.padding = '8px';
				const scoreHeader = document.createElement('th');
				scoreHeader.textContent = 'Score';
				scoreHeader.style.border = '1px solid black';
				scoreHeader.style.padding = '8px';

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
					profile.setAttribute('data-link', '');
					nameCell.appendChild(profile);

					nameCell.style.textAlign = 'center';
					nameCell.style.border = '1px solid black';
					nameCell.style.padding = '8px';

					scoreCell.textContent = Math.trunc(score);
					scoreCell.style.textAlign = 'center';
					scoreCell.style.border = '1px solid black';
					scoreCell.style.padding = '8px';

				});

				leaderboardElement.appendChild(table);
			});
		});

		this.innerHTML = `
			<p id="leaderboard"></p>
		`;
	}
}

customElements.define("leader-board", Leaderboard);
