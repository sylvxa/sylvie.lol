const timeDisplay = document.querySelector(".time")
const TIMEZONE = "America/Chicago";

let options = {
    timeZone: TIMEZONE,
    hour: 'numeric',
    minute: 'numeric'
}
formatter = new Intl.DateTimeFormat([], options);

function updateTime() {
    timeDisplay.innerText = formatter.format(new Date())
}

if (timeDisplay != null) {
    setInterval(() => {
        updateTime()
    }, 1000)
    updateTime();
}
