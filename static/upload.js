const textarea = document.getElementById("editor")
const editor = CodeMirror.fromTextArea(textarea, {
    lineNumbers: true,
    mode: "markdown"
});

editor.setOption("theme", "ctp-mocha")

const passwordElement = document.querySelector(".password input")
const fileElement = document.querySelector(".file-upload input")
const fileListElement = document.querySelector(".files")
const deleteIdElement = document.querySelector(".deleter input")
const deleteConfirmElement = document.querySelector(".deleter button")
const postConfirmElement = document.querySelector(".post-button")

const postTitleElement = document.querySelector(".post-title")
const postDescriptionElement = document.querySelector(".post-description")

function getPassword() {
    return passwordElement.value;
}

// File uploading
fileElement.addEventListener('change', async function(e) {
    const file = e.target.files[0]
    if (file && confirm("Are you sure you want to upload this file?")) {
        const formData = new FormData();
        formData.append("password", getPassword())
        formData.append("file", file);
        try {
            const response = await fetch("/blog/control/image", {
                method: "POST",
                body: formData,
            });
            if (response.ok) {
                const link = document.createElement("a");
                link.innerText = link.href = await response.text();
                fileListElement.appendChild(link);
            }
        } catch (e) {
            console.error(e);
        }
    }
});

// Post deleting
deleteConfirmElement.addEventListener("click", async function (e) {
    if (confirm("Are you sure you want to delete this post?")) {
        const formData = new FormData();
        formData.append("password", getPassword())
        formData.append("id", deleteIdElement.value);
        try {
            await fetch("/blog/control/delete", {
                method: "POST",
                body: formData,
            });
        } catch (e) {
            console.error(e);
        }
    }
})

// Post... posting.
postConfirmElement.addEventListener("click", async function (e) {
    if (confirm("Are you sure you want to post this?")) {
        const formData = new FormData();
        formData.append("password", getPassword())
        formData.append("id", deleteIdElement.value);
        formData.append("title", postTitleElement.value)
        formData.append("description", postDescriptionElement.value)
        formData.append("content", editor.getValue().trim())
        try {
            await fetch("/blog/control/post", {
                method: "POST",
                body: formData,
            });
        } catch (e) {
            console.error(e);
        }
    }
})