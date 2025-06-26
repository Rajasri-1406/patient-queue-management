function categorizePatient() {
    let symptoms = document.getElementById("symptoms").value.toLowerCase();
    let age = parseInt(document.getElementById("age").value);

    let triageLevel = "Low";
    let department = "General Medicine";
    let waitingTime = "30-60 mins";
    let priorityScore = 1;

    if (symptoms.includes("chest pain") || symptoms.includes("heart attack")) {
        triageLevel = "Critical";
        department = "Cardiology";
        waitingTime = "Immediate";
        priorityScore = 5;
    } else if (symptoms.includes("stroke") || symptoms.includes("seizure")) {
        triageLevel = "High";
        department = "Neurology";
        waitingTime = "15-30 mins";
        priorityScore = 4;
    } else if (symptoms.includes("fever") || symptoms.includes("cough")) {
        triageLevel = "Moderate";
        department = "General Medicine";
        waitingTime = "30-60 mins";
        priorityScore = 2;
    }

    if (age > 65 || age < 10) {
        priorityScore += 1; // Higher priority for elderly or children
    }

    document.getElementById("triageLevel").innerText = triageLevel;
    document.getElementById("department").innerText = department;
    document.getElementById("waitingTime").innerText = waitingTime;
    document.getElementById("priorityScore").innerText = priorityScore;
}
