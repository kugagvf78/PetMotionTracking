function pushAlert(msg){
    const alertBox = document.createElement("div");
    alertBox.className = "alert-popup";
    alertBox.innerHTML = "🚨 " + msg;

    document.body.appendChild(alertBox);

    setTimeout(() => alertBox.remove(), 5000);
}
