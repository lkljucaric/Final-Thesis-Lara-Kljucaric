const obrazac = document.getElementById("obrazac");
const unos = document.getElementById("unos");
const razgovor = document.getElementById("razgovor");

function dodajPoruku(uloga, tekst) {
    const redDiv = document.createElement("div");
    redDiv.classList.add("redPoruke");

    if (uloga === "korisnik") {
        redDiv.classList.add("redKorisnika");
    } else {
        redDiv.classList.add("redBota");
    }

    if (uloga === "bot") {
        const avatar = document.createElement("img");
        avatar.src = "/static/slike/robot.jpg";
        avatar.alt = "BookBot";
        avatar.classList.add("avatarBota");
        redDiv.appendChild(avatar);
    }

    const porukaDiv = document.createElement("div");
    porukaDiv.classList.add("poruka");

    let oznaka;

    if (uloga === "korisnik") {
        oznaka = "Ti";
        porukaDiv.classList.add("porukaKorisnika");
    } else {
        oznaka = "BookBot";
        porukaDiv.classList.add("porukaBota");
    }

    porukaDiv.innerHTML = "<strong>" + oznaka + ":</strong> " + tekst;

    redDiv.appendChild(porukaDiv);
    razgovor.appendChild(redDiv);
    razgovor.scrollTop = razgovor.scrollHeight;

    return redDiv;
}

obrazac.addEventListener("submit", async function(event) {
    event.preventDefault();

    const poruka = unos.value.trim();

    if (poruka === "") {
        return;
    }

    dodajPoruku("korisnik", poruka);
    unos.value = "";

    const porukaCekanja = dodajPoruku("bot", "Razmišljam...");

    try {
        const odgovorServera = await fetch("/chat", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                message: poruka
            })
        });

        const podaci = await odgovorServera.json();

        porukaCekanja.remove();

        if (odgovorServera.ok) {
            dodajPoruku("bot", podaci.answer);
        } else {
            dodajPoruku("bot", "Dogodila se greška: " + podaci.answer);
        }

    } catch (error) {
        porukaCekanja.remove();
        dodajPoruku("bot", "Greška u komunikaciji s Flask serverom.");
    }
});